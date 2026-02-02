"""
Settings Dialog

Implements QC-038 Settings and Preferences:
- AC #1: Researcher can change UI theme (dark, light, colors)
- AC #2: Researcher can configure font size and family
- AC #3: Researcher can select application language
- AC #4: Researcher can configure automatic backups
- AC #5: Researcher can set timestamp format for AV coding
- AC #6: Researcher can configure speaker name format

Structure:
    ┌─────────────────────────────────────────────────────────────────┐
    │ Settings                                                   [×]  │
    ├────────────┬────────────────────────────────────────────────────┤
    │            │                                                    │
    │ Appearance │  Theme                                             │
    │ Language   │  ○ Light   ● Dark   ○ System                       │
    │ Backup     │                                                    │
    │ AV Coding  │  Font                                              │
    │            │  Family: [Inter        ▼]                          │
    │            │  Size:   [──●────────] 14px                        │
    │            │                                                    │
    ├────────────┴────────────────────────────────────────────────────┤
    │                                        [Cancel]  [Apply]  [OK]  │
    └─────────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from design_system import (
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    ColorPalette,
    Icon,
    get_colors,
)

if TYPE_CHECKING:
    from src.presentation.viewmodels.settings_viewmodel import SettingsViewModel


class SettingsDialog(QDialog):
    """
    Settings and Preferences dialog.

    Provides a tabbed interface for configuring application settings.
    """

    settings_changed = Signal()

    def __init__(
        self,
        viewmodel: SettingsViewModel,
        colors: ColorPalette | None = None,
        parent: QWidget | None = None,
    ):
        """
        Initialize the dialog.

        Args:
            viewmodel: Settings ViewModel for data access
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._colors = colors or get_colors()
        self._pending_changes: dict = {}

        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumSize(700, 500)

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
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

        # Main content area with sidebar and stacked widget
        content_frame = QFrame()
        content_layout = QHBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Content stack (created first so sidebar can reference it)
        self._content_stack = QStackedWidget()
        self._content_stack.setStyleSheet(f"""
            QStackedWidget {{
                background-color: {self._colors.surface};
            }}
        """)
        self._content_stack.addWidget(self._create_appearance_section())
        self._content_stack.addWidget(self._create_language_section())
        self._content_stack.addWidget(self._create_backup_section())
        self._content_stack.addWidget(self._create_av_coding_section())

        # Sidebar navigation (created after content stack)
        self._sidebar = self._create_sidebar()
        content_layout.addWidget(self._sidebar)
        content_layout.addWidget(self._content_stack, 1)

        layout.addWidget(content_frame, 1)

        # Footer with buttons
        self._setup_footer(layout)

    def _setup_header(self, layout: QVBoxLayout) -> None:
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
        icon = Icon(
            "mdi6.cog",
            size=24,
            color=self._colors.primary,
            colors=self._colors,
        )
        header_layout.addWidget(icon)

        # Title
        title_label = QLabel("Settings")
        title_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addWidget(header)

    def _create_sidebar(self) -> QListWidget:
        """Create the sidebar navigation."""
        sidebar = QListWidget()
        sidebar.setFixedWidth(160)
        sidebar.setStyleSheet(f"""
            QListWidget {{
                background-color: {self._colors.surface_light};
                border: none;
                border-right: 1px solid {self._colors.border};
                outline: none;
            }}
            QListWidget::item {{
                padding: {SPACING.sm}px {SPACING.md}px;
                color: {self._colors.text_primary};
            }}
            QListWidget::item:selected {{
                background-color: {self._colors.primary};
                color: {self._colors.primary_foreground};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {self._colors.surface};
            }}
        """)

        sections = [
            ("Appearance", "mdi6.palette"),
            ("Language", "mdi6.translate"),
            ("Backup", "mdi6.backup-restore"),
            ("AV Coding", "mdi6.video"),
        ]

        for name, icon_name in sections:
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, icon_name)
            sidebar.addItem(item)

        sidebar.setCurrentRow(0)
        sidebar.currentRowChanged.connect(self._content_stack.setCurrentIndex)

        return sidebar

    def _create_appearance_section(self) -> QWidget:
        """Create the Appearance settings section."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.lg)

        # Theme section
        theme_label = QLabel("Theme")
        theme_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
        """)
        layout.addWidget(theme_label)

        theme_frame = QFrame()
        theme_layout = QHBoxLayout(theme_frame)
        theme_layout.setContentsMargins(0, 0, 0, 0)
        theme_layout.setSpacing(SPACING.md)

        self._theme_group = QButtonGroup(self)
        themes = [("Light", "light"), ("Dark", "dark"), ("System", "system")]

        for display_name, value in themes:
            btn = QPushButton(display_name)
            btn.setCheckable(True)
            btn.setProperty("theme_value", value)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._get_toggle_button_style())
            btn.clicked.connect(lambda _checked, v=value: self._on_theme_changed(v))
            self._theme_group.addButton(btn)
            theme_layout.addWidget(btn)

        theme_layout.addStretch()
        layout.addWidget(theme_frame)

        # Font section
        font_label = QLabel("Font")
        font_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
            margin-top: {SPACING.md}px;
        """)
        layout.addWidget(font_label)

        # Font family
        family_frame = QFrame()
        family_layout = QHBoxLayout(family_frame)
        family_layout.setContentsMargins(0, 0, 0, 0)
        family_layout.setSpacing(SPACING.sm)

        family_label = QLabel("Family:")
        family_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        family_layout.addWidget(family_label)

        self._font_combo = QComboBox()
        self._font_combo.setStyleSheet(self._get_combo_style())
        self._font_combo.setMinimumWidth(200)
        for font in self._viewmodel.get_available_fonts():
            self._font_combo.addItem(font.display_name, font.family)
        self._font_combo.currentIndexChanged.connect(self._on_font_changed)
        family_layout.addWidget(self._font_combo)
        family_layout.addStretch()

        layout.addWidget(family_frame)

        # Font size
        size_frame = QFrame()
        size_layout = QHBoxLayout(size_frame)
        size_layout.setContentsMargins(0, 0, 0, 0)
        size_layout.setSpacing(SPACING.sm)

        size_label = QLabel("Size:")
        size_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        size_layout.addWidget(size_label)

        self._font_slider = QSlider(Qt.Orientation.Horizontal)
        self._font_slider.setMinimum(10)
        self._font_slider.setMaximum(24)
        self._font_slider.setFixedWidth(200)
        self._font_slider.setStyleSheet(self._get_slider_style())
        self._font_slider.valueChanged.connect(self._on_font_size_changed)
        size_layout.addWidget(self._font_slider)

        self._font_size_label = QLabel("14px")
        self._font_size_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            min-width: 40px;
        """)
        size_layout.addWidget(self._font_size_label)
        size_layout.addStretch()

        layout.addWidget(size_frame)
        layout.addStretch()

        return widget

    def _create_language_section(self) -> QWidget:
        """Create the Language settings section."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.lg)

        # Language selection
        lang_label = QLabel("Application Language")
        lang_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
        """)
        layout.addWidget(lang_label)

        self._language_combo = QComboBox()
        self._language_combo.setStyleSheet(self._get_combo_style())
        self._language_combo.setMinimumWidth(250)
        for lang in self._viewmodel.get_available_languages():
            self._language_combo.addItem(lang.name, lang.code)
        self._language_combo.currentIndexChanged.connect(self._on_language_changed)
        layout.addWidget(self._language_combo)

        # Note about restart
        note_label = QLabel(
            "Note: Language changes may require an application restart."
        )
        note_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-style: italic;
        """)
        layout.addWidget(note_label)

        layout.addStretch()

        return widget

    def _create_backup_section(self) -> QWidget:
        """Create the Backup settings section."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.lg)

        # Backup header
        backup_label = QLabel("Automatic Backups")
        backup_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
        """)
        layout.addWidget(backup_label)

        # Enable checkbox
        self._backup_enabled = QCheckBox("Enable automatic backups")
        self._backup_enabled.setStyleSheet(f"""
            QCheckBox {{
                color: {self._colors.text_primary};
                font-size: {TYPOGRAPHY.text_sm}px;
                spacing: {SPACING.sm}px;
            }}
        """)
        self._backup_enabled.stateChanged.connect(self._on_backup_enabled_changed)
        layout.addWidget(self._backup_enabled)

        # Backup interval
        interval_frame = QFrame()
        interval_layout = QHBoxLayout(interval_frame)
        interval_layout.setContentsMargins(0, 0, 0, 0)
        interval_layout.setSpacing(SPACING.sm)

        interval_label = QLabel("Backup every:")
        interval_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        interval_layout.addWidget(interval_label)

        self._backup_interval = QSpinBox()
        self._backup_interval.setMinimum(5)
        self._backup_interval.setMaximum(120)
        self._backup_interval.setValue(30)
        self._backup_interval.setSuffix(" minutes")
        self._backup_interval.setStyleSheet(self._get_spinbox_style())
        self._backup_interval.valueChanged.connect(self._on_backup_interval_changed)
        interval_layout.addWidget(self._backup_interval)
        interval_layout.addStretch()

        layout.addWidget(interval_frame)

        # Max backups
        max_frame = QFrame()
        max_layout = QHBoxLayout(max_frame)
        max_layout.setContentsMargins(0, 0, 0, 0)
        max_layout.setSpacing(SPACING.sm)

        max_label = QLabel("Keep last:")
        max_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        max_layout.addWidget(max_label)

        self._backup_max = QSpinBox()
        self._backup_max.setMinimum(1)
        self._backup_max.setMaximum(20)
        self._backup_max.setValue(5)
        self._backup_max.setSuffix(" backups")
        self._backup_max.setStyleSheet(self._get_spinbox_style())
        self._backup_max.valueChanged.connect(self._on_backup_max_changed)
        max_layout.addWidget(self._backup_max)
        max_layout.addStretch()

        layout.addWidget(max_frame)

        # Backup path
        path_frame = QFrame()
        path_layout = QHBoxLayout(path_frame)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(SPACING.sm)

        path_label = QLabel("Backup location:")
        path_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        path_layout.addWidget(path_label)

        self._backup_path = QLineEdit()
        self._backup_path.setPlaceholderText("Default (project directory)")
        self._backup_path.setStyleSheet(self._get_input_style())
        path_layout.addWidget(self._backup_path, 1)

        browse_btn = QPushButton("Browse...")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setStyleSheet(self._get_button_style())
        browse_btn.clicked.connect(self._on_browse_backup_path)
        path_layout.addWidget(browse_btn)

        layout.addWidget(path_frame)

        layout.addStretch()

        return widget

    def _create_av_coding_section(self) -> QWidget:
        """Create the AV Coding settings section."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.lg)

        # Timestamp format
        ts_label = QLabel("Timestamp Format")
        ts_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
        """)
        layout.addWidget(ts_label)

        self._timestamp_combo = QComboBox()
        self._timestamp_combo.setStyleSheet(self._get_combo_style())
        self._timestamp_combo.setMinimumWidth(200)
        formats = self._viewmodel.get_available_timestamp_formats()
        for fmt in formats:
            display = {
                "HH:MM:SS": "Hours:Minutes:Seconds (00:05:30)",
                "HH:MM:SS.mmm": "With milliseconds (00:05:30.250)",
                "MM:SS": "Minutes:Seconds (05:30)",
            }.get(fmt, fmt)
            self._timestamp_combo.addItem(display, fmt)
        self._timestamp_combo.currentIndexChanged.connect(self._on_timestamp_changed)
        layout.addWidget(self._timestamp_combo)

        # Speaker format
        speaker_label = QLabel("Speaker Name Format")
        speaker_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
            margin-top: {SPACING.md}px;
        """)
        layout.addWidget(speaker_label)

        speaker_frame = QFrame()
        speaker_layout = QHBoxLayout(speaker_frame)
        speaker_layout.setContentsMargins(0, 0, 0, 0)
        speaker_layout.setSpacing(SPACING.sm)

        self._speaker_format = QLineEdit()
        self._speaker_format.setPlaceholderText("Speaker {n}")
        self._speaker_format.setStyleSheet(self._get_input_style())
        self._speaker_format.textChanged.connect(self._on_speaker_format_changed)
        speaker_layout.addWidget(self._speaker_format, 1)

        layout.addWidget(speaker_frame)

        # Preview
        preview_label = QLabel("Preview:")
        preview_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)
        layout.addWidget(preview_label)

        self._speaker_preview = QLabel("Speaker 1, Speaker 2, Speaker 3")
        self._speaker_preview.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-style: italic;
        """)
        layout.addWidget(self._speaker_preview)

        # Help text
        help_label = QLabel("Use {n} as placeholder for speaker number")
        help_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)
        layout.addWidget(help_label)

        layout.addStretch()

        return widget

    def _setup_footer(self, layout: QVBoxLayout) -> None:
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
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(self._get_button_style())
        cancel_btn.clicked.connect(self.reject)
        footer_layout.addWidget(cancel_btn)

        # OK button
        ok_btn = QPushButton("OK")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setStyleSheet(self._get_primary_button_style())
        ok_btn.clicked.connect(self._on_ok)
        footer_layout.addWidget(ok_btn)

        layout.addWidget(footer)

    # =========================================================================
    # Load Settings
    # =========================================================================

    def _load_settings(self) -> None:
        """Load current settings into UI."""
        settings = self._viewmodel.get_settings()

        # Theme
        for btn in self._theme_group.buttons():
            if btn.property("theme_value") == settings.theme:
                btn.setChecked(True)
                break

        # Font
        index = self._font_combo.findData(settings.font_family)
        if index >= 0:
            self._font_combo.setCurrentIndex(index)
        self._font_slider.setValue(settings.font_size)
        self._font_size_label.setText(f"{settings.font_size}px")

        # Language
        lang_index = self._language_combo.findData(settings.language_code)
        if lang_index >= 0:
            self._language_combo.setCurrentIndex(lang_index)

        # Backup
        self._backup_enabled.setChecked(settings.backup_enabled)
        self._backup_interval.setValue(settings.backup_interval)
        self._backup_max.setValue(settings.backup_max)
        if settings.backup_path:
            self._backup_path.setText(settings.backup_path)

        # AV Coding
        ts_index = self._timestamp_combo.findData(settings.timestamp_format)
        if ts_index >= 0:
            self._timestamp_combo.setCurrentIndex(ts_index)
        self._speaker_format.setText(settings.speaker_format)
        self._update_speaker_preview()

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_theme_changed(self, theme: str) -> None:
        """Handle theme selection."""
        self._viewmodel.change_theme(theme)
        self.settings_changed.emit()

    def _on_font_changed(self, _index: int) -> None:
        """Handle font family change."""
        family = self._font_combo.currentData()
        size = self._font_slider.value()
        if family:
            self._viewmodel.change_font(family, size)
            self.settings_changed.emit()

    def _on_font_size_changed(self, value: int) -> None:
        """Handle font size change."""
        self._font_size_label.setText(f"{value}px")
        family = self._font_combo.currentData()
        if family:
            self._viewmodel.change_font(family, value)
            self.settings_changed.emit()

    def _on_language_changed(self, _index: int) -> None:
        """Handle language change."""
        code = self._language_combo.currentData()
        if code:
            self._viewmodel.change_language(code)
            self.settings_changed.emit()

    def _on_backup_enabled_changed(self, _state: int) -> None:
        """Handle backup enabled change."""
        self._apply_backup_settings()

    def _on_backup_interval_changed(self, _value: int) -> None:
        """Handle backup interval change."""
        self._apply_backup_settings()

    def _on_backup_max_changed(self, _value: int) -> None:
        """Handle backup max change."""
        self._apply_backup_settings()

    def _apply_backup_settings(self) -> None:
        """Apply backup settings."""
        enabled = self._backup_enabled.isChecked()
        interval = self._backup_interval.value()
        max_backups = self._backup_max.value()
        path = self._backup_path.text() or None

        self._viewmodel.configure_backup(enabled, interval, max_backups, path)
        self.settings_changed.emit()

    def _on_browse_backup_path(self) -> None:
        """Handle browse backup path button."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Backup Directory",
            self._backup_path.text(),
        )
        if path:
            self._backup_path.setText(path)
            self._apply_backup_settings()

    def _on_timestamp_changed(self, _index: int) -> None:
        """Handle timestamp format change."""
        ts_format = self._timestamp_combo.currentData()
        speaker_format = self._speaker_format.text()
        if ts_format:
            self._viewmodel.configure_av_coding(ts_format, speaker_format)
            self.settings_changed.emit()

    def _on_speaker_format_changed(self, text: str) -> None:
        """Handle speaker format change."""
        self._update_speaker_preview()
        if self._viewmodel.validate_speaker_format(text):
            ts_format = self._timestamp_combo.currentData()
            if ts_format:
                self._viewmodel.configure_av_coding(ts_format, text)
                self.settings_changed.emit()

    def _update_speaker_preview(self) -> None:
        """Update the speaker format preview."""
        format_str = self._speaker_format.text()
        previews = [
            self._viewmodel.get_speaker_format_preview(format_str, i)
            for i in range(1, 4)
        ]
        self._speaker_preview.setText(", ".join(previews))

    def _on_ok(self) -> None:
        """Handle OK button click."""
        self.accept()

    # =========================================================================
    # Style Helpers
    # =========================================================================

    def _get_toggle_button_style(self) -> str:
        """Get style for toggle buttons."""
        return f"""
            QPushButton {{
                background-color: {self._colors.surface};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:checked {{
                background-color: {self._colors.primary};
                color: {self._colors.primary_foreground};
                border-color: {self._colors.primary};
            }}
            QPushButton:hover:!checked {{
                background-color: {self._colors.surface_light};
            }}
        """

    def _get_combo_style(self) -> str:
        """Get style for combo boxes."""
        return f"""
            QComboBox {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QComboBox:focus {{
                border-color: {self._colors.primary};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: {SPACING.sm}px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self._colors.surface};
                color: {self._colors.text_primary};
                selection-background-color: {self._colors.primary};
                selection-color: {self._colors.primary_foreground};
            }}
        """

    def _get_slider_style(self) -> str:
        """Get style for sliders."""
        return f"""
            QSlider::groove:horizontal {{
                background: {self._colors.surface_light};
                height: 8px;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {self._colors.primary};
                width: 16px;
                height: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: {self._colors.primary};
                border-radius: 4px;
            }}
        """

    def _get_spinbox_style(self) -> str:
        """Get style for spin boxes."""
        return f"""
            QSpinBox {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QSpinBox:focus {{
                border-color: {self._colors.primary};
            }}
        """

    def _get_input_style(self) -> str:
        """Get style for line edits."""
        return f"""
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
        """

    def _get_button_style(self) -> str:
        """Get style for secondary buttons."""
        return f"""
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
        """

    def _get_primary_button_style(self) -> str:
        """Get style for primary buttons."""
        return f"""
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
        """
