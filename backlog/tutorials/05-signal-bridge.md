# Part 5: Adding a SignalBridge Payload

Now let's update the UI integration for our new priority field.

## What are Payloads?

**Payloads** are UI-friendly DTOs (Data Transfer Objects) that carry event data to Qt widgets. They:

- Use primitive types (no domain objects)
- Are immutable (frozen dataclasses)
- Carry metadata for UI rendering (timestamps, session info)

Look at `src/application/signal_bridge/payloads.py`:

```python
@dataclass(frozen=True)
class SignalPayload:
    """Base type for all signal payloads."""
    timestamp: datetime
    session_id: str
    is_ai_action: bool
    event_type: str
```

All payloads inherit from this base.

## Creating a CodeCreatedPayload

For our `CodeCreated` event, we need a payload:

```python
@dataclass(frozen=True)
class CodeCreatedPayload(SignalPayload):
    """Payload for code creation events."""
    code_id: int           # Primitive, not CodeId
    name: str
    color_hex: str         # "#ff0000", not Color
    memo: Optional[str]
    category_id: Optional[int]
    priority: Optional[int]  # NEW field
    owner: Optional[str]
```

Notice:
- `CodeId` becomes `int`
- `Color` becomes `str` (hex)
- Domain types → primitive types

## The Converter Pattern

A **converter** transforms domain events to payloads:

```python
from src.application.signal_bridge.protocols import EventConverter

class CodeCreatedConverter(EventConverter):
    """Converts CodeCreated events to CodeCreatedPayload."""

    def convert(self, event: CodeCreated) -> CodeCreatedPayload:
        return CodeCreatedPayload(
            timestamp=event.occurred_at,
            session_id=getattr(event, 'session_id', 'local'),
            is_ai_action=getattr(event, 'session_id', 'local') != 'local',
            event_type="coding.code_created",
            code_id=event.code_id.value,
            name=event.name,
            color_hex=event.color.to_hex(),
            memo=event.memo,
            category_id=event.category_id.value if event.category_id else None,
            priority=event.priority,  # Pass through new field
            owner=event.owner,
        )
```

The converter:
1. Receives the domain event
2. Extracts and transforms fields
3. Returns a UI-friendly payload

## Registering the Converter

In a context-specific SignalBridge:

```python
class CodingSignalBridge(BaseSignalBridge):
    # Define the Qt signal
    code_created = pyqtSignal(object)

    def _register_converters(self) -> None:
        self.register_converter(
            "coding.code_created",       # Event type to listen for
            CodeCreatedConverter(),       # Converter instance
            "code_created"               # Signal name to emit
        )
```

When `CodeCreated` is published:
1. EventBus routes to SignalBridge
2. SignalBridge calls `CodeCreatedConverter.convert(event)`
3. SignalBridge emits `code_created` signal with the payload

## Why Convert?

You might ask: "Why not just emit the domain event directly?"

### 1. Type Isolation

The UI shouldn't depend on domain types:

```python
# Bad: UI depends on domain
from src.domain.coding.entities import Code, Color
from src.domain.shared.types import CodeId

class TreeView(QWidget):
    def on_code_created(self, event: CodeCreated):
        color = event.color  # Type: Color
        # Must import Color, know its API
```

```python
# Good: UI depends only on primitives
class TreeView(QWidget):
    def on_code_created(self, payload: CodeCreatedPayload):
        color = payload.color_hex  # Type: str
        # Just a string, no domain knowledge needed
```

### 2. Serialization

Payloads with primitives are easy to:
- Log to files
- Send over network (for remote collaboration)
- Store in activity history

### 3. API Stability

Domain events might evolve (add fields, rename things). Payloads provide a stable UI contract.

## Thread Safety

The SignalBridge handles thread-safe emission:

```python
def _emit_threadsafe(self, signal: Any, payload: Any) -> None:
    if is_main_thread():
        signal.emit(payload)
    else:
        # Queue for main thread via Qt's mechanism
        QMetaObject.invokeMethod(
            self,
            "_do_emit",
            Qt.ConnectionType.QueuedConnection,
            payload,
        )
```

This is crucial because:
- AI agents might create Codes from background threads
- Qt widgets can only be updated from the main thread
- The SignalBridge bridges this gap automatically

## Activity Feed Integration

The base SignalBridge also emits to the activity feed:

```python
def _dispatch_event(self, event_type: str, event: Any) -> None:
    # ... convert and emit to specific signal ...

    # Also emit to activity feed
    activity = self._create_activity_item(event, payload)
    if activity:
        self._emit_threadsafe(self.activity_logged, activity)
```

This means every domain event automatically appears in the activity panel.

## Using Payloads in UI

A Qt widget connects to the signal:

```python
class CodebookTreeView(QTreeView):
    def __init__(self, signal_bridge: CodingSignalBridge):
        super().__init__()
        signal_bridge.code_created.connect(self._on_code_created)

    def _on_code_created(self, payload: CodeCreatedPayload):
        """Add new code to tree."""
        item = QStandardItem(payload.name)
        item.setData(payload.code_id, Qt.ItemDataRole.UserRole)
        item.setForeground(QColor(payload.color_hex))

        # NEW: Show priority indicator
        if payload.priority:
            item.setIcon(self._priority_icon(payload.priority))

        self.model().appendRow(item)

    def _priority_icon(self, priority: int) -> QIcon:
        # Return icon based on priority 1-5
        ...
```

The widget:
- Receives the payload (not the domain event)
- Uses primitive types directly
- Has no dependency on domain layer

## Summary

Payloads and converters:

1. **Payloads** are UI-friendly DTOs with primitive types
2. **Converters** transform domain events to payloads
3. **Registration** connects event types to signals
4. **Thread safety** is handled automatically
5. **UI isolation** - widgets don't depend on domain

To add our priority field:
1. Add `priority` to `CodeCreatedPayload`
2. Map `event.priority` in the converter
3. Use `payload.priority` in UI widgets

## Next Steps

Let's see how easy it is to test all of this.

**Next:** [Part 6: Testing Without Mocks](./06-testing.md)
