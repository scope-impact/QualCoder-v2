"""
Research Replication: Code Review Comprehension (ICPC 2025)

Uses REAL observation+interview transcripts from the Zenodo replication package
to replicate a theory-driven thematic analysis of code reviewer behaviour,
entirely through QualCoder v2's MCP tool pipeline.

Dataset: "Code Review Comprehension: Reviewing Strategies Seen Through Code
Comprehension Theories" — Replication Package (CC-BY 4.0)
Source: Zenodo record 14748996, doi:10.5281/zenodo.14748996
Participants: 10 experienced code reviewers performing 25 real reviews

Published Codebook (validated codes used in this test):
  Top-level themes:
    1. Code Review Process (Context building, Decision, Testing, etc.)
    2. Comprehension Scope (Full, Partial, Shallow review)
    3. Information Sources (PR, Code base, Issue tracking, etc.)
    4. Knowledge Base (Domain knowledge, Experience, Mental model)
    5. Mental Model (Actual, Expected, Ideal models)

  This test applies codes FROM the published codebook to real transcript
  passages, enabling validation against the original researchers' analysis.

Methodology: Theory-driven Thematic Analysis (Letovsky's comprehension model)
References:
  - Letovsky, S. (1987). Cognitive processes in program comprehension.
  - Braun, V. & Clarke, V. (2006). Using thematic analysis in psychology.
  - Saldana, J. (2021). The Coding Manual for Qualitative Researchers (4th ed.).
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
    allure.feature("Research Replication: Code Review Comprehension (ICPC)"),
]

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "code_review_transcripts"


def _load_transcript(name: str) -> str:
    """Load a code review transcript from the fixtures directory."""
    path = FIXTURES_DIR / f"{name}.txt"
    assert path.exists(), f"Transcript not found: {path}"
    return path.read_text(encoding="utf-8")


def _find_segment(text: str, phrase: str) -> tuple[int, int]:
    """Find start and end positions of a phrase in text."""
    start = text.find(phrase)
    assert start >= 0, f"Phrase not found in transcript: '{phrase[:60]}...'"
    return start, start + len(phrase)


# =============================================================================
# Published Codebook — Top-Level Themes and Selected Codes
#
# These codes are taken directly from the published codebook.pdf in the
# replication package. Using the researchers' exact terminology enables
# validation against their analysis.
# =============================================================================

PUBLISHED_CODEBOOK = {
    # Theme 1: Code Review Process
    "Context building": {
        "color": "#1E88E5",
        "memo": (
            "Published code: Reviewer builds context before inspecting changes. "
            "Includes: assigning review strategy, creating review goals, "
            "establishing scope, gathering information sources. "
            "22 files, 94 references in original analysis."
        ),
    },
    "Decision": {
        "color": "#43A047",
        "memo": (
            "Published code: Reviewer reaches a verdict on the change. "
            "Includes: checked everything in scope, giving final verdict "
            "(accept/comment/request changes), writing review message. "
            "23 files, 50 references in original analysis."
        ),
    },
    "Testing": {
        "color": "#FB8C00",
        "memo": (
            "Published code: Reviewer engages with CI/CD or hands-on testing. "
            "Includes: CI/CD approval, interpreting fails, local environment "
            "testing, build testing. 5 files, 11 references."
        ),
    },
    "Discussion management": {
        "color": "#8E24AA",
        "memo": (
            "Published code: Reviewer manages PR conversation threads. "
            "Includes: checking past activity, loading context from discussion, "
            "wrap-up of conversations. 6 files, 12 references."
        ),
    },
    # Theme 2: Comprehension Scope
    "Comprehension scope": {
        "color": "#00897B",
        "memo": (
            "Published code: Depth of reviewer's understanding of the change. "
            "Includes: full review, partial review, shallow review, "
            "focused/expertise-based reviewing. 24 files, 151 references."
        ),
    },
    # Theme 3: Information Sources
    "Information Sources": {
        "color": "#5C6BC0",
        "memo": (
            "Published code: External artifacts consulted during review. "
            "Includes: code base, IDE, issue tracking, PR description, "
            "PR conversation, documentation. 21 files, 77 references."
        ),
    },
    # Theme 4: Knowledge Base
    "Knowledge base": {
        "color": "#D81B60",
        "memo": (
            "Published code: Prior knowledge the reviewer brings to the review. "
            "Includes: domain knowledge, programming standards, experience, "
            "mental model of code base. 20 files, 117 references."
        ),
    },
    # Theme 5: Mental Model
    "Mental Model": {
        "color": "#FF7043",
        "memo": (
            "Published code: Cognitive models built and used during review. "
            "Includes: actual MM (implementation, specification, annotation), "
            "expected MM, ideal MM. 13 files, 67 references."
        ),
    },
}

# Published top-level categories from the codebook hierarchy
PUBLISHED_CATEGORIES = {
    "Code Review Process": {
        "memo": (
            "Published theme: The strategies and activities reviewers use to "
            "navigate and evaluate code changes. Contains: Chunking, Context "
            "building, Decision, Difficulty-based, Discussion management, "
            "Linear, Micro strategies, Pair review, Pre-context, Testing."
        ),
    },
    "Reviewer Cognition": {
        "memo": (
            "Published theme: Cognitive aspects of code review — what reviewers "
            "know, how they build understanding, and how deep they go. Contains: "
            "Comprehension scope, Knowledge base, Mental Model."
        ),
    },
    "Review Context": {
        "memo": (
            "Published theme: External resources and contextual factors. "
            "Contains: Information Sources, Pre-context, Factors."
        ),
    },
}


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def review_project(app_context: AppContext, tmp_path: Path) -> dict:
    """
    Create a project with 3 real code review transcripts imported.

    Uses P5R1, P5R2, P9R1 — representing diverse review scenarios:
    - P5R1: First review of upstream community PR (troubleshooting lazy loading)
    - P5R2: Deployment service review (API definition, documentation quality)
    - P9R1: Package dependency upgrade (complex, reviewer has local branch)
    """
    from src.contexts.sources.core.entities import Source, SourceType
    from src.shared.common.types import SourceId

    project_path = tmp_path / "code_review_replication.qda"
    result = app_context.create_project(
        name="Code Review Comprehension Replication", path=str(project_path)
    )
    assert result.is_success, f"Failed to create project: {result.error}"
    app_context.open_project(str(project_path))

    sources = {}
    for name in ["P5R1", "P5R2", "P9R1"]:
        text = _load_transcript(name)
        source = Source(
            id=SourceId.new(),
            name=f"{name}_review_transcript.txt",
            fulltext=text,
            source_type=SourceType.TEXT,
        )
        app_context.sources_context.source_repo.save(source)
        sources[name] = {"id": source.id.value, "text": text}

    if app_context.session:
        app_context.session.commit()

    return {"project_path": project_path, "sources": sources}


# =============================================================================
# Phase 1: Import Real Code Review Transcripts
# =============================================================================


@allure.story("QC-ICPC.01 Phase 1 - Import Code Review Transcripts")
class TestPhase1ImportTranscripts:
    """Import real observation transcripts from the ICPC replication package."""

    @allure.title("AC #1.1: Import real code review transcripts")
    def test_import_real_review_transcripts(self, review_project):
        """Verify 3 real transcripts imported with substantial content."""
        sources = review_project["sources"]

        with allure.step("Verify 3 transcripts imported"):
            assert len(sources) == 3
            for name in ["P5R1", "P5R2", "P9R1"]:
                assert name in sources
                word_count = len(sources[name]["text"].split())
                assert word_count > 500, (
                    f"{name}: expected 500+ words, got {word_count}"
                )

        with allure.step("Verify transcripts contain review observations"):
            # P5R1: upstream community review
            assert "REVIEW TYPE AND GOAL" in sources["P5R1"]["text"]
            assert "TRANSCRIPT" in sources["P5R1"]["text"]
            # P9R1: dependency upgrade review
            assert "upgrading package dependency manager" in sources["P9R1"]["text"]


# =============================================================================
# Phase 2: Apply Published Codes to Real Transcript Passages
# =============================================================================


@allure.story("QC-ICPC.02 Phase 2 - Apply Published Codebook to Real Data")
class TestPhase2ApplyPublishedCodes:
    """
    Apply codes FROM the published codebook to real transcript passages.

    This is the key validation step: the codes are not invented — they are
    the exact codes from the researchers' published codebook.pdf, applied
    to the same transcripts they analyzed.
    """

    @allure.title("AC #2.1: Create codes from published codebook and apply to real passages")
    def test_apply_published_codes_to_real_data(
        self,
        mcp_server: MCPClient,
        app_context: AppContext,
        review_project: dict,
    ):
        """Create codes from the published codebook and apply to matching passages."""
        sources = review_project["sources"]

        # --- Create codes from published codebook ---
        with allure.step("Create codes from published codebook"):
            codes = {}
            for name, info in PUBLISHED_CODEBOOK.items():
                result = mcp_server.execute(
                    "create_code",
                    {"name": name, "color": info["color"], "memo": info["memo"]},
                )
                assert result["success"], f"Failed to create '{name}': {result}"
                codes[name] = result["data"]["code_id"]

        # --- Apply codes to real passages that match the codebook ---
        with allure.step("Apply 'Context building' to P5R1 context-building passage"):
            p5r1 = sources["P5R1"]
            # P5R1: Reviewer reads description to understand the change
            s, e = _find_segment(
                p5r1["text"],
                "Reading a description and saying the change is trying to "
                "troubleshoot some behaviour they do not understand",
            )
            mcp_server.execute("batch_apply_codes", {"operations": [{
                "code_id": codes["Context building"],
                "source_id": p5r1["id"],
                "start_position": s, "end_position": e,
            }]})

        with allure.step("Apply 'Testing' to P5R1 CI passage"):
            # P5R1: Reviewer checks failing CI
            s, e = _find_segment(
                p5r1["text"],
                "Goes to the CI summary tab",
            )
            mcp_server.execute("batch_apply_codes", {"operations": [{
                "code_id": codes["Testing"],
                "source_id": p5r1["id"],
                "start_position": s, "end_position": e,
            }]})

        with allure.step("Apply 'Knowledge base' to P5R1 lazy loading insight"):
            # P5R1: Reviewer draws on prior knowledge
            s, e = _find_segment(
                p5r1["text"],
                "overusing lazy loading",
            )
            mcp_server.execute("batch_apply_codes", {"operations": [{
                "code_id": codes["Knowledge base"],
                "source_id": p5r1["id"],
                "start_position": s, "end_position": e,
            }]})

        with allure.step("Apply 'Mental Model' to P5R2 understanding passage"):
            p5r2 = sources["P5R2"]
            # P5R2: Reviewer builds mental model of the new state
            s, e = _find_segment(
                p5r2["text"],
                "Also wants to understand whether the new state makes sense",
            )
            mcp_server.execute("batch_apply_codes", {"operations": [{
                "code_id": codes["Mental Model"],
                "source_id": p5r2["id"],
                "start_position": s, "end_position": e,
            }]})

        with allure.step("Apply 'Information Sources' to P5R2 documentation passage"):
            # P5R2: Documentation as information source
            s, e = _find_segment(
                p5r2["text"],
                "documentation definitely needs",
            )
            mcp_server.execute("batch_apply_codes", {"operations": [{
                "code_id": codes["Information Sources"],
                "source_id": p5r2["id"],
                "start_position": s, "end_position": e,
            }]})

        with allure.step("Apply 'Decision' to P9R1 verdict passage"):
            p9r1 = sources["P9R1"]
            # P9R1: Reviewer gives up and accepts
            s, e = _find_segment(
                p9r1["text"],
                "gives up and accepts the changes",
            )
            mcp_server.execute("batch_apply_codes", {"operations": [{
                "code_id": codes["Decision"],
                "source_id": p9r1["id"],
                "start_position": s, "end_position": e,
            }]})

        with allure.step("Apply 'Comprehension scope' to P9R1 understanding passage"):
            # P9R1: Reviewer's comprehension limited
            s, e = _find_segment(
                p9r1["text"],
                "reviewer does not understand it so checks it out",
            )
            mcp_server.execute("batch_apply_codes", {"operations": [{
                "code_id": codes["Comprehension scope"],
                "source_id": p9r1["id"],
                "start_position": s, "end_position": e,
            }]})

        with allure.step("Apply 'Discussion management' to P9R1"):
            # P9R1: Reviewer manages discussion about the change
            s, e = _find_segment(
                p9r1["text"],
                "already has a local version of the branch",
            )
            mcp_server.execute("batch_apply_codes", {"operations": [{
                "code_id": codes["Discussion management"],
                "source_id": p9r1["id"],
                "start_position": s, "end_position": e,
            }]})

        # --- Verify all codes applied across transcripts ---
        with allure.step("Verify 8 segments created across 3 transcripts"):
            total = 0
            for name, info in sources.items():
                seg = mcp_server.execute(
                    "list_segments_for_source",
                    {"source_id": info["id"]},
                )
                assert seg["success"]
                total += len(seg["data"])
            assert total == 8, f"Expected 8 segments, got {total}"

        with allure.step("Verify all 8 published codes are in the codebook"):
            all_codes = mcp_server.execute("list_codes", {})
            assert all_codes["success"]
            code_names = {c["name"] for c in all_codes["data"]}
            for name in PUBLISHED_CODEBOOK:
                assert name in code_names, f"Published code '{name}' missing"


# =============================================================================
# Phase 3-5: Organize into Published Theme Hierarchy
# =============================================================================


@allure.story("QC-ICPC.03-05 Phase 3-5 - Build Published Theme Hierarchy")
class TestPhase3to5ThemeHierarchy:
    """
    Organize codes into the thematic structure from the published codebook,
    then merge, rename, and define themes.
    """

    @allure.title("AC #3-5: Full theme development with published codebook")
    def test_theme_development_with_published_codes(
        self,
        mcp_server: MCPClient,
        app_context: AppContext,
        review_project: dict,
    ):
        """Build the published theme hierarchy and verify via MCP tools."""
        sources = review_project["sources"]

        # --- Create codes from published codebook ---
        with allure.step("Create codes from published codebook"):
            codes = {}
            for name, info in PUBLISHED_CODEBOOK.items():
                r = mcp_server.execute(
                    "create_code",
                    {"name": name, "color": info["color"], "memo": info["memo"]},
                )
                assert r["success"]
                codes[name] = r["data"]["code_id"]

        # --- Apply a subset of codes to anchor them in data ---
        with allure.step("Apply codes to anchor passages"):
            p5r1 = sources["P5R1"]
            p9r1 = sources["P9R1"]

            ops = []
            s, e = _find_segment(
                p5r1["text"],
                "Reading a description and saying the change is trying to "
                "troubleshoot some behaviour they do not understand",
            )
            ops.append({
                "code_id": codes["Context building"],
                "source_id": p5r1["id"],
                "start_position": s, "end_position": e,
            })
            s, e = _find_segment(p9r1["text"], "gives up and accepts the changes")
            ops.append({
                "code_id": codes["Decision"],
                "source_id": p9r1["id"],
                "start_position": s, "end_position": e,
            })
            result = mcp_server.execute(
                "batch_apply_codes", {"operations": ops}
            )
            assert result["success"]

        # --- Phase 3: Create thematic categories from published structure ---
        with allure.step("Phase 3: Create published thematic categories"):
            categories = {}
            for cat_name, info in PUBLISHED_CATEGORIES.items():
                r = mcp_server.execute(
                    "create_category",
                    {"name": cat_name, "memo": info["memo"]},
                )
                assert r["success"]
                categories[cat_name] = r["data"]["category_id"]

        # --- Phase 3: Organize codes into published themes ---
        with allure.step("Phase 3: Organize codes into published theme hierarchy"):
            moves = [
                # Code Review Process theme
                (codes["Context building"], categories["Code Review Process"]),
                (codes["Decision"], categories["Code Review Process"]),
                (codes["Testing"], categories["Code Review Process"]),
                (codes["Discussion management"], categories["Code Review Process"]),
                # Reviewer Cognition theme
                (codes["Comprehension scope"], categories["Reviewer Cognition"]),
                (codes["Knowledge base"], categories["Reviewer Cognition"]),
                (codes["Mental Model"], categories["Reviewer Cognition"]),
                # Review Context theme
                (codes["Information Sources"], categories["Review Context"]),
            ]
            for code_id, cat_id in moves:
                r = mcp_server.execute(
                    "move_code_to_category",
                    {"code_id": code_id, "category_id": cat_id},
                )
                assert r["success"]

        # --- Phase 4: Merge related codes ---
        with allure.step("Phase 4: Merge 'Discussion management' into 'Context building'"):
            # In the published codebook, discussion management is closely related
            # to context building (both involve managing information flow)
            merge_result = mcp_server.execute(
                "merge_codes",
                {
                    "source_code_id": codes["Discussion management"],
                    "target_code_id": codes["Context building"],
                },
            )
            assert merge_result["success"]

            # Verify source code deleted
            deleted = mcp_server.execute(
                "get_code", {"code_id": codes["Discussion management"]}
            )
            assert not deleted["success"]

        # --- Phase 5: Rename for analytical precision ---
        with allure.step("Phase 5: Rename code using published model terminology"):
            rename_result = mcp_server.execute(
                "rename_code",
                {
                    "code_id": codes["Context building"],
                    "new_name": "Context building & discussion management",
                },
            )
            assert rename_result["success"]
            assert rename_result["data"]["old_name"] == "Context building"

        # --- Phase 5: Write theme definition ---
        with allure.step("Phase 5: Write theme definition from published model"):
            memo = (
                "THEME: Context Building & Discussion Management\n\n"
                "FROM PUBLISHED MODEL: The Code Review Comprehension Model "
                "(extension of Letovsky) identifies context building as the "
                "initial phase where reviewers gather information to build "
                "understanding before code inspection.\n\n"
                "MERGED: Discussion management (loading context from PR "
                "conversation, wrap-up of threads) incorporated as sub-activity "
                "of context building.\n\n"
                "EVIDENCE: 22 files, 94 references (context building) + "
                "6 files, 12 references (discussion management) in original."
            )
            mcp_server.execute(
                "update_code_memo",
                {"code_id": codes["Context building"], "memo": memo},
            )

        # --- Verify final state ---
        with allure.step("Verify final codebook: 7 codes, 3 categories"):
            all_codes = mcp_server.execute("list_codes", {})
            assert all_codes["success"]
            # Started with 8, merged 1 = 7
            assert len(all_codes["data"]) == 7

            all_cats = mcp_server.execute("list_categories", {})
            assert all_cats["success"]
            assert len(all_cats["data"]) == 3
            cat_names = {c["name"] for c in all_cats["data"]}
            assert cat_names == {
                "Code Review Process",
                "Reviewer Cognition",
                "Review Context",
            }

        with allure.step("Verify Code Review Process has 3 codes (after merge)"):
            process_cat = next(
                c for c in all_cats["data"] if c["name"] == "Code Review Process"
            )
            assert process_cat["code_count"] == 3

        with allure.step("Verify renamed code has theme definition memo"):
            detail = mcp_server.execute(
                "get_code", {"code_id": codes["Context building"]}
            )
            assert detail["success"]
            assert detail["data"]["name"] == "Context building & discussion management"
            assert "PUBLISHED MODEL" in detail["data"]["memo"]
            assert "Letovsky" in detail["data"]["memo"]


# =============================================================================
# Phase 6: Full Workflow with Audit Trail
# =============================================================================


@allure.story("QC-ICPC.06 Phase 6 - Full Validated Workflow")
class TestPhase6FullValidatedWorkflow:
    """
    Complete MCP-only workflow using published codebook on real transcripts,
    with audit trail verification.
    """

    @allure.title("AC #6.1: End-to-end validated replication with audit trail")
    def test_full_validated_replication(
        self,
        mcp_server: MCPClient,
        app_context: AppContext,
        review_project: dict,
    ):
        """
        Full workflow: published codes → real passages → published themes →
        verify codebook → verify audit trail.
        """
        sources = review_project["sources"]
        p5r1 = sources["P5R1"]
        p5r2 = sources["P5R2"]
        p9r1 = sources["P9R1"]

        # ---- Create published codes ----
        with allure.step("Create 5 codes from published codebook"):
            code_ids = {}
            for name, color in [
                ("Context building", "#1E88E5"),
                ("Decision", "#43A047"),
                ("Testing", "#FB8C00"),
                ("Mental Model", "#FF7043"),
                ("Information Sources", "#5C6BC0"),
            ]:
                r = mcp_server.execute(
                    "create_code", {"name": name, "color": color}
                )
                assert r["success"]
                code_ids[name] = r["data"]["code_id"]

        # ---- Apply to real passages ----
        with allure.step("Apply codes to real transcript passages"):
            segment_defs = [
                (code_ids["Context building"], p5r1["id"], p5r1["text"],
                 "Reading a description and saying the change is trying to "
                 "troubleshoot some behaviour they do not understand"),
                (code_ids["Testing"], p5r1["id"], p5r1["text"],
                 "Goes to the CI summary tab"),
                (code_ids["Mental Model"], p5r2["id"], p5r2["text"],
                 "Also wants to understand whether the new state makes sense"),
                (code_ids["Decision"], p9r1["id"], p9r1["text"],
                 "gives up and accepts the changes"),
                (code_ids["Information Sources"], p5r2["id"], p5r2["text"],
                 "documentation definitely needs"),
            ]

            ops = []
            for code_id, source_id, text, phrase in segment_defs:
                s, e = _find_segment(text, phrase)
                ops.append({
                    "code_id": code_id,
                    "source_id": source_id,
                    "start_position": s,
                    "end_position": e,
                })

            result = mcp_server.execute(
                "batch_apply_codes", {"operations": ops}
            )
            assert result["success"]
            assert result["data"]["succeeded"] == 5

        # ---- Create published theme categories ----
        with allure.step("Create published thematic categories"):
            cat_process = mcp_server.execute(
                "create_category", {"name": "Code Review Process"}
            )
            assert cat_process["success"]

            cat_cognition = mcp_server.execute(
                "create_category", {"name": "Reviewer Cognition"}
            )
            assert cat_cognition["success"]

        # ---- Organize codes ----
        with allure.step("Organize codes into published themes"):
            for code_name in ["Context building", "Decision", "Testing"]:
                mcp_server.execute(
                    "move_code_to_category",
                    {
                        "code_id": code_ids[code_name],
                        "category_id": cat_process["data"]["category_id"],
                    },
                )
            for code_name in ["Mental Model", "Information Sources"]:
                mcp_server.execute(
                    "move_code_to_category",
                    {
                        "code_id": code_ids[code_name],
                        "category_id": cat_cognition["data"]["category_id"],
                    },
                )

        # ---- Verify final state ----
        with allure.step("Verify final codebook"):
            codes = mcp_server.execute("list_codes", {})
            assert codes["success"]
            assert len(codes["data"]) == 5

            cats = mcp_server.execute("list_categories", {})
            assert cats["success"]
            assert len(cats["data"]) == 2

        with allure.step("Verify segment coverage"):
            total = 0
            for info in sources.values():
                seg = mcp_server.execute(
                    "list_segments_for_source",
                    {"source_id": info["id"]},
                )
                if seg["success"]:
                    total += len(seg["data"])
            assert total == 5

        with allure.step("Verify audit trail (Lincoln & Guba trustworthiness)"):
            history = app_context.event_bus.get_history()
            event_types = [e.event_type for e in history]

            assert "coding.code_created" in event_types
            assert "coding.segment_coded" in event_types
            assert "coding.category_created" in event_types
            assert "coding.code_moved_to_category" in event_types

            assert event_types.count("coding.code_created") == 5
            assert event_types.count("coding.segment_coded") == 5
            assert event_types.count("coding.category_created") == 2
