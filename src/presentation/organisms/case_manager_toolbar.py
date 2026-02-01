"""
Case Manager Toolbar Organism

Toolbar for the Case Manager screen with create, import, export actions
and search functionality.

Implements QC-034 presentation layer:
- AC #1: Researcher can create cases
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout

from design_system import ColorPalette, get_colors
from design_system.components import Button, SearchBox
from design_system.tokens import SPACING


class CaseManagerToolbar(QFrame):
    """
    Toolbar for case management actions.

    Signals:
        create_case_clicked: Emitted when create case button is clicked
        import_clicked: Emitted when import button is clicked
        export_clicked: Emitted when export button is clicked
        search_changed: Emitted when search text changes (query)
    """

    create_case_clicked = Signal()
    import_clicked = Signal()
    export_clicked = Signal()
    search_changed = Signal(str)

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the toolbar UI."""
        self.setStyleSheet(f"""
            CaseManagerToolbar {{
                background-color: {self._colors.surface};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)
        layout.setSpacing(SPACING.md)

        # Left side - action buttons
        left_layout = QHBoxLayout()
        left_layout.setSpacing(SPACING.sm)

        # Create case button (primary)
        self._create_btn = Button(
            "Create Case",
            variant="primary",
            icon="mdi6.plus",
            colors=self._colors,
        )
        left_layout.addWidget(self._create_btn)

        # Import button
        self._import_btn = Button(
            "Import",
            variant="outline",
            icon="mdi6.upload-outline",
            colors=self._colors,
        )
        left_layout.addWidget(self._import_btn)

        # Export button
        self._export_btn = Button(
            "Export",
            variant="outline",
            icon="mdi6.download-outline",
            colors=self._colors,
        )
        left_layout.addWidget(self._export_btn)

        layout.addLayout(left_layout)
        layout.addStretch()

        # Right side - search
        self._search = SearchBox(
            placeholder="Search cases...",
            colors=self._colors,
        )
        self._search.setFixedWidth(250)
        layout.addWidget(self._search)

    def _connect_signals(self):
        """Connect internal signals."""
        self._create_btn.clicked.connect(self.create_case_clicked.emit)
        self._import_btn.clicked.connect(self.import_clicked.emit)
        self._export_btn.clicked.connect(self.export_clicked.emit)
        self._search.textChanged.connect(self.search_changed.emit)

    def set_search_text(self, text: str):
        """Set the search text."""
        self._search.setText(text)

    def clear_search(self):
        """Clear the search text."""
        self._search.clear()
