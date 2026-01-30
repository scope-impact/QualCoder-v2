# Data Display Components

Components for presenting data: tables, trees, cards, and lists.

## DataTable

Data table with selection support.

![Data Table](../../../design_system/assets/screenshots/data_table.png)

```python
from design_system import DataTable

table = DataTable(
    headers=["Name", "Type", "Size"],
    checkable=True  # Enable row selection
)

# Set data
table.set_data([
    {"name": "file1.txt", "type": "text", "size": "10KB"},
    {"name": "file2.pdf", "type": "pdf", "size": "2MB"},
])

# Signals
table.row_clicked.connect(lambda idx, data: print(f"Clicked row {idx}"))
table.row_double_clicked.connect(lambda idx, data: print(f"Double-clicked {idx}"))
table.selection_changed.connect(lambda selected: print(f"Selected: {selected}"))

# Methods
selected = table.get_selected()
table.clear()
```

### DataTable Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `headers` | list | `[]` | Column headers |
| `checkable` | bool | `False` | Enable row selection |

### DataTable Signals

| Signal | Description |
|--------|-------------|
| `row_clicked(idx, data)` | Row clicked |
| `row_double_clicked(idx, data)` | Row double-clicked |
| `selection_changed(selected)` | Selection changed |

---

## CodeTree

Hierarchical tree for qualitative codes.

![Code Tree](../../../design_system/assets/screenshots/code_tree.png)

```python
from design_system import CodeTree, CodeItem, CodeTreeNode

# Define hierarchical structure using CodeItem data class
items = [
    CodeItem(
        id="1",
        name="Theme A",
        color="#FFC107",
        count=15,
        children=[
            CodeItem(id="1.1", name="Sub-theme", color="#FFD54F", count=5),
        ]
    ),
    CodeItem(id="2", name="Theme B", color="#4CAF50", count=8),
]

tree = CodeTree()
tree.set_items(items)

# Signals
tree.item_clicked.connect(lambda id: print(f"Clicked: {id}"))
tree.item_double_clicked.connect(lambda id: print(f"Edit: {id}"))
tree.item_expanded.connect(lambda id, expanded: print(f"Expanded: {id} = {expanded}"))

# Methods
tree.add_item(CodeItem("3", "New Code", "#2196F3"), parent_id="1")
tree.remove_item("3")
tree.expand_item("1", True)
```

### CodeItem Data Class

```python
from design_system import CodeItem

item = CodeItem(
    id="unique-id",
    name="Code Name",
    color="#FFC107",
    count=10,
    children=[]  # Nested CodeItems
)
```

### CodeTree Signals

| Signal | Description |
|--------|-------------|
| `item_clicked(id)` | Item clicked |
| `item_double_clicked(id)` | Item double-clicked |
| `item_expanded(id, expanded)` | Item expand toggled |

---

## InfoCard

Information card with icon, supports collapsible content.

```python
from design_system import InfoCard

card = InfoCard(
    icon="mdi6.information",
    title="Total Files",
    description="127 files imported",
    collapsible=True
)

# Signal for collapse state changes
card.collapsed_changed.connect(lambda collapsed: print(f"Collapsed: {collapsed}"))
```

### InfoCard Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `icon` | str | `None` | Icon name |
| `title` | str | `""` | Card title |
| `description` | str | `""` | Card description |
| `collapsible` | bool | `False` | Enable collapse |

---

## KeyValueList

Key-value pairs display.

![Key Value List](../../../design_system/assets/screenshots/key_value_list.png)

```python
from design_system import KeyValueList

kvlist = KeyValueList()
kvlist.set_items([
    ("Name", "Project Alpha"),
    ("Created", "2024-01-15"),
    ("Files", "42"),
])
```

### KeyValueList Methods

| Method | Description |
|--------|-------------|
| `set_items(items)` | Set key-value pairs |
| `add_item(key, value)` | Add single pair |
| `clear()` | Clear all items |

---

## EmptyState

Placeholder for empty content.

![Empty State](../../../design_system/assets/screenshots/empty_state.png)

```python
from design_system import EmptyState

empty = EmptyState(
    icon="mdi6.folder-open",
    title="No files yet",
    description="Import files to get started"
)
```

### EmptyState Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `icon` | str | `None` | Icon name |
| `title` | str | `""` | Empty state title |
| `description` | str | `""` | Explanatory text |

---

## HeatMapGrid / HeatMapCell

Heatmap visualization with interactive cells.

```python
from design_system import HeatMapGrid, HeatMapCell

grid = HeatMapGrid(rows=5, cols=5)
grid.set_value(row=0, col=0, value=0.8)

# Signal for cell interaction
grid.cell_clicked.connect(lambda row, col, value: print(f"Cell ({row},{col}): {value}"))

# Individual cell
cell = HeatMapCell(value=0.5)
cell.clicked.connect(lambda value: print(f"Value: {value}"))
```

---

## CodeDetailCard

Detailed code information card with actions.

```python
from design_system import CodeDetailCard

card = CodeDetailCard(
    code_name="Theme A",
    code_color="#FFC107",
    description="Description of the code",
    count=15
)

# Signals
card.edit_clicked.connect(lambda: edit_code())
card.delete_clicked.connect(lambda: delete_code())
```

---

## FileCell / EntityCell

Table cell widgets for file and entity display.

```python
from design_system import FileCell, EntityCell

# File cell with icon
file_cell = FileCell(filename="document.txt", file_type="text")
file_cell.clicked.connect(lambda: open_file())

# Entity cell
entity_cell = EntityCell(name="Person A", entity_type="participant")
entity_cell.clicked.connect(lambda: show_entity())
```

---

## StatRow

Statistics row display.

```python
from design_system import StatRow

row = StatRow()
row.add_stat("Files", "42")
row.add_stat("Codes", "15")
row.add_stat("Cases", "8")
```
