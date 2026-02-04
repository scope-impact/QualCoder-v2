# Layout Components

Application structure components: containers, panels, sidebars, and toolbars.

## AppContainer

Main application container with section management.

```python
from design_system import AppContainer, TitleBar, MenuBar, Toolbar, StatusBar, MainContent

app = AppContainer()
app.set_title_bar(TitleBar(title="QualCoder"))
app.set_menu_bar(MenuBar())
app.set_toolbar(Toolbar())
app.set_content(MainContent())  # Central content area
app.set_status_bar(StatusBar())
```

### AppContainer Methods

| Method | Description |
|--------|-------------|
| `set_title_bar(widget)` | Set the title bar |
| `set_menu_bar(widget)` | Set the menu bar |
| `set_toolbar(widget)` | Set the toolbar |
| `set_content(widget)` | Set central content |
| `set_status_bar(widget)` | Set the status bar |

---

## TitleBar

Application title bar.

```python
from design_system import TitleBar

title_bar = TitleBar(title="QualCoder v2")
title_bar.set_title("New Title")
```

### TitleBar Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `title` | str | `""` | Application title |

---

## MenuBar

Application menu bar container.

```python
from design_system import MenuBar

menu_bar = MenuBar()
menu_bar.add_menu("File")
menu_bar.add_menu("Edit")
menu_bar.add_menu("View")
```

### MenuBar Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `add_menu(name)` | QMenu | Add a menu |

---

## MainContent

Main content area container.

```python
from design_system import MainContent

content = MainContent()
content.add_widget(panel)
```

---

## Panel

Side panel with header.

![Panel with Header](images/panel_with_header.png)

```python
from design_system import Panel, PanelHeader

panel = Panel()
header = PanelHeader(title="Properties")
panel.add_widget(header)
panel.add_widget(content)
```

### PanelHeader

```python
from design_system import PanelHeader

header = PanelHeader(title="Section Title")
```

---

## Sidebar

Collapsible sidebar.

![Sidebar](images/sidebar.png)

```python
from design_system import Sidebar

sidebar = Sidebar()
sidebar.add_widget(navigation)
```

---

## Toolbar

Tool button container.

![Toolbar](images/toolbar.png)

```python
from design_system import Toolbar, ToolbarGroup, ToolbarButton

toolbar = Toolbar()

# Add groups of buttons using ToolbarGroup
file_group = ToolbarGroup()
file_group.add_widget(ToolbarButton("mdi6.folder-open", "Open"))
file_group.add_widget(ToolbarButton("mdi6.content-save", "Save"))
toolbar.add_widget(file_group)
```

### ToolbarButton

```python
from design_system import ToolbarButton

btn = ToolbarButton(icon="mdi6.play", tooltip="Play")
btn.clicked.connect(play_handler)
```

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `icon` | str | required | Icon name |
| `tooltip` | str | `""` | Hover tooltip |

### ToolbarGroup

Groups related toolbar buttons together.

```python
from design_system import ToolbarGroup, ToolbarButton

group = ToolbarGroup()
group.add_widget(ToolbarButton("mdi6.undo", "Undo"))
group.add_widget(ToolbarButton("mdi6.redo", "Redo"))
```

---

## StatusBar

Bottom status bar.

```python
from design_system import StatusBar, Label

status = StatusBar()
status.add_widget(Label("Ready"))
```

---

## TabBar

Tab bar component for window/panel tabs.

```python
from design_system import TabBar

tab_bar = TabBar()
tab_bar.add_tab("Tab 1", active=True)
tab_bar.add_tab("Tab 2")
tab_bar.tab_changed.connect(lambda index: switch_content(index))
```

### TabBar Methods

| Method | Description |
|--------|-------------|
| `add_tab(name, active=False)` | Add a tab |

### TabBar Signals

| Signal | Description |
|--------|-------------|
| `tab_changed(index)` | Emitted when active tab changes |

---

## Layout Example

Complete application layout:

```python
from design_system import (
    AppContainer, TitleBar, MenuBar, Toolbar, StatusBar,
    MainContent, Sidebar, Panel, PanelHeader,
    ToolbarGroup, ToolbarButton, Label
)

# Create container
app = AppContainer()

# Title bar
app.set_title_bar(TitleBar(title="QualCoder"))

# Menu bar
menu_bar = MenuBar()
menu_bar.add_menu("File")
menu_bar.add_menu("Edit")
app.set_menu_bar(menu_bar)

# Toolbar
toolbar = Toolbar()
file_group = ToolbarGroup()
file_group.add_widget(ToolbarButton("mdi6.folder-open", "Open"))
file_group.add_widget(ToolbarButton("mdi6.content-save", "Save"))
toolbar.add_widget(file_group)
app.set_toolbar(toolbar)

# Sidebar
sidebar = Sidebar()
# Add navigation items...
app.set_sidebar(sidebar)

# Main content
content = MainContent()

# Side panel
panel = Panel()
panel.add_widget(PanelHeader(title="Properties"))
panel.add_widget(Label("Content here"))
content.add_widget(panel)

app.set_content(content)

# Status bar
status = StatusBar()
status.add_widget(Label("Ready"))
app.set_status_bar(status)
```
