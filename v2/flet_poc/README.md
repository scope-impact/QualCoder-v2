# QualCoder v2 - Flet Dashboard POC

Proof-of-concept demonstrating migration from PySide6 to Flet while preserving the EventBus architecture.

## Quick Start

```bash
# From project root
cd v2/flet_poc
uv run python dashboard.py
```

## What This Demonstrates

### 1. EventBus Architecture (Preserved)

The existing QualCoder EventBus pattern integrates seamlessly with Flet:

```
User Action (button click)
    ↓
EventBus.publish(DomainEvent)
    ↓
FletSignalBridge (subscribes to events)
    ↓
UI Callback (updates state)
    ↓
page.update() (triggers re-render)
```

### 2. Design Token System

The CSS design tokens from `v2/mockups/css/design-system.css` translate to Python dataclasses:

```python
from tokens import TYPOGRAPHY, SPACING, RADIUS, get_colors

colors = get_colors(dark_mode=False)
ft.Text("Hello", size=TYPOGRAPHY.lg, color=colors.primary_500)
```

### 3. Component Architecture

The dashboard implements the full mockup design:
- Navigation sidebar with user info
- Hero section with live stats
- Quick action cards
- AI insight card
- Code frequency chart
- Activity feed (updates in real-time)
- Sources to code list

## Interactive Features

Click the buttons to see EventBus in action:

| Button | Event Published | UI Update |
|--------|-----------------|-----------|
| Import | `SourceImported` | Sources list + stats + activity |
| Create Code | `CodeCreated` | Code chart + stats + activity |
| Continue Coding | `SegmentCoded` | Code counts + activity |
| Theme toggle | - | Full UI re-render |

## Files

```
v2/flet_poc/
├── dashboard.py      # Main UI (~850 lines)
├── event_bus.py      # Simplified EventBus
├── signal_bridge.py  # Flet-specific bridge
├── tokens.py         # Design tokens
└── README.md         # This file
```

## Key Patterns

### FletSignalBridge

```python
class FletSignalBridge:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.on_code_created: Callable | None = None  # UI callback

    def start(self):
        self.event_bus.subscribe_type(CodeCreated, self._handle_code_created)

    def _handle_code_created(self, event: CodeCreated):
        if self.on_code_created:
            self.on_code_created(event)  # Call UI callback
        self._update_ui()  # Trigger Flet re-render
```

### Dashboard Component

```python
class Dashboard(ft.Column):
    def __init__(self, event_bus: EventBus, bridge: FletSignalBridge):
        self.event_bus = event_bus
        self.bridge = bridge
        self.bridge.on_code_created = self._on_code_created  # Wire callback

    def _on_code_created(self, event: CodeCreated):
        self.state.add_code(event.name, event.color)  # Update state
        # Bridge calls page.update() automatically

    def _create_code(self, e):  # Button handler
        event = CodeCreated(name="New Code", color="#3d7a63")
        self.event_bus.publish(event)  # Publish to EventBus
```

## Comparison: Qt vs Flet

| Aspect | Qt (Current) | Flet (POC) |
|--------|--------------|------------|
| Signal Bridge | Qt Signals + QMetaObject | Callbacks + page.update() |
| Thread Safety | QueuedConnection | Flet handles internally |
| Styling | QSS stylesheets | Python properties |
| State | ViewModels | State classes |
| Lifecycle | show/close events | did_mount/will_unmount |

## Next Steps

1. Evaluate text editor component (WebView + CodeMirror?)
2. Implement remaining screens (Coding, Sources, Cases)
3. Test cross-platform (Windows, macOS, web)
4. Performance profiling with large datasets
