---
id: decision-002
title: Library Alternatives Analysis for Custom Infrastructure
date: '2026-01-30 05:51'
status: proposed
---
## Context

This document analyzes the custom implementations in the diff against `origin/main` and evaluates whether existing Python libraries could replace them.

### Summary of Changes

| File/Module | Lines | Purpose |
|-------------|-------|---------|
| `src/application/event_bus.py` | 427 | Synchronous pub/sub event bus |
| `src/application/signal_bridge/` | ~600 | Qt signal bridging for domain events |
| `src/domain/shared/validation.py` | 310 | Validation predicates and helpers |
| `src/domain/shared/types.py` | 161 | Result type (Success/Failure) |
| `src/domain/coding/derivers.py` | 637 | Pure event derivation functions |
| `src/domain/coding/invariants.py` | 409 | Business rule predicates |

**Total custom infrastructure: ~2,544 lines**

---

### 1. EventBus Implementation

#### Current Implementation
- Synchronous pub/sub with thread-safety (RLock)
- Subscription by string type or event class
- `subscribe_all()` for global handlers
- Event history for debugging
- Subscription handles for cleanup

#### Library Alternatives

##### **Blinker** (Recommended for simplicity)
```python
from blinker import signal

code_created = signal('code_created')

@code_created.connect
def handle_code_created(sender, **kwargs):
    pass

code_created.send(sender=app, event=event)
```

**Pros:**
- Flask's signal library, very mature
- Simple API, thread-safe
- ~1000 GitHub stars, actively maintained
- Supports named signals, anonymous signals
- Weak reference support

**Cons:**
- No built-in event history
- No subscribe_all() equivalent (need multiple connections)

##### **PyPubSub**
```python
from pubsub import pub

pub.subscribe(handler, 'coding.code_created')
pub.sendMessage('coding.code_created', event=event)
```

**Pros:**
- Mature library, extensive documentation
- Built-in debugging/tracing
- Topic hierarchy support

**Cons:**
- API is more verbose
- Less pythonic

##### **PyDispatcher**
```python
from pydispatch import dispatcher

dispatcher.connect(handler, signal='code_created', sender=dispatcher.Any)
dispatcher.send(signal='code_created', sender=self, event=event)
```

**Pros:**
- Django's dispatcher foundation
- Very flexible sender/signal matching

**Cons:**
- API is verbose
- Less modern design

#### EventBus Recommendation: **Keep Custom Implementation**

**Rationale:**
1. Current implementation is only ~400 lines, well-tested
2. Libraries don't provide all features (subscribe_all, event history, type-based subscription)
3. Tight integration with domain event conventions (event_type attribute)
4. Adding a library adds a dependency for minimal gain

**If replacing:** Use **Blinker** - simplest API, most Pythonic.

---

### 2. Result Type (Success/Failure)

#### Current Implementation
- Simple `Success[T]` and `Failure[E]` dataclasses
- Basic `map()`, `unwrap()`, `is_success()`, `is_failure()`

#### Library Alternatives

##### **returns** by dry-python (Recommended)
```python
from returns.result import Result, Success, Failure

def divide(a: int, b: int) -> Result[float, str]:
    if b == 0:
        return Failure("division by zero")
    return Success(a / b)

result.map(lambda x: x * 2).unwrap()
```

**Pros:**
- Full railway-oriented programming
- Rich API: `bind()`, `lash()`, `alt()`, `rescue()`
- Type-safe with mypy plugins
- Well-documented, 3k+ GitHub stars
- Also provides: `Maybe`, `IO`, `Future`, `RequiresContext`

**Cons:**
- Heavier dependency
- Learning curve for full API

##### **result** (lighter alternative)
```python
from result import Result, Ok, Err

Ok(1).map(lambda x: x + 1)  # Ok(2)
Err("boom").map(lambda x: x + 1)  # Err("boom")
```

**Pros:**
- Minimal API, Rust-inspired
- Very lightweight

**Cons:**
- Less feature-rich than `returns`

#### Result Type Recommendation: **Consider `returns` library**

**Rationale:**
1. Current implementation is minimal (~50 lines of core logic)
2. `returns` provides significantly more functionality (bind, do notation, async support)
3. Better mypy integration
4. Would improve composition in derivers

**Migration effort:** Low - just change imports, API is compatible.

---

### 3. Validation Utilities

#### Current Implementation
- Predicates: `is_non_empty_string()`, `is_within_length()`, etc.
- `ValidationResult = ValidationSuccess | ValidationFailure`
- `validate_field()`, `validate_all()` composers

#### Library Alternatives

##### **Pydantic v2** (Most popular)
```python
from pydantic import BaseModel, field_validator, ValidationError

class CodeCreate(BaseModel):
    name: str
    color: str

    @field_validator('name')
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('name cannot be empty')
        return v
```

**Pros:**
- Industry standard for Python validation
- Excellent performance (Rust core in v2)
- Rich ecosystem, IDE support
- JSON Schema generation

**Cons:**
- Different paradigm (class-based vs functional predicates)
- Would require architectural changes
- Overkill for pure predicate functions

##### **Cerberus**
```python
from cerberus import Validator

schema = {'name': {'type': 'string', 'minlength': 1, 'maxlength': 100}}
v = Validator(schema)
v.validate({'name': 'Test'})
```

**Pros:**
- Schema-based validation
- Extensible rules

**Cons:**
- Schema-centric, not predicate-centric
- Different paradigm

##### **validators** (lightweight)
```python
import validators

validators.length('hello', min=1, max=100)
validators.uuid(some_uuid)
```

**Pros:**
- Simple predicate functions
- Similar to current approach

**Cons:**
- Limited scope (URLs, emails, etc.)
- Doesn't cover domain-specific rules

#### Validation Recommendation: **Keep Custom Implementation**

**Rationale:**
1. Current predicates are domain-specific (hierarchy validation, uniqueness checks)
2. Libraries focus on data validation, not business rule predicates
3. The functional approach (pure predicates) is intentional for testing
4. Current implementation is clean and minimal (~300 lines)
5. Pydantic would require significant architectural changes

---

### 4. Signal Bridge (Qt Integration)

#### Current Implementation
- Thread-safe signal emission from background threads to Qt main thread
- Event → Payload converter pattern
- Activity feed integration
- Singleton pattern per context

#### Library Alternatives

**There are no direct alternatives.** This is highly specialized infrastructure that:
1. Bridges domain events to PyQt6 signals
2. Handles Qt's thread-affinity requirements
3. Integrates with the application's activity feed

#### Signal Bridge Recommendation: **Keep Custom Implementation**

**Rationale:**
1. Qt-specific threading requirements
2. Tight integration with domain event patterns
3. No library exists for this exact use case

---

### 5. Derivers and Invariants

#### Current Implementation
- Pure functions: `(command, state) → Event | Failure`
- Compose invariants to validate operations
- Domain-specific business rules

#### Library Alternatives

**None applicable.** These are domain-specific implementations that encode business rules. Libraries cannot replace domain logic.

#### Derivers/Invariants Recommendation: **Keep Custom Implementation**

**Rationale:**
1. Domain logic must be custom
2. The functional pattern is the architecture, not replaceable infrastructure

---

## Decision

| Component | Recommendation | Rationale |
|-----------|---------------|-----------|
| **EventBus** | Keep custom | Full-featured, well-tested, tight integration |
| **Result Type** | Consider `returns` | Richer API, better typing, low migration cost |
| **Validation** | Keep custom | Domain-specific predicates, functional design |
| **Signal Bridge** | Keep custom | No alternatives exist |
| **Derivers/Invariants** | Keep custom | Domain logic, not infrastructure |

### If Adopting Libraries

**Priority 1: `returns` for Result type**
- Install: `pip install returns`
- Benefits: Better composition, mypy plugin, do-notation
- Migration: Replace imports, API mostly compatible

**Priority 2: Consider `blinker` for simpler use cases**
- Only if EventBus features (history, subscribe_all) aren't needed
- Current EventBus is well-designed; switching adds little value

### Dependencies to Consider Adding

```toml
# pyproject.toml
[project.optional-dependencies]
ddd = [
    "returns>=0.22",  # Result/Maybe/IO monads
]
```

## Consequences

### Positive
- Custom implementations provide exactly what's needed without unnecessary abstractions
- ~2,500 lines of well-documented, tested code following clean architecture principles
- Tight integration with Qt and domain event patterns
- No external dependencies for core infrastructure

### Negative
- Maintenance burden for custom code
- Missing advanced features that `returns` library provides (bind, do-notation, async support)

### Recommended Action
Evaluate adopting `returns` for the Result type to gain better composition primitives, but keep all other custom implementations.
