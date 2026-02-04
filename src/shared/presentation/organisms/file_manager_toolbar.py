"""
File Manager Toolbar Organism

Provides action buttons and search for the File Manager screen.

Based on mockup analysis:
- Import Files (primary action)
- Link Files (secondary)
- Create Text (secondary)
- Export (secondary)
- Search box for filtering

Addresses UX-004 from UX_TECH_DEBT.md:
- Import becomes secondary when files are selected
- Primary action shifts to contextual actions
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout

from design_system import ColorPalette, get_colors
from design_system.components import Button
from design_system.forms import SearchBox
from design_system.tokens import SPACING


class FileManagerToolbar(QFrame):
    """
    Toolbar for File Manager screen with actions and search.

    Signals:
        import_clicked: User wants to import files
        link_clicked: User wants to link external files
        create_text_clicked: User wants to create a new text document
        export_clicked: User wants to export files
        search_changed(str): Search text changed
    """

    import_clicked = Signal()
    link_clicked = Signal()
    create_text_clicked = Signal()
    export_clicked = Signal()
    search_changed = Signal(str)

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self._setup_ui()

    def _setup_ui(self):
        """Build the toolbar UI."""
        self.setStyleSheet("""
            FileManagerToolbar {
                background-color: transparent;
                border: none;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.md)

        # Left side: Action buttons
        self._import_btn = self._create_button(
            "Import Files",
            "mdi6.file-import-outline",
            variant="primary",
        )
        self._import_btn.clicked.connect(self.import_clicked.emit)
        layout.addWidget(self._import_btn)

        self._link_btn = self._create_button(
            "Link Files",
            "mdi6.link-variant",
            variant="secondary",
        )
        self._link_btn.clicked.connect(self.link_clicked.emit)
        layout.addWidget(self._link_btn)

        self._create_text_btn = self._create_button(
            "Create Text",
            "mdi6.file-plus-outline",
            variant="secondary",
        )
        self._create_text_btn.clicked.connect(self.create_text_clicked.emit)
        layout.addWidget(self._create_text_btn)

        self._export_btn = self._create_button(
            "Export",
            "mdi6.export-variant",
            variant="secondary",
        )
        self._export_btn.clicked.connect(self.export_clicked.emit)
        layout.addWidget(self._export_btn)

        # Spacer
        layout.addStretch()

        # Right side: Search box
        self._search_box = SearchBox(
            placeholder="Search file names...",
            colors=self._colors,
        )
        self._search_box.setFixedWidth(280)
        self._search_box.text_changed.connect(self.search_changed.emit)
        layout.addWidget(self._search_box)

    def _create_button(
        self, text: str, icon_name: str, variant: str = "secondary"
    ) -> Button:
        """Create a button with icon."""
        btn = Button(text, variant=variant, size="md", colors=self._colors)

        # Add icon using qtawesome
        try:
            import qtawesome as qta

            btn.setIcon(qta.icon(icon_name, color=self._get_icon_color(variant)))
        except ImportError:
            pass  # No icon if qtawesome not available

        return btn

    def _get_icon_color(self, variant: str) -> str:
        """Get icon color based on button variant."""
        if variant == "primary":
            return self._colors.primary_foreground
        return self._colors.text_primary

    def search_text(self) -> str:
        """Get current search text."""
        return self._search_box.text()

    def clear_search(self):
        """Clear the search box."""
        self._search_box.clear()

    def set_import_enabled(self, enabled: bool):
        """Enable or disable the import button."""
        self._import_btn.setEnabled(enabled)

    def set_export_enabled(self, enabled: bool):
        """Enable or disable the export button."""
        self._export_btn.setEnabled(enabled)


class EmptyState(QFrame):
    """
    Empty state display when no files are present.

    Addresses UX-002 from UX_TECH_DEBT.md:
    - Clear call-to-action for new users
    - Shows supported file types
    """

    import_clicked = Signal()
    link_clicked = Signal()

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self._setup_ui()

    def _setup_ui(self):
        """Build the empty state UI."""
        from PySide6.QtWidgets import QLabel, QVBoxLayout

        self.setStyleSheet(f"""
            EmptyState {{
                background-color: {self._colors.surface};
                border: 2px dashed {self._colors.border};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING.xxl, SPACING.xxl * 2, SPACING.xxl, SPACING.xxl * 2
        )
        layout.setSpacing(SPACING.lg)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon
        icon_label = QLabel()
        try:
            import qtawesome as qta

            icon_label.setPixmap(
                qta.icon(
                    "mdi6.folder-open-outline", color=self._colors.text_disabled
                ).pixmap(64, 64)
            )
        except ImportError:
            icon_label.setText("📁")
            icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Title
        title = QLabel("No files yet")
        title.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: 20px;
            font-weight: 600;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Description
        desc = QLabel(
            "Import your first source files to\nstart coding your qualitative data"
        )
        desc.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: 14px;
        """)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(SPACING.md)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        import_btn = Button(
            "Import Files", variant="primary", size="lg", colors=self._colors
        )
        try:
            import qtawesome as qta

            import_btn.setIcon(
                qta.icon(
                    "mdi6.file-import-outline", color=self._colors.primary_foreground
                )
            )
        except ImportError:
            pass
        import_btn.clicked.connect(self.import_clicked.emit)
        btn_layout.addWidget(import_btn)

        link_btn = Button(
            "Link External Files", variant="outline", size="lg", colors=self._colors
        )
        try:
            import qtawesome as qta

            link_btn.setIcon(
                qta.icon("mdi6.link-variant", color=self._colors.text_primary)
            )
        except ImportError:
            pass
        link_btn.clicked.connect(self.link_clicked.emit)
        btn_layout.addWidget(link_btn)

        layout.addLayout(btn_layout)

        # Supported formats hint
        formats = QLabel("Supported: TXT, DOCX, PDF, MP3, MP4, JPG, PNG")
        formats.setStyleSheet(f"""
            color: {self._colors.text_hint};
            font-size: 12px;
        """)
        formats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(formats)
