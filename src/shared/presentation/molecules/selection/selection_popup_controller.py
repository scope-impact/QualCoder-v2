"""
Selection Popup Controller Molecule

Manages the delayed display of a popup when text is selected.
Provides timer-based debouncing to prevent popup interference while
the user is still making a selection.

This is a reusable controller that can work with any popup widget
that has show_near_selection(pos) and hide() methods.
"""

from typing import Protocol

from PySide6.QtCore import QObject, QPoint, QTimer, Signal


class PopupWidget(Protocol):
    """Protocol for popup widgets that can be controlled."""

    def show_near_selection(self, pos: QPoint) -> None: ...
    def hide(self) -> None: ...
    def isVisible(self) -> bool: ...


class SelectionPopupController(QObject):
    """
    Controls the delayed display of a selection popup.

    Features:
    - Debounced display: popup only shows after user stops selecting
    - Enable/disable toggle
    - Integrates with any popup that implements PopupWidget protocol

    Example:
        popup = SelectionPopup(actions=[...])
        controller = SelectionPopupController(popup)

        # When selection changes
        controller.on_selection_changed(
            has_selection=True,
            selection_text="selected text",
            get_position=lambda: text_edit.mapToGlobal(cursor_rect.topRight())
        )

        # When selection is cleared
        controller.on_selection_changed(has_selection=False)

    Signals:
        popup_shown: Emitted when popup becomes visible
        popup_hidden: Emitted when popup is hidden
    """

    popup_shown = Signal()
    popup_hidden = Signal()

    def __init__(
        self,
        popup: PopupWidget,
        delay_ms: int = 400,
        parent: QObject = None,
    ):
        """
        Initialize the controller.

        Args:
            popup: The popup widget to control
            delay_ms: Delay in milliseconds before showing popup (default 400)
            parent: Parent QObject
        """
        super().__init__(parent)
        self._popup = popup
        self._enabled = True
        self._get_position = None

        # Timer for delayed popup display
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(delay_ms)
        self._timer.timeout.connect(self._show_popup_now)

    # =========================================================================
    # Public API
    # =========================================================================

    def on_selection_changed(
        self,
        has_selection: bool,
        selection_text: str = "",
        get_position: callable = None,
    ):
        """
        Handle a selection change event.

        Call this whenever the text selection changes. The controller will
        manage the timer and popup display.

        Args:
            has_selection: Whether there is an active selection
            selection_text: The selected text (used to check if non-empty)
            get_position: Callable that returns QPoint for popup position
        """
        if has_selection and self._enabled and len(selection_text.strip()) > 0:
            self._get_position = get_position
            self._timer.start()  # Restart timer on each change
        else:
            self._cancel()

    def set_enabled(self, enabled: bool):
        """
        Enable or disable the popup controller.

        Args:
            enabled: Whether popup should be shown on selection
        """
        self._enabled = enabled
        if not enabled:
            self._cancel()

    def is_enabled(self) -> bool:
        """Check if popup is enabled."""
        return self._enabled

    def is_visible(self) -> bool:
        """Check if popup is currently visible."""
        return self._popup.isVisible()

    def hide(self):
        """Immediately hide the popup and cancel any pending show."""
        self._cancel()

    def set_delay(self, delay_ms: int):
        """
        Set the delay before popup appears.

        Args:
            delay_ms: Delay in milliseconds
        """
        self._timer.setInterval(delay_ms)

    def get_delay(self) -> int:
        """Get the current delay in milliseconds."""
        return self._timer.interval()

    # =========================================================================
    # Internal
    # =========================================================================

    def _show_popup_now(self):
        """Show the popup after the delay timer fires."""
        if self._enabled and self._get_position is not None:
            pos = self._get_position()
            if pos is not None:
                self._popup.show_near_selection(pos)
                self.popup_shown.emit()

    def _cancel(self):
        """Cancel timer and hide popup."""
        self._timer.stop()
        if self._popup.isVisible():
            self._popup.hide()
            self.popup_hidden.emit()
        self._get_position = None
