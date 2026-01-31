"""
Tests for SelectionPopupController Molecule

Tests the timer-based popup management behavior.
"""

from PySide6.QtCore import QPoint
from PySide6.QtTest import QSignalSpy


class MockPopup:
    """Mock popup widget for testing."""

    def __init__(self):
        self._visible = False
        self._last_position = None

    def show_near_selection(self, pos: QPoint):
        self._visible = True
        self._last_position = pos

    def hide(self):
        self._visible = False

    def isVisible(self) -> bool:
        return self._visible


class TestSelectionPopupControllerMolecule:
    """Unit tests for SelectionPopupController molecule."""

    def test_enabled_by_default(self, qapp):
        """Controller is enabled by default."""
        from src.presentation.molecules.selection import SelectionPopupController

        popup = MockPopup()
        controller = SelectionPopupController(popup)

        assert controller.is_enabled() is True

    def test_set_enabled_false(self, qapp):
        """set_enabled(False) disables the controller."""
        from src.presentation.molecules.selection import SelectionPopupController

        popup = MockPopup()
        controller = SelectionPopupController(popup)
        controller.set_enabled(False)

        assert controller.is_enabled() is False

    def test_default_delay(self, qapp):
        """Default delay is 400ms."""
        from src.presentation.molecules.selection import SelectionPopupController

        popup = MockPopup()
        controller = SelectionPopupController(popup)

        assert controller.get_delay() == 400

    def test_custom_delay(self, qapp):
        """Custom delay can be set."""
        from src.presentation.molecules.selection import SelectionPopupController

        popup = MockPopup()
        controller = SelectionPopupController(popup, delay_ms=200)

        assert controller.get_delay() == 200

    def test_set_delay(self, qapp):
        """set_delay() updates the delay."""
        from src.presentation.molecules.selection import SelectionPopupController

        popup = MockPopup()
        controller = SelectionPopupController(popup)
        controller.set_delay(100)

        assert controller.get_delay() == 100

    def test_is_visible_reflects_popup(self, qapp):
        """is_visible() reflects popup visibility."""
        from src.presentation.molecules.selection import SelectionPopupController

        popup = MockPopup()
        controller = SelectionPopupController(popup)

        assert controller.is_visible() is False

        popup._visible = True
        assert controller.is_visible() is True

    def test_hide_hides_popup(self, qapp):
        """hide() hides the popup."""
        from src.presentation.molecules.selection import SelectionPopupController

        popup = MockPopup()
        popup._visible = True
        controller = SelectionPopupController(popup)

        controller.hide()

        assert popup._visible is False


class TestSelectionPopupControllerBehavior:
    """Tests for SelectionPopupController behavior."""

    def test_no_popup_when_disabled(self, qapp):
        """Popup doesn't show when controller is disabled."""
        from PySide6.QtCore import QCoreApplication

        from src.presentation.molecules.selection import SelectionPopupController

        popup = MockPopup()
        controller = SelectionPopupController(popup, delay_ms=10)
        controller.set_enabled(False)

        controller.on_selection_changed(
            has_selection=True,
            selection_text="test",
            get_position=lambda: QPoint(100, 100),
        )

        # Process events and wait
        QCoreApplication.processEvents()
        import time

        time.sleep(0.05)
        QCoreApplication.processEvents()

        assert popup._visible is False

    def test_no_popup_for_empty_selection(self, qapp):
        """Popup doesn't show for empty/whitespace selection."""
        from PySide6.QtCore import QCoreApplication

        from src.presentation.molecules.selection import SelectionPopupController

        popup = MockPopup()
        controller = SelectionPopupController(popup, delay_ms=10)

        controller.on_selection_changed(
            has_selection=True,
            selection_text="   ",  # Only whitespace
            get_position=lambda: QPoint(100, 100),
        )

        QCoreApplication.processEvents()
        import time

        time.sleep(0.05)
        QCoreApplication.processEvents()

        assert popup._visible is False

    def test_hide_on_selection_cleared(self, qapp):
        """Popup hides when selection is cleared."""
        from src.presentation.molecules.selection import SelectionPopupController

        popup = MockPopup()
        popup._visible = True
        controller = SelectionPopupController(popup)

        controller.on_selection_changed(has_selection=False)

        assert popup._visible is False

    def test_disable_hides_popup(self, qapp):
        """Disabling controller hides popup."""
        from src.presentation.molecules.selection import SelectionPopupController

        popup = MockPopup()
        popup._visible = True
        controller = SelectionPopupController(popup)

        controller.set_enabled(False)

        assert popup._visible is False


class TestSelectionPopupControllerSignals:
    """Tests for SelectionPopupController signals."""

    def test_popup_hidden_signal(self, qapp):
        """popup_hidden signal emits when popup is hidden."""
        from src.presentation.molecules.selection import SelectionPopupController

        popup = MockPopup()
        popup._visible = True
        controller = SelectionPopupController(popup)
        spy = QSignalSpy(controller.popup_hidden)

        controller.hide()

        assert spy.count() == 1
