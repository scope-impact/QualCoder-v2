---
name: developer
description: |
  QualCoder v2 development conventions following DDD-workshop vertical slice architecture.
  AI-agent-first design where both humans and AI are first-class consumers.

  **Invoke when:**
  - Writing domain logic (invariants, derivers, events)
  - Creating use cases and ViewModels
  - Adding PySide6/Qt UI components
  - Adding MCP tools for AI agents
  - Writing tests (unit, E2E with Allure)
---

# QualCoder v2 Developer Guide

## Architecture Overview

Following the **DDD-workshop vertical slice pattern**, each bounded context is a complete vertical slice:

```
src/
├── contexts/{name}/              # Bounded context (vertical slice)
│   ├── core/                     # Domain: invariants, derivers, events (PURE - no I/O)
│   │   ├── commandHandlers/      # Use cases (orchestration)
│   │   ├── entities.py
│   │   ├── events.py
│   │   ├── invariants.py
│   │   └── derivers.py
│   ├── infra/                    # Infrastructure: repositories, schema
│   ├── interface/                # MCP tools for AI agents
│   └── presentation/             # ViewModels, screens, dialogs, pages
│       ├── viewmodels/
│       ├── screens/
│       ├── dialogs/
│       └── pages/
├── shared/                       # Cross-cutting concerns ONLY
│   ├── common/                   # Types, Result monad, failure events
│   ├── core/                     # Shared validation, policies
│   ├── infra/                    # EventBus, AppContext, SignalBridges
│   │   ├── event_bus.py
│   │   ├── app_context.py
│   │   └── signal_bridge/        # Event → Qt Signal bridges
│   │       ├── coding.py
│   │       ├── cases.py
│   │       └── projects.py
│   └── presentation/             # Shared UI components
│       ├── dto.py                # Cross-context DTOs
│       ├── organisms/            # Reusable complex widgets
│       ├── molecules/            # Reusable small widgets
│       ├── templates/            # AppShell, layouts
│       └── services/             # DialogService
design_system/                    # Design tokens, atoms, base components
```

### Bounded Contexts

| Context | Purpose |
|---------|---------|
| `coding` | Code creation, text segments, categories |
| `cases` | Case management, attributes, source links |
| `sources` | File import, source management |
| `folders` | Folder organization |
| `projects` | Project lifecycle, settings |
| `settings` | User preferences |

### Layer Responsibilities

```
┌─────────────────────────────────────────────────────────────────┐
│ Presentation (ViewModel, Screens, MCP Tools)                    │
│ → UI state, AI tool interface, rendering                        │
│ → Location: src/contexts/{name}/presentation/                   │
│ → Shared: src/shared/presentation/ (organisms, templates)       │
├─────────────────────────────────────────────────────────────────┤
│ Application (Command Handlers, EventBus, SignalBridge)          │
│ → Orchestration only, NO business logic                         │
│ → Location: src/contexts/{name}/core/commandHandlers/           │
│ → Shared: src/shared/infra/ (EventBus, SignalBridges)           │
├─────────────────────────────────────────────────────────────────┤
│ Domain (Entities, Derivers, Events, Invariants)                 │
│ → Pure functions, ALL business logic, NO I/O                    │
│ → Location: src/contexts/{name}/core/                           │
├─────────────────────────────────────────────────────────────────┤
│ Infrastructure (Repositories, DB, External Services)            │
│ → Persistence, external APIs                                    │
│ → Location: src/contexts/{name}/infra/                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Principles

### 1. Don't Add Layers You Don't Need

**Delete unnecessary abstractions:**

| Delete | Reason |
|--------|--------|
| Controller Protocol | Single implementation, no value |
| Service/Operations adapter | Pass-through layer, just noise |
| God interfaces (span 4+ contexts) | Split or remove |

**Keep abstractions for:**

| Keep | Reason |
|------|--------|
| Repository Protocol | Testability, failure injection |
| AIProvider Protocol | Multiple backends (OpenAI, Ollama, mock) |
| External service protocols | Auth, sync, third-party APIs |

### 2. AI and UI Are Both Presentation Adapters

```
Human UI ──→ ViewModel ──┐
                         ├──→ Command Handlers ──→ Domain (pure)
AI Agent ──→ MCP Tools ──┘
```

Both call command handlers directly. No intermediate "Operations Layer."

### 3. CQRS: Commands vs Queries

| Operation | Goes Through | Why |
|-----------|--------------|-----|
| Commands (writes) | Command Handlers | Domain logic, events, validation |
| Queries (reads) | Direct to Repo | No business logic needed |

---

## Domain Layer Patterns

### Invariants (Pure Validation)

Pure predicate functions. Named `is_*` or `can_*`.

```python
# src/contexts/coding/core/invariants.py
def is_valid_code_name(name: str) -> bool:
    """Name must be non-empty and <= 100 chars."""
    return is_non_empty_string(name) and is_within_length(name, 1, 100)

def is_code_name_unique(name: str, existing_codes: tuple[Code, ...]) -> bool:
    """Name must not conflict with existing codes (case-insensitive)."""
    return not any(c.name.lower() == name.lower() for c in existing_codes)
```

### State Container (Immutable Context)

```python
@dataclass(frozen=True)
class CodingState:
    """State container for coding context derivers."""
    existing_codes: tuple[Code, ...] = ()
    existing_categories: tuple[Category, ...] = ()
    source_length: int | None = None
```

### Derivers (Pure Event Derivation)

Compose invariants to derive success or failure events:

```python
# src/contexts/coding/core/derivers.py
def derive_create_code(
    cmd: CreateCodeCommand,
    state: CodingState,
) -> CodeCreated | CodeCreationFailed:
    """Derive event from command and state. PURE - no I/O."""
    if not is_valid_code_name(cmd.name):
        return CodeCreationFailed.empty_name()
    if not is_code_name_unique(cmd.name, state.existing_codes):
        return CodeCreationFailed.duplicate_name(cmd.name)
    return CodeCreated(
        code_id=generate_id(),
        name=cmd.name.strip(),
        color=cmd.color,
    )
```

### Domain Events (Immutable Facts)

```python
@dataclass(frozen=True)
class CodeCreated:
    """Success event - past tense naming."""
    event_type: str = "coding.code_created"
    code_id: int
    name: str
    color: str
```

### Failure Events (Rich Context)

```python
@dataclass(frozen=True)
class CodeCreationFailed:
    """Failure with machine-readable code and suggestions."""
    reason: str
    error_code: str
    suggestions: tuple[str, ...] = ()

    @classmethod
    def duplicate_name(cls, name: str) -> CodeCreationFailed:
        return cls(
            reason=f"Code '{name}' already exists",
            error_code="DUPLICATE_NAME",
            suggestions=(
                "Use a different name",
                "Or use the existing code",
            ),
        )
```

---

## Application Layer Patterns

### Use Cases Return Rich Results

```python
@dataclass(frozen=True)
class OperationResult:
    """Rich result serving both UI and AI consumers."""
    success: bool
    data: Any | None = None
    error: str | None = None
    error_code: str | None = None       # Machine-readable
    suggestions: list[str] | None = None # Recovery hints
    rollback_command: Any | None = None  # For undo
```

### Command Handler Pattern (Orchestration Only)

```python
# src/contexts/coding/core/commandHandlers/create_code.py
def create_code(
    cmd: CreateCodeCommand,
    code_repo: CodeRepository,
    event_bus: EventBus,
) -> OperationResult:
    """
    Command handler - orchestration only.

    1. Load state (I/O)
    2. Call domain (pure) - DOMAIN DECIDES
    3. Handle failure
    4. Persist (I/O)
    5. Publish event (I/O)
    """
    # 1. Load state
    state = CodingState(existing_codes=tuple(code_repo.get_all()))

    # 2. Call domain (THE DOMAIN DECIDES)
    event = derive_create_code(cmd, state)

    # 3. Handle failure
    if isinstance(event, CodeCreationFailed):
        return OperationResult(
            success=False,
            error=event.reason,
            error_code=event.error_code,
            suggestions=list(event.suggestions),
        )

    # 4. Persist
    code = Code(id=CodeId(event.code_id), name=event.name, color=Color(event.color))
    code_repo.save(code)

    # 5. Publish event
    event_bus.publish(event)

    return OperationResult(
        success=True,
        data=code,
        rollback_command=DeleteCodeCommand(code_id=event.code_id),
    )
```

### Batch Operations (For AI Efficiency)

```python
def batch_apply_codes(
    commands: list[ApplyCodeCommand],
    segment_repo: SegmentRepository,
    event_bus: EventBus,
) -> OperationResult:
    """Batch operation - AI agents use this for efficiency."""
    succeeded, failed, rollbacks = [], [], []

    for cmd in commands:
        result = apply_code(cmd, segment_repo, event_bus)
        if result.success:
            succeeded.append(result.data)
            rollbacks.append(result.rollback_command)
        else:
            failed.append({"command": cmd, "error": result.error})

    return OperationResult(
        success=len(failed) == 0,
        data=succeeded,
        error=f"{len(failed)} failed" if failed else None,
        rollback_command=BatchRollbackCommand(rollbacks),
    )
```

### Signal Bridge (Event → Qt Signal)

Signal bridges live in `src/shared/infra/signal_bridge/`:

```python
# src/shared/infra/signal_bridge/coding.py
class CodingSignalBridge(BaseSignalBridge):
    code_created = Signal(object)
    segment_coded = Signal(object)

    def _get_context_name(self) -> str:
        return "coding"

    def _register_converters(self) -> None:
        self.register_converter(
            "coding.code_created",
            CodeCreatedConverter(),
            "code_created",
        )

@dataclass(frozen=True)
class CodePayload:
    """UI payload - primitives only, no domain objects."""
    event_type: str
    code_id: int
    name: str
    color: str
```

---

## Presentation Layer Patterns

### ViewModel (Calls Command Handlers Directly)

ViewModels live in `src/contexts/{name}/presentation/viewmodels/`:

```python
# src/contexts/coding/presentation/viewmodels/text_coding_viewmodel.py
class TextCodingViewModel:
    """
    ViewModel for human UI.

    - Calls command handlers directly (no intermediate service)
    - Has repos for queries (CQRS)
    - Manages UI state (selection, undo)
    """

    def __init__(
        self,
        code_repo: CodeRepository,      # For queries
        segment_repo: SegmentRepository,
        event_bus: EventBus,            # For commands
        signal_bridge: CodingSignalBridge,  # For reactive updates
    ):
        self._code_repo = code_repo
        self._segment_repo = segment_repo
        self._event_bus = event_bus
        self._bridge = signal_bridge
        self._undo_stack: list[Any] = []

        # Subscribe to updates
        self._bridge.code_created.connect(self._on_code_created)

    # Commands → Command handlers
    def create_code(self, name: str, color: str) -> bool:
        from src.contexts.coding.core.commandHandlers import create_code

        result = create_code(
            CreateCodeCommand(name=name, color=color),
            self._code_repo,
            self._event_bus,
        )

        if result.success:
            self._undo_stack.append(result.rollback_command)
            return True

        self._last_error = result.error
        self._last_suggestions = result.suggestions
        return False

    # Queries → Direct repo (CQRS)
    def get_codes(self) -> list[CodeDTO]:
        return [self._to_dto(c) for c in self._code_repo.get_all()]
```

### MCP Tools (Calls Command Handlers Directly)

MCP tools live in `src/contexts/{name}/interface/`:

```python
# src/contexts/coding/interface/mcp_tools.py
class CodingMCPTools:
    """
    MCP tools for AI agents.

    Calls SAME command handlers as ViewModel.
    Shared EventBus = UI updates automatically when AI acts.
    """

    def __init__(
        self,
        code_repo: CodeRepository,
        segment_repo: SegmentRepository,
        event_bus: EventBus,  # Same instance as ViewModel
    ):
        self._code_repo = code_repo
        self._segment_repo = segment_repo
        self._event_bus = event_bus

    def handle_create_code(self, params: dict) -> ToolResult:
        from src.contexts.coding.core.commandHandlers import create_code

        result = create_code(  # Same handler as ViewModel!
            CreateCodeCommand(name=params["name"], color=params["color"]),
            self._code_repo,
            self._event_bus,
        )

        return ToolResult(
            success=result.success,
            data=serialize(result.data),
            error=result.error,
            error_code=result.error_code,
            suggestions=result.suggestions,
        )
```

### Shared Presentation Components

Cross-cutting UI components in `src/shared/presentation/`:

```python
# Import shared DTOs
from src.shared.presentation.dto import TextCodingDataDTO, SourceDTO

# Import shared organisms
from src.shared.presentation.organisms import SourceTable, TextEditorPanel

# Import shared templates
from src.shared.presentation.templates import AppShell, ThreePanelLayout
```

---

## Provider Pattern (When To Use)

**Use Provider Pattern for external/swappable services:**

```python
class AIProvider(Protocol):
    """Multiple implementations: OpenAI, Ollama, Mock."""
    def suggest_codes(self, text: str) -> list[Suggestion]: ...

class SyncProvider(Protocol):
    """External service abstraction."""
    def push_changes(self, changes: list) -> SyncResult: ...
```

**Use Direct Wiring for internal, stable dependencies:**

```python
# ViewModel takes repos directly - no protocol needed
class FileManagerViewModel:
    def __init__(
        self,
        source_repo: SourceRepository,  # Direct - single impl
        folder_repo: FolderRepository,  # Direct - single impl
        ai_provider: AIProvider,        # Protocol - multiple impls
    ): ...
```

### Decision Flowchart

```
External service (API, sync, auth)? → YES → Provider Pattern
                                    → NO  ↓
Multiple implementations?           → YES → Provider Pattern
                                    → NO  ↓
Team boundary?                      → YES → Provider Pattern
                                    → NO  → Direct Wiring
```

---

## Code Style

### Imports - Strict Ordering

```python
"""Module docstring (required)."""
from __future__ import annotations           # 1. Future
import re                                     # 2. Stdlib
from returns.result import Result             # 3. Third-party
from src.contexts.coding.core.entities import Code  # 4. Local
if TYPE_CHECKING:                             # 5. Type-checking only
    from src.shared.infra.event_bus import EventBus
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Classes | PascalCase | `TextCodingViewModel` |
| Functions | snake_case | `derive_create_code()` |
| Invariants | `is_*` / `can_*` | `is_valid_code_name()` |
| Derivers | `derive_*` | `derive_create_code()` |
| Events | PastTense | `CodeCreated`, `CodeCreationFailed` |
| Command Handlers | verb_noun | `create_code()`, `apply_code()` |

---

## E2E Testing with Allure

### Test Structure

```python
"""QC-027 Manage Sources - E2E Tests."""
import allure
import pytest

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-027 Manage Sources"),
]

@allure.story("QC-027.01 Import Text Document")
class TestImportTextDocument:

    @allure.title("AC #1: I can select .txt, .docx, .rtf files")
    def test_ac1_select_txt_files(self, text_extractor):
        with allure.step("Verify TextExtractor supports .txt"):
            assert text_extractor.supports(Path("doc.txt"))
```

### Testing Failure Scenarios

```python
class FailingCodeRepository:
    """Mock repo for failure testing."""
    def save(self, code: Code) -> None:
        raise DatabaseError("Connection lost")

def test_handles_db_failure():
    """Test ViewModel handles repo failure gracefully."""
    viewmodel = TextCodingViewModel(
        code_repo=FailingCodeRepository(),
        event_bus=EventBus(),
        signal_bridge=mock_bridge,
    )

    result = viewmodel.create_code("Test", "#FF0000")

    assert result == False
    assert "Connection lost" in viewmodel.get_last_error()[0]
```

---

## Quick Checklist

### Domain
- [ ] Invariants are pure predicates (`is_*` → bool)
- [ ] Derivers are pure: `(command, state) → SuccessEvent | FailureEvent`
- [ ] State containers are frozen dataclasses with tuples
- [ ] Events use past tense (`CodeCreated`, not `CreateCode`)
- [ ] Failure events have error_code and suggestions

### Application
- [ ] Command handlers return `OperationResult` (not just `Result`)
- [ ] Command handlers orchestrate only, domain decides
- [ ] Batch operations exist for AI efficiency

### Presentation
- [ ] ViewModel calls command handlers directly (no service layer)
- [ ] ViewModel has repos for queries (CQRS)
- [ ] MCP Tools call same command handlers as ViewModel
- [ ] Shared EventBus for automatic UI updates
- [ ] Signal payloads use primitives only

### Architecture
- [ ] No unnecessary Protocol/Service layers
- [ ] Provider pattern only for external services
- [ ] AI and UI are both presentation adapters
- [ ] Each bounded context is a complete vertical slice

---

## Reference

- **Tutorials:** `docs/tutorials/` - Hands-on learning
- **E2E Tests:** `src/tests/e2e/`
- **Signal Bridges:** `src/shared/infra/signal_bridge/`
- **Shared Presentation:** `src/shared/presentation/`
