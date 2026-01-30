"""
QualCoder App Shell Template

The main application shell that provides the consistent structure
across all screens. Screens fill the toolbar and content slots.

Structure:
┌─────────────────────────────────────────────────────────┐
│ TITLE BAR                                               │
│ [Q] QualCoder - project_name.qda        [─][□][×]       │
├─────────────────────────────────────────────────────────┤
│ MENU BAR                                                │
│ Project | Files and Cases | Coding | Reports | AI | Help│
├─────────────────────────────────────────────────────────┤
│ TAB BAR                                                 │
│ [Coding] [Reports] [Manage] [Action Log]                │
├─────────────────────────────────────────────────────────┤
│ TOOLBAR                                    ← slot       │
│ [context-specific buttons and actions]                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ MAIN CONTENT                               ← slot       │
│ (screen-specific content goes here)                     │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ STATUS BAR                                              │
│ Ready | 24 files | 156 codes | Last saved: 2:34 PM      │
└─────────────────────────────────────────────────────────┘
"""

from typing import Protocol, runtime_checkable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
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
    get_theme,
)

# QualCoder-specific menu items
MENU_ITEMS = [
    ("project", "Project"),
    ("files", "Files and Cases"),
    ("coding", "Coding"),
    ("reports", "Reports"),
    ("ai", "AI"),
    ("help", "Help"),
]

# QualCoder-specific tabs (using qtawesome mdi6 icon names)
TAB_ITEMS = [
    ("coding", "Coding", "mdi6.code-tags"),
    ("reports", "Reports", "mdi6.chart-box"),
    ("manage", "Manage", "mdi6.folder"),
    ("action_log", "Action Log", "mdi6.history"),
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


class AppMenuBar(QFrame):
    """
    QualCoder-specific menu bar with predefined menu items.
    Emits signals when menu items are clicked.
    """

    item_clicked = pyqtSignal(str)  # menu_id

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

    clicked = pyqtSignal()

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

    tab_clicked = pyqtSignal(str)  # tab_id

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
            color: white;
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
    Main QualCoder application shell.

    This is the fixed template that all screens plug into.
    It provides:
    - Title bar with project name
    - Menu bar (Project, Files, Coding, Reports, AI, Help)
    - Tab bar (Coding, Reports, Manage, Action Log)
    - Toolbar slot (filled by screens)
    - Content slot (filled by screens)
    - Status bar

    Usage:
        shell = AppShell(colors=get_theme("dark"))
        shell.set_project("my_project.qda")

        # Set a screen
        shell.set_screen(my_screen)  # screen must implement ScreenProtocol

        # Or manually set slots
        shell.set_toolbar_content(toolbar_widget)
        shell.set_content(content_widget)
        shell.set_status_message("Processing...")
    """

    # Navigation signals
    menu_clicked = pyqtSignal(str)  # menu_id
    tab_clicked = pyqtSignal(str)  # tab_id

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
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

        # Title bar
        self._title_bar = TitleBar(
            title=f"QualCoder - {self._project_name}",
            show_logo=True,
            show_controls=True,
            colors=self._colors,
        )
        layout.addWidget(self._title_bar)

        # Menu bar
        self._menu_bar = AppMenuBar(colors=self._colors)
        layout.addWidget(self._menu_bar)

        # Tab bar
        self._tab_bar = AppTabBar(colors=self._colors)
        layout.addWidget(self._tab_bar)

        # Toolbar slot
        self._toolbar_slot = ToolbarSlot(colors=self._colors)
        layout.addWidget(self._toolbar_slot)

        # Content slot (expands)
        self._content_slot = ContentSlot(colors=self._colors)
        layout.addWidget(self._content_slot, 1)

        # Status bar
        self._status_bar = AppStatusBar(colors=self._colors)
        layout.addWidget(self._status_bar)

        # Apply background
        central.setStyleSheet(f"""
            QWidget {{
                background-color: {self._colors.background};
            }}
        """)

    def _connect_signals(self):
        self._menu_bar.item_clicked.connect(self.menu_clicked.emit)
        self._tab_bar.tab_clicked.connect(self.tab_clicked.emit)

        # Window controls
        self._title_bar.close_clicked.connect(self.close)
        self._title_bar.minimize_clicked.connect(self.showMinimized)
        self._title_bar.maximize_clicked.connect(self._toggle_maximize)

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

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
        """Set status bar message"""
        self._status_bar.set_message(message)

    def set_status_stat(self, key: str, value: str):
        """Set a status bar stat"""
        self._status_bar.set_stat(key, value)

    def set_active_menu(self, menu_id: str):
        """Set active menu item"""
        self._menu_bar.set_active(menu_id)

    def set_active_tab(self, tab_id: str):
        """Set active tab"""
        self._tab_bar.set_active(tab_id)

    # --- Accessors ---

    @property
    def toolbar_slot(self) -> ToolbarSlot:
        return self._toolbar_slot

    @property
    def content_slot(self) -> ContentSlot:
        return self._content_slot

    @property
    def status_bar(self) -> AppStatusBar:
        return self._status_bar

    @property
    def menu_bar(self) -> AppMenuBar:
        return self._menu_bar

    @property
    def tab_bar(self) -> AppTabBar:
        return self._tab_bar
