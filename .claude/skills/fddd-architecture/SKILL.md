---
name: fddd-architecture
description: |
  Functional Domain-Driven Design patterns for QualCoder v2. Implements the
  Functional Core / Imperative Shell architecture with PyQt6 Signal Bridge.

  **Invoke when:**
  - Implementing domain entities, events, or derivers
  - Creating command handlers (controllers)
  - Setting up Signal Bridge for UI reactivity
  - Writing policies (event-driven side effects)
  - Understanding the layer architecture

  **Provides:**
  - Pattern templates for entities, events, derivers
  - Signal Bridge implementation guide
  - Command handler (controller) structure
  - Policy configuration patterns
  - Mapping from PensionBee DDD Workshop (TypeScript) to Python
---

# QualCoder v2: Functional DDD Architecture

Functional Domain-Driven Design patterns based on the PensionBee DDD Workshop,
adapted for Python/PyQt6.

## Reference Material

- `docs/FUNCTIONAL_DDD_DESIGN.md` - Full architecture specification
- `docs/AGENT_CONTEXT_DESIGN.md` - Agent integration and Signal Bridge
- `ddd-workshop/` - PensionBee TypeScript reference (submodule, `final` branch)

---

## Core Principle: Functional Core / Imperative Shell

```
┌─────────────────────────────────────────────────────────────────┐
│  Imperative Shell (I/O, side effects)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Controllers │  │ Repositories│  │ Signal Bridge → PyQt6  │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
│         │                │                     │               │
│         ▼                ▼                     ▼               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Functional Core                         │   │
│  │  Entities │ Events │ Invariants │ Derivers              │   │
│  │  (Pure, no I/O, fully testable)                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Pattern 1: Entity (Immutable Data)

Entities are **frozen dataclasses** with Pydantic validation.

```python
# src/domain/coding/entities.py
from pydantic import Field
from pydantic.dataclasses import dataclass
from domain.shared.types import CodeId, CategoryId, CoderId

@dataclass(frozen=True)
class Code:
    """Aggregate root for the Coding context."""
    code_id: CodeId
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    memo: str | None = None
    category_id: CategoryId | None = None
    owner: CoderId
```

**Key points:**
- `frozen=True` ensures immutability
- Pydantic provides runtime validation
- Use typed IDs (`CodeId`, not `int`)

---

## Pattern 2: Events (Success + Failure)

Events are **discriminated unions** - either success or failure.

```python
# src/domain/coding/events.py
from dataclasses import dataclass
from datetime import datetime
from domain.shared.events import DomainEvent

# Success Events
@dataclass(frozen=True)
class CodeCreated(DomainEvent):
    event_type: str = "coding.code_created"
    code_id: CodeId
    name: str
    color: str
    category_id: CategoryId | None
    owner: CoderId

@dataclass(frozen=True)
class SegmentCoded(DomainEvent):
    event_type: str = "coding.segment_coded"
    segment_id: SegmentId
    code_id: CodeId
    source_id: SourceId
    start_pos: int
    end_pos: int
    selected_text: str

# Failure Events (include reason in type)
@dataclass(frozen=True)
class CodeNotCreated(DomainEvent):
    event_type: str = "coding.code_not_created/name_exists"
    name: str

@dataclass(frozen=True)
class SegmentNotCoded(DomainEvent):
    event_type: str = "coding.segment_not_coded/invalid_position"
    source_id: SourceId
    start_pos: int
    end_pos: int
```

**Naming convention:** `{Action}` for success, `{Action}Not{Done}/{Reason}` for failure.

---

## Pattern 3: Invariants (Pure Predicates)

Invariants are **pure boolean functions** that check business rules.

```python
# src/domain/coding/invariants.py

def is_code_name_unique(name: str, existing_codes: list[Code]) -> bool:
    """No two codes can have the same name."""
    return not any(c.name.lower() == name.lower() for c in existing_codes)

def is_hierarchy_acyclic(
    category_id: CategoryId,
    new_parent_id: CategoryId,
    all_categories: list[Category]
) -> bool:
    """Moving a category must not create a cycle."""
    # Walk up from new_parent, ensure we don't hit category_id
    ...

def is_segment_within_bounds(start: int, end: int, source_length: int) -> bool:
    """Segment positions must be within source bounds."""
    return 0 <= start < end <= source_length
```

---

## Pattern 4: Deriver (Pure Function → Event)

Derivers are **pure functions** that compose invariants and return events.

```python
# src/domain/coding/derivers.py
from domain.shared.types import Result, Success, Failure

def derive_create_code_event(
    command: CreateCodeCommand,
    state: CodingState
) -> CodeCreated | CodeNotCreated:
    """
    Pure function: command + state → event
    No I/O, no side effects, fully testable.
    """
    # Check invariants
    if not is_code_name_unique(command.name, state.existing_codes):
        return CodeNotCreated(name=command.name)

    # Return success event
    return CodeCreated(
        code_id=generate_code_id(),
        name=command.name,
        color=command.color or generate_random_color(),
        category_id=command.category_id,
        owner=command.owner,
    )
```

**The 5-step command handler pattern (from PensionBee):**

1. Parse/validate command data
2. Fetch state from repository
3. Call deriver (pure) → get event
4. Persist changes (if success)
5. Publish event

---

## Pattern 5: Controller (Command Handler)

Controllers live in the **Imperative Shell** and orchestrate I/O.

```python
# src/application/coding/controller.py
from domain.coding.derivers import derive_create_code_event
from domain.coding.events import CodeCreated, CodeNotCreated

class CodingController:
    def __init__(
        self,
        repository: CodingRepository,
        event_bus: EventBus,
    ):
        self._repo = repository
        self._event_bus = event_bus

    async def create_code(self, command: CreateCodeCommand) -> CodeCreated | CodeNotCreated:
        # Step 1: Command already validated by Pydantic

        # Step 2: Fetch state
        existing_codes = await self._repo.get_codes_by_project(command.project_id)
        state = CodingState(existing_codes=existing_codes)

        # Step 3: Derive event (PURE - no I/O)
        event = derive_create_code_event(command, state)

        # Step 4: Persist (if success)
        match event:
            case CodeCreated():
                code = Code(
                    code_id=event.code_id,
                    name=event.name,
                    color=event.color,
                    category_id=event.category_id,
                    owner=event.owner,
                )
                await self._repo.save_code(code)

        # Step 5: Publish event
        self._event_bus.publish(event)

        return event
```

---

## Pattern 6: Repository (Persistence Abstraction)

```python
# src/domain/coding/repository.py (Protocol)
from typing import Protocol

class CodingRepository(Protocol):
    async def save_code(self, code: Code) -> None: ...
    async def get_code(self, code_id: CodeId) -> Code | None: ...
    async def get_codes_by_project(self, project_id: ProjectId) -> list[Code]: ...
    async def delete_code(self, code_id: CodeId) -> None: ...

# src/infrastructure/coding/sqlite_repository.py (Implementation)
class SqliteCodingRepository:
    def __init__(self, connection: Connection):
        self._conn = connection

    async def save_code(self, code: Code) -> None:
        await self._conn.execute(
            "INSERT INTO code_name (cid, name, color, ...) VALUES (?, ?, ?, ...)",
            (code.code_id, code.name, code.color, ...)
        )
```

---

## Pattern 7: Policy (Reactive Event Handler)

Policies react to events and trigger cross-aggregate side effects.

```python
# src/application/coding/policies.py

class CodingPolicies:
    def __init__(self, event_bus: EventBus, controller: CodingController):
        self._controller = controller
        # Subscribe to events
        event_bus.subscribe("coding.code_deleted", self._on_code_deleted)
        event_bus.subscribe("coding.codes_merged", self._on_codes_merged)

    async def _on_code_deleted(self, event: CodeDeleted) -> None:
        """When a code is deleted, remove orphaned segments."""
        await self._controller.remove_segments_for_code(event.code_id)

    async def _on_codes_merged(self, event: CodesMerged) -> None:
        """When codes are merged, update AI embeddings."""
        await self._ai_service.reindex_code(event.target_code_id)
```

---

## Pattern 8: Signal Bridge (Qt Integration)

The Signal Bridge converts domain events to PyQt6 signals for thread-safe UI updates.

```python
# src/application/signal_bridge/base.py
from PyQt6.QtCore import QObject, pyqtSignal, QMetaObject, Qt

class BaseSignalBridge(QObject):
    """Base class for all context-specific signal bridges."""

    # Common signal for activity feed
    activity_logged = pyqtSignal(object)

    def __init__(self, event_bus: EventBus):
        super().__init__()
        self._event_bus = event_bus
        self._signal_map: dict[str, pyqtSignal] = {}

    def _emit_threadsafe(self, signal: pyqtSignal, payload: object) -> None:
        """Thread-safe emission via QueuedConnection."""
        QMetaObject.invokeMethod(
            self,
            "_do_emit",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(object, signal),
            Q_ARG(object, payload),
        )

    @pyqtSlot(object, object)
    def _do_emit(self, signal: pyqtSignal, payload: object) -> None:
        signal.emit(payload)


# src/application/signal_bridge/coding_bridge.py
class CodingSignalBridge(BaseSignalBridge):
    # Context-specific signals
    code_created = pyqtSignal(object)
    code_deleted = pyqtSignal(object)
    segment_coded = pyqtSignal(object)

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
        # Subscribe to domain events
        event_bus.subscribe("coding.code_created", self._on_code_created)
        event_bus.subscribe("coding.segment_coded", self._on_segment_coded)

    def _on_code_created(self, event: CodeCreated) -> None:
        payload = CodeCreatedPayload(
            code_id=event.code_id,
            name=event.name,
            color=event.color,
            is_ai_action=event.session_id != "local",
        )
        self._emit_threadsafe(self.code_created, payload)
```

---

## File Structure

```
src/
├── domain/                          # Functional Core (PURE)
│   ├── shared/
│   │   ├── types.py                 # Result, IDs, base types
│   │   ├── events.py                # DomainEvent base class
│   │   └── identifiers.py           # Typed ID generation
│   │
│   └── coding/                      # Bounded Context
│       ├── entities.py              # Code, Segment, Category
│       ├── events.py                # CodeCreated, SegmentCoded, etc.
│       ├── derivers.py              # derive_create_code_event(), etc.
│       └── invariants.py            # is_code_name_unique(), etc.
│
├── application/                     # Imperative Shell
│   ├── event_bus.py                 # Simple pub/sub
│   ├── signal_bridge/
│   │   ├── base.py                  # BaseSignalBridge (QC-003.01)
│   │   ├── coding_bridge.py         # CodingSignalBridge (QC-006.04)
│   │   └── payloads.py              # UI payload DTOs
│   │
│   └── coding/
│       ├── controller.py            # CodingController
│       ├── policies.py              # CodingPolicies
│       └── queries.py               # Read-side query service
│
├── infrastructure/
│   └── coding/
│       └── sqlite_repository.py     # SqliteCodingRepository
│
└── presentation/
    └── coding/
        ├── code_tree_widget.py      # Connects to CodingSignalBridge
        └── source_view_widget.py
```

---

## Backlog Tasks Reference

| Task | Description |
|------|-------------|
| QC-003.01 | Base Signal Bridge Infrastructure |
| QC-006.04 | Coding Signal Bridge |
| QC-010.06 | Source Signal Bridge |
| QC-014.05 | Case Signal Bridge |
| QC-020.06 | Agent Signal Bridge |
| QC-024.05 | Collaboration Signal Bridge |

---

## TypeScript → Python Mapping

| TypeScript (PensionBee) | Python (QualCoder) |
|-------------------------|-------------------|
| `z.object({...})` (Zod) | `@dataclass(frozen=True)` + Pydantic |
| `type Event = { type, payload }` | `@dataclass` with `event_type` field |
| `deriveEvent(data, state): Event` | Same pattern, type hints |
| `handleX(command): Promise<Event>` | `async def create_x(command) -> Event` |
| `EventEmitter` | Custom `EventBus` class |
| `configurePolicy({ event, actions })` | Class with `event_bus.subscribe()` |

---

## Testing Strategy

```python
# Derivers are pure - easy to test
def test_derive_create_code_returns_failure_when_name_exists():
    command = CreateCodeCommand(name="Anxiety", ...)
    state = CodingState(existing_codes=[Code(name="Anxiety", ...)])

    event = derive_create_code_event(command, state)

    assert isinstance(event, CodeNotCreated)
    assert event.event_type == "coding.code_not_created/name_exists"

# Invariants are pure - easy to test
def test_is_code_name_unique_returns_false_for_duplicate():
    codes = [Code(name="Anxiety", ...)]

    assert is_code_name_unique("anxiety", codes) is False  # case-insensitive
    assert is_code_name_unique("Depression", codes) is True
```

---

## Quick Reference: The 5-Step Pattern

Every command handler follows this pattern:

```python
async def handle_command(self, command: Command) -> Event:
    # 1. Validate (Pydantic does this automatically)

    # 2. Fetch state
    state = await self._build_state(command)

    # 3. Derive event (PURE - call domain function)
    event = derive_event(command, state)

    # 4. Persist (only on success)
    if isinstance(event, SuccessEvent):
        await self._repo.save(...)

    # 5. Publish
    self._event_bus.publish(event)

    return event
```

This keeps I/O at the edges and business logic pure and testable.
