# Part 2: Your First Deriver

Now let's compose invariants into event derivation.

## What is a Deriver?

A **deriver** is a pure function that:

1. Takes a **command** (what the user wants to do) and **state** (current system state)
2. Validates using invariants
3. Returns either a **success event** or a **failure**

The pattern:

```
(command, state) -> SuccessEvent | Failure
```

## Examining `derive_create_code`

Open `src/contexts/coding/core/derivers.py` and find `derive_create_code`:

```python
def derive_create_code(
    name: str,
    color: Color,
    memo: str | None,
    category_id: CategoryId | None,
    owner: str | None,
    state: CodingState,
) -> CodeCreated | CodeNotCreated:
    """
    Derive a CodeCreated event or failure event.
    """
    # Validate name
    if not is_valid_code_name(name):
        return CodeNotCreated.empty_name()

    # Check uniqueness
    if not is_code_name_unique(name, state.existing_codes):
        return CodeNotCreated.duplicate_name(name)

    # Validate category exists if specified
    if category_id is not None:
        if not does_category_exist(category_id, state.existing_categories):
            return CodeNotCreated.category_not_found(category_id)

    # Generate new ID and create event
    new_id = CodeId.new()

    return CodeCreated.create(
        code_id=new_id,
        name=name,
        color=color,
        memo=memo,
        category_id=category_id,
        owner=owner,
    )
```

Notice the pattern:
1. **Validate** using invariants, return a **failure event** early if invalid
2. **Compute** any derived values (like generating an ID)
3. **Return** the success event

## Adding Priority Validation

Let's extend this deriver to validate priority. First, we need a failure event type.

Failure events inherit from `FailureEvent` base class (in `src/shared/common/failure_events.py`) and are defined per-context in `src/contexts/coding/core/failure_events.py`:

```python
# In src/contexts/coding/core/failure_events.py
@dataclass(frozen=True)
class CodeNotCreated(FailureEvent):
    """Code creation failed."""

    # FailureEvent base requires: event_id, occurred_at, event_type
    # event_type follows pattern: {ENTITY}_NOT_{OPERATION}/{REASON}

    reason: str
    name: str | None = None
    category_id: CategoryId | None = None
    suggestions: tuple[str, ...] = ()  # Recovery hints for UI/AI

    @classmethod
    def invalid_priority(cls, value: int) -> "CodeNotCreated":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODE_NOT_CREATED/INVALID_PRIORITY",
            reason=f"Priority must be between 1 and 5, got {value}",
            suggestions=("Use a value between 1 and 5", "Use None for no priority"),
        )
```

Now modify the deriver:

```python
def derive_create_code(
    name: str,
    color: Color,
    memo: str | None,
    category_id: CategoryId | None,
    priority: int | None,  # NEW parameter
    owner: str | None,
    state: CodingState,
) -> CodeCreated | CodeNotCreated:
    """
    Derive a CodeCreated event or failure event.
    """
    # Validate name
    if not is_valid_code_name(name):
        return CodeNotCreated.empty_name()

    # Check uniqueness
    if not is_code_name_unique(name, state.existing_codes):
        return CodeNotCreated.duplicate_name(name)

    # Validate category exists if specified
    if category_id is not None:
        if not does_category_exist(category_id, state.existing_categories):
            return CodeNotCreated.category_not_found(category_id)

    # NEW: Validate priority
    if not is_valid_priority(priority):
        return CodeNotCreated.invalid_priority(priority)

    # Generate new ID and create event
    new_id = CodeId.new()

    return CodeCreated.create(
        code_id=new_id,
        name=name,
        color=color,
        memo=memo,
        category_id=category_id,
        priority=priority,  # NEW field in event
        owner=owner,
    )
```

We also need to update the event (see below).

## Updating the Event

Open `src/contexts/coding/core/events.py` and find `CodeCreated`:

```python
@dataclass(frozen=True)
class CodeCreated(DomainEvent):
    """A new code was created in the codebook"""
    code_id: CodeId
    name: str
    color: Color
    memo: Optional[str] = None
    category_id: Optional[CategoryId] = None
    priority: Optional[int] = None  # NEW field
    owner: Optional[str] = None
```

And update its factory method:

```python
@classmethod
def create(
    cls,
    code_id: CodeId,
    name: str,
    color: Color,
    memo: Optional[str] = None,
    category_id: Optional[CategoryId] = None,
    priority: Optional[int] = None,  # NEW
    owner: Optional[str] = None
) -> 'CodeCreated':
    return cls(
        event_id=cls._generate_id(),
        occurred_at=cls._now(),
        code_id=code_id,
        name=name,
        color=color,
        memo=memo,
        category_id=category_id,
        priority=priority,  # NEW
        owner=owner
    )
```

## Testing the Deriver

Open `src/contexts/coding/core/tests/test_derivers.py`. Add tests for priority:

```python
class TestDeriveCreateCodePriority:
    """Tests for priority validation in derive_create_code."""

    def test_creates_code_with_valid_priority(self, empty_state: CodingState):
        """Should create code with priority 1-5."""
        result = derive_create_code(
            name="High Priority Theme",
            color=Color(red=100, green=150, blue=200),
            memo=None,
            category_id=None,
            priority=5,
            owner="user1",
            state=empty_state,
        )

        assert isinstance(result, CodeCreated)
        assert result.priority == 5

    def test_creates_code_with_no_priority(self, empty_state: CodingState):
        """Should create code without priority (None)."""
        result = derive_create_code(
            name="No Priority Theme",
            color=Color(red=100, green=150, blue=200),
            memo=None,
            category_id=None,
            priority=None,
            owner="user1",
            state=empty_state,
        )

        assert isinstance(result, CodeCreated)
        assert result.priority is None

    def test_fails_with_invalid_priority(self, empty_state: CodingState):
        """Should return failure event with priority outside 1-5."""
        result = derive_create_code(
            name="Bad Priority Theme",
            color=Color(red=100, green=150, blue=200),
            memo=None,
            category_id=None,
            priority=10,
            owner="user1",
            state=empty_state,
        )

        assert isinstance(result, CodeNotCreated)
        assert "Priority must be between 1 and 5" in result.reason
```

## The CodingState Container

Notice we pass `state: CodingState` to derivers. Look at its definition:

```python
@dataclass(frozen=True)
class CodingState:
    """
    State container for coding context derivers.
    Contains all the context needed to validate operations.
    """
    existing_codes: tuple[Code, ...] = ()
    existing_categories: tuple[Category, ...] = ()
    existing_segments: tuple[Segment, ...] = ()
    source_length: Optional[int] = None
    source_exists: bool = True
```

Key points:
- **Immutable** (frozen dataclass with tuples)
- **Contains everything** needed for validation
- **Passed in** - the deriver doesn't fetch data

This is crucial: the deriver is pure because all inputs are explicit. No hidden database calls.

## Why Return Failure Events Instead of Raising Exceptions?

You might ask: "Why not just raise an exception?"

```python
# Traditional approach
def create_code(name, ...):
    if not is_valid_code_name(name):
        raise ValueError("Invalid name")
    ...
```

Problems:
1. **Hidden control flow** - caller must know what exceptions to catch
2. **No type safety** - can't express "returns X or these errors" in types
3. **Forces try/except** - clutters calling code

With explicit failure events:
1. **Visible in signature** - `-> CodeCreated | CodeNotCreated`
2. **Pattern matchable** - `if isinstance(result, CodeNotCreated): ...`
3. **Composable** - can chain operations that might fail
4. **Rich error data** - failure events carry context (reason, related IDs, etc.)

## Summary

You've learned:

- Derivers compose invariants into event derivation
- Pattern: `(command, state) -> SuccessEvent | Failure`
- State is passed in, making derivers pure
- Failures are returned, not raised

## Next Steps

Let's dive deeper into why `Success | Failure` beats exceptions.

**Next:** [Part 3: Understanding the Result Type](./03-result-type.md)
