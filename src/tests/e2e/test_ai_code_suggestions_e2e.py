"""
QC-028.07 & QC-028.08: AI Code Suggestions E2E Tests (TDD)

Test-Driven Development tests for AI-assisted code management:
- QC-028.07: Agent Suggest New Code
- QC-028.08: Agent Detect Duplicate Codes

These tests define the expected behavior BEFORE implementation.
Run with: QT_QPA_PLATFORM=offscreen uv run pytest src/tests/e2e/test_ai_code_suggestions_e2e.py -v
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import allure
import pytest

if TYPE_CHECKING:
    from pathlib import Path

    from src.contexts.coding.interface.mcp_tools import CodingTools
    from src.shared.infra.app_context import AppContext

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-028 Code Management"),
]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def project_with_codes(app_context: AppContext, tmp_path: Path) -> Path:
    """Create a project with sample codes for AI analysis."""
    from src.contexts.coding.core.entities import Category, Code, Color
    from src.shared.common.types import CategoryId, CodeId

    project_path = tmp_path / "ai_codes_test.qda"
    result = app_context.create_project(name="AI Codes Test", path=str(project_path))
    assert result.is_success
    app_context.open_project(str(project_path))

    # Add sample codes
    codes = [
        Code(
            id=CodeId("1"),
            name="Theme",
            color=Color.from_hex("#FF5722"),
            memo="Main themes",
        ),
        Code(
            id=CodeId("2"),
            name="Themes",
            color=Color.from_hex("#FF9800"),
            memo="Alternative themes",
        ),
        Code(
            id=CodeId("3"),
            name="Positive Emotion",
            color=Color.from_hex("#4CAF50"),
            memo="Happy feelings",
        ),
        Code(
            id=CodeId("4"),
            name="Positive Feeling",
            color=Color.from_hex("#8BC34A"),
            memo="Good feelings",
        ),
        Code(
            id=CodeId("5"),
            name="Challenge",
            color=Color.from_hex("#F44336"),
            memo="Difficulties",
        ),
        Code(
            id=CodeId("6"),
            name="Learning",
            color=Color.from_hex("#2196F3"),
            memo="Education related",
        ),
    ]
    for code in codes:
        app_context.coding_context.code_repo.save(code)

    # Add a category
    category = Category(id=CategoryId("1"), name="Emotions", memo="Emotional codes")
    app_context.coding_context.category_repo.save(category)

    return project_path


@pytest.fixture
def project_with_uncoded_content(app_context: AppContext, tmp_path: Path) -> Path:
    """Create a project with uncoded text content for AI suggestion testing."""
    from src.contexts.coding.core.entities import Code, Color
    from src.contexts.projects.core.entities import Source, SourceType
    from src.shared.common.types import CodeId, SourceId

    project_path = tmp_path / "ai_suggest_test.qda"
    result = app_context.create_project(name="AI Suggest Test", path=str(project_path))
    assert result.is_success
    app_context.open_project(str(project_path))

    # Add a source with uncoded content
    source = Source(
        id=SourceId("1"),
        name="interview_01.txt",
        source_type=SourceType.TEXT,
        fulltext="""
        Interview Transcript - Participant 01

        Q: Tell me about your learning experience.
        A: I found the course very challenging but rewarding. The learning process
        was intense, especially the first few weeks. I experienced moments of
        frustration when things didn't click, but also moments of joy when I
        finally understood a concept.

        Q: What was most difficult?
        A: Time management was a major challenge. Balancing work and study
        required significant adjustment. Some topics were particularly hard,
        like the advanced statistics module.

        Q: What did you enjoy most?
        A: The collaborative learning with peers was fantastic. I felt a sense
        of achievement when completing projects. The positive atmosphere in
        class really helped my motivation.
        """,
    )
    app_context.sources_context.source_repo.save(source)

    # Add a few existing codes
    codes = [
        Code(id=CodeId("1"), name="Challenge", color=Color.from_hex("#F44336")),
        Code(id=CodeId("2"), name="Achievement", color=Color.from_hex("#4CAF50")),
    ]
    for code in codes:
        app_context.coding_context.code_repo.save(code)

    return project_path


# =============================================================================
# QC-028.07: Agent Suggest New Code
# =============================================================================


@allure.story("QC-028.07 Agent Suggest New Code")
@allure.severity(allure.severity_level.CRITICAL)
class TestAgentSuggestNewCode:
    """
    QC-028.07: Suggest New Code
    As an AI Agent, I want to suggest new codes so that I can help build the coding scheme.
    """

    @allure.title("AC #1-2: Agent analyzes uncoded content and proposes new code")
    def test_ac1_ac2_analyze_and_propose(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        project_with_uncoded_content: Path,
    ):
        """Agent can analyze uncoded content and propose a new code with details."""

        with allure.step("Analyze uncoded content for potential codes"):
            result = coding_tools.execute(
                "analyze_content_for_codes",
                {"source_id": 1},
            )

        with allure.step("Verify analysis returned"):
            assert result.get("success") is True
            data = result["data"]
            assert "uncoded_segments" in data or "analysis" in data
            assert data.get("source_id") == 1

        with allure.step("Propose new code"):
            result = coding_tools.execute(
                "suggest_new_code",
                {
                    "name": "Learning Experience",
                    "color": "#2196F3",
                    "description": "Passages related to learning and educational experiences",
                    "rationale": "Multiple participants discuss learning processes",
                    "confidence": 85,
                    "sample_contexts": [
                        "I found the course very challenging but rewarding",
                        "The learning process was intense",
                    ],
                },
            )

        with allure.step("Verify suggestion created"):
            assert result.get("success") is True
            data = result["data"]
            assert data["status"] == "pending_approval"
            assert "suggestion_id" in data
            assert data["name"] == "Learning Experience"

    @allure.title("AC #3: Suggestion includes rationale and confidence score")
    def test_ac3_rationale_and_confidence(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        project_with_uncoded_content: Path,
    ):
        """Code suggestions include rationale and confidence score (0-100)."""

        with allure.step("Submit suggestion with rationale"):
            result = coding_tools.execute(
                "suggest_new_code",
                {
                    "name": "Time Management",
                    "color": "#FF9800",
                    "description": "References to managing time",
                    "rationale": "Several interview segments mention time management challenges",
                    "confidence": 72,
                },
            )

        with allure.step("Verify rationale and confidence"):
            assert result.get("success") is True
            data = result["data"]
            assert "rationale" in data
            assert "time management" in data["rationale"].lower()
            assert "confidence" in data
            assert 0 <= data["confidence"] <= 100
            assert data["confidence"] == 72

    @allure.title("AC #4: Researcher approval required, and pending list works")
    def test_ac4_approval_and_pending_list(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        project_with_uncoded_content: Path,
    ):
        """Suggested codes require approval and can be listed as pending."""

        with allure.step("Submit code suggestions"):
            result = coding_tools.execute(
                "suggest_new_code",
                {
                    "name": "Code A",
                    "color": "#FF0000",
                    "description": "Collaborative learning references",
                    "rationale": "Peer collaboration mentioned",
                    "confidence": 80,
                },
            )

        with allure.step("Verify suggestion is pending, not created"):
            assert result.get("success") is True
            data = result["data"]
            assert data["status"] == "pending_approval"
            assert data["requires_approval"] is True

        with allure.step("Verify code NOT in repository yet"):
            codes = app_context.coding_context.code_repo.get_all()
            code_names = [c.name for c in codes]
            assert "Code A" not in code_names

        with allure.step("Submit second suggestion"):
            coding_tools.execute(
                "suggest_new_code",
                {
                    "name": "Code B",
                    "color": "#00FF00",
                    "rationale": "Test",
                    "confidence": 80,
                },
            )

        with allure.step("List pending suggestions"):
            result = coding_tools.execute("list_pending_suggestions", {})

        with allure.step("Verify pending suggestions returned"):
            assert result.get("success") is True
            data = result["data"]
            assert data["count"] >= 2
            names = [s["name"] for s in data["suggestions"]]
            assert "Code A" in names
            assert "Code B" in names


# =============================================================================
# QC-028.08: Agent Detect Duplicate Codes
# =============================================================================


@allure.story("QC-028.08 Agent Detect Duplicate Codes")
@allure.severity(allure.severity_level.CRITICAL)
class TestAgentDetectDuplicateCodes:
    """
    QC-028.08: Detect Duplicate Codes
    As an AI Agent, I want to detect duplicate codes so that I can help consolidate the scheme.
    """

    @allure.title("AC #1-2: Identify similar codes and suggest merge candidates")
    def test_ac1_ac2_identify_and_suggest_merge(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        project_with_codes: Path,
    ):
        """Agent detects semantically similar codes and suggests merge candidates."""

        with allure.step("Detect duplicate codes"):
            result = coding_tools.execute(
                "detect_duplicate_codes",
                {"threshold": 0.7},
            )

        with allure.step("Verify duplicates detected"):
            assert result.get("success") is True
            data = result["data"]
            assert "candidates" in data
            assert len(data["candidates"]) > 0

        with allure.step("Verify Theme/Themes pair detected"):
            pairs = [(c["code_a_name"], c["code_b_name"]) for c in data["candidates"]]
            theme_pair_found = any(("Theme" in a and "Theme" in b) for a, b in pairs)
            assert theme_pair_found

        with allure.step("Verify merge suggestions include both code IDs"):
            for candidate in data["candidates"]:
                assert "code_a_id" in candidate
                assert "code_b_id" in candidate
                assert "similarity" in candidate
                assert candidate["similarity"] >= 70

    @allure.title(
        "AC #3-4: Detection considers names/usage and requires researcher approval"
    )
    def test_ac3_ac4_rationale_and_approval(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        project_with_codes: Path,
    ):
        """Detection includes rationale and does not auto-merge."""

        with allure.step("Get initial code count"):
            initial_codes = app_context.coding_context.code_repo.get_all()
            initial_count = len(initial_codes)

        with allure.step("Detect duplicates with analysis"):
            result = coding_tools.execute(
                "detect_duplicate_codes",
                {"threshold": 0.6, "include_usage_analysis": True},
            )

        with allure.step("Verify analysis includes rationale"):
            assert result.get("success") is True
            data = result["data"]
            for candidate in data["candidates"]:
                assert "rationale" in candidate
                assert len(candidate["rationale"]) > 0

        with allure.step("Verify codes NOT merged automatically"):
            codes = app_context.coding_context.code_repo.get_all()
            assert len(codes) == initial_count

        with allure.step("Verify result indicates approval required"):
            assert data["requires_approval"] is True

    @allure.title("Similarity scores, segment counts, and merge request")
    @allure.severity(allure.severity_level.NORMAL)
    def test_scores_segments_and_merge_request(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        project_with_codes: Path,
    ):
        """Duplicate pairs include scores/counts, and agent can request merge."""

        with allure.step("Detect duplicates"):
            result = coding_tools.execute("detect_duplicate_codes", {"threshold": 0.5})

        with allure.step("Verify similarity scores and segment counts"):
            assert result.get("success") is True
            data = result["data"]
            for candidate in data["candidates"]:
                assert "similarity" in candidate
                assert 0 <= candidate["similarity"] <= 100
                assert "code_a_segments" in candidate
                assert "code_b_segments" in candidate
                assert isinstance(candidate["code_a_segments"], int)
                assert isinstance(candidate["code_b_segments"], int)

        with allure.step("Request merge"):
            result = coding_tools.execute(
                "suggest_merge_codes",
                {
                    "source_code_id": 1,  # Theme
                    "target_code_id": 2,  # Themes
                    "rationale": "These codes represent the same concept",
                },
            )

        with allure.step("Verify merge suggestion created"):
            assert result.get("success") is True
            data = result["data"]
            assert data["status"] == "pending_approval"
            assert data["merge_source_id"] == 1
            assert data["merge_target_id"] == 2


# =============================================================================
# Integration Tests
# =============================================================================


@allure.story("QC-028 AI Code Management Integration")
@allure.severity(allure.severity_level.CRITICAL)
class TestAICodeManagementIntegration:
    """Integration tests for AI code management workflows."""

    @allure.title("Complete workflow: Analyze -> Suggest -> Approve -> Create")
    def test_full_suggestion_workflow(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        project_with_uncoded_content: Path,
    ):
        """Test complete workflow from analysis to code creation."""
        with allure.step("Step 1: Analyze content for potential codes"):
            analysis = coding_tools.execute(
                "analyze_content_for_codes", {"source_id": 1}
            )
            assert analysis.get("success") is True

        with allure.step("Step 2: Suggest a new code based on analysis"):
            suggestion = coding_tools.execute(
                "suggest_new_code",
                {
                    "name": "Frustration",
                    "color": "#F44336",
                    "description": "Expressions of frustration",
                    "rationale": "Participant mentions frustration when learning",
                    "confidence": 85,
                },
            )
            assert suggestion.get("success") is True
            suggestion_id = suggestion["data"]["suggestion_id"]

        with allure.step("Step 3: Verify suggestion is pending"):
            pending = coding_tools.execute("list_pending_suggestions", {})
            assert pending.get("success") is True
            ids = [s["suggestion_id"] for s in pending["data"]["suggestions"]]
            assert suggestion_id in ids

        with allure.step("Step 4: Approve suggestion (simulated researcher action)"):
            approval = coding_tools.execute(
                "approve_suggestion",
                {"suggestion_id": suggestion_id},
            )
            assert approval.get("success") is True
            assert approval["data"]["status"] == "created"

        with allure.step("Step 5: Verify code now exists"):
            codes = app_context.coding_context.code_repo.get_all()
            code_names = [c.name for c in codes]
            assert "Frustration" in code_names

    @allure.title("Complete workflow: Detect duplicates -> Review -> Merge")
    def test_full_duplicate_workflow(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        project_with_codes: Path,
    ):
        """Test complete workflow from detection to merge."""
        with allure.step("Step 1: Detect duplicate codes"):
            detection = coding_tools.execute(
                "detect_duplicate_codes", {"threshold": 0.8}
            )
            assert detection.get("success") is True
            candidates = detection["data"]["candidates"]
            assert len(candidates) > 0

        with allure.step("Step 2: Suggest merge for a detected pair"):
            pair = candidates[0]
            merge_suggestion = coding_tools.execute(
                "suggest_merge_codes",
                {
                    "source_code_id": pair["code_a_id"],
                    "target_code_id": pair["code_b_id"],
                    "rationale": pair["rationale"],
                },
            )
            assert merge_suggestion.get("success") is True
            merge_id = merge_suggestion["data"]["merge_suggestion_id"]

        with allure.step("Step 3: Approve merge"):
            approval = coding_tools.execute(
                "approve_merge",
                {"merge_suggestion_id": merge_id},
            )
            assert approval.get("success") is True

        with allure.step("Step 4: Verify merge completed"):
            codes = app_context.coding_context.code_repo.get_all()
            # One of the codes should be gone
            initial_count = 6
            assert len(codes) == initial_count - 1


# =============================================================================
# MCP Tool Schema Tests
# =============================================================================


@allure.story("QC-028 AI Tools Schema Validation")
@allure.severity(allure.severity_level.NORMAL)
class TestAIToolsSchema:
    """Tests to verify MCP tool schemas are correctly defined."""

    @allure.title("All AI coding tools have correct schemas")
    def test_all_ai_tool_schemas(
        self, coding_tools: CodingTools, app_context: AppContext
    ):
        """Verify schemas for suggest_new_code, detect_duplicate_codes, list_codes, and create_code."""

        with allure.step("Get tool schemas"):
            schemas = coding_tools.get_tool_schemas()
            schema_map = {s["name"]: s for s in schemas}

        with allure.step("Verify suggest_new_code schema"):
            schema = schema_map.get("suggest_new_code")
            assert schema is not None
            required = schema["inputSchema"]["required"]
            assert "name" in required
            assert "rationale" in required
            props = schema["inputSchema"]["properties"]
            assert "color" in props
            assert "description" in props
            assert "confidence" in props
            assert "sample_contexts" in props

        with allure.step("Verify detect_duplicate_codes schema"):
            schema = schema_map.get("detect_duplicate_codes")
            assert schema is not None
            props = schema["inputSchema"]["properties"]
            assert "threshold" in props
            assert props["threshold"]["type"] in ("number", "integer")

        with allure.step("Verify list_codes schema"):
            schema = schema_map.get("list_codes")
            assert schema is not None
            required = schema["inputSchema"].get("required", [])
            assert len(required) == 0

        with allure.step("Verify create_code schema"):
            schema = schema_map.get("create_code")
            assert schema is not None
            required = schema["inputSchema"]["required"]
            assert "name" in required
            assert "color" in required
            props = schema["inputSchema"]["properties"]
            assert "memo" in props
            assert "category_id" in props


# =============================================================================
# QC-028.07: Agent List All Codes
# =============================================================================


@allure.story("QC-028.07 Agent List All Codes")
@allure.severity(allure.severity_level.CRITICAL)
class TestAgentListCodes:
    """
    QC-028.07: Agent List All Codes
    As an AI Agent, I want to list all codes so I can understand the coding scheme.
    """

    @allure.title(
        "AC #1-4: List all codes with required fields, memo, and empty project"
    )
    def test_list_codes_full(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        project_with_codes: Path,
        tmp_path: Path,
    ):
        """Agent can list codes with id/name/color/memo, and empty project returns empty list."""

        with allure.step("List all codes"):
            result = coding_tools.execute("list_codes", {})

        with allure.step("Verify codes returned with required fields"):
            assert result.get("success") is True
            data = result["data"]
            assert isinstance(data, list)
            assert len(data) == 6  # We created 6 codes in fixture

            for code in data:
                assert "id" in code
                assert "name" in code
                assert "color" in code
                assert isinstance(code["id"], str)
                assert isinstance(code["name"], str)
                assert isinstance(code["color"], str)
                assert code["color"].startswith("#")
                assert "memo" in code
                assert code["memo"] is None or isinstance(code["memo"], str)

        with allure.step("Create empty project"):
            app_context.close_project()
            project_path = tmp_path / "empty_codes_test.qda"
            result = app_context.create_project(
                name="Empty Codes Test", path=str(project_path)
            )
            assert result.is_success
            app_context.open_project(str(project_path))

        with allure.step("List codes on empty project"):
            result = coding_tools.execute("list_codes", {})

        with allure.step("Verify empty list returned"):
            assert result.get("success") is True
            assert result["data"] == []


# =============================================================================
# QC-028.10: Agent Create Code
# =============================================================================


@allure.story("QC-028.10 Agent Create Code")
@allure.severity(allure.severity_level.CRITICAL)
class TestAgentCreateCode:
    """
    QC-028.10: Agent Create Code
    As an AI Agent, I want to create codes directly so I can build the coding scheme.
    """

    @allure.title(
        "AC #1-3: Create code with name, color, and optional memo; verify persistence"
    )
    def test_create_code_with_memo_and_persistence(
        self, coding_tools: CodingTools, app_context: AppContext, tmp_path: Path
    ):
        """Agent can create a code with required fields and optional memo, and it persists."""

        with allure.step("Create project"):
            project_path = tmp_path / "create_code_test.qda"
            result = app_context.create_project(
                name="Create Code Test", path=str(project_path)
            )
            assert result.is_success
            app_context.open_project(str(project_path))

        with allure.step("Create code with memo"):
            result = coding_tools.execute(
                "create_code",
                {
                    "name": "New Theme",
                    "color": "#FF5722",
                    "memo": "This code captures positive user experiences.",
                },
            )

        with allure.step("Verify code created with correct fields"):
            assert result.get("success") is True
            data = result["data"]
            assert data["name"] == "New Theme"
            assert data["color"].lower() == "#ff5722"
            assert "code_id" in data
            assert isinstance(data["code_id"], str)
            assert data["memo"] == "This code captures positive user experiences."

        with allure.step("Verify code exists in repository"):
            codes = app_context.coding_context.code_repo.get_all()
            code_names = [c.name for c in codes]
            assert "New Theme" in code_names

    @allure.title("AC #4: Create code in a category")
    def test_code_with_category(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        project_with_codes: Path,
    ):
        """Agent can create a code in a specific category."""

        with allure.step("Create code in category"):
            result = coding_tools.execute(
                "create_code",
                {
                    "name": "Categorized Code",
                    "color": "#9C27B0",
                    "category_id": 1,  # Emotions category from fixture
                },
            )

        with allure.step("Verify category assignment"):
            assert result.get("success") is True
            data = result["data"]
            assert data["category_id"] == "1"

    @allure.title("AC #5-7: Invalid color and missing params return errors")
    def test_error_cases(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        tmp_path: Path,
    ):
        """Creating code with invalid color or missing params returns error."""

        with allure.step("Create project for invalid color test"):
            project_path = tmp_path / "error_test.qda"
            result = app_context.create_project(
                name="Error Test", path=str(project_path)
            )
            assert result.is_success
            app_context.open_project(str(project_path))

        with allure.step("Attempt to create code with invalid color"):
            result = coding_tools.execute(
                "create_code",
                {"name": "Bad Color", "color": "not-a-color"},
            )

        with allure.step("Verify error returned for invalid color"):
            assert result.get("success") is False
            assert "error" in result
            assert "INVALID_COLOR" in result.get("error_code", "")

        with allure.step("Attempt to create code without name"):
            result = coding_tools.execute(
                "create_code",
                {"color": "#FF0000"},  # Missing name
            )

        with allure.step("Verify error for missing name"):
            assert result.get("success") is False
            assert "name" in result.get("error", "").lower()

        with allure.step("Attempt to create code without color"):
            result = coding_tools.execute(
                "create_code",
                {"name": "No Color Code"},  # Missing color
            )

        with allure.step("Verify error for missing color"):
            assert result.get("success") is False
            assert "color" in result.get("error", "").lower()
