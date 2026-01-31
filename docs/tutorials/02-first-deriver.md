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

Open `src/domain/coding/derivers.py` and find `derive_create_code`:

```python
def derive_create_code(
    name: str,
    color: Color,
    memo: Optional[str],
    category_id: Optional[CategoryId],
    owner: Optional[str],
    state: CodingState,
) -> CodeCreated | Failure:
    """
    Derive a CodeCreated event or failure.
    """
    # Validate name
    if not is_valid_code_name(name):
        return Failure(EmptyName())

    # Check uniqueness
    if not is_code_name_unique(name, state.existing_codes):
        return Failure(DuplicateName(name))

    # Validate category exists if specified
    if category_id is not None:
        if not does_category_exist(category_id, state.existing_categories):
            return Failure(CategoryNotFound(category_id))

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
1. **Validate** using invariants, return `Failure` early if invalid
2. **Compute** any derived values (like generating an ID)
3. **Return** the success event

## Adding Priority Validation

Let's extend this deriver to validate priority. First, we need a failure type:

```python
# In derivers.py (or a shared types module)
@dataclass(frozen=True)
class InvalidPriority:
    """Priority must be 1-5."""
    value: int
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, 'message',
            f"Priority must be between 1 and 5, got {self.value}"
        )
```

Now modify the deriver:

```python
def derive_create_code(
    name: str,
    color: Color,
    memo: Optional[str],
    category_id: Optional[CategoryId],
    priority: Optional[int],  # NEW parameter
    owner: Optional[str],
    state: CodingState,
) -> CodeCreated | Failure:
    """
    Derive a CodeCreated event or failure.
    """
    # Validate name
    if not is_valid_code_name(name):
        return Failure(EmptyName())

    # Check uniqueness
    if not is_code_name_unique(name, state.existing_codes):
        return Failure(DuplicateName(name))

    # Validate category exists if specified
    if category_id is not None:
        if not does_category_exist(category_id, state.existing_categories):
            return Failure(CategoryNotFound(category_id))

    # NEW: Validate priority
    if not is_valid_priority(priority):
        return Failure(InvalidPriority(priority))

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

Open `src/domain/coding/events.py` and find `CodeCreated`:

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

Open `src/domain/coding/tests/test_derivers.py`. Add tests for priority:

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
        """Should fail with priority outside 1-5."""
        result = derive_create_code(
            name="Bad Priority Theme",
            color=Color(red=100, green=150, blue=200),
            memo=None,
            category_id=None,
            priority=10,
            owner="user1",
            state=empty_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidPriority)
        assert result.failure().value == 10
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

## Why Return `Failure` Instead of Raising?

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

With explicit `Failure`:
1. **Visible in signature** - `-> CodeCreated | Failure`
2. **Pattern matchable** - `if isinstance(result, Failure): ...`
3. **Composable** - can chain operations that might fail

## Summary

You've learned:

- Derivers compose invariants into event derivation
- Pattern: `(command, state) -> SuccessEvent | Failure`
- State is passed in, making derivers pure
- Failures are returned, not raised

## Next Steps

Let's dive deeper into why `Success | Failure` beats exceptions.

**Next:** [Part 3: Understanding the Result Type](./03-result-type.md)
