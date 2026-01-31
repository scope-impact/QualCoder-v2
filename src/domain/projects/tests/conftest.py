"""
Project domain test fixtures.

Provides sample entities and states for testing project operations.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest


@pytest.fixture
def sample_project_path() -> Path:
    """Valid project file path."""
    return Path("/home/user/research/my_project.qda")


@pytest.fixture
def sample_project_name() -> str:
    """Valid project name."""
    return "Research Study 2026"


@pytest.fixture
def sample_source_path() -> Path:
    """Valid source file path."""
    return Path("/home/user/data/interview_01.docx")


@pytest.fixture
def existing_project_paths() -> tuple[Path, ...]:
    """List of existing project paths for uniqueness checks."""
    return (
        Path("/home/user/research/project_a.qda"),
        Path("/home/user/research/project_b.qda"),
    )


@pytest.fixture
def recent_projects() -> list[dict]:
    """List of recent projects for quick access testing."""
    return [
        {
            "path": Path("/home/user/research/project_a.qda"),
            "name": "Project A",
            "last_opened": datetime(2026, 1, 28, 10, 0, tzinfo=UTC),
        },
        {
            "path": Path("/home/user/research/project_b.qda"),
            "name": "Project B",
            "last_opened": datetime(2026, 1, 25, 15, 30, tzinfo=UTC),
        },
    ]
