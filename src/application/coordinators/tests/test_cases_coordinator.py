"""
Tests for CasesCoordinator.
"""

from pathlib import Path

import pytest

from src.application.coordinators.base import CoordinatorInfrastructure
from src.application.coordinators.cases_coordinator import CasesCoordinator
from src.application.coordinators.projects_coordinator import ProjectsCoordinator


@pytest.fixture
def open_project(coordinator_infra: CoordinatorInfrastructure, tmp_path: Path):
    """Open a test project before testing cases."""
    projects = ProjectsCoordinator(coordinator_infra)
    project_path = tmp_path / "test.qda"
    projects.create_project("Test Project", str(project_path))
    return projects


class TestCasesCoordinatorQueries:
    """Tests for case query methods."""

    def test_get_cases_empty(
        self,
        coordinator_infra: CoordinatorInfrastructure,
        open_project: ProjectsCoordinator,
    ):
        """Returns empty list when no cases."""
        cases = CasesCoordinator(coordinator_infra)

        result = cases.get_cases()

        assert result == []

    def test_get_case_not_found(
        self,
        coordinator_infra: CoordinatorInfrastructure,
        open_project: ProjectsCoordinator,
    ):
        """Returns None for nonexistent case."""
        cases = CasesCoordinator(coordinator_infra)

        result = cases.get_case(999)

        assert result is None
