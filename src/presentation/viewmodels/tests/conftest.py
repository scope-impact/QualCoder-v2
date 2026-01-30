"""
Pytest fixtures for ViewModel tests.

These fixtures are specific to the viewmodels subdirectory.
"""

import sys

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def coding_context():
    """Create an in-memory CodingContext for testing."""
    from src.presentation.factory import CodingContext

    ctx = CodingContext.create_in_memory()
    yield ctx
    ctx.close()


@pytest.fixture
def viewmodel(coding_context):
    """Create a TextCodingViewModel connected to the test context."""
    return coding_context.create_text_coding_viewmodel()


@pytest.fixture
def colors():
    """Get theme colors."""
    from design_system import get_colors

    return get_colors()
