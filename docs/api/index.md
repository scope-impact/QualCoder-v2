# Design System

The QualCoder Design System is a comprehensive PySide6-based component library featuring **180+ reusable, themeable components** following Material Design principles.

## Overview

The design system provides:

- **Design Tokens** — Consistent colors, spacing, typography, and layout values
- **180+ Components** — Buttons, inputs, cards, modals, tables, charts, and more
- **Theme Support** — Light and dark themes with custom theme registration
- **Material Icons** — 7,000+ icons via qtawesome (mdi6 prefix)
- **Qt Signals** — Event-driven interactivity patterns

## Quick Example

```python
from design_system import (
    Button, Input, Label, Card,
    COLORS, SPACING
)

# Create a simple form
card = Card()
card.add_widget(Label("Username", variant="title"))
card.add_widget(Input(placeholder="Enter username..."))
card.add_widget(Button("Submit", variant="primary"))
```

## Sections

| Section | Description |
|---------|-------------|
| [Getting Started](getting-started/index.md) | Installation and quick start guide |
| [Design Tokens](tokens/index.md) | Colors, spacing, typography, and layout constants |
| [Components](components/index.md) | 180+ UI components organized by category |
| [Patterns](patterns/index.md) | Signal handling, theming, and composition patterns |
| [Reference](reference/index.md) | Module index and dependency information |

## Component Categories

| Category | Components | Description |
|----------|------------|-------------|
| [Core](components/core.md) | Button, Input, Label, Card, Badge | Fundamental UI elements |
| [Icons](components/icons.md) | Icon, IconText | Material Design Icons |
| [Layout](components/layout.md) | AppContainer, Panel, Sidebar, Toolbar | Application structure |
| [Forms](components/forms.md) | SearchBox, Select, Textarea | User input |
| [Navigation](components/navigation.md) | Tab, Breadcrumb, NavList | Navigation patterns |
| [Data Display](components/data-display.md) | DataTable, CodeTree, InfoCard | Data presentation |
| [Lists](components/lists.md) | FileList, CaseList, AttributeList | Collection displays |
| [Media](components/media.md) | VideoContainer, Timeline | Media playback |
| [Chat & AI](components/chat.md) | MessageBubble, ChatInput | AI interface |
| [Document](components/document.md) | TextPanel, TranscriptPanel | Document handling |
| [Feedback](components/feedback.md) | Spinner, Toast, ProgressBar | User feedback |
| [Visualization](components/visualization.md) | ChartWidget, NetworkGraph | Data visualization |
| [Pickers](components/pickers.md) | TypeSelector, ColorSchemeSelector | Selection widgets |
| [Advanced](components/advanced.md) | Modal, ContextMenu, CodeEditor | Complex components |

## Integration with Architecture

The Design System is the **Presentation Layer** of QualCoder v2's architecture:

```
Domain (Pure) → Application (Events) → Presentation (Design System)
```

Components receive updates via Qt signals from the [SignalBridge](../tutorials/05-signal-bridge.md), maintaining the separation between pure domain logic and UI.

See the [Architecture Overview](../ARCHITECTURE.md) for how the Design System fits into the larger system.
