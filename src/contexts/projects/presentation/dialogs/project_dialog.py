"""
Project Dialog Components

Implements QC-026 Open & Navigate Project:
- AC #1: Researcher can open an existing project file
- AC #2: Researcher can create a new project
"""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from design_system import (
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    ColorPalette,
    Icon,
    get_colors,
)


class OpenProjectDialog(QDialog):
    """
    Dialog for opening an existing project.

    Provides:
    - Recent projects list (clickable)
    - Browse button for file system navigation

    Signals:
        project_selected(str): Emitted when a project path is selected
        cancel_clicked(): Emitted when cancel button is clicked
    """

    project_selected = Signal(str)
    cancel_clicked = Signal()

    def __init__(
        self,
        recent_projects: list[dict] | None = None,
        colors: ColorPalette = None,
        parent=None,
    ):
        """
        Initialize the dialog.

        Args:
            recent_projects: List of recent project dicts with keys:
                - name: Project name
                - path: Project path
                - last_opened: Optional datetime string
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._recent_projects = recent_projects or []
        self._selected_path: str = ""

        self.setWindowTitle("Open Project")
        self.setModal(True)
        self.setMinimumSize(500, 400)

        self._setup_ui()

    def _setup_ui(self):
        """Build the dialog UI."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self._colors.surface};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self._setup_header(layout)

        # Content area
        content_frame = QFrame()
        content_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
            }}
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(
            SPACING.lg, SPACING.md, SPACING.lg, SPACING.md
        )
        content_layout.setSpacing(SPACING.md)

        # Recent projects section
        if self._recent_projects:
            recent_label = QLabel("Recent Projects")
            recent_label.setStyleSheet(f"""
                color: {self._colors.text_primary};
                font-size: {TYPOGRAPHY.text_sm}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            """)
            content_layout.addWidget(recent_label)

            self._recent_list = QListWidget()
            self._recent_list.setStyleSheet(f"""
                QListWidget {{
                    background-color: {self._colors.surface_light};
                    color: {self._colors.text_primary};
                    border: 1px solid {self._colors.border};
                    border-radius: {RADIUS.md}px;
                    padding: {SPACING.sm}px;
                }}
                QListWidget::item {{
                    padding: {SPACING.sm}px;
                    border-radius: {RADIUS.sm}px;
                }}
                QListWidget::item:selected {{
                    background-color: {self._colors.primary};
                    color: {self._colors.primary_foreground};
                }}
                QListWidget::item:hover {{
                    background-color: {self._colors.surface};
                }}
            """)
            self._recent_list.itemDoubleClicked.connect(self._on_recent_double_clicked)
            self._recent_list.itemClicked.connect(self._on_recent_clicked)

            for project in self._recent_projects:
                item = QListWidgetItem(f"{project.get('name', 'Unknown')}")
                item.setToolTip(project.get("path", ""))
                item.setData(Qt.ItemDataRole.UserRole, project.get("path", ""))
                self._recent_list.addItem(item)

            content_layout.addWidget(self._recent_list, 1)
        else:
            # No recent projects message
            empty_label = QLabel("No recent projects")
            empty_label.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_sm}px;
            """)
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addWidget(empty_label, 1)

        # Browse section
        browse_frame = QFrame()
        browse_layout = QHBoxLayout(browse_frame)
        browse_layout.setContentsMargins(0, SPACING.md, 0, 0)

        browse_label = QLabel("Or browse for project file:")
        browse_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        browse_layout.addWidget(browse_label)
        browse_layout.addStretch()

        self._browse_btn = QPushButton("Browse...")
        self._browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.surface};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)
        self._browse_btn.clicked.connect(self._on_browse_clicked)
        browse_layout.addWidget(self._browse_btn)

        content_layout.addWidget(browse_frame)

        layout.addWidget(content_frame, 1)

        # Footer with buttons
        self._setup_footer(layout)

    def _setup_header(self, layout: QVBoxLayout):
        """Setup the dialog header."""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)

        # Icon
        self._icon = Icon(
            "mdi6.folder-open",
            size=24,
            color=self._colors.primary,
            colors=self._colors,
        )
        header_layout.addWidget(self._icon)

        # Title
        title_label = QLabel("Open Project")
        title_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addWidget(header)

    def _setup_footer(self, layout: QVBoxLayout):
        """Setup the dialog footer with buttons."""
        footer = QFrame()
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-top: 1px solid {self._colors.border};
            }}
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)
        footer_layout.addStretch()

        # Cancel button
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.surface};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.lg}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)
        self._cancel_btn.clicked.connect(self._on_cancel)
        footer_layout.addWidget(self._cancel_btn)

        # Open button
        self._open_btn = QPushButton("Open")
        self._open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_btn.setEnabled(False)
        self._open_btn.setStyleSheet(f"""
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
            QPushButton:disabled {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_secondary};
            }}
        """)
        self._open_btn.clicked.connect(self._on_open)
        footer_layout.addWidget(self._open_btn)

        layout.addWidget(footer)

    def _on_recent_clicked(self, item: QListWidgetItem):
        """Handle recent project item click."""
        self._selected_path = item.data(Qt.ItemDataRole.UserRole) or ""
        self._open_btn.setEnabled(bool(self._selected_path))

    def _on_recent_double_clicked(self, item: QListWidgetItem):
        """Handle recent project item double-click."""
        self._selected_path = item.data(Qt.ItemDataRole.UserRole) or ""
        if self._selected_path:
            self._on_open()

    def _on_browse_clicked(self):
        """Handle browse button click."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open QualCoder Project",
            "",
            "QualCoder Projects (*.qda);;All Files (*)",
        )
        if path:
            self._selected_path = path
            self._open_btn.setEnabled(True)
            # Clear list selection
            if hasattr(self, "_recent_list"):
                self._recent_list.clearSelection()

    def _on_open(self):
        """Handle open button click."""
        if self._selected_path:
            self.project_selected.emit(self._selected_path)
            self.accept()

    def _on_cancel(self):
        """Handle cancel button click."""
        self.cancel_clicked.emit()
        self.reject()

    def get_selected_path(self) -> str:
        """Get the selected project path."""
        return self._selected_path


class CreateProjectDialog(QDialog):
    """
    Dialog for creating a new project.

    Provides:
    - Project name input
    - Location selection (directory + filename)

    Signals:
        project_created(str, str): Emitted with (name, path) when create is clicked
        cancel_clicked(): Emitted when cancel button is clicked
    """

    project_created = Signal(str, str)  # name, path
    cancel_clicked = Signal()

    def __init__(
        self,
        default_directory: str = "",
        colors: ColorPalette = None,
        parent=None,
    ):
        """
        Initialize the dialog.

        Args:
            default_directory: Default directory for project location
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._default_directory = default_directory or str(Path.home())

        self.setWindowTitle("Create New Project")
        self.setModal(True)
        self.setMinimumSize(500, 280)

        self._setup_ui()

    def _setup_ui(self):
        """Build the dialog UI."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self._colors.surface};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self._setup_header(layout)

        # Content area
        content_frame = QFrame()
        content_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
            }}
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(
            SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg
        )
        content_layout.setSpacing(SPACING.lg)

        # Project name input
        name_label = QLabel("Project Name")
        name_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        content_layout.addWidget(name_label)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Enter project name...")
        self._name_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QLineEdit:focus {{
                border-color: {self._colors.primary};
            }}
            QLineEdit::placeholder {{
                color: {self._colors.text_secondary};
            }}
        """)
        self._name_input.textChanged.connect(self._on_name_changed)
        content_layout.addWidget(self._name_input)

        # Location input
        location_label = QLabel("Location")
        location_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        content_layout.addWidget(location_label)

        location_frame = QFrame()
        location_layout = QHBoxLayout(location_frame)
        location_layout.setContentsMargins(0, 0, 0, 0)
        location_layout.setSpacing(SPACING.sm)

        self._location_input = QLineEdit()
        self._location_input.setText(self._default_directory)
        self._location_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QLineEdit:focus {{
                border-color: {self._colors.primary};
            }}
        """)
        self._location_input.textChanged.connect(self._on_location_changed)
        location_layout.addWidget(self._location_input, 1)

        self._location_btn = QPushButton("Browse...")
        self._location_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._location_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.surface};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)
        self._location_btn.clicked.connect(self._on_browse_clicked)
        location_layout.addWidget(self._location_btn)

        content_layout.addWidget(location_frame)

        # Preview of full path
        self._path_preview = QLabel("")
        self._path_preview.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)
        self._path_preview.setWordWrap(True)
        content_layout.addWidget(self._path_preview)

        content_layout.addStretch()

        layout.addWidget(content_frame, 1)

        # Footer with buttons
        self._setup_footer(layout)

        # Update preview
        self._update_path_preview()

    def _setup_header(self, layout: QVBoxLayout):
        """Setup the dialog header."""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)

        # Icon
        self._icon = Icon(
            "mdi6.folder-plus",
            size=24,
            color=self._colors.primary,
            colors=self._colors,
        )
        header_layout.addWidget(self._icon)

        # Title
        title_label = QLabel("Create New Project")
        title_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addWidget(header)

    def _setup_footer(self, layout: QVBoxLayout):
        """Setup the dialog footer with buttons."""
        footer = QFrame()
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-top: 1px solid {self._colors.border};
            }}
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)
        footer_layout.addStretch()

        # Cancel button
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.surface};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.lg}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)
        self._cancel_btn.clicked.connect(self._on_cancel)
        footer_layout.addWidget(self._cancel_btn)

        # Create button
        self._create_btn = QPushButton("Create")
        self._create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._create_btn.setEnabled(False)
        self._create_btn.setStyleSheet(f"""
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
            QPushButton:disabled {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_secondary};
            }}
        """)
        self._create_btn.clicked.connect(self._on_create)
        footer_layout.addWidget(self._create_btn)

        layout.addWidget(footer)

    def _on_name_changed(self, _text: str):
        """Handle project name change."""
        self._update_path_preview()
        self._update_create_button()

    def _on_location_changed(self, _text: str):
        """Handle location change."""
        self._update_path_preview()
        self._update_create_button()

    def _on_browse_clicked(self):
        """Handle browse button click."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Project Location",
            self._location_input.text() or self._default_directory,
        )
        if directory:
            self._location_input.setText(directory)

    def _update_path_preview(self):
        """Update the path preview label."""
        name = self._name_input.text().strip()
        location = self._location_input.text().strip()

        if name and location:
            # Sanitize name for filename
            safe_name = "".join(c for c in name if c.isalnum() or c in " _-")
            safe_name = safe_name.strip().replace(" ", "_")
            if safe_name:
                full_path = Path(location) / f"{safe_name}.qda"
                self._path_preview.setText(f"Project will be created at: {full_path}")
            else:
                self._path_preview.setText("")
        else:
            self._path_preview.setText("")

    def _update_create_button(self):
        """Update the create button enabled state."""
        name = self._name_input.text().strip()
        location = self._location_input.text().strip()
        location_exists = Path(location).exists() if location else False
        self._create_btn.setEnabled(bool(name) and location_exists)

    def _on_create(self):
        """Handle create button click."""
        name = self._name_input.text().strip()
        location = self._location_input.text().strip()

        if name and location:
            # Generate safe filename
            safe_name = "".join(c for c in name if c.isalnum() or c in " _-")
            safe_name = safe_name.strip().replace(" ", "_")
            full_path = str(Path(location) / f"{safe_name}.qda")

            self.project_created.emit(name, full_path)
            self.accept()

    def _on_cancel(self):
        """Handle cancel button click."""
        self.cancel_clicked.emit()
        self.reject()

    def get_project_name(self) -> str:
        """Get the entered project name."""
        return self._name_input.text().strip()

    def get_project_path(self) -> str:
        """Get the full project path."""
        name = self._name_input.text().strip()
        location = self._location_input.text().strip()
        if name and location:
            safe_name = "".join(c for c in name if c.isalnum() or c in " _-")
            safe_name = safe_name.strip().replace(" ", "_")
            return str(Path(location) / f"{safe_name}.qda")
        return ""
