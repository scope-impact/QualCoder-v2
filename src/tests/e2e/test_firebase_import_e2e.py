"""
Firebase Analytics Import Pipeline - E2E Tests

Tests for importing Firebase Analytics data (pre-aggregated CSV)
into QualCoder as typed Case attributes with merge support.
"""

from __future__ import annotations

import allure
import pytest

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-051 Firebase Analytics Import"),
]


def _make_tools(code_repo, category_repo, segment_repo, source_repo, case_repo, event_bus):
    """Create ExchangeTools wired through ExchangeCoordinator."""
    from src.contexts.exchange.interface.mcp_tools import ExchangeTools
    from src.contexts.exchange.presentation.coordinator import ExchangeCoordinator

    coordinator = ExchangeCoordinator(
        code_repo=code_repo,
        category_repo=category_repo,
        segment_repo=segment_repo,
        source_repo=source_repo,
        case_repo=case_repo,
        event_bus=event_bus,
    )
    return ExchangeTools(coordinator=coordinator)


@allure.story("QC-051.02 Import Pre-Aggregated CSV with Type Inference")
class TestCSVTypeInference:
    """AC #2 and #3: Import CSV with auto-detected attribute types."""

    @allure.title("AC #3: Import auto-detects NUMBER, DATE, BOOLEAN, TEXT types")
    def test_import_csv_with_type_inference(
        self, case_repo, event_bus, tmp_path
    ):
        """CSV import should infer attribute types instead of defaulting to TEXT."""
        from src.contexts.exchange.core.commands import ImportSurveyCSVCommand
        from src.contexts.exchange.core.commandHandlers.import_survey_csv import (
            import_survey_csv,
        )

        csv_path = tmp_path / "firebase_profiles.csv"
        csv_path.write_text(
            "participant_id,sessions,engagement_tier,active,first_seen\n"
            "user_001,12,power_user,true,2026-01-15\n"
            "user_002,3,regular,false,2026-02-01\n"
            "user_003,1,casual,true,2026-03-10\n"
        )

        result = import_survey_csv(
            command=ImportSurveyCSVCommand(
                source_path=str(csv_path),
                name_column="participant_id",
            ),
            case_repo=case_repo,
            event_bus=event_bus,
        )

        assert result.is_success

        from src.contexts.cases.core.entities import AttributeType

        cases = case_repo.get_all()
        assert len(cases) == 3

        user1 = next(c for c in cases if c.name == "user_001")
        sessions_attr = user1.get_attribute("sessions")
        tier_attr = user1.get_attribute("engagement_tier")
        active_attr = user1.get_attribute("active")
        first_seen_attr = user1.get_attribute("first_seen")

        assert sessions_attr is not None
        assert sessions_attr.attr_type == AttributeType.NUMBER
        assert tier_attr.attr_type == AttributeType.TEXT
        assert active_attr.attr_type == AttributeType.BOOLEAN
        assert first_seen_attr.attr_type == AttributeType.DATE


@allure.story("QC-051.05 Case Merge Behavior")
class TestCaseMerge:
    """AC #5: Import merges with existing cases instead of creating duplicates."""

    @allure.title("AC #5: Import updates existing case attributes without duplicating")
    def test_merge_updates_existing_case(
        self, case_repo, event_bus, tmp_path
    ):
        """When a case with the same name exists, update its attributes."""
        from src.contexts.cases.core.entities import (
            AttributeType,
            Case,
            CaseAttribute,
        )
        from src.contexts.exchange.core.commands import ImportSurveyCSVCommand
        from src.contexts.exchange.core.commandHandlers.import_survey_csv import (
            import_survey_csv,
        )
        from src.shared import CaseId

        # Pre-create a case with an existing attribute
        existing_case = Case(
            id=CaseId.new(),
            name="user_001",
            attributes=(
                CaseAttribute(
                    name="role",
                    attr_type=AttributeType.TEXT,
                    value="admin",
                ),
            ),
        )
        case_repo.save(existing_case)

        # Import CSV with overlapping case name
        csv_path = tmp_path / "profiles.csv"
        csv_path.write_text(
            "participant_id,sessions,engagement_tier\n"
            "user_001,12,power_user\n"
            "user_002,3,regular\n"
        )

        result = import_survey_csv(
            command=ImportSurveyCSVCommand(
                source_path=str(csv_path),
                name_column="participant_id",
            ),
            case_repo=case_repo,
            event_bus=event_bus,
        )

        assert result.is_success

        # Should have 2 cases total, not 3
        cases = case_repo.get_all()
        assert len(cases) == 2

        # Existing case should have new attributes AND preserve old ones
        user1 = case_repo.get_by_name("user_001")
        assert user1 is not None

        # Old attribute preserved
        role_attr = user1.get_attribute("role")
        assert role_attr is not None
        assert role_attr.value == "admin"

        # New attributes added
        sessions_attr = user1.get_attribute("sessions")
        assert sessions_attr is not None
        assert sessions_attr.attr_type == AttributeType.NUMBER

        tier_attr = user1.get_attribute("engagement_tier")
        assert tier_attr is not None

    @allure.title("AC #5: Merge overwrites existing attribute values")
    def test_merge_overwrites_attribute_value(
        self, case_repo, event_bus, tmp_path
    ):
        """Importing over an existing attribute should update its value."""
        from src.contexts.cases.core.entities import (
            AttributeType,
            Case,
            CaseAttribute,
        )
        from src.contexts.exchange.core.commands import ImportSurveyCSVCommand
        from src.contexts.exchange.core.commandHandlers.import_survey_csv import (
            import_survey_csv,
        )
        from src.shared import CaseId

        existing_case = Case(
            id=CaseId.new(),
            name="user_001",
            attributes=(
                CaseAttribute(name="sessions", attr_type=AttributeType.NUMBER, value=5),
            ),
        )
        case_repo.save(existing_case)

        csv_path = tmp_path / "profiles.csv"
        csv_path.write_text(
            "participant_id,sessions\n"
            "user_001,12\n"
        )

        result = import_survey_csv(
            command=ImportSurveyCSVCommand(
                source_path=str(csv_path),
                name_column="participant_id",
            ),
            case_repo=case_repo,
            event_bus=event_bus,
        )

        assert result.is_success

        user1 = case_repo.get_by_name("user_001")
        sessions_attr = user1.get_attribute("sessions")
        assert sessions_attr.value == "12" or sessions_attr.value == 12


@allure.story("QC-051.04 Configurable ID Column")
class TestConfigurableIdColumn:
    """AC #4: Import maps configurable column to Case name."""

    @allure.title("AC #4: Custom name_column maps to Case name")
    def test_custom_id_column(
        self, case_repo, event_bus, tmp_path
    ):
        from src.contexts.exchange.core.commands import ImportSurveyCSVCommand
        from src.contexts.exchange.core.commandHandlers.import_survey_csv import (
            import_survey_csv,
        )

        csv_path = tmp_path / "profiles.csv"
        csv_path.write_text(
            "custom_id,sessions,tier\n"
            "participant_A,10,power\n"
            "participant_B,2,casual\n"
        )

        result = import_survey_csv(
            command=ImportSurveyCSVCommand(
                source_path=str(csv_path),
                name_column="custom_id",
            ),
            case_repo=case_repo,
            event_bus=event_bus,
        )

        assert result.is_success
        cases = case_repo.get_all()
        case_names = {c.name for c in cases}
        assert "participant_A" in case_names
        assert "participant_B" in case_names


@allure.story("QC-051.07 MCP Tool import_firebase")
class TestMCPFirebaseImport:
    """AC #7: Agent can import Firebase data via MCP tools."""

    @allure.title("AC #7: import_data with format=firebase_csv works via MCP")
    def test_mcp_import_firebase_csv(
        self,
        code_repo,
        category_repo,
        segment_repo,
        source_repo,
        case_repo,
        event_bus,
        tmp_path,
    ):
        tools = _make_tools(
            code_repo, category_repo, segment_repo, source_repo, case_repo, event_bus
        )

        csv_path = tmp_path / "firebase_profiles.csv"
        csv_path.write_text(
            "participant_id,sessions,engagement_tier\n"
            "user_001,12,power_user\n"
            "user_002,3,regular\n"
        )

        result = tools.execute(
            "import_data",
            {
                "format": "firebase_csv",
                "source_path": str(csv_path),
                "name_column": "participant_id",
            },
        )

        assert result["success"] is True

        cases = case_repo.get_all()
        assert len(cases) == 2

    @allure.title("AC #7: import_data tool lists firebase_csv as supported format")
    def test_mcp_tool_schema_includes_firebase(
        self,
        code_repo,
        category_repo,
        segment_repo,
        source_repo,
        case_repo,
        event_bus,
    ):
        tools = _make_tools(
            code_repo, category_repo, segment_repo, source_repo, case_repo, event_bus
        )

        schemas = tools.get_tool_schemas()
        import_tool = next(s for s in schemas if s["name"] == "import_data")
        format_param = import_tool["inputSchema"]["properties"]["format"]
        assert "firebase_csv" in format_param["description"]


@allure.story("QC-051.01 SurveyCSVImported Event Tracks Merges")
class TestImportEventCounts:
    """Import events should distinguish created vs updated cases."""

    @allure.title("Import event includes cases_updated count")
    def test_import_event_has_updated_count(
        self, case_repo, event_bus, tmp_path
    ):
        from src.contexts.cases.core.entities import (
            AttributeType,
            Case,
            CaseAttribute,
        )
        from src.contexts.exchange.core.commands import ImportSurveyCSVCommand
        from src.contexts.exchange.core.commandHandlers.import_survey_csv import (
            import_survey_csv,
        )
        from src.shared import CaseId

        # Pre-create one case
        existing = Case(
            id=CaseId.new(),
            name="user_001",
            attributes=(
                CaseAttribute(name="role", attr_type=AttributeType.TEXT, value="admin"),
            ),
        )
        case_repo.save(existing)

        csv_path = tmp_path / "profiles.csv"
        csv_path.write_text(
            "participant_id,sessions\n"
            "user_001,12\n"
            "user_002,3\n"
        )

        result = import_survey_csv(
            command=ImportSurveyCSVCommand(
                source_path=str(csv_path),
                name_column="participant_id",
            ),
            case_repo=case_repo,
            event_bus=event_bus,
        )

        assert result.is_success
        event_data = result.data
        assert event_data.cases_created == 1
        assert event_data.cases_updated == 1
