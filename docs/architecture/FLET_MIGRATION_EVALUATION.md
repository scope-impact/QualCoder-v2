# Flet Migration Evaluation Plan

## Executive Summary

This document evaluates migrating QualCoder-v2's UI layer from **PySide6 (Qt)** to **Flet** while **preserving the existing EventBus architecture**. The analysis covers architectural compatibility, migration strategy, effort estimation, and risk assessment.

**Recommendation**: Migration is **feasible with moderate effort**. The EventBus architecture can be fully preserved and will integrate naturally with Flet's event model.

---

## 1. Current Architecture Overview

### 1.1 UI Framework: PySide6

| Aspect | Current Implementation |
|--------|----------------------|
| Framework | PySide6 >=6.5.0 (Qt binding) |
| Design Pattern | Atomic Design + MVVM |
| State Management | ViewModels + Qt Signals |
| Threading | QThread + QMetaObject.invokeMethod |
| Styling | QSS (Qt Style Sheets) from design tokens |

### 1.2 EventBus Architecture (TO BE PRESERVED)

```
┌─────────────────────────────────────────────────────────────────┐
│                         EventBus                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  subscribe(event_type, handler) → Subscription          │   │
│  │  subscribe_type(EventClass, handler) → Subscription     │   │
│  │  publish(event) → broadcasts to all subscribers         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │                              │
          ▼                              ▼
┌──────────────────────┐      ┌──────────────────────────────────┐
│   Policy Handlers    │      │        Signal Bridges            │
│  (cross-context)     │      │  (Qt Signals → UI updates)       │
└──────────────────────┘      └──────────────────────────────────┘
```

**Key Components**:
- `EventBus` (`src/shared/infra/event_bus.py`) - Thread-safe pub/sub
- `BaseSignalBridge` (`src/shared/infra/signal_bridge/base.py`) - Domain events → Qt signals
- `OperationResult` (`src/shared/common/operation_result.py`) - Rich result type
- Domain Events (`src/contexts/*/core/events.py`) - Immutable event dataclasses

---

## 2. Flet Framework Analysis

### 2.1 What is Flet?

Flet is a Python framework for building cross-platform apps (web, desktop, mobile) using Flutter as the rendering engine. Key characteristics:

| Feature | Description |
|---------|-------------|
| Rendering | Flutter engine (Skia) |
| Platforms | Windows, macOS, Linux, Web, iOS, Android |
| Architecture | Python ↔ Dart via MessagePack protocol |
| State Model | Control tree with diffing algorithm |
| Styling | Material/Cupertino design + custom themes |

### 2.2 Flet 1.0 Alpha (June 2025)

Major architectural improvements relevant to this migration:

1. **Dataclass Controls** - Controls are Python dataclasses (matches our domain events)
2. **New Diffing Algorithm** - Efficient UI tree updates (imperative & declarative)
3. **InheritedWidget + Provider** - Replaced Redux (better fits our EventBus)
4. **Typed Event Handlers** - Strong typing for events
5. **MessagePack Protocol** - Efficient binary communication

### 2.3 Flet's Built-in PubSub

Flet provides a `page.pubsub` mechanism for inter-session communication:

```python
# Subscribe
page.pubsub.subscribe(handle_message)
page.pubsub.subscribe_topic("coding", handle_coding_event)

# Publish
page.pubsub.send_all(message)
page.pubsub.send_all_on_topic("coding", event)
```

**Important**: Flet's PubSub is for **session-to-session** communication (multi-user apps). Our EventBus is for **domain events within a single app session**. They serve different purposes and can coexist.

---

## 3. EventBus Preservation Strategy

### 3.1 Architecture Compatibility Matrix

| Current Component | Flet Equivalent | Migration Strategy |
|-------------------|-----------------|-------------------|
| `EventBus` | **Keep as-is** | No change needed |
| `BaseSignalBridge` | `FletSignalBridge` | Replace Qt signals with Flet callbacks |
| Qt Signals | Flet control callbacks | Direct function calls |
| `QMetaObject.invokeMethod` | `page.run_task()` / `await` | Async task scheduling |
| `QThread` | `asyncio` / `threading` | Use Flet's async model |
| ViewModels | Reactive state classes | Minimal changes |

### 3.2 New Signal Bridge Architecture

The SignalBridge pattern adapts cleanly to Flet:

```
┌─────────────────────────────────────────────────────────────────┐
│                         EventBus                                │
│                    (UNCHANGED - keep as-is)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FletSignalBridge                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Subscribes to EventBus                               │   │
│  │  • Converts domain events to UI payloads                │   │
│  │  • Schedules UI updates via page.update()               │   │
│  │  • Thread-safe via page.run_task()                      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Flet Controls                              │
│            (receive updates, re-render automatically)           │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Thread Safety Adaptation

**Current (Qt)**:
```python
def _emit_threadsafe(self, signal: Signal, payload: Any) -> None:
    if is_main_thread():
        signal.emit(payload)
    else:
        self._emission_queue.put((signal, payload))
        QMetaObject.invokeMethod(self, "_do_emit", Qt.QueuedConnection)
```

**Flet Equivalent**:
```python
async def _emit_threadsafe(self, handler: Callable, payload: Any) -> None:
    if self._page:
        # Flet handles thread safety internally
        await self._page.run_task(handler, payload)
        self._page.update()
```

### 3.4 Preserved Invariants

These architectural invariants remain unchanged:

1. **EventBus is the single source of truth** for domain events
2. **Domain events are immutable dataclasses** with `event_type: ClassVar[str]`
3. **Command handlers return OperationResult** (not raw data)
4. **Failure events are first-class citizens** (published like success events)
5. **Cross-context communication via string event types** (loose coupling)
6. **Policies subscribe to events** (not called directly)

---

## 4. Component Migration Mapping

### 4.1 Atomic Design → Flet Controls

| Atomic Level | Qt Component | Flet Equivalent |
|--------------|--------------|-----------------|
| **Atoms** | QPushButton, QLineEdit | ft.ElevatedButton, ft.TextField |
| **Atoms** | QLabel, QCheckBox | ft.Text, ft.Checkbox |
| **Molecules** | Custom QWidget | ft.UserControl subclass |
| **Organisms** | Complex QWidget | ft.UserControl with state |
| **Templates** | QMainWindow layouts | ft.Page + ft.Row/Column |
| **Screens** | ScreenProtocol impl | Page-level UserControl |

### 4.2 Design System Token Migration

Current tokens translate directly:

| Token Category | Current (tokens.py) | Flet Equivalent |
|----------------|---------------------|-----------------|
| Colors | `ColorPalette.PRIMARY` | `ft.colors` + custom |
| Spacing | `Spacing.MD = 12` | Padding/margin values |
| Typography | Font sizes, weights | `ft.TextStyle` |
| Shadows | Box shadows | `ft.BoxShadow` |
| Radius | Border radius | `ft.border_radius` |

### 4.3 Complex Components

| Component | Migration Complexity | Notes |
|-----------|---------------------|-------|
| Text Editor | **High** | Need custom control or WebView |
| PDF Viewer | **High** | Use Flet's WebView or native |
| Media Player | **Medium** | Flet has Audio/Video controls |
| Data Tables | **Low** | `ft.DataTable` direct mapping |
| Charts | **Medium** | Flet Charts package available |
| Tree Views | **Medium** | Build with `ft.Column` + recursion |

---

## 5. Migration Phases

### Phase 1: Foundation (Weeks 1-2)

**Goal**: Establish Flet infrastructure without breaking existing app

1. **Add Flet dependency** to `pyproject.toml`
2. **Create `FletSignalBridge`** base class
3. **Create `FletAppContext`** factory
4. **Implement design token adapter** for Flet theming
5. **Create proof-of-concept screen** (Settings dialog)

**Deliverables**:
- `src/shared/infra/signal_bridge/flet_base.py`
- `design_system/flet/tokens.py`
- Working settings dialog in Flet

### Phase 2: Shared Components (Weeks 3-5)

**Goal**: Migrate design system atoms and molecules

1. **Migrate atoms** (Button, Input, Label, etc.)
2. **Migrate molecules** (SearchBar, LineNumberGutter, etc.)
3. **Create Flet storybook** for component testing
4. **Validate event flow** with unit tests

**Deliverables**:
- `design_system/flet/components.py`
- `design_system/flet/storybook/`
- Component test suite

### Phase 3: Context-by-Context Migration (Weeks 6-12)

**Goal**: Migrate each bounded context's presentation layer

#### 3a. Settings Context (Week 6) - Lowest Risk
- Settings dialog
- Theme switching

#### 3b. Projects Context (Week 7)
- Project selection screen
- Project creation dialog

#### 3c. Sources Context (Weeks 8-9)
- File manager screen
- Source table
- Folder tree

#### 3d. Cases Context (Week 10)
- Case manager screen
- Case table
- Attribute management

#### 3e. Coding Context (Weeks 11-12) - Highest Complexity
- Text coding screen
- Code tree panel
- Text editor panel
- Media player
- AI suggestion panel

### Phase 4: Integration & Polish (Weeks 13-14)

**Goal**: Complete integration and optimize

1. **Remove Qt dependencies** from presentation layer
2. **Performance optimization** (rendering, memory)
3. **Cross-platform testing** (Windows, macOS, Linux)
4. **Accessibility audit**
5. **Documentation update**

---

## 6. Risk Assessment

### 6.1 High-Risk Areas

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Text Editor** | Core feature | Evaluate Flet WebView with CodeMirror |
| **PDF Viewer** | Essential for sources | Use embedded WebView with PDF.js |
| **VLC Integration** | Media playback | Flet's native Audio/Video or WebView |
| **Performance** | Large codebases | Profile early, optimize control tree |
| **Accessibility** | Compliance | Flet's a11y support is improving |

### 6.2 Medium-Risk Areas

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Thread Safety** | Background operations | Use Flet's async model consistently |
| **Drag & Drop** | UX feature | Flet supports drag/drop operations |
| **Clipboard** | Copy/paste codes | Flet has clipboard API |
| **System Tray** | Desktop integration | May need platform-specific code |

### 6.3 Low-Risk Areas

- Data tables
- Basic forms
- Navigation
- Dialogs/modals
- Theme switching

---

## 7. Benefits of Migration

### 7.1 Cross-Platform Advantages

| Benefit | Current (Qt) | With Flet |
|---------|--------------|-----------|
| Web deployment | Not possible | Native support |
| Mobile apps | Limited | Full iOS/Android |
| Package size | ~100MB | ~30MB (web) |
| Installation | Requires Qt | Pure Python or web |

### 7.2 Developer Experience

| Aspect | Current | With Flet |
|--------|---------|-----------|
| Hot reload | Limited | Full support |
| Component model | QWidget subclassing | Dataclass controls |
| Styling | QSS (CSS-like) | Python-native + CSS |
| Async | QThread complexity | Native async/await |

### 7.3 Maintenance

| Aspect | Current | With Flet |
|--------|---------|-----------|
| Dependencies | PySide6 + many | Flet (includes Flutter) |
| Licensing | LGPL complexity | MIT (Flet) |
| Updates | Qt release cycle | Rapid Flet releases |

---

## 8. EventBus Integration Code Examples

### 8.1 FletSignalBridge Implementation

```python
# src/shared/infra/signal_bridge/flet_base.py

from dataclasses import dataclass
from typing import Any, Callable, Dict
import flet as ft

from src.shared.infra.event_bus import EventBus, Subscription


@dataclass
class FletSignalBridge:
    """Bridge between EventBus domain events and Flet UI updates."""

    event_bus: EventBus
    page: ft.Page | None = None

    _subscriptions: list[Subscription] = None
    _handlers: Dict[str, list[Callable]] = None

    def __post_init__(self):
        self._subscriptions = []
        self._handlers = {}

    def bind_page(self, page: ft.Page) -> None:
        """Bind to Flet page for UI updates."""
        self.page = page

    def register_handler(
        self,
        event_type: str,
        handler: Callable[[Any], None]
    ) -> None:
        """Register UI handler for domain event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
            # Subscribe to EventBus once per event type
            sub = self.event_bus.subscribe(
                event_type,
                lambda e: self._dispatch(event_type, e)
            )
            self._subscriptions.append(sub)
        self._handlers[event_type].append(handler)

    def _dispatch(self, event_type: str, event: Any) -> None:
        """Dispatch event to all registered handlers."""
        for handler in self._handlers.get(event_type, []):
            try:
                handler(event)
            except Exception as e:
                print(f"Handler error for {event_type}: {e}")

        # Trigger UI update
        if self.page:
            self.page.update()

    def cleanup(self) -> None:
        """Unsubscribe all handlers."""
        for sub in self._subscriptions:
            sub.cancel()
        self._subscriptions.clear()
        self._handlers.clear()
```

### 8.2 Context-Specific Bridge

```python
# src/contexts/coding/interface/flet_signal_bridge.py

from dataclasses import dataclass
from typing import Callable

from src.shared.infra.signal_bridge.flet_base import FletSignalBridge
from src.contexts.coding.core.events import (
    CodeCreated, CodeDeleted, SegmentCoded
)


@dataclass
class CodingFletBridge(FletSignalBridge):
    """Coding context signal bridge for Flet."""

    # Callback registrations
    on_code_created: Callable | None = None
    on_code_deleted: Callable | None = None
    on_segment_coded: Callable | None = None

    def start(self) -> None:
        """Register all event handlers."""
        if self.on_code_created:
            self.register_handler("coding.code_created", self.on_code_created)
        if self.on_code_deleted:
            self.register_handler("coding.code_deleted", self.on_code_deleted)
        if self.on_segment_coded:
            self.register_handler("coding.segment_coded", self.on_segment_coded)
```

### 8.3 Usage in Flet Screen

```python
# src/contexts/coding/presentation/flet/text_coding_screen.py

import flet as ft
from src.shared.infra.app_context import AppContext


class TextCodingScreen(ft.UserControl):
    """Text coding screen implemented in Flet."""

    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self.bridge = CodingFletBridge(
            event_bus=ctx.event_bus,
            on_code_created=self._handle_code_created,
            on_code_deleted=self._handle_code_deleted,
            on_segment_coded=self._handle_segment_coded,
        )
        self._codes: list = []

    def did_mount(self):
        """Lifecycle: control mounted to page."""
        self.bridge.bind_page(self.page)
        self.bridge.start()
        self._load_initial_data()

    def will_unmount(self):
        """Lifecycle: control about to unmount."""
        self.bridge.cleanup()

    def _handle_code_created(self, event: CodeCreated) -> None:
        """React to code creation event."""
        self._codes.append({
            "id": event.code_id,
            "name": event.name,
            "color": event.color,
        })
        # UI update triggered automatically by bridge

    def _handle_code_deleted(self, event: CodeDeleted) -> None:
        """React to code deletion event."""
        self._codes = [c for c in self._codes if c["id"] != event.code_id]

    def _handle_segment_coded(self, event: SegmentCoded) -> None:
        """React to segment coding event."""
        # Update highlights, etc.
        pass

    def build(self):
        """Build the control tree."""
        return ft.Column([
            ft.Text("Text Coding", size=24),
            ft.Row([
                self._build_codes_panel(),
                self._build_editor_panel(),
            ], expand=True),
        ])

    def _build_codes_panel(self):
        return ft.Container(
            content=ft.ListView([
                ft.ListTile(
                    title=ft.Text(code["name"]),
                    leading=ft.Container(
                        bgcolor=code["color"],
                        width=20,
                        height=20,
                        border_radius=4,
                    ),
                )
                for code in self._codes
            ]),
            width=250,
        )

    def _build_editor_panel(self):
        return ft.Container(
            content=ft.Text("Editor placeholder"),
            expand=True,
        )
```

---

## 9. Decision Matrix

| Criterion | Weight | Qt Score | Flet Score | Notes |
|-----------|--------|----------|------------|-------|
| Cross-platform | 20% | 7 | 10 | Flet wins with web/mobile |
| EventBus compat | 25% | 10 | 9 | Both work well |
| Component richness | 15% | 10 | 7 | Qt more mature |
| Text editing | 15% | 10 | 5 | Qt has QTextEdit |
| Dev experience | 10% | 6 | 9 | Flet hot reload |
| Maintenance | 10% | 7 | 8 | Flet simpler deps |
| Performance | 5% | 9 | 8 | Both good |
| **Weighted Total** | 100% | **8.3** | **8.0** |

**Interpretation**: Scores are close. Migration makes sense if web/mobile deployment is a priority. The EventBus architecture is fully compatible with both.

---

## 10. Recommendations

### 10.1 Proceed with Migration If:

1. **Web deployment** is a requirement
2. **Mobile apps** are planned
3. **Simpler dependency management** is valued
4. **Team is comfortable** with newer framework

### 10.2 Stay with Qt If:

1. **Desktop-only** is acceptable
2. **Complex text editing** is critical path
3. **Stability** over innovation is preferred
4. **Qt expertise** already exists in team

### 10.3 Hybrid Approach (Recommended for Evaluation):

1. **Build proof-of-concept** with Settings context
2. **Evaluate text editor options** (WebView + CodeMirror)
3. **Benchmark performance** with realistic data
4. **Make final decision** after Phase 1

---

## 11. Appendix

### A. Flet Resources

- [Flet Documentation](https://docs.flet.dev/)
- [Flet 1.0 Alpha Announcement](https://flet.dev/blog/introducing-flet-1-0-alpha/)
- [Flet GitHub](https://github.com/flet-dev/flet)
- [Flet Controls Reference](https://docs.flet.dev/controls/)

### B. Related QualCoder Files

- EventBus: `src/shared/infra/event_bus.py`
- Signal Bridge: `src/shared/infra/signal_bridge/base.py`
- Design Tokens: `design_system/tokens.py`
- Domain Events: `src/contexts/*/core/events.py`

### C. Migration Checklist

- [ ] Add Flet dependency
- [ ] Create FletSignalBridge base
- [ ] Migrate design tokens
- [ ] Build POC with Settings
- [ ] Evaluate text editor solution
- [ ] Migrate each context
- [ ] Remove Qt dependencies
- [ ] Cross-platform testing
- [ ] Performance optimization
- [ ] Documentation update
