# Part 4: Events Flow Through the System

Let's trace how a `CodeCreated` event travels from the deriver to the UI.

## The Journey

When a user creates a Code, the event travels through these layers:

```mermaid
graph LR
    A[ViewModel/MCP Tool] -->|call| B[CommandHandler<br/><i>orchestration</i>]
    B -->|call| C[Deriver<br/><i>pure domain</i>]
    C -->|return event| B
    B -->|publish| D[EventBus<br/><i>pub/sub</i>]
    D -->|subscribe| E[SignalBridge<br/><i>Qt signals</i>]
    E -->|emit| F[UI Widget<br/><i>update</i>]
```

Let's trace each step.

## Step 1: CommandHandler Orchestrates the Flow

Command handlers live in `src/contexts/{context}/core/commandHandlers/`. They orchestrate the operation:

```python
# In src/contexts/coding/core/commandHandlers/create_code.py
def create_code(
    command: CreateCodeCommand,
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    segment_repo: SegmentRepository,
    event_bus: EventBus,
) -> OperationResult:
    """
    Create a new code in the codebook.

    This is the USE CASE - it orchestrates:
    1. Load state (I/O)
    2. Call deriver (pure domain)
    3. Handle failure
    4. Persist (I/O)
    5. Publish event (I/O)
    """
    # 1. Build state from repositories
    state = build_coding_state(code_repo, category_repo, segment_repo)

    # 2. Call the pure deriver
    result = derive_create_code(
        name=command.name,
        color=color,
        memo=command.memo,
        category_id=category_id,
        owner=None,
        state=state,
    )

    # 3. Handle failure
    if isinstance(result, FailureEvent):
        event_bus.publish(result)  # Publish for policies
        return OperationResult.from_failure(result)

    event: CodeCreated = result

    # 4. Persist (side effect)
    code = Code(
        id=event.code_id,
        name=event.name,
        color=event.color,
        memo=event.memo,
        category_id=event.category_id,
    )
    code_repo.save(code)

    # 5. Publish event (side effect)
    event_bus.publish(event)

    return OperationResult.ok(
        data=code,
        rollback=DeleteCodeCommand(code_id=code.id.value),
    )
```

Key points:
- The **deriver is pure** - it just computes
- The **command handler handles side effects** - persistence, publishing
- State is built **before** calling the deriver
- Returns `OperationResult` with data, error info, and rollback command

## Step 2: EventBus Receives and Routes

Look at `src/shared/infra/event_bus.py`:

```python
class EventBus:
    def publish(self, event: Any) -> None:
        """Publish an event to all matching subscribers."""
        event_type = self._get_event_type(event)

        # Get handlers for this event type
        type_handlers = list(self._handlers.get(event_type, []))

        # Invoke each handler
        for handler in type_handlers:
            handler(event)
```

The EventBus:
1. Extracts the event type (e.g., `"coding.code_created"`)
2. Finds all subscribers for that type
3. Calls each handler synchronously

Event type is defined as a class variable on the event:

```python
@dataclass(frozen=True)
class CodeCreated(DomainEvent):
    event_type: ClassVar[str] = "coding.code_created"
```

## Step 3: SignalBridge Receives Event

The SignalBridge subscribes to domain events and converts them to Qt signals.

From `src/shared/infra/signal_bridge/base.py`:

```python
class BaseSignalBridge(QObject, ABC):
    def start(self) -> None:
        """Start listening to domain events."""
        for event_type in self._converters:
            handler = self._make_handler(event_type)
            self._event_bus.subscribe(event_type, handler)

    def _dispatch_event(self, event_type: str, event: Any) -> None:
        """Dispatch a domain event to the appropriate signal."""
        converter, signal_name = self._converters[event_type]

        # Convert event to UI-friendly payload
        payload = converter.convert(event)

        # Get the signal
        signal = self._signals.get(signal_name)

        # Emit thread-safely
        self._emit_threadsafe(signal, payload)
```

A context-specific bridge might look like:

```python
class CodingSignalBridge(BaseSignalBridge):
    # Define Qt signals
    code_created = Signal(object)
    code_deleted = Signal(object)
    code_renamed = Signal(object)

    def _get_context_name(self) -> str:
        return "coding"

    def _register_converters(self) -> None:
        self.register_converter(
            "coding.code_created",
            CodeCreatedConverter(),
            "code_created"  # Signal to emit
        )
```

## Step 4: Converter Transforms Event to Payload

The converter maps domain event fields to UI-friendly payload:

```python
class CodeCreatedConverter:
    def convert(self, event: CodeCreated) -> CodeCreatedPayload:
        return CodeCreatedPayload(
            timestamp=event.occurred_at,
            session_id="local",
            is_ai_action=False,
            event_type="coding.code_created",
            code_id=event.code_id.value,
            name=event.name,
            color_hex=event.color.to_hex(),
            priority=event.priority,  # Include new field
            category_id=event.category_id.value if event.category_id else None,
        )
```

Why convert?
- Domain events use domain types (`CodeId`, `Color`)
- UI needs primitive types (`int`, `str`, `#hex`)
- Payloads are UI-optimized DTOs

## Step 5: Qt Signal Emits (Thread-Safe)

The SignalBridge ensures emission happens on the Qt main thread:

```python
def _emit_threadsafe(self, signal: Any, payload: Any) -> None:
    if is_main_thread():
        # Already on main thread - emit directly
        signal.emit(payload)
    else:
        # Queue for main thread
        QMetaObject.invokeMethod(...)
```

This is critical:
- Domain events might come from background threads (AI agent)
- Qt widgets can only be updated from the main thread
- SignalBridge handles the threading automatically

## Step 6: UI Widget Receives Payload

A Qt widget connects to the signal:

```python
class CodebookTreeView(QTreeView):
    def __init__(self, signal_bridge: CodingSignalBridge):
        super().__init__()
        # Connect to signal
        signal_bridge.code_created.connect(self._on_code_created)

    def _on_code_created(self, payload: CodeCreatedPayload):
        """Handle new code creation."""
        # Add to tree model
        item = QStandardItem(payload.name)
        item.setData(payload.code_id, Qt.ItemDataRole.UserRole)
        item.setForeground(QColor(payload.color_hex))
        self.model().appendRow(item)
```

## Tracing the Full Flow

Let's trace "Create Code with priority=3":

```mermaid
sequenceDiagram
    participant User
    participant Button as Create Button
    participant VM as ViewModel
    participant CH as CommandHandler
    participant Repo as Repository
    participant Der as Deriver
    participant EB as EventBus
    participant SB as SignalBridge
    participant Tree as TreeView
    participant Activity as ActivityPanel

    User->>Button: Click "Create Code"
    Button->>VM: create_code("Theme A", color, priority=3)
    VM->>CH: create_code(command, repos, event_bus)

    Note over CH,Repo: Build State
    CH->>Repo: get_all()
    Repo-->>CH: existing_codes
    CH->>CH: build_coding_state()

    Note over CH,Der: Pure Domain Logic
    CH->>Der: derive_create_code(...)
    Note over Der: is_valid_code_name() ✓<br/>is_code_name_unique() ✓<br/>is_valid_priority(3) ✓
    Der-->>CH: CodeCreated event

    Note over CH,Repo: Persist
    CH->>Repo: save(code)

    Note over CH,Activity: Publish & React
    CH->>EB: publish(CodeCreated)
    CH-->>VM: OperationResult.ok(code, rollback)
    EB->>SB: _dispatch_event(event)
    Note over SB: Convert to payload
    SB->>Tree: code_created.emit(payload)
    SB->>Activity: activity_logged.emit(...)

    Tree->>Tree: Add "Theme A" with priority icon
    Activity->>Activity: Log "Code created"
```

## Observing the Flow

To observe this in practice, you could:

1. **Add logging** to each step
2. **Use EventBus history** (`EventBus(history_size=100)`)
3. **Set breakpoints** in deriver, controller, bridge, widget

## Why This Architecture?

1. **Separation of concerns** - Each layer has one job
2. **Testability** - Deriver tests don't need UI, UI tests don't need domain
3. **Decoupling** - UI doesn't know about derivers, just payloads
4. **Threading** - SignalBridge handles cross-thread communication
5. **Reactivity** - UI automatically updates when events flow

## Summary

Events flow through:

1. **ViewModel/MCP Tool** receives user/AI request
2. **CommandHandler** orchestrates: load state, call deriver, persist, publish
3. **Deriver** (pure function) validates and returns success/failure event
4. **EventBus** routes events to subscribers
5. **SignalBridge** converts events to UI payloads
6. **Qt Signals** emit payloads thread-safely
7. **UI Widgets** update from payloads

Each step is isolated and testable.

## Next Steps

Let's look at how to update the SignalBridge for our new priority field.

**Next:** [Part 5: Adding a SignalBridge Payload](./05-signal-bridge.md)
