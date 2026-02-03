"""
Tests for ProjectState session state management.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from src.shared.common.types import SourceId
from src.shared.infra.state import ProjectState


class TestProjectStateBasic:
    """Tests for basic ProjectState functionality."""

    def test_initial_state_has_no_project(self) -> None:
        """New state should have no project open."""
        state = ProjectState()

        assert state.project is None
        assert state.is_project_open is False

    def test_initial_state_has_no_screen(self) -> None:
        """New state should have no current screen."""
        state = ProjectState()

        assert state.current_screen is None

    def test_initial_state_has_no_source(self) -> None:
        """New state should have no current source."""
        state = ProjectState()

        assert state.current_source_id is None

    def test_initial_state_has_empty_recent_projects(self) -> None:
        """New state should have empty recent projects list."""
        state = ProjectState()

        assert state.recent_projects == []

    def test_is_project_open_true_when_project_set(self) -> None:
        """is_project_open should return True when project is set."""
        state = ProjectState()
        state.project = MagicMock()

        assert state.is_project_open is True


class TestProjectStateClear:
    """Tests for ProjectState.clear() method."""

    def test_clear_removes_project(self) -> None:
        """clear() should remove the project."""
        state = ProjectState()
        state.project = MagicMock()

        state.clear()

        assert state.project is None

    def test_clear_removes_screen(self) -> None:
        """clear() should remove the current screen."""
        state = ProjectState()
        state.current_screen = "text_coding"

        state.clear()

        assert state.current_screen is None

    def test_clear_removes_source_id(self) -> None:
        """clear() should remove the current source ID."""
        state = ProjectState()
        state.current_source_id = SourceId(42)

        state.clear()

        assert state.current_source_id is None

    def test_clear_preserves_recent_projects(self) -> None:
        """clear() should NOT clear recent projects list."""
        state = ProjectState()
        state.recent_projects = [MagicMock()]

        state.clear()

        assert len(state.recent_projects) == 1


class TestProjectStateRecentProjects:
    """Tests for ProjectState.add_to_recent() method."""

    def test_add_to_recent_adds_project(self) -> None:
        """add_to_recent() should add project to list."""
        state = ProjectState()
        project = MagicMock()
        project.path = Path("/test/project.qda")
        project.name = "Test Project"

        state.add_to_recent(project)

        assert len(state.recent_projects) == 1
        assert state.recent_projects[0].path == Path("/test/project.qda")
        assert state.recent_projects[0].name == "Test Project"

    def test_add_to_recent_adds_at_front(self) -> None:
        """add_to_recent() should add new projects at front of list."""
        state = ProjectState()

        project1 = MagicMock()
        project1.path = Path("/test/project1.qda")
        project1.name = "Project 1"

        project2 = MagicMock()
        project2.path = Path("/test/project2.qda")
        project2.name = "Project 2"

        state.add_to_recent(project1)
        state.add_to_recent(project2)

        assert state.recent_projects[0].name == "Project 2"
        assert state.recent_projects[1].name == "Project 1"

    def test_add_to_recent_removes_duplicate(self) -> None:
        """add_to_recent() should remove existing entry for same path."""
        state = ProjectState()

        project = MagicMock()
        project.path = Path("/test/project.qda")
        project.name = "Original Name"

        state.add_to_recent(project)

        # Re-add with different name
        project.name = "Updated Name"
        state.add_to_recent(project)

        assert len(state.recent_projects) == 1
        assert state.recent_projects[0].name == "Updated Name"

    def test_add_to_recent_limits_to_10(self) -> None:
        """add_to_recent() should limit list to 10 projects."""
        state = ProjectState()

        # Add 15 projects
        for i in range(15):
            project = MagicMock()
            project.path = Path(f"/test/project{i}.qda")
            project.name = f"Project {i}"
            state.add_to_recent(project)

        assert len(state.recent_projects) == 10
        # Most recent should be at front
        assert state.recent_projects[0].name == "Project 14"

    def test_add_to_recent_sets_last_opened(self) -> None:
        """add_to_recent() should set last_opened timestamp."""
        state = ProjectState()
        project = MagicMock()
        project.path = Path("/test/project.qda")
        project.name = "Test Project"

        state.add_to_recent(project)

        assert state.recent_projects[0].last_opened is not None


class TestSessionStateAlias:
    """Test that SessionState is an alias for ProjectState."""

    def test_session_state_is_project_state(self) -> None:
        """SessionState should be an alias for ProjectState."""
        from src.shared.infra.state import SessionState

        assert SessionState is ProjectState
