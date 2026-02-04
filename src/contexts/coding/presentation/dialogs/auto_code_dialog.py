"""
Auto-Code Dialog Components

Implements QC-007.07 Auto-Coding Features:
- AC #1: Auto-code exact text matches (all/first/last)
- AC #2: Auto-code similar fragments/sentences
- AC #3: Mark speakers pattern detection
- AC #4: Progress indicator for batch operations
- AC #5: Undo last auto-code batch
- AC #6: Preview matches before applying

Architecture (fDDD):
- Dialog emits SIGNALS for operations (find_matches_requested, etc.)
- Controller receives signals, calls domain services
- Controller emits result PAYLOADS via signal bridge
- Dialog receives payloads and updates UI

This follows proper fDDD decoupling - presentation NEVER imports domain.
"""

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from design_system import (
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    ColorPalette,
    get_colors,
)


class AutoCodeDialog(QDialog):
    """
    Dialog for configuring and applying auto-coding.

    Allows user to:
    - Enter search pattern
    - Select match type (exact, contains, regex)
    - Select scope (all, first, last)
    - Preview matches before applying

    Architecture:
    - Emits signals for operations (find_matches_requested, etc.)
    - Receives results via slots (on_matches_found, etc.)
    - NEVER directly calls domain services

    Signals:
        find_matches_requested: Request to find matches
        detect_speakers_requested: Request to detect speakers
        apply_auto_code_requested: Request to apply auto-code
    """

    # Request signals - emitted when user wants an operation
    find_matches_requested = Signal(
        str, str, str, str, bool
    )  # text, pattern, match_type, scope, case_sensitive
    detect_speakers_requested = Signal(str)  # text
    get_speaker_segments_requested = Signal(str, str)  # text, speaker_name
    apply_auto_code_requested = Signal(dict)  # config dict

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._code: dict[str, Any] = {}
        self._pattern: str = ""
        self._text: str = ""  # Text to search in
        self._cached_matches: list[tuple[int, int]] = []  # Cache from last find

        self.setWindowTitle("Auto-Code")
        self.setModal(True)
        self.setMinimumSize(450, 350)

        self._setup_ui()

    def _setup_ui(self):
        """Build the dialog UI."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self._colors.surface};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.lg)

        # Title
        title = QLabel("Auto-Code Text Matches")
        title.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
        """)
        layout.addWidget(title)

        # Code display
        self._code_frame = QFrame()
        self._code_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.sm}px;
            }}
        """)
        code_layout = QHBoxLayout(self._code_frame)
        code_layout.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.sm, SPACING.xs)

        self._code_color = QFrame()
        self._code_color.setFixedSize(16, 16)
        self._code_color.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.text_disabled};
                border-radius: {RADIUS.xs}px;
            }}
        """)
        code_layout.addWidget(self._code_color)

        self._code_label = QLabel("No code selected")
        self._code_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        code_layout.addWidget(self._code_label)
        code_layout.addStretch()

        layout.addWidget(self._code_frame)

        # Pattern input
        pattern_label = QLabel("Search Pattern")
        pattern_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        layout.addWidget(pattern_label)

        self._pattern_input = QLineEdit()
        self._pattern_input.setPlaceholderText("Enter text to find...")
        self._pattern_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.sm}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QLineEdit:focus {{
                border-color: {self._colors.primary};
            }}
        """)
        self._pattern_input.textChanged.connect(self._on_pattern_changed)
        layout.addWidget(self._pattern_input)

        # Options row
        options_layout = QHBoxLayout()
        options_layout.setSpacing(SPACING.lg)

        # Match type
        match_group = QVBoxLayout()
        match_label = QLabel("Match Type")
        match_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)
        match_group.addWidget(match_label)

        self._match_combo = QComboBox()
        self._match_combo.addItems(["Exact word", "Contains", "Regex"])
        self._match_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.xs}px {SPACING.sm}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
        """)
        match_group.addWidget(self._match_combo)
        options_layout.addLayout(match_group)

        # Scope
        scope_group = QVBoxLayout()
        scope_label = QLabel("Apply To")
        scope_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)
        scope_group.addWidget(scope_label)

        self._scope_combo = QComboBox()
        self._scope_combo.addItems(["All matches", "First only", "Last only"])
        self._scope_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.xs}px {SPACING.sm}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
        """)
        scope_group.addWidget(self._scope_combo)
        options_layout.addLayout(scope_group)

        options_layout.addStretch()
        layout.addLayout(options_layout)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.lg}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        preview_btn = QPushButton("Preview")
        preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        preview_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.surface_light};
                color: {self._colors.primary};
                border: 1px solid {self._colors.primary};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.lg}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.primary}10;
            }}
        """)
        preview_btn.clicked.connect(self._on_preview)
        btn_layout.addWidget(preview_btn)

        apply_btn = QPushButton("Apply")
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.primary};
                color: {self._colors.primary_foreground};
                border: none;
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.lg}px;
                font-size: {TYPOGRAPHY.text_sm}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            }}
            QPushButton:hover {{
                background-color: {self._colors.primary_light};
            }}
        """)
        apply_btn.clicked.connect(self._on_apply)
        btn_layout.addWidget(apply_btn)

        layout.addLayout(btn_layout)

    def _on_pattern_changed(self, text: str):
        """Handle pattern input change."""
        self._pattern = text

    def _on_preview(self):
        """
        Handle preview button click.

        Emits find_matches_requested signal - controller will handle
        the domain service call and emit results back.
        """
        if not self._text or not self._pattern:
            return

        match_type = self._get_match_type_str()
        scope = self._get_scope_str()

        # Emit signal for controller to handle
        self.find_matches_requested.emit(
            self._text,
            self._pattern,
            match_type,
            scope,
            False,  # case_sensitive
        )

    def _on_apply(self):
        """
        Handle apply button click.

        Emits apply signals - controller will handle the actual operation.
        """
        match_type = self._get_match_type_str()
        scope = self._get_scope_str()

        config = {
            "pattern": self._pattern,
            "match_type": match_type,
            "scope": scope,
            "code": self._code,
        }

        self.apply_auto_code_requested.emit(config)
        self.accept()

    def _get_match_type_str(self) -> str:
        """Get match type as string."""
        index = self._match_combo.currentIndex()
        return ["exact", "contains", "regex"][index]

    def _get_scope_str(self) -> str:
        """Get scope as string."""
        index = self._scope_combo.currentIndex()
        return ["all", "first", "last"][index]

    # =========================================================================
    # Slots for receiving results from controller
    # =========================================================================

    def on_matches_found(self, matches: list[tuple[int, int]]):
        """
        Slot to receive matches found by controller.

        Args:
            matches: List of (start, end) tuples
        """
        self._cached_matches = matches
        # Could update a preview widget here

    def on_speakers_detected(self, speakers: list[dict[str, Any]]):
        """
        Slot to receive detected speakers from controller.

        Args:
            speakers: List of speaker dicts with 'name' and 'count'
        """
        # Could update speaker selection UI here
        pass

    def on_error(self, operation: str, message: str):
        """
        Slot to receive error notifications.

        Args:
            operation: Which operation failed
            message: Error message
        """
        # Could show error dialog here
        pass

    # =========================================================================
    # Public API
    # =========================================================================

    def set_text(self, text: str):
        """Set the text to search in."""
        self._text = text

    def set_pattern(self, pattern: str):
        """Set the search pattern."""
        self._pattern = pattern
        self._pattern_input.setText(pattern)

    def get_pattern(self) -> str:
        """Get the current pattern."""
        return self._pattern

    def set_code(self, code: dict[str, Any]):
        """Set the code to apply."""
        self._code = code
        self._code_label.setText(code.get("name", "Unknown"))
        color = code.get("color", self._colors.text_disabled)
        self._code_color.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: {RADIUS.xs}px;
            }}
        """)

    def get_code(self) -> dict[str, Any]:
        """Get the selected code."""
        return self._code

    def get_available_match_types(self) -> list[str]:
        """Get available match type options."""
        return ["exact", "contains", "regex"]

    def get_available_scopes(self) -> list[str]:
        """Get available scope options."""
        return ["all", "first", "last"]

    def get_cached_matches(self) -> list[tuple[int, int]]:
        """Get the last cached matches (for testing)."""
        return self._cached_matches
