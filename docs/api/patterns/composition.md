# Composition Patterns

Building complex layouts from simple components.

## Container Composition

### Basic Card Layout

```python
from design_system import Card, CardHeader, Label, Button

card = Card()
card.add_widget(CardHeader(title="Section Title"))
card.add_widget(Label("Content goes here"))
card.add_widget(Button("Action", variant="primary"))
```

### Panel with Header

```python
from design_system import Panel, PanelHeader, FileList

panel = Panel()
panel.add_widget(PanelHeader(title="Files"))
panel.add_widget(FileList())
```

## Hierarchical Data

### Tree Structures

```python
from design_system import CodeTree, CodeItem

tree = CodeTree()
tree.set_items([
    CodeItem("1", "Parent", "#FFC107", count=10, children=[
        CodeItem("1.1", "Child A", "#FFD54F", count=5),
        CodeItem("1.2", "Child B", "#FFE082", count=5),
    ])
])
```

### Nested Layouts

```python
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout
from design_system import Panel, Card, Label

# Main horizontal layout
main_layout = QHBoxLayout()

# Left sidebar
sidebar = Panel()
sidebar.add_widget(Label("Navigation"))
main_layout.addWidget(sidebar, stretch=1)

# Right content area
content = QVBoxLayout()

# Top card
top_card = Card()
top_card.add_widget(Label("Top Section"))
content.addWidget(top_card)

# Bottom card
bottom_card = Card()
bottom_card.add_widget(Label("Bottom Section"))
content.addWidget(bottom_card)

main_layout.addLayout(content, stretch=3)
```

## Reusable Components

### Create Compound Components

```python
from design_system import (
    Panel, PanelHeader, SearchBox, FileList, EmptyState
)

class FileBrowser(Panel):
    """Reusable file browser component."""

    def __init__(self, title="Files"):
        super().__init__()

        # Header
        self.add_widget(PanelHeader(title=title))

        # Search
        self.search = SearchBox(placeholder="Search...")
        self.search.text_changed.connect(self._filter)
        self.add_widget(self.search)

        # File list
        self.file_list = FileList()
        self.add_widget(self.file_list)

        # Empty state
        self.empty = EmptyState(
            icon="mdi6.file-outline",
            title="No files",
            description="No files match your search"
        )
        self.empty.hide()
        self.add_widget(self.empty)

        self._all_files = []

    def set_files(self, files):
        self._all_files = files
        self._render_files(files)

    def _filter(self, query):
        filtered = [f for f in self._all_files
                    if query.lower() in f["name"].lower()]
        self._render_files(filtered)

    def _render_files(self, files):
        self.file_list.clear()
        for f in files:
            self.file_list.add_file(**f)

        if files:
            self.file_list.show()
            self.empty.hide()
        else:
            self.file_list.hide()
            self.empty.show()
```

### Parameterized Components

```python
from design_system import Card, CardHeader, Button, Badge

class ActionCard(Card):
    """Card with configurable actions."""

    def __init__(self, title, actions=None, badge=None):
        super().__init__()

        # Header with optional badge
        header = CardHeader(title=title)
        if badge:
            header.add_widget(Badge(badge["text"], variant=badge.get("variant", "primary")))
        self.add_widget(header)

        # Action buttons
        if actions:
            for action in actions:
                btn = Button(
                    action["label"],
                    variant=action.get("variant", "outline")
                )
                if "on_click" in action:
                    btn.clicked.connect(action["on_click"])
                self.add_widget(btn)

# Usage
card = ActionCard(
    title="Document",
    badge={"text": "New", "variant": "success"},
    actions=[
        {"label": "Edit", "variant": "primary", "on_click": edit_doc},
        {"label": "Delete", "variant": "danger", "on_click": delete_doc},
    ]
)
```

## Layout Patterns

### Master-Detail Layout

```python
from PySide6.QtWidgets import QSplitter
from design_system import Panel, FileList, TextPanel

class MasterDetailView(QSplitter):
    def __init__(self):
        super().__init__()

        # Master (list)
        self.master = Panel()
        self.file_list = FileList()
        self.file_list.item_clicked.connect(self.show_detail)
        self.master.add_widget(self.file_list)
        self.addWidget(self.master)

        # Detail (content)
        self.detail = TextPanel()
        self.addWidget(self.detail)

        # Set proportions
        self.setSizes([300, 700])

    def show_detail(self, file_id):
        # Load and display file content
        content = self.load_file(file_id)
        self.detail.set_text(content)
```

### Tab-Based Layout

```python
from design_system import TabGroup, Panel

class TabbedView(Panel):
    def __init__(self):
        super().__init__()

        # Tab navigation
        self.tabs = TabGroup()
        self.tabs.add_tab("Overview", active=True)
        self.tabs.add_tab("Details")
        self.tabs.add_tab("History")
        self.tabs.tab_changed.connect(self.switch_tab)
        self.add_widget(self.tabs)

        # Content panels
        self.overview_panel = self.create_overview()
        self.details_panel = self.create_details()
        self.history_panel = self.create_history()

        self.panels = {
            "Overview": self.overview_panel,
            "Details": self.details_panel,
            "History": self.history_panel,
        }

        # Show initial panel
        self.current_panel = self.overview_panel
        self.add_widget(self.current_panel)

    def switch_tab(self, tab_name):
        # Hide current
        self.current_panel.hide()

        # Show new
        self.current_panel = self.panels[tab_name]
        self.current_panel.show()
```

## Composition Best Practices

### Do

- Break complex UIs into reusable components
- Use composition over inheritance
- Pass configuration through constructor parameters
- Keep components focused on single responsibility

### Don't

- Create deeply nested component hierarchies
- Duplicate layout code across components
- Tightly couple components to specific data structures
- Mix business logic with presentation
