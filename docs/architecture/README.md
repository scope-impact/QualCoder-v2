# QualCoder v2 Architecture

This document explains the architectural patterns used in QualCoder v2 and why they exist.

## Table of Contents

1. [Overview](#overview)
2. [The Problem We're Solving](#the-problem-were-solving)
3. [Architectural Layers](#architectural-layers)
4. [Core Patterns](#core-patterns)
5. [Data Flow](#data-flow)
6. [Component Reference](#component-reference)
7. [Bounded Contexts](#bounded-contexts)
8. [Design Decisions](#design-decisions)

---

## Overview

QualCoder v2 uses **Functional Domain-Driven Design (fDDD)** - an architectural approach that combines:

- **Domain-Driven Design** for modeling complex business logic
- **Functional Programming** for testability and composability
- **Event-Driven Architecture** for loose coupling and real-time updates

### Key Principles

| Principle | Implementation |
|-----------|----------------|
| Pure domain logic | Invariants and Derivers have no side effects |
| Immutable data | Frozen dataclasses, Value Objects |
| Explicit effects | All state changes expressed as Events |
| Type safety | Runtime validation + type hints |
| Strict layering | Presentation → Application → Domain → Infrastructure |

---

## The Problem We're Solving

QualCoder is a qualitative research tool where users apply semantic "codes" to research data. This presents several challenges:

### 1. Complex Business Rules

```
- Code names must be unique (case-insensitive)
- Category hierarchies cannot have cycles
- Text positions must be within source bounds
- Codes with segments require confirmation to delete
- Merged codes must both exist and be different
```

### 2. Real-Time UI Updates

When a code is applied, the UI must instantly:
- Highlight the coded text
- Update the code tree segment count
- Show the action in the activity feed
- Invalidate cached analysis reports

### 3. Multi-Context Communication

Nine bounded contexts need to react to each other's events:
- Coding events trigger Analysis recalculation
- Source changes affect Coding segments
- AI actions must appear in the activity feed

### 4. Testability

Business rules must be testable without:
- Database connections
- PyQt6 UI components
- File system access

---

## Architectural Layers

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation                         │
│              (PyQt6 Widgets, Screens)                   │
├─────────────────────────────────────────────────────────┤
│                    Application                          │
│      (Controllers, EventBus, SignalBridge, Queries)     │
├─────────────────────────────────────────────────────────┤
│                      Domain                             │
│    (Entities, Value Objects, Invariants, Derivers)      │
├─────────────────────────────────────────────────────────┤
│                   Infrastructure                        │
│           (Repositories, SQLite, File I/O)              │
└─────────────────────────────────────────────────────────┘
```

### Layer Dependencies

```
Presentation  →  Application  →  Domain  ←  Infrastructure
                     ↓
              Infrastructure
```

- **Domain** has no dependencies (pure Python)
- **Application** depends on Domain
- **Infrastructure** implements Domain interfaces
- **Presentation** depends on Application

---

## Core Patterns

### 1. Invariants (Business Rule Predicates)

Pure functions that answer: **"Is this allowed?"**

```python
# src/domain/coding/invariants.py

def is_valid_code_name(name: str) -> bool:
    """Check that a code name is valid."""
    return is_non_empty_string(name) and is_within_length(name, 1, 100)

def is_code_name_unique(
    name: str,
    existing_codes: Iterable[Code],
    exclude_code_id: Optional[CodeId] = None,
) -> bool:
    """Check that a code name is unique (case-insensitive)."""
    for code in existing_codes:
        if exclude_code_id and code.id == exclude_code_id:
            continue
        if code.name.lower() == name.lower():
            return False
    return True

def is_category_hierarchy_valid(
    category_id: CategoryId,
    new_parent_id: Optional[CategoryId],
    categories: Iterable[Category],
) -> bool:
    """Check that moving a category won't create a cycle."""
    # ... cycle detection logic
```

**Characteristics:**
- Pure functions (no side effects)
- Return `bool`
- Named with `is_*` or `can_*` prefix
- Composable into complex rules

### 2. Derivers (Event Derivation Functions)

Pure functions that answer: **"What happened?"**

```python
# src/domain/coding/derivers.py

def derive_create_code(
    name: str,
    color: Color,
    category_id: Optional[CategoryId],
    memo: Optional[str],
    existing_codes: Iterable[Code],
    existing_categories: Iterable[Category],
) -> Result[CodeCreated, FailureReason]:
    """
    Derive a CodeCreated event from a create code command.

    Composes invariants to validate, returns Success(event) or Failure(reason).
    """
    # Validate name
    if not is_valid_code_name(name):
        return Failure(EmptyName())

    # Check uniqueness
    if not is_code_name_unique(name, existing_codes):
        return Failure(DuplicateName(name))

    # Check category exists (if specified)
    if category_id and not does_category_exist(category_id, existing_categories):
        return Failure(CategoryNotFound(category_id))

    # All invariants pass - derive the event
    return Success(CodeCreated(
        code_id=CodeId.new(),
        name=name,
        color=color,
        category_id=category_id,
        memo=memo,
    ))
```

**Characteristics:**
- Pure functions (no I/O, no side effects)
- Compose invariants for validation
- Return `Success[Event]` or `Failure[Reason]`
- Contain all business logic for an operation

### 3. Result Type (Success | Failure)

Explicit success/failure handling without exceptions:

```python
# src/domain/shared/types.py

@dataclass(frozen=True)
class Success(Generic[T]):
    value: T

    def is_success(self) -> bool:
        return True

    def map(self, fn: Callable[[T], T]) -> Result[T, E]:
        return Success(fn(self.value))

@dataclass(frozen=True)
class Failure(Generic[E]):
    error: E

    def is_success(self) -> bool:
        return False

Result = Union[Success[T], Failure[E]]
```

**Usage:**
```python
result = derive_create_code(name, color, ...)

if result.is_success():
    event = result.unwrap()
    repository.save(event)
    event_bus.publish(event)
else:
    error = result.error
    show_error_to_user(error.message)
```

### 4. Domain Events

Immutable records of what happened:

```python
@dataclass(frozen=True)
class CodeCreated(DomainEvent):
    code_id: CodeId
    name: str
    color: Color
    category_id: Optional[CategoryId]
    memo: Optional[str]

    event_type: str = "coding.code_created"

@dataclass(frozen=True)
class SegmentCoded(DomainEvent):
    segment_id: SegmentId
    source_id: SourceId
    code_id: CodeId
    position: TextPosition
    selected_text: str

    event_type: str = "coding.segment_coded"
```

**Characteristics:**
- Immutable (frozen dataclass)
- Past tense naming (`Created`, `Deleted`, `Merged`)
- Contains all data needed to understand what happened
- Includes `event_type` for routing

### 5. EventBus (Pub/Sub)

Synchronous event distribution:

```python
# src/application/event_bus.py

class EventBus:
    def subscribe(self, event_type: str, handler: Callable) -> Subscription:
        """Subscribe to events by type string."""

    def subscribe_type(self, event_class: type, handler: Callable) -> Subscription:
        """Subscribe to events by class."""

    def subscribe_all(self, handler: Callable) -> Subscription:
        """Subscribe to all events (for logging, audit)."""

    def publish(self, event: DomainEvent) -> None:
        """Publish event to all matching subscribers."""
```

**Usage:**
```python
bus = EventBus()

# Subscribe to specific events
bus.subscribe("coding.code_created", handle_code_created)
bus.subscribe_type(SegmentCoded, update_segment_count)

# Subscribe to everything (audit log)
bus.subscribe_all(audit_logger.log)

# Publish
bus.publish(CodeCreated(...))
```

### 6. SignalBridge (Qt Integration)

Thread-safe bridge from domain events to PyQt6 signals:

```python
# src/application/signal_bridge/base.py

class BaseSignalBridge(QObject):
    """
    Bridges domain events to PyQt6 signals.

    - Subscribes to EventBus
    - Converts events to Qt-friendly payloads
    - Emits signals thread-safely (for background operations)
    - Records to activity feed
    """

    # Define Qt signals
    code_created = pyqtSignal(CodeCreatedPayload)
    segment_coded = pyqtSignal(SegmentCodedPayload)

    def _on_event(self, event: DomainEvent) -> None:
        """Convert domain event to signal emission."""
        payload = self._convert_to_payload(event)

        # Thread-safe emission to main thread
        QMetaObject.invokeMethod(
            self,
            "_emit_signal",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(object, payload),
        )
```

**Why it exists:**
- Qt signals must be emitted from the main thread
- Domain events can come from background threads (AI, imports)
- Provides type-safe payloads for UI consumption
- Centralizes activity feed recording

---

## Data Flow

### Complete Flow: Apply Code to Text

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. USER ACTION                                                   │
│    User selects text, clicks "Apply Code: Anxiety"               │
└──────────────────────────────────────────────────────────────────┘
                                 ↓
┌──────────────────────────────────────────────────────────────────┐
│ 2. CONTROLLER (Application Layer)                                │
│                                                                  │
│    def apply_code(code_id, source_id, start, end):               │
│        # Load current state                                      │
│        state = CodingState(                                      │
│            codes=code_repo.get_all(),                            │
│            sources=source_repo.get_all(),                        │
│            segments=segment_repo.get_for_source(source_id),      │
│        )                                                         │
└──────────────────────────────────────────────────────────────────┘
                                 ↓
┌──────────────────────────────────────────────────────────────────┐
│ 3. DERIVER (Domain Layer) - Pure Function                        │
│                                                                  │
│    result = derive_apply_code_to_text(                           │
│        code_id=code_id,                                          │
│        source_id=source_id,                                      │
│        position=TextPosition(start, end),                        │
│        state=state,                                              │
│    )                                                             │
│                                                                  │
│    Internally composes INVARIANTS:                               │
│    ├─ does_code_exist(code_id, state.codes)        → True ✓      │
│    ├─ does_source_exist(source_id, state.sources)  → True ✓      │
│    ├─ is_valid_text_position(position, source)     → True ✓      │
│    └─ Returns Success(SegmentCoded event)                        │
└──────────────────────────────────────────────────────────────────┘
                                 ↓
┌──────────────────────────────────────────────────────────────────┐
│ 4. CONTROLLER HANDLES SUCCESS                                    │
│                                                                  │
│    if result.is_success():                                       │
│        event = result.unwrap()                                   │
│        segment_repo.save(event)          # Persist               │
│        event_bus.publish(event)          # Notify                │
│        return Success(event.segment_id)                          │
└──────────────────────────────────────────────────────────────────┘
                                 ↓
┌──────────────────────────────────────────────────────────────────┐
│ 5. EVENTBUS DISTRIBUTES                                          │
│                                                                  │
│    Subscribers notified synchronously:                           │
│    ├─ SignalBridge._on_segment_coded(event)                      │
│    ├─ AnalysisPolicy.invalidate_cache(event)                     │
│    ├─ AuditLogger.log(event)                                     │
│    └─ AIContext.update_embeddings(event)                         │
└──────────────────────────────────────────────────────────────────┘
                                 ↓
┌──────────────────────────────────────────────────────────────────┐
│ 6. SIGNALBRIDGE EMITS QT SIGNAL                                  │
│                                                                  │
│    payload = SegmentCodedPayload(                                │
│        segment_id=event.segment_id,                              │
│        code_name="Anxiety",                                      │
│        selected_text="I felt worried about...",                  │
│        source_name="Interview_P01.txt",                          │
│    )                                                             │
│    self.segment_coded.emit(payload)  # Thread-safe               │
└──────────────────────────────────────────────────────────────────┘
                                 ↓
┌──────────────────────────────────────────────────────────────────┐
│ 7. UI REACTS                                                     │
│                                                                  │
│    Connected slots update in real-time:                          │
│    ├─ SourceView: Highlights text with code color                │
│    ├─ CodeTree: Increments segment count badge                   │
│    ├─ ActivityFeed: Shows "Applied Anxiety to Interview_P01"     │
│    └─ StatusBar: Updates statistics                              │
└──────────────────────────────────────────────────────────────────┘
```

### Failure Flow

```
User tries to create code "Anxiety" (already exists)
                    ↓
Controller calls: derive_create_code("Anxiety", ...)
                    ↓
Deriver checks: is_code_name_unique("Anxiety", existing_codes)
                    ↓
                Returns False
                    ↓
Deriver returns: Failure(DuplicateName("Anxiety"))
                    ↓
Controller handles failure:
    - No database write
    - No event published
    - Returns error to UI
                    ↓
UI shows: "Code name 'Anxiety' already exists"
```

---

## Component Reference

### Directory Structure

```
src/
├── domain/                     # Pure business logic
│   ├── coding/
│   │   ├── entities.py         # Code, Category, Segment
│   │   ├── invariants.py       # Business rule predicates
│   │   ├── derivers.py         # Event derivation functions
│   │   ├── events.py           # Domain events
│   │   └── tests/              # Unit tests (no mocks needed)
│   └── shared/
│       ├── types.py            # Result, DomainEvent, IDs
│       └── validation.py       # Reusable validation helpers
│
├── application/                # Orchestration
│   ├── event_bus.py            # Pub/sub infrastructure
│   ├── signal_bridge/
│   │   ├── base.py             # Abstract bridge
│   │   ├── payloads.py         # Qt-friendly data objects
│   │   └── thread_utils.py     # Thread-safe helpers
│   ├── controllers/            # Command handlers
│   └── queries/                # Read-side queries
│
├── infrastructure/             # External concerns
│   ├── repositories/           # Database access
│   └── adapters/               # File I/O, external APIs
│
└── presentation/               # PyQt6 UI
    ├── organisms/              # Complex widgets
    ├── pages/                  # Full page layouts
    └── screens/                # Top-level windows
```

### Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `domain/coding/invariants.py` | Business rule predicates | ~410 |
| `domain/coding/derivers.py` | Event derivation logic | ~640 |
| `domain/shared/types.py` | Result type, base event, IDs | ~160 |
| `domain/shared/validation.py` | Reusable validation helpers | ~310 |
| `application/event_bus.py` | Pub/sub infrastructure | ~430 |
| `application/signal_bridge/base.py` | Qt signal bridging | ~430 |

---

## Bounded Contexts

QualCoder v2 is organized into 9 bounded contexts:

```
┌─────────────────────────────────────────────────────────────────┐
│                         CORE DOMAIN                             │
│  ┌─────────────────┐              ┌─────────────────┐           │
│  │     Coding      │──events───→  │    Analysis     │           │
│  │  (apply codes)  │              │ (generate       │           │
│  │                 │              │  insights)      │           │
│  └────────┬────────┘              └─────────────────┘           │
│           │                                                      │
│           │ events                                               │
│           ↓                                                      │
├─────────────────────────────────────────────────────────────────┤
│                      SUPPORTING DOMAIN                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Sources   │  │    Cases    │  │  Projects   │              │
│  │ (documents) │  │ (grouping)  │  │ (lifecycle) │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                  │
│  ┌─────────────────────────────────────────────────┐            │
│  │              Collaboration                       │            │
│  │         (multi-coder workflows)                  │            │
│  └─────────────────────────────────────────────────┘            │
├─────────────────────────────────────────────────────────────────┤
│                       GENERIC DOMAIN                            │
│  ┌─────────────────┐              ┌─────────────────┐           │
│  │   AI Services   │              │     Export      │           │
│  │ (LLM, vectors)  │              │   (reports)     │           │
│  └─────────────────┘              └─────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### Context Integration Patterns

| From → To | Pattern | Description |
|-----------|---------|-------------|
| Coding → Analysis | Published Language | Events define the contract |
| Source → Coding | Open Host Service | Standard segment API |
| Project → Coding | Conformist | Coding adapts to Project |
| AI ↔ Coding | Partnership | Bidirectional collaboration |
| External → Project | Anti-Corruption Layer | Translates formats |

---

## Design Decisions

### Why Functional DDD?

| Concern | Traditional OOP | Functional DDD |
|---------|----------------|----------------|
| Testing | Mocks required | Pure functions, no mocks |
| Side effects | Hidden in methods | Explicit via events |
| State | Mutable objects | Immutable data |
| Composition | Inheritance | Function composition |
| Debugging | Stack traces | Event replay |

### Why Custom EventBus?

Libraries like Blinker and PyPubSub lack:
- `subscribe_all()` for global handlers (audit, logging)
- Event history for debugging
- Type-based subscription by event class
- Tight integration with our event conventions

### Why Custom SignalBridge?

No library exists for this use case:
- Bridges domain events to PyQt6 signals
- Handles Qt's thread-affinity requirements
- Converts to UI-friendly payloads
- Records to activity feed

### Why Custom Result Type?

The `returns` library is a good alternative (see `library-alternatives-analysis.md`), but current implementation:
- Is minimal (~50 lines)
- Avoids external dependency
- Sufficient for current needs

Consider migrating to `returns` for richer composition.

---

## Testing Strategy

### Domain Layer (Pure Functions)

```python
# No mocks needed - just call functions with data

def test_code_name_uniqueness():
    existing = [Code(id=CodeId(1), name="Anxiety", ...)]

    assert is_code_name_unique("Depression", existing) == True
    assert is_code_name_unique("anxiety", existing) == False  # case-insensitive
    assert is_code_name_unique("Anxiety", existing, exclude_code_id=CodeId(1)) == True

def test_derive_create_code_duplicate():
    existing = [Code(id=CodeId(1), name="Anxiety", ...)]

    result = derive_create_code("Anxiety", Color(255, 0, 0), None, None, existing, [])

    assert result.is_failure()
    assert isinstance(result.error, DuplicateName)
```

### Application Layer (Integration)

```python
def test_event_bus_subscription():
    bus = EventBus()
    received = []

    bus.subscribe("coding.code_created", lambda e: received.append(e))
    bus.publish(CodeCreated(...))

    assert len(received) == 1
```

### Presentation Layer (Qt)

```python
def test_signal_bridge_emission(qtbot):
    bridge = CodingSignalBridge()

    with qtbot.waitSignal(bridge.code_created) as blocker:
        bridge._on_event(CodeCreated(...))

    assert blocker.args[0].code_name == "Anxiety"
```

---

## Further Reading

- `FUNCTIONAL_DDD_DESIGN.md` - Complete DDD specification
- `AGENT_CONTEXT_DESIGN.md` - AI integration architecture
- `library-alternatives-analysis.md` - Library evaluation

---

*Architecture documentation for QualCoder v2. Last updated: 2025.*
