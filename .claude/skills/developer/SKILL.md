---
name: developer
description: |
  QualCoder v2 development conventions, coding standards, and implementation patterns.
  Enforces fDDD architecture, Result types, and project-specific idioms.

  **Invoke when:**
  - Writing new Python code (entities, services, controllers, UI)
  - Creating tests (unit, integration, E2E)
  - Implementing features following DDD layers
  - Adding PySide6/Qt UI components
  - Working with Signal Bridge patterns
  - Understanding codebase conventions

  **Provides:**
  - Code style and naming conventions
  - Import organization rules
  - Testing patterns and fixtures
  - Result type usage (`returns` library)
  - Entity and event patterns
  - Controller 5-step pattern
  - Signal Bridge implementation guide
  - UI component patterns (design system usage)
---

# QualCoder v2 Developer Guide

Development conventions for the QualCoder v2 codebase following Functional DDD architecture.

## Quick Reference

```
src/
├── domain/           # Pure functions, entities, events, derivers (NO I/O)
├── infrastructure/   # Repositories, database, external services
├── application/      # Controllers, Signal Bridges, orchestration
├── presentation/     # PySide6 widgets, screens, dialogs
design_system/        # Reusable UI components, tokens, patterns
```

---

## Code Style

### Imports - Strict Ordering

```python
"""Module docstring (required)."""

from __future__ import annotations           # 1. Future imports

import re                                     # 2. Standard library
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from pydantic import Field                    # 3. Third-party
from pydantic.dataclasses import dataclass as pydantic_dataclass
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QFrame
from returns.result import Failure, Result, Success

from src.domain.shared.types import CodeId    # 4. Local imports
from src.domain.coding.entities import Code

if TYPE_CHECKING:                             # 5. Type-checking only
    from src.application.event_bus import EventBus
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Classes | PascalCase | `CodingController`, `TextSegment` |
| Functions | snake_case | `derive_create_code()`, `get_by_id()` |
| Constants | SCREAMING_SNAKE | `DEFAULT_MAX_HISTORY`, `RADIUS` |
| Type aliases | PascalCase | `CodeId`, `SegmentId` |
| Private | Leading underscore | `_build_state()`, `_emit_threadsafe()` |
| Protocols | PascalCase + Protocol suffix | `EventConverter` |

### Docstrings - Google Style

```python
def derive_create_code(
    name: str,
    color: Color,
    state: CodingState,
) -> CodeCreated | Failure[str]:
    """
    Derive a code creation event from command and state.

    Pure function following fDDD pattern - no I/O, no side effects.

    Args:
        name: The code name (1-100 characters)
        color: The code color (hex format)
        state: Current coding state for invariant checking

    Returns:
        CodeCreated event on success, Failure with reason on error

    Example:
        >>> result = derive_create_code("Anxiety", Color("#FF5722"), state)
        >>> if isinstance(result, CodeCreated):
        ...     print(f"Created: {result.code_id}")
    """
```

---

## Result Type Pattern

Use the `returns` library for all operations that can fail.

### Basic Usage

```python
from returns.result import Failure, Result, Success

def find_code(code_id: CodeId, codes: list[Code]) -> Result[Code, str]:
    """Find a code by ID."""
    for code in codes:
        if code.id == code_id:
            return Success(code)
    return Failure(f"Code {code_id.value} not found")

# Usage
result = find_code(CodeId(value=1), codes)
match result:
    case Success(code):
        print(f"Found: {code.name}")
    case Failure(error):
        print(f"Error: {error}")
```

### In Controllers (Unwrap Pattern)

```python
def create_code(self, command: CreateCodeCommand) -> Result:
    # Derive returns Success or Failure
    result = derive_create_code(command.name, color, state)

    if isinstance(result, Failure):
        return result  # Propagate failure

    event: CodeCreated = result  # Type narrowing
    # Continue with success path...
    return Success(code)
```

---

## Entity Patterns

### Immutable Entities with Pydantic

```python
from pydantic import Field
from pydantic.dataclasses import dataclass

@dataclass(frozen=True)
class Code:
    """
    Code entity - Aggregate root for the Coding context.

    Immutable with Pydantic validation.
    """
    id: CodeId
    name: str = Field(min_length=1, max_length=100)
    color: Color
    memo: str | None = None
    category_id: CategoryId | None = None
    owner: str | None = None

    def with_name(self, new_name: str) -> Code:
        """Return new Code with updated name."""
        return Code(
            id=self.id,
            name=new_name,
            color=self.color,
            memo=self.memo,
            category_id=self.category_id,
            owner=self.owner,
        )
```

### Typed IDs

```python
from dataclasses import dataclass
import uuid

@dataclass(frozen=True)
class CodeId:
    """Typed identifier for Code entities."""
    value: int

    @classmethod
    def new(cls) -> CodeId:
        """Generate a new unique ID."""
        return cls(value=int(uuid.uuid4().int % 2**31))
```

---

## Event Patterns

### Success Events

```python
@dataclass(frozen=True)
class CodeCreated(DomainEvent):
    """Emitted when a code is successfully created."""
    event_type: str = "coding.code_created"
    code_id: CodeId
    name: str
    color: Color
    memo: str | None
    category_id: CategoryId | None
    owner: str | None
```

### Failure Events (Include Reason in Type)

```python
@dataclass(frozen=True)
class CodeNotCreated(DomainEvent):
    """Emitted when code creation fails due to duplicate name."""
    event_type: str = "coding.code_not_created/name_exists"
    name: str
```

---

## Controller 5-Step Pattern

Every controller command follows this pattern:

```python
class CodingControllerImpl:
    def create_code(self, command: CreateCodeCommand) -> Result:
        # Step 1: Validate (Pydantic does automatically)

        # Step 2: Build current state
        state = self._build_coding_state()

        # Step 3: Derive event (PURE - call domain function)
        result = derive_create_code(
            name=command.name,
            color=color,
            state=state,
        )

        # Step 4: Handle failure or persist on success
        if isinstance(result, Failure):
            return result

        event: CodeCreated = result
        code = Code(id=event.code_id, name=event.name, ...)
        self._code_repo.save(code)

        # Step 5: Publish event
        self._event_bus.publish(event)

        return Success(code)
```

---

## Signal Bridge Pattern

Convert domain events to Qt signals for reactive UI updates.

### Signal Bridge Structure

```python
from PySide6.QtCore import Signal
from src.application.signal_bridge.base import BaseSignalBridge

class CodingSignalBridge(BaseSignalBridge):
    """Signal bridge for the Coding bounded context."""

    # Define signals
    code_created = Signal(object)
    code_deleted = Signal(object)
    segment_coded = Signal(object)

    def _get_context_name(self) -> str:
        return "coding"

    def _register_converters(self) -> None:
        self.register_converter(
            "coding.code_created",
            CodeCreatedConverter(),
            "code_created"
        )
```

### Payload Pattern (Primitives Only)

```python
@dataclass(frozen=True)
class CodePayload:
    """UI payload - primitives only, no domain objects."""
    event_type: str
    code_id: int          # int, not CodeId
    code_name: str
    color: str | None     # hex string, not Color
    timestamp: datetime = field(default_factory=_now)
    is_ai_action: bool = False
```

---

## Testing Patterns

### Test File Structure

```python
"""Tests for AutoCodingController - Application Service."""

from unittest.mock import Mock
import pytest
from returns.result import Success, Failure

class TestFindMatches:
    """Tests for finding text matches via controller."""

    def test_find_matches_returns_match_positions(self):
        """Controller should return match positions using domain service."""
        from src.application.coding.auto_coding_controller import AutoCodingController

        controller = AutoCodingController()
        result = controller.find_matches(text="cat sat", pattern="cat")

        assert isinstance(result, Success)
        matches = result.unwrap()
        assert len(matches) == 1

    def test_find_matches_handles_no_matches(self):
        """Controller should return empty list for no matches."""
        # ...
```

### Fixtures (conftest.py)

```python
@pytest.fixture
def engine():
    """Create an in-memory SQLite engine with schema."""
    engine = create_engine("sqlite:///:memory:")
    create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture
def controller(code_repo, category_repo, segment_repo, event_bus):
    """Create a coding controller with all dependencies."""
    return CodingControllerImpl(
        code_repo=code_repo,
        category_repo=category_repo,
        segment_repo=segment_repo,
        event_bus=event_bus,
    )
```

---

## UI Component Patterns

### Use Design System Components

```python
from design_system import (
    ColorSwatch,
    get_colors,
    RADIUS,
    SPACING,
    TYPOGRAPHY,
)

class ColorPickerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._colors = get_colors()

        # Use design system tokens
        self.setStyleSheet(f"""
            QDialog {{
                background: {self._colors.surface};
                border-radius: {RADIUS.md}px;
            }}
        """)

        # Use design system components
        swatch = ColorSwatch("#FF5722", size=32)
        swatch.clicked.connect(self._on_color_selected)
```

### Signal-Slot Connections

```python
class TextCodingScreen(QWidget):
    def __init__(self, signal_bridge: CodingSignalBridge):
        super().__init__()
        self._bridge = signal_bridge

        # Connect to signals
        self._bridge.code_created.connect(self._on_code_created)
        self._bridge.segment_coded.connect(self._on_segment_coded)

    def _on_code_created(self, payload: CodePayload) -> None:
        """Handle code creation from any source."""
        self._code_tree.add_code(
            code_id=payload.code_id,
            name=payload.code_name,
            color=payload.color,
        )
```

---

## Module __init__.py Pattern

```python
"""
Application layer for the Coding bounded context.

Provides the CodingController for handling commands and queries,
and CodingSignalBridge for reactive UI updates.
"""

from src.application.coding.controller import CodingControllerImpl
from src.application.coding.signal_bridge import (
    CodingSignalBridge,
    CodePayload,
    SegmentPayload,
)

__all__ = [
    "CodingControllerImpl",
    "CodingSignalBridge",
    "CodePayload",
    "SegmentPayload",
]
```

---

## Section Separators

Use comment separators for logical sections:

```python
# =============================================================================
# Code Commands
# =============================================================================

def create_code(self, command): ...
def rename_code(self, command): ...

# =============================================================================
# Segment Commands
# =============================================================================

def apply_code(self, command): ...
def remove_code(self, command): ...

# =============================================================================
# Queries
# =============================================================================

def get_all_codes(self) -> list[Code]: ...
```

---

## Common Patterns

### Factory Methods with `@classmethod`

```python
@dataclass(frozen=True)
class MatchesFoundPayload:
    timestamp: datetime
    pattern: str
    matches: tuple[TextMatchPayload, ...]

    @classmethod
    def from_matches(
        cls,
        pattern: str,
        matches: list[tuple[int, int]],
    ) -> MatchesFoundPayload:
        """Create payload from match list."""
        return cls(
            timestamp=datetime.now(UTC),
            pattern=pattern,
            matches=tuple(
                TextMatchPayload(start=m[0], end=m[1])
                for m in matches
            ),
        )
```

### Optional Dependencies with None Default

```python
def __init__(
    self,
    segment_repo: Any | None = None,
    event_bus: EventBus | None = None,
    batch_manager: BatchManager | None = None,
) -> None:
    self._segment_repo = segment_repo
    self._event_bus = event_bus
    self._batch_manager = batch_manager or BatchManager()
```

### Property for Computed Values

```python
@property
def batch_count(self) -> int:
    """Number of batches in history."""
    return len(self._history)

@property
def length(self) -> int:
    """Length of the match."""
    return self.end - self.start
```

---

## File Templates

### New Domain Service

```python
"""
[Service Name] - Domain Service

Pure functions for [purpose]. No I/O, no side effects.

Usage:
    service = ServiceName(data)
    result = service.operation()
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OutputType:
    """Output from the service."""
    field: type


class ServiceName:
    """Domain service for [purpose]."""

    def __init__(self, data: str) -> None:
        self._data = data

    def operation(self) -> list[OutputType]:
        """Perform the operation."""
        # Implementation
        return []
```

### New Test File

```python
"""
Tests for [Module Name] - [Layer] Layer.

TDD tests written BEFORE implementation.
"""

import pytest
from returns.result import Success, Failure


class TestFeatureName:
    """Tests for [feature description]."""

    def test_basic_functionality(self):
        """[Description of what is being tested]."""
        # Arrange
        # Act
        # Assert
        pass

    def test_edge_case(self):
        """[Description of edge case]."""
        pass
```

---

## Quick Checklist

Before committing code, verify:

- [ ] Imports ordered: future → stdlib → third-party → local → TYPE_CHECKING
- [ ] Docstrings present for modules, classes, public methods
- [ ] Result types used for fallible operations
- [ ] Entities are frozen dataclasses
- [ ] Events follow naming: `{Action}` for success, `{Action}Not{Done}/{Reason}` for failure
- [ ] Controllers follow 5-step pattern
- [ ] Payloads use primitives only (no domain objects)
- [ ] Tests use descriptive names and follow Arrange-Act-Assert
- [ ] Design system tokens used for UI styling
