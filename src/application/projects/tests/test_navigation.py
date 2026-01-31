"""
Tests for Navigation Commands (AC #4 and AC #6)

TDD tests for:
- AC #4: Researcher can switch between different screens/views
- AC #6: Agent can navigate to a specific source or segment

These tests are written FIRST, before implementation.
"""

from pathlib import Path

import pytest
from returns.result import Failure, Success

from src.application.projects.controller import (
    NavigateToScreenCommand,
    OpenSourceCommand,
)
from src.domain.projects.entities import Project, Source, SourceStatus, SourceType
from src.domain.projects.events import ScreenChanged, SourceOpened
from src.domain.shared.types import SourceId


class TestNavigateToScreen:
    """Tests for AC #4: Switch between screens/views."""

    def test_navigate_to_valid_screen(self, project_controller, event_bus):
        """
        GIVEN a project controller
        WHEN navigating to a valid screen name
        THEN the screen change succeeds and event is published.
        """
        command = NavigateToScreenCommand(screen_name="coding")

        result = project_controller.navigate_to_screen(command)

        assert isinstance(result, Success)
        assert project_controller.get_current_screen() == "coding"

        # Verify event published (history contains EventRecord objects)
        history = event_bus.get_history()
        screen_events = [h for h in history if "screen_changed" in h.event_type]
        assert len(screen_events) >= 1

    def test_navigate_to_file_manager(self, project_controller):
        """
        GIVEN a controller on any screen
        WHEN navigating to file_manager
        THEN the screen changes to file_manager.
        """
        command = NavigateToScreenCommand(screen_name="file_manager")

        result = project_controller.navigate_to_screen(command)

        assert isinstance(result, Success)
        assert project_controller.get_current_screen() == "file_manager"

    def test_navigate_with_source_context(
        self, project_controller_with_project, sample_source
    ):
        """
        GIVEN a controller with an open source
        WHEN navigating to coding screen
        THEN the source context is preserved.
        """
        # Add source and open it
        project_controller_with_project._sources.append(sample_source)
        project_controller_with_project.open_source(
            OpenSourceCommand(source_id=sample_source.id.value)
        )

        # Navigate to coding
        command = NavigateToScreenCommand(screen_name="coding")
        result = project_controller_with_project.navigate_to_screen(command)

        assert isinstance(result, Success)
        assert project_controller_with_project.get_current_source() is not None

    def test_navigate_emits_screen_changed_event(self, project_controller, event_bus):
        """
        GIVEN a project controller
        WHEN navigating to a screen
        THEN ScreenChanged event is emitted with correct payload.
        """
        command = NavigateToScreenCommand(screen_name="analysis")

        project_controller.navigate_to_screen(command)

        # History contains EventRecord objects with .event attribute
        history = event_bus.get_history()
        screen_events = [h.event for h in history if isinstance(h.event, ScreenChanged)]
        assert len(screen_events) >= 1
        assert screen_events[-1].to_screen == "analysis"


class TestNavigateToSegment:
    """Tests for AC #6: Agent can navigate to a specific source or segment."""

    def test_navigate_to_segment_opens_source_at_position(
        self, project_controller_with_source, event_bus
    ):
        """
        GIVEN a controller with sources
        WHEN navigating to a specific segment position
        THEN the source opens at the specified position.
        """
        from src.application.projects.controller import NavigateToSegmentCommand

        command = NavigateToSegmentCommand(
            source_id=1,
            start_pos=100,
            end_pos=200,
        )

        result = project_controller_with_source.navigate_to_segment(command)

        assert isinstance(result, Success)
        # Source should be opened
        assert project_controller_with_source.get_current_source() is not None
        # Screen should change to coding
        assert project_controller_with_source.get_current_screen() == "coding"

    def test_navigate_to_segment_emits_events(
        self, project_controller_with_source, event_bus
    ):
        """
        GIVEN a controller with sources
        WHEN navigating to a segment
        THEN NavigatedToSegment event is emitted.
        """
        from src.application.projects.controller import NavigateToSegmentCommand
        from src.domain.projects.events import NavigatedToSegment

        command = NavigateToSegmentCommand(
            source_id=1,
            start_pos=50,
            end_pos=150,
        )

        project_controller_with_source.navigate_to_segment(command)

        history = event_bus.get_history()
        nav_events = [
            h.event for h in history if isinstance(h.event, NavigatedToSegment)
        ]
        assert len(nav_events) >= 1
        assert nav_events[-1].position_start == 50
        assert nav_events[-1].position_end == 150

    def test_navigate_to_segment_fails_for_invalid_source(
        self, project_controller, event_bus
    ):
        """
        GIVEN a controller
        WHEN navigating to a nonexistent source
        THEN the navigation fails.
        """
        from src.application.projects.controller import NavigateToSegmentCommand

        command = NavigateToSegmentCommand(
            source_id=9999,  # Nonexistent
            start_pos=0,
            end_pos=100,
        )

        result = project_controller.navigate_to_segment(command)

        assert isinstance(result, Failure)

    def test_navigate_to_segment_with_highlight(
        self, project_controller_with_source, event_bus
    ):
        """
        GIVEN a controller with sources
        WHEN navigating to a segment with highlight=True
        THEN the segment should be highlighted.
        """
        from src.application.projects.controller import NavigateToSegmentCommand
        from src.domain.projects.events import NavigatedToSegment

        command = NavigateToSegmentCommand(
            source_id=1,
            start_pos=0,
            end_pos=50,
            highlight=True,
        )

        project_controller_with_source.navigate_to_segment(command)

        history = event_bus.get_history()
        nav_events = [
            h.event for h in history if isinstance(h.event, NavigatedToSegment)
        ]
        assert len(nav_events) >= 1
        assert nav_events[-1].highlight is True


class TestOpenSourceNavigation:
    """Tests for opening sources with navigation context."""

    def test_open_source_navigates_to_coding(
        self, project_controller_with_project, sample_source, event_bus
    ):
        """
        GIVEN a controller with sources
        WHEN opening a source
        THEN the screen changes to coding.
        """
        project_controller_with_project._sources.append(sample_source)
        command = OpenSourceCommand(source_id=1)

        result = project_controller_with_project.open_source(command)

        assert isinstance(result, Success)
        # Should navigate to coding screen
        history = event_bus.get_history()
        screen_events = [
            h.event for h in history if isinstance(h.event, ScreenChanged)
        ]
        coding_events = [e for e in screen_events if e.to_screen == "coding"]
        assert len(coding_events) >= 1

    def test_open_source_emits_source_opened_event(
        self, project_controller_with_project, sample_source, event_bus
    ):
        """
        GIVEN a controller with sources
        WHEN opening a source
        THEN SourceOpened event is emitted.
        """
        project_controller_with_project._sources.append(sample_source)
        command = OpenSourceCommand(source_id=1)

        project_controller_with_project.open_source(command)

        history = event_bus.get_history()
        opened_events = [h.event for h in history if isinstance(h.event, SourceOpened)]
        assert len(opened_events) >= 1


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def sample_source():
    """Create a sample source entity."""
    return Source(
        id=SourceId(value=1),
        name="test_source.txt",
        source_type=SourceType.TEXT,
        status=SourceStatus.READY,
        file_path=Path("/tmp/test_source.txt"),
        origin="internal",
        memo=None,
        code_count=0,
        case_ids=(),
    )


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project entity."""
    from src.domain.projects.entities import ProjectId

    return Project(
        id=ProjectId(value=str(tmp_path / "test.qda")),
        name="Test Project",
        path=tmp_path / "test.qda",
    )


@pytest.fixture
def project_controller_with_project(project_controller, sample_project):
    """Create a controller with a project already open."""
    project_controller._current_project = sample_project
    return project_controller


@pytest.fixture
def project_controller_with_source(project_controller, sample_source):
    """Create a controller with a source already added."""
    # Simulate having a source in the project
    project_controller._sources.append(sample_source)
    return project_controller
