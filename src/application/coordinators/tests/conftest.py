"""
Shared fixtures for coordinator tests.
"""

from pathlib import Path

import pytest

from src.application.coordinators.base import CoordinatorInfrastructure
from src.application.event_bus import EventBus
from src.application.lifecycle import ProjectLifecycle
from src.application.state import ProjectState


@pytest.fixture
def event_bus() -> EventBus:
    """Create a fresh event bus for testing."""
    return EventBus(history_size=100)


@pytest.fixture
def project_state() -> ProjectState:
    """Create a fresh project state for testing."""
    return ProjectState()


@pytest.fixture
def project_lifecycle() -> ProjectLifecycle:
    """Create a fresh project lifecycle for testing."""
    return ProjectLifecycle()


@pytest.fixture
def temp_settings_repo(tmp_path: Path):
    """Create a temporary settings repository for testing."""
    from src.contexts.settings.infra import UserSettingsRepository

    config_path = tmp_path / "settings.json"
    return UserSettingsRepository(config_path=config_path)


@pytest.fixture
def coordinator_infra(
    event_bus: EventBus,
    project_state: ProjectState,
    project_lifecycle: ProjectLifecycle,
    temp_settings_repo,
) -> CoordinatorInfrastructure:
    """Create coordinator infrastructure for testing."""
    return CoordinatorInfrastructure(
        event_bus=event_bus,
        state=project_state,
        lifecycle=project_lifecycle,
        settings_repo=temp_settings_repo,
        signal_bridge=None,
    )
