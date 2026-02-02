"""
Tests for NavigationCoordinator.
"""

from pathlib import Path

from returns.result import Failure

from src.application.coordinators.base import CoordinatorInfrastructure
from src.application.coordinators.navigation_coordinator import NavigationCoordinator
from src.application.coordinators.projects_coordinator import ProjectsCoordinator


class TestNavigationCoordinatorQueries:
    """Tests for navigation query methods."""

    def test_get_current_screen_none(
        self, coordinator_infra: CoordinatorInfrastructure
    ):
        """Returns None when no screen is active."""
        nav = NavigationCoordinator(coordinator_infra)

        result = nav.get_current_screen()

        assert result is None


class TestNavigateToSegment:
    """Tests for segment navigation."""

    def test_navigate_fails_without_project(
        self, coordinator_infra: CoordinatorInfrastructure
    ):
        """Navigation fails when no project is open."""
        from src.application.projects.commands import NavigateToSegmentCommand

        nav = NavigationCoordinator(coordinator_infra)
        command = NavigateToSegmentCommand(
            source_id=1,
            start_pos=0,
            end_pos=100,
        )

        result = nav.navigate_to_segment(command)

        assert isinstance(result, Failure)

    def test_navigate_fails_for_nonexistent_source(
        self, coordinator_infra: CoordinatorInfrastructure, tmp_path: Path
    ):
        """Navigation fails for nonexistent source."""
        from src.application.projects.commands import NavigateToSegmentCommand

        # Open a project first
        projects = ProjectsCoordinator(coordinator_infra)
        project_path = tmp_path / "test.qda"
        projects.create_project("Test", str(project_path))

        nav = NavigationCoordinator(coordinator_infra)
        command = NavigateToSegmentCommand(
            source_id=999,
            start_pos=0,
            end_pos=100,
        )

        result = nav.navigate_to_segment(command)

        assert isinstance(result, Failure)
