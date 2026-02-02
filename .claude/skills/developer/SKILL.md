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
---

# QualCoder v2 Developer Guide

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
from pydantic import Field                    # 3. Third-party
from src.domain.shared.types import CodeId    # 4. Local imports
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

### Docstrings - Google Style

```python
def derive_create_code(name: str, color: Color, state: CodingState) -> CodeCreated | Failure[str]:
    """
    Derive a code creation event from command and state.

    Args:
        name: The code name (1-100 characters)
        color: The code color (hex format)
        state: Current coding state for invariant checking

    Returns:
        CodeCreated event on success, Failure with reason on error
    """
```

---

## Result Type Pattern

Use the `returns` library for all operations that can fail.

```python
from returns.result import Failure, Result, Success

def find_code(code_id: CodeId, codes: list[Code]) -> Result[Code, str]:
    for code in codes:
        if code.id == code_id:
            return Success(code)
    return Failure(f"Code {code_id.value} not found")

# In controllers - propagate failures
def create_code(self, command: CreateCodeCommand) -> Result:
    result = derive_create_code(command.name, color, state)
    if isinstance(result, Failure):
        return result  # Propagate failure
    event: CodeCreated = result  # Type narrowing
    return Success(code)
```

---

## Entity Patterns

```python
from pydantic import Field
from pydantic.dataclasses import dataclass

@dataclass(frozen=True)
class Code:
    """Code entity - immutable with Pydantic validation."""
    id: CodeId
    name: str = Field(min_length=1, max_length=100)
    color: Color
    memo: str | None = None

    def with_name(self, new_name: str) -> Code:
        """Return new Code with updated name."""
        return Code(id=self.id, name=new_name, color=self.color, memo=self.memo)

@dataclass(frozen=True)
class CodeId:
    """Typed identifier for Code entities."""
    value: int
```

---

## Event Patterns

```python
@dataclass(frozen=True)
class CodeCreated(DomainEvent):
    """Emitted when a code is successfully created."""
    event_type: str = "coding.code_created"
    code_id: CodeId
    name: str
    color: Color

@dataclass(frozen=True)
class CodeNotCreated(DomainEvent):
    """Failure event - include reason in type."""
    event_type: str = "coding.code_not_created/name_exists"
    name: str
```

---

## Controller 5-Step Pattern

```python
class CodingControllerImpl:
    def create_code(self, command: CreateCodeCommand) -> Result:
        # Step 1: Validate (Pydantic does automatically)
        # Step 2: Build current state
        state = self._build_coding_state()
        # Step 3: Derive event (PURE - call domain function)
        result = derive_create_code(name=command.name, color=color, state=state)
        # Step 4: Handle failure or persist on success
        if isinstance(result, Failure):
            return result
        event: CodeCreated = result
        self._code_repo.save(Code(id=event.code_id, name=event.name, ...))
        # Step 5: Publish event
        self._event_bus.publish(event)
        return Success(code)
```

---

## Signal Bridge Pattern

Convert domain events to Qt signals for reactive UI updates.

```python
class CodingSignalBridge(BaseSignalBridge):
    code_created = Signal(object)
    code_deleted = Signal(object)

    def _get_context_name(self) -> str:
        return "coding"

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

## UI Component Patterns

```python
from design_system import ColorSwatch, get_colors, RADIUS, SPACING, TYPOGRAPHY

class ColorPickerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._colors = get_colors()
        self.setStyleSheet(f"""
            QDialog {{ background: {self._colors.surface}; border-radius: {RADIUS.md}px; }}
        """)
        swatch = ColorSwatch("#FF5722", size=32)
        swatch.clicked.connect(self._on_color_selected)
```

---

## E2E Testing with Allure

### Module Structure

```python
"""QC-027 Manage Sources - E2E Tests for all acceptance criteria."""
import allure
import pytest

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-027 Manage Sources"),  # Parent task
]

@allure.story("QC-027.01 Import Text Document")  # Subtask
@allure.severity(allure.severity_level.CRITICAL)
class TestImportTextDocument:
    """QC-027.01: As a Researcher, I want to import text documents..."""

    @allure.title("AC #1: I can select .txt, .docx, .rtf files")
    def test_ac1_select_txt_files(self, text_extractor, sample_files):
        with allure.step("Verify TextExtractor supports .txt files"):
            assert text_extractor.supports(Path("document.txt"))

    @allure.title("AC #2: Document text is extracted and stored")
    def test_ac2_text_extracted_and_stored(self, text_extractor, sample_files):
        with allure.step("Extract text from .txt file"):
            result = text_extractor.extract(sample_files.txt_file)
        with allure.step("Verify extraction succeeded"):
            assert isinstance(result, Success)
```

### Allure Annotation Hierarchy

| Level | Decorator | Maps To |
|-------|-----------|---------|
| Epic | `@allure.epic("QualCoder v2")` | Product |
| Feature | `@allure.feature("QC-027 Manage Sources")` | Parent task |
| Story | `@allure.story("QC-027.01 Import Text")` | Subtask |
| Title | `@allure.title("AC #1: ...")` | Acceptance criterion |
| Step | `with allure.step("...")` | Test steps |

### Test Organization

```
src/presentation/tests/
├── test_manage_sources_e2e.py   # QC-027 - one file per parent task
│   ├── TestImportTextDocument   # QC-027.01 - one class per subtask
│   │   ├── test_ac1_*           # AC #1
│   │   └── test_ac2_*           # AC #2
└── test_case_manager_e2e.py     # QC-026
```

### Naming Convention

```python
# Pattern: test_ac{N}_{brief_description}
def test_ac1_select_txt_files(self):       # AC #1
def test_ac2_text_extracted_and_stored(self):  # AC #2

# Additional tests beyond ACs use descriptive names
def test_handles_unicode_content(self):
```

### Persistence Testing

```python
@allure.title("Imported sources persist between sessions")
def test_imported_sources_persist_after_reopen(self, tmp_path):
    project_path = tmp_path / "persist_test.qda"

    with allure.step("Step 1: Create project and import source"):
        ctx = create_app_context()
        ctx.start()
        ctx.create_project(name="Test", path=str(project_path))
        source = Source(id=SourceId(1), name="test.txt", fulltext="Content")
        ctx.sources_context.source_repo.save(source)

    with allure.step("Step 2: Close project"):
        ctx.close_project()
        reset_app_context()

    with allure.step("Step 3: Reopen and verify"):
        ctx2 = create_app_context()
        ctx2.open_project(str(project_path))
        loaded = ctx2.sources_context.source_repo.get_by_id(SourceId(1))
        assert loaded.fulltext == "Content"
```

### Fixture Hierarchy

```python
@pytest.fixture
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    create_all(engine)
    yield engine
    drop_all(engine)

@pytest.fixture
def case_repo(db_connection):
    return SQLiteCaseRepository(db_connection)

@pytest.fixture
def viewmodel(case_repo, event_bus):
    return CaseManagerViewModel(case_repo=case_repo, event_bus=event_bus)
```

### Running Tests

```bash
QT_QPA_PLATFORM=offscreen uv run pytest src/presentation/tests/test_manage_sources_e2e.py -v
QT_QPA_PLATFORM=offscreen uv run pytest --alluredir=allure-results
allure serve allure-results
```

---

## Section Separators

```python
# =============================================================================
# Code Commands
# =============================================================================

def create_code(self, command): ...

# =============================================================================
# Queries
# =============================================================================

def get_all_codes(self) -> list[Code]: ...
```

---

## Quick Checklist

- [ ] Imports ordered: future → stdlib → third-party → local → TYPE_CHECKING
- [ ] Docstrings present for modules, classes, public methods
- [ ] Result types used for fallible operations
- [ ] Entities are frozen dataclasses
- [ ] Events follow naming: `{Action}` for success, `{Action}Not{Done}/{Reason}` for failure
- [ ] Controllers follow 5-step pattern
- [ ] Payloads use primitives only (no domain objects)
- [ ] Tests use `test_ac{N}_*` naming for acceptance criteria
- [ ] E2E tests use Allure annotations (`@allure.story`, `@allure.title`)
- [ ] Design system tokens used for UI styling
