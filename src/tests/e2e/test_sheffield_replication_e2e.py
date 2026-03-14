"""
Research Replication: Sheffield ORDA "Fostering Cultures of Open Qualitative Research"

Uses REAL interview transcripts from the Sheffield Hallam University dataset
(Sheridan et al., 2023) to replicate a Reflexive Thematic Analysis workflow
entirely through QualCoder v2's MCP tool pipeline.

Dataset: "Fostering cultures of open qualitative research" (CC-BY-NC 4.0)
Source: Sheffield Online Research Data Archive (ORDA), Figshare article 23567223
Participants: Qualitative researchers discussing their experiences with open data

This test exercises the full AI-agent coding workflow:
  Phase 1: Import real transcripts → Phase 2: Create codes + apply to real text →
  Phase 3: Create thematic categories → Phase 4-5: Merge, rename, define themes →
  Phase 6: Verify codebook integrity and audit trail

Methodology: Braun & Clarke (2006, 2022) Reflexive Thematic Analysis
Coding methods: Descriptive Coding + In Vivo Coding (Saldana, 2021)

References:
  - Sheridan, N., Sheridan, L., Sheridan, G. & Parry, K. (2023). Interview
    Transcripts: Fostering cultures of open qualitative research. University of
    Sheffield. https://doi.org/10.15131/shef.data.23567223
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
    allure.feature("Research Replication: Sheffield Open QR Transcripts"),
]

# =============================================================================
# Real transcript excerpts from Sheffield ORDA dataset
# Using key passages that represent codable data about open qualitative research
# =============================================================================

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "sheffield_transcripts"


def _load_transcript(name: str) -> str:
    """Load a Sheffield transcript from the fixtures directory."""
    path = FIXTURES_DIR / f"{name}.txt"
    assert path.exists(), f"Transcript not found: {path}"
    return path.read_text(encoding="utf-8")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sheffield_project(app_context: AppContext, tmp_path: Path) -> dict:
    """
    Create a project and import 3 real Sheffield interview transcripts.

    Uses Ana, David, and Jessica — representing diverse perspectives:
    - Ana: Arts-based researcher, copyleft culture, Open Science Framework user
    - David: Framework analyst, pen-and-paper, values participant protection
    - Jessica: NVivo user, early-career, learning about open research ethics
    """
    from src.contexts.sources.core.entities import Source, SourceType
    from src.shared.common.types import SourceId

    project_path = tmp_path / "sheffield_replication.qda"
    result = app_context.create_project(
        name="Sheffield Open QR Replication", path=str(project_path)
    )
    assert result.is_success, f"Failed to create project: {result.error}"
    app_context.open_project(str(project_path))

    sources = {}
    for name in ["Ana", "David", "Jessica"]:
        text = _load_transcript(name)
        source = Source(
            id=SourceId.new(),
            name=f"{name}_interview.txt",
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
    start = text.find(phrase)
    assert start >= 0, f"Phrase not found in transcript: '{phrase[:60]}...'"
    return start, start + len(phrase)


# =============================================================================
# Phase 1: Familiarization — Import Real Transcripts
# =============================================================================


@allure.story("QC-051.02 Sheffield Replication")
class TestPhase1ImportRealTranscripts:
    """
    Braun & Clarke Phase 1: Familiarize yourself with the data.

    Import 3 real semi-structured interview transcripts from the Sheffield
    ORDA dataset about researchers' experiences with open qualitative data.
    """

    @allure.title("AC #1.1: Import real transcripts and verify content")
    def test_import_and_verify_real_transcripts(self, sheffield_project):
        """Real interview transcripts should be imported with full content."""
        sources = sheffield_project["sources"]

        with allure.step("Verify 3 real transcripts imported"):
            assert len(sources) == 3
            for name in ["Ana", "David", "Jessica"]:
                assert name in sources
                text = sources[name]["text"]
                # Real transcripts are substantial (4000+ words)
                word_count = len(text.split())
                assert word_count > 4000, (
                    f"{name}: expected 4000+ words, got {word_count}"
                )

        with allure.step("Verify transcripts contain interview dialogue"):
            # Ana discusses copyleft culture and Open Science Framework
            assert "Open Science framework" in sources["Ana"]["text"] or \
                   "open" in sources["Ana"]["text"].lower()
            # David discusses participant protection and data archives
            assert "participant" in sources["David"]["text"].lower()
            # Jessica discusses NVivo and research ethics
            assert "Nvivo" in sources["Jessica"]["text"] or \
                   "NVivo" in sources["Jessica"]["text"]


# =============================================================================
# Phase 2: Initial Coding — Apply Codes to Real Transcript Passages
# =============================================================================


@allure.story("QC-051.02 Sheffield Replication")
class TestPhase2CodeRealData:
    """
    Braun & Clarke Phase 2: Generate initial codes.

    Apply descriptive and in vivo codes to real passages from Sheffield
    interviews about open qualitative research practices.
    """

    @allure.title("AC #2.1: Create codes and apply to real transcript passages")
    def test_code_real_passages(
        self,
        mcp_server: MCPClient,
        app_context: AppContext,
        sheffield_project: dict,
    ):
        """Create codes grounded in the research topic and apply to real data."""
        sources = sheffield_project["sources"]

        # --- Create descriptive codes relevant to the study topic ---
        with allure.step("Create descriptive codes for open research themes"):
            code_defs = [
                ("Data sharing willingness", "#4CAF50",
                 "Researcher attitudes toward sharing qualitative data"),
                ("Participant protection", "#F44336",
                 "Concerns about anonymity, consent, and participant welfare"),
                ("Research software tools", "#2196F3",
                 "Use of QDA software: NVivo, Atlas.ti, manual analysis"),
                ("Ethical tensions", "#FF9800",
                 "Tension between openness and ethical obligations"),
                ("Institutional barriers", "#9C27B0",
                 "University policies, GDPR, repository access constraints"),
            ]

            codes = {}
            for name, color, memo in code_defs:
                result = mcp_server.execute(
                    "create_code",
                    {"name": name, "color": color, "memo": memo},
                )
                assert result["success"], f"Failed to create '{name}': {result}"
                codes[name] = result["data"]["code_id"]

        # --- Apply codes to real passages ---
        with allure.step("Apply codes to Ana's transcript"):
            ana = sources["Ana"]

            # Ana on difficulty of making qualitative data open
            s, e = _find_segment(
                ana["text"],
                "what makes it also difficult to make it open"
            )
            mcp_server.execute("batch_apply_codes", {"operations": [{
                "code_id": codes["Data sharing willingness"],
                "source_id": ana["id"],
                "start_position": s, "end_position": e,
            }]})

        with allure.step("Apply codes to David's transcript"):
            david = sources["David"]

            # David on sharing analysis vs protecting participants
            s, e = _find_segment(
                david["text"],
                "share my analysis"
            )
            mcp_server.execute("batch_apply_codes", {"operations": [{
                "code_id": codes["Participant protection"],
                "source_id": david["id"],
                "start_position": s, "end_position": e,
            }]})

            # David on not using QDA software
            s, e = _find_segment(
                david["text"],
                "I don't tend to use things like Atlas Ti"
                if "Atlas Ti" in david["text"]
                else "pen and paper"
            )
            mcp_server.execute("batch_apply_codes", {"operations": [{
                "code_id": codes["Research software tools"],
                "source_id": david["id"],
                "start_position": s, "end_position": e,
            }]})

        with allure.step("Apply codes to Jessica's transcript"):
            jessica = sources["Jessica"]

            # Jessica on using NVivo
            s, e = _find_segment(
                jessica["text"],
                "I used Nvivo"
                if "I used Nvivo" in jessica["text"]
                else "Nvivo"
            )
            mcp_server.execute("batch_apply_codes", {"operations": [{
                "code_id": codes["Research software tools"],
                "source_id": jessica["id"],
                "start_position": s, "end_position": e,
            }]})

            # Jessica on ethics concerns
            s, e = _find_segment(
                jessica["text"],
                "should have thought more about the ethics"
                if "should have thought more about the ethics" in jessica["text"]
                else "ethics"
            )
            mcp_server.execute("batch_apply_codes", {"operations": [{
                "code_id": codes["Ethical tensions"],
                "source_id": jessica["id"],
                "start_position": s, "end_position": e,
            }]})

        with allure.step("Verify segments created across transcripts"):
            total = 0
            for name, info in sources.items():
                seg = mcp_server.execute(
                    "list_segments_for_source",
                    {"source_id": info["id"]},
                )
                assert seg["success"]
                total += len(seg["data"])

            assert total >= 4, f"Expected at least 4 segments, got {total}"

    @allure.title("AC #2.2: Create in vivo codes from real participant language")
    def test_in_vivo_codes_from_real_speech(
        self,
        mcp_server: MCPClient,
        app_context: AppContext,
        sheffield_project: dict,
    ):
        """Create In Vivo codes using real participants' own words (Saldana)."""
        sources = sheffield_project["sources"]

        with allure.step("Create in vivo codes from real speech"):
            # Ana's actual words about craft-based analysis
            ana_text = sources["Ana"]["text"]
            in_vivo_result = mcp_server.execute(
                "create_code",
                {
                    "name": "my analysis are much more craft",
                    "color": "#FFB74D",
                    "memo": "In vivo: Ana describing her analytical approach as craft rather than mechanical process",
                },
            )
            assert in_vivo_result["success"]
            craft_id = in_vivo_result["data"]["code_id"]

            # Apply to the actual passage
            s, e = _find_segment(ana_text, "my analysis are much more craft")
            result = mcp_server.execute("batch_apply_codes", {"operations": [{
                "code_id": craft_id,
                "source_id": sources["Ana"]["id"],
                "start_position": s, "end_position": e,
            }]})
            assert result["success"]

        with allure.step("Create in vivo code from David's speech"):
            david_text = sources["David"]["text"]
            # David's words about participant welfare
            iv2 = mcp_server.execute(
                "create_code",
                {
                    "name": "they do come first",
                    "color": "#EF9A9A",
                    "memo": "In vivo: David on prioritizing participants over open data",
                },
            )
            assert iv2["success"]

            s, e = _find_segment(david_text, "do come first")
            result = mcp_server.execute("batch_apply_codes", {"operations": [{
                "code_id": iv2["data"]["code_id"],
                "source_id": sources["David"]["id"],
                "start_position": s, "end_position": e,
            }]})
            assert result["success"]


# =============================================================================
# Phase 3-5: Theme Development — Organize, Merge, Rename, Define
# =============================================================================


@allure.story("QC-051.02 Sheffield Replication")
class TestPhase3to5DevelopThemes:
    """
    Braun & Clarke Phases 3-5: Search for themes, review, define and name.

    Organize codes into thematic categories, merge overlapping codes,
    rename for analytical precision, and write theme definitions.
    """

    @allure.title("AC #3-5: Full theme development workflow on real data")
    def test_theme_development_workflow(
        self,
        mcp_server: MCPClient,
        app_context: AppContext,
        sheffield_project: dict,
    ):
        """Build thematic structure from codes applied to real transcript data."""
        sources = sheffield_project["sources"]

        # --- Phase 2 setup: Create and apply codes ---
        with allure.step("Setup: Create codes"):
            code_ids = {}
            for name, color in [
                ("Data sharing attitudes", "#4CAF50"),
                ("Open research barriers", "#F44336"),
                ("Participant consent", "#FF9800"),
                ("Research philosophy", "#2196F3"),
                ("Trust in repositories", "#9C27B0"),
                ("Anonymization challenges", "#795548"),
            ]:
                r = mcp_server.execute(
                    "create_code", {"name": name, "color": color}
                )
                assert r["success"]
                code_ids[name] = r["data"]["code_id"]

        with allure.step("Setup: Apply codes to real passages"):
            ana = sources["Ana"]
            david = sources["David"]

            ops = []

            # Ana on openness
            s, e = _find_segment(ana["text"], "what makes it also difficult to make it open")
            ops.append({
                "code_id": code_ids["Data sharing attitudes"],
                "source_id": ana["id"],
                "start_position": s, "end_position": e,
            })

            # Ana on research philosophy
            s, e = _find_segment(ana["text"], "my analysis are much more craft")
            ops.append({
                "code_id": code_ids["Research philosophy"],
                "source_id": ana["id"],
                "start_position": s, "end_position": e,
            })

            # David on trust
            s, e = _find_segment(david["text"], "trust in the repository")
            ops.append({
                "code_id": code_ids["Trust in repositories"],
                "source_id": david["id"],
                "start_position": s, "end_position": e,
            })

            # David on consent
            s, e = _find_segment(
                david["text"],
                "when I get the consent from them"
                if "when I get the consent from them" in david["text"]
                else "consent"
            )
            ops.append({
                "code_id": code_ids["Participant consent"],
                "source_id": david["id"],
                "start_position": s, "end_position": e,
            })

            result = mcp_server.execute(
                "batch_apply_codes", {"operations": ops}
            )
            assert result["success"]

        # --- Phase 3: Create thematic categories ---
        with allure.step("Phase 3: Create candidate themes via MCP"):
            cat_openness = mcp_server.execute(
                "create_category",
                {
                    "name": "Navigating Openness in Qualitative Research",
                    "memo": "How researchers conceptualize and practice open data sharing",
                },
            )
            assert cat_openness["success"]
            openness_id = cat_openness["data"]["category_id"]

            cat_ethics = mcp_server.execute(
                "create_category",
                {
                    "name": "Ethical Stewardship of Participant Data",
                    "memo": "Tensions between open science ideals and participant protection",
                },
            )
            assert cat_ethics["success"]
            ethics_id = cat_ethics["data"]["category_id"]

            cat_infra = mcp_server.execute(
                "create_category",
                {
                    "name": "Infrastructures of Trust",
                    "memo": "Institutional systems, repositories, and policies shaping open practices",
                },
            )
            assert cat_infra["success"]
            infra_id = cat_infra["data"]["category_id"]

        # --- Phase 3: Organize codes into themes ---
        with allure.step("Phase 3: Move codes into thematic categories via MCP"):
            moves = [
                (code_ids["Data sharing attitudes"], openness_id),
                (code_ids["Research philosophy"], openness_id),
                (code_ids["Participant consent"], ethics_id),
                (code_ids["Anonymization challenges"], ethics_id),
                (code_ids["Open research barriers"], infra_id),
                (code_ids["Trust in repositories"], infra_id),
            ]
            for cid, catid in moves:
                r = mcp_server.execute(
                    "move_code_to_category",
                    {"code_id": cid, "category_id": catid},
                )
                assert r["success"]

        # --- Phase 4: Merge overlapping codes ---
        with allure.step("Phase 4: Merge 'Open research barriers' into 'Trust in repositories'"):
            merge_result = mcp_server.execute(
                "merge_codes",
                {
                    "source_code_id": code_ids["Open research barriers"],
                    "target_code_id": code_ids["Trust in repositories"],
                },
            )
            assert merge_result["success"]
            assert merge_result["data"]["segments_moved"] >= 0

            # Verify source code deleted
            get_deleted = mcp_server.execute(
                "get_code", {"code_id": code_ids["Open research barriers"]}
            )
            assert not get_deleted["success"]

        # --- Phase 5: Rename and define themes ---
        with allure.step("Phase 5: Rename code for analytical precision via MCP"):
            rename_result = mcp_server.execute(
                "rename_code",
                {
                    "code_id": code_ids["Trust in repositories"],
                    "new_name": "Institutional trust and open infrastructure",
                },
            )
            assert rename_result["success"]
            assert rename_result["data"]["old_name"] == "Trust in repositories"

        with allure.step("Phase 5: Write analytical theme definition via MCP"):
            memo = (
                "THEME: Institutional Trust and Open Infrastructure\n\n"
                "DEFINITION: Captures how researchers' willingness to share data\n"
                "is shaped by trust in institutional repositories, university\n"
                "policies, and the broader open science infrastructure.\n\n"
                "SCOPE: Repository trust, GDPR compliance, university support,\n"
                "data management policies, FAIR principles.\n\n"
                "KEY EVIDENCE: David emphasizes 'trust in the repository' as\n"
                "prerequisite for sharing; Ana uses Open Science Framework\n"
                "proactively from copyleft background."
            )
            memo_result = mcp_server.execute(
                "update_code_memo",
                {"code_id": code_ids["Trust in repositories"], "memo": memo},
            )
            assert memo_result["success"]

        # --- Verify final state ---
        with allure.step("Verify final codebook state via MCP"):
            codes = mcp_server.execute("list_codes", {})
            assert codes["success"]
            # Started with 6, merged 1 away = 5 remaining
            assert len(codes["data"]) == 5

            categories = mcp_server.execute("list_categories", {})
            assert categories["success"]
            assert len(categories["data"]) == 3
            cat_names = {c["name"] for c in categories["data"]}
            assert "Navigating Openness in Qualitative Research" in cat_names
            assert "Ethical Stewardship of Participant Data" in cat_names
            assert "Infrastructures of Trust" in cat_names

        with allure.step("Verify renamed code has memo with theme definition"):
            detail = mcp_server.execute(
                "get_code",
                {"code_id": code_ids["Trust in repositories"]},
            )
            assert detail["success"]
            assert detail["data"]["name"] == "Institutional trust and open infrastructure"
            assert "DEFINITION:" in detail["data"]["memo"]
            assert "SCOPE:" in detail["data"]["memo"]


# =============================================================================
# Phase 6: Full Workflow — Complete Thematic Analysis on Real Data
# =============================================================================


@allure.story("QC-051.02 Sheffield Replication")
class TestPhase6FullWorkflowRealData:
    """
    Complete end-to-end thematic analysis on real Sheffield transcripts
    with audit trail verification (Lincoln & Guba trustworthiness).
    """

    @allure.title("AC #6.1: Complete TA workflow on real data with audit trail")
    def test_full_workflow_real_data(
        self,
        mcp_server: MCPClient,
        app_context: AppContext,
        sheffield_project: dict,
    ):
        """
        Full MCP-only workflow on real transcripts:
        Create codes → Apply to real passages → Create categories →
        Organize → Delete redundant code → Verify audit trail
        """
        sources = sheffield_project["sources"]
        ana = sources["Ana"]
        david = sources["David"]
        jessica = sources["Jessica"]

        # ---- Phase 2: Create codes ----
        with allure.step("Phase 2: Create initial codes"):
            code_ids = {}
            for name, color in [
                ("Open data practices", "#4CAF50"),
                ("Ethical dilemmas", "#F44336"),
                ("Software preferences", "#2196F3"),
                ("Participant voice", "#FF9800"),
            ]:
                r = mcp_server.execute(
                    "create_code", {"name": name, "color": color}
                )
                assert r["success"]
                code_ids[name] = r["data"]["code_id"]

        # ---- Phase 2: Apply to real passages ----
        with allure.step("Phase 2: Apply codes to real transcript passages"):
            ops = []

            # Ana on open practices
            s, e = _find_segment(
                ana["text"],
                "I wanted to have it on a platform, and I wanted to have it open from the beginning"
                if "I wanted to have it on a platform" in ana["text"]
                else "I wanted to have it open"
            )
            ops.append({
                "code_id": code_ids["Open data practices"],
                "source_id": ana["id"],
                "start_position": s, "end_position": e,
            })

            # David on ethical dilemmas
            s, e = _find_segment(
                david["text"],
                "respecting the basis of consent"
                if "respecting the basis of consent" in david["text"]
                else "consent"
            )
            ops.append({
                "code_id": code_ids["Ethical dilemmas"],
                "source_id": david["id"],
                "start_position": s, "end_position": e,
            })

            # Jessica on software
            s, e = _find_segment(jessica["text"], "I used Nvivo")
            ops.append({
                "code_id": code_ids["Software preferences"],
                "source_id": jessica["id"],
                "start_position": s, "end_position": e,
            })

            result = mcp_server.execute(
                "batch_apply_codes", {"operations": ops}
            )
            assert result["success"]
            assert result["data"]["succeeded"] == 3

        # ---- Phase 3: Create categories ----
        with allure.step("Phase 3: Create thematic categories"):
            cat1 = mcp_server.execute(
                "create_category",
                {"name": "Cultures of Openness"},
            )
            assert cat1["success"]

            cat2 = mcp_server.execute(
                "create_category",
                {"name": "Ethics and Responsibility"},
            )
            assert cat2["success"]

        with allure.step("Phase 3: Organize codes"):
            mcp_server.execute(
                "move_code_to_category",
                {
                    "code_id": code_ids["Open data practices"],
                    "category_id": cat1["data"]["category_id"],
                },
            )
            mcp_server.execute(
                "move_code_to_category",
                {
                    "code_id": code_ids["Software preferences"],
                    "category_id": cat1["data"]["category_id"],
                },
            )
            mcp_server.execute(
                "move_code_to_category",
                {
                    "code_id": code_ids["Ethical dilemmas"],
                    "category_id": cat2["data"]["category_id"],
                },
            )
            mcp_server.execute(
                "move_code_to_category",
                {
                    "code_id": code_ids["Participant voice"],
                    "category_id": cat2["data"]["category_id"],
                },
            )

        # ---- Phase 4-5: Delete unused code ----
        with allure.step("Phase 4: Delete unused 'Participant voice' code"):
            del_result = mcp_server.execute(
                "delete_code",
                {"code_id": code_ids["Participant voice"]},
            )
            assert del_result["success"]
            assert del_result["data"]["deleted"] is True

        # ---- Phase 6: Verify ----
        with allure.step("Phase 6: Verify final codebook"):
            final_codes = mcp_server.execute("list_codes", {})
            assert final_codes["success"]
            assert len(final_codes["data"]) == 3
            code_names = {c["name"] for c in final_codes["data"]}
            assert "Open data practices" in code_names
            assert "Ethical dilemmas" in code_names
            assert "Software preferences" in code_names

            final_cats = mcp_server.execute("list_categories", {})
            assert final_cats["success"]
            assert len(final_cats["data"]) == 2

        with allure.step("Phase 6: Verify segment coverage on real data"):
            total_segments = 0
            for name, info in sources.items():
                seg = mcp_server.execute(
                    "list_segments_for_source",
                    {"source_id": info["id"]},
                )
                if seg["success"] and seg["data"]:
                    total_segments += len(seg["data"])
            assert total_segments == 3

        with allure.step("Phase 6: Verify event audit trail (Lincoln & Guba)"):
            history = app_context.event_bus.get_history()
            event_types = [e.event_type for e in history]

            assert "coding.code_created" in event_types
            assert "coding.segment_coded" in event_types
            assert "coding.category_created" in event_types
            assert "coding.code_moved_to_category" in event_types
            assert "coding.code_deleted" in event_types

            # 4 codes created, 1 deleted = 3 remaining (verified above)
            assert event_types.count("coding.code_created") == 4
            assert event_types.count("coding.segment_coded") == 3
            assert event_types.count("coding.category_created") == 2
            assert event_types.count("coding.code_deleted") == 1
