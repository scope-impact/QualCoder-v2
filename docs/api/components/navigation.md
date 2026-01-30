# Navigation Components

Navigation patterns: tabs, menus, breadcrumbs, and step indicators.

## Tab / TabGroup

Tab navigation.

![Tab Group](../../../design_system/assets/screenshots/tab_group.png)

```python
from design_system import Tab, TabGroup

tabs = TabGroup()
tabs.add_tab("Files", icon="mdi6.file", active=True)
tabs.add_tab("Codes", icon="mdi6.tag")
tabs.add_tab("Cases", icon="mdi6.folder")

tabs.tab_changed.connect(lambda name: print(f"Tab: {name}"))
active = tabs.get_active_tab()
```

### TabGroup Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `add_tab(name, icon, active)` | Tab | Add a tab |
| `get_active_tab()` | str | Get active tab name |
| `set_active_tab(name)` | None | Set active tab |

### TabGroup Signals

| Signal | Description |
|--------|-------------|
| `tab_changed(name)` | Emitted when tab changes |

---

## MenuItem

Menu item with optional icon.

```python
from design_system import MenuItem

item = MenuItem("Open Project", icon="mdi6.folder-open")
item.setActive(True)
item.clicked.connect(handler)
```

### MenuItem Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `text` | str | required | Menu item label |
| `icon` | str | `None` | Icon name |

### MenuItem Methods

| Method | Description |
|--------|-------------|
| `setActive(bool)` | Set active state |

---

## Breadcrumb

Breadcrumb navigation path.

![Breadcrumb](../../../design_system/assets/screenshots/breadcrumb_navigation.png)

```python
from design_system import Breadcrumb

breadcrumb = Breadcrumb()
breadcrumb.set_path(["Home", "Projects", "Current"])
```

### Breadcrumb Methods

| Method | Description |
|--------|-------------|
| `set_path(items)` | Set breadcrumb path |
| `get_path()` | Get current path |

---

## NavList

Vertical navigation list.

```python
from design_system import NavList

nav = NavList()
nav.add_item("Dashboard", icon="mdi6.view-dashboard")
nav.add_item("Settings", icon="mdi6.cog")
```

### NavList Methods

| Method | Description |
|--------|-------------|
| `add_item(name, icon)` | Add navigation item |
| `set_active(name)` | Set active item |

---

## StepIndicator

Progress steps display.

![Step Indicator](../../../design_system/assets/screenshots/step_indicator.png)

```python
from design_system import StepIndicator

steps = StepIndicator()
steps.set_steps(["Upload", "Configure", "Review", "Complete"])
steps.set_current(1)  # 0-indexed
```

### StepIndicator Methods

| Method | Description |
|--------|-------------|
| `set_steps(steps)` | Set step names |
| `set_current(index)` | Set current step (0-indexed) |
| `get_current()` | Get current step index |

---

## MediaTypeSelector

File type filter selector.

```python
from design_system import MediaTypeSelector

selector = MediaTypeSelector()
# Allows filtering by: text, audio, video, image, pdf
```

---

## Navigation Example

Complete navigation setup:

```python
from design_system import (
    Sidebar, NavList, TabGroup, Breadcrumb, MenuItem
)

# Sidebar navigation
sidebar = Sidebar()
nav = NavList()
nav.add_item("Home", icon="mdi6.home")
nav.add_item("Files", icon="mdi6.file")
nav.add_item("Codes", icon="mdi6.tag")
nav.add_item("Cases", icon="mdi6.folder")
nav.add_item("Reports", icon="mdi6.chart-bar")
nav.add_item("Settings", icon="mdi6.cog")
sidebar.add_widget(nav)

# Tab navigation for content area
tabs = TabGroup()
tabs.add_tab("Overview", active=True)
tabs.add_tab("Details")
tabs.add_tab("History")

tabs.tab_changed.connect(lambda name: switch_view(name))

# Breadcrumb for location
breadcrumb = Breadcrumb()
breadcrumb.set_path(["Home", "Projects", "My Project", "Files"])
```
