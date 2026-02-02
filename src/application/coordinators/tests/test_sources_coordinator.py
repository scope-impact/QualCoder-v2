"""
Tests for SourcesCoordinator.
"""

from pathlib import Path

import pytest

from src.application.coordinators.base import CoordinatorInfrastructure
from src.application.coordinators.projects_coordinator import ProjectsCoordinator
from src.application.coordinators.sources_coordinator import SourcesCoordinator


@pytest.fixture
def open_project(coordinator_infra: CoordinatorInfrastructure, tmp_path: Path):
    """Open a test project before testing sources."""
    projects = ProjectsCoordinator(coordinator_infra)
    project_path = tmp_path / "test.qda"
    projects.create_project("Test Project", str(project_path))
    return projects


class TestSourcesCoordinatorQueries:
    """Tests for source query methods."""

    def test_get_sources_empty(
        self,
        coordinator_infra: CoordinatorInfrastructure,
        open_project: ProjectsCoordinator,
    ):
        """Returns empty list when no sources."""
        sources = SourcesCoordinator(coordinator_infra)

        result = sources.get_sources()

        assert result == []

    def test_get_source_not_found(
        self,
        coordinator_infra: CoordinatorInfrastructure,
        open_project: ProjectsCoordinator,
    ):
        """Returns None for nonexistent source."""
        sources = SourcesCoordinator(coordinator_infra)

        result = sources.get_source(999)

        assert result is None

    def test_get_sources_by_type_empty(
        self,
        coordinator_infra: CoordinatorInfrastructure,
        open_project: ProjectsCoordinator,
    ):
        """Returns empty list when no sources of type."""
        sources = SourcesCoordinator(coordinator_infra)

        result = sources.get_sources_by_type("text")

        assert result == []

    def test_get_current_source_none(
        self,
        coordinator_infra: CoordinatorInfrastructure,
        open_project: ProjectsCoordinator,
    ):
        """Returns None when no source is open."""
        sources = SourcesCoordinator(coordinator_infra)

        result = sources.get_current_source()

        assert result is None

    def test_get_segment_count_no_context(
        self, coordinator_infra: CoordinatorInfrastructure
    ):
        """Returns 0 when no coding context."""
        sources = SourcesCoordinator(coordinator_infra)

        result = sources.get_segment_count_for_source(1)

        assert result == 0
