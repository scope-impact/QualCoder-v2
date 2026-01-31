"""
Root pytest configuration and shared fixtures.

This is the central location for fixtures shared across ALL test modules.
Layer-specific fixtures should remain in their respective conftest.py files.

Fixture Hierarchy:
    conftest.py (root)           <- You are here: qapp, colors
    ├── src/presentation/tests/conftest.py    <- coding_context, viewmodel
    ├── src/domain/*/tests/conftest.py        <- domain entities
    ├── src/application/*/tests/conftest.py   <- controllers, repos
    └── design_system/tests/conftest.py       <- screenshot utilities
"""

import sys

import pytest
from PySide6.QtWidgets import QApplication


# =============================================================================
# Qt Application Fixtures (Session-scoped)
# =============================================================================


@pytest.fixture(scope="session")
def qapp():
    """
    Create a single QApplication instance for the entire test session.

    Qt requires exactly one QApplication instance. This fixture ensures
    all tests share the same instance and it's properly cleaned up.

    Note: Session scope is required because Qt doesn't allow multiple
    QApplication instances in the same process.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # Don't call app.quit() - let Qt handle cleanup


# =============================================================================
# Theme/Color Fixtures
# =============================================================================


@pytest.fixture
def colors():
    """
    Get the design system color palette.

    Returns the default (dark) theme colors for testing UI components.
    """
    from design_system import get_colors

    return get_colors()


# =============================================================================
# Test Helpers
# =============================================================================


@pytest.fixture
def create_widget(qtbot):
    """
    Factory fixture for creating widgets with automatic cleanup.

    Usage:
        def test_button(create_widget):
            btn = create_widget(Button, "Click me")
            assert btn.text() == "Click me"
    """

    def _create(widget_class, *args, **kwargs):
        widget = widget_class(*args, **kwargs)
        qtbot.addWidget(widget)
        return widget

    return _create


# =============================================================================
# Database/Context Fixtures
# =============================================================================


@pytest.fixture
def coding_context():
    """
    Create an in-memory CodingContext for testing.

    This provides a complete test environment with:
    - In-memory SQLite database
    - All repositories (codes, categories, segments)
    - Controller for business operations
    """
    from src.presentation.factory import CodingContext

    ctx = CodingContext.create_in_memory()
    yield ctx
    ctx.close()


@pytest.fixture
def viewmodel(coding_context):
    """
    Create a TextCodingViewModel connected to the test context.

    The viewmodel provides the interface between UI and business logic.
    """
    return coding_context.create_text_coding_viewmodel()


# =============================================================================
# Timeout Constants
# =============================================================================

# Default timeout for signal waiting (ms)
DEFAULT_SIGNAL_TIMEOUT = 1000

# Extended timeout for slow operations (ms)
SLOW_SIGNAL_TIMEOUT = 5000
