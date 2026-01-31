"""
Project application test fixtures.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.application.event_bus import EventBus


@pytest.fixture
def event_bus() -> EventBus:
    """Create an event bus with history enabled for testing."""
    return EventBus(history_size=100)


@pytest.fixture
def project_controller(event_bus: EventBus):
    """Create a ProjectController with the test event bus."""
    from src.application.projects.controller import ProjectControllerImpl

    return ProjectControllerImpl(
        event_bus=event_bus,
        source_repo=None,
        project_repo=None,
    )


@pytest.fixture
def sample_project_path(tmp_path: Path) -> Path:
    """Create a sample project path in temp directory."""
    return tmp_path / "test_project.qda"


@pytest.fixture
def existing_project_path(tmp_path: Path) -> Path:
    """Create an existing project file for open tests."""
    project_path = tmp_path / "existing_project.qda"
    project_path.touch()
    return project_path


@pytest.fixture
def sample_source_path(tmp_path: Path) -> Path:
    """Create a sample source file."""
    source_path = tmp_path / "interview.txt"
    source_path.write_text("Sample interview content")
    return source_path
