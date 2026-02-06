# QualCoder v2 - Copilot Instructions

## Overview

QualCoder v2 is a qualitative data analysis desktop application built with **Python 3.11+** and **PySide6 (Qt)**. It follows **Functional Domain-Driven Design (fDDD)** with vertical slice architecture, where the domain layer is a pure functional core with no I/O.

Key design principle: **Both human UI and AI agents are first-class consumers** of the same domain logic via shared command handlers.

## Architecture: Functional Core / Imperative Shell

```
┌─────────────────────────────────────────────────────────────────┐
│ Presentation (ViewModel, Screens, MCP Tools)                    │
│ → UI state, AI tool interface, rendering                        │
├─────────────────────────────────────────────────────────────────┤
│ Application (Command Handlers, EventBus, SignalBridge)          │
│ → Orchestration only, NO business logic                         │
├─────────────────────────────────────────────────────────────────┤
│ Domain (Entities, Derivers, Events, Invariants)                 │
│ → Pure functions, ALL business logic, NO I/O                    │
├─────────────────────────────────────────────────────────────────┤
│ Infrastructure (Repositories, DB, External Services)            │
│ → Persistence, external APIs                                    │
└─────────────────────────────────────────────────────────────────┘
```

## Project Layout

```
src/
├── contexts/               # Bounded contexts (vertical slices)
│   ├── coding/             # Code creation, text segments, categories
│   ├── cases/              # Case management, attributes
│   ├── sources/            # File import, source management
│   ├── folders/            # Folder organization
│   ├── projects/           # Project lifecycle
│   └── settings/           # User preferences
├── shared/                 # Cross-cutting concerns
│   ├── common/             # Types, OperationResult, failure events
│   ├── core/               # Shared domain logic
│   ├── infra/              # EventBus, SignalBridge, AppContext
│   └── presentation/       # Molecules, organisms, templates
└── tests/e2e/              # End-to-end tests

design_system/              # Reusable UI components, tokens
```

### Context Layer Structure

Each bounded context follows:

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **core/** | `contexts/{name}/core/` | Domain: entities, events, invariants, derivers (PURE) |
| **commandHandlers/** | `core/commandHandlers/` | Use cases - orchestration only |
| **infra/** | `contexts/{name}/infra/` | Repositories, database schemas |
| **interface/** | `contexts/{name}/interface/` | MCP tools for AI agents |
| **presentation/** | `contexts/{name}/presentation/` | ViewModels, screens, dialogs |

## The 5 Building Blocks

### 1. Invariants (Pure Validation)

Pure predicate functions that validate business rules. Named `is_*` or `can_*`.

```python
def is_valid_code_name(name: str) -> bool:
    """Name must be non-empty and <= 100 chars."""
    return is_non_empty_string(name) and is_within_length(name, 1, 100)
```

### 2. Derivers (Pure Event Derivation)

Compose invariants to derive success or failure events. Pattern: `(command, state) → SuccessEvent | FailureEvent`

```python
def derive_create_code(cmd: CreateCodeCommand, state: CodingState) -> CodeCreated | CodeCreationFailed:
    if not is_valid_code_name(cmd.name):
        return CodeCreationFailed.empty_name()
    if not is_code_name_unique(cmd.name, state.existing_codes):
        return CodeCreationFailed.duplicate_name(cmd.name)
    return CodeCreated(code_id=generate_id(), name=cmd.name.strip(), color=cmd.color)
```

### 3. Events (Immutable Facts)

Past-tense named frozen dataclasses. Failure events include error_code and suggestions.

```python
@dataclass(frozen=True)
class CodeCreated:
    event_type: str = "coding.code_created"
    code_id: int
    name: str
    color: str

@dataclass(frozen=True)
class CodeCreationFailed:
    reason: str
    error_code: str
    suggestions: tuple[str, ...] = ()
```

### 4. Command Handlers (Orchestration Only)

Load state, call domain, persist, publish. Return `OperationResult`.

```python
def create_code(cmd, code_repo, event_bus) -> OperationResult:
    state = CodingState(existing_codes=tuple(code_repo.get_all()))
    event = derive_create_code(cmd, state)  # THE DOMAIN DECIDES
    if isinstance(event, CodeCreationFailed):
        return OperationResult(success=False, error=event.reason, error_code=event.error_code)
    code_repo.save(Code(id=event.code_id, name=event.name, color=event.color))
    event_bus.publish(event)
    return OperationResult(success=True, data=code, rollback_command=DeleteCodeCommand(code_id=event.code_id))
```

### 5. SignalBridge (Event → Qt Signal)

Bridges domain events to Qt signals for reactive UI updates.

```python
class CodingSignalBridge(BaseSignalBridge):
    code_created = Signal(object)
    def _register_converters(self):
        self.register_converter("coding.code_created", CodeCreatedConverter(), "code_created")
```

## Key Patterns

- **CQRS**: Commands go through handlers, queries go direct to repos
- **AI and UI parity**: Both ViewModel and MCP Tools call the same command handlers
- **No unnecessary layers**: Delete protocols with single implementations
- **State containers**: Frozen dataclasses with tuples for deriver input
- **Batch operations**: For AI agent efficiency

## MCP Handler Pattern

MCP tools in `interface/handlers/` **MUST delegate mutations to command handlers**. This ensures events are published and the UI refreshes via SignalBridge.

```python
# CORRECT: Delegate to command handler (publishes event)
def handle_approve_suggestion(ctx: HandlerContext, args: dict) -> dict:
    command = CreateCodeCommand(name=suggestion.name, color=suggestion.color)
    result = create_code(
        command=command,
        code_repo=ctx.code_repo,
        event_bus=ctx.event_bus,  # Always pass event_bus
    )
    return result.to_dict()

# WRONG: Direct repo access (no event, UI won't refresh)
def handle_approve_suggestion(ctx: HandlerContext, args: dict) -> dict:
    code = Code(id=new_id, name=suggestion.name)
    ctx.code_repo.save(code)  # No event published!
    return {"success": True}
```

**Why this matters:**
- Command handlers call derivers (domain logic) and publish events
- SignalBridge converts events to Qt signals for reactive UI
- Direct repo calls bypass this flow, causing UI desync

**Anti-pattern checklist** - MCP handlers should NOT:
- Call `repo.save()` directly without command handler
- Call `repo.delete()` directly without command handler
- Create entities manually instead of via command handler
- Skip passing `event_bus` to command handlers

## Build & Test Commands

```bash
make init                           # First-time setup
uv sync --all-extras                # Sync dependencies
QT_QPA_PLATFORM=offscreen make test-all  # Run all tests
make run                            # Run application
```

## Code Style

- Python 3.11+
- Import order: future → stdlib → third-party → local → TYPE_CHECKING
- Naming: PascalCase (classes), snake_case (functions), `is_*`/`can_*` (invariants), `derive_*` (derivers)
- Events use past tense (`CodeCreated`, not `CreateCode`)

## Commit Convention

```
type(scope): description

feat(cases): add case attribute management
fix(coding): resolve segment overlap detection
test(cases): add e2e tests for case manager
```

Types: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`
Scopes: `coding`, `cases`, `sources`, `projects`, `settings`, `folders`
