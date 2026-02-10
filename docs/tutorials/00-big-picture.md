# Part 0: The Big Picture

Before diving into code, let's understand *why* QualCoder v2 uses this architecture.

## The Problem: Why Traditional Approaches Fail

QualCoder is a qualitative data analysis tool with complex requirements:

### 1. Complex Validation Rules

Consider creating a new Code:
- Name can't be empty
- Name must be unique (case-insensitive)
- If assigning to a category, that category must exist
- Color must have valid RGB values

These rules interact. Testing them in a traditional `Code.create()` method means:
- Mocking the database for uniqueness checks
- Setting up category fixtures
- Testing each combination of valid/invalid inputs

### 2. Real-Time UI Updates

When an AI agent creates a Code in a background thread:
- The codebook tree must update immediately
- The activity feed must show what happened
- Other views might need to refresh

Traditional approaches scatter this logic:
- Observer patterns couple components
- Signals/slots become spaghetti
- Race conditions lurk in threading

### 3. Testing is Painful

To test "creating a code with a duplicate name fails":

**Traditional approach:**
```python
def test_duplicate_name_rejected():
    # Setup database connection
    db = setup_test_database()
    # Create existing code
    repo = CodeRepository(db)
    repo.save(Code(name="Theme A", ...))
    # Create service with dependencies
    service = CodeService(repo, event_bus, ...)
    # Finally test
    with pytest.raises(DuplicateNameError):
        service.create_code("Theme A", ...)
```

**With fDDD:**
```python
def test_duplicate_name_rejected():
    state = CodingState(existing_codes=(Code(name="Theme A", ...),))
    result = derive_create_code("Theme A", ..., state=state)
    assert isinstance(result, CodeNotCreated)
    assert result.reason == "DUPLICATE_NAME"
```

No database. No mocks. Just data in, data out.

## The Solution: Functional Core / Imperative Shell

The architecture separates **pure logic** from **side effects**:

```mermaid
graph TB
    subgraph Presentation ["Presentation Layer"]
        UI[Qt Widgets & MCP Tools]
        VM[ViewModels]
        UI_DESC["• Qt Widgets receive SignalPayloads<br/>• MCP Tools serve AI agents<br/>• Both call CommandHandlers"]
    end

    subgraph Application ["Application Layer (CommandHandlers, EventBus)"]
        CH[Command Handlers]
        EB[EventBus]
        SB[SignalBridge]
        APP_DESC["• CommandHandlers orchestrate flow<br/>• EventBus routes events<br/>• SignalBridge converts to Qt signals"]
    end

    subgraph Domain ["Domain Layer (Pure Functions)"]
        DOM[Invariants, Derivers, Events]
        DOM_DESC["• PURE FUNCTIONS - no I/O<br/>• All business rules live here<br/>• Fully testable in isolation"]
    end

    subgraph Infrastructure ["Infrastructure Layer (Repositories)"]
        INFRA[Repositories & Adapters]
        INFRA_DESC["• Database access<br/>• File I/O<br/>• External services"]
    end

    VM --> CH
    CH -->|load state| INFRA
    CH -->|call| DOM
    DOM -->|return event| CH
    CH -->|persist| INFRA
    CH -->|publish| EB
    EB --> SB
    SB -->|emit| UI
```

**Key insight:** The Domain Layer is a "pure functional core" - given the same inputs, it always produces the same outputs. Side effects (database writes, UI updates) happen at the edges.

## The 5 Building Blocks

```mermaid
graph LR
    subgraph "Domain Layer (Pure)"
        INV[Invariants]
        DER[Derivers]
        EVT[Events]
    end

    subgraph "Application Layer (Orchestration)"
        CH[CommandHandlers]
        BUS[EventBus]
        BRG[SignalBridge]
    end

    subgraph "Presentation Layer"
        VM[ViewModel / MCP Tools]
    end

    VM -->|call| CH
    CH -->|compose| INV
    INV -->|validate| DER
    DER -->|produce| EVT
    CH -->|publish| BUS
    BUS -->|route to| BRG
    BRG -->|emit| SIG[Qt Signals]
```

### 1. Invariants

Pure predicate functions that validate business rules.

```python
def is_valid_code_name(name: str) -> bool:
    """Name must be non-empty and <= 100 chars."""
    return is_non_empty_string(name) and is_within_length(name, 1, 100)
```

Properties:
- Take data, return `bool`
- No side effects
- Named `is_*` or `can_*`

### 2. Derivers

Pure functions that compose invariants and derive events.

```python
def derive_create_code(name, color, state) -> CodeCreated | CodeNotCreated:
    if not is_valid_code_name(name):
        return CodeNotCreated.empty_name()
    if not is_code_name_unique(name, state.existing_codes):
        return CodeNotCreated.duplicate_name(name)
    return CodeCreated.create(name=name, color=color, ...)
```

Properties:
- Take command + state, return success event or failure event
- Compose multiple invariants
- Pattern: `(command, state) -> SuccessEvent | FailureEvent`

### 3. Events

Immutable records of things that happened.

```python
@dataclass(frozen=True)
class CodeCreated(DomainEvent):
    code_id: CodeId
    name: str
    color: Color
```

Properties:
- Past tense naming (`CodeCreated`, not `CreateCode`)
- Immutable (frozen dataclass)
- Carry all data needed by subscribers

### 4. EventBus

Pub/sub infrastructure for domain events.

```python
# Subscribe
bus.subscribe("coding.code_created", handle_code_created)

# Publish
bus.publish(CodeCreated(...))
```

Properties:
- Decouples publishers from subscribers
- Type-based or string-based subscription
- Thread-safe

### 5. SignalBridge

Converts domain events to Qt signals.

```python
class CodingSignalBridge(BaseSignalBridge):
    code_created = Signal(object)  # Emits CodeCreatedPayload

    def _register_converters(self):
        self.register_converter(
            "coding.code_created",
            CodeCreatedConverter(),
            "code_created"
        )
```

Properties:
- Bridges background threads to Qt main thread
- Converts domain events to UI-friendly payloads
- One bridge per bounded context

## How They Work Together

When a user clicks "Create Code" (or AI calls the MCP tool):

```mermaid
sequenceDiagram
    participant UI as UI Widget / MCP Tool
    participant VM as ViewModel
    participant CH as CommandHandler
    participant D as Deriver
    participant R as Repository
    participant EB as EventBus
    participant SB as SignalBridge
    participant TV as TreeView

    UI->>VM: create_code("Theme A", color)
    VM->>CH: create_code(command, repos, event_bus)
    CH->>R: get_all() [load state]
    R-->>CH: existing_codes
    CH->>CH: build_coding_state()
    CH->>D: derive_create_code(name, color, state)

    Note over D: Pure validation:<br/>is_valid_code_name() ✓<br/>is_code_name_unique() ✓

    D-->>CH: CodeCreated event
    CH->>R: save(code)
    CH->>EB: publish(event)
    CH-->>VM: OperationResult.ok(code, rollback)
    EB->>SB: _dispatch_event(event)

    Note over SB: Convert event → payload

    SB->>TV: code_created.emit(payload)
    TV->>TV: Update tree view
```

**Key Points:**
- **CommandHandler** is the orchestrator (loads state, calls deriver, persists, publishes)
- **Deriver** contains all business logic (pure function, no I/O)
- **OperationResult** returned to caller with data, rollback command, or error details
- **Same flow** for both human UI and AI agents

## Next Steps

Now that you understand the big picture, let's write your first invariant.

**Next:** [Part 1: Your First Invariant](./01-first-invariant.md)
