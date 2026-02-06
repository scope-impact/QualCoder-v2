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

# Note: CodingTools.execute() returns dict, not Result

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
        Code(
            id=CodeId(1),
            name="Theme",
            color=Color.from_hex("#FF5722"),
            memo="Main themes",
        ),
        Code(
            id=CodeId(2),
            name="Themes",
            color=Color.from_hex("#FF9800"),
            memo="Alternative themes",
        ),
        Code(
            id=CodeId(3),
            name="Positive Emotion",
            color=Color.from_hex("#4CAF50"),
            memo="Happy feelings",
        ),
        Code(
            id=CodeId(4),
            name="Positive Feeling",
            color=Color.from_hex("#8BC34A"),
            memo="Good feelings",
        ),
        Code(
            id=CodeId(5),
            name="Challenge",
            color=Color.from_hex("#F44336"),
            memo="Difficulties",
        ),
        Code(
            id=CodeId(6),
            name="Learning",
            color=Color.from_hex("#2196F3"),
            memo="Education related",
        ),
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
            assert result.get("success") is True
            data = result["data"]
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
            assert result.get("success") is True
            data = result["data"]
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
            assert result.get("success") is True
            data = result["data"]
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
            assert result.get("success") is True
            data = result["data"]
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
                {
                    "name": "Code A",
                    "color": "#FF0000",
                    "rationale": "Test",
                    "confidence": 70,
                },
            )
            tools.execute(
                "suggest_new_code",
                {
                    "name": "Code B",
                    "color": "#00FF00",
                    "rationale": "Test",
                    "confidence": 80,
                },
            )

        with allure.step("List pending suggestions"):
            result = tools.execute("list_pending_suggestions", {})

        with allure.step("Verify pending suggestions returned"):
            assert result.get("success") is True
            data = result["data"]
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
            assert result.get("success") is True
            data = result["data"]
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
            assert result.get("success") is True
            data = result["data"]
            assert "candidates" in data
            assert len(data["candidates"]) > 0

        with allure.step("Verify Theme/Themes pair detected"):
            pairs = [(c["code_a_name"], c["code_b_name"]) for c in data["candidates"]]
            # Either order is valid
            theme_pair_found = any(("Theme" in a and "Theme" in b) for a, b in pairs)
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
            assert result.get("success") is True
            data = result["data"]
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
            assert result.get("success") is True
            data = result["data"]
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
            assert result.get("success") is True

        with allure.step("Verify codes NOT merged automatically"):
            codes = app_context.coding_context.code_repo.get_all()
            assert len(codes) == initial_count

        with allure.step("Verify result indicates approval required"):
            data = result["data"]
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
            assert result.get("success") is True
            data = result["data"]
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
            assert result.get("success") is True
            data = result["data"]
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
        self, app_context: AppContext, project_with_uncoded_content: Path
    ):
        """Test complete workflow from analysis to code creation."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        tools = CodingTools(ctx=app_context)

        with allure.step("Step 1: Analyze content for potential codes"):
            analysis = tools.execute("analyze_content_for_codes", {"source_id": 1})
            assert analysis.get("success") is True

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
            assert suggestion.get("success") is True
            suggestion_id = suggestion["data"]["suggestion_id"]

        with allure.step("Step 3: Verify suggestion is pending"):
            pending = tools.execute("list_pending_suggestions", {})
            assert pending.get("success") is True
            ids = [s["suggestion_id"] for s in pending["data"]["suggestions"]]
            assert suggestion_id in ids

        with allure.step("Step 4: Approve suggestion (simulated researcher action)"):
            # This would be done via UI/ViewModel, but we test the MCP interface
            approval = tools.execute(
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
        self, app_context: AppContext, project_with_codes: Path
    ):
        """Test complete workflow from detection to merge."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        tools = CodingTools(ctx=app_context)

        with allure.step("Step 1: Detect duplicate codes"):
            detection = tools.execute("detect_duplicate_codes", {"threshold": 0.8})
            assert detection.get("success") is True
            candidates = detection["data"]["candidates"]
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
            assert merge_suggestion.get("success") is True
            merge_id = merge_suggestion["data"]["merge_suggestion_id"]

        with allure.step("Step 3: Approve merge"):
            approval = tools.execute(
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

    @allure.title("suggest_new_code tool has correct schema")
    def test_suggest_new_code_schema(self, app_context: AppContext):
        """Verify suggest_new_code tool schema."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Get tool schemas"):
            tools = CodingTools(ctx=app_context)
            schemas = tools.get_tool_schemas()

        with allure.step("Find suggest_new_code schema"):
            schema = next((s for s in schemas if s["name"] == "suggest_new_code"), None)
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

    @allure.title("AC #1: Agent can retrieve all codes")
    def test_ac1_list_all_codes(
        self, app_context: AppContext, project_with_codes: Path
    ):
        """Agent can list all codes in the codebook."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Initialize CodingTools"):
            tools = CodingTools(ctx=app_context)

        with allure.step("List all codes"):
            result = tools.execute("list_codes", {})

        with allure.step("Verify codes returned"):
            assert result.get("success") is True
            data = result["data"]
            assert isinstance(data, list)
            assert len(data) == 6  # We created 6 codes in fixture

    @allure.title("AC #2: Each code includes required fields")
    def test_ac2_codes_include_required_fields(
        self, app_context: AppContext, project_with_codes: Path
    ):
        """Each code returned has id, name, and color fields."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("List codes"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute("list_codes", {})

        with allure.step("Verify required fields for each code"):
            assert result.get("success") is True
            for code in result["data"]:
                assert "id" in code
                assert "name" in code
                assert "color" in code
                assert isinstance(code["id"], int)
                assert isinstance(code["name"], str)
                assert isinstance(code["color"], str)
                assert code["color"].startswith("#")

    @allure.title("AC #3: Each code includes memo field")
    def test_ac3_codes_include_memo(
        self, app_context: AppContext, project_with_codes: Path
    ):
        """Each code returned includes the memo field."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("List codes"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute("list_codes", {})

        with allure.step("Verify memo field exists"):
            assert result.get("success") is True
            for code in result["data"]:
                assert "memo" in code
                # Memo can be None or string
                assert code["memo"] is None or isinstance(code["memo"], str)

    @allure.title("AC #4: Empty project returns empty list")
    def test_ac4_empty_when_no_codes(self, app_context: AppContext, tmp_path: Path):
        """Listing codes on empty project returns empty list."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Create empty project"):
            project_path = tmp_path / "empty_codes_test.qda"
            result = app_context.create_project(
                name="Empty Codes Test", path=str(project_path)
            )
            assert result.is_success
            app_context.open_project(str(project_path))

        with allure.step("List codes"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute("list_codes", {})

        with allure.step("Verify empty list returned"):
            assert result.get("success") is True
            assert result["data"] == []

    @allure.title("list_codes tool has correct schema")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_codes_schema(self, app_context: AppContext):
        """Verify list_codes tool schema is correctly defined."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Get tool schemas"):
            tools = CodingTools(ctx=app_context)
            schemas = tools.get_tool_schemas()

        with allure.step("Find list_codes schema"):
            schema = next((s for s in schemas if s["name"] == "list_codes"), None)
            assert schema is not None

        with allure.step("Verify no required parameters"):
            # list_codes should have no required params
            required = schema["inputSchema"].get("required", [])
            assert len(required) == 0


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

    @allure.title("AC #1: Agent can create code with name and color")
    def test_ac1_create_code_basic(self, app_context: AppContext, tmp_path: Path):
        """Agent can create a code with required name and color."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Create project"):
            project_path = tmp_path / "create_code_test.qda"
            result = app_context.create_project(
                name="Create Code Test", path=str(project_path)
            )
            assert result.is_success
            app_context.open_project(str(project_path))

        with allure.step("Initialize CodingTools"):
            tools = CodingTools(ctx=app_context)

        with allure.step("Create code"):
            result = tools.execute(
                "create_code",
                {"name": "New Theme", "color": "#FF5722"},
            )

        with allure.step("Verify code created"):
            assert result.get("success") is True
            data = result["data"]
            assert data["name"] == "New Theme"
            assert (
                data["color"].lower() == "#ff5722"
            )  # Color may be normalized to lowercase
            assert "code_id" in data
            assert isinstance(data["code_id"], int)

    @allure.title("AC #2: Created code persisted to repository")
    def test_ac2_code_persisted(self, app_context: AppContext, tmp_path: Path):
        """Created code is saved to the repository."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Create project"):
            project_path = tmp_path / "persist_code_test.qda"
            result = app_context.create_project(
                name="Persist Code Test", path=str(project_path)
            )
            assert result.is_success
            app_context.open_project(str(project_path))

        with allure.step("Create code"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute(
                "create_code",
                {"name": "Persisted Code", "color": "#4CAF50"},
            )
            assert result.get("success") is True

        with allure.step("Verify code exists in repository"):
            codes = app_context.coding_context.code_repo.get_all()
            code_names = [c.name for c in codes]
            assert "Persisted Code" in code_names

    @allure.title("AC #3: Agent can create code with optional memo")
    def test_ac3_code_with_memo(self, app_context: AppContext, tmp_path: Path):
        """Agent can create a code with an optional memo/description."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Create project"):
            project_path = tmp_path / "memo_code_test.qda"
            result = app_context.create_project(
                name="Memo Code Test", path=str(project_path)
            )
            assert result.is_success
            app_context.open_project(str(project_path))

        with allure.step("Create code with memo"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute(
                "create_code",
                {
                    "name": "Documented Code",
                    "color": "#2196F3",
                    "memo": "This code captures positive user experiences.",
                },
            )

        with allure.step("Verify memo saved"):
            assert result.get("success") is True
            data = result["data"]
            assert data["memo"] == "This code captures positive user experiences."

    @allure.title("AC #4: Agent can create code in a category")
    def test_ac4_code_with_category(
        self, app_context: AppContext, project_with_codes: Path
    ):
        """Agent can create a code in a specific category."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Create code in category"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute(
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
            assert data["category_id"] == 1

    @allure.title("AC #5: Invalid color returns error")
    def test_ac5_invalid_color_error(self, app_context: AppContext, tmp_path: Path):
        """Creating code with invalid color returns error."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Create project"):
            project_path = tmp_path / "invalid_color_test.qda"
            result = app_context.create_project(
                name="Invalid Color Test", path=str(project_path)
            )
            assert result.is_success
            app_context.open_project(str(project_path))

        with allure.step("Attempt to create code with invalid color"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute(
                "create_code",
                {"name": "Bad Color", "color": "not-a-color"},
            )

        with allure.step("Verify error returned"):
            assert result.get("success") is False
            assert "error" in result
            assert "INVALID_COLOR" in result.get("error_code", "")

    @allure.title("AC #6: Duplicate name returns error")
    def test_ac6_duplicate_name_error(
        self, app_context: AppContext, project_with_codes: Path
    ):
        """Creating code with duplicate name returns error."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Attempt to create code with existing name"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute(
                "create_code",
                {"name": "Theme", "color": "#FF0000"},  # "Theme" already exists
            )

        with allure.step("Verify error returned"):
            assert result.get("success") is False
            assert "error" in result

    @allure.title("AC #7: Missing required params returns error")
    def test_ac7_missing_params_error(self, app_context: AppContext, tmp_path: Path):
        """Missing required parameters returns error."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Create project"):
            project_path = tmp_path / "missing_params_test.qda"
            result = app_context.create_project(
                name="Missing Params Test", path=str(project_path)
            )
            assert result.is_success
            app_context.open_project(str(project_path))

        with allure.step("Attempt to create code without name"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute(
                "create_code",
                {"color": "#FF0000"},  # Missing name
            )

        with allure.step("Verify error for missing name"):
            assert result.get("success") is False
            assert "name" in result.get("error", "").lower()

        with allure.step("Attempt to create code without color"):
            result = tools.execute(
                "create_code",
                {"name": "No Color Code"},  # Missing color
            )

        with allure.step("Verify error for missing color"):
            assert result.get("success") is False
            assert "color" in result.get("error", "").lower()

    @allure.title("create_code tool has correct schema")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_code_schema(self, app_context: AppContext):
        """Verify create_code tool schema is correctly defined."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Get tool schemas"):
            tools = CodingTools(ctx=app_context)
            schemas = tools.get_tool_schemas()

        with allure.step("Find create_code schema"):
            schema = next((s for s in schemas if s["name"] == "create_code"), None)
            assert schema is not None

        with allure.step("Verify required parameters"):
            required = schema["inputSchema"]["required"]
            assert "name" in required
            assert "color" in required

        with allure.step("Verify optional parameters"):
            props = schema["inputSchema"]["properties"]
            assert "memo" in props
            assert "category_id" in props
