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

    def test_creates_project_controller(self, coordinator: ApplicationCoordinator):
        """Coordinator creates a project controller."""
        assert coordinator.project_controller is not None

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
        project_path = tmp_path / "test.qda"
        project_path.touch()

        result = coordinator.open_project(str(project_path))

        assert isinstance(result, Success)

    def test_open_project_failure(self, coordinator: ApplicationCoordinator):
        """Opening a nonexistent project fails."""
        result = coordinator.open_project("/nonexistent/project.qda")

        assert isinstance(result, Failure)


class TestCreateProject:
    """Tests for AC #2: Researcher can create a new project."""

    def test_create_project_success(
        self, coordinator: ApplicationCoordinator, tmp_path: Path
    ):
        """Creating a new project succeeds."""
        project_path = tmp_path / "new_project.qda"

        result = coordinator.create_project("My Project", str(project_path))

        assert isinstance(result, Success)

    def test_create_project_with_empty_name_fails(
        self, coordinator: ApplicationCoordinator, tmp_path: Path
    ):
        """Creating a project with empty name fails."""
        project_path = tmp_path / "empty.qda"

        result = coordinator.create_project("", str(project_path))

        assert isinstance(result, Failure)


class TestNavigateToSegment:
    """Tests for AC #6: Agent can navigate to a specific source or segment."""

    def test_navigate_fails_without_project(self, coordinator: ApplicationCoordinator):
        """Navigation fails when no project is open."""
        result = coordinator.navigate_to_segment(
            source_id=1,
            start_pos=0,
            end_pos=100,
        )

        assert isinstance(result, Failure)

    def test_navigate_fails_for_nonexistent_source(
        self, coordinator: ApplicationCoordinator, tmp_path: Path
    ):
        """Navigation fails for nonexistent source."""
        project_path = tmp_path / "test.qda"
        coordinator.create_project("Test", str(project_path))

        result = coordinator.navigate_to_segment(
            source_id=999,
            start_pos=0,
            end_pos=100,
        )

        assert isinstance(result, Failure)


class TestProjectContext:
    """Tests for AC #5: Agent can query current project context."""

    def test_context_when_no_project(self, coordinator: ApplicationCoordinator):
        """Returns closed state when no project."""
        context = coordinator.get_project_context()

        assert context["project_open"] is False

    def test_context_with_project(
        self, coordinator: ApplicationCoordinator, tmp_path: Path
    ):
        """Returns project info when project is open."""
        project_path = tmp_path / "test.qda"
        coordinator.create_project("Test Project", str(project_path))

        context = coordinator.get_project_context()

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

    def test_mcp_tools_use_same_controller(
        self, coordinator: ApplicationCoordinator, tmp_path: Path
    ):
        """MCP tools share controller state with coordinator."""
        project_path = tmp_path / "test.qda"
        coordinator.create_project("Test", str(project_path))

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
