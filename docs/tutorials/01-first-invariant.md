# Part 1: Your First Invariant

Let's write a pure validation function for our "priority" feature.

## What is an Invariant?

An **invariant** is a pure predicate function that validates a business rule. It:

- Takes data as input
- Returns `True` (valid) or `False` (invalid)
- Has **no side effects** - doesn't modify anything, doesn't call external services
- Is named with `is_*` or `can_*` prefix

## The Priority Rule

For our toy example, we're adding an optional priority field to Codes:

> **Rule:** Priority must be 1-5 (inclusive), or `None` (no priority set).

Let's encode this as an invariant.

## Writing the Invariant

Open `src/contexts/coding/core/invariants.py`. You'll see existing invariants like:

```python
def is_valid_code_name(name: str) -> bool:
    """
    Check that a code name is valid.

    Rules:
    - Not empty or whitespace-only
    - Between 1 and 100 characters
    """
    return is_non_empty_string(name) and is_within_length(name, 1, 100)
```

Notice the pattern:
1. Clear docstring stating the rule
2. Pure logic using helper predicates
3. Returns `bool`

Now let's write our priority invariant:

```python
def is_valid_priority(priority: Optional[int]) -> bool:
    """
    Check that a priority value is valid.

    Rules:
    - None is allowed (no priority)
    - If set, must be 1-5 (inclusive)
    """
    if priority is None:
        return True
    return 1 <= priority <= 5
```

That's it! A few lines of pure logic.

## Why This is Powerful

This tiny function is:

1. **Trivial to test** - no setup, no mocks
2. **Easy to understand** - the rule is right there
3. **Reusable** - any code that needs to validate priority calls this
4. **Composable** - derivers combine this with other invariants

## Writing Tests

Open `src/contexts/coding/core/tests/test_invariants.py`. You'll see test classes for each invariant group. Let's add tests for priority:

```python
class TestPriorityInvariants:
    """Tests for priority validation."""

    def test_none_priority_is_valid(self):
        """None (no priority) should be valid."""
        assert is_valid_priority(None) is True

    def test_valid_priority_values(self):
        """Priority 1-5 should be valid."""
        assert is_valid_priority(1) is True
        assert is_valid_priority(3) is True
        assert is_valid_priority(5) is True

    def test_priority_below_range_invalid(self):
        """Priority below 1 should be invalid."""
        assert is_valid_priority(0) is False
        assert is_valid_priority(-1) is False

    def test_priority_above_range_invalid(self):
        """Priority above 5 should be invalid."""
        assert is_valid_priority(6) is False
        assert is_valid_priority(100) is False
```

Run the tests:

```bash
pytest src/contexts/coding/core/tests/test_invariants.py::TestPriorityInvariants -v
```

## Anatomy of an Invariant Test

Notice how simple these tests are:

```python
def test_valid_priority_values(self):
    assert is_valid_priority(1) is True
```

Compare to testing validation in a traditional service:

```python
def test_valid_priority_values(self):
    # Setup database
    db = create_test_db()
    # Setup repository
    repo = CodeRepository(db)
    # Setup service
    service = CodeService(repo, event_bus, logger)
    # Create test code with priority
    code = service.create_code("Test", color, priority=1)
    # Assert no exception was raised
    assert code.priority == 1
```

The pure function test is:
- **Faster** - no I/O
- **Simpler** - no fixtures
- **Focused** - tests exactly one rule

## Edge Cases to Consider

When writing invariants, think about:

1. **Boundary values**: 1 and 5 are edges of our range
2. **None/empty**: Is `None` valid? (Yes, for optional fields)
3. **Type boundaries**: What about `0`? Negative numbers?

Our tests cover these.

## Invariants vs Validation Methods

You might ask: "Why not put this in the `Code` entity?"

```python
# Don't do this
@dataclass
class Code:
    priority: Optional[int] = None

    def __post_init__(self):
        if self.priority is not None and not (1 <= self.priority <= 5):
            raise ValueError("Priority must be 1-5")
```

Problems:
1. **Couples validation to entity** - can't reuse the rule
2. **Throws exceptions** - forces try/except control flow
3. **Hard to test** - must create full entity to test one rule

With invariants:
1. **Decoupled** - rule lives independently
2. **Returns bool** - caller decides what to do
3. **Easy to test** - just call the function

## Summary

You've learned:

- Invariants are pure predicate functions
- They validate one business rule
- Testing them requires no setup
- The pattern: `is_*(value) -> bool`

In the actual codebase, you'd add `is_valid_priority` to `src/contexts/coding/core/invariants.py` and the tests to `src/contexts/coding/core/tests/test_invariants.py`. The snippets here show the pattern.

## Next Steps

Now let's use this invariant in a deriver to produce domain events.

**Next:** [Part 2: Your First Deriver](./02-first-deriver.md)
