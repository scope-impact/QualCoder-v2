# Icons

Material Design Icons via qtawesome (mdi6 prefix).

## Icon

Icon widget for displaying Material Design Icons.

```python
from design_system import Icon, IconText, icon, get_pixmap, get_qicon

# Icon widget
folder_icon = Icon("mdi6.folder", size=24, color="#009688")
folder_icon.set_color("#FF5722")
folder_icon.set_size(32)
```

### Icon Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `name` | str | required | Icon name (mdi6.xxx) |
| `size` | int | `24` | Icon size in pixels |
| `color` | str | `None` | Icon color (hex) |

### Icon Methods

| Method | Description |
|--------|-------------|
| `set_color(color)` | Update icon color |
| `set_size(size)` | Update icon size |

---

## IconText

Icon and text side by side.

```python
from design_system import IconText

item = IconText(icon="mdi6.file", text="document.txt", icon_size=20)
```

### IconText Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `icon` | str | required | Icon name |
| `text` | str | required | Text label |
| `icon_size` | int | `20` | Icon size |

---

## Factory Functions

### icon()

Create an icon widget.

```python
from design_system import icon

icon_widget = icon("mdi6.home", size=20, color="#000")
```

### get_pixmap()

Get a QPixmap for use in other widgets.

```python
from design_system import get_pixmap

pixmap = get_pixmap("mdi6.save", size=24, color="#009688")
label.setPixmap(pixmap)
```

### get_qicon()

Get a QIcon for use in menus, buttons, etc.

```python
from design_system import get_qicon

qicon = get_qicon("mdi6.settings", color="#666")
action.setIcon(qicon)
button.setIcon(qicon)
```

---

## Common Icon Names

### Navigation

| Icon | Name | Description |
|------|------|-------------|
| 🏠 | `mdi6.home` | Home |
| ☰ | `mdi6.menu` | Menu |
| ← | `mdi6.arrow-left` | Back |
| › | `mdi6.chevron-right` | Expand |
| ↑ | `mdi6.arrow-up` | Up |
| ↓ | `mdi6.arrow-down` | Down |

### Actions

| Icon | Name | Description |
|------|------|-------------|
| + | `mdi6.plus` | Add |
| 🗑 | `mdi6.delete` | Delete |
| ✏ | `mdi6.pencil` | Edit |
| ✓ | `mdi6.check` | Confirm |
| ✕ | `mdi6.close` | Close |
| 💾 | `mdi6.content-save` | Save |
| ↻ | `mdi6.refresh` | Refresh |

### Files

| Icon | Name | Description |
|------|------|-------------|
| 📄 | `mdi6.file` | File |
| 📁 | `mdi6.folder` | Folder |
| 📂 | `mdi6.folder-open` | Open folder |
| 📝 | `mdi6.file-document` | Document |
| 🖼 | `mdi6.file-image` | Image file |
| 📊 | `mdi6.file-chart` | Chart file |

### Media

| Icon | Name | Description |
|------|------|-------------|
| ▶ | `mdi6.play` | Play |
| ⏸ | `mdi6.pause` | Pause |
| ⏹ | `mdi6.stop` | Stop |
| 🔊 | `mdi6.volume-high` | Volume |
| 🎤 | `mdi6.microphone` | Microphone |

### Status

| Icon | Name | Description |
|------|------|-------------|
| ✓ | `mdi6.check-circle` | Success |
| ⚠ | `mdi6.alert` | Warning |
| ✕ | `mdi6.close-circle` | Error |
| ℹ | `mdi6.information` | Info |
| ⏳ | `mdi6.loading` | Loading |

### UI

| Icon | Name | Description |
|------|------|-------------|
| 🔍 | `mdi6.magnify` | Search |
| ⚙ | `mdi6.cog` | Settings |
| 👤 | `mdi6.account` | User |
| 🏷 | `mdi6.tag` | Tag |
| ⋮ | `mdi6.dots-vertical` | More options |

---

## Finding Icons

The design system uses Material Design Icons from the [Pictogrammers](https://pictogrammers.com/library/mdi/) library.

1. Visit [pictogrammers.com/library/mdi/](https://pictogrammers.com/library/mdi/)
2. Search for an icon
3. Use the name with `mdi6.` prefix

**Example:** The "folder" icon becomes `mdi6.folder`

---

## Usage Examples

### Button with Icon

```python
from design_system import Button, get_qicon

button = Button("Save")
button.setIcon(get_qicon("mdi6.content-save"))
```

### Menu Item with Icon

```python
from PySide6.QtWidgets import QAction
from design_system import get_qicon

action = QAction("Open")
action.setIcon(get_qicon("mdi6.folder-open"))
menu.addAction(action)
```

### Tree Item with Icon

```python
from PySide6.QtWidgets import QTreeWidgetItem
from design_system import get_qicon

item = QTreeWidgetItem(["Documents"])
item.setIcon(0, get_qicon("mdi6.folder"))
```

### Status Indicator

```python
from design_system import Icon

def get_status_icon(status: str) -> Icon:
    icons = {
        "success": ("mdi6.check-circle", "#4CAF50"),
        "warning": ("mdi6.alert", "#FF9800"),
        "error": ("mdi6.close-circle", "#F44336"),
        "info": ("mdi6.information", "#2196F3"),
    }
    name, color = icons.get(status, ("mdi6.help-circle", "#9E9E9E"))
    return Icon(name, color=color)
```
