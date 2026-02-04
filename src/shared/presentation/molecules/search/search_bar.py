"""
Search Bar Molecule

A search input widget with navigation buttons and search options.
Pure presentation component - emits signals for search actions,
receives results to display via set_results().

Signals:
    search_changed(str): Emitted when search query changes
    next_clicked(): Emitted when next button clicked
    prev_clicked(): Emitted when prev button clicked
    close_clicked(): Emitted when close button clicked
    options_changed(): Emitted when search options change
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
)

from design_system import (
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    Button,
    ColorPalette,
    Input,
    get_colors,
)


class SearchBar(QFrame):
    """
    Search bar widget for text search functionality.

    Provides search input, navigation buttons, and options for case sensitivity and regex.
    This is a pure presentation molecule - it doesn't perform searches, only emits signals
    and displays results provided via set_results().

    Example:
        search_bar = SearchBar()
        search_bar.search_changed.connect(on_search)
        search_bar.next_clicked.connect(on_next)

        # Update results from search engine
        search_bar.set_results(current=2, total=5)
    """

    search_changed = Signal(str)
    next_clicked = Signal()
    prev_clicked = Signal()
    close_clicked = Signal()
    options_changed = Signal()

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._case_sensitive = False
        self._use_regex = False

        self.setVisible(False)  # Hidden by default
        self._setup_ui()

    def _setup_ui(self):
        """Build the search widget UI."""
        self.setStyleSheet(f"""
            SearchBar {{
                background-color: {self._colors.surface};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.sm, SPACING.xs)
        layout.setSpacing(SPACING.sm)

        # Search input - using design_system.Input
        self._search_input = Input(placeholder="Search...", colors=self._colors)
        self._search_input.setFixedWidth(200)
        self._search_input.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self._search_input)

        # Status label
        self._status_label = QLabel("0 / 0")
        self._status_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
            min-width: 50px;
        """)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)

        # Navigation buttons - using design_system.Button with icon variant
        self._prev_btn = Button("▲", variant="icon", size="sm", colors=self._colors)
        self._prev_btn.setFixedSize(24, 24)
        self._prev_btn.setToolTip("Previous match (Shift+Enter)")
        self._prev_btn.clicked.connect(self.prev_clicked.emit)
        layout.addWidget(self._prev_btn)

        self._next_btn = Button("▼", variant="icon", size="sm", colors=self._colors)
        self._next_btn.setFixedSize(24, 24)
        self._next_btn.setToolTip("Next match (Enter)")
        self._next_btn.clicked.connect(self.next_clicked.emit)
        layout.addWidget(self._next_btn)

        # Options buttons - using design_system.Button with ghost variant
        # Note: Button extends QPushButton so setCheckable works
        self._case_btn = Button("Aa", variant="ghost", size="sm", colors=self._colors)
        self._case_btn.setCheckable(True)
        self._case_btn.setToolTip("Case sensitive")
        self._case_btn.setStyleSheet(
            self._case_btn.styleSheet()
            + f"""
            QPushButton:checked {{
                background-color: {self._colors.primary}20;
                color: {self._colors.primary};
                border: 1px solid {self._colors.primary};
            }}
        """
        )
        self._case_btn.toggled.connect(self._on_case_toggled)
        layout.addWidget(self._case_btn)

        self._regex_btn = Button(".*", variant="ghost", size="sm", colors=self._colors)
        self._regex_btn.setCheckable(True)
        self._regex_btn.setToolTip("Regular expression")
        self._regex_btn.setStyleSheet(
            self._regex_btn.styleSheet()
            + f"""
            QPushButton:checked {{
                background-color: {self._colors.primary}20;
                color: {self._colors.primary};
                border: 1px solid {self._colors.primary};
            }}
        """
        )
        self._regex_btn.toggled.connect(self._on_regex_toggled)
        layout.addWidget(self._regex_btn)

        # Close button - using design_system.Button with icon variant
        self._close_btn = Button("×", variant="icon", size="sm", colors=self._colors)
        self._close_btn.setFixedSize(24, 24)
        self._close_btn.setToolTip("Close search (Esc)")
        self._close_btn.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self._close_btn)

    def _on_case_toggled(self, checked: bool):
        """Handle case sensitivity toggle."""
        self._case_sensitive = checked
        self.options_changed.emit()

    def _on_regex_toggled(self, checked: bool):
        """Handle regex toggle."""
        self._use_regex = checked
        self.options_changed.emit()

    # =========================================================================
    # Public API - Results Display
    # =========================================================================

    def set_results(self, current: int, total: int):
        """
        Update the match count display.

        Args:
            current: Current match index (1-indexed for display)
            total: Total number of matches
        """
        if total == 0:
            self._status_label.setText("No results")
        else:
            self._status_label.setText(f"{current} / {total}")

    def get_status_text(self) -> str:
        """Get the current status text."""
        return self._status_label.text()

    # =========================================================================
    # Public API - Options
    # =========================================================================

    def is_case_sensitive(self) -> bool:
        """Check if case sensitive search is enabled."""
        return self._case_sensitive

    def set_case_sensitive(self, enabled: bool):
        """Set case sensitive search option."""
        self._case_sensitive = enabled
        self._case_btn.setChecked(enabled)

    def is_regex(self) -> bool:
        """Check if regex search is enabled."""
        return self._use_regex

    def set_regex(self, enabled: bool):
        """Set regex search option."""
        self._use_regex = enabled
        self._regex_btn.setChecked(enabled)

    # =========================================================================
    # Public API - Query
    # =========================================================================

    def get_query(self) -> str:
        """Get the current search query."""
        return self._search_input.text()

    def set_query(self, query: str):
        """Set the search query."""
        self._search_input.setText(query)

    def focus_input(self):
        """Focus the search input field."""
        self._search_input.setFocus()
        self._search_input.selectAll()
