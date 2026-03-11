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

from src.contexts.coding.interface.mcp_tools import CodingTools

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
def project_with_text_and_codes(app_context: AppContext, tmp_path: Path) -> Path:
    """Create a project with text sources and codes for AI coding tests."""
    from src.contexts.coding.core.entities import Code, Color
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
        id=SourceId("1"),
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
        Code(
            id=CodeId("1"), name="Initial Skepticism", color=Color.from_hex("#FF5722")
        ),
        Code(
            id=CodeId("2"), name="Positive Experience", color=Color.from_hex("#4CAF50")
        ),
        Code(
            id=CodeId("3"),
            name="Time Management Challenge",
            color=Color.from_hex("#F44336"),
        ),
        Code(id=CodeId("4"), name="Adaptive Learning", color=Color.from_hex("#2196F3")),
        Code(id=CodeId("5"), name="Motivation", color=Color.from_hex("#9C27B0")),
        Code(id=CodeId("6"), name="Support System", color=Color.from_hex("#FF9800")),
        Code(id=CodeId("7"), name="Feedback Value", color=Color.from_hex("#00BCD4")),
        Code(
            id=CodeId("8"),
            name="Improvement Suggestion",
            color=Color.from_hex("#795548"),
        ),
    ]
    for code in codes:
        app_context.coding_context.code_repo.save(code)

    return project_path


@pytest.fixture
def project_with_multiple_sources(app_context: AppContext, tmp_path: Path) -> Path:
    """Create a project with multiple sources for batch coding tests."""
    from src.contexts.coding.core.entities import Code, Color
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
            id=SourceId("1"),
            name="interview_01.txt",
            source_type=SourceType.TEXT,
            fulltext="The time management aspect was very challenging for me. I struggled to balance work and study.",
        ),
        Source(
            id=SourceId("2"),
            name="interview_02.txt",
            source_type=SourceType.TEXT,
            fulltext="I found time management difficult because of my busy schedule. Work-life balance suffered.",
        ),
        Source(
            id=SourceId("3"),
            name="interview_03.txt",
            source_type=SourceType.TEXT,
            fulltext="Time management was the biggest hurdle for me. I had to reorganize my daily routine.",
        ),
    ]
    for source in sources:
        app_context.sources_context.source_repo.save(source)

    # Add codes
    codes = [
        Code(id=CodeId("1"), name="Time Management", color=Color.from_hex("#F44336")),
        Code(id=CodeId("2"), name="Work-Life Balance", color=Color.from_hex("#FF9800")),
    ]
    for code in codes:
        app_context.coding_context.code_repo.save(code)

    return project_path


@pytest.fixture
def coding_tools(app_context: AppContext) -> CodingTools:
    """Create CodingTools instance bound to the test AppContext."""
    return CodingTools(ctx=app_context)


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

    @allure.title("AC #1+3: Agent can specify coding parameters with rationale")
    def test_ac1_ac3_specify_parameters_with_rationale(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        project_with_text_and_codes: Path,
    ):
        """Agent can specify all parameters and include rationale for code application."""

        with allure.step("Suggest code application with parameters"):
            result = coding_tools.execute(
                "suggest_code_application",
                {
                    "source_id": 1,
                    "code_id": 1,  # Initial Skepticism
                    "start_pos": 195,
                    "end_pos": 310,
                    "rationale": "Participant expresses initial skepticism about online learning",
                },
            )

        with allure.step("Verify suggestion accepted with correct parameters"):
            assert result.get("success") is True
            data = result["data"]
            assert data["source_id"] == 1
            assert data["code_id"] == 1
            assert data["start_pos"] == 195
            assert data["end_pos"] == 310
            assert "suggestion_id" in data

        with allure.step("Submit suggestion with detailed rationale and confidence"):
            result2 = coding_tools.execute(
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
            assert result2.get("success") is True
            data2 = result2["data"]
            assert "rationale" in data2
            assert "time management" in data2["rationale"].lower()

    @allure.title("AC #2+4: Suggestions require approval and are visible as pending")
    def test_ac2_ac4_requires_approval_and_pending_visible(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        project_with_text_and_codes: Path,
    ):
        """Code application suggestions require researcher approval and can be listed."""

        with allure.step("Submit coding suggestion"):
            result = coding_tools.execute(
                "suggest_code_application",
                {
                    "source_id": 1,
                    "code_id": 2,  # Positive Experience
                    "start_pos": 400,
                    "end_pos": 500,
                    "rationale": "Positive change in perception",
                },
            )

        with allure.step("Verify approval required and segment NOT created"):
            assert result.get("success") is True
            data = result["data"]
            assert data["status"] == "pending_approval"
            assert data["requires_approval"] is True
            segments = app_context.coding_context.segment_repo.get_all()
            matching = [
                s
                for s in segments
                if s.source_id.value == "1" and s.position.start == 400
            ]
            assert len(matching) == 0

        with allure.step("Submit additional suggestion"):
            coding_tools.execute(
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
            result = coding_tools.execute(
                "list_pending_coding_suggestions",
                {"source_id": 1},
            )

        with allure.step("Verify pending suggestions returned"):
            assert result.get("success") is True
            data = result["data"]
            assert data["count"] >= 2
            assert all("suggestion_id" in s for s in data["suggestions"])
            assert all("rationale" in s for s in data["suggestions"])

    @allure.title("Agent can suggest with text excerpt and approve suggestions")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_suggest_with_excerpt_and_approve(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        project_with_text_and_codes: Path,
    ):
        """Agent can include text excerpt and approve coding suggestions."""

        with allure.step("Submit suggestion with text excerpt"):
            result = coding_tools.execute(
                "suggest_code_application",
                {
                    "source_id": 1,
                    "code_id": 5,  # Motivation
                    "start_pos": 580,
                    "end_pos": 620,
                    "rationale": "Participant expresses increased motivation",
                    "include_text": True,
                },
            )

        with allure.step("Verify text excerpt included"):
            assert result.get("success") is True
            data = result["data"]
            assert "text_excerpt" in data
            assert len(data["text_excerpt"]) > 0

        with allure.step("Submit and approve a coding suggestion"):
            suggestion = coding_tools.execute(
                "suggest_code_application",
                {
                    "source_id": 1,
                    "code_id": 7,  # Feedback Value
                    "start_pos": 1400,
                    "end_pos": 1550,
                    "rationale": "Participant values immediate feedback",
                },
            )
            suggestion_id = suggestion["data"]["suggestion_id"]

            approval = coding_tools.execute(
                "approve_coding_suggestion",
                {"suggestion_id": suggestion_id},
            )

        with allure.step("Verify segment created after approval"):
            assert approval.get("success") is True
            assert approval["data"]["status"] == "applied"
            assert "segment_id" in approval["data"]
            segments = app_context.coding_context.segment_repo.get_all()
            matching = [
                s
                for s in segments
                if s.source_id.value == "1" and s.code_id.value == "7"
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

    @allure.title("AC #1+2: Agent can analyze uncoded text and suggest appropriate codes with confidence")
    def test_ac1_ac2_ac3_analyze_and_suggest_codes(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        project_with_text_and_codes: Path,
    ):
        """Agent can analyze text, suggest codes with confidence scores (0-100)."""

        with allure.step("Analyze source for uncoded segments"):
            result = coding_tools.execute(
                "analyze_uncoded_text",
                {"source_id": 1},
            )

        with allure.step("Verify analysis returned"):
            assert result.get("success") is True
            data = result["data"]
            assert "uncoded_ranges" in data
            assert data["total_length"] > 0
            assert "uncoded_percentage" in data

        with allure.step("Request code suggestions for a text range"):
            result = coding_tools.execute(
                "suggest_codes_for_range",
                {
                    "source_id": 1,
                    "start_pos": 1600,
                    "end_pos": 1800,
                },
            )

        with allure.step("Verify code suggestions with confidence scores"):
            assert result.get("success") is True
            data = result["data"]
            assert "suggestions" in data
            assert len(data["suggestions"]) > 0
            for suggestion in data["suggestions"]:
                assert "code_id" in suggestion
                assert "code_name" in suggestion
                assert "confidence" in suggestion
                assert "rationale" in suggestion
                assert 0 <= suggestion["confidence"] <= 100

    @allure.title("AC #4: Researcher can accept, reject, or modify suggestions")
    def test_ac4_researcher_can_respond(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        project_with_text_and_codes: Path,
    ):
        """Researcher can accept, reject, or modify code suggestions."""

        with allure.step("Get code suggestions"):
            suggestions = coding_tools.execute(
                "suggest_codes_for_range",
                {"source_id": 1, "start_pos": 400, "end_pos": 600},
            )
            assert suggestions.get("success") is True
            suggestion_id = suggestions["data"]["suggestion_batch_id"]

        with allure.step("Accept a suggestion"):
            accept_result = coding_tools.execute(
                "respond_to_code_suggestion",
                {
                    "suggestion_batch_id": suggestion_id,
                    "response": "accept",
                    "selected_code_ids": [4],  # Accept Adaptive Learning
                },
            )
            assert accept_result.get("success") is True
            assert accept_result["data"]["applied_count"] >= 1

        with allure.step("Reject a suggestion"):
            suggestions2 = coding_tools.execute(
                "suggest_codes_for_range",
                {"source_id": 1, "start_pos": 100, "end_pos": 200},
            )
            batch_id = suggestions2["data"]["suggestion_batch_id"]

            reject_result = coding_tools.execute(
                "respond_to_code_suggestion",
                {
                    "suggestion_batch_id": batch_id,
                    "response": "reject",
                    "reason": "Not applicable to this context",
                },
            )
            assert reject_result.get("success") is True
            assert reject_result["data"]["status"] == "rejected"

    @allure.title("Auto-suggest codes for entire source and verify pending batch")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_auto_suggest_and_batch_pending(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        project_with_text_and_codes: Path,
    ):
        """Agent can auto-suggest codes and batch suggestions are pending for review."""

        with allure.step("Auto-suggest for entire source"):
            result = coding_tools.execute(
                "auto_suggest_codes",
                {
                    "source_id": 1,
                    "min_confidence": 70,
                },
            )

        with allure.step("Verify batch suggestions returned meeting threshold"):
            assert result.get("success") is True
            data = result["data"]
            assert "suggestions" in data
            assert "total_suggested" in data
            assert data["total_suggested"] > 0
            for suggestion in data["suggestions"]:
                assert suggestion["confidence"] >= 70

        with allure.step("Generate batch suggestions and verify pending status"):
            result2 = coding_tools.execute(
                "auto_suggest_codes",
                {"source_id": 1, "min_confidence": 60},
            )
            assert result2.get("success") is True
            batch_id = result2["data"]["batch_id"]

            status = coding_tools.execute(
                "get_suggestion_batch_status",
                {"batch_id": batch_id},
            )
            assert status.get("success") is True
            assert status["data"]["status"] == "pending_review"
            assert status["data"]["reviewed_count"] == 0


# =============================================================================
# Batch and Multi-Source Tests
# =============================================================================


@allure.story("QC-029 Batch Coding Operations")
@allure.severity(allure.severity_level.CRITICAL)
class TestBatchCodingOperations:
    """Tests for batch coding across multiple sources."""

    @allure.title("Agent can find similar content and batch apply code across sources")
    def test_cross_source_find_and_batch_suggest(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        project_with_multiple_sources: Path,
    ):
        """Agent can identify similar content across sources and suggest batch coding."""

        with allure.step("Find similar content across sources"):
            result = coding_tools.execute(
                "find_similar_content",
                {
                    "search_text": "time management",
                    "code_id": 1,  # Time Management code
                },
            )

        with allure.step("Verify matches found across all 3 sources"):
            assert result.get("success") is True
            data = result["data"]
            assert "matches" in data
            source_ids = {m["source_id"] for m in data["matches"]}
            assert "1" in source_ids
            assert "2" in source_ids
            assert "3" in source_ids

        with allure.step("Suggest batch application"):
            matches = data["matches"]
            batch_result = coding_tools.execute(
                "suggest_batch_coding",
                {
                    "code_id": 1,
                    "segments": [
                        {
                            "source_id": m["source_id"],
                            "start_pos": m["start_pos"],
                            "end_pos": m["end_pos"],
                        }
                        for m in matches
                    ],
                    "rationale": "All segments discuss time management challenges",
                },
            )

        with allure.step("Verify batch suggestion created"):
            assert batch_result.get("success") is True
            batch_data = batch_result["data"]
            assert batch_data["status"] == "pending_approval"
            assert batch_data["segment_count"] == len(matches)

    @allure.title("Batch approval applies all segments")
    def test_batch_approval(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        project_with_multiple_sources: Path,
    ):
        """Approving a batch applies all suggested segments at once."""

        with allure.step("Create batch suggestion"):
            batch_result = coding_tools.execute(
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
            batch_id = batch_result["data"]["batch_id"]

        with allure.step("Approve entire batch"):
            approval = coding_tools.execute(
                "approve_batch_coding",
                {"batch_id": batch_id},
            )

        with allure.step("Verify all segments created"):
            assert approval.get("success") is True
            data = approval["data"]
            assert data["applied_count"] == 3

        with allure.step("Verify segments in repository"):
            segments = app_context.coding_context.segment_repo.get_all()
            code_1_segments = [s for s in segments if s.code_id.value == "1"]
            assert len(code_1_segments) == 3


# =============================================================================
# Integration Tests
# =============================================================================


@allure.story("QC-029 AI Text Coding Integration")
@allure.severity(allure.severity_level.CRITICAL)
class TestAITextCodingIntegration:
    """Integration tests for AI-assisted text coding workflows."""

    @allure.title("Complete workflow: Analyze -> Suggest -> Review -> Apply, and Reject -> Modify -> Approve")
    def test_full_ai_coding_and_reject_modify_workflow(
        self,
        coding_tools: CodingTools,
        app_context: AppContext,
        project_with_text_and_codes: Path,
    ):
        """Test complete AI-assisted coding workflow including reject and modify."""

        with allure.step("Step 1: Analyze uncoded text"):
            analysis = coding_tools.execute("analyze_uncoded_text", {"source_id": 1})
            assert analysis.get("success") is True
            uncoded_pct = analysis["data"]["uncoded_percentage"]
            assert uncoded_pct == 100  # Nothing coded yet

        with allure.step("Step 2: Auto-suggest codes"):
            suggestions = coding_tools.execute(
                "auto_suggest_codes",
                {"source_id": 1, "min_confidence": 75},
            )
            assert suggestions.get("success") is True
            batch_id = suggestions["data"]["batch_id"]
            total_suggested = suggestions["data"]["total_suggested"]
            assert total_suggested > 0

        with allure.step("Step 3: Review suggestions"):
            status = coding_tools.execute(
                "get_suggestion_batch_status",
                {"batch_id": batch_id},
            )
            assert status["data"]["status"] == "pending_review"

        with allure.step("Step 4: Approve suggestions"):
            approval = coding_tools.execute(
                "approve_batch_coding",
                {"batch_id": batch_id},
            )
            assert approval.get("success") is True
            applied = approval["data"]["applied_count"]
            assert applied > 0

        with allure.step("Step 5: Verify coding completed"):
            analysis2 = coding_tools.execute("analyze_uncoded_text", {"source_id": 1})
            uncoded_pct2 = analysis2["data"]["uncoded_percentage"]
            assert uncoded_pct2 < uncoded_pct

        with allure.step("Step 6: Reject suggestion with feedback"):
            suggestion = coding_tools.execute(
                "suggest_code_application",
                {
                    "source_id": 1,
                    "code_id": 1,
                    "start_pos": 100,
                    "end_pos": 200,
                    "rationale": "Test suggestion",
                },
            )
            suggestion_id = suggestion["data"]["suggestion_id"]

            rejection = coding_tools.execute(
                "reject_coding_suggestion",
                {
                    "suggestion_id": suggestion_id,
                    "reason": "The selected range is too narrow",
                    "feedback": "Include more context",
                },
            )
            assert rejection.get("success") is True

        with allure.step("Step 7: Submit modified suggestion and approve"):
            modified = coding_tools.execute(
                "suggest_code_application",
                {
                    "source_id": 1,
                    "code_id": 1,
                    "start_pos": 50,
                    "end_pos": 250,
                    "rationale": "Expanded range based on feedback",
                },
            )
            new_suggestion_id = modified["data"]["suggestion_id"]

            approval = coding_tools.execute(
                "approve_coding_suggestion",
                {"suggestion_id": new_suggestion_id},
            )
            assert approval.get("success") is True


# =============================================================================
# MCP Tool Schema Tests
# =============================================================================


@allure.story("QC-029 AI Coding Tools Schema Validation")
@allure.severity(allure.severity_level.NORMAL)
class TestAICodingToolsSchema:
    """Tests to verify MCP tool schemas are correctly defined."""

    @allure.title("AI coding tools have correct schemas")
    def test_ai_coding_tools_schemas(
        self, coding_tools: CodingTools, app_context: AppContext
    ):
        """Verify schemas for suggest_code_application, suggest_codes_for_range, and auto_suggest_codes."""

        with allure.step("Get tool schemas"):
            schemas = coding_tools.get_tool_schemas()
            schema_map = {s["name"]: s for s in schemas}

        with allure.step("Verify suggest_code_application schema"):
            schema = schema_map.get("suggest_code_application")
            assert schema is not None
            required = schema["inputSchema"]["required"]
            assert "source_id" in required
            assert "code_id" in required
            assert "start_pos" in required
            assert "end_pos" in required
            props = schema["inputSchema"]["properties"]
            assert "rationale" in props
            assert "confidence" in props

        with allure.step("Verify suggest_codes_for_range schema"):
            schema = schema_map.get("suggest_codes_for_range")
            assert schema is not None
            props = schema["inputSchema"]["properties"]
            assert "source_id" in props
            assert "start_pos" in props
            assert "end_pos" in props

        with allure.step("Verify auto_suggest_codes schema"):
            schema = schema_map.get("auto_suggest_codes")
            assert schema is not None
            props = schema["inputSchema"]["properties"]
            assert "source_id" in props
            assert "min_confidence" in props
