"""Tests for ProjectState session state management."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import allure
import pytest

from src.shared.common.types import SourceId
from src.shared.infra.state import ProjectState


@allure.epic("QualCoder v2")
@allure.feature("Shared Infrastructure")
@allure.story("QC-000.07 Application State")
class TestProjectStateDefaults:
    """Initial ProjectState should have sensible defaults."""

    @allure.title("New state has defaults; is_project_open reflects project; clear resets transient state")
    def test_defaults_project_open_and_clear(self) -> None:
        state = ProjectState()

        # Initial defaults
        assert state.project is None
        assert state.is_project_open is False
        assert state.current_screen is None
        assert state.current_source_id is None
        assert state.recent_projects == []

        # is_project_open returns True when project is set
        state.project = MagicMock()
        assert state.is_project_open is True

        # Set additional state
        state.current_screen = "text_coding"
        state.current_source_id = SourceId(42)
        state.recent_projects = [MagicMock()]

        # clear() resets transient but preserves recent projects
        state.clear()
        assert state.project is None
        assert state.current_screen is None
        assert state.current_source_id is None
        assert len(state.recent_projects) == 1


@allure.epic("QualCoder v2")
@allure.feature("Shared Infrastructure")
@allure.story("QC-000.07 Application State")
class TestProjectStateRecentProjects:
    """Tests for ProjectState.add_to_recent() method."""

    @allure.title("add_to_recent adds at front with timestamp, deduplicates, and limits to 10")
    def test_add_to_recent_ordering_dedup_and_limit(self) -> None:
        state = ProjectState()

        project1 = MagicMock()
        project1.path = Path("/test/project1.qda")
        project1.name = "Project 1"

        project2 = MagicMock()
        project2.path = Path("/test/project2.qda")
        project2.name = "Project 2"

        state.add_to_recent(project1)
        state.add_to_recent(project2)

        assert len(state.recent_projects) == 2
        assert state.recent_projects[0].name == "Project 2"
        assert state.recent_projects[1].name == "Project 1"
        assert state.recent_projects[0].last_opened is not None

        # Deduplicates by path
        project = MagicMock()
        project.path = Path("/test/dedup.qda")
        project.name = "Original"
        state.add_to_recent(project)

        project.name = "Updated"
        state.add_to_recent(project)

        dedup_entries = [p for p in state.recent_projects if p.path == Path("/test/dedup.qda")]
        assert len(dedup_entries) == 1
        assert dedup_entries[0].name == "Updated"

        # Limits to 10
        state2 = ProjectState()
        for i in range(15):
            p = MagicMock()
            p.path = Path(f"/test/project{i}.qda")
            p.name = f"Project {i}"
            state2.add_to_recent(p)

        assert len(state2.recent_projects) == 10
        assert state2.recent_projects[0].name == "Project 14"
