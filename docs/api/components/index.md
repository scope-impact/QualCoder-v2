# Components

The QualCoder Design System provides 180+ reusable components organized into functional categories.

## Component Categories

| Category | Components | Description |
|----------|------------|-------------|
| [Core](core.md) | Button, Input, Label, Card, Badge, Alert, Avatar, Chip | Fundamental UI elements |
| [Icons](icons.md) | Icon, IconText | Material Design Icons |
| [Layout](layout.md) | AppContainer, Panel, Sidebar, Toolbar | Application structure |
| [Forms](forms.md) | SearchBox, Select, Textarea, ColorPicker | User input |
| [Navigation](navigation.md) | Tab, TabGroup, Breadcrumb, NavList | Navigation patterns |
| [Data Display](data-display.md) | DataTable, CodeTree, InfoCard, KeyValueList | Data presentation |
| [Lists](lists.md) | FileList, CaseList, AttributeList, VersionHistoryPanel | Collection displays |
| [Media](media.md) | VideoContainer, Timeline, PlayerControls | Media playback |
| [Chat & AI](chat.md) | MessageBubble, ChatInput, CodeSuggestion | AI interface |
| [Document](document.md) | TextPanel, TranscriptPanel, SelectionPopup, DiffHighlighter | Document handling |
| [Feedback](feedback.md) | Spinner, Toast, ProgressBar | User feedback |
| [Visualization](visualization.md) | ChartWidget, NetworkGraph, WordCloud | Data visualization |
| [Pickers](pickers.md) | TypeSelector, ColorSchemeSelector | Selection widgets |
| [Advanced](advanced.md) | Modal, ContextMenu, CodeEditor, Pagination | Complex components |

## Import Patterns

### Individual Imports

```python
from design_system import Button, Card, Label
```

### Category Imports

```python
from design_system import (
    # Core
    Button, Input, Label, Card, Badge, Alert,
    # Layout
    AppContainer, Panel, Sidebar,
    # Forms
    SearchBox, Select, Textarea,
)
```

### Full Import

```python
from design_system import *  # Not recommended for production
```

## Component Conventions

### Constructor Parameters

Most components accept:

- **Required parameters** — Essential data (text, items, etc.)
- **Optional styling** — `variant`, `size`, `colors`
- **Optional behavior** — `closable`, `checkable`, `editable`

### Signals

Components emit Qt signals for interactivity:

```python
button.clicked.connect(handler)
table.row_clicked.connect(lambda idx, data: handle_row(idx))
search.text_changed.connect(filter_results)
```

### Common Signals

| Signal | Emitted When |
|--------|--------------|
| `clicked` | Element clicked |
| `double_clicked` | Element double-clicked |
| `value_changed` | Value modified |
| `selection_changed` | Selection updated |
| `text_changed` | Text content changed |

### Methods

Components provide methods for:

- **Data access** — `text()`, `value()`, `get_selected()`
- **Data modification** — `setText()`, `setValue()`, `set_items()`
- **State management** — `setEnabled()`, `setVisible()`, `clear()`
