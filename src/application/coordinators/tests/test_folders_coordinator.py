"""
Tests for FoldersCoordinator.
"""

from pathlib import Path

import pytest

from src.application.coordinators.base import CoordinatorInfrastructure
from src.application.coordinators.folders_coordinator import FoldersCoordinator
from src.application.coordinators.projects_coordinator import ProjectsCoordinator


@pytest.fixture
def open_project(coordinator_infra: CoordinatorInfrastructure, tmp_path: Path):
    """Open a test project before testing folders."""
    projects = ProjectsCoordinator(coordinator_infra)
    project_path = tmp_path / "test.qda"
    projects.create_project("Test Project", str(project_path))
    return projects


class TestFoldersCoordinatorQueries:
    """Tests for folder query methods."""

    def test_get_folders_empty(
        self,
        coordinator_infra: CoordinatorInfrastructure,
        open_project: ProjectsCoordinator,
    ):
        """Returns empty list when no folders."""
        folders = FoldersCoordinator(coordinator_infra)

        result = folders.get_folders()

        assert result == []
