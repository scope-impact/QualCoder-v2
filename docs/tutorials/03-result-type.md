# Part 3: Understanding Failure Events and the Result Type

Why do we use explicit failure events instead of exceptions?

## The Problem with Exceptions

Consider this traditional approach:

```python
def create_code(name: str, color: Color) -> Code:
    """Create a new code. Raises ValueError on invalid input."""
    if not name:
        raise ValueError("Name cannot be empty")
    if not is_unique(name):
        raise DuplicateNameError(f"Name '{name}' already exists")
    if not is_valid_color(color):
        raise ValueError("Invalid color")
    return Code(name=name, color=color)
```

Problems:

### 1. Hidden Control Flow

The function signature says `-> Code`, but it might not return a `Code` at all! The caller must know (somehow) what exceptions to catch:

```python
try:
    code = create_code(name, color)
except ValueError as e:
    # Was it the name? The color? Something else?
    show_error(str(e))
except DuplicateNameError as e:
    show_error("Name taken")
```

### 2. No Type Safety

Python's type system can't express "returns Code or raises these specific exceptions." The caller has no compile-time help.

### 3. Exception Proliferation

Each failure type needs its own exception class:

```python
class EmptyNameError(ValueError): pass
class DuplicateNameError(ValueError): pass
class InvalidColorError(ValueError): pass
class InvalidPriorityError(ValueError): pass
# ... and on it goes
```

### 4. Composition is Awkward

Chaining operations that might fail requires nested try/except:

```python
try:
    code = create_code(name, color)
    try:
        segment = apply_code(code.id, source_id, position)
    except CodeNotFoundError:
        ...
    except InvalidPositionError:
        ...
except DuplicateNameError:
    ...
```

## The Failure Events Solution

QualCoder v2 uses **failure events** - domain events that represent failed operations. These are defined in `src/contexts/{context}/core/failure_events.py`:

```python
@dataclass(frozen=True)
class CodeNotCreated(FailureEvent):
    """Failure event: Code creation failed."""

    name: str | None = None
    category_id: CategoryId | None = None

    @classmethod
    def empty_name(cls) -> CodeNotCreated:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODE_NOT_CREATED/EMPTY_NAME",
        )

    @classmethod
    def duplicate_name(cls, name: str) -> CodeNotCreated:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODE_NOT_CREATED/DUPLICATE_NAME",
            name=name,
        )
```

Now our function signature is **honest**:

```python
def derive_create_code(...) -> CodeCreated | CodeNotCreated:
```

The return type tells you: "You'll get a `CodeCreated` success event OR a `CodeNotCreated` failure event."

> **Note:** The codebase also provides `OperationResult` (in `src/shared/common/operation_result.py`) which command handlers use to wrap results with error codes, suggestions, and rollback commands. See the section below.

## Benefits

### 1. Explicit Error Handling

The caller **must** handle both cases:

```python
result = derive_create_code(name, color, state)

if isinstance(result, CodeNotCreated):
    # Handle error - can't accidentally ignore it
    return handle_error(result)

# result is CodeCreated here
save_and_publish(result)
```

### 2. Pattern Matching on Failure Events

Failure events have a `reason` property extracted from their `event_type`:

```python
result = derive_create_code(name, color, state)

if isinstance(result, CodeNotCreated):
    match result.reason:
        case "EMPTY_NAME":
            show_error("Please enter a name")
        case "DUPLICATE_NAME":
            show_error(f"'{result.name}' already exists")
        case "CATEGORY_NOT_FOUND":
            show_error(f"Category not found")
        case _:
            show_error(result.message)  # Fallback to human-readable message
```

### 3. Failure Events are Data

Failure events carry context as data:

```python
@dataclass(frozen=True)
class CodeNotCreated(FailureEvent):
    name: str | None = None
    category_id: CategoryId | None = None

    @property
    def message(self) -> str:
        match self.reason:
            case "EMPTY_NAME":
                return "Code name cannot be empty"
            case "DUPLICATE_NAME":
                return f"Code name '{self.name}' already exists"
            case _:
                return super().message
```

You can:
- Access `result.name` for the conflicting name
- Access `result.message` for user-friendly text
- Access `result.reason` for programmatic handling
- Publish failure events to the EventBus for policies to react

### 4. No Hidden Control Flow

The function signature tells the whole story. No surprise exceptions.

### 5. Composition with Explicit Checking

For chaining operations, explicit checking works well:

```python
def create_and_apply(name, color, source_id, position, state):
    # First operation
    code_result = derive_create_code(name, color, state)
    if isinstance(code_result, CodeNotCreated):
        return code_result  # Pass through the failure event

    # Second operation
    segment_result = derive_apply_code_to_text(
        code_id=code_result.code_id,
        source_id=source_id,
        start=position.start,
        end=position.end,
        selected_text="...",
        memo=None,
        importance=0,
        owner=None,
        state=state,
    )

    return segment_result  # Could be SegmentCoded or SegmentNotCoded
```

> **Note:** Command handlers wrap failure events in `OperationResult` to provide a richer response for ViewModels and MCP tools.

## Failure Events in QualCoder

Look at the failure events in `src/contexts/coding/core/failure_events.py`:

```python
@dataclass(frozen=True)
class CodeNotCreated(FailureEvent):
    """Failure event: Code creation failed."""
    name: str | None = None
    category_id: CategoryId | None = None

    @classmethod
    def empty_name(cls) -> CodeNotCreated:
        return cls(event_type="CODE_NOT_CREATED/EMPTY_NAME", ...)

    @classmethod
    def duplicate_name(cls, name: str) -> CodeNotCreated:
        return cls(event_type="CODE_NOT_CREATED/DUPLICATE_NAME", name=name, ...)

@dataclass(frozen=True)
class CodeNotDeleted(FailureEvent):
    """Failure event: Code deletion failed."""
    code_id: CodeId | None = None
    reference_count: int = 0

    @classmethod
    def not_found(cls, code_id: CodeId) -> CodeNotDeleted:
        return cls(event_type="CODE_NOT_DELETED/NOT_FOUND", code_id=code_id, ...)

    @classmethod
    def has_references(cls, code_id: CodeId, count: int) -> CodeNotDeleted:
        return cls(event_type="CODE_NOT_DELETED/HAS_REFERENCES", code_id=code_id, reference_count=count, ...)
```

Each failure event:
- Inherits from `FailureEvent` base class
- Is a frozen dataclass (immutable)
- Has factory methods for each failure reason
- Carries relevant context (IDs, names, counts)
- Has a `message` property for human-readable output
- Has a `reason` property extracted from `event_type`
- Can be published to the EventBus for policies to react

## OperationResult: Wrapping for Presentation

While derivers return `SuccessEvent | FailureEvent`, command handlers wrap these in `OperationResult` to serve both UI and AI consumers:

```python
# In src/shared/common/operation_result.py
@dataclass(frozen=True)
class OperationResult:
    """Rich result type for use case operations."""

    success: bool
    data: Any | None = None           # The entity on success
    error: str | None = None          # Human-readable error
    error_code: str | None = None     # Machine-readable (e.g., "CODE_NOT_CREATED/DUPLICATE_NAME")
    suggestions: tuple[str, ...] = () # Recovery hints for UI/AI
    rollback_command: Any | None = None  # For undo functionality

    @classmethod
    def ok(cls, data: Any = None, rollback: Any = None) -> OperationResult:
        return cls(success=True, data=data, rollback_command=rollback)

    @classmethod
    def fail(cls, error: str, error_code: str | None = None, suggestions: tuple[str, ...] = ()) -> OperationResult:
        return cls(success=False, error=error, error_code=error_code, suggestions=suggestions)

    @classmethod
    def from_failure(cls, event: FailureEvent) -> OperationResult:
        """Convert a domain failure event to OperationResult."""
        return cls(
            success=False,
            error=event.message,
            error_code=event.event_type,
            suggestions=getattr(event, "suggestions", ()),
        )
```

Command handlers use it like this:

```python
# In src/contexts/coding/core/commandHandlers/create_code.py
def create_code(command: CreateCodeCommand, code_repo, event_bus) -> OperationResult:
    # Call deriver
    result = derive_create_code(name=command.name, color=color, state=state)

    # Handle failure
    if isinstance(result, FailureEvent):
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    # Persist and publish success
    code = Code(...)
    code_repo.save(code)
    event_bus.publish(result)

    return OperationResult.ok(
        data=code,
        rollback=DeleteCodeCommand(code_id=code.id.value),
    )
```

**Why OperationResult?**
- **UI consumers** get `error` and `suggestions` for display
- **AI consumers** get `error_code` for programmatic handling
- **Undo functionality** gets `rollback_command` for the undo stack
- **Same interface** for both human and AI callers

## When to Use Each

**Use failure events for:**
- Business rule violations (duplicate name, invalid priority)
- Missing entities (code not found, category not found)
- Invalid state transitions
- Any failure that policies or UI might need to react to

**Use OperationResult for:**
- Command handler return values (wraps failure events)
- ViewModel return values
- MCP tool responses

**Use exceptions for:**
- Programming errors (should never happen in production)
- Infrastructure failures (database down, network error)
- System-level issues (out of memory)

The domain layer returns failure events. Command handlers wrap them in OperationResult. Infrastructure exceptions bubble up separately.

## Summary

Failure events (`CodeCreated | CodeNotCreated`) provide:

- **Explicit error handling** - can't forget to check
- **Type-safe** - errors are data, not exceptions
- **Pattern matchable** - easy to handle different reasons
- **Publishable** - failure events can be published to EventBus for policies
- **Rich context** - carry IDs, names, and human-readable messages
- **No hidden control flow** - signature tells all

## Next Steps

Now let's trace how events flow from the domain to the UI.

**Next:** [Part 4: Events Flow Through the System](./04-event-flow.md)
