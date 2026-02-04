"""
QualCoder App Shell Template

The main application shell that provides the consistent structure
across all screens. Screens fill the toolbar and content slots.

Structure (Modern Layout - QC-047):
┌─────────────────────────────────────────────────────────┐
│ UNIFIED NAV BAR                                         │
│ QUALCODER  │ Project │ Files │ Coding │ Reports │ AI   │
├─────────────────────────────────────────────────────────┤
│ TOOLBAR                                    ← slot       │
│ [context-specific buttons and actions]                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ MAIN CONTENT                               ← slot       │
│ (screen-specific content goes here)                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
"""

from typing import Protocol, runtime_checkable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from design_system import (
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    ColorPalette,
    Icon,
    TitleBar,
    get_colors,
    set_theme,
)

# QualCoder navigation items (unified nav bar - QC-047.01)
NAV_ITEMS = [
    ("project", "Project"),
    ("files", "Files"),
    ("coding", "Coding"),
    ("reports", "Reports"),
    ("ai", "AI"),
]

# Legacy constants for backwards compatibility with tests
MENU_ITEMS = [
    ("project", "Project"),
    ("files", "Files"),
    ("coding", "Coding"),
    ("reports", "Reports"),
    ("ai", "AI"),
]

TAB_ITEMS = [
    ("coding", "Coding", "mdi6.code-tags"),
    ("reports", "Reports", "mdi6.chart-box"),
]


@runtime_checkable
class ScreenProtocol(Protocol):
    """Protocol that screens must implement to work with AppShell"""

    def get_toolbar_content(self) -> QWidget | None:
        """Return widget(s) for the toolbar slot, or None for empty toolbar"""
        ...

    def get_content(self) -> QWidget:
        """Return the main content widget"""
        ...

    def get_status_message(self) -> str:
        """Return status bar message for this screen"""
        ...


class ToolbarSlot(QFrame):
    """
    Container for screen-provided toolbar content.
    Shows empty space when no content is set.
    """

    def __init__(self, colors: ColorPalette, parent=None):
        super().__init__(parent)
        self._colors = colors
        self._content = None

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(SPACING.lg, SPACING.sm, SPACING.lg, SPACING.sm)
        self._layout.setSpacing(SPACING.sm)

        # Default empty state - just spacing
        self.setMinimumHeight(52)

    def set_content(self, widget: QWidget | None):
        """Set toolbar content from screen"""
        # Clear existing
        if self._content:
            self._layout.removeWidget(self._content)
            self._content.setParent(None)
            self._content = None

        # Clear any remaining items
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        if widget:
            self._content = widget
            self._layout.addWidget(widget)

    def clear(self):
        """Clear toolbar content"""
        self.set_content(None)


class ContentSlot(QWidget):
    """
    Container for screen-provided main content.
    Expands to fill available space.
    """

    def __init__(self, colors: ColorPalette, parent=None):
        super().__init__(parent)
        self._colors = colors
        self._content = None

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self._colors.background};
            }}
        """)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_content(self, widget: QWidget):
        """Set main content from screen"""
        # Clear existing
        if self._content:
            self._layout.removeWidget(self._content)
            self._content.setParent(None)
            self._content = None

        # Clear any remaining items
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        self._content = widget
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._layout.addWidget(widget)

    def clear(self):
        """Clear content"""
        if self._content:
            self._layout.removeWidget(self._content)
            self._content.setParent(None)
            self._content = None


class UnifiedNavBar(QFrame):
    """
    Unified navigation bar combining logo and navigation items (QC-047.01).

    Structure:
    ┌─────────────────────────────────────────────────────────────────┐
    │ QUALCODER  │ Project │ Files │ Coding │ Reports │ AI   [⚙]    │
    └─────────────────────────────────────────────────────────────────┘
    """

    navigation_clicked = Signal(str)  # nav_id: project, files, coding, etc.
    settings_clicked = Signal()

    def __init__(self, colors: ColorPalette, parent=None):
        super().__init__(parent)
        self._colors = colors
        self._buttons = {}
        self._active_id = None

        self.setFixedHeight(48)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, 0, SPACING.lg, 0)
        layout.setSpacing(0)

        # Logo section
        logo_label = QLabel("QUALCODER")
        logo_label.setStyleSheet(f"""
            QLabel {{
                color: {self._colors.text_primary};
                font-size: {TYPOGRAPHY.text_lg}px;
                font-weight: {TYPOGRAPHY.weight_bold};
                padding-right: {SPACING.xl}px;
            }}
        """)
        layout.addWidget(logo_label)

        # Navigation items
        for nav_id, label in NAV_ITEMS:
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked, nid=nav_id: self._on_click(nid))
            self._buttons[nav_id] = btn
            layout.addWidget(btn)
            self._style_button(btn, False)

        layout.addStretch()

        # Settings button (gear icon)
        self._settings_btn = QPushButton()
        self._settings_btn.setObjectName("settings_button")
        self._settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._settings_btn.setToolTip("Settings")
        self._settings_btn.clicked.connect(self.settings_clicked.emit)
        self._settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)
        settings_icon = Icon(
            "mdi6.cog",
            size=18,
            color=self._colors.text_secondary,
            colors=self._colors,
        )
        icon_layout = QHBoxLayout(self._settings_btn)
        icon_layout.setContentsMargins(SPACING.xs, SPACING.xs, SPACING.xs, SPACING.xs)
        icon_layout.addWidget(settings_icon)
        layout.addWidget(self._settings_btn)

    def _on_click(self, nav_id: str):
        self.set_active(nav_id)
        self.navigation_clicked.emit(nav_id)

    def set_active(self, nav_id: str):
        """Set active navigation item"""
        # Deactivate previous
        if self._active_id and self._active_id in self._buttons:
            self._style_button(self._buttons[self._active_id], False)

        # Activate new
        self._active_id = nav_id
        if nav_id in self._buttons:
            self._style_button(self._buttons[nav_id], True)

    def _style_button(self, btn: QPushButton, active: bool):
        if active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._colors.primary};
                    color: {self._colors.primary_foreground};
                    border: none;
                    border-radius: {RADIUS.md}px;
                    padding: {SPACING.sm}px {SPACING.lg}px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                    margin: 0 {SPACING.xs}px;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.text_secondary};
                    border: none;
                    border-radius: {RADIUS.md}px;
                    padding: {SPACING.sm}px {SPACING.lg}px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                    margin: 0 {SPACING.xs}px;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.surface_light};
                    color: {self._colors.text_primary};
                }}
            """)


class AppMenuBar(QFrame):
    """
    QualCoder-specific menu bar with predefined menu items.
    Emits signals when menu items are clicked.
    """

    item_clicked = Signal(str)  # menu_id
    settings_clicked = Signal()  # settings button clicked

    def __init__(self, colors: ColorPalette, parent=None):
        super().__init__(parent)
        self._colors = colors
        self._buttons = {}
        self._active_id = None

        self.setFixedHeight(40)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, 0, SPACING.sm, 0)
        layout.setSpacing(SPACING.xs)

        # Add menu items
        for menu_id, label in MENU_ITEMS:
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked, mid=menu_id: self._on_click(mid))
            self._buttons[menu_id] = btn
            layout.addWidget(btn)
            self._style_button(btn, False)

        layout.addStretch()

        # Settings button (gear icon) on the right
        self._settings_btn = QPushButton()
        self._settings_btn.setObjectName("settings_button")
        self._settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._settings_btn.setToolTip("Settings")
        self._settings_btn.clicked.connect(self.settings_clicked.emit)
        self._settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)
        # Add gear icon
        settings_icon = Icon(
            "mdi6.cog",
            size=18,
            color=self._colors.text_secondary,
            colors=self._colors,
        )
        icon_layout = QHBoxLayout(self._settings_btn)
        icon_layout.setContentsMargins(SPACING.xs, SPACING.xs, SPACING.xs, SPACING.xs)
        icon_layout.addWidget(settings_icon)
        layout.addWidget(self._settings_btn)

    def _on_click(self, menu_id: str):
        self.set_active(menu_id)
        self.item_clicked.emit(menu_id)

    def set_active(self, menu_id: str):
        """Set active menu item"""
        # Deactivate previous
        if self._active_id and self._active_id in self._buttons:
            self._style_button(self._buttons[self._active_id], False)

        # Activate new
        self._active_id = menu_id
        if menu_id in self._buttons:
            self._style_button(self._buttons[menu_id], True)

    def _style_button(self, btn: QPushButton, active: bool):
        if active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.primary};
                    border: none;
                    border-radius: {RADIUS.xs}px;
                    padding: {SPACING.sm}px {SPACING.lg}px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.text_secondary};
                    border: none;
                    border-radius: {RADIUS.xs}px;
                    padding: {SPACING.sm}px {SPACING.lg}px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.surface_light};
                    color: {self._colors.text_primary};
                }}
            """)


class TabButton(QFrame):
    """
    Custom tab button with icon and label.
    """

    clicked = Signal()

    def __init__(self, label: str, icon_name: str, colors: ColorPalette, parent=None):
        super().__init__(parent)
        self._colors = colors
        self._label_text = label
        self._icon_name = icon_name
        self._active = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, 0, SPACING.xl, 0)
        layout.setSpacing(SPACING.sm)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Icon
        self._icon = Icon(
            icon_name, size=16, color=colors.text_secondary, colors=colors
        )
        layout.addWidget(self._icon, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Label
        self._label = QLabel(label)
        layout.addWidget(self._label, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._apply_style()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def set_active(self, active: bool):
        self._active = active
        self._apply_style()

    def _apply_style(self):
        if self._active:
            self._icon.set_color(self._colors.primary)
            self._label.setStyleSheet(f"""
                QLabel {{
                    color: {self._colors.primary};
                    font-size: {TYPOGRAPHY.text_sm}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                }}
            """)
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: transparent;
                    border: none;
                    border-bottom: 2px solid {self._colors.primary};
                    min-height: 42px;
                }}
            """)
        else:
            self._icon.set_color(self._colors.text_secondary)
            self._label.setStyleSheet(f"""
                QLabel {{
                    color: {self._colors.text_secondary};
                    font-size: {TYPOGRAPHY.text_sm}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                }}
            """)
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: transparent;
                    border: none;
                    border-bottom: 2px solid transparent;
                    min-height: 42px;
                }}
                QFrame:hover {{
                    background-color: {self._colors.surface_light};
                }}
            """)


class AppTabBar(QFrame):
    """
    QualCoder-specific tab bar with predefined tabs and icons.
    """

    tab_clicked = Signal(str)  # tab_id

    def __init__(self, colors: ColorPalette, parent=None):
        super().__init__(parent)
        self._colors = colors
        self._tabs = {}
        self._active_id = None

        self.setFixedHeight(44)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, 0, SPACING.lg, 0)
        layout.setSpacing(0)

        # Add tabs with icons
        for tab_id, label, icon_name in TAB_ITEMS:
            tab = TabButton(label, icon_name, colors=self._colors)
            tab.clicked.connect(lambda tid=tab_id: self._on_click(tid))
            self._tabs[tab_id] = tab
            layout.addWidget(tab)

        layout.addStretch()

    def _on_click(self, tab_id: str):
        self.set_active(tab_id)
        self.tab_clicked.emit(tab_id)

    def set_active(self, tab_id: str):
        """Set active tab"""
        # Deactivate previous
        if self._active_id and self._active_id in self._tabs:
            self._tabs[self._active_id].set_active(False)

        # Activate new
        self._active_id = tab_id
        if tab_id in self._tabs:
            self._tabs[tab_id].set_active(True)

    # Keep _buttons for backwards compatibility with tests
    @property
    def _buttons(self):
        return self._tabs


class AppStatusBar(QFrame):
    """
    QualCoder-specific status bar.
    """

    def __init__(self, colors: ColorPalette, parent=None):
        super().__init__(parent)
        self._colors = colors

        self.setFixedHeight(32)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.primary_dark};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, 0, SPACING.lg, 0)
        layout.setSpacing(SPACING.lg)

        # Left side - main message
        self._message_label = QLabel("Ready")
        self._message_label.setStyleSheet(f"""
            color: {self._colors.text_on_dark};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        layout.addWidget(self._message_label)

        layout.addStretch()

        # Right side - stats
        self._right_layout = QHBoxLayout()
        self._right_layout.setSpacing(SPACING.lg)
        layout.addLayout(self._right_layout)

        # Default stats
        self._stats = {}
        self.add_stat("files", "0 files")
        self.add_stat("codes", "0 codes")

    def set_message(self, message: str):
        """Set main status message"""
        self._message_label.setText(message)

    def add_stat(self, key: str, text: str):
        """Add a stat item to the right side"""
        label = QLabel(text)
        label.setStyleSheet(f"""
            color: rgba(255, 255, 255, 0.8);
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        self._stats[key] = label
        self._right_layout.addWidget(label)

    def set_stat(self, key: str, text: str):
        """Update a stat item"""
        if key in self._stats:
            self._stats[key].setText(text)


class AppShell(QMainWindow):
    """
    Main QualCoder application shell (QC-047.01 Modern Layout).

    This is the fixed template that all screens plug into.
    It provides:
    - Unified navigation bar (QUALCODER | Project | Files | Coding | Reports | AI)
    - Toolbar slot (filled by screens)
    - Content slot (filled by screens)

    Usage:
        shell = AppShell(colors=get_colors())
        shell.set_project("my_project.qda")

        # Set a screen
        shell.set_screen(my_screen)  # screen must implement ScreenProtocol

        # Or manually set slots
        shell.set_toolbar_content(toolbar_widget)
        shell.set_content(content_widget)
    """

    # Navigation signals
    navigation_clicked = Signal(str)  # nav_id: project, files, coding, etc.
    menu_clicked = Signal(str)  # Legacy alias for navigation_clicked
    settings_clicked = Signal()  # settings button clicked

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._current_screen = None
        self._project_name = "Untitled"

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self.setWindowTitle("QualCoder")
        self.setMinimumSize(1200, 800)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Unified navigation bar (QC-047.01)
        self._nav_bar = UnifiedNavBar(colors=self._colors)
        layout.addWidget(self._nav_bar)

        # Legacy references for backwards compatibility
        self._menu_bar = self._nav_bar  # Tests may reference _menu_bar
        self._tab_bar = self._nav_bar  # Tests may reference _tab_bar

        # Toolbar slot
        self._toolbar_slot = ToolbarSlot(colors=self._colors)
        layout.addWidget(self._toolbar_slot)

        # Content slot (expands)
        self._content_slot = ContentSlot(colors=self._colors)
        layout.addWidget(self._content_slot, 1)

        # Apply background
        central.setStyleSheet(f"""
            QWidget {{
                background-color: {self._colors.background};
            }}
        """)

    def _connect_signals(self):
        # Connect unified nav bar signals (QC-047.01)
        self._nav_bar.navigation_clicked.connect(self.navigation_clicked.emit)
        self._nav_bar.navigation_clicked.connect(self.menu_clicked.emit)  # Legacy
        self._nav_bar.settings_clicked.connect(self.settings_clicked.emit)

    # --- Public API ---

    def set_project(self, name: str):
        """Set project name in title bar"""
        self._project_name = name
        # Update title bar - need to recreate or update the label
        self.setWindowTitle(f"QualCoder - {name}")

    def set_screen(self, screen: ScreenProtocol):
        """
        Set the current screen.

        The screen must implement:
        - get_toolbar_content() -> Optional[QWidget]
        - get_content() -> QWidget
        - get_status_message() -> str
        """
        self._current_screen = screen

        # Set toolbar content
        toolbar_content = screen.get_toolbar_content()
        self._toolbar_slot.set_content(toolbar_content)

        # Set main content
        content = screen.get_content()
        self._content_slot.set_content(content)

        # Set status message
        message = screen.get_status_message()
        self._status_bar.set_message(message)

    def set_toolbar_content(self, widget: QWidget | None):
        """Directly set toolbar content"""
        self._toolbar_slot.set_content(widget)

    def set_content(self, widget: QWidget):
        """Directly set main content"""
        self._content_slot.set_content(widget)

    def set_status_message(self, message: str):
        """Set status bar message (no-op in modern layout)"""
        pass  # Status bar removed in QC-047.01

    def set_status_stat(self, key: str, value: str):
        """Set a status bar stat (no-op in modern layout)"""
        pass  # Status bar removed in QC-047.01

    def set_active_navigation(self, nav_id: str):
        """Set active navigation item (QC-047.01)"""
        self._nav_bar.set_active(nav_id)

    def set_active_menu(self, menu_id: str):
        """Set active menu item (legacy - maps to navigation)"""
        self._nav_bar.set_active(menu_id)

    def set_active_tab(self, tab_id: str):
        """Set active tab (legacy - maps to navigation)"""
        self._nav_bar.set_active(tab_id)

    # --- Settings Application ---

    def apply_theme(self, theme_name: str) -> None:
        """
        Apply theme to the entire application UI.

        This changes the design system's global theme and refreshes
        all widgets to use the new color palette.

        Args:
            theme_name: Theme name ('light' or 'dark')
        """
        # Update global design system theme
        set_theme(theme_name)

        # Get new colors
        self._colors = get_colors()

        # Rebuild UI with new colors
        self._refresh_ui()

    def apply_font(self, family: str, size: int) -> None:
        """
        Apply font settings to the application.

        Args:
            family: Font family name
            size: Font size in pixels
        """
        from PySide6.QtGui import QFont
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app:
            font = QFont(family, size)
            app.setFont(font)

    def load_and_apply_settings(self, settings_repo) -> None:
        """
        Load settings from repository and apply to UI.

        This should be called at application startup to restore
        saved user preferences.

        Args:
            settings_repo: UserSettingsRepository instance
        """
        self._settings_repo = settings_repo
        settings = settings_repo.load()

        # Apply theme (only if not system - system theme handled separately)
        if settings.theme.name in ("light", "dark"):
            self.apply_theme(settings.theme.name)

        # Apply font
        self.apply_font(settings.font.family, settings.font.size)

    def open_settings_dialog(self, colors: ColorPalette | None = None) -> None:
        """
        Open the settings dialog and wire up live UI updates.

        This method:
        1. Creates the SettingsDialog with proper viewmodel
        2. Connects settings_changed signal to apply theme/font changes live
        3. Shows the dialog modally

        Args:
            colors: Optional color palette for dialog theming
        """
        from src.contexts.settings.presentation import SettingsViewModel
        from src.contexts.settings.presentation.dialogs import SettingsDialog
        from src.shared.presentation.services.settings_service import SettingsService

        # Use stored settings repo or create default
        if not hasattr(self, "_settings_repo") or self._settings_repo is None:
            from src.contexts.settings.infra import UserSettingsRepository

            self._settings_repo = UserSettingsRepository()

        settings_service = SettingsService(self._settings_repo)
        viewmodel = SettingsViewModel(settings_provider=settings_service)

        dialog = SettingsDialog(
            viewmodel=viewmodel,
            colors=colors or self._colors,
            parent=self,
        )

        # Wire up live UI updates when settings change
        def on_settings_changed():
            settings = self._settings_repo.load()
            # Apply theme if changed
            if (
                settings.theme.name in ("light", "dark")
                and settings.theme.name != self._get_current_theme()
            ):
                self.apply_theme(settings.theme.name)
            # Apply font
            self.apply_font(settings.font.family, settings.font.size)

        dialog.settings_changed.connect(on_settings_changed)
        dialog.exec()

    def _get_current_theme(self) -> str:
        """Get current theme name from design system."""
        from design_system.tokens import _current_theme

        return _current_theme

    def _refresh_ui(self) -> None:
        """Refresh all UI components with current colors."""
        # Save current state
        current_screen = self._current_screen
        current_nav_id = (
            self._nav_bar._active_id if hasattr(self, "_nav_bar") else None
        )

        # Rebuild components with new colors
        central = self.centralWidget()

        # Remove old layout
        old_layout = central.layout()
        if old_layout:
            # Clear all widgets
            while old_layout.count():
                item = old_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        # Rebuild UI and reconnect signals
        self._setup_ui()
        self._connect_signals()

        # Restore current screen and navigation state
        if current_screen is not None:
            self.set_screen(current_screen)
        if current_nav_id:
            self._nav_bar.set_active(current_nav_id)

    # --- Accessors ---

    @property
    def toolbar_slot(self) -> ToolbarSlot:
        return self._toolbar_slot

    @property
    def content_slot(self) -> ContentSlot:
        return self._content_slot

    @property
    def nav_bar(self) -> UnifiedNavBar:
        """Get the unified navigation bar (QC-047.01)"""
        return self._nav_bar

    @property
    def menu_bar(self) -> UnifiedNavBar:
        """Legacy accessor - returns nav_bar for compatibility"""
        return self._nav_bar

    @property
    def tab_bar(self) -> UnifiedNavBar:
        """Legacy accessor - returns nav_bar for compatibility"""
        return self._nav_bar
