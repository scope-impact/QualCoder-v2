# Part 6: Testing Without Mocks

One of the biggest benefits of fDDD is testability. Let's see how easy it is to test each layer.

## The Traditional Testing Problem

In a traditional architecture, testing business logic requires:

```python
# Traditional test - lots of setup
def test_create_code_fails_with_duplicate_name():
    # Setup database
    db = sqlite3.connect(":memory:")
    create_tables(db)

    # Setup repositories
    code_repo = CodeRepository(db)
    category_repo = CategoryRepository(db)

    # Create existing code
    existing = Code(name="Theme A", ...)
    code_repo.save(existing)

    # Setup event bus (mock or real)
    event_bus = Mock()

    # Setup service with all dependencies
    service = CodeService(code_repo, category_repo, event_bus)

    # Finally, the actual test
    with pytest.raises(DuplicateNameError):
        service.create_code("Theme A", color)
```

Problems:
- **Slow**: Database setup takes time
- **Brittle**: Schema changes break tests
- **Complex**: Many dependencies to wire up
- **Unclear**: Hard to see what's actually being tested

## Testing Invariants: Pure Functions

Invariants are trivially testable:

```python
def test_valid_priority_values():
    """Priority 1-5 should be valid."""
    assert is_valid_priority(1) is True
    assert is_valid_priority(3) is True
    assert is_valid_priority(5) is True

def test_invalid_priority_values():
    """Priority outside 1-5 should be invalid."""
    assert is_valid_priority(0) is False
    assert is_valid_priority(6) is False

def test_none_priority_is_valid():
    """None (no priority) should be valid."""
    assert is_valid_priority(None) is True
```

Notice:
- **No setup** - just call the function
- **No mocks** - pure data in, data out
- **Fast** - microseconds per test
- **Clear** - obvious what's being tested

## Testing Derivers: Data In, Data Out

Derivers take state and return events or failures. Test them with data fixtures:

```python
# conftest.py - pytest fixtures
@pytest.fixture
def empty_state() -> CodingState:
    return CodingState()

@pytest.fixture
def populated_state(sample_codes, sample_categories) -> CodingState:
    return CodingState(
        existing_codes=tuple(sample_codes),
        existing_categories=tuple(sample_categories),
        source_length=1000,
        source_exists=True,
    )
```

Now test the deriver:

```python
class TestDeriveCreateCodePriority:
    """Tests for priority validation in derive_create_code."""

    def test_creates_code_with_valid_priority(self, empty_state):
        result = derive_create_code(
            name="High Priority",
            color=Color(red=100, green=150, blue=200),
            memo=None,
            category_id=None,
            priority=5,
            owner="user1",
            state=empty_state,
        )

        assert isinstance(result, CodeCreated)
        assert result.priority == 5

    def test_fails_with_invalid_priority(self, empty_state):
        result = derive_create_code(
            name="Bad Priority",
            color=Color(red=100, green=150, blue=200),
            memo=None,
            category_id=None,
            priority=10,  # Invalid!
            owner="user1",
            state=empty_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.error, InvalidPriority)
        assert result.error.value == 10
```

Notice:
- **State is just data** - no database required
- **Result is just data** - assert on the returned event
- **No mocks** - pure function, pure test
- **Fast** - no I/O

## Testing Failure Cases

Testing error conditions is equally simple:

```python
def test_fails_with_duplicate_name(self, populated_state):
    """Duplicate name should return DuplicateName failure."""
    result = derive_create_code(
        name="Theme A",  # Already exists in sample_codes
        color=Color(red=100, green=100, blue=100),
        memo=None,
        category_id=None,
        priority=3,
        owner="user1",
        state=populated_state,
    )

    assert isinstance(result, Failure)
    assert isinstance(result.error, DuplicateName)
    assert result.error.name == "Theme A"
```

Compare to traditional:

```python
# Traditional - awkward exception testing
def test_fails_with_duplicate_name(self, service):
    with pytest.raises(DuplicateNameError) as exc_info:
        service.create_code("Theme A", color)
    assert "Theme A" in str(exc_info.value)
```

The fDDD version is cleaner: just check the returned data.

## Testing Multiple Validation Rules

Test that validations happen in order:

```python
def test_validates_name_before_priority(self, empty_state):
    """Empty name should fail before priority is checked."""
    result = derive_create_code(
        name="",           # Invalid name
        color=Color(red=100, green=100, blue=100),
        memo=None,
        category_id=None,
        priority=100,      # Also invalid priority
        owner="user1",
        state=empty_state,
    )

    # Name is checked first
    assert isinstance(result, Failure)
    assert isinstance(result.error, EmptyName)
    # Priority error never reached
```

## Testing Converters

Converters are also pure functions:

```python
def test_converter_maps_all_fields():
    event = CodeCreated(
        event_id="123",
        occurred_at=datetime(2024, 1, 1),
        code_id=CodeId(value=42),
        name="Test Code",
        color=Color(red=255, green=128, blue=0),
        priority=3,
        memo="Test memo",
        category_id=None,
        owner="user1",
    )

    converter = CodeCreatedConverter()
    payload = converter.convert(event)

    assert payload.code_id == 42
    assert payload.name == "Test Code"
    assert payload.color_hex == "#ff8000"
    assert payload.priority == 3
```

No Qt required. Just data transformation.

## Testing the Full Flow

Even integration tests can be clean:

```python
def test_code_creation_flow():
    """Test the full flow: deriver -> event_bus -> signal_bridge."""
    # Setup
    event_bus = EventBus()
    received_payloads = []

    # Mock signal bridge (just capture payloads)
    def capture_payload(payload):
        received_payloads.append(payload)

    event_bus.subscribe("coding.code_created", lambda e: capture_payload(
        CodeCreatedConverter().convert(e)
    ))

    # Execute
    state = CodingState()
    result = derive_create_code(
        name="Test",
        color=Color(100, 100, 100),
        memo=None,
        category_id=None,
        priority=3,
        owner="user1",
        state=state,
    )

    if isinstance(result, CodeCreated):
        event_bus.publish(result)

    # Verify
    assert len(received_payloads) == 1
    assert received_payloads[0].name == "Test"
    assert received_payloads[0].priority == 3
```

No database. No Qt. Just the core logic.

## Test Organization

Organize tests to mirror the architecture:

```
src/domain/coding/tests/
├── conftest.py           # Shared fixtures (sample_codes, states)
├── test_invariants.py    # Pure predicate tests
└── test_derivers.py      # Event derivation tests

src/application/tests/
├── test_event_bus.py     # Pub/sub tests
└── test_converters.py    # Payload conversion tests
```

Each layer tested in isolation.

## Running Tests

Fast, focused test runs:

```bash
# Test just invariants (milliseconds)
pytest src/domain/coding/tests/test_invariants.py -v

# Test just derivers (still fast)
pytest src/domain/coding/tests/test_derivers.py -v

# Test specific feature
pytest -k "priority" -v
```

## Summary

Testing in fDDD is easy because:

1. **Invariants** are pure functions - trivial to test
2. **Derivers** are pure functions - just data in, data out
3. **No database** needed for domain tests
4. **No mocks** needed for pure functions
5. **Fast** tests encourage thorough coverage

The architecture pushes complexity to the edges, leaving the core logic simple and testable.

## Next Steps

Let's put it all together with a complete reference diagram.

**Next:** [Part 7: Complete Flow Reference](./07-complete-flow.md)
