# Part 3: Understanding the Result Type

Why do we use `Success | Failure` instead of exceptions?

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

## The Result Type Solution

Look at `src/domain/shared/types.py`:

```python
@dataclass(frozen=True)
class Success(Generic[T]):
    """Successful result containing a value"""
    value: T

    def is_success(self) -> bool:
        return True

    def is_failure(self) -> bool:
        return False


@dataclass(frozen=True)
class Failure(Generic[E]):
    """Failed result containing an error"""
    error: E

    def is_success(self) -> bool:
        return False

    def is_failure(self) -> bool:
        return True


Result = Union[Success[T], Failure[E]]
```

Now our function signature is **honest**:

```python
def derive_create_code(...) -> CodeCreated | Failure:
```

The return type tells you: "You'll get a `CodeCreated` event OR a `Failure`."

## Benefits

### 1. Explicit Error Handling

The caller **must** handle both cases:

```python
result = derive_create_code(name, color, state)

if isinstance(result, Failure):
    # Handle error - can't accidentally ignore it
    return handle_error(result.error)

# result is CodeCreated here
save_and_publish(result)
```

### 2. Pattern Matching on Failure Types

Each failure is a dataclass you can match:

```python
result = derive_create_code(name, color, state)

if isinstance(result, Failure):
    match result.error:
        case EmptyName():
            show_error("Please enter a name")
        case DuplicateName(name):
            show_error(f"'{name}' already exists")
        case InvalidPriority(value):
            show_error(f"Priority {value} must be 1-5")
        case _:
            show_error("Unknown error")
```

### 3. Failure Types are Data

Failures carry context as data:

```python
@dataclass(frozen=True)
class DuplicateName:
    name: str
    message: str = ""

    def __post_init__(self):
        object.__setattr__(self, 'message', f"Code name '{self.name}' already exists")
```

You can:
- Access `error.name` for the conflicting name
- Access `error.message` for user-friendly text
- Serialize it for logging/API responses

### 4. No Hidden Control Flow

The function signature tells the whole story. No surprise exceptions.

### 5. Composition

Operations that might fail can be chained cleanly:

```python
def create_and_apply(name, color, source_id, position, state):
    # First operation
    code_result = derive_create_code(name, color, state)
    if isinstance(code_result, Failure):
        return code_result  # Pass through the failure

    # Second operation
    segment_result = derive_apply_code(
        code_id=code_result.code_id,
        source_id=source_id,
        position=position,
        state=state,
    )

    return segment_result  # Could be success or failure
```

## Failure Types in QualCoder

Look at the failure types in `src/domain/shared/types.py`:

```python
@dataclass(frozen=True)
class DuplicateName:
    name: str
    message: str = ""

@dataclass(frozen=True)
class CodeNotFound:
    code_id: CodeId
    message: str = ""

@dataclass(frozen=True)
class InvalidPosition:
    start: int
    end: int
    source_length: int
    message: str = ""

@dataclass(frozen=True)
class EmptyName:
    message: str = "Code name cannot be empty"
```

And in `src/domain/coding/derivers.py`:

```python
@dataclass(frozen=True)
class CategoryNotFound:
    category_id: CategoryId
    message: str = ""

@dataclass(frozen=True)
class HasReferences:
    entity_type: str
    entity_id: int
    reference_count: int
    message: str = ""
```

Each failure type:
- Is a frozen dataclass (immutable)
- Carries relevant context
- Has a `message` for human-readable output

## When to Use Each

**Use `Failure` for:**
- Business rule violations (duplicate name, invalid priority)
- Missing entities (code not found, category not found)
- Invalid state transitions

**Use exceptions for:**
- Programming errors (should never happen in production)
- Infrastructure failures (database down, network error)
- System-level issues (out of memory)

The domain layer returns `Failure`. The infrastructure/application layers handle exceptions.

## Summary

The Result type (`Success | Failure`) provides:

- **Explicit error handling** - can't forget to check
- **Type-safe** - errors are data, not exceptions
- **Pattern matchable** - easy to handle different cases
- **Composable** - chain operations cleanly
- **No hidden control flow** - signature tells all

## Next Steps

Now let's trace how events flow from the domain to the UI.

**Next:** [Part 4: Events Flow Through the System](./04-event-flow.md)
