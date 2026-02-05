# List Components

Collection display components for files, cases, attributes, and queues.

## FileList

File list with type icons.

![File List](images/file_list.png)

```python
from design_system import FileList

files = FileList()
files.add_file(
    id="1",
    name="interview.txt",
    file_type="text",
    size="15KB",
    status="coded"
)

files.item_clicked.connect(lambda id: print(f"Selected: {id}"))
files.item_double_clicked.connect(lambda id: print(f"Open: {id}"))
```

### FileList Methods

| Method | Description |
|--------|-------------|
| `add_file(id, name, file_type, size, status)` | Add a file |
| `remove_file(id)` | Remove a file |
| `clear()` | Clear all files |

### FileList Signals

| Signal | Description |
|--------|-------------|
| `item_clicked(id)` | File clicked |
| `item_double_clicked(id)` | File double-clicked |

---

## CaseList

Case/study list.

![Case List](images/case_list.png)

```python
from design_system import CaseList, ListItem

cases = CaseList()
cases.add_item(ListItem(id="1", text="Case Study A", subtitle="5 files"))
```

---

## AttributeList

Attribute list display.

```python
from design_system import AttributeList, ListItem

attrs = AttributeList()
attrs.add_item(ListItem(id="1", text="Age", subtitle="Numeric"))
```

---

## QueueList

Queue/task list.

```python
from design_system import QueueList, ListItem

queue = QueueList()
queue.add_item(ListItem(
    id="1",
    text="Review coding",
    badge="3",
    badge_variant="warning"
))
```

---

## ListItem

Data structure for list items.

```python
from design_system import ListItem

item = ListItem(
    id="unique-id",
    text="Item Title",
    subtitle="Optional subtitle",
    icon="mdi6.file",
    badge="New",
    badge_variant="primary",
    data={"custom": "data"}
)
```

### ListItem Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `id` | str | required | Unique identifier |
| `text` | str | required | Primary text |
| `subtitle` | str | `None` | Secondary text |
| `icon` | str | `None` | Icon name |
| `badge` | str | `None` | Badge text |
| `badge_variant` | str | `"default"` | Badge style |
| `data` | dict | `None` | Custom data |

---

## BaseList

Base class for all list components.

```python
from design_system import BaseList

# Typically subclassed, provides:
# - item_clicked signal
# - item_double_clicked signal
# - Selection management
```

### BaseList Signals

| Signal | Description |
|--------|-------------|
| `item_clicked(id)` | Item clicked |
| `item_double_clicked(id)` | Item double-clicked |

---

## List Item Widgets

Individual item widgets for list components.

### FileListItem

```python
from design_system import FileListItem

file_item = FileListItem(
    id="1",
    name="document.txt",
    file_type="text",
    size="10KB"
)
```

### CaseListItem

```python
from design_system import CaseListItem

case_item = CaseListItem(
    id="1",
    name="Case Study A",
    file_count=5
)
```

### AttributeListItem

```python
from design_system import AttributeListItem

attr_item = AttributeListItem(
    id="1",
    name="Age",
    value_type="numeric"
)
```

### QueueListItem

```python
from design_system import QueueListItem

queue_item = QueueListItem(
    id="1",
    title="Review document",
    status="pending"
)
```

---

## VersionHistoryPanel

Timeline panel showing VCS snapshots with restore functionality.

```python
from src.shared.presentation.organisms import VersionHistoryPanel, SnapshotItem
from datetime import datetime

panel = VersionHistoryPanel(colors=get_colors())

# Set snapshots (newest first)
panel.set_snapshots([
    SnapshotItem(
        git_sha="abc12345",
        message="coding: 3 events",
        timestamp=datetime.now(),
        event_count=3,
        is_current=True
    ),
    SnapshotItem(
        git_sha="def67890",
        message="sources: 1 event",
        timestamp=datetime.now(),
        event_count=1,
        is_current=False
    ),
])

# Handle user actions
panel.restore_requested.connect(lambda sha: restore_to(sha))
panel.view_diff_requested.connect(lambda from_sha, to_sha: show_diff(from_sha, to_sha))
panel.refresh_requested.connect(lambda: reload_history())
```

### VersionHistoryPanel Signals

| Signal | Description |
|--------|-------------|
| `restore_requested(str)` | User wants to restore to snapshot (emits SHA) |
| `view_diff_requested(str, str)` | User wants to view diff (from_sha, to_sha) |
| `refresh_requested()` | User clicked refresh button |

### VersionHistoryPanel Methods

| Method | Description |
|--------|-------------|
| `set_snapshots(list)` | Update displayed snapshots |
| `clear()` | Clear all snapshots |

---

## SnapshotItem

Data class for a single snapshot in the version history timeline.

```python
from src.shared.presentation.organisms import SnapshotItem
from datetime import datetime

item = SnapshotItem(
    git_sha="abc12345",
    message="coding: 3 events",
    timestamp=datetime.now(),
    event_count=3,
    is_current=True
)
```

### SnapshotItem Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `git_sha` | str | required | Git commit SHA |
| `message` | str | required | Commit message |
| `timestamp` | datetime | required | When snapshot was created |
| `event_count` | int | `0` | Number of events in snapshot |
| `is_current` | bool | `False` | Whether this is the current state |

---

## SnapshotCard

Individual card widget for a snapshot in the timeline.

```python
from src.shared.presentation.organisms import SnapshotCard, SnapshotItem

card = SnapshotCard(
    snapshot=snapshot_item,
    previous_sha="def67890",  # For diff comparison
    colors=get_colors()
)

card.restore_clicked.connect(lambda sha: handle_restore(sha))
card.view_diff_clicked.connect(lambda from_sha, to_sha: handle_diff(from_sha, to_sha))
```

### SnapshotCard Features

- **Current badge** - Shows "Current" badge for active state
- **Timeline dot** - Visual indicator in timeline
- **Timestamp** - When snapshot was created
- **Message** - Commit message describing changes
- **SHA display** - Truncated commit SHA
- **Restore button** - Restore to this snapshot (non-current only)
- **View Changes button** - Compare with previous snapshot

---

## List Example

File browser with filtering:

```python
from design_system import (
    Panel, PanelHeader, FileList, SearchBox,
    MediaTypeSelector, EmptyState
)

class FileBrowser(Panel):
    def __init__(self):
        super().__init__()

        # Header with search
        header = PanelHeader(title="Files")
        self.add_widget(header)

        # Search
        self.search = SearchBox(placeholder="Search files...")
        self.search.text_changed.connect(self.filter_files)
        self.add_widget(self.search)

        # Type filter
        self.type_filter = MediaTypeSelector()
        self.add_widget(self.type_filter)

        # File list
        self.file_list = FileList()
        self.file_list.item_clicked.connect(self.on_file_selected)
        self.file_list.item_double_clicked.connect(self.on_file_opened)
        self.add_widget(self.file_list)

        # Empty state (shown when no files)
        self.empty = EmptyState(
            icon="mdi6.file-outline",
            title="No files",
            description="Import files to get started"
        )
        self.empty.hide()
        self.add_widget(self.empty)

    def set_files(self, files):
        self.file_list.clear()
        for f in files:
            self.file_list.add_file(
                id=f["id"],
                name=f["name"],
                file_type=f["type"],
                size=f["size"],
                status=f.get("status", "")
            )

        if not files:
            self.file_list.hide()
            self.empty.show()
        else:
            self.file_list.show()
            self.empty.hide()

    def filter_files(self, query):
        # Implement filtering logic
        pass

    def on_file_selected(self, file_id):
        print(f"Selected: {file_id}")

    def on_file_opened(self, file_id):
        print(f"Opening: {file_id}")
```
