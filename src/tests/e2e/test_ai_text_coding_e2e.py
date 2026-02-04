"""
QC-029.07 & QC-029.08: AI-Assisted Text Coding E2E Tests (TDD)

Test-Driven Development tests for AI-assisted text coding:
- QC-029.07: Agent Apply Code to Text Range
- QC-029.08: Agent Suggest Codes for Text

These tests define the expected behavior BEFORE implementation.
Run with: QT_QPA_PLATFORM=offscreen uv run pytest src/tests/e2e/test_ai_text_coding_e2e.py -v
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
    allure.feature("QC-029 Apply Codes to Text - AI Features"),
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
def project_with_text_and_codes(app_context: AppContext, tmp_path: Path) -> Path:
    """Create a project with text sources and codes for AI coding tests."""
    from src.contexts.coding.core.entities import Code
    from src.contexts.projects.core.entities import Source, SourceType
    from src.shared.common.types import CodeId, SourceId

    project_path = tmp_path / "ai_text_coding_test.qda"
    result = app_context.create_project(
        name="AI Text Coding Test", path=str(project_path)
    )
    assert result.is_success
    app_context.open_project(str(project_path))

    # Add a source with rich content for coding
    source = Source(
        id=SourceId(1),
        name="interview_transcript.txt",
        source_type=SourceType.TEXT,
        fulltext="""Interview Transcript - Participant P001
Date: January 15, 2026
Duration: 45 minutes

Interviewer: Thank you for joining us today. Can you tell me about your experience with the new learning platform?

Participant: Sure. I started using it about three months ago. Initially, I was skeptical because I had bad experiences with online learning before. The interface was confusing and I felt lost.

Interviewer: What changed your mind?

Participant: After the first week, I noticed the platform adapted to my learning style. The exercises became more relevant. I felt more motivated to continue. The gamification elements kept me engaged.

Interviewer: Were there any challenges?

Participant: Yes, definitely. Time management was hard. I work full-time, so finding consistent study time was difficult. Some modules felt too long. I also struggled with the technical vocabulary at first.

Interviewer: How did you overcome those challenges?

Participant: I started waking up earlier to study before work. The mobile app helped - I could learn during my commute. The glossary feature was useful for technical terms. I also joined study groups which provided support and accountability.

Interviewer: What aspects were most valuable?

Participant: The immediate feedback on quizzes was great. I could see where I made mistakes and learn from them right away. The progress tracking kept me motivated. Seeing my scores improve over time was rewarding.

Interviewer: Any suggestions for improvement?

Participant: More interactive content would be helpful. Videos explaining complex concepts. Maybe AI-powered tutoring for personalized help. Also, the discussion forums could be more active.

Interviewer: Thank you for your valuable insights.
""",
    )
    app_context.sources_context.source_repo.save(source)

    # Add codes for coding the text
    codes = [
        Code(id=CodeId(1), name="Initial Skepticism", color="#FF5722"),
        Code(id=CodeId(2), name="Positive Experience", color="#4CAF50"),
        Code(id=CodeId(3), name="Time Management Challenge", color="#F44336"),
        Code(id=CodeId(4), name="Adaptive Learning", color="#2196F3"),
        Code(id=CodeId(5), name="Motivation", color="#9C27B0"),
        Code(id=CodeId(6), name="Support System", color="#FF9800"),
        Code(id=CodeId(7), name="Feedback Value", color="#00BCD4"),
        Code(id=CodeId(8), name="Improvement Suggestion", color="#795548"),
    ]
    for code in codes:
        app_context.coding_context.code_repo.save(code)

    return project_path


@pytest.fixture
def project_with_multiple_sources(app_context: AppContext, tmp_path: Path) -> Path:
    """Create a project with multiple sources for batch coding tests."""
    from src.contexts.coding.core.entities import Code
    from src.contexts.projects.core.entities import Source, SourceType
    from src.shared.common.types import CodeId, SourceId

    project_path = tmp_path / "ai_batch_coding_test.qda"
    result = app_context.create_project(
        name="AI Batch Coding Test", path=str(project_path)
    )
    assert result.is_success
    app_context.open_project(str(project_path))

    # Add multiple sources
    sources = [
        Source(
            id=SourceId(1),
            name="interview_01.txt",
            source_type=SourceType.TEXT,
            fulltext="The time management aspect was very challenging for me. I struggled to balance work and study.",
        ),
        Source(
            id=SourceId(2),
            name="interview_02.txt",
            source_type=SourceType.TEXT,
            fulltext="I found time management difficult because of my busy schedule. Work-life balance suffered.",
        ),
        Source(
            id=SourceId(3),
            name="interview_03.txt",
            source_type=SourceType.TEXT,
            fulltext="Managing time effectively was the biggest hurdle. I had to reorganize my daily routine.",
        ),
    ]
    for source in sources:
        app_context.sources_context.source_repo.save(source)

    # Add codes
    codes = [
        Code(id=CodeId(1), name="Time Management", color="#F44336"),
        Code(id=CodeId(2), name="Work-Life Balance", color="#FF9800"),
    ]
    for code in codes:
        app_context.coding_context.code_repo.save(code)

    return project_path


# =============================================================================
# QC-029.07: Agent Apply Code to Text Range
# =============================================================================


@allure.story("QC-029.07 Agent Apply Code to Text Range")
@allure.severity(allure.severity_level.CRITICAL)
class TestAgentApplyCodeToTextRange:
    """
    QC-029.07: Apply Code to Text Range
    As an AI Agent, I want to apply codes to text ranges so that I can assist with coding.
    """

    @allure.title("AC #1: Agent can specify source, start, end, and code")
    def test_ac1_specify_coding_parameters(
        self, app_context: AppContext, project_with_text_and_codes: Path
    ):
        """Agent can specify all parameters needed to apply a code to text."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Initialize CodingTools"):
            tools = CodingTools(ctx=app_context)

        with allure.step("Suggest code application with parameters"):
            result = tools.execute(
                "suggest_code_application",
                {
                    "source_id": 1,
                    "code_id": 1,  # Initial Skepticism
                    "start_pos": 195,  # Start of "Initially, I was skeptical..."
                    "end_pos": 310,  # End of the sentence
                    "rationale": "Participant expresses initial skepticism about online learning",
                },
            )

        with allure.step("Verify suggestion accepted"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["source_id"] == 1
            assert data["code_id"] == 1
            assert data["start_pos"] == 195
            assert data["end_pos"] == 310
            assert "suggestion_id" in data

    @allure.title("AC #2: Action requires researcher approval")
    def test_ac2_requires_researcher_approval(
        self, app_context: AppContext, project_with_text_and_codes: Path
    ):
        """Code application suggestions require researcher approval."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Submit coding suggestion"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute(
                "suggest_code_application",
                {
                    "source_id": 1,
                    "code_id": 2,  # Positive Experience
                    "start_pos": 400,
                    "end_pos": 500,
                    "rationale": "Positive change in perception",
                },
            )

        with allure.step("Verify approval required"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["status"] == "pending_approval"
            assert data["requires_approval"] is True

        with allure.step("Verify segment NOT created yet"):
            segments = app_context.coding_context.segment_repo.get_all()
            # No segments should exist until approved
            matching = [
                s for s in segments
                if s.source_id.value == 1 and s.start_pos == 400
            ]
            assert len(matching) == 0

    @allure.title("AC #3: Agent can provide rationale for suggestion")
    def test_ac3_provide_rationale(
        self, app_context: AppContext, project_with_text_and_codes: Path
    ):
        """Agent includes rationale explaining why this code fits the text."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Submit suggestion with detailed rationale"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute(
                "suggest_code_application",
                {
                    "source_id": 1,
                    "code_id": 3,  # Time Management Challenge
                    "start_pos": 800,
                    "end_pos": 950,
                    "rationale": "Participant explicitly mentions 'Time management was hard' and describes struggles with finding study time while working full-time.",
                    "confidence": 92,
                },
            )

        with allure.step("Verify rationale included"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert "rationale" in data
            assert "time management" in data["rationale"].lower()

    @allure.title("AC #4: Researcher sees pending suggestions")
    def test_ac4_pending_suggestions_visible(
        self, app_context: AppContext, project_with_text_and_codes: Path
    ):
        """Researcher can see all pending coding suggestions."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        tools = CodingTools(ctx=app_context)

        with allure.step("Submit multiple coding suggestions"):
            tools.execute(
                "suggest_code_application",
                {
                    "source_id": 1,
                    "code_id": 1,
                    "start_pos": 195,
                    "end_pos": 310,
                    "rationale": "Initial skepticism",
                },
            )
            tools.execute(
                "suggest_code_application",
                {
                    "source_id": 1,
                    "code_id": 4,  # Adaptive Learning
                    "start_pos": 450,
                    "end_pos": 550,
                    "rationale": "Platform adaptation mentioned",
                },
            )

        with allure.step("List pending coding suggestions"):
            result = tools.execute(
                "list_pending_coding_suggestions",
                {"source_id": 1},
            )

        with allure.step("Verify pending suggestions returned"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["count"] >= 2
            assert all("suggestion_id" in s for s in data["suggestions"])
            assert all("rationale" in s for s in data["suggestions"])

    @allure.title("Agent can suggest with text excerpt")
    @allure.severity(allure.severity_level.NORMAL)
    def test_suggest_with_text_excerpt(
        self, app_context: AppContext, project_with_text_and_codes: Path
    ):
        """Agent can include the actual text being coded in the suggestion."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Submit suggestion"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute(
                "suggest_code_application",
                {
                    "source_id": 1,
                    "code_id": 5,  # Motivation
                    "start_pos": 580,
                    "end_pos": 620,
                    "rationale": "Participant expresses increased motivation",
                    "include_text": True,  # Request text excerpt
                },
            )

        with allure.step("Verify text excerpt included"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert "text_excerpt" in data
            assert len(data["text_excerpt"]) > 0

    @allure.title("Agent can approve/reject suggestions via MCP")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_approve_coding_suggestion(
        self, app_context: AppContext, project_with_text_and_codes: Path
    ):
        """Agent (or UI) can approve a coding suggestion."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        tools = CodingTools(ctx=app_context)

        with allure.step("Submit coding suggestion"):
            suggestion = tools.execute(
                "suggest_code_application",
                {
                    "source_id": 1,
                    "code_id": 7,  # Feedback Value
                    "start_pos": 1400,
                    "end_pos": 1550,
                    "rationale": "Participant values immediate feedback",
                },
            )
            suggestion_id = suggestion.unwrap()["suggestion_id"]

        with allure.step("Approve suggestion"):
            approval = tools.execute(
                "approve_coding_suggestion",
                {"suggestion_id": suggestion_id},
            )

        with allure.step("Verify segment created"):
            assert isinstance(approval, Success)
            data = approval.unwrap()
            assert data["status"] == "applied"
            assert "segment_id" in data

        with allure.step("Verify segment exists in repository"):
            segments = app_context.coding_context.segment_repo.get_all()
            matching = [
                s for s in segments
                if s.source_id.value == 1 and s.code_id.value == 7
            ]
            assert len(matching) == 1


# =============================================================================
# QC-029.08: Agent Suggest Codes for Text
# =============================================================================


@allure.story("QC-029.08 Agent Suggest Codes for Text")
@allure.severity(allure.severity_level.CRITICAL)
class TestAgentSuggestCodesForText:
    """
    QC-029.08: Suggest Codes for Text
    As an AI Agent, I want to suggest codes for uncoded text so that I can help complete coding.
    """

    @allure.title("AC #1: Agent can analyze uncoded text")
    def test_ac1_analyze_uncoded_text(
        self, app_context: AppContext, project_with_text_and_codes: Path
    ):
        """Agent can analyze text to find uncoded segments."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Initialize CodingTools"):
            tools = CodingTools(ctx=app_context)

        with allure.step("Analyze source for uncoded segments"):
            result = tools.execute(
                "analyze_uncoded_text",
                {"source_id": 1},
            )

        with allure.step("Verify analysis returned"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert "uncoded_ranges" in data
            assert data["total_length"] > 0
            assert "uncoded_percentage" in data

    @allure.title("AC #2: Agent can suggest appropriate codes")
    def test_ac2_suggest_appropriate_codes(
        self, app_context: AppContext, project_with_text_and_codes: Path
    ):
        """Agent can suggest which existing codes fit uncoded text segments."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Request code suggestions for a text range"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute(
                "suggest_codes_for_range",
                {
                    "source_id": 1,
                    "start_pos": 1600,  # Suggestions section
                    "end_pos": 1800,
                },
            )

        with allure.step("Verify code suggestions returned"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert "suggestions" in data
            assert len(data["suggestions"]) > 0

        with allure.step("Verify suggestions include code info"):
            for suggestion in data["suggestions"]:
                assert "code_id" in suggestion
                assert "code_name" in suggestion
                assert "confidence" in suggestion
                assert "rationale" in suggestion

    @allure.title("AC #3: Suggestions include confidence score")
    def test_ac3_suggestions_include_confidence(
        self, app_context: AppContext, project_with_text_and_codes: Path
    ):
        """Code suggestions include confidence scores (0-100)."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Request suggestions"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute(
                "suggest_codes_for_range",
                {
                    "source_id": 1,
                    "start_pos": 800,  # Challenge section
                    "end_pos": 1000,
                },
            )

        with allure.step("Verify confidence scores"):
            assert isinstance(result, Success)
            data = result.unwrap()
            for suggestion in data["suggestions"]:
                assert "confidence" in suggestion
                assert 0 <= suggestion["confidence"] <= 100

    @allure.title("AC #4: Researcher can accept, reject, or modify")
    def test_ac4_researcher_can_respond(
        self, app_context: AppContext, project_with_text_and_codes: Path
    ):
        """Researcher can accept, reject, or modify code suggestions."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        tools = CodingTools(ctx=app_context)

        with allure.step("Get code suggestions"):
            suggestions = tools.execute(
                "suggest_codes_for_range",
                {"source_id": 1, "start_pos": 400, "end_pos": 600},
            )
            assert isinstance(suggestions, Success)
            suggestion_id = suggestions.unwrap()["suggestion_batch_id"]

        with allure.step("Accept a suggestion"):
            accept_result = tools.execute(
                "respond_to_code_suggestion",
                {
                    "suggestion_batch_id": suggestion_id,
                    "response": "accept",
                    "selected_code_ids": [4],  # Accept Adaptive Learning
                },
            )
            assert isinstance(accept_result, Success)
            assert accept_result.unwrap()["applied_count"] >= 1

        with allure.step("Reject a suggestion"):
            # Get new suggestions first
            suggestions2 = tools.execute(
                "suggest_codes_for_range",
                {"source_id": 1, "start_pos": 100, "end_pos": 200},
            )
            batch_id = suggestions2.unwrap()["suggestion_batch_id"]

            reject_result = tools.execute(
                "respond_to_code_suggestion",
                {
                    "suggestion_batch_id": batch_id,
                    "response": "reject",
                    "reason": "Not applicable to this context",
                },
            )
            assert isinstance(reject_result, Success)
            assert reject_result.unwrap()["status"] == "rejected"

    @allure.title("Auto-suggest codes for entire source")
    @allure.severity(allure.severity_level.NORMAL)
    def test_auto_suggest_for_source(
        self, app_context: AppContext, project_with_text_and_codes: Path
    ):
        """Agent can auto-suggest codes for all uncoded portions of a source."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Auto-suggest for entire source"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute(
                "auto_suggest_codes",
                {
                    "source_id": 1,
                    "min_confidence": 70,  # Only suggest if >= 70% confident
                },
            )

        with allure.step("Verify batch suggestions returned"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert "suggestions" in data
            assert "total_suggested" in data
            # Should find multiple segments to code
            assert data["total_suggested"] > 0

        with allure.step("Verify all suggestions meet threshold"):
            for suggestion in data["suggestions"]:
                assert suggestion["confidence"] >= 70

    @allure.title("Batch suggestion creates pending items")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_batch_suggestion_pending(
        self, app_context: AppContext, project_with_text_and_codes: Path
    ):
        """Batch suggestions are created as pending items for review."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        tools = CodingTools(ctx=app_context)

        with allure.step("Generate batch suggestions"):
            result = tools.execute(
                "auto_suggest_codes",
                {"source_id": 1, "min_confidence": 60},
            )
            assert isinstance(result, Success)
            batch_id = result.unwrap()["batch_id"]

        with allure.step("Verify batch is pending"):
            status = tools.execute(
                "get_suggestion_batch_status",
                {"batch_id": batch_id},
            )
            assert isinstance(status, Success)
            assert status.unwrap()["status"] == "pending_review"
            assert status.unwrap()["reviewed_count"] == 0


# =============================================================================
# Batch and Multi-Source Tests
# =============================================================================


@allure.story("QC-029 Batch Coding Operations")
@allure.severity(allure.severity_level.CRITICAL)
class TestBatchCodingOperations:
    """Tests for batch coding across multiple sources."""

    @allure.title("Agent can suggest same code across multiple sources")
    def test_cross_source_suggestions(
        self, app_context: AppContext, project_with_multiple_sources: Path
    ):
        """Agent can identify similar content across sources and suggest codes."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Find similar content across sources"):
            tools = CodingTools(ctx=app_context)
            result = tools.execute(
                "find_similar_content",
                {
                    "search_text": "time management",
                    "code_id": 1,  # Time Management code
                },
            )

        with allure.step("Verify matches found across sources"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert "matches" in data
            # Should find matches in all 3 sources
            source_ids = {m["source_id"] for m in data["matches"]}
            assert 1 in source_ids
            assert 2 in source_ids
            assert 3 in source_ids

    @allure.title("Agent can batch apply code to similar segments")
    def test_batch_apply_to_similar(
        self, app_context: AppContext, project_with_multiple_sources: Path
    ):
        """Agent can request batch application of code to similar segments."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        tools = CodingTools(ctx=app_context)

        with allure.step("Find similar content"):
            find_result = tools.execute(
                "find_similar_content",
                {"search_text": "time management", "code_id": 1},
            )
            matches = find_result.unwrap()["matches"]

        with allure.step("Suggest batch application"):
            batch_result = tools.execute(
                "suggest_batch_coding",
                {
                    "code_id": 1,
                    "segments": [
                        {"source_id": m["source_id"], "start_pos": m["start_pos"], "end_pos": m["end_pos"]}
                        for m in matches
                    ],
                    "rationale": "All segments discuss time management challenges",
                },
            )

        with allure.step("Verify batch suggestion created"):
            assert isinstance(batch_result, Success)
            data = batch_result.unwrap()
            assert data["status"] == "pending_approval"
            assert data["segment_count"] == len(matches)

    @allure.title("Batch approval applies all segments")
    def test_batch_approval(
        self, app_context: AppContext, project_with_multiple_sources: Path
    ):
        """Approving a batch applies all suggested segments at once."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        tools = CodingTools(ctx=app_context)

        with allure.step("Create batch suggestion"):
            batch_result = tools.execute(
                "suggest_batch_coding",
                {
                    "code_id": 1,
                    "segments": [
                        {"source_id": 1, "start_pos": 4, "end_pos": 50},
                        {"source_id": 2, "start_pos": 8, "end_pos": 60},
                        {"source_id": 3, "start_pos": 0, "end_pos": 45},
                    ],
                    "rationale": "Time management mentions",
                },
            )
            batch_id = batch_result.unwrap()["batch_id"]

        with allure.step("Approve entire batch"):
            approval = tools.execute(
                "approve_batch_coding",
                {"batch_id": batch_id},
            )

        with allure.step("Verify all segments created"):
            assert isinstance(approval, Success)
            data = approval.unwrap()
            assert data["applied_count"] == 3

        with allure.step("Verify segments in repository"):
            segments = app_context.coding_context.segment_repo.get_all()
            code_1_segments = [s for s in segments if s.code_id.value == 1]
            assert len(code_1_segments) == 3


# =============================================================================
# Integration Tests
# =============================================================================


@allure.story("QC-029 AI Text Coding Integration")
@allure.severity(allure.severity_level.CRITICAL)
class TestAITextCodingIntegration:
    """Integration tests for AI-assisted text coding workflows."""

    @allure.title("Complete workflow: Analyze -> Suggest -> Review -> Apply")
    def test_full_ai_coding_workflow(
        self, app_context: AppContext, project_with_text_and_codes: Path
    ):
        """Test complete AI-assisted coding workflow."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        tools = CodingTools(ctx=app_context)

        with allure.step("Step 1: Analyze uncoded text"):
            analysis = tools.execute("analyze_uncoded_text", {"source_id": 1})
            assert isinstance(analysis, Success)
            uncoded_pct = analysis.unwrap()["uncoded_percentage"]
            assert uncoded_pct == 100  # Nothing coded yet

        with allure.step("Step 2: Auto-suggest codes"):
            suggestions = tools.execute(
                "auto_suggest_codes",
                {"source_id": 1, "min_confidence": 75},
            )
            assert isinstance(suggestions, Success)
            batch_id = suggestions.unwrap()["batch_id"]
            total_suggested = suggestions.unwrap()["total_suggested"]
            assert total_suggested > 0

        with allure.step("Step 3: Review suggestions"):
            status = tools.execute(
                "get_suggestion_batch_status",
                {"batch_id": batch_id},
            )
            assert status.unwrap()["status"] == "pending_review"

        with allure.step("Step 4: Approve suggestions"):
            approval = tools.execute(
                "approve_batch_coding",
                {"batch_id": batch_id},
            )
            assert isinstance(approval, Success)
            applied = approval.unwrap()["applied_count"]
            assert applied > 0

        with allure.step("Step 5: Verify coding completed"):
            analysis2 = tools.execute("analyze_uncoded_text", {"source_id": 1})
            uncoded_pct2 = analysis2.unwrap()["uncoded_percentage"]
            # Should have less uncoded text now
            assert uncoded_pct2 < uncoded_pct

    @allure.title("Reject and modify workflow")
    def test_reject_modify_workflow(
        self, app_context: AppContext, project_with_text_and_codes: Path
    ):
        """Test workflow for rejecting and modifying AI suggestions."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        tools = CodingTools(ctx=app_context)

        with allure.step("Get AI suggestion"):
            suggestion = tools.execute(
                "suggest_code_application",
                {
                    "source_id": 1,
                    "code_id": 1,
                    "start_pos": 100,
                    "end_pos": 200,
                    "rationale": "Test suggestion",
                },
            )
            suggestion_id = suggestion.unwrap()["suggestion_id"]

        with allure.step("Reject with feedback"):
            rejection = tools.execute(
                "reject_coding_suggestion",
                {
                    "suggestion_id": suggestion_id,
                    "reason": "The selected range is too narrow",
                    "feedback": "Include more context",
                },
            )
            assert isinstance(rejection, Success)

        with allure.step("Submit modified suggestion"):
            modified = tools.execute(
                "suggest_code_application",
                {
                    "source_id": 1,
                    "code_id": 1,
                    "start_pos": 50,  # Expanded range
                    "end_pos": 250,
                    "rationale": "Expanded range based on feedback",
                },
            )
            new_suggestion_id = modified.unwrap()["suggestion_id"]

        with allure.step("Approve modified suggestion"):
            approval = tools.execute(
                "approve_coding_suggestion",
                {"suggestion_id": new_suggestion_id},
            )
            assert isinstance(approval, Success)


# =============================================================================
# MCP Tool Schema Tests
# =============================================================================


@allure.story("QC-029 AI Coding Tools Schema Validation")
@allure.severity(allure.severity_level.NORMAL)
class TestAICodingToolsSchema:
    """Tests to verify MCP tool schemas are correctly defined."""

    @allure.title("suggest_code_application tool has correct schema")
    def test_suggest_code_application_schema(self, app_context: AppContext):
        """Verify suggest_code_application tool schema."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Get tool schemas"):
            tools = CodingTools(ctx=app_context)
            schemas = tools.get_tool_schemas()

        with allure.step("Find suggest_code_application schema"):
            schema = next(
                (s for s in schemas if s["name"] == "suggest_code_application"), None
            )
            assert schema is not None

        with allure.step("Verify required parameters"):
            required = schema["inputSchema"]["required"]
            assert "source_id" in required
            assert "code_id" in required
            assert "start_pos" in required
            assert "end_pos" in required

        with allure.step("Verify optional parameters"):
            props = schema["inputSchema"]["properties"]
            assert "rationale" in props
            assert "confidence" in props

    @allure.title("suggest_codes_for_range tool has correct schema")
    def test_suggest_codes_for_range_schema(self, app_context: AppContext):
        """Verify suggest_codes_for_range tool schema."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Get tool schemas"):
            tools = CodingTools(ctx=app_context)
            schemas = tools.get_tool_schemas()

        with allure.step("Find suggest_codes_for_range schema"):
            schema = next(
                (s for s in schemas if s["name"] == "suggest_codes_for_range"), None
            )
            assert schema is not None

        with allure.step("Verify parameters"):
            props = schema["inputSchema"]["properties"]
            assert "source_id" in props
            assert "start_pos" in props
            assert "end_pos" in props

    @allure.title("auto_suggest_codes tool has correct schema")
    def test_auto_suggest_codes_schema(self, app_context: AppContext):
        """Verify auto_suggest_codes tool schema."""
        from src.contexts.coding.interface.mcp_tools import CodingTools

        with allure.step("Get tool schemas"):
            tools = CodingTools(ctx=app_context)
            schemas = tools.get_tool_schemas()

        with allure.step("Find auto_suggest_codes schema"):
            schema = next(
                (s for s in schemas if s["name"] == "auto_suggest_codes"), None
            )
            assert schema is not None

        with allure.step("Verify parameters"):
            props = schema["inputSchema"]["properties"]
            assert "source_id" in props
            assert "min_confidence" in props
