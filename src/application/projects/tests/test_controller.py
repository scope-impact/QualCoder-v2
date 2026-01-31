"""
Project Controller Tests.

Tests for the application layer controller that orchestrates project operations.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from returns.result import Failure, Success

pytestmark = pytest.mark.integration


class TestCreateProject:
    """Tests for create_project command."""

    def test_creates_project_successfully(
        self,
        project_controller,
        event_bus,
        sample_project_path: Path,
    ):
        """Test successful project creation."""
        from src.application.projects.controller import CreateProjectCommand

        command = CreateProjectCommand(
            name="Test Project",
            path=str(sample_project_path),
            memo="Test memo",
        )

        result = project_controller.create_project(command)

        assert isinstance(result, Success)
        project = result.unwrap()
        assert project.name == "Test Project"
        assert project.path == sample_project_path

        # Verify event was published
        history = event_bus.get_history()
        assert len(history) == 1
        assert "project_created" in history[0].event_type

    def test_fails_with_empty_name(
        self,
        project_controller,
        sample_project_path: Path,
    ):
        """Test failure with empty project name."""
        from src.application.projects.controller import CreateProjectCommand

        command = CreateProjectCommand(
            name="",
            path=str(sample_project_path),
        )

        result = project_controller.create_project(command)

        assert isinstance(result, Failure)

    def test_fails_with_invalid_path(
        self,
        project_controller,
        tmp_path: Path,
    ):
        """Test failure with non-.qda path."""
        from src.application.projects.controller import CreateProjectCommand

        command = CreateProjectCommand(
            name="Test Project",
            path=str(tmp_path / "project.txt"),  # Wrong extension
        )

        result = project_controller.create_project(command)

        assert isinstance(result, Failure)

    def test_updates_current_project(
        self,
        project_controller,
        sample_project_path: Path,
    ):
        """Test that current project is updated after creation."""
        from src.application.projects.controller import CreateProjectCommand

        command = CreateProjectCommand(
            name="Test Project",
            path=str(sample_project_path),
        )

        project_controller.create_project(command)

        current = project_controller.get_current_project()
        assert current is not None
        assert current.name == "Test Project"


class TestOpenProject:
    """Tests for open_project command."""

    def test_opens_existing_project(
        self,
        project_controller,
        event_bus,
        existing_project_path: Path,
    ):
        """Test opening an existing project file."""
        from src.application.projects.controller import OpenProjectCommand

        command = OpenProjectCommand(path=str(existing_project_path))

        result = project_controller.open_project(command)

        assert isinstance(result, Success)
        project = result.unwrap()
        assert project.path == existing_project_path

        # Verify event was published
        history = event_bus.get_history()
        assert len(history) == 1
        assert "project_opened" in history[0].event_type

    def test_fails_with_nonexistent_path(
        self,
        project_controller,
        tmp_path: Path,
    ):
        """Test failure when project file doesn't exist."""
        from src.application.projects.controller import OpenProjectCommand

        command = OpenProjectCommand(
            path=str(tmp_path / "nonexistent.qda"),
        )

        result = project_controller.open_project(command)

        assert isinstance(result, Failure)

    def test_adds_to_recent_projects(
        self,
        project_controller,
        existing_project_path: Path,
    ):
        """Test that opened project is added to recent list."""
        from src.application.projects.controller import OpenProjectCommand

        command = OpenProjectCommand(path=str(existing_project_path))
        project_controller.open_project(command)

        recent = project_controller.get_recent_projects()
        assert len(recent) == 1
        assert recent[0].path == existing_project_path


class TestCloseProject:
    """Tests for close_project command."""

    def test_closes_open_project(
        self,
        project_controller,
        event_bus,
        existing_project_path: Path,
    ):
        """Test closing an open project."""
        from src.application.projects.controller import OpenProjectCommand

        # First open a project
        open_cmd = OpenProjectCommand(path=str(existing_project_path))
        project_controller.open_project(open_cmd)

        # Then close it
        result = project_controller.close_project()

        assert isinstance(result, Success)
        assert project_controller.get_current_project() is None

        # Verify close event was published
        history = event_bus.get_history()
        assert any("project_closed" in h.event_type for h in history)

    def test_fails_when_no_project_open(self, project_controller):
        """Test failure when no project is open."""
        result = project_controller.close_project()

        assert isinstance(result, Failure)


class TestAddSource:
    """Tests for add_source command."""

    def test_adds_source_successfully(
        self,
        project_controller,
        event_bus,
        existing_project_path: Path,
        sample_source_path: Path,
    ):
        """Test adding a source file to the project."""
        from src.application.projects.controller import (
            AddSourceCommand,
            OpenProjectCommand,
        )

        # First open a project
        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )

        # Add source
        command = AddSourceCommand(
            source_path=str(sample_source_path),
            origin="Field Interview",
            memo="First interview",
        )

        result = project_controller.add_source(command)

        assert isinstance(result, Success)
        source = result.unwrap()
        assert source.name == "interview.txt"
        assert source.origin == "Field Interview"

        # Verify event was published
        history = event_bus.get_history()
        assert any("source_added" in h.event_type for h in history)

    def test_fails_without_open_project(
        self,
        project_controller,
        sample_source_path: Path,
    ):
        """Test failure when no project is open."""
        from src.application.projects.controller import AddSourceCommand

        command = AddSourceCommand(source_path=str(sample_source_path))

        result = project_controller.add_source(command)

        assert isinstance(result, Failure)

    def test_fails_with_nonexistent_source(
        self,
        project_controller,
        existing_project_path: Path,
        tmp_path: Path,
    ):
        """Test failure when source file doesn't exist."""
        from src.application.projects.controller import (
            AddSourceCommand,
            OpenProjectCommand,
        )

        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )

        command = AddSourceCommand(
            source_path=str(tmp_path / "nonexistent.txt"),
        )

        result = project_controller.add_source(command)

        assert isinstance(result, Failure)


class TestQueries:
    """Tests for query methods."""

    def test_get_sources_returns_all_sources(
        self,
        project_controller,
        existing_project_path: Path,
        sample_source_path: Path,
    ):
        """Test getting all sources."""
        from src.application.projects.controller import (
            AddSourceCommand,
            OpenProjectCommand,
        )

        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )
        project_controller.add_source(
            AddSourceCommand(source_path=str(sample_source_path))
        )

        sources = project_controller.get_sources()

        assert len(sources) == 1
        assert sources[0].name == "interview.txt"

    def test_get_project_summary(
        self,
        project_controller,
        existing_project_path: Path,
        sample_source_path: Path,
    ):
        """Test getting project summary statistics."""
        from src.application.projects.controller import (
            AddSourceCommand,
            OpenProjectCommand,
        )

        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )
        project_controller.add_source(
            AddSourceCommand(source_path=str(sample_source_path))
        )

        summary = project_controller.get_project_summary()

        assert summary is not None
        assert summary.total_sources == 1
        assert summary.text_count == 1

    def test_get_project_context_for_agent(
        self,
        project_controller,
        existing_project_path: Path,
        sample_source_path: Path,
    ):
        """Test getting project context for AI agent."""
        from src.application.projects.controller import (
            AddSourceCommand,
            OpenProjectCommand,
        )

        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )
        project_controller.add_source(
            AddSourceCommand(source_path=str(sample_source_path))
        )

        context = project_controller.get_project_context()

        assert context["project_open"] is True
        assert context["source_count"] == 1
        assert len(context["sources"]) == 1
        assert context["sources"][0]["name"] == "interview.txt"

    def test_get_project_context_when_closed(self, project_controller):
        """Test project context when no project is open."""
        context = project_controller.get_project_context()

        assert context["project_open"] is False


class TestNavigation:
    """Tests for navigation commands."""

    def test_navigate_to_screen(
        self,
        project_controller,
        event_bus,
    ):
        """Test navigating to a different screen."""
        from src.application.projects.controller import NavigateToScreenCommand

        command = NavigateToScreenCommand(screen_name="coding")

        result = project_controller.navigate_to_screen(command)

        assert isinstance(result, Success)
        assert project_controller.get_current_screen() == "coding"

        # Verify event was published
        history = event_bus.get_history()
        assert any("screen_changed" in h.event_type for h in history)
