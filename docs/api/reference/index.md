# Reference

Technical reference for the QualCoder Design System.

## Sections

- [Module Index](modules.md) — All modules and their contents
- [Dependencies](dependencies.md) — Required packages

## Quick Links

### Import Everything

```python
from design_system import *
```

### Import by Category

```python
# Tokens
from design_system import COLORS, SPACING, RADIUS, TYPOGRAPHY

# Core components
from design_system import Button, Input, Label, Card, Badge

# Layout
from design_system import AppContainer, Panel, Sidebar, Toolbar

# Forms
from design_system import SearchBox, Select, Textarea

# Data display
from design_system import DataTable, CodeTree, FileList

# Feedback
from design_system import Toast, Spinner, ProgressBar
```

## Type Annotations

All components include type annotations for IDE support:

```python
def add_file(
    self,
    id: str,
    name: str,
    file_type: str,
    size: str = "",
    status: str = ""
) -> None:
    ...
```

## Signal Types

Common signal signatures:

| Signal | Parameters | Description |
|--------|------------|-------------|
| `clicked` | `()` | Simple click |
| `text_changed` | `(str)` | Text updated |
| `value_changed` | `(Any)` | Value changed |
| `item_clicked` | `(str)` | Item ID clicked |
| `row_clicked` | `(int, dict)` | Row index and data |
| `selection_changed` | `(list)` | Selected items |
