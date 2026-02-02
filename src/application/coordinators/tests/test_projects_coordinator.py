"""
Tests for ProjectsCoordinator.
"""

from pathlib import Path

from returns.result import Failure, Success

from src.application.coordinators.base import CoordinatorInfrastructure
from src.application.coordinators.projects_coordinator import ProjectsCoordinator


class TestProjectsCoordinatorOpen:
    """Tests for opening projects."""

    def test_open_project_success(
        self, coordinator_infra: CoordinatorInfrastructure, tmp_path: Path
    ):
        """Opening an existing project succeeds."""
        from src.contexts.projects.infra.project_repository import (
            SQLiteProjectRepository,
        )

        # Create a proper .qda database file with schema
        project_path = tmp_path / "test.qda"
        repo = SQLiteProjectRepository()
        repo.create_database(project_path, "Test Project")

        coordinator = ProjectsCoordinator(coordinator_infra)
        result = coordinator.open_project(str(project_path))

        assert isinstance(result, Success)

    def test_open_project_failure(self, coordinator_infra: CoordinatorInfrastructure):
        """Opening a nonexistent project fails."""
        coordinator = ProjectsCoordinator(coordinator_infra)

        result = coordinator.open_project("/nonexistent/project.qda")

        assert isinstance(result, Failure)


class TestProjectsCoordinatorCreate:
    """Tests for creating projects."""

    def test_create_project_success(
        self, coordinator_infra: CoordinatorInfrastructure, tmp_path: Path
    ):
        """Creating a new project succeeds."""
        project_path = tmp_path / "new_project.qda"

        coordinator = ProjectsCoordinator(coordinator_infra)
        result = coordinator.create_project("My Project", str(project_path))

        assert isinstance(result, Success)

    def test_create_project_with_empty_name_fails(
        self, coordinator_infra: CoordinatorInfrastructure, tmp_path: Path
    ):
        """Creating a project with empty name fails."""
        project_path = tmp_path / "empty.qda"

        coordinator = ProjectsCoordinator(coordinator_infra)
        result = coordinator.create_project("", str(project_path))

        assert isinstance(result, Failure)


class TestProjectsCoordinatorClose:
    """Tests for closing projects."""

    def test_close_project(
        self, coordinator_infra: CoordinatorInfrastructure, tmp_path: Path
    ):
        """Closing a project clears contexts."""
        project_path = tmp_path / "test.qda"

        coordinator = ProjectsCoordinator(coordinator_infra)
        coordinator.create_project("Test", str(project_path))

        result = coordinator.close_project()

        assert isinstance(result, Success)
        assert coordinator_infra.sources_context is None
        assert coordinator_infra.cases_context is None


class TestProjectsCoordinatorQueries:
    """Tests for project query methods."""

    def test_get_current_project_none(
        self, coordinator_infra: CoordinatorInfrastructure
    ):
        """Returns None when no project is open."""
        coordinator = ProjectsCoordinator(coordinator_infra)

        project = coordinator.get_current_project()

        assert project is None

    def test_get_current_project_with_open_project(
        self, coordinator_infra: CoordinatorInfrastructure, tmp_path: Path
    ):
        """Returns project when one is open."""
        project_path = tmp_path / "test.qda"

        coordinator = ProjectsCoordinator(coordinator_infra)
        coordinator.create_project("Test Project", str(project_path))

        project = coordinator.get_current_project()

        assert project is not None
        assert project.name == "Test Project"

    def test_get_project_context_no_project(
        self, coordinator_infra: CoordinatorInfrastructure
    ):
        """Returns closed state when no project."""
        coordinator = ProjectsCoordinator(coordinator_infra)

        context = coordinator.get_project_context()

        assert context["project_open"] is False

    def test_get_project_context_with_project(
        self, coordinator_infra: CoordinatorInfrastructure, tmp_path: Path
    ):
        """Returns project info when project is open."""
        project_path = tmp_path / "test.qda"

        coordinator = ProjectsCoordinator(coordinator_infra)
        coordinator.create_project("Test Project", str(project_path))

        context = coordinator.get_project_context()

        assert context["project_open"] is True
        assert context["project_name"] == "Test Project"

    def test_get_project_summary_no_project(
        self, coordinator_infra: CoordinatorInfrastructure
    ):
        """Returns None when no project is open."""
        coordinator = ProjectsCoordinator(coordinator_infra)

        summary = coordinator.get_project_summary()

        assert summary is None

    def test_get_project_summary_with_project(
        self, coordinator_infra: CoordinatorInfrastructure, tmp_path: Path
    ):
        """Returns summary when project is open."""
        project_path = tmp_path / "test.qda"

        coordinator = ProjectsCoordinator(coordinator_infra)
        coordinator.create_project("Test", str(project_path))

        summary = coordinator.get_project_summary()

        assert summary is not None
        assert summary.total_sources == 0
