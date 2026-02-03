# UI Layer Implementation Plan

## Overview

Build QualCoder UI with a clear three-layer architecture that separates reusable components from app-specific templates and screens.

---

## Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   LAYER 3: SCREENS                                              │
│   Content that fills template slots                             │
│   (TextCodingContent, SettingsContent, AIChat, ...)             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   LAYER 2: TEMPLATES                                            │
│   App shell & layout patterns                                   │
│   (AppShell, SidebarLayout, ThreePanelLayout, ...)              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   LAYER 1: DESIGN SYSTEM                                        │
│   Primitive components & tokens                                 │
│   (Button, Input, Card, DataTable, CodeTree, ...)               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Location | Contains | Reusable? |
|-------|----------|----------|-----------|
| **Design System** | `design_system/` | Tokens, primitives, generic components | Yes - any PyQt6 project |
| **Templates** | `ui/templates/` | App shell, layout patterns, navigation | Partially - similar apps |
| **Screens** | `ui/screens/` | Screen content, business logic | No - QualCoder specific |

---

## Directory Structure

```
QualCoder-v2/
│
├── design_system/                    # LAYER 1: Generic components
│   ├── __init__.py
│   ├── tokens.py                     # Colors, spacing, typography
│   ├── components.py                 # Button, Input, Card, Badge
│   ├── layout.py                     # Panel, Sidebar, Splitter
│   ├── forms.py                      # SearchBox, Select, FormGroup
│   ├── data_display.py               # DataTable, KeyValueList
│   ├── code_tree.py                  # CodeTree, CodeItem
│   ├── document.py                   # TextPanel, TranscriptPanel
│   ├── media.py                      # VideoContainer, Timeline
│   ├── chat.py                       # MessageBubble, ChatInput
│   ├── ... (other modules)
│   └── storybook/                    # Component documentation
│
├── ui/                               # LAYER 2 & 3: App-specific
│   ├── __init__.py
│   │
│   ├── templates/                    # LAYER 2: App shell & layouts
│   │   ├── __init__.py
│   │   ├── app_shell.py              # Main app container
│   │   ├── title_bar.py              # Window title bar
│   │   ├── menu_bar.py               # Main menu navigation
│   │   ├── tab_bar.py                # Quick access tabs
│   │   ├── toolbar.py                # Toolbar container
│   │   ├── status_bar.py             # Status bar
│   │   └── layouts/                  # Content area layouts
│   │       ├── __init__.py
│   │       ├── single_panel.py       # Full-width content
│   │       ├── sidebar_layout.py     # Sidebar + main content
│   │       ├── three_panel.py        # Left + center + right
│   │       └── split_layout.py       # Resizable split panels
│   │
│   ├── screens/                      # LAYER 3: Screen content
│   │   ├── __init__.py
│   │   ├── coding/
│   │   │   ├── __init__.py
│   │   │   ├── text.py               # Text coding content
│   │   │   ├── image.py              # Image coding content
│   │   │   ├── audio_video.py        # A/V coding content
│   │   │   └── pdf.py                # PDF coding content
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py
│   │   │   └── search.py
│   │   ├── manage/
│   │   │   ├── __init__.py
│   │   │   ├── files.py
│   │   │   ├── cases.py
│   │   │   ├── journals.py
│   │   │   └── attributes.py
│   │   ├── reports/
│   │   │   ├── __init__.py
│   │   │   ├── coding.py
│   │   │   ├── charts.py
│   │   │   ├── comparison.py
│   │   │   ├── text_mining.py
│   │   │   └── graph.py
│   │   └── settings/
│   │       ├── __init__.py
│   │       ├── settings.py
│   │       └── sql_query.py
│   │
│   ├── mock_data/                    # Test data for standalone dev
│   │   ├── __init__.py
│   │   ├── files.py
│   │   ├── codes.py
│   │   ├── cases.py
│   │   ├── documents.py
│   │   └── chat.py
│   │
│   └── storybook/                    # Screen preview app
│       ├── __init__.py
│       ├── app.py
│       └── stories/
```

---

## Layer 2: Templates

### App Shell Structure

Every QualCoder screen uses the same shell:

```
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
```

### AppShell Implementation

```python
# ui/templates/app_shell.py
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal

from design_system import ColorPalette, get_theme

from .title_bar import TitleBar
from .menu_bar import AppMenuBar
from .tab_bar import AppTabBar
from .toolbar import ToolbarContainer
from .status_bar import AppStatusBar


class AppShell(QMainWindow):
    """
    Main application shell - the fixed template for all screens.

    Provides:
    - Title bar with project name
    - Menu bar navigation
    - Tab bar for quick access
    - Toolbar slot (filled by screens)
    - Content slot (filled by screens)
    - Status bar
    """

    # Navigation signals
    menu_selected = pyqtSignal(str)      # "project", "files", "coding", etc.
    tab_selected = pyqtSignal(str)       # "coding", "reports", "manage", etc.

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._current_screen = None
        self._setup_ui()

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
        self.title_bar = TitleBar(colors=self._colors)
        layout.addWidget(self.title_bar)

        # Menu bar
        self.menu_bar = AppMenuBar(colors=self._colors)
        self.menu_bar.item_clicked.connect(self.menu_selected.emit)
        layout.addWidget(self.menu_bar)

        # Tab bar
        self.tab_bar = AppTabBar(colors=self._colors)
        self.tab_bar.tab_clicked.connect(self.tab_selected.emit)
        layout.addWidget(self.tab_bar)

        # Toolbar (slot - filled by screens)
        self.toolbar = ToolbarContainer(colors=self._colors)
        layout.addWidget(self.toolbar)

        # Content area (slot - filled by screens)
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.content_area, 1)  # stretch

        # Status bar
        self.status_bar = AppStatusBar(colors=self._colors)
        layout.addWidget(self.status_bar)

    def set_project(self, name: str):
        """Update title bar with project name"""
        self.title_bar.set_project(name)

    def set_screen(self, screen: 'BaseScreen'):
        """
        Set the current screen content.

        The screen provides:
        - toolbar_content(): widgets for the toolbar
        - content(): the main content widget
        """
        # Clear current
        if self._current_screen:
            self._current_screen.setParent(None)

        self._current_screen = screen

        # Set toolbar content
        self.toolbar.set_content(screen.toolbar_content())

        # Set main content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

        self.content_layout.addWidget(screen.content())

        # Update status bar
        self.status_bar.set_message(screen.status_message())

    def set_active_menu(self, menu_id: str):
        """Highlight active menu item"""
        self.menu_bar.set_active(menu_id)

    def set_active_tab(self, tab_id: str):
        """Highlight active tab"""
        self.tab_bar.set_active(tab_id)
```

### Menu Bar

```python
# ui/templates/menu_bar.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal

from design_system import ColorPalette


class AppMenuBar(QWidget):
    """Main menu navigation bar"""

    item_clicked = pyqtSignal(str)

    MENU_ITEMS = [
        ("project", "Project"),
        ("files", "Files and Cases"),
        ("coding", "Coding"),
        ("reports", "Reports"),
        ("ai", "AI"),
        ("help", "Help"),
    ]

    def __init__(self, colors: ColorPalette, parent=None):
        super().__init__(parent)
        self._colors = colors
        self._buttons = {}
        self._active = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(0)

        for menu_id, label in self.MENU_ITEMS:
            btn = QPushButton(label)
            btn.setProperty("menuItem", True)
            btn.clicked.connect(lambda checked, mid=menu_id: self._on_click(mid))
            self._buttons[menu_id] = btn
            layout.addWidget(btn)

        layout.addStretch()
        self._apply_style()

    def set_active(self, menu_id: str):
        """Set active menu item"""
        if self._active:
            self._buttons[self._active].setProperty("active", False)
        self._active = menu_id
        if menu_id in self._buttons:
            self._buttons[menu_id].setProperty("active", True)
        self._apply_style()

    def _on_click(self, menu_id: str):
        self.set_active(menu_id)
        self.item_clicked.emit(menu_id)

    def _apply_style(self):
        # ... styling code
        pass
```

### Content Layouts

```python
# ui/templates/layouts/sidebar_layout.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSplitter
from PyQt6.QtCore import Qt

from design_system import ColorPalette


class SidebarLayout(QWidget):
    """
    Layout with sidebar + main content.

    ┌──────────┬────────────────────────┐
    │          │                        │
    │ SIDEBAR  │     MAIN CONTENT       │
    │          │                        │
    └──────────┴────────────────────────┘
    """

    def __init__(self, colors: ColorPalette, parent=None):
        super().__init__(parent)
        self._colors = colors
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Sidebar container
        self.sidebar = QWidget()
        self.sidebar.setMinimumWidth(200)
        self.sidebar.setMaximumWidth(400)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(0, 0, 0, 0)
        self.splitter.addWidget(self.sidebar)

        # Main content container
        self.main_content = QWidget()
        self.main_layout = QVBoxLayout(self.main_content)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.splitter.addWidget(self.main_content)

        self.splitter.setSizes([280, 920])
        layout.addWidget(self.splitter)

    def set_sidebar(self, widget: QWidget):
        """Set sidebar content"""
        self._clear_layout(self.sidebar_layout)
        self.sidebar_layout.addWidget(widget)

    def set_content(self, widget: QWidget):
        """Set main content"""
        self._clear_layout(self.main_layout)
        self.main_layout.addWidget(widget)

    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)


# ui/templates/layouts/three_panel.py
class ThreePanelLayout(QWidget):
    """
    Layout with left sidebar + center + right panel.

    ┌──────────┬──────────────┬──────────┐
    │          │              │          │
    │   LEFT   │    CENTER    │  RIGHT   │
    │          │              │          │
    └──────────┴──────────────┴──────────┘
    """

    def __init__(self, colors: ColorPalette, parent=None):
        super().__init__(parent)
        self._colors = colors
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel
        self.left_panel = QWidget()
        self.left_panel.setMinimumWidth(200)
        self.left_panel.setMaximumWidth(350)
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.splitter.addWidget(self.left_panel)

        # Center panel
        self.center_panel = QWidget()
        self.center_layout = QVBoxLayout(self.center_panel)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.splitter.addWidget(self.center_panel)

        # Right panel
        self.right_panel = QWidget()
        self.right_panel.setMinimumWidth(200)
        self.right_panel.setMaximumWidth(350)
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.splitter.addWidget(self.right_panel)

        self.splitter.setSizes([280, 640, 280])
        layout.addWidget(self.splitter)

    def set_left(self, widget: QWidget):
        self._clear_layout(self.left_layout)
        self.left_layout.addWidget(widget)

    def set_center(self, widget: QWidget):
        self._clear_layout(self.center_layout)
        self.center_layout.addWidget(widget)

    def set_right(self, widget: QWidget):
        self._clear_layout(self.right_layout)
        self.right_layout.addWidget(widget)
```

---

## Layer 3: Screens

### Base Screen Class

```python
# ui/screens/base.py
from abc import ABC, abstractmethod
from PyQt6.QtWidgets import QWidget

from design_system import ColorPalette, get_theme


class BaseScreen(ABC):
    """
    Base class for all screen content.

    Screens don't include the app shell - they provide:
    - toolbar_content(): widgets for the toolbar slot
    - content(): the main content widget
    - status_message(): text for status bar
    """

    def __init__(self, colors: ColorPalette = None):
        self._colors = colors or get_theme("dark")
        self._data_provider = None
        self._toolbar_widget = None
        self._content_widget = None
        self._build()

    @abstractmethod
    def _build(self):
        """Build the screen's toolbar and content widgets"""
        pass

    @abstractmethod
    def _build_toolbar(self) -> QWidget:
        """Create toolbar content for this screen"""
        pass

    @abstractmethod
    def _build_content(self) -> QWidget:
        """Create main content for this screen"""
        pass

    def toolbar_content(self) -> QWidget:
        """Get toolbar widget"""
        if not self._toolbar_widget:
            self._toolbar_widget = self._build_toolbar()
        return self._toolbar_widget

    def content(self) -> QWidget:
        """Get content widget"""
        if not self._content_widget:
            self._content_widget = self._build_content()
        return self._content_widget

    def status_message(self) -> str:
        """Status bar message"""
        return "Ready"

    def set_data_provider(self, provider):
        """Inject data provider for real data"""
        self._data_provider = provider
        self._refresh_data()

    def _refresh_data(self):
        """Override to reload data from provider"""
        pass
```

### Example Screen: Text Coding

```python
# ui/screens/coding/text.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout

from design_system import ColorPalette
from design_system.components import Button
from design_system.code_tree import CodeTree
from design_system.document import TextPanel, SelectionPopup
from design_system.data_display import KeyValueList

from ..base import BaseScreen
from ...templates.layouts import ThreePanelLayout
from ...mock_data import get_mock_codes, get_mock_document


class TextCodingScreen(BaseScreen):
    """Text coding screen content"""

    def _build(self):
        self._codes = []
        self._document = None
        self._load_data()

    def _build_toolbar(self) -> QWidget:
        """Build toolbar with coding actions"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(8, 4, 8, 4)

        # File selection dropdown would go here
        layout.addWidget(Button("Open File", icon="folder_open", colors=self._colors))
        layout.addWidget(Button("Save", icon="save", colors=self._colors))

        layout.addStretch()

        layout.addWidget(Button("Undo", icon="undo", variant="ghost", colors=self._colors))
        layout.addWidget(Button("Redo", icon="redo", variant="ghost", colors=self._colors))

        return toolbar

    def _build_content(self) -> QWidget:
        """Build three-panel coding layout"""
        layout = ThreePanelLayout(colors=self._colors)

        # Left: Code tree
        self.code_tree = CodeTree(colors=self._colors)
        self.code_tree.set_codes(self._codes)
        layout.set_left(self.code_tree)

        # Center: Document text
        self.text_panel = TextPanel(colors=self._colors)
        self.text_panel.set_content(self._document)
        layout.set_center(self.text_panel)

        # Right: Code details
        self.details_panel = self._build_details_panel()
        layout.set_right(self.details_panel)

        return layout

    def _build_details_panel(self) -> QWidget:
        """Build right panel with code details"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Code info
        self.code_info = KeyValueList(colors=self._colors)
        self.code_info.add_item("Selected Code", "None")
        self.code_info.add_item("Color", "-")
        self.code_info.add_item("Frequency", "0")
        layout.addWidget(self.code_info)

        layout.addStretch()
        return panel

    def _load_data(self):
        """Load mock or real data"""
        if self._data_provider:
            self._codes = self._data_provider.get_codes()
            self._document = self._data_provider.get_document()
        else:
            self._codes = get_mock_codes()
            self._document = get_mock_document()

    def status_message(self) -> str:
        doc_name = self._document.get("name", "No document") if self._document else "No document"
        code_count = len(self._codes)
        return f"{doc_name} | {code_count} codes"
```

### Example Screen: Settings

```python
# ui/screens/settings/settings.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout

from design_system import ColorPalette
from design_system.components import Button
from design_system.navigation import NavList
from design_system.forms import Select, Toggle, FormGroup

from ..base import BaseScreen
from ...templates.layouts import SidebarLayout


class SettingsScreen(BaseScreen):
    """Settings screen content"""

    SECTIONS = [
        ("general", "General", "tune"),
        ("appearance", "Appearance", "palette"),
        ("fonts", "Fonts", "text_fields"),
        ("shortcuts", "Shortcuts", "keyboard"),
        ("backup", "Backup", "backup"),
        ("ai", "AI Settings", "smart_toy"),
        ("advanced", "Advanced", "code"),
    ]

    def _build(self):
        self._current_section = "general"

    def _build_toolbar(self) -> QWidget:
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(8, 4, 8, 4)

        layout.addStretch()
        layout.addWidget(Button("Reset to Defaults", variant="secondary", colors=self._colors))
        layout.addWidget(Button("Save Changes", variant="primary", colors=self._colors))

        return toolbar

    def _build_content(self) -> QWidget:
        layout = SidebarLayout(colors=self._colors)

        # Left: Settings navigation
        self.nav = NavList(colors=self._colors)
        for section_id, label, icon in self.SECTIONS:
            self.nav.add_item(section_id, label, icon)
        self.nav.set_active("general")
        self.nav.item_clicked.connect(self._on_section_change)
        layout.set_sidebar(self.nav)

        # Right: Settings content
        self.settings_content = self._build_general_section()
        layout.set_content(self.settings_content)

        return layout

    def _build_general_section(self) -> QWidget:
        """Build general settings form"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)

        # Language
        lang_group = FormGroup("Language & Region", colors=self._colors)
        lang_group.add_row(
            "Interface Language",
            Select(options=["English", "German", "Spanish", "French"], colors=self._colors),
            description="Choose the language for menus and interface"
        )
        lang_group.add_row(
            "Date Format",
            Select(options=["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"], colors=self._colors),
        )
        layout.addWidget(lang_group)

        # Behavior
        behavior_group = FormGroup("Behavior", colors=self._colors)
        behavior_group.add_row(
            "Auto-save",
            Toggle(checked=True, colors=self._colors),
            description="Automatically save changes"
        )
        behavior_group.add_row(
            "Confirm deletions",
            Toggle(checked=True, colors=self._colors),
        )
        layout.addWidget(behavior_group)

        layout.addStretch()
        return panel

    def _on_section_change(self, section_id: str):
        self._current_section = section_id
        # Would rebuild content for selected section

    def status_message(self) -> str:
        return "Settings"
```

---

## How It All Connects

### Running a Screen

```python
# main.py
from PyQt6.QtWidgets import QApplication
import sys

from design_system import get_theme
from ui.templates.app_shell import AppShell
from ui.screens.coding.text import TextCodingScreen


def main():
    app = QApplication(sys.argv)

    colors = get_theme("dark")

    # Create app shell (template)
    shell = AppShell(colors=colors)
    shell.set_project("research_project.qda")

    # Create screen content
    screen = TextCodingScreen(colors=colors)

    # Insert screen into shell
    shell.set_screen(screen)
    shell.set_active_menu("coding")
    shell.set_active_tab("coding")

    shell.show()
    sys.exit(app.exec())
```

### Screen Navigation

```python
# In AppShell or a router
class AppShell(QMainWindow):

    def __init__(self, ...):
        # ...
        self.menu_selected.connect(self._handle_navigation)

    def _handle_navigation(self, menu_id: str):
        """Navigate to different screen based on menu selection"""
        screen_map = {
            "coding": lambda: TextCodingScreen(self._colors),
            "files": lambda: FileManagerScreen(self._colors),
            "reports": lambda: CodingReportsScreen(self._colors),
            "settings": lambda: SettingsScreen(self._colors),
            # ...
        }

        creator = screen_map.get(menu_id)
        if creator:
            screen = creator()
            self.set_screen(screen)
            self.set_active_menu(menu_id)
```

---

## Visual Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                         AppShell                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ TitleBar (design_system/layout.py)                        │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │ AppMenuBar (ui/templates/menu_bar.py)                     │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │ AppTabBar (ui/templates/tab_bar.py)                       │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │ ToolbarContainer ← screen.toolbar_content()               │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │           screen.content()                          │  │  │
│  │  │  ┌─────────┬─────────────────────┬─────────┐        │  │  │
│  │  │  │CodeTree │    TextPanel        │ Details │        │  │  │
│  │  │  │(design  │    (design_system)  │ (design │        │  │  │
│  │  │  │_system) │                     │ _system)│        │  │  │
│  │  │  └─────────┴─────────────────────┴─────────┘        │  │  │
│  │  │           ThreePanelLayout                          │  │  │
│  │  │           (ui/templates/layouts)                    │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │ AppStatusBar (ui/templates/status_bar.py)                 │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Templates Foundation
1. Create `ui/templates/` structure
2. Build `AppShell` with all shell components
3. Build layout classes (`SidebarLayout`, `ThreePanelLayout`)
4. Test shell with placeholder content

### Phase 2: First Screens
1. Create `ui/screens/base.py`
2. Build `SettingsScreen` (simplest)
3. Build `FileManagerScreen` (validates layouts)
4. Test navigation between screens

### Phase 3: Mock Data & Storybook
1. Create `ui/mock_data/` module
2. Build `ui/storybook/` for screen previews
3. Add more screens progressively

### Phase 4-6: Remaining Screens
Follow priority order from previous plan.

---

## Benefits of This Architecture

1. **Clear separation**: Design system stays generic, templates handle app structure, screens handle content
2. **Consistency**: All screens share the same shell automatically
3. **Testability**: Screens can be tested in isolation with mock data
4. **Maintainability**: Change shell once, all screens update
5. **Reusability**: Templates could be reused for similar apps
6. **Gradual migration**: Can build screens one at a time

---

## Next Steps

1. **Create `ui/templates/` structure**
2. **Build `AppShell`** with shell components
3. **Build first layout** (`SidebarLayout`)
4. **Build `SettingsScreen`** to validate the pattern
5. **Set up screen storybook**

Ready to start?
