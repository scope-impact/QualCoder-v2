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
from returns.result import Failure, Success

if TYPE_CHECKING:
    from pathlib import Path

    from src.shared.infra.app_context import AppContext

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-028 Code Management - AI Features"),
]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def app_context():
    """Create AppContext for testing."""
    from src.shared.infra.app_context import create_app_context

    ctx = create_app_context()
    ctx.start()
    yield ctx
    ctx.stop()


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
        Code(id=CodeId(1), name="Theme", color=Color.from_hex("#FF5722"), memo="Main themes"),
        Code(id=CodeId(2), name="Themes", color=Color.from_hex("#FF9800"), memo="Alternative themes"),
        Code(id=CodeId(3), name="Positive Emotion", color=Color.from_hex("#4CAF50"), memo="Happy feelings"),
        Code(id=CodeId(4), name="Positive Feeling", color=Color.from_hex("#8BC34A"), memo="Good feelings"),
        Code(id=CodeId(5), name="Challenge", color=Color.from_hex("#F44336"), memo="Difficulties"),
        Code(id=CodeId(6), name="Learning", color=Color.from_hex("#2196F3"), memo="Education related"),
    ]
    for code in codes:
        app_context.coding_context.code_repo.save(code)

    # Add a category
    category = Category(id=CategoryId(1), name="Emotions", memo="Emotional codes")
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
        id=SourceId(1),
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
        Code(id=CodeId(1), name="Challenge", color=Color.from_hex("#F44336")),
        Code(id=CodeId(2), name="Achievement", color=Color.from_hex("#4CAF50")),
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

    @allure.title("AC #1: Agent can analyze uncoded content")
    def test_ac1_analyze_uncoded_content(
        self, app_context: AppContext, project_with_uncoded_content: Path
    ):
        """Agent can analyze text content that has not been coded."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Initialize CodingTools"):
            tools = CodingTools(ctx=app_context)

        with allure.step("Analyze uncoded content for potential codes"):
            result = tools.execute(
                "analyze_content_for_codes",
                {"source_id": 1},
            )

        with allure.step("Verify analysis returned"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert "uncoded_segments" in data or "analysis" in data
            assert data.get("source_id") == 1

    @allure.title("AC #2: Agent can propose new code with name and description")
    def test_ac2_propose_new_code(
        self, app_context: AppContext, project_with_uncoded_content: Path
    ):
        """Agent can propose a new code with name, color, and description."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Initialize CodingTools"):
            tools = CodingTools(ctx=app_context)

        with allure.step("Propose new code"):
            result = tools.execute(
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
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["status"] == "pending_approval"
            assert "suggestion_id" in data
            assert data["name"] == "Learning Experience"

    @allure.title("AC #3: Suggestion includes rationale")
    def test_ac3_suggestion_includes_rationale(
        self, app_context: AppContext, project_with_uncoded_content: Path
    ):
        """Code suggestions include rationale explaining why the code is needed."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Submit suggestion with rationale"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute(
                "suggest_new_code",
                {
                    "name": "Time Management",
                    "color": "#FF9800",
                    "description": "References to managing time",
                    "rationale": "Several interview segments mention time management challenges",
                    "confidence": 72,
                },
            )

        with allure.step("Verify rationale is included in suggestion"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert "rationale" in data
            assert "time management" in data["rationale"].lower()

    @allure.title("AC #4: Researcher must approve before creation")
    def test_ac4_researcher_approval_required(
        self, app_context: AppContext, project_with_uncoded_content: Path
    ):
        """Suggested codes are not created until researcher approves."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Submit code suggestion"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute(
                "suggest_new_code",
                {
                    "name": "Collaboration",
                    "color": "#9C27B0",
                    "description": "Collaborative learning references",
                    "rationale": "Peer collaboration mentioned",
                    "confidence": 80,
                },
            )

        with allure.step("Verify suggestion is pending, not created"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["status"] == "pending_approval"
            assert data["requires_approval"] is True

        with allure.step("Verify code NOT in repository yet"):
            codes = app_context.coding_context.code_repo.get_all()
            code_names = [c.name for c in codes]
            assert "Collaboration" not in code_names

    @allure.title("Agent can list pending code suggestions")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_pending_suggestions(
        self, app_context: AppContext, project_with_uncoded_content: Path
    ):
        """Agent can retrieve list of pending code suggestions."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Submit multiple suggestions"):
            tools = CodingTools(ctx=app_context)
            tools.execute(
                "suggest_new_code",
                {"name": "Code A", "color": "#FF0000", "rationale": "Test", "confidence": 70},
            )
            tools.execute(
                "suggest_new_code",
                {"name": "Code B", "color": "#00FF00", "rationale": "Test", "confidence": 80},
            )

        with allure.step("List pending suggestions"):
            result = tools.execute("list_pending_suggestions", {})

        with allure.step("Verify pending suggestions returned"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["count"] >= 2
            names = [s["name"] for s in data["suggestions"]]
            assert "Code A" in names
            assert "Code B" in names

    @allure.title("Suggestion includes confidence score")
    @allure.severity(allure.severity_level.NORMAL)
    def test_suggestion_confidence_score(
        self, app_context: AppContext, project_with_uncoded_content: Path
    ):
        """Code suggestions include confidence score (0-100)."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Submit suggestion with confidence"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute(
                "suggest_new_code",
                {
                    "name": "High Confidence Code",
                    "color": "#4CAF50",
                    "rationale": "Strong evidence",
                    "confidence": 95,
                },
            )

        with allure.step("Verify confidence score in response"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert "confidence" in data
            assert 0 <= data["confidence"] <= 100
            assert data["confidence"] == 95


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

    @allure.title("AC #1: Agent can identify semantically similar codes")
    def test_ac1_identify_similar_codes(
        self, app_context: AppContext, project_with_codes: Path
    ):
        """Agent can detect codes that are semantically similar."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Initialize CodingTools"):
            tools = CodingTools(ctx=app_context)

        with allure.step("Detect duplicate codes"):
            result = tools.execute(
                "detect_duplicate_codes",
                {"threshold": 0.8},  # 80% similarity threshold
            )

        with allure.step("Verify duplicates detected"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert "candidates" in data
            assert len(data["candidates"]) > 0

        with allure.step("Verify Theme/Themes pair detected"):
            pairs = [(c["code_a_name"], c["code_b_name"]) for c in data["candidates"]]
            # Either order is valid
            theme_pair_found = any(
                ("Theme" in a and "Theme" in b) for a, b in pairs
            )
            assert theme_pair_found

    @allure.title("AC #2: Agent can suggest merge candidates")
    def test_ac2_suggest_merge_candidates(
        self, app_context: AppContext, project_with_codes: Path
    ):
        """Agent can suggest which codes should be merged."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Detect duplicates"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute("detect_duplicate_codes", {"threshold": 0.7})

        with allure.step("Verify merge suggestions include both code IDs"):
            assert isinstance(result, Success)
            data = result.unwrap()
            for candidate in data["candidates"]:
                assert "code_a_id" in candidate
                assert "code_b_id" in candidate
                assert "similarity" in candidate
                assert candidate["similarity"] >= 70

    @allure.title("AC #3: Detection considers code names and usage")
    def test_ac3_considers_names_and_usage(
        self, app_context: AppContext, project_with_codes: Path
    ):
        """Detection considers both code names and how codes are used."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Detect duplicates with analysis"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute(
                "detect_duplicate_codes",
                {"threshold": 0.6, "include_usage_analysis": True},
            )

        with allure.step("Verify analysis includes rationale"):
            assert isinstance(result, Success)
            data = result.unwrap()
            for candidate in data["candidates"]:
                assert "rationale" in candidate
                # Rationale should explain why they're similar
                assert len(candidate["rationale"]) > 0

    @allure.title("AC #4: Researcher decides on merge actions")
    def test_ac4_researcher_decides_merge(
        self, app_context: AppContext, project_with_codes: Path
    ):
        """Detected duplicates are not merged automatically - researcher decides."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Get initial code count"):
            initial_codes = app_context.coding_context.code_repo.get_all()
            initial_count = len(initial_codes)

        with allure.step("Detect duplicates"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute("detect_duplicate_codes", {"threshold": 0.8})
            assert isinstance(result, Success)

        with allure.step("Verify codes NOT merged automatically"):
            codes = app_context.coding_context.code_repo.get_all()
            assert len(codes) == initial_count

        with allure.step("Verify result indicates approval required"):
            data = result.unwrap()
            assert data["requires_approval"] is True

    @allure.title("Detection returns similarity scores")
    @allure.severity(allure.severity_level.NORMAL)
    def test_similarity_scores_returned(
        self, app_context: AppContext, project_with_codes: Path
    ):
        """Each duplicate pair includes a similarity score."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Detect duplicates"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute("detect_duplicate_codes", {"threshold": 0.5})

        with allure.step("Verify similarity scores"):
            assert isinstance(result, Success)
            data = result.unwrap()
            for candidate in data["candidates"]:
                assert "similarity" in candidate
                assert 0 <= candidate["similarity"] <= 100

    @allure.title("Detection shows segment counts for merge decision")
    @allure.severity(allure.severity_level.NORMAL)
    def test_shows_segment_counts(
        self, app_context: AppContext, project_with_codes: Path
    ):
        """Detection results show segment counts to help merge decision."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Detect duplicates"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute("detect_duplicate_codes", {"threshold": 0.7})

        with allure.step("Verify segment counts included"):
            assert isinstance(result, Success)
            data = result.unwrap()
            for candidate in data["candidates"]:
                assert "code_a_segments" in candidate
                assert "code_b_segments" in candidate
                assert isinstance(candidate["code_a_segments"], int)
                assert isinstance(candidate["code_b_segments"], int)

    @allure.title("Agent can request merge after detection")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_request_merge(self, app_context: AppContext, project_with_codes: Path):
        """Agent can request a merge operation (still requires approval)."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Request merge"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute(
                "suggest_merge_codes",
                {
                    "source_code_id": 1,  # Theme
                    "target_code_id": 2,  # Themes
                    "rationale": "These codes represent the same concept",
                },
            )

        with allure.step("Verify merge suggestion created"):
            assert isinstance(result, Success)
            data = result.unwrap()
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
        self, app_context: AppContext, project_with_uncoded_content: Path
    ):
        """Test complete workflow from analysis to code creation."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        tools = CodingTools(ctx=app_context)

        with allure.step("Step 1: Analyze content for potential codes"):
            analysis = tools.execute("analyze_content_for_codes", {"source_id": 1})
            assert isinstance(analysis, Success)

        with allure.step("Step 2: Suggest a new code based on analysis"):
            suggestion = tools.execute(
                "suggest_new_code",
                {
                    "name": "Frustration",
                    "color": "#F44336",
                    "description": "Expressions of frustration",
                    "rationale": "Participant mentions frustration when learning",
                    "confidence": 85,
                },
            )
            assert isinstance(suggestion, Success)
            suggestion_id = suggestion.unwrap()["suggestion_id"]

        with allure.step("Step 3: Verify suggestion is pending"):
            pending = tools.execute("list_pending_suggestions", {})
            assert isinstance(pending, Success)
            ids = [s["suggestion_id"] for s in pending.unwrap()["suggestions"]]
            assert suggestion_id in ids

        with allure.step("Step 4: Approve suggestion (simulated researcher action)"):
            # This would be done via UI/ViewModel, but we test the MCP interface
            approval = tools.execute(
                "approve_suggestion",
                {"suggestion_id": suggestion_id},
            )
            assert isinstance(approval, Success)
            assert approval.unwrap()["status"] == "created"

        with allure.step("Step 5: Verify code now exists"):
            codes = app_context.coding_context.code_repo.get_all()
            code_names = [c.name for c in codes]
            assert "Frustration" in code_names

    @allure.title("Complete workflow: Detect duplicates -> Review -> Merge")
    def test_full_duplicate_workflow(
        self, app_context: AppContext, project_with_codes: Path
    ):
        """Test complete workflow from detection to merge."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        tools = CodingTools(ctx=app_context)

        with allure.step("Step 1: Detect duplicate codes"):
            detection = tools.execute("detect_duplicate_codes", {"threshold": 0.8})
            assert isinstance(detection, Success)
            candidates = detection.unwrap()["candidates"]
            assert len(candidates) > 0

        with allure.step("Step 2: Suggest merge for a detected pair"):
            pair = candidates[0]
            merge_suggestion = tools.execute(
                "suggest_merge_codes",
                {
                    "source_code_id": pair["code_a_id"],
                    "target_code_id": pair["code_b_id"],
                    "rationale": pair["rationale"],
                },
            )
            assert isinstance(merge_suggestion, Success)
            merge_id = merge_suggestion.unwrap()["merge_suggestion_id"]

        with allure.step("Step 3: Approve merge"):
            approval = tools.execute(
                "approve_merge",
                {"merge_suggestion_id": merge_id},
            )
            assert isinstance(approval, Success)

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

    @allure.title("suggest_new_code tool has correct schema")
    def test_suggest_new_code_schema(self, app_context: AppContext):
        """Verify suggest_new_code tool schema."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Get tool schemas"):
            tools = CodingTools(ctx=app_context)
            schemas = tools.get_tool_schemas()

        with allure.step("Find suggest_new_code schema"):
            schema = next(
                (s for s in schemas if s["name"] == "suggest_new_code"), None
            )
            assert schema is not None

        with allure.step("Verify required parameters"):
            required = schema["inputSchema"]["required"]
            assert "name" in required
            assert "rationale" in required

        with allure.step("Verify optional parameters"):
            props = schema["inputSchema"]["properties"]
            assert "color" in props
            assert "description" in props
            assert "confidence" in props
            assert "sample_contexts" in props

    @allure.title("detect_duplicate_codes tool has correct schema")
    def test_detect_duplicate_codes_schema(self, app_context: AppContext):
        """Verify detect_duplicate_codes tool schema."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Get tool schemas"):
            tools = CodingTools(ctx=app_context)
            schemas = tools.get_tool_schemas()

        with allure.step("Find detect_duplicate_codes schema"):
            schema = next(
                (s for s in schemas if s["name"] == "detect_duplicate_codes"), None
            )
            assert schema is not None

        with allure.step("Verify threshold parameter"):
            props = schema["inputSchema"]["properties"]
            assert "threshold" in props
            assert props["threshold"]["type"] in ("number", "integer")
