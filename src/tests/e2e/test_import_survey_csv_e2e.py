"""
QC-039.06: Import Survey CSV - E2E Tests

TDD: Tests written FIRST, before implementation.

Tests verify importing a CSV file creates cases with attributes.
"""

from __future__ import annotations

import allure
import pytest

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-039 Import Export Formats"),
]


@allure.story("QC-039.06 Import Survey CSV")
class TestImportSurveyCSV:
    @allure.title("AC #1+#2: Import CSV creates cases with attributes and publishes event")
    def test_import_csv_creates_cases_with_attributes_and_event(self, case_repo, event_bus, tmp_path):
        from src.contexts.exchange.core.commandHandlers.import_survey_csv import (
            import_survey_csv,
        )
        from src.contexts.exchange.core.commands import ImportSurveyCSVCommand
        from src.contexts.exchange.core.events import SurveyCSVImported

        published = []
        event_bus.subscribe("exchange.survey_csv_imported", published.append)

        csv_file = tmp_path / "survey.csv"
        csv_file.write_text("Name,Age,Gender\nAlice,30,F\nBob,25,M\n")

        with allure.step("Import CSV"):
            result = import_survey_csv(
                command=ImportSurveyCSVCommand(source_path=str(csv_file)),
                case_repo=case_repo,
                event_bus=event_bus,
            )

        with allure.step("Verify success"):
            assert result.is_success, f"Import failed: {result.error}"

        with allure.step("Verify cases created"):
            cases = case_repo.get_all()
            case_names = {c.name for c in cases}
            assert "Alice" in case_names
            assert "Bob" in case_names

        with allure.step("Verify attributes"):
            alice = case_repo.get_by_name("Alice")
            assert alice is not None
            age_attr = alice.get_attribute("Age")
            assert age_attr is not None
            assert age_attr.value == "30"
            gender_attr = alice.get_attribute("Gender")
            assert gender_attr is not None
            assert gender_attr.value == "F"

        with allure.step("Verify event"):
            assert len(published) == 1
            event = published[0]
            assert isinstance(event, SurveyCSVImported)
            assert event.cases_created == 2

    @allure.title("AC #3: Import uses custom name column")
    def test_ac3_custom_name_column(self, case_repo, event_bus, tmp_path):
        from src.contexts.exchange.core.commandHandlers.import_survey_csv import (
            import_survey_csv,
        )
        from src.contexts.exchange.core.commands import ImportSurveyCSVCommand

        csv_file = tmp_path / "survey.csv"
        csv_file.write_text("ID,Participant,Score\n1,Alice,85\n2,Bob,92\n")

        import_survey_csv(
            command=ImportSurveyCSVCommand(
                source_path=str(csv_file),
                name_column="Participant",
            ),
            case_repo=case_repo,
            event_bus=event_bus,
        )

        with allure.step("Verify cases named from Participant column"):
            cases = case_repo.get_all()
            case_names = {c.name for c in cases}
            assert "Alice" in case_names
            assert "Bob" in case_names

    @allure.title("Import fails with empty CSV or nonexistent file")
    def test_fails_invalid_input(self, case_repo, event_bus, tmp_path):
        from src.contexts.exchange.core.commandHandlers.import_survey_csv import (
            import_survey_csv,
        )
        from src.contexts.exchange.core.commands import ImportSurveyCSVCommand

        with allure.step("Verify failure with empty CSV"):
            csv_file = tmp_path / "empty.csv"
            csv_file.write_text("")

            result = import_survey_csv(
                command=ImportSurveyCSVCommand(source_path=str(csv_file)),
                case_repo=case_repo,
                event_bus=event_bus,
            )
            assert result.is_failure
            assert "EMPTY" in result.error_code

        with allure.step("Verify failure with nonexistent file"):
            result = import_survey_csv(
                command=ImportSurveyCSVCommand(source_path=str(tmp_path / "missing.csv")),
                case_repo=case_repo,
                event_bus=event_bus,
            )
            assert result.is_failure
            assert "FILE_NOT_FOUND" in result.error_code
