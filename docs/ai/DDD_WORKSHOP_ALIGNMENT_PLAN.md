# DDD Workshop Alignment Plan for QualCoder-v2

## Executive Summary

This plan aligns QualCoder-v2 with ddd-workshop patterns through four key initiatives:

| Initiative | Priority | Scope | Breaking Changes |
|------------|----------|-------|------------------|
| 1. Explicit Failure Events | High | Domain + Application | Low (backwards-compatible) |
| 2. Policy Pattern | High | Application | None (additive) |
| 3. Repository Mappers | Medium | Infrastructure | None (internal refactor) |
| 4. Bounded Context Restructure | High | All layers | High (all imports change) |

**Implementation order**: 1 → 2 → 3 → 4

---

## Initiative 1: Explicit Failure Events

### Goal
Replace `Failure(reason)` pattern with first-class failure events that can be published and trigger policies.

### Current Pattern (QualCoder)
```python
def derive_create_project(...) -> ProjectCreated | Failure:
    if not is_valid_project_name(name):
        return Failure(EmptyProjectName())  # Not publishable
```

### Target Pattern (ddd-workshop)
```python
def derive_create_project(...) -> ProjectCreated | ProjectNotCreated:
    if not is_valid_project_name(name):
        return ProjectNotCreated.empty_name()  # Publishable event
```

### Implementation Steps

#### Step 1.1: Create Base FailureEvent Class
**File**: `src/domain/shared/failure_events.py`

```python
@dataclass(frozen=True)
class FailureEvent:
    """Base class for publishable failure events."""
    event_id: str
    occurred_at: datetime
    event_type: str  # e.g., "PROJECT_NOT_CREATED/EMPTY_NAME"

    @property
    def is_failure(self) -> bool:
        return True

    @property
    def operation(self) -> str:
        return self.event_type.split("/")[0]

    @property
    def reason(self) -> str:
        parts = self.event_type.split("/")
        return parts[1] if len(parts) > 1 else ""
```

#### Step 1.2: Create Failure Events per Context
**File**: `src/domain/projects/failure_events.py`

```python
@dataclass(frozen=True)
class ProjectNotCreated(FailureEvent):
    name: str | None = None
    path: Path | None = None

    @classmethod
    def empty_name(cls) -> "ProjectNotCreated":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="PROJECT_NOT_CREATED/EMPTY_NAME",
        )

    @classmethod
    def already_exists(cls, path: Path) -> "ProjectNotCreated":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="PROJECT_NOT_CREATED/ALREADY_EXISTS",
            path=path,
        )
```

#### Step 1.3: Update Derivers
**File**: `src/domain/projects/derivers.py`

```python
# BEFORE
def derive_create_project(...) -> ProjectCreated | Failure:
    if not is_valid_project_name(name):
        return Failure(EmptyProjectName())

# AFTER
def derive_create_project(...) -> ProjectCreated | ProjectNotCreated:
    if not is_valid_project_name(name):
        return ProjectNotCreated.empty_name()
```

#### Step 1.4: Update Use Cases to Publish Failures
```python
result = derive_create_project(...)

if isinstance(result, FailureEvent):
    event_bus.publish(result)  # Now publishable!
    return Failure(result.event_type)  # Backwards compatible

event_bus.publish(result)
return Success(...)
```

### Files to Modify
- `src/domain/shared/failure_events.py` (new)
- `src/domain/projects/failure_events.py` (new)
- `src/domain/projects/derivers.py`
- `src/domain/coding/failure_events.py` (new)
- `src/domain/coding/derivers.py`
- `src/application/projects/usecases/*.py`
- `src/application/coding/usecases/*.py`

### Event Naming Convention
**Format**: `{ENTITY}_NOT_{OPERATION}/{REASON}`

Examples:
- `PROJECT_NOT_CREATED/EMPTY_NAME`
- `PROJECT_NOT_CREATED/ALREADY_EXISTS`
- `SOURCE_NOT_ADDED/DUPLICATE_NAME`
- `FOLDER_NOT_DELETED/NOT_EMPTY`
- `CODE_NOT_CREATED/INVALID_COLOR`

---

## Initiative 2: Policy Pattern

### Goal
Replace ad-hoc event subscriptions with declarative policy declarations for cross-context reactions.

### Current Pattern (QualCoder)
```python
# In SourceSyncHandler - imperative subscriptions
self._event_bus.subscribe("projects.source_removed", self._on_source_removed)
```

### Target Pattern (ddd-workshop)
```python
configure_policy(
    event_type=SourceRemoved,
    actions={
        "DELETE_SEGMENTS": remove_source_segments,
        "UNLINK_CASES": unlink_source_from_cases,
    },
    description="Cleanup when a source is removed"
)
```

### Implementation Steps

#### Step 2.1: Create Policy Infrastructure
**Directory**: `src/application/policies/`

```
src/application/policies/
    __init__.py           # configure_policy, PolicyExecutor exports
    base.py               # PolicyDefinition, PolicyAction types
    registry.py           # PolicyRegistry singleton
    executor.py           # PolicyExecutor (EventBus integration)
    projects_policies.py  # Source, folder policies
    coding_policies.py    # Code, category policies
    tests/
```

#### Step 2.2: Core Policy API
**File**: `src/application/policies/__init__.py`

```python
def configure_policy(
    event_type: type[E],
    actions: dict[str, PolicyAction],
    description: str = "",
) -> PolicyDefinition[E]:
    """
    Configure a declarative policy for a domain event.

    Args:
        event_type: The domain event class to react to
        actions: Dict mapping action names to async functions
        description: Human-readable description
    """
    definition = PolicyDefinition(event_type, actions, description)
    get_policy_registry().register(definition)
    return definition
```

#### Step 2.3: PolicyExecutor
**File**: `src/application/policies/executor.py`

```python
class PolicyExecutor:
    """Executes policy actions in response to domain events."""

    def __init__(self, event_bus: EventBus, registry: PolicyRegistry | None = None):
        self._event_bus = event_bus
        self._registry = registry or get_policy_registry()

    def start(self) -> None:
        self._subscription = self._event_bus.subscribe_all(self._handle_event)

    def _handle_event(self, event: Any) -> None:
        actions = self._registry.get_actions(event.event_type)
        for action_name, action_fn in actions:
            try:
                action_fn(event)
            except Exception as e:
                logger.error(f"Policy '{action_name}' failed: {e}")
```

#### Step 2.4: Define Context Policies
**File**: `src/application/policies/projects_policies.py`

```python
def configure_projects_policies() -> None:
    configure_policy(
        event_type=SourceRemoved,
        actions={
            "DELETE_SEGMENTS": sync_segment_source_name_on_remove,
            "UNLINK_CASES": unlink_cases_on_source_remove,
        },
        description="Cleanup when a source is removed"
    )

    configure_policy(
        event_type=SourceRenamed,
        actions={
            "SYNC_SEGMENT_NAME": sync_segment_source_name_on_rename,
            "SYNC_CASE_LINK_NAME": sync_case_link_source_name_on_rename,
        },
        description="Sync denormalized names when source renamed"
    )
```

#### Step 2.5: Wire to ApplicationCoordinator
**File**: `src/application/coordinator.py`

```python
def __init__(self, ...):
    # Configure policies
    configure_projects_policies()
    configure_coding_policies()

    # Create executor
    self._policy_executor = PolicyExecutor(self._event_bus)

def start(self) -> None:
    self._policy_executor.start()
    # Remove old: self._source_sync_handler.start()
```

### Identified Policies to Implement

| Event | Policy Actions | Current Location |
|-------|---------------|-----------------|
| `SourceRemoved` | DELETE_SEGMENTS, UNLINK_CASES | SourceSyncHandler, use case |
| `SourceRenamed` | SYNC_SEGMENT_NAME, SYNC_CASE_LINK_NAME | SourceSyncHandler |
| `CodeDeleted` | (cascade handled in use case) | use case |
| `CategoryDeleted` | ORPHAN_CODES | to be implemented |
| `FolderDeleted` | ORPHAN_FOLDER_SOURCES | to be implemented |

### Files to Create/Modify
- `src/application/policies/__init__.py` (new)
- `src/application/policies/base.py` (new)
- `src/application/policies/registry.py` (new)
- `src/application/policies/executor.py` (new)
- `src/application/policies/projects_policies.py` (new)
- `src/application/policies/coding_policies.py` (new)
- `src/application/coordinator.py` (modify)
- `src/application/sync/source_sync_handler.py` (eventually remove)

---

## Initiative 3: Repository Mapper Pattern

### Goal
Enforce explicit mapper functions between domain entities and database schemas.

### Current Pattern (Mixed)
Some repositories inline mapping, others don't have clear separation.

### Target Pattern (ddd-workshop)
```python
def _to_code(row: Row) -> Code:
    """Map database row to domain entity."""
    return Code(
        id=CodeId(row.cod_id),
        name=row.cod_name,
        color=row.cod_color,
        ...
    )

def _to_code_data(code: Code) -> dict:
    """Map domain entity to database format."""
    return {
        "cod_id": code.id.value,
        "cod_name": code.name,
        "cod_color": code.color,
        ...
    }
```

### Implementation Steps

#### Step 3.1: Audit Current Repositories
- `src/infrastructure/coding/repositories.py`
- `src/infrastructure/projects/project_repository.py`
- `src/infrastructure/cases/case_repository.py`

#### Step 3.2: Extract Mapper Functions
For each repository, create explicit `_to_{entity}` and `_to_{entity}_data` functions.

#### Step 3.3: Validate on Boundary
Mappers should call entity constructors which enforce invariants.

### Files to Modify
- `src/infrastructure/coding/repositories.py`
- `src/infrastructure/projects/project_repository.py`
- `src/infrastructure/cases/` (if exists)
- `src/infrastructure/sources/source_repository.py`

---

## Initiative 4: Bounded Context Restructure

### Goal
Co-locate domain and infrastructure by bounded context instead of by layer.

### Current Structure
```
src/
├── domain/
│   ├── coding/
│   ├── projects/
│   ├── cases/
│   ├── settings/
│   └── shared/
├── infrastructure/
│   ├── coding/
│   ├── projects/
│   ├── cases/
│   ├── settings/
│   └── sources/
```

### Target Structure
```
src/contexts/
├── coding/
│   ├── __init__.py      # Public API exports
│   ├── core/            # Domain layer
│   │   ├── entities.py
│   │   ├── events.py
│   │   ├── derivers.py
│   │   ├── invariants.py
│   │   ├── failure_events.py
│   │   └── tests/
│   └── infra/           # Infrastructure layer
│       ├── repositories.py
│       ├── schema.py
│       └── tests/
├── projects/
│   ├── core/
│   └── infra/
├── cases/
│   ├── core/
│   └── infra/
├── settings/
│   ├── core/
│   └── infra/
├── sources/
│   ├── core/
│   └── infra/
└── shared/              # Shared kernel
    ├── core/
    │   ├── types.py
    │   ├── validation.py
    │   ├── failure_events.py  # Base FailureEvent
    │   └── agent.py
    └── infra/
        └── protocols.py
```

### Implementation Steps

#### Step 4.1: Create Directory Structure
```bash
mkdir -p src/contexts/{coding,projects,cases,settings,sources,shared}/{core,infra}
mkdir -p src/contexts/{coding,projects,cases,settings,sources}/core/tests
mkdir -p src/contexts/{coding,projects,cases,settings,sources}/infra/tests
mkdir -p src/contexts/shared/core/tests
```

#### Step 4.2: Migrate Shared Kernel First
Move shared types (lowest dependencies):
- `src/domain/shared/types.py` → `src/contexts/shared/core/types.py`
- `src/domain/shared/validation.py` → `src/contexts/shared/core/validation.py`
- `src/domain/shared/agent.py` → `src/contexts/shared/core/agent.py`
- `src/infrastructure/protocols.py` → `src/contexts/shared/infra/protocols.py`

Create backward-compatible re-exports:
```python
# src/domain/shared/__init__.py
from src.contexts.shared.core.types import *
from src.contexts.shared.core.validation import *
```

#### Step 4.3: Migrate Coding Context (Pilot)
Domain files:
- `src/domain/coding/entities.py` → `src/contexts/coding/core/entities.py`
- `src/domain/coding/events.py` → `src/contexts/coding/core/events.py`
- `src/domain/coding/derivers.py` → `src/contexts/coding/core/derivers.py`
- `src/domain/coding/invariants.py` → `src/contexts/coding/core/invariants.py`
- `src/domain/coding/tests/` → `src/contexts/coding/core/tests/`

Infrastructure files:
- `src/infrastructure/coding/repositories.py` → `src/contexts/coding/infra/repositories.py`
- `src/infrastructure/coding/schema.py` → `src/contexts/coding/infra/schema.py`
- `src/infrastructure/coding/tests/` → `src/contexts/coding/infra/tests/`

Create public API:
```python
# src/contexts/coding/__init__.py
"""Coding bounded context - public API."""
from src.contexts.coding.core.entities import Code, Category, TextSegment
from src.contexts.coding.core.events import CodeCreated, CodeDeleted
from src.contexts.coding.infra.repositories import SQLiteCodeRepository
```

#### Step 4.4: Migrate Remaining Contexts
Order by dependency (least to most):
1. `cases` - minimal dependencies
2. `settings` - depends on projects entities
3. `sources` - depends on projects, has extractors
4. `projects` - most dependencies, schema coordination

#### Step 4.5: Update All Imports
Use automated tools to update imports:
```bash
# Find and replace imports
find src -name "*.py" -exec sed -i '' \
  's/from src.domain.coding/from src.contexts.coding.core/g' {} +
find src -name "*.py" -exec sed -i '' \
  's/from src.infrastructure.coding/from src.contexts.coding.infra/g' {} +
```

#### Step 4.6: Handle Cross-Context Dependencies
For `sources` context which uses `projects` entities:
```python
# src/contexts/sources/core/entities.py
from src.contexts.projects.core.entities import Source, Folder
```

For schema coordination in `projects`:
```python
# src/contexts/projects/infra/schema.py
from src.contexts.coding.infra.schema import metadata as coding_metadata
from src.contexts.cases.infra.schema import metadata as cases_metadata
# ... unified schema creation
```

#### Step 4.7: Create Context-Level __init__.py Files
Each context exposes a clean public API:
```python
# src/contexts/projects/__init__.py
"""Projects bounded context - public API."""

# Core (Domain)
from src.contexts.projects.core.entities import Project, Source, Folder
from src.contexts.projects.core.events import (
    ProjectCreated, SourceAdded, SourceRemoved, FolderCreated
)
from src.contexts.projects.core.derivers import (
    derive_create_project, derive_add_source
)
from src.contexts.projects.core.failure_events import (
    ProjectNotCreated, SourceNotAdded
)

# Infra
from src.contexts.projects.infra.repositories import SQLiteProjectRepository
```

#### Step 4.8: Remove Old Directories
After all tests pass:
```bash
rm -rf src/domain/
rm -rf src/infrastructure/coding/
rm -rf src/infrastructure/projects/
# etc.
```

### Import Convention After Migration

```python
# From application layer
from src.contexts.coding import Code, CodeCreated, SQLiteCodeRepository
from src.contexts.projects import Project, derive_create_project

# Direct access when needed
from src.contexts.coding.core.derivers import derive_create_code
from src.contexts.coding.infra.schema import codes_table
```

---

## Verification Plan

### Running Tests
```bash
# Full test suite
QT_QPA_PLATFORM=offscreen make test-all

# Specific layer tests
QT_QPA_PLATFORM=offscreen uv run pytest src/domain/ -v
QT_QPA_PLATFORM=offscreen uv run pytest src/application/ -v
QT_QPA_PLATFORM=offscreen uv run pytest src/infrastructure/ -v
```

### Manual Verification
1. Create a new project
2. Add sources, create folders
3. Create codes and segments
4. Delete a source → verify segments are cleaned up (policy test)
5. Rename a source → verify denormalized names update
6. Close and reopen project → verify state consistency

### Type Checking
```bash
uv run mypy src/
```

---

## Implementation Order

### Phase 1: Failure Events
1. Create `FailureEvent` base class in `src/domain/shared/failure_events.py`
2. Create failure events for `projects` context
3. Update `projects` derivers to return failure events
4. Update `projects` use cases to publish failures
5. Add tests for failure events
6. Repeat for `coding` context
7. Repeat for `cases` context

### Phase 2: Policy Pattern
1. Create policy infrastructure (`src/application/policies/`)
2. Define `projects_policies.py` (source removal/rename reactions)
3. Define `coding_policies.py` (category deletion reactions)
4. Wire PolicyExecutor to `ApplicationCoordinator`
5. Test policy execution end-to-end
6. Remove `SourceSyncHandler` (replaced by policies)

### Phase 3: Repository Mappers
1. Audit existing repositories for mapping patterns
2. Extract explicit `_to_{entity}` and `_to_{entity}_data` functions
3. Add entity validation in mapper functions
4. Update all repositories consistently

### Phase 4: Bounded Context Restructure
1. Create `src/contexts/` directory structure
2. Migrate `shared` kernel first (lowest dependencies)
3. Migrate `coding` context as pilot
4. Create backward-compatible re-exports at old locations
5. Run full test suite - fix any import issues
6. Migrate `cases` context
7. Migrate `settings` context
8. Migrate `sources` context (has extractors)
9. Migrate `projects` context (most dependencies, schema coordination)
10. Update all application layer imports
11. Update all presentation layer imports
12. Run full test suite
13. Remove old `src/domain/` and `src/infrastructure/` directories
14. Update any tooling/CI paths

---

## Critical Files Summary

| File | Purpose | Initiative |
|------|---------|------------|
| `src/domain/shared/failure_events.py` | Base failure event | 1 |
| `src/domain/projects/derivers.py` | Deriver updates | 1 |
| `src/domain/projects/failure_events.py` | Project failure events | 1 |
| `src/domain/coding/failure_events.py` | Coding failure events | 1 |
| `src/application/policies/__init__.py` | Policy API | 2 |
| `src/application/policies/executor.py` | EventBus integration | 2 |
| `src/application/policies/projects_policies.py` | Source policies | 2 |
| `src/application/coordinator.py` | Wire policies | 2 |
| `src/infrastructure/coding/repositories.py` | Mapper pattern | 3 |
| `src/infrastructure/projects/project_repository.py` | Mapper pattern | 3 |
| `src/contexts/shared/core/types.py` | Migrated shared types | 4 |
| `src/contexts/coding/__init__.py` | Context public API | 4 |
| `src/contexts/projects/__init__.py` | Context public API | 4 |

---

## Risk Mitigation

### Initiative 1 (Failure Events)
- **Risk**: Existing code depends on `Failure(reason)` pattern
- **Mitigation**: Keep backward compatibility in use cases by converting failure events to `Failure(event_type)` for return values

### Initiative 2 (Policies)
- **Risk**: Policies don't execute in the right order
- **Mitigation**: Test policies in isolation and integration; ensure idempotency

### Initiative 3 (Mappers)
- **Risk**: Data loss during mapping
- **Mitigation**: Add round-trip tests (entity → data → entity equality)

### Initiative 4 (Restructure)
- **Risk**: Breaking all imports causes massive churn
- **Mitigation**:
  1. Create re-export modules at old locations during transition
  2. Migrate one context at a time
  3. Run full test suite after each context migration
  4. Only remove old directories after all tests pass

---

## Success Criteria

1. **Failure Events**: `event_bus.history` contains failure events when operations fail
2. **Policies**: Deleting a source automatically removes segments (no manual cascade)
3. **Mappers**: Each repository has explicit `_to_*` and `_to_*_data` functions
4. **Restructure**: All code lives under `src/contexts/{context}/{core|infra}/`
