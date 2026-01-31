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


class TestCaseCommands:
    """Tests for case commands."""

    def test_create_case_successfully(
        self,
        project_controller,
        event_bus,
        existing_project_path: Path,
    ):
        """Test creating a case in the project."""
        from src.application.projects.controller import (
            CreateCaseCommand,
            OpenProjectCommand,
        )

        # First open a project
        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )

        # Create case
        command = CreateCaseCommand(
            name="Participant A",
            description="First interview subject",
            memo="Recruited from university",
        )

        result = project_controller.create_case(command)

        assert isinstance(result, Success)
        case = result.unwrap()
        assert case.name == "Participant A"
        assert case.description == "First interview subject"

        # Verify event was published
        history = event_bus.get_history()
        assert any("case_created" in h.event_type for h in history)

    def test_create_case_fails_without_open_project(
        self,
        project_controller,
    ):
        """Test failure when no project is open."""
        from src.application.projects.controller import CreateCaseCommand

        command = CreateCaseCommand(name="Participant A")

        result = project_controller.create_case(command)

        assert isinstance(result, Failure)

    def test_create_case_fails_with_empty_name(
        self,
        project_controller,
        existing_project_path: Path,
    ):
        """Test failure with empty case name."""
        from src.application.projects.controller import (
            CreateCaseCommand,
            OpenProjectCommand,
        )

        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )

        command = CreateCaseCommand(name="")

        result = project_controller.create_case(command)

        assert isinstance(result, Failure)

    def test_create_case_fails_with_duplicate_name(
        self,
        project_controller,
        existing_project_path: Path,
    ):
        """Test failure with duplicate case name."""
        from src.application.projects.controller import (
            CreateCaseCommand,
            OpenProjectCommand,
        )

        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )

        # Create first case
        project_controller.create_case(CreateCaseCommand(name="Participant A"))

        # Try to create duplicate
        result = project_controller.create_case(CreateCaseCommand(name="Participant A"))

        assert isinstance(result, Failure)

    def test_update_case_successfully(
        self,
        project_controller,
        event_bus,
        existing_project_path: Path,
    ):
        """Test updating an existing case."""
        from src.application.projects.controller import (
            CreateCaseCommand,
            OpenProjectCommand,
            UpdateCaseCommand,
        )

        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )

        # Create case
        create_result = project_controller.create_case(
            CreateCaseCommand(name="Original Name")
        )
        case = create_result.unwrap()

        # Update case
        command = UpdateCaseCommand(
            case_id=case.id.value,
            name="Updated Name",
            description="New description",
        )

        result = project_controller.update_case(command)

        assert isinstance(result, Success)
        updated = result.unwrap()
        assert updated.name == "Updated Name"
        assert updated.description == "New description"

        # Verify event was published
        history = event_bus.get_history()
        assert any("case_updated" in h.event_type for h in history)

    def test_remove_case_successfully(
        self,
        project_controller,
        event_bus,
        existing_project_path: Path,
    ):
        """Test removing a case."""
        from src.application.projects.controller import (
            CreateCaseCommand,
            OpenProjectCommand,
            RemoveCaseCommand,
        )

        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )

        # Create case
        create_result = project_controller.create_case(
            CreateCaseCommand(name="To Delete")
        )
        case = create_result.unwrap()

        # Remove case
        command = RemoveCaseCommand(case_id=case.id.value)

        result = project_controller.remove_case(command)

        assert isinstance(result, Success)

        # Verify case is removed
        assert project_controller.get_case(case.id.value) is None

        # Verify event was published
        history = event_bus.get_history()
        assert any("case_removed" in h.event_type for h in history)

    def test_get_cases_returns_all_cases(
        self,
        project_controller,
        existing_project_path: Path,
    ):
        """Test getting all cases."""
        from src.application.projects.controller import (
            CreateCaseCommand,
            OpenProjectCommand,
        )

        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )

        project_controller.create_case(CreateCaseCommand(name="Participant A"))
        project_controller.create_case(CreateCaseCommand(name="Participant B"))

        cases = project_controller.get_cases()

        assert len(cases) == 2

    def test_get_project_context_includes_cases(
        self,
        project_controller,
        existing_project_path: Path,
    ):
        """Test that project context includes case information."""
        from src.application.projects.controller import (
            CreateCaseCommand,
            OpenProjectCommand,
        )

        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )
        project_controller.create_case(
            CreateCaseCommand(name="Participant A", description="First subject")
        )

        context = project_controller.get_project_context()

        assert context["case_count"] == 1
        assert len(context["cases"]) == 1
        assert context["cases"][0]["name"] == "Participant A"


class TestSourceLinkingCommands:
    """Tests for linking sources to cases."""

    def test_link_source_to_case_successfully(
        self,
        project_controller,
        event_bus,
        existing_project_path: Path,
        sample_source_path: Path,
    ):
        """Test linking a source to a case."""
        from src.application.projects.controller import (
            AddSourceCommand,
            CreateCaseCommand,
            LinkSourceToCaseCommand,
            OpenProjectCommand,
        )

        # Open project
        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )

        # Add source
        source_result = project_controller.add_source(
            AddSourceCommand(source_path=str(sample_source_path))
        )
        source = source_result.unwrap()

        # Create case
        case_result = project_controller.create_case(
            CreateCaseCommand(name="Participant A")
        )
        case = case_result.unwrap()

        # Link source to case
        command = LinkSourceToCaseCommand(
            case_id=case.id.value,
            source_id=source.id.value,
        )
        result = project_controller.link_source_to_case(command)

        assert isinstance(result, Success)

        # Verify event was published
        history = event_bus.get_history()
        assert any("source_linked" in h.event_type for h in history)

    def test_link_source_fails_without_open_project(self, project_controller):
        """Test failure when no project is open."""
        from src.application.projects.controller import LinkSourceToCaseCommand

        command = LinkSourceToCaseCommand(case_id=1, source_id=10)
        result = project_controller.link_source_to_case(command)

        assert isinstance(result, Failure)

    def test_link_source_fails_for_nonexistent_source(
        self,
        project_controller,
        existing_project_path: Path,
    ):
        """Test failure when source doesn't exist."""
        from src.application.projects.controller import (
            CreateCaseCommand,
            LinkSourceToCaseCommand,
            OpenProjectCommand,
        )

        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )
        case_result = project_controller.create_case(
            CreateCaseCommand(name="Participant A")
        )
        case = case_result.unwrap()

        command = LinkSourceToCaseCommand(case_id=case.id.value, source_id=999)
        result = project_controller.link_source_to_case(command)

        assert isinstance(result, Failure)

    def test_link_source_fails_for_nonexistent_case(
        self,
        project_controller,
        existing_project_path: Path,
        sample_source_path: Path,
    ):
        """Test failure when case doesn't exist."""
        from src.application.projects.controller import (
            AddSourceCommand,
            LinkSourceToCaseCommand,
            OpenProjectCommand,
        )

        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )
        source_result = project_controller.add_source(
            AddSourceCommand(source_path=str(sample_source_path))
        )
        source = source_result.unwrap()

        command = LinkSourceToCaseCommand(case_id=999, source_id=source.id.value)
        result = project_controller.link_source_to_case(command)

        assert isinstance(result, Failure)

    def test_unlink_source_from_case_successfully(
        self,
        project_controller,
        event_bus,
        existing_project_path: Path,
        sample_source_path: Path,
    ):
        """Test unlinking a source from a case."""
        from src.application.projects.controller import (
            AddSourceCommand,
            CreateCaseCommand,
            LinkSourceToCaseCommand,
            OpenProjectCommand,
            UnlinkSourceFromCaseCommand,
        )

        # Setup: open project, add source, create case, link
        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )
        source_result = project_controller.add_source(
            AddSourceCommand(source_path=str(sample_source_path))
        )
        source = source_result.unwrap()
        case_result = project_controller.create_case(
            CreateCaseCommand(name="Participant A")
        )
        case = case_result.unwrap()
        project_controller.link_source_to_case(
            LinkSourceToCaseCommand(case_id=case.id.value, source_id=source.id.value)
        )

        # Unlink
        command = UnlinkSourceFromCaseCommand(
            case_id=case.id.value,
            source_id=source.id.value,
        )
        result = project_controller.unlink_source_from_case(command)

        assert isinstance(result, Success)

        # Verify event was published
        history = event_bus.get_history()
        assert any("source_unlinked" in h.event_type for h in history)

    def test_unlink_source_fails_when_not_linked(
        self,
        project_controller,
        existing_project_path: Path,
        sample_source_path: Path,
    ):
        """Test failure when source is not linked to case."""
        from src.application.projects.controller import (
            AddSourceCommand,
            CreateCaseCommand,
            OpenProjectCommand,
            UnlinkSourceFromCaseCommand,
        )

        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )
        source_result = project_controller.add_source(
            AddSourceCommand(source_path=str(sample_source_path))
        )
        source = source_result.unwrap()
        case_result = project_controller.create_case(
            CreateCaseCommand(name="Participant A")
        )
        case = case_result.unwrap()

        # Try to unlink without linking first
        command = UnlinkSourceFromCaseCommand(
            case_id=case.id.value,
            source_id=source.id.value,
        )
        result = project_controller.unlink_source_from_case(command)

        assert isinstance(result, Failure)


class TestCaseAttributeCommands:
    """Tests for case attribute commands."""

    def test_set_case_attribute_successfully(
        self,
        project_controller,
        event_bus,
        existing_project_path: Path,
    ):
        """Test setting an attribute on a case."""
        from src.application.projects.controller import (
            CreateCaseCommand,
            OpenProjectCommand,
            SetCaseAttributeCommand,
        )

        # Open project and create case
        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )
        case_result = project_controller.create_case(
            CreateCaseCommand(name="Participant A")
        )
        case = case_result.unwrap()

        # Set attribute
        command = SetCaseAttributeCommand(
            case_id=case.id.value,
            attr_name="age",
            attr_type="number",
            attr_value=25,
        )
        result = project_controller.set_case_attribute(command)

        assert isinstance(result, Success)

        # Verify event was published
        history = event_bus.get_history()
        assert any("attribute_set" in h.event_type for h in history)

    def test_set_case_attribute_fails_without_open_project(self, project_controller):
        """Test failure when no project is open."""
        from src.application.projects.controller import SetCaseAttributeCommand

        command = SetCaseAttributeCommand(
            case_id=1,
            attr_name="age",
            attr_type="number",
            attr_value=25,
        )
        result = project_controller.set_case_attribute(command)

        assert isinstance(result, Failure)

    def test_set_case_attribute_fails_for_nonexistent_case(
        self,
        project_controller,
        existing_project_path: Path,
    ):
        """Test failure when case doesn't exist."""
        from src.application.projects.controller import (
            OpenProjectCommand,
            SetCaseAttributeCommand,
        )

        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )

        command = SetCaseAttributeCommand(
            case_id=999,
            attr_name="age",
            attr_type="number",
            attr_value=25,
        )
        result = project_controller.set_case_attribute(command)

        assert isinstance(result, Failure)

    def test_set_case_attribute_fails_for_invalid_type(
        self,
        project_controller,
        existing_project_path: Path,
    ):
        """Test failure for invalid attribute type."""
        from src.application.projects.controller import (
            CreateCaseCommand,
            OpenProjectCommand,
            SetCaseAttributeCommand,
        )

        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )
        case_result = project_controller.create_case(
            CreateCaseCommand(name="Participant A")
        )
        case = case_result.unwrap()

        command = SetCaseAttributeCommand(
            case_id=case.id.value,
            attr_name="age",
            attr_type="invalid_type",
            attr_value=25,
        )
        result = project_controller.set_case_attribute(command)

        assert isinstance(result, Failure)

    def test_get_case_includes_attributes(
        self,
        project_controller,
        existing_project_path: Path,
    ):
        """Test that get_case includes attributes."""
        from src.application.projects.controller import (
            CreateCaseCommand,
            OpenProjectCommand,
            SetCaseAttributeCommand,
        )

        project_controller.open_project(
            OpenProjectCommand(path=str(existing_project_path))
        )
        case_result = project_controller.create_case(
            CreateCaseCommand(name="Participant A")
        )
        case = case_result.unwrap()

        project_controller.set_case_attribute(
            SetCaseAttributeCommand(
                case_id=case.id.value,
                attr_name="age",
                attr_type="number",
                attr_value=25,
            )
        )

        retrieved = project_controller.get_case(case.id.value)
        assert retrieved is not None
        assert len(retrieved.attributes) == 1
        assert retrieved.attributes[0].name == "age"
        assert retrieved.attributes[0].value == 25
