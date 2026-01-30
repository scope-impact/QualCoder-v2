"""
Connected Text Coding Demo

Demonstrates the full DDD stack working together:
    Presentation → ViewModel → Controller → Domain → Infrastructure

Run with:
    uv run python -m src.presentation.demo_connected
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from design_system import get_colors
from src.presentation.dto import (
    CodeCategoryDTO,
    DocumentDTO,
    NavigationDTO,
    TextCodingDataDTO,
)
from src.presentation.factory import CodingContext
from src.presentation.screens import TextCodingScreen
from src.presentation.viewmodels import TextCodingViewModel


class ConnectedTextCodingDemo(QMainWindow):
    """
    Demo window showing connected text coding with real persistence.

    Features:
    - Create codes with a simple form
    - See codes appear in the codes panel
    - Apply codes to text selections
    - All changes persist to SQLite (in-memory for demo)
    """

    def __init__(self) -> None:
        super().__init__()
        self._colors = get_colors()
        self._context: CodingContext | None = None
        self._viewmodel: TextCodingViewModel | None = None

        self.setWindowTitle("Connected Text Coding Demo (DDD Stack)")
        self.setMinimumSize(1400, 900)
        self.setStyleSheet(f"background-color: {self._colors.background};")

        # Initialize the coding context (in-memory SQLite)
        self._context = CodingContext.create_in_memory()
        self._viewmodel = self._context.create_text_coding_viewmodel()

        # Create some initial data
        self._seed_data()

        # Build UI
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Control bar for creating codes
        control_bar = self._create_control_bar()
        layout.addWidget(control_bar)

        # Text coding screen
        initial_data = self._build_initial_data()
        self._screen = TextCodingScreen(data=initial_data, colors=self._colors)
        layout.addWidget(self._screen, 1)

        # Connect viewmodel signals
        self._viewmodel.codes_changed.connect(self._on_codes_changed)
        self._viewmodel.error_occurred.connect(self._on_error)

        # Connect screen signals
        self._screen.code_selected.connect(self._on_code_selected)
        self._screen.text_selected.connect(self._on_text_selected)

    def _create_control_bar(self) -> QWidget:
        """Create a control bar for demo actions."""
        bar = QWidget()
        bar.setStyleSheet(f"""
            QWidget {{
                background: {self._colors.surface};
                border-bottom: 1px solid {self._colors.border};
            }}
            QLineEdit {{
                padding: 6px 12px;
                border: 1px solid {self._colors.border};
                border-radius: 4px;
                background: {self._colors.background};
                color: {self._colors.text_primary};
            }}
            QPushButton {{
                padding: 6px 16px;
                border: none;
                border-radius: 4px;
                background: {self._colors.primary};
                color: white;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {self._colors.primary_dark};
            }}
            QLabel {{
                color: {self._colors.text_secondary};
                font-size: 12px;
            }}
        """)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        # Code name input
        layout.addWidget(QLabel("Create Code:"))
        self._code_name_input = QLineEdit()
        self._code_name_input.setPlaceholderText("Code name...")
        self._code_name_input.setFixedWidth(200)
        layout.addWidget(self._code_name_input)

        # Color input
        self._code_color_input = QLineEdit()
        self._code_color_input.setPlaceholderText("#ff0000")
        self._code_color_input.setText("#e74c3c")
        self._code_color_input.setFixedWidth(80)
        layout.addWidget(self._code_color_input)

        # Create button
        create_btn = QPushButton("Create Code")
        create_btn.clicked.connect(self._on_create_code)
        layout.addWidget(create_btn)

        layout.addSpacing(20)

        # Apply code button
        self._apply_btn = QPushButton("Apply Selected Code to Selection")
        self._apply_btn.clicked.connect(self._on_apply_code)
        self._apply_btn.setEnabled(False)
        layout.addWidget(self._apply_btn)

        # Status label
        self._status_label = QLabel("Select text and a code to apply coding")
        layout.addWidget(self._status_label)

        layout.addStretch()

        return bar

    def _seed_data(self) -> None:
        """Create some initial codes and categories for demo."""
        # Create a category
        self._viewmodel.create_category("Themes")
        self._viewmodel.create_category("Emotions")

        # Create some codes
        self._viewmodel.create_code("positive", "#27ae60")
        self._viewmodel.create_code("negative", "#e74c3c")
        self._viewmodel.create_code("neutral", "#95a5a6")
        self._viewmodel.create_code("question", "#3498db")

    def _build_initial_data(self) -> TextCodingDataDTO:
        """Build initial data DTO from viewmodel."""
        categories = self._viewmodel.load_codes()

        # Sample document
        document = DocumentDTO(
            id="1",
            title="Interview Transcript",
            badge="Demo",
            content="""I have really enjoyed learning about qualitative research methods.
The course has been challenging but rewarding.

Sometimes I feel overwhelmed by the amount of reading required.
But the support from tutors has been excellent.

I wonder if there are more efficient ways to code large datasets?
The software tools we've learned are helpful but take time to master.

Overall, I'm satisfied with my progress and feel confident about the exam.""",
        )

        return TextCodingDataDTO(
            files=[],
            categories=categories,
            document=document,
            document_stats=None,
            selected_code=None,
            overlapping_segments=[],
            file_memo=None,
            navigation=NavigationDTO(current=1, total=1),
            coders=["demo_user"],
            selected_coder="demo_user",
        )

    # =========================================================================
    # Event Handlers
    # =========================================================================

    @Slot()
    def _on_create_code(self) -> None:
        """Handle create code button click."""
        name = self._code_name_input.text().strip()
        color = self._code_color_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Error", "Please enter a code name")
            return

        if not color.startswith("#") or len(color) != 7:
            QMessageBox.warning(
                self, "Error", "Please enter a valid hex color (e.g., #ff0000)"
            )
            return

        if self._viewmodel.create_code(name, color):
            self._code_name_input.clear()
            self._status_label.setText(f"Created code: {name}")
        else:
            self._status_label.setText(f"Failed to create code: {name}")

    @Slot(list)
    def _on_codes_changed(self, categories: list[CodeCategoryDTO]) -> None:
        """Handle codes changed from viewmodel."""
        # Convert to dict format expected by page
        cat_dicts = [
            {
                "name": cat.name,
                "codes": [
                    {"id": c.id, "name": c.name, "color": c.color, "count": c.count}
                    for c in cat.codes
                ],
            }
            for cat in categories
        ]
        self._screen.set_codes(cat_dicts)

    @Slot(str)
    def _on_error(self, error: str) -> None:
        """Handle error from viewmodel."""
        self._status_label.setText(f"Error: {error}")

    @Slot(dict)
    def _on_code_selected(self, code_data: dict) -> None:
        """Handle code selection in UI."""
        code_id = code_data.get("id", "")
        self._selected_code_id = code_id

        # Look up the code name for display
        code_name = "Unknown"
        try:
            code_id_int = int(code_id)
            code = self._context.controller.get_code(code_id_int)
            if code:
                code_name = code.name
        except (ValueError, TypeError):
            pass

        self._status_label.setText(f"Selected code: {code_name} (ID: {code_id})")
        self._update_apply_button()

    @Slot(str, int, int)
    def _on_text_selected(self, text: str, start: int, end: int) -> None:
        """Handle text selection in editor."""
        self._selected_text = text
        self._selection_start = start
        self._selection_end = end
        preview = text[:30] + "..." if len(text) > 30 else text
        self._status_label.setText(f'Selected: "{preview}" ({start}-{end})')
        self._update_apply_button()

    def _update_apply_button(self) -> None:
        """Update apply button enabled state."""
        has_code = hasattr(self, "_selected_code_id") and self._selected_code_id
        has_selection = hasattr(self, "_selected_text") and self._selected_text
        self._apply_btn.setEnabled(bool(has_code and has_selection))

    @Slot()
    def _on_apply_code(self) -> None:
        """Apply selected code to selected text."""
        if not hasattr(self, "_selected_code_id") or not self._selected_code_id:
            return
        if not hasattr(self, "_selection_start"):
            return

        # For demo, use source_id=1
        try:
            code_id = int(self._selected_code_id)
        except ValueError:
            self._status_label.setText("Invalid code ID")
            return

        success = self._viewmodel.apply_code_to_selection(
            code_id=code_id,
            source_id=1,
            start=self._selection_start,
            end=self._selection_end,
        )

        if success:
            # Get the code info for display
            code = self._context.controller.get_code(code_id)
            code_name = code.name if code else "Unknown"
            code_color = code.color.to_hex() if code else "#ffff00"

            self._status_label.setText(
                f"Applied code '{code_name}' to selection ({self._selection_start}-{self._selection_end})"
            )

            # Highlight the coded text in the editor
            self._screen.page.editor_panel.highlight_range(
                self._selection_start,
                self._selection_end,
                code_color,
            )

            # Refresh codes to update counts
            self._on_codes_changed(self._viewmodel.load_codes())
        else:
            self._status_label.setText("Failed to apply code")

    def closeEvent(self, event) -> None:
        """Clean up on close."""
        if self._context:
            self._context.close()
        super().closeEvent(event)


def main():
    """Run the connected demo."""
    app = QApplication(sys.argv)
    window = ConnectedTextCodingDemo()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
