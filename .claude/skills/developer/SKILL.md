---
name: developer
description: |
  QualCoder v2 development conventions following Functional DDD architecture.
  See docs/tutorials/ for hands-on learning.

  **Invoke when:**
  - Writing domain logic (invariants, derivers, events)
  - Creating controllers and signal bridges
  - Adding PySide6/Qt UI components
  - Writing tests (unit, E2E with Allure)
---

# QualCoder v2 Developer Guide

## Architecture Overview

```
src/
├── contexts/{name}/core/    # Domain: invariants, derivers, events (PURE - no I/O)
├── contexts/{name}/infra/   # Infrastructure: repositories, schema
├── application/             # Controllers, Signal Bridges, orchestration
├── presentation/            # PySide6 widgets, screens, dialogs
design_system/               # Reusable UI components, tokens
```

---

## Domain Layer Patterns

### 1. Invariants (Pure Validation)

Pure predicate functions that validate business rules. Named `is_*` or `can_*`.

```python
# src/contexts/coding/core/invariants.py
def is_valid_code_name(name: str) -> bool:
    """Name must be non-empty and <= 100 chars."""
    return is_non_empty_string(name) and is_within_length(name, 1, 100)

def is_code_name_unique(name: str, existing_codes: tuple[Code, ...]) -> bool:
    """Name must not conflict with existing codes (case-insensitive)."""
    return not any(c.name.lower() == name.lower() for c in existing_codes)
```

### 2. State Container (Immutable Context)

Pass all validation context as an immutable state object:

```python
@dataclass(frozen=True)
class CodingState:
    """State container for coding context derivers."""
    existing_codes: tuple[Code, ...] = ()
    existing_categories: tuple[Category, ...] = ()
    source_length: int | None = None
```

### 3. Derivers (Pure Event Derivation)

Compose invariants to derive success or failure events:

```python
# src/contexts/coding/core/derivers.py
def derive_create_code(
    name: str, color: Color, state: CodingState
) -> CodeCreated | CodeNotCreated:
    """Derive event from command and state. PURE - no I/O."""
    if not is_valid_code_name(name):
        return CodeNotCreated.empty_name()
    if not is_code_name_unique(name, state.existing_codes):
        return CodeNotCreated.duplicate_name(name)
    return CodeCreated.create(code_id=CodeId.new(), name=name, color=color)
```

### 4. Domain Events (Success)

Immutable records of things that happened. Past tense naming.

```python
@dataclass(frozen=True)
class CodeCreated(DomainEvent):
    event_type: str = "coding.code_created"
    code_id: CodeId
    name: str
    color: Color
```

### 5. Failure Events (Domain Failures)

Rich failure events with factory methods and context:

```python
@dataclass(frozen=True)
class CodeNotCreated(FailureEvent):
    """Code creation failed."""
    name: str | None = None

    @classmethod
    def empty_name(cls) -> CodeNotCreated:
        return cls(event_type="CODE_NOT_CREATED/EMPTY_NAME")

    @classmethod
    def duplicate_name(cls, name: str) -> CodeNotCreated:
        return cls(event_type="CODE_NOT_CREATED/DUPLICATE_NAME", name=name)

    @property
    def reason(self) -> str:
        return self.event_type.split("/")[1] if "/" in self.event_type else ""
```

---

## Application Layer Patterns

### Controller 5-Step Pattern

```python
class CodingControllerImpl:
    def create_code(self, command: CreateCodeCommand) -> Result:
        # 1. Validate (Pydantic does automatically)
        # 2. Build state from repositories
        state = CodingState(existing_codes=tuple(self._code_repo.get_all()))
        # 3. Derive event (PURE - call domain function)
        result = derive_create_code(command.name, command.color, state)
        # 4. Handle failure or persist on success
        if isinstance(result, CodeNotCreated):
            return Failure(result.message)
        self._code_repo.save(Code(id=result.code_id, name=result.name, ...))
        # 5. Publish event
        self._event_bus.publish(result)
        return Success(code)
```

### Signal Bridge (Event → Qt Signal)

```python
class CodingSignalBridge(BaseSignalBridge):
    code_created = Signal(object)  # Emits CodePayload

    def _register_converters(self) -> None:
        self.register_converter("coding.code_created", CodeCreatedConverter(), "code_created")

@dataclass(frozen=True)
class CodePayload:
    """UI payload - primitives only, no domain objects."""
    code_id: int          # int, not CodeId
    code_name: str
    color: str | None     # hex string, not Color
```

---

## Code Style

### Imports - Strict Ordering

```python
"""Module docstring (required)."""
from __future__ import annotations           # 1. Future
import re                                     # 2. Stdlib
from pydantic import Field                    # 3. Third-party
from src.contexts.coding.core.entities import Code  # 4. Local
if TYPE_CHECKING:                             # 5. Type-checking only
    from src.application.event_bus import EventBus
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Classes | PascalCase | `CodingController` |
| Functions | snake_case | `derive_create_code()` |
| Invariants | `is_*` / `can_*` | `is_valid_code_name()` |
| Derivers | `derive_*` | `derive_create_code()` |
| Events | PastTense | `CodeCreated`, `CodeNotCreated` |

---

## Entity Patterns

```python
from pydantic.dataclasses import dataclass

@dataclass(frozen=True)
class Code:
    """Immutable entity with Pydantic validation."""
    id: CodeId
    name: str = Field(min_length=1, max_length=100)
    color: Color

    def with_name(self, new_name: str) -> Code:
        """Return new Code with updated name."""
        return Code(id=self.id, name=new_name, color=self.color)
```

---

## UI Component Patterns

```python
from design_system import get_colors, RADIUS, SPACING

class ColorPickerDialog(QDialog):
    def __init__(self, parent=None):
        self._colors = get_colors()
        self.setStyleSheet(f"""
            QDialog {{ background: {self._colors.surface}; border-radius: {RADIUS.md}px; }}
        """)
```

---

## E2E Testing with Allure

### Module Structure

```python
"""QC-027 Manage Sources - E2E Tests for acceptance criteria."""
import allure
import pytest

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-027 Manage Sources"),  # Parent task
]

@allure.story("QC-027.01 Import Text Document")  # Subtask
class TestImportTextDocument:

    @allure.title("AC #1: I can select .txt, .docx, .rtf files")
    def test_ac1_select_txt_files(self, text_extractor):
        with allure.step("Verify TextExtractor supports .txt"):
            assert text_extractor.supports(Path("doc.txt"))
```

### Allure Hierarchy

| Level | Decorator | Maps To |
|-------|-----------|---------|
| Epic | `@allure.epic()` | Product |
| Feature | `@allure.feature()` | Parent task |
| Story | `@allure.story()` | Subtask |
| Title | `@allure.title()` | Acceptance criterion |

### Test Naming

```python
def test_ac1_select_txt_files(self):       # AC #1
def test_ac2_text_extracted(self):         # AC #2
def test_handles_unicode_content(self):    # Additional test
```

### Running Tests

```bash
QT_QPA_PLATFORM=offscreen uv run pytest src/presentation/tests/ -v
QT_QPA_PLATFORM=offscreen uv run pytest --alluredir=allure-results
```

---

## Quick Checklist

- [ ] Invariants are pure predicates (`is_*` → bool)
- [ ] Derivers are pure: `(command, state) → SuccessEvent | FailureEvent`
- [ ] State containers are frozen dataclasses with tuples
- [ ] Events use past tense (`CodeCreated`, not `CreateCode`)
- [ ] Failure events have factory methods with context
- [ ] Controllers follow 5-step pattern
- [ ] Signal payloads use primitives only
- [ ] E2E tests use Allure annotations mapping to ACs

---

## Reference

- **Tutorials:** `docs/tutorials/` - Hands-on learning with "priority" example
- **E2E Example:** `src/presentation/tests/test_manage_sources_e2e.py`
