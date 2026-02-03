"""
E2E Test Helpers for Black-Box Testing

Utilities for finding and interacting with UI elements by their visible
properties (text, tooltip, accessible name) rather than internal attributes.

BLACK-BOX PRINCIPLE: Tests should simulate real user behavior - finding
elements by what's visible (button text, tooltips) not by implementation
details (private attributes like _create_btn, _color_buttons).
"""

from __future__ import annotations

from typing import TypeVar

from PySide6.QtWidgets import (
    QAbstractButton,
    QComboBox,
    QDialog,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QWidget,
)

T = TypeVar("T", bound=QWidget)


# =============================================================================
# Find Elements by Visible Properties
# =============================================================================


def find_button_by_text(
    parent: QWidget, text: str, partial: bool = False
) -> QPushButton | None:
    """
    Find a button by its visible text.

    Args:
        parent: Widget to search in
        text: Button text to match
        partial: If True, match partial text; if False, exact match

    Returns:
        The button if found, None otherwise
    """
    for btn in parent.findChildren(QPushButton):
        btn_text = btn.text()
        if (
            partial
            and text.lower() in btn_text.lower()
            or not partial
            and btn_text == text
        ):
            return btn
    return None


def find_button_by_tooltip(
    parent: QWidget, tooltip: str, partial: bool = False
) -> QPushButton | None:
    """
    Find a button by its tooltip.

    Args:
        parent: Widget to search in
        tooltip: Tooltip text to match
        partial: If True, match partial text; if False, exact match

    Returns:
        The button if found, None otherwise
    """
    for btn in parent.findChildren(QPushButton):
        btn_tooltip = btn.toolTip()
        if (
            partial
            and tooltip.lower() in btn_tooltip.lower()
            or not partial
            and btn_tooltip == tooltip
        ):
            return btn
    return None


def find_any_button_by_tooltip(
    parent: QWidget, tooltip: str, partial: bool = False
) -> QAbstractButton | None:
    """
    Find any button (including tool buttons) by its tooltip.

    Args:
        parent: Widget to search in
        tooltip: Tooltip text to match
        partial: If True, match partial text

    Returns:
        The button if found, None otherwise
    """
    for btn in parent.findChildren(QAbstractButton):
        btn_tooltip = btn.toolTip()
        if (
            partial
            and tooltip.lower() in btn_tooltip.lower()
            or not partial
            and btn_tooltip == tooltip
        ):
            return btn
    return None


def find_buttons_with_text(parent: QWidget, text: str) -> list[QPushButton]:
    """
    Find all buttons containing the given text.

    Args:
        parent: Widget to search in
        text: Text to search for in button labels

    Returns:
        List of matching buttons
    """
    return [
        btn
        for btn in parent.findChildren(QPushButton)
        if text.lower() in btn.text().lower()
    ]


def find_label_with_text(
    parent: QWidget, text: str, partial: bool = True
) -> QLabel | None:
    """
    Find a label by its visible text.

    Args:
        parent: Widget to search in
        text: Text to match
        partial: If True, match partial text

    Returns:
        The label if found, None otherwise
    """
    for label in parent.findChildren(QLabel):
        label_text = label.text()
        if (
            partial
            and text.lower() in label_text.lower()
            or not partial
            and label_text == text
        ):
            return label
    return None


def find_input_by_placeholder(parent: QWidget, placeholder: str) -> QLineEdit | None:
    """
    Find a line edit by its placeholder text.

    Args:
        parent: Widget to search in
        placeholder: Placeholder text to match

    Returns:
        The input if found, None otherwise
    """
    for input_widget in parent.findChildren(QLineEdit):
        if placeholder.lower() in input_widget.placeholderText().lower():
            return input_widget
    return None


def find_text_area_by_placeholder(
    parent: QWidget, placeholder: str
) -> QPlainTextEdit | None:
    """
    Find a text area by its placeholder text.

    Args:
        parent: Widget to search in
        placeholder: Placeholder text to match

    Returns:
        The text area if found, None otherwise
    """
    for text_area in parent.findChildren(QPlainTextEdit):
        if placeholder.lower() in text_area.placeholderText().lower():
            return text_area
    return None


def find_combo_box_by_items(parent: QWidget, *items: str) -> QComboBox | None:
    """
    Find a combo box that contains specific items.

    Args:
        parent: Widget to search in
        *items: Items that should be in the combo box

    Returns:
        The combo box if found, None otherwise
    """
    for combo in parent.findChildren(QComboBox):
        combo_items = [combo.itemText(i) for i in range(combo.count())]
        if all(item in combo_items for item in items):
            return combo
    return None


# =============================================================================
# Dialog Helpers
# =============================================================================


def find_visible_dialog(widget_type: type[T]) -> T | None:
    """
    Find a visible dialog of the given type.

    Args:
        widget_type: The dialog class to find

    Returns:
        The dialog if found and visible, None otherwise
    """
    from PySide6.QtWidgets import QApplication

    for widget in QApplication.topLevelWidgets():
        if isinstance(widget, widget_type) and widget.isVisible():
            return widget
    return None


def get_all_visible_dialogs() -> list[QDialog]:
    """
    Get all currently visible dialogs.

    Returns:
        List of visible QDialog instances
    """
    from PySide6.QtWidgets import QApplication

    return [
        w
        for w in QApplication.topLevelWidgets()
        if isinstance(w, QDialog) and w.isVisible()
    ]


def click_dialog_button(dialog: QDialog, button_text: str) -> bool:
    """
    Click a button in a dialog by its text.

    Args:
        dialog: The dialog containing the button
        button_text: Text of the button to click

    Returns:
        True if button was found and clicked, False otherwise
    """
    btn = find_button_by_text(dialog, button_text, partial=True)
    if btn and btn.isEnabled():
        btn.click()
        return True
    return False


# =============================================================================
# UI State Verification
# =============================================================================


def is_button_enabled(parent: QWidget, text: str) -> bool:
    """
    Check if a button with given text is enabled.

    Args:
        parent: Widget to search in
        text: Button text to find

    Returns:
        True if button exists and is enabled
    """
    btn = find_button_by_text(parent, text, partial=True)
    return btn is not None and btn.isEnabled()


def get_label_text(
    parent: QWidget, object_name: str = None, partial_text: str = None
) -> str | None:
    """
    Get text from a label by object name or partial text match.

    Args:
        parent: Widget to search in
        object_name: Qt object name to find
        partial_text: Partial text to match

    Returns:
        The label text if found, None otherwise
    """
    if object_name:
        label = parent.findChild(QLabel, object_name)
        if label:
            return label.text()
    if partial_text:
        label = find_label_with_text(parent, partial_text)
        if label:
            return label.text()
    return None


def get_input_value(parent: QWidget, placeholder: str = None) -> str | None:
    """
    Get value from an input field.

    Args:
        parent: Widget to search in
        placeholder: Placeholder text to identify the input

    Returns:
        The input value if found, None otherwise
    """
    if placeholder:
        input_widget = find_input_by_placeholder(parent, placeholder)
        if input_widget:
            return input_widget.text()
    return None


def get_combo_selection(parent: QWidget, *expected_items: str) -> str | None:
    """
    Get current selection from a combo box.

    Args:
        parent: Widget to search in
        *expected_items: Items to identify the combo box

    Returns:
        Current selection text if found, None otherwise
    """
    combo = find_combo_box_by_items(parent, *expected_items)
    if combo:
        return combo.currentText()
    return None


def set_combo_selection(parent: QWidget, value: str, *expected_items: str) -> bool:
    """
    Set selection in a combo box.

    Args:
        parent: Widget to search in
        value: Value to select
        *expected_items: Items to identify the combo box

    Returns:
        True if selection was set, False otherwise
    """
    combo = find_combo_box_by_items(parent, *expected_items)
    if combo:
        index = combo.findText(value)
        if index >= 0:
            combo.setCurrentIndex(index)
            return True
    return False


# =============================================================================
# Visibility Assertions
# =============================================================================


def assert_element_visible(
    parent: QWidget, text: str, element_type: str = "any"
) -> None:
    """
    Assert that an element with given text is visible.

    Args:
        parent: Widget to search in
        text: Text to find
        element_type: "button", "label", or "any"

    Raises:
        AssertionError if element not found or not visible
    """
    if element_type == "button":
        elem = find_button_by_text(parent, text, partial=True)
    elif element_type == "label":
        elem = find_label_with_text(parent, text)
    else:
        elem = find_button_by_text(parent, text, partial=True) or find_label_with_text(
            parent, text
        )

    assert elem is not None, f"Element with text '{text}' not found"
    assert elem.isVisible(), f"Element with text '{text}' is not visible"


def assert_dialog_visible(dialog_type: type) -> None:
    """
    Assert that a dialog of the given type is visible.

    Args:
        dialog_type: The dialog class to check for

    Raises:
        AssertionError if dialog not found or not visible
    """
    dialog = find_visible_dialog(dialog_type)
    assert dialog is not None, f"Dialog of type {dialog_type.__name__} not visible"


def assert_no_dialog_visible() -> None:
    """
    Assert that no dialogs are currently visible.

    Raises:
        AssertionError if any dialog is visible
    """
    dialogs = get_all_visible_dialogs()
    assert len(dialogs) == 0, f"Expected no dialogs but found {len(dialogs)}"


# =============================================================================
# Color Helpers
# =============================================================================


def find_color_swatch_buttons(parent: QWidget) -> list[QAbstractButton]:
    """
    Find all color swatch buttons in a widget.

    Looks for widgets that:
    1. Have a 'color' property set, OR
    2. Have a get_color() method (ColorSwatch widgets)

    Args:
        parent: Widget to search in

    Returns:
        List of buttons/widgets that are color swatches
    """
    swatches = []
    # First try to find widgets with get_color method (ColorSwatch)
    for widget in parent.findChildren(QWidget):
        if hasattr(widget, "get_color") and callable(widget.get_color):
            swatches.append(widget)

    # If no ColorSwatch found, try buttons with color property
    if not swatches:
        for btn in parent.findChildren(QAbstractButton):
            if btn.property("color") is not None:
                swatches.append(btn)

    return swatches


def get_swatch_color(swatch) -> str | None:
    """Get color from a swatch widget."""
    if hasattr(swatch, "get_color"):
        return swatch.get_color()
    elif hasattr(swatch, "property"):
        return swatch.property("color")
    return None


def click_color_swatch(parent: QWidget, color: str) -> bool:
    """
    Click a color swatch with the given color.

    Args:
        parent: Widget to search in
        color: Hex color to click (e.g., "#FF0000")

    Returns:
        True if swatch was found and clicked
    """
    for swatch in find_color_swatch_buttons(parent):
        swatch_color = get_swatch_color(swatch)
        if swatch_color == color:
            if hasattr(swatch, "click"):
                swatch.click()
            elif hasattr(swatch, "clicked"):
                swatch.clicked.emit(color)
            return True
    return False


def click_color_swatch_by_index(parent: QWidget, index: int) -> bool:
    """
    Click a color swatch by index.

    Args:
        parent: Widget to search in
        index: Zero-based index of the swatch to click

    Returns:
        True if swatch was found and clicked
    """
    swatches = find_color_swatch_buttons(parent)
    if 0 <= index < len(swatches):
        swatch = swatches[index]
        if hasattr(swatch, "click"):
            swatch.click()
        elif hasattr(swatch, "clicked"):
            color = get_swatch_color(swatch)
            swatch.clicked.emit(color)
        return True
    return False


# =============================================================================
# Table Helpers
# =============================================================================


def get_table_row_count(parent: QWidget) -> int:
    """
    Get the row count from the first QTableWidget found.

    Args:
        parent: Widget to search in

    Returns:
        Number of rows, or 0 if no table found
    """
    from PySide6.QtWidgets import QTableWidget

    table = parent.findChild(QTableWidget)
    if table:
        return table.rowCount()
    return 0


def get_visible_table_data(parent: QWidget, column: int = 0) -> list[str]:
    """
    Get visible data from a table column.

    Args:
        parent: Widget to search in
        column: Column index to read

    Returns:
        List of cell values in that column
    """
    from PySide6.QtWidgets import QTableWidget

    table = parent.findChild(QTableWidget)
    if not table:
        return []

    data = []
    for row in range(table.rowCount()):
        item = table.item(row, column)
        if item:
            data.append(item.text())
    return data


# =============================================================================
# Screenshot Helpers for Allure
# =============================================================================


def capture_screenshot(widget: QWidget, name: str = "screenshot") -> bytes:
    """
    Capture a screenshot of a widget.

    Args:
        widget: The widget to capture
        name: Name for the screenshot

    Returns:
        PNG image data as bytes
    """
    from PySide6.QtCore import QBuffer, QIODevice
    from PySide6.QtWidgets import QApplication

    QApplication.processEvents()
    pixmap = widget.grab()

    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap.save(buffer, "PNG")
    return bytes(buffer.data())


def attach_screenshot(widget: QWidget, name: str = "screenshot") -> None:
    """
    Capture a screenshot and attach it to the Allure report.

    Args:
        widget: The widget to capture
        name: Name for the screenshot attachment
    """
    import allure

    image_data = capture_screenshot(widget, name)
    allure.attach(
        image_data,
        name=name,
        attachment_type=allure.attachment_type.PNG,
    )


def attach_screenshot_on_step(widget: QWidget, step_name: str) -> None:
    """
    Create an Allure step with a screenshot attached.

    Args:
        widget: The widget to capture
        step_name: Name of the step
    """
    import allure

    with allure.step(step_name):
        attach_screenshot(widget, step_name)
