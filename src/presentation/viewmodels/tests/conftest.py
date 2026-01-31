"""
Pytest fixtures for ViewModel tests.

Note: All fixtures are inherited from parent conftest.py files:
- qapp, colors: from root conftest.py
- coding_context, viewmodel: from presentation/tests/conftest.py

This file can contain viewmodel-specific fixtures if needed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.application.event_bus import EventBus


@pytest.fixture
def project_event_bus() -> EventBus:
    """Create an event bus for project tests."""
    return EventBus(history_size=100)


@pytest.fixture
def project_controller(project_event_bus: EventBus):
    """Create a ProjectController for testing."""
    from src.application.projects.controller import (
        CreateProjectCommand,
        ProjectControllerImpl,
    )

    controller = ProjectControllerImpl(event_bus=project_event_bus)

    # Create a project so we can add sources
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        project_path = Path(tmp_dir) / "test_project.qda"
        controller.create_project(
            CreateProjectCommand(name="Test Project", path=str(project_path))
        )
        yield controller


@pytest.fixture
def file_manager_vm(project_controller, project_event_bus):
    """Create a FileManagerViewModel for testing."""
    from src.presentation.viewmodels.file_manager_viewmodel import (
        FileManagerViewModel,
    )

    return FileManagerViewModel(
        controller=project_controller,
        event_bus=project_event_bus,
    )


@pytest.fixture
def sample_source_file(tmp_path: Path) -> Path:
    """Create a sample source file for testing."""
    source_file = tmp_path / "interview.txt"
    source_file.write_text("Sample interview content for testing.")
    return source_file
