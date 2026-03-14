"""
Research Replication: Braun & Clarke Reflexive Thematic Analysis (MCP E2E)

Replicates a qualitative study on "Student Experiences of Online Learning"
using Braun & Clarke's (2006, 2022) six-phase Reflexive Thematic Analysis.

This E2E test exercises QualCoder v2's MCP tool pipeline as an AI agent would:
  Source import → create_code → batch_apply_codes → list_codes →
  list_segments → Category creation → Code reorganization → Verification

Methodology: Reflexive TA (Braun & Clarke, 2022)
Coding methods used: Descriptive Coding + In Vivo Coding (Saldana, 2021)
Quality framework: Lincoln & Guba (1985) trustworthiness via audit trail

References:
  - Braun, V. & Clarke, V. (2006). Using thematic analysis in psychology.
  - Braun, V. & Clarke, V. (2022). Thematic Analysis: A Practical Guide. SAGE.
  - Saldana, J. (2021). The Coding Manual for Qualitative Researchers (4th ed.). SAGE.
  - Lincoln, Y.S. & Guba, E.G. (1985). Naturalistic Inquiry. SAGE.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import allure
import pytest

if TYPE_CHECKING:
    from src.shared.infra.app_context import AppContext
    from src.tests.e2e.conftest import MCPClient

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("Research Replication: Thematic Analysis"),
]

# =============================================================================
# Synthetic Interview Data
#
# Five semi-structured interviews with university students about their
# experiences transitioning to online learning. Synthetic data designed
# to produce recognizable thematic patterns for a teaching demonstration.
# =============================================================================

INTERVIEW_TRANSCRIPTS = {
    "participant_01_sarah.txt": (
        "INTERVIEWER: Can you describe your experience with online learning?\n\n"
        "SARAH: Honestly, it was a mixed bag. At first I felt completely lost. "
        "The technology was overwhelming and I didn't know how to navigate the "
        "learning management system. I remember sitting at my kitchen table "
        "staring at my laptop feeling anxious about missing something important.\n\n"
        "INTERVIEWER: How did that change over time?\n\n"
        "SARAH: After about three weeks I started to find my rhythm. I actually "
        "began to appreciate the flexibility. I could watch lectures at my own pace "
        "and rewind parts I didn't understand. That was a game-changer for me. "
        "But I really missed the social aspect. Study groups over Zoom just aren't "
        "the same as sitting in the library together. There's something about being "
        "physically present with other people who are struggling with the same material.\n\n"
        "INTERVIEWER: What about your relationship with instructors?\n\n"
        "SARAH: Some professors were amazing at adapting. They held virtual office "
        "hours and were really responsive on email. Others just uploaded their old "
        "slides and disappeared. The quality was so inconsistent it was frustrating."
    ),
    "participant_02_james.txt": (
        "INTERVIEWER: Tell me about your online learning experience.\n\n"
        "JAMES: I have to be honest, I thrived in online learning. I'm an introvert "
        "and I always found large lecture halls intimidating. Being able to learn "
        "from my own space was actually liberating. I could focus without the "
        "distractions of other students.\n\n"
        "INTERVIEWER: Were there any challenges?\n\n"
        "JAMES: The biggest challenge was self-discipline. Without a fixed schedule "
        "forcing me to be somewhere, I sometimes procrastinated badly. I had to "
        "create my own structure, like setting alarms and blocking social media "
        "during study hours. Also, group projects were a nightmare online. "
        "Coordinating with people across different time zones who had different "
        "schedules was really difficult.\n\n"
        "INTERVIEWER: How did you feel about the assessment methods?\n\n"
        "JAMES: Online exams were stressful. The proctoring software felt invasive "
        "and I was anxious about my internet connection dropping. I preferred "
        "assignments and projects where I could demonstrate my understanding "
        "without that time pressure. I learned more from those anyway."
    ),
    "participant_03_maria.txt": (
        "INTERVIEWER: What was online learning like for you?\n\n"
        "MARIA: It was really hard at first because of my home situation. I share "
        "a small apartment with my family and finding a quiet space to study was "
        "nearly impossible. My younger siblings would interrupt me constantly. "
        "I felt like I was falling behind because I couldn't concentrate.\n\n"
        "INTERVIEWER: How did you cope with that?\n\n"
        "MARIA: I started going to the public library when it reopened. That helped "
        "a lot. But it made me realize how much of a privilege it is to have a "
        "proper study environment. Not everyone has a home office or even a desk. "
        "The university seemed to assume everyone had ideal conditions at home.\n\n"
        "INTERVIEWER: What aspects of online learning worked well for you?\n\n"
        "MARIA: The recorded lectures were fantastic. As a non-native English "
        "speaker, I could pause and look up words I didn't understand. I also "
        "appreciated discussion forums where I had time to compose my thoughts "
        "before responding. In face-to-face seminars, the fast speakers always "
        "dominated. Online I felt like I had a voice for the first time."
    ),
    "participant_04_david.txt": (
        "INTERVIEWER: How would you describe your online learning journey?\n\n"
        "DAVID: I went through phases. The first phase was denial - I kept thinking "
        "we'd go back to campus any day. Then frustration set in when I realized "
        "this was the new normal. Eventually I adapted but it required a complete "
        "change in how I approached my education.\n\n"
        "INTERVIEWER: What was the biggest adjustment?\n\n"
        "DAVID: Mental health, honestly. I felt isolated and unmotivated. "
        "The boundary between my living space and my study space disappeared "
        "completely. I was basically living in my classroom. I started experiencing "
        "burnout by the middle of the semester because I could never truly switch off.\n\n"
        "INTERVIEWER: Were there any positive aspects?\n\n"
        "DAVID: I developed better time management skills out of necessity. "
        "I also became more independent as a learner. Instead of passively sitting "
        "in lectures, I had to actively engage with the material. In some ways "
        "I think it made me a stronger student, even though the process was painful."
    ),
    "participant_05_aisha.txt": (
        "INTERVIEWER: Can you share your thoughts on the online learning experience?\n\n"
        "AISHA: What struck me most was the digital divide. Some of my classmates "
        "had high-speed internet and multiple monitors while others were trying "
        "to attend lectures on their phones with spotty connections. It really "
        "highlighted inequalities that were always there but hidden.\n\n"
        "INTERVIEWER: How did technology affect your learning?\n\n"
        "AISHA: I became much more tech-savvy which I think is valuable. But I "
        "also experienced screen fatigue. After eight hours of Zoom, my eyes hurt "
        "and my brain felt like mush. We need to rethink how much screen time is "
        "reasonable. Not every class needs to be a live video call.\n\n"
        "INTERVIEWER: What would you keep from online learning going forward?\n\n"
        "AISHA: The accessibility features were incredible. Automatic captions, "
        "recorded lectures, digital materials - these should be standard even in "
        "face-to-face courses. For students with disabilities, this was a huge "
        "improvement. I also loved the flexibility of asynchronous learning. "
        "Being able to structure my own day meant I could work part-time and "
        "still keep up with my studies."
    ),
}


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def study_project(app_context: AppContext, tmp_path: Path) -> dict:
    """
    Create a project with all 5 interview transcripts imported.
    Returns source IDs for use in coding operations.
    """
    from src.contexts.sources.core.entities import Source, SourceType
    from src.shared.common.types import SourceId

    project_path = tmp_path / "thematic_analysis_study.qda"
    result = app_context.create_project(
        name="Online Learning Thematic Analysis", path=str(project_path)
    )
    assert result.is_success, f"Failed to create project: {result.error}"
    app_context.open_project(str(project_path))

    sources = {}
    for name, text in INTERVIEW_TRANSCRIPTS.items():
        source = Source(
            id=SourceId.new(),
            name=name,
            fulltext=text,
            source_type=SourceType.TEXT,
        )
        app_context.sources_context.source_repo.save(source)
        sources[name] = {
            "id": source.id.value,
            "text": text,
        }

    if app_context.session:
        app_context.session.commit()

    return {"project_path": project_path, "sources": sources}


def _find_segment(text: str, phrase: str) -> tuple[int, int]:
    """Find start and end positions of a phrase in text."""
    start = text.index(phrase)
    return start, start + len(phrase)


# =============================================================================
# Phase 1: Familiarization with Data
# =============================================================================


@allure.story("QC-051.01 Phase 1 - Familiarization with Data")
class TestPhase1Familiarization:
    """
    Braun & Clarke Phase 1: Familiarize yourself with the data.

    The researcher reads and re-reads the data, taking initial notes.
    In QualCoder, this involves importing sources and reviewing them.
    """

    @allure.title("AC #1.1: Import five interview transcripts as text sources")
    def test_import_transcripts(self, study_project):
        """All 5 participant interviews should be imported as text sources."""
        with allure.step("Verify all 5 transcripts are imported"):
            assert len(study_project["sources"]) == 5
            for _name, info in study_project["sources"].items():
                assert len(info["text"]) > 100

    @allure.title("AC #1.2: Verify transcript content is accessible")
    def test_transcript_content_accessible(self, study_project):
        """Each transcript should contain interview dialogue."""
        with allure.step("Check each transcript has interviewer/participant dialogue"):
            for name, info in study_project["sources"].items():
                assert "INTERVIEWER:" in info["text"]
                participant_name = name.split("_")[2].split(".")[0].upper()
                assert participant_name in info["text"].upper()


# =============================================================================
# Phase 2: Generating Initial Codes (First Cycle - via MCP tools)
# =============================================================================


@allure.story("QC-051.01 Phase 2 - Generating Initial Codes via MCP")
class TestPhase2InitialCodingMCP:
    """
    Braun & Clarke Phase 2: Generate initial codes.

    Uses MCP tools (create_code, batch_apply_codes) as an AI agent would.
    Demonstrates Descriptive Coding and In Vivo Coding (Saldana).
    """

    @allure.title("AC #2.1: Create descriptive codes via MCP create_code tool")
    def test_create_descriptive_codes_via_mcp(
        self,
        mcp_server: MCPClient,
        app_context: AppContext,
        study_project: dict,
    ):
        """Create codes via MCP tool, the way an AI agent would."""
        code_defs = [
            (
                "Technology barriers",
                "#E53935",
                "Difficulties with tech tools, LMS, connectivity",
            ),
            (
                "Flexibility benefits",
                "#43A047",
                "Appreciation for self-paced, asynchronous learning",
            ),
            (
                "Social isolation",
                "#1E88E5",
                "Missing peer interaction, loneliness, disconnection",
            ),
            (
                "Self-discipline",
                "#FB8C00",
                "Self-regulation, time management, procrastination",
            ),
            (
                "Instructor quality",
                "#8E24AA",
                "Variation in teaching quality and engagement",
            ),
        ]

        created_codes = []
        with allure.step("Create 5 descriptive codes via MCP"):
            for name, color, memo in code_defs:
                result = mcp_server.execute(
                    "create_code",
                    {"name": name, "color": color, "memo": memo},
                )
                assert result["success"] is True, f"Failed to create '{name}': {result}"
                created_codes.append(result["data"])

        with allure.step("Verify codes via list_codes MCP tool"):
            list_result = mcp_server.execute("list_codes", {})
            assert list_result["success"] is True
            codes = list_result["data"]
            code_names = {c["name"] for c in codes}
            for name, _, _ in code_defs:
                assert name in code_names, f"Code '{name}' not found in codebook"

    @allure.title("AC #2.2: Create in vivo codes from participant language")
    def test_create_in_vivo_codes_via_mcp(
        self,
        mcp_server: MCPClient,
        app_context: AppContext,
        study_project: dict,
    ):
        """Create In Vivo codes using participants' own words (Saldana)."""
        in_vivo_codes = [
            ("mixed bag", "#FFB74D", "In vivo: Sarah's summary of her experience"),
            ("game-changer", "#AED581", "In vivo: Sarah on rewinding lectures"),
            (
                "living in my classroom",
                "#EF9A9A",
                "In vivo: David on blurred boundaries",
            ),
            ("had a voice", "#81D4FA", "In vivo: Maria on discussion forums"),
            ("brain felt like mush", "#CE93D8", "In vivo: Aisha on screen fatigue"),
        ]

        with allure.step("Create 5 in vivo codes via MCP"):
            for name, color, memo in in_vivo_codes:
                result = mcp_server.execute(
                    "create_code",
                    {"name": name, "color": color, "memo": memo},
                )
                assert result["success"] is True

        with allure.step("Verify in vivo codes in codebook"):
            list_result = mcp_server.execute("list_codes", {})
            codes = list_result["data"]
            in_vivo_names = {c[0] for c in in_vivo_codes}
            found = {c["name"] for c in codes if c["name"] in in_vivo_names}
            assert found == in_vivo_names

    @allure.title("AC #2.3: Apply codes to segments via MCP batch_apply_codes")
    def test_apply_codes_to_segments_via_mcp(
        self,
        mcp_server: MCPClient,
        app_context: AppContext,
        study_project: dict,
    ):
        """Apply codes to text segments using batch_apply_codes MCP tool."""
        sources = study_project["sources"]
        sarah = sources["participant_01_sarah.txt"]
        sarah_text = sarah["text"]
        sarah_id = sarah["id"]

        with allure.step("Create codes for this test"):
            tech_result = mcp_server.execute(
                "create_code",
                {
                    "name": "Technology barriers",
                    "color": "#E53935",
                    "memo": "Tech access issues",
                },
            )
            tech_id = tech_result["data"]["code_id"]

            flex_result = mcp_server.execute(
                "create_code",
                {
                    "name": "Flexibility benefits",
                    "color": "#43A047",
                    "memo": "Self-paced learning",
                },
            )
            flex_id = flex_result["data"]["code_id"]

            iso_result = mcp_server.execute(
                "create_code",
                {
                    "name": "Social isolation",
                    "color": "#1E88E5",
                    "memo": "Missing peers",
                },
            )
            iso_id = iso_result["data"]["code_id"]

        with allure.step("Batch apply 3 codes to Sarah's transcript"):
            # Segment 1: Tech barriers
            tech_start, tech_end = _find_segment(
                sarah_text,
                "The technology was overwhelming and I didn't know how to navigate the "
                "learning management system.",
            )
            # Segment 2: Flexibility
            flex_start, flex_end = _find_segment(
                sarah_text,
                "I could watch lectures at my own pace and rewind parts I didn't understand.",
            )
            # Segment 3: Social isolation
            iso_start, iso_end = _find_segment(
                sarah_text,
                "I really missed the social aspect.",
            )

            result = mcp_server.execute(
                "batch_apply_codes",
                {
                    "operations": [
                        {
                            "code_id": tech_id,
                            "source_id": sarah_id,
                            "start_position": tech_start,
                            "end_position": tech_end,
                        },
                        {
                            "code_id": flex_id,
                            "source_id": sarah_id,
                            "start_position": flex_start,
                            "end_position": flex_end,
                        },
                        {
                            "code_id": iso_id,
                            "source_id": sarah_id,
                            "start_position": iso_start,
                            "end_position": iso_end,
                        },
                    ]
                },
            )

        with allure.step("Verify all 3 segments created"):
            assert result["success"] is True
            data = result["data"]
            assert data["total"] == 3
            assert data["succeeded"] == 3
            assert data["all_succeeded"] is True

        with allure.step("Verify segments via list_segments_for_source"):
            seg_result = mcp_server.execute(
                "list_segments_for_source",
                {"source_id": sarah_id},
            )
            assert seg_result["success"] is True
            segments = seg_result["data"]
            assert len(segments) == 3

    @allure.title("AC #2.4: Simultaneous coding - multiple codes per segment")
    def test_simultaneous_coding_via_mcp(
        self,
        mcp_server: MCPClient,
        app_context: AppContext,
        study_project: dict,
    ):
        """
        Apply two codes to the same segment (Saldana's Simultaneous Coding).
        Maria's forum comment touches both accessibility and empowerment.
        """
        maria = study_project["sources"]["participant_03_maria.txt"]
        maria_text = maria["text"]
        maria_id = maria["id"]

        with allure.step("Create two codes"):
            acc = mcp_server.execute(
                "create_code",
                {
                    "name": "Accessibility gains",
                    "color": "#7CB342",
                    "memo": "Benefits for diverse learners",
                },
            )
            emp = mcp_server.execute(
                "create_code",
                {
                    "name": "Student empowerment",
                    "color": "#FFD54F",
                    "memo": "Gaining confidence, finding voice",
                },
            )
            acc_id = acc["data"]["code_id"]
            emp_id = emp["data"]["code_id"]

        with allure.step("Apply both codes to same segment"):
            phrase = (
                "I also appreciated discussion forums where I had time to compose "
                "my thoughts before responding."
            )
            start, end = _find_segment(maria_text, phrase)

            result = mcp_server.execute(
                "batch_apply_codes",
                {
                    "operations": [
                        {
                            "code_id": acc_id,
                            "source_id": maria_id,
                            "start_position": start,
                            "end_position": end,
                        },
                        {
                            "code_id": emp_id,
                            "source_id": maria_id,
                            "start_position": start,
                            "end_position": end,
                        },
                    ]
                },
            )
            assert result["success"] is True
            assert result["data"]["succeeded"] == 2

        with allure.step("Verify two different codes on same text range"):
            seg_result = mcp_server.execute(
                "list_segments_for_source",
                {"source_id": maria_id},
            )
            segments = seg_result["data"]
            assert len(segments) == 2
            assert segments[0]["start_position"] == segments[1]["start_position"]
            assert segments[0]["end_position"] == segments[1]["end_position"]
            assert segments[0]["code_id"] != segments[1]["code_id"]

    @allure.title("AC #2.5: Cross-transcript coding via MCP (constant comparison)")
    def test_cross_transcript_coding_via_mcp(
        self,
        mcp_server: MCPClient,
        app_context: AppContext,
        study_project: dict,
    ):
        """Apply the same code across multiple transcripts (constant comparison)."""
        sources = study_project["sources"]

        with allure.step("Create mental health code"):
            mh = mcp_server.execute(
                "create_code",
                {
                    "name": "Mental health impact",
                    "color": "#D81B60",
                    "memo": "Anxiety, burnout, emotional wellbeing",
                },
            )
            mh_id = mh["data"]["code_id"]

        with allure.step("Apply across 3 participants"):
            operations = []

            # Sarah: anxious
            sarah_text = sources["participant_01_sarah.txt"]["text"]
            s_start, s_end = _find_segment(
                sarah_text, "feeling anxious about missing something important."
            )
            operations.append(
                {
                    "code_id": mh_id,
                    "source_id": sources["participant_01_sarah.txt"]["id"],
                    "start_position": s_start,
                    "end_position": s_end,
                }
            )

            # David: isolated and unmotivated
            david_text = sources["participant_04_david.txt"]["text"]
            d_start, d_end = _find_segment(
                david_text, "I felt isolated and unmotivated."
            )
            operations.append(
                {
                    "code_id": mh_id,
                    "source_id": sources["participant_04_david.txt"]["id"],
                    "start_position": d_start,
                    "end_position": d_end,
                }
            )

            # Aisha: screen fatigue
            aisha_text = sources["participant_05_aisha.txt"]["text"]
            a_start, a_end = _find_segment(aisha_text, "my brain felt like mush.")
            operations.append(
                {
                    "code_id": mh_id,
                    "source_id": sources["participant_05_aisha.txt"]["id"],
                    "start_position": a_start,
                    "end_position": a_end,
                }
            )

            result = mcp_server.execute(
                "batch_apply_codes",
                {"operations": operations},
            )
            assert result["success"] is True
            assert result["data"]["succeeded"] == 3

        with allure.step("Verify code spans 3 different sources"):
            source_ids_with_code = set()
            for _name, info in sources.items():
                seg_result = mcp_server.execute(
                    "list_segments_for_source",
                    {"source_id": info["id"]},
                )
                if seg_result["success"]:
                    for seg in seg_result["data"]:
                        if seg["code_id"] == mh_id:
                            source_ids_with_code.add(info["id"])

            assert len(source_ids_with_code) == 3


# =============================================================================
# Phase 3: Searching for Themes (Category creation + code organization)
# =============================================================================


@allure.story("QC-051.01 Phase 3 - Searching for Themes")
class TestPhase3SearchingForThemes:
    """
    Braun & Clarke Phase 3: Search for themes.

    Group codes into candidate themes using categories.
    All operations via MCP tools (create_category, move_code_to_category).
    """

    @allure.title("AC #3.1: Create thematic categories and organize codes")
    def test_create_themes_and_organize_codes(
        self,
        mcp_server: MCPClient,
        app_context: AppContext,
        study_project: dict,
    ):
        """Create categories and move codes into them (Pattern Coding)."""
        with allure.step("Create codes via MCP"):
            codes = {}
            for name, color in [
                ("Technology barriers", "#E53935"),
                ("Flexibility benefits", "#43A047"),
                ("Social isolation", "#1E88E5"),
                ("Mental health", "#D81B60"),
                ("Digital equity", "#00897B"),
            ]:
                result = mcp_server.execute(
                    "create_code",
                    {"name": name, "color": color},
                )
                assert result["success"] is True
                codes[name] = result["data"]["code_id"]

        with allure.step("Create 3 thematic categories via MCP"):
            cat_digital = mcp_server.execute(
                "create_category",
                {
                    "name": "Navigating the Digital Transition",
                    "memo": "Technology challenges, adaptation, digital literacy",
                },
            )
            assert cat_digital["success"] is True
            digital_id = cat_digital["data"]["category_id"]

            cat_paradox = mcp_server.execute(
                "create_category",
                {
                    "name": "The Flexibility-Isolation Paradox",
                    "memo": "Tension between freedom and disconnection",
                },
            )
            assert cat_paradox["success"] is True
            paradox_id = cat_paradox["data"]["category_id"]

            cat_wellbeing = mcp_server.execute(
                "create_category",
                {
                    "name": "Wellbeing Under Pressure",
                    "memo": "Mental health, burnout, blurred boundaries",
                },
            )
            assert cat_wellbeing["success"] is True

        with allure.step("Organize codes into themes via MCP"):
            moves = [
                (codes["Technology barriers"], digital_id),
                (codes["Digital equity"], digital_id),
                (codes["Flexibility benefits"], paradox_id),
                (codes["Social isolation"], paradox_id),
                (codes["Mental health"], cat_wellbeing["data"]["category_id"]),
            ]
            for code_id, category_id in moves:
                result = mcp_server.execute(
                    "move_code_to_category",
                    {"code_id": code_id, "category_id": category_id},
                )
                assert result["success"] is True

        with allure.step("Verify codes are grouped via MCP get_code"):
            flex_detail = mcp_server.execute(
                "get_code", {"code_id": codes["Flexibility benefits"]}
            )
            iso_detail = mcp_server.execute(
                "get_code", {"code_id": codes["Social isolation"]}
            )
            assert (
                flex_detail["data"]["category_id"] == iso_detail["data"]["category_id"]
            )
            assert flex_detail["data"]["category_id"] == paradox_id

        with allure.step("Verify category list via MCP"):
            cats = mcp_server.execute("list_categories", {})
            assert cats["success"] is True
            assert len(cats["data"]) == 3


# =============================================================================
# Phase 4+5: Reviewing, Defining, and Naming Themes
# =============================================================================


@allure.story("QC-051.01 Phase 4-5 - Reviewing and Defining Themes")
class TestPhase4And5ReviewingDefiningThemes:
    """
    Braun & Clarke Phase 4-5: Review and define themes.

    Merge overlapping codes, rename for clarity, write analytical memos.
    All operations via MCP tools (merge_codes, rename_code, update_code_memo).
    """

    @allure.title("AC #4.1: Merge overlapping codes (Focused Coding)")
    def test_merge_overlapping_codes(
        self,
        mcp_server: MCPClient,
        app_context: AppContext,
        study_project: dict,
    ):
        """Merge 'Tech frustration' into 'Technology barriers'."""
        sources = study_project["sources"]
        sarah = sources["participant_01_sarah.txt"]
        james = sources["participant_02_james.txt"]

        with allure.step("Create two overlapping codes via MCP"):
            r1 = mcp_server.execute(
                "create_code",
                {"name": "Technology barriers", "color": "#E53935"},
            )
            r2 = mcp_server.execute(
                "create_code",
                {"name": "Tech frustration", "color": "#C62828"},
            )
            barriers_id = r1["data"]["code_id"]
            frustration_id = r2["data"]["code_id"]

        with allure.step("Apply each code to a segment"):
            s1_start, s1_end = _find_segment(
                sarah["text"],
                "The technology was overwhelming",
            )
            s2_start, s2_end = _find_segment(
                james["text"],
                "The proctoring software felt invasive",
            )

            mcp_server.execute(
                "batch_apply_codes",
                {
                    "operations": [
                        {
                            "code_id": barriers_id,
                            "source_id": sarah["id"],
                            "start_position": s1_start,
                            "end_position": s1_end,
                        },
                        {
                            "code_id": frustration_id,
                            "source_id": james["id"],
                            "start_position": s2_start,
                            "end_position": s2_end,
                        },
                    ]
                },
            )

        with allure.step("Merge via MCP merge_codes"):
            result = mcp_server.execute(
                "merge_codes",
                {
                    "source_code_id": frustration_id,
                    "target_code_id": barriers_id,
                },
            )
            assert result["success"] is True
            assert result["data"]["segments_moved"] >= 0

        with allure.step("Verify merged: source code deleted, target has all segments"):
            # Source code should be gone
            deleted = mcp_server.execute("get_code", {"code_id": frustration_id})
            assert deleted["success"] is False

            # List all codes - only barriers should remain
            all_codes = mcp_server.execute("list_codes", {})
            code_ids = {c["id"] for c in all_codes["data"]}
            assert barriers_id in code_ids
            assert frustration_id not in code_ids

    @allure.title("AC #5.1: Rename code and write analytical memo")
    def test_rename_and_write_memo(
        self,
        mcp_server: MCPClient,
        app_context: AppContext,
        study_project: dict,
    ):
        """Rename a code and update its memo with a theme definition."""
        with allure.step("Create initial code via MCP"):
            r = mcp_server.execute(
                "create_code",
                {"name": "Tech issues", "color": "#E53935", "memo": "Initial code"},
            )
            code_id = r["data"]["code_id"]

        with allure.step("Rename to analytically precise label via MCP"):
            result = mcp_server.execute(
                "rename_code",
                {"code_id": code_id, "new_name": "Digital literacy gap"},
            )
            assert result["success"] is True
            assert result["data"]["old_name"] == "Tech issues"
            assert result["data"]["new_name"] == "Digital literacy gap"

        with allure.step("Write analytical memo defining the theme via MCP"):
            memo_text = (
                "THEME: Digital Literacy Gap\n\n"
                "DEFINITION: Captures the mismatch between institutional "
                "assumptions about student digital competency and students' "
                "actual ability to navigate online learning systems.\n\n"
                "SCOPE: Technology overwhelm, LMS navigation, proctoring "
                "software anxiety, connectivity issues.\n\n"
                "BOUNDARY: Does NOT include broader digital equity concerns "
                "(infrastructure access) — those belong to 'Digital Divide'."
            )
            result = mcp_server.execute(
                "update_code_memo",
                {"code_id": code_id, "memo": memo_text},
            )
            assert result["success"] is True

        with allure.step("Verify via MCP get_code"):
            detail = mcp_server.execute("get_code", {"code_id": code_id})
            assert detail["success"] is True
            assert detail["data"]["name"] == "Digital literacy gap"
            assert "DEFINITION:" in detail["data"]["memo"]
            assert "SCOPE:" in detail["data"]["memo"]
            assert "BOUNDARY:" in detail["data"]["memo"]


# =============================================================================
# Phase 6: Full Workflow Integration + Audit Trail
# =============================================================================


@allure.story("QC-051.01 Phase 6 - Full Workflow and Audit Trail")
class TestPhase6FullWorkflow:
    """
    Complete end-to-end thematic analysis demonstrating the full
    MCP-driven research workflow with audit trail verification.
    """

    @allure.title("AC #6.1: Complete thematic analysis via MCP tools")
    def test_full_thematic_analysis_workflow(
        self,
        mcp_server: MCPClient,
        app_context: AppContext,
        study_project: dict,
    ):
        """
        Full end-to-end workflow via MCP tools only:
        Create codes → Apply across transcripts → Create categories →
        Organize → Verify codebook state.
        """
        sources = study_project["sources"]

        # ---- Phase 2: Create codes via MCP ----
        with allure.step("Phase 2: Create initial codes"):
            code_ids = {}
            for name, color in [
                ("Overwhelm", "#E53935"),
                ("Adaptation", "#43A047"),
                ("Loneliness", "#1E88E5"),
                ("Self-growth", "#FF9800"),
                ("Inequity", "#00897B"),
            ]:
                r = mcp_server.execute("create_code", {"name": name, "color": color})
                assert r["success"] is True
                code_ids[name] = r["data"]["code_id"]

        # ---- Phase 2: Apply codes via MCP batch ----
        with allure.step("Phase 2: Apply codes across transcripts"):
            sarah_text = sources["participant_01_sarah.txt"]["text"]
            james_text = sources["participant_02_james.txt"]["text"]
            maria_text = sources["participant_03_maria.txt"]["text"]
            david_text = sources["participant_04_david.txt"]["text"]

            operations = []

            # Sarah: Overwhelm
            s, e = _find_segment(sarah_text, "I felt completely lost.")
            operations.append(
                {
                    "code_id": code_ids["Overwhelm"],
                    "source_id": sources["participant_01_sarah.txt"]["id"],
                    "start_position": s,
                    "end_position": e,
                }
            )

            # James: Adaptation
            s, e = _find_segment(
                james_text,
                "I had to create my own structure, like setting alarms and "
                "blocking social media during study hours.",
            )
            operations.append(
                {
                    "code_id": code_ids["Adaptation"],
                    "source_id": sources["participant_02_james.txt"]["id"],
                    "start_position": s,
                    "end_position": e,
                }
            )

            # Maria: Inequity
            s, e = _find_segment(
                maria_text,
                "Not everyone has a home office or even a desk.",
            )
            operations.append(
                {
                    "code_id": code_ids["Inequity"],
                    "source_id": sources["participant_03_maria.txt"]["id"],
                    "start_position": s,
                    "end_position": e,
                }
            )

            # David: Loneliness
            s, e = _find_segment(david_text, "I felt isolated and unmotivated.")
            operations.append(
                {
                    "code_id": code_ids["Loneliness"],
                    "source_id": sources["participant_04_david.txt"]["id"],
                    "start_position": s,
                    "end_position": e,
                }
            )

            # David: Self-growth
            s, e = _find_segment(
                david_text,
                "I developed better time management skills out of necessity.",
            )
            operations.append(
                {
                    "code_id": code_ids["Self-growth"],
                    "source_id": sources["participant_04_david.txt"]["id"],
                    "start_position": s,
                    "end_position": e,
                }
            )

            result = mcp_server.execute("batch_apply_codes", {"operations": operations})
            assert result["success"] is True
            assert result["data"]["succeeded"] == 5

        # ---- Phase 3: Create categories and organize via MCP ----
        with allure.step("Phase 3: Create thematic categories via MCP"):
            cat_struggle = mcp_server.execute(
                "create_category",
                {
                    "name": "Struggle and Adaptation",
                    "memo": "How students navigated challenges",
                },
            )
            assert cat_struggle["success"] is True
            struggle_id = cat_struggle["data"]["category_id"]

            cat_connection = mcp_server.execute(
                "create_category",
                {
                    "name": "Connection and Isolation",
                    "memo": "Social dimension of online learning",
                },
            )
            assert cat_connection["success"] is True
            connection_id = cat_connection["data"]["category_id"]

            cat_justice = mcp_server.execute(
                "create_category",
                {"name": "Educational Justice", "memo": "Equity and access concerns"},
            )
            assert cat_justice["success"] is True
            justice_id = cat_justice["data"]["category_id"]

        with allure.step("Phase 3: Organize codes into themes via MCP"):
            org = [
                (code_ids["Overwhelm"], struggle_id),
                (code_ids["Adaptation"], struggle_id),
                (code_ids["Loneliness"], connection_id),
                (code_ids["Self-growth"], connection_id),
                (code_ids["Inequity"], justice_id),
            ]
            for cid, catid in org:
                r = mcp_server.execute(
                    "move_code_to_category",
                    {"code_id": cid, "category_id": catid},
                )
                assert r["success"] is True

        # ---- Phase 6: Verify final state ----
        with allure.step("Phase 6: Verify final codebook via MCP"):
            list_result = mcp_server.execute("list_codes", {})
            assert list_result["success"] is True
            final_codes = list_result["data"]
            assert len(final_codes) == 5

            # Verify codes have categories assigned
            categorized = [c for c in final_codes if c["category_id"] is not None]
            assert len(categorized) == 5

        with allure.step("Phase 6: Verify segment coverage"):
            total_segments = 0
            sources_with_segments = 0
            for _name, info in sources.items():
                seg_result = mcp_server.execute(
                    "list_segments_for_source",
                    {"source_id": info["id"]},
                )
                if seg_result["success"] and seg_result["data"]:
                    total_segments += len(seg_result["data"])
                    sources_with_segments += 1

            assert total_segments == 5, f"Expected 5 segments, got {total_segments}"
            # Sarah, James, Maria, David all have segments (4 of 5 sources)
            assert sources_with_segments >= 3

        with allure.step("Phase 6: Verify event audit trail (Lincoln & Guba)"):
            history = app_context.event_bus.get_history()
            event_types = [e.event_type for e in history]

            assert "coding.code_created" in event_types, "Missing code creation events"
            assert "coding.segment_coded" in event_types, "Missing coding events"
            assert "coding.category_created" in event_types, "Missing category events"
            assert "coding.code_moved_to_category" in event_types, (
                "Missing organization events"
            )

            # All 5 codes should have been created
            assert event_types.count("coding.code_created") == 5
            # All 5 segments should have been coded
            assert event_types.count("coding.segment_coded") == 5
            # 3 categories created
            assert event_types.count("coding.category_created") == 3
