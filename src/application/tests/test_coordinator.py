"""
Tests for Application Coordinator

Tests the central wiring and integration for QC-026.
"""

from pathlib import Path

import pytest
from returns.result import Failure, Success

from src.application.coordinator import (
    ApplicationCoordinator,
    get_coordinator,
    reset_coordinator,
)


@pytest.fixture
def coordinator() -> ApplicationCoordinator:
    """Create a fresh coordinator for testing."""
    reset_coordinator()
    return ApplicationCoordinator()


@pytest.fixture(autouse=True)
def cleanup_coordinator():
    """Clean up coordinator after each test."""
    yield
    reset_coordinator()


class TestCoordinatorInitialization:
    """Tests for coordinator initialization."""

    def test_creates_event_bus(self, coordinator: ApplicationCoordinator):
        """Coordinator creates an event bus."""
        assert coordinator.event_bus is not None

    def test_has_sub_coordinators(self, coordinator: ApplicationCoordinator):
        """Coordinator exposes per-context sub-coordinators."""
        assert coordinator.projects is not None
        assert coordinator.sources is not None
        assert coordinator.cases is not None
        assert coordinator.folders is not None
        assert coordinator.coding is not None
        assert coordinator.navigation is not None
        assert coordinator.settings is not None

    def test_start_and_stop(self, coordinator: ApplicationCoordinator):
        """Coordinator can start and stop."""
        coordinator.start()
        coordinator.stop()
        # No exception means success


class TestOpenProject:
    """Tests for AC #1: Researcher can open an existing project file."""

    def test_open_project_success(
        self, coordinator: ApplicationCoordinator, tmp_path: Path
    ):
        """Opening an existing project succeeds."""
        # Create a proper .qda database file with schema
        from src.contexts.projects.infra.project_repository import (
            SQLiteProjectRepository,
        )

        project_path = tmp_path / "test.qda"
        repo = SQLiteProjectRepository()
        repo.create_database(project_path, "Test Project")

        result = coordinator.projects.open_project(str(project_path))

        assert isinstance(result, Success)

    def test_open_project_failure(self, coordinator: ApplicationCoordinator):
        """Opening a nonexistent project fails."""
        result = coordinator.projects.open_project("/nonexistent/project.qda")

        assert isinstance(result, Failure)


class TestCreateProject:
    """Tests for AC #2: Researcher can create a new project."""

    def test_create_project_success(
        self, coordinator: ApplicationCoordinator, tmp_path: Path
    ):
        """Creating a new project succeeds."""
        project_path = tmp_path / "new_project.qda"

        result = coordinator.projects.create_project("My Project", str(project_path))

        assert isinstance(result, Success)

    def test_create_project_with_empty_name_fails(
        self, coordinator: ApplicationCoordinator, tmp_path: Path
    ):
        """Creating a project with empty name fails."""
        project_path = tmp_path / "empty.qda"

        result = coordinator.projects.create_project("", str(project_path))

        assert isinstance(result, Failure)


class TestNavigateToSegment:
    """Tests for AC #6: Agent can navigate to a specific source or segment."""

    def test_navigate_fails_without_project(self, coordinator: ApplicationCoordinator):
        """Navigation fails when no project is open."""
        from src.application.projects.commands import NavigateToSegmentCommand

        command = NavigateToSegmentCommand(
            source_id=1,
            start_pos=0,
            end_pos=100,
        )
        result = coordinator.navigation.navigate_to_segment(command)

        assert isinstance(result, Failure)

    def test_navigate_fails_for_nonexistent_source(
        self, coordinator: ApplicationCoordinator, tmp_path: Path
    ):
        """Navigation fails for nonexistent source."""
        from src.application.projects.commands import NavigateToSegmentCommand

        project_path = tmp_path / "test.qda"
        coordinator.projects.create_project("Test", str(project_path))

        command = NavigateToSegmentCommand(
            source_id=999,
            start_pos=0,
            end_pos=100,
        )
        result = coordinator.navigation.navigate_to_segment(command)

        assert isinstance(result, Failure)


class TestProjectContext:
    """Tests for AC #5: Agent can query current project context."""

    def test_context_when_no_project(self, coordinator: ApplicationCoordinator):
        """Returns closed state when no project."""
        context = coordinator.projects.get_project_context()

        assert context["project_open"] is False

    def test_context_with_project(
        self, coordinator: ApplicationCoordinator, tmp_path: Path
    ):
        """Returns project info when project is open."""
        project_path = tmp_path / "test.qda"
        coordinator.projects.create_project("Test Project", str(project_path))

        context = coordinator.projects.get_project_context()

        assert context["project_open"] is True
        assert context["project_name"] == "Test Project"


class TestMCPTools:
    """Tests for MCP tools integration."""

    def test_get_mcp_tools(self, coordinator: ApplicationCoordinator):
        """Can get MCP tools from coordinator."""
        tools = coordinator.get_mcp_tools()

        assert tools is not None
        assert "get_project_context" in tools.get_tool_names()
        assert "navigate_to_segment" in tools.get_tool_names()

    def test_mcp_tools_use_same_coordinator(
        self, coordinator: ApplicationCoordinator, tmp_path: Path
    ):
        """MCP tools share state with coordinator."""
        project_path = tmp_path / "test.qda"
        coordinator.projects.create_project("Test", str(project_path))

        tools = coordinator.get_mcp_tools()
        result = tools.execute("get_project_context", {})

        assert isinstance(result, Success)
        assert result.unwrap()["project_name"] == "Test"


class TestSingleton:
    """Tests for singleton pattern."""

    def test_get_coordinator_returns_same_instance(self):
        """get_coordinator returns the same instance."""
        reset_coordinator()

        coord1 = get_coordinator()
        coord2 = get_coordinator()

        assert coord1 is coord2

    def test_reset_clears_instance(self):
        """reset_coordinator clears the instance."""
        coord1 = get_coordinator()
        reset_coordinator()
        coord2 = get_coordinator()

        assert coord1 is not coord2
