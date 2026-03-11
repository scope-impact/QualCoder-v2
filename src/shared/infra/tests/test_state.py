"""Tests for ProjectState session state management."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import allure
import pytest

from src.shared.common.types import SourceId
from src.shared.infra.state import ProjectState


@allure.epic("Shared Infrastructure")
@allure.feature("Shared Infrastructure")
@allure.story("QC-000.07 Application State")
class TestProjectStateInitialDefaults:
    """Initial ProjectState should have sensible defaults."""

    @allure.title("New state has no project, screen, source, or recent projects")
    def test_initial_state_defaults(self) -> None:
        state = ProjectState()

        assert state.project is None
        assert state.is_project_open is False
        assert state.current_screen is None
        assert state.current_source_id is None
        assert state.recent_projects == []

    @allure.title("is_project_open returns True when project is set")
    def test_is_project_open_true_when_project_set(self) -> None:
        state = ProjectState()
        state.project = MagicMock()

        assert state.is_project_open is True


@allure.epic("Shared Infrastructure")
@allure.feature("Shared Infrastructure")
@allure.story("QC-000.07 Application State")
class TestProjectStateClear:
    """Tests for ProjectState.clear() method."""

    @allure.title("clear() resets project, screen, source but preserves recent projects")
    def test_clear_resets_transient_state_but_preserves_recent(self) -> None:
        state = ProjectState()
        state.project = MagicMock()
        state.current_screen = "text_coding"
        state.current_source_id = SourceId(42)
        state.recent_projects = [MagicMock()]

        state.clear()

        assert state.project is None
        assert state.current_screen is None
        assert state.current_source_id is None
        assert len(state.recent_projects) == 1


@allure.epic("Shared Infrastructure")
@allure.feature("Shared Infrastructure")
@allure.story("QC-000.07 Application State")
class TestProjectStateRecentProjects:
    """Tests for ProjectState.add_to_recent() method."""

    @allure.title("add_to_recent adds project at front with timestamp")
    def test_add_to_recent_adds_at_front_with_timestamp(self) -> None:
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

    @allure.title("add_to_recent deduplicates by path and limits to 10")
    def test_add_to_recent_deduplicates_and_limits(self) -> None:
        state = ProjectState()

        # Add a project twice with different names
        project = MagicMock()
        project.path = Path("/test/project.qda")
        project.name = "Original"
        state.add_to_recent(project)

        project.name = "Updated"
        state.add_to_recent(project)

        assert len(state.recent_projects) == 1
        assert state.recent_projects[0].name == "Updated"

        # Add 15 distinct projects — list should cap at 10
        for i in range(15):
            p = MagicMock()
            p.path = Path(f"/test/project{i}.qda")
            p.name = f"Project {i}"
            state.add_to_recent(p)

        assert len(state.recent_projects) == 10
        assert state.recent_projects[0].name == "Project 14"
