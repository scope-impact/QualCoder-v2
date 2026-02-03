# DDD Workshop Pattern Refactoring Plan

## Overview

Restructure QualCoder v2 to **religiously follow** the ddd-workshop pattern where each bounded context is a complete vertical slice containing domain, infrastructure, and interface layers.

## Target Architecture

### ddd-workshop Pattern (Reference)

```
src/
├── contexts/
│   └── {context}/
│       ├── core/                    # Domain layer
│       │   ├── entities/            # Domain models with validation
│       │   ├── events/              # Domain events (success + failure)
│       │   ├── commandHandlers/     # Use cases with embedded derivers
│       │   └── policies.py          # Context-specific event reactions
│       ├── infra/                   # Infrastructure layer
│       │   ├── repositories/        # Data access
│       │   └── schema.py           # Database schema
│       └── interface/               # External API layer (NEW)
│           └── mcp_tools.py         # MCP tools for AI agents
└── shared/                          # Cross-cutting concerns ONLY
    ├── common/                      # Shared types
    │   ├── types.py                # TypedIds, Result monad
    │   └── events.py               # Base Event protocol
    ├── core/                        # Shared domain logic
    │   ├── validation.py           # Validation utilities
    │   └── policies.py             # Policy framework
    └── infra/                       # Shared infrastructure
        ├── event_bus.py            # Pub/sub backbone
        ├── signal_bridge/          # Qt signal bridging
        ├── ai/                     # AI providers
        └── migrations/             # Schema migrations
```

---

## Current Structure vs Target

| Current Location | Target Location | Rationale |
|------------------|-----------------|-----------|
| `src/contexts/{ctx}/core/` | `src/contexts/{ctx}/core/` | ✅ Keep as-is |
| `src/contexts/{ctx}/infra/` | `src/contexts/{ctx}/infra/` | ✅ Keep as-is |
| `src/application/{ctx}/usecases/` | `src/contexts/{ctx}/core/commandHandlers/` | Command handlers belong in context |
| `src/application/{ctx}/commands.py` | `src/contexts/{ctx}/core/commands.py` | Commands are domain DTOs |
| `src/infrastructure/mcp/{ctx}_tools.py` | `src/contexts/{ctx}/interface/mcp_tools.py` | Interface layer per context |
| `src/application/event_bus.py` | `src/shared/infra/event_bus.py` | Cross-cutting infrastructure |
| `src/application/signal_bridge/` | `src/shared/infra/signal_bridge/` | Qt-specific cross-cutting |
| `src/application/app_context.py` | `src/shared/infra/app_context.py` | Composition root |
| `src/application/state.py` | `src/shared/infra/state.py` | Cross-cutting state cache |
| `src/application/lifecycle.py` | `src/shared/infra/lifecycle.py` | Cross-cutting DB lifecycle |
| `src/application/policies/` | `src/shared/core/policies/` | Policy framework |
| `src/application/sync/` | `src/shared/core/sync/` | Cross-context sync handlers |
| `src/infrastructure/ai/` | `src/shared/infra/ai/` | Cross-cutting AI services |
| `src/infrastructure/migrations/` | `src/shared/infra/migrations/` | Cross-cutting schema evolution |
| `src/contexts/shared/` | `src/shared/` | Rename for clarity |

---

## Phase 1: Restructure `shared/` (Foundation)

### 1.1 Create new `src/shared/` structure

```bash
mkdir -p src/shared/{common,core,infra}
mkdir -p src/shared/infra/{signal_bridge,ai,migrations}
mkdir -p src/shared/core/{policies,sync}
```

### 1.2 Move from `src/contexts/shared/`

| From | To |
|------|-----|
| `src/contexts/shared/core/types.py` | `src/shared/common/types.py` |
| `src/contexts/shared/core/validation.py` | `src/shared/core/validation.py` |
| `src/contexts/shared/core/failure_events.py` | `src/shared/common/failure_events.py` |
| `src/contexts/shared/core/operation_result.py` | `src/shared/common/operation_result.py` |
| `src/contexts/shared/core/agent.py` | `src/shared/common/agent.py` |

### 1.3 Move from `src/application/`

| From | To |
|------|-----|
| `src/application/event_bus.py` | `src/shared/infra/event_bus.py` |
| `src/application/app_context.py` | `src/shared/infra/app_context.py` |
| `src/application/state.py` | `src/shared/infra/state.py` |
| `src/application/lifecycle.py` | `src/shared/infra/lifecycle.py` |
| `src/application/signal_bridge/` | `src/shared/infra/signal_bridge/` |
| `src/application/policies/` | `src/shared/core/policies/` |
| `src/application/sync/` | `src/shared/core/sync/` |

### 1.4 Move from `src/infrastructure/`

| From | To |
|------|-----|
| `src/infrastructure/ai/` | `src/shared/infra/ai/` |
| `src/infrastructure/migrations/` | `src/shared/infra/migrations/` |

### 1.5 Create barrel files

**`src/shared/__init__.py`:**
```python
"""Shared kernel - cross-cutting concerns only."""
from src.shared.common.types import (
    CodeId, SegmentId, SourceId, CategoryId, CaseId, FolderId,
    Success, Failure, Result,
)
from src.shared.common.operation_result import OperationResult
from src.shared.infra.event_bus import EventBus
```

---

## Phase 2: Restructure Bounded Contexts

### 2.1 Coding Context

**Current:**
```
src/contexts/coding/
├── core/
│   ├── entities.py
│   ├── events.py
│   ├── failure_events.py
│   ├── invariants.py
│   ├── derivers.py
│   └── services/
└── infra/
    ├── repositories.py
    └── schema.py

src/application/coding/
├── usecases/
│   ├── create_code.py
│   ├── rename_code.py
│   ├── apply_code.py
│   └── ...
└── commands.py

src/infrastructure/mcp/
└── coding_tools.py
```

**Target:**
```
src/contexts/coding/
├── core/
│   ├── entities.py          # Keep
│   ├── events.py             # Keep
│   ├── failure_events.py     # Keep
│   ├── invariants.py         # Keep
│   ├── derivers.py           # Keep
│   ├── commands.py           # Move from application
│   ├── services/             # Keep
│   ├── policies.py           # NEW: context-specific policies
│   └── commandHandlers/      # Move from application/usecases
│       ├── __init__.py
│       ├── create_code.py
│       ├── rename_code.py
│       ├── apply_code.py
│       ├── batch_apply_codes.py
│       ├── change_code_color.py
│       ├── create_category.py
│       ├── delete_category.py
│       ├── delete_code.py
│       ├── merge_codes.py
│       ├── move_code_to_category.py
│       ├── remove_segment.py
│       ├── update_code_memo.py
│       └── queries.py
├── infra/
│   ├── repositories.py       # Keep
│   └── schema.py            # Keep
└── interface/                # NEW
    ├── __init__.py
    └── mcp_tools.py          # Move from infrastructure/mcp
```

### 2.2 Cases Context

**Target:**
```
src/contexts/cases/
├── core/
│   ├── entities.py
│   ├── events.py
│   ├── failure_events.py
│   ├── invariants.py
│   ├── derivers.py
│   ├── commands.py           # NEW
│   ├── policies.py           # NEW
│   └── commandHandlers/      # Move from application
│       ├── __init__.py
│       ├── create_case.py
│       ├── update_case.py
│       ├── remove_case.py
│       ├── set_attribute.py
│       ├── remove_attribute.py
│       ├── link_source.py
│       ├── unlink_source.py
│       ├── get_case.py
│       └── list_cases.py
├── infra/
│   ├── case_repository.py
│   └── schema.py
└── interface/
    ├── __init__.py
    └── mcp_tools.py          # Move from infrastructure/mcp
```

### 2.3 Sources Context

**Target:**
```
src/contexts/sources/
├── core/
│   ├── entities.py
│   ├── events.py
│   ├── failure_events.py
│   ├── invariants.py
│   ├── derivers.py
│   ├── commands.py           # NEW
│   ├── policies.py           # NEW
│   ├── services/
│   └── commandHandlers/      # Move from application
│       ├── __init__.py
│       ├── add_source.py
│       ├── remove_source.py
│       ├── update_source.py
│       ├── get_source.py
│       └── list_sources.py
├── infra/
│   ├── source_repository.py
│   ├── folder_repository.py
│   ├── text_extractor.py
│   ├── pdf_extractor.py
│   ├── image_extractor.py
│   ├── media_extractor.py
│   └── schema.py
└── interface/
    ├── __init__.py
    └── mcp_tools.py          # NEW (source query tools)
```

### 2.4 Folders Context (Extract from Sources)

**Target:**
```
src/contexts/folders/
├── core/
│   ├── entities.py           # Extract from sources
│   ├── events.py
│   ├── failure_events.py
│   ├── invariants.py
│   ├── derivers.py
│   ├── commands.py
│   └── commandHandlers/      # Move from application
│       ├── __init__.py
│       ├── create_folder.py
│       ├── delete_folder.py
│       ├── rename_folder.py
│       ├── move_source.py
│       ├── get_folder.py
│       └── list_folders.py
├── infra/
│   ├── folder_repository.py  # Move from sources/infra
│   └── schema.py
└── interface/
    └── __init__.py
```

### 2.5 Projects Context

**Target:**
```
src/contexts/projects/
├── core/
│   ├── entities.py
│   ├── events.py
│   ├── failure_events.py
│   ├── invariants.py
│   ├── derivers.py
│   ├── commands.py           # Move from application
│   ├── policies.py           # NEW
│   └── commandHandlers/      # Move from application
│       ├── __init__.py
│       ├── create_project.py
│       ├── open_project.py
│       └── close_project.py
├── infra/
│   ├── project_repository.py
│   ├── settings_repository.py
│   └── schema.py
└── interface/
    ├── __init__.py
    └── mcp_tools.py          # Move from infrastructure/mcp
```

### 2.6 Settings Context

**Target:**
```
src/contexts/settings/
├── core/
│   ├── entities.py
│   ├── events.py
│   ├── failure_events.py
│   ├── invariants.py
│   ├── derivers.py
│   ├── commands.py           # Move from application
│   └── commandHandlers/      # Move from application
│       ├── __init__.py
│       ├── change_theme.py
│       ├── change_font.py
│       ├── change_language.py
│       ├── configure_backup.py
│       └── configure_av_coding.py
├── infra/
│   └── user_settings_repository.py
└── interface/
    └── __init__.py
```

### 2.7 AI Services Context

**Target:**
```
src/contexts/ai_services/
├── core/
│   ├── entities.py
│   ├── events.py
│   ├── failure_events.py
│   ├── invariants.py
│   ├── derivers.py
│   ├── protocols.py
│   ├── commands.py           # Move from application
│   └── commandHandlers/      # Move from application
│       ├── __init__.py
│       ├── suggest_codes.py
│       ├── approve_code_suggestion.py
│       ├── detect_duplicates.py
│       └── approve_merge.py
├── infra/                    # Move from infrastructure/ai
│   ├── __init__.py
│   ├── config.py
│   ├── llm_provider.py
│   ├── embedding_provider.py
│   ├── code_analyzer.py
│   ├── code_comparator.py
│   └── vector_store.py
└── interface/
    ├── __init__.py
    └── mcp_tools.py          # AI agent tools
```

---

## Phase 3: Command Handler Pattern

### 3.1 Standard Command Handler Template

Following ddd-workshop pattern, each command handler should:

```python
"""
{context}/core/commandHandlers/{operation}.py

Command handler for {operation}.
"""
from dataclasses import dataclass

from src.shared.common.types import Result, Success, Failure
from src.shared.common.operation_result import OperationResult
from src.shared.infra.event_bus import EventBus

from ..entities import Entity
from ..events import SuccessEvent
from ..failure_events import FailureEvent
from ..derivers import derive_operation
from ...infra.repositories import EntityRepository


# Command DTO
# -----------

@dataclass(frozen=True)
class OperationCommand:
    """Command data for operation."""
    field: str


# State type
# ----------

@dataclass(frozen=True)
class OperationState:
    """State needed for deriving event."""
    existing: Entity | None


# Command handler
# ---------------

def handle_operation(
    command: OperationCommand,
    repository: EntityRepository,
    event_bus: EventBus,
) -> OperationResult[Entity]:
    """
    Handle operation command.

    Steps:
    1. Parse/validate command data
    2. Fetch state from repository
    3. Derive event using pure deriver
    4. Update state (persist)
    5. Publish and return event
    """
    # Step 1: Validate command
    if not command.field:
        return OperationResult.fail(
            error="Field is required",
            error_code="EMPTY_FIELD",
        )

    # Step 2: Fetch state
    existing = repository.get_by_field(command.field)
    state = OperationState(existing=existing)

    # Step 3: Derive event (pure function)
    event = derive_operation(command, state)

    # Step 4: Update state based on event type
    match event:
        case SuccessEvent():
            entity = Entity(...)
            repository.save(entity)
        case FailureEvent():
            return OperationResult.fail(
                error=event.reason,
                error_code=event.code,
            )

    # Step 5: Publish and return
    event_bus.publish(event)

    return OperationResult.ok(
        data=entity,
        rollback=DeleteCommand(id=entity.id),
    )
```

### 3.2 Deriver stays in `derivers.py`

Unlike ddd-workshop which embeds derivers in handlers, we keep derivers in `derivers.py` because:
- Python's module system makes imports cleaner
- Derivers are pure and independently testable
- Multiple handlers might share derivers

---

## Phase 4: Context-Specific Policies

### 4.1 Policy Pattern

Each context defines its own policies in `{context}/core/policies.py`:

```python
"""
coding/core/policies.py

Policies for coding context - reactions to domain events.
"""
from src.shared.core.policies import configure_policy
from src.contexts.sources.core.events import SourceRemoved

from .commandHandlers.remove_segment import handle_remove_segments_for_source


def configure_coding_policies(segment_repository, event_bus):
    """Configure coding context policies."""

    # When source is removed, clean up segments
    configure_policy(
        event_type=SourceRemoved,
        actions={
            "DELETE_SEGMENTS": lambda e: handle_remove_segments_for_source(
                source_id=e.source_id,
                repository=segment_repository,
                event_bus=event_bus,
            ),
        },
        description="Clean up segments when source is deleted",
    )
```

---

## Phase 5: Interface Layer (MCP Tools)

### 5.1 MCP Tools per Context

Each context exposes its tools in `{context}/interface/mcp_tools.py`:

```python
"""
coding/interface/mcp_tools.py

MCP tools for AI agent access to coding operations.
"""
from src.shared.common.operation_result import OperationResult
from src.shared.infra.mcp import ToolDefinition, ToolParameter

from ..core.commandHandlers.batch_apply_codes import (
    handle_batch_apply_codes,
    BatchApplyCodesCommand,
)
from ..core.commandHandlers.queries import get_all_codes, get_segments_for_source


def create_coding_tools(coding_context, event_bus):
    """Create MCP tools for coding context."""

    return [
        ToolDefinition(
            name="batch_apply_codes",
            description="Apply multiple codes to text segments",
            parameters=[
                ToolParameter(name="source_id", type="string", required=True),
                ToolParameter(name="segments", type="array", required=True),
            ],
            handler=lambda params: handle_batch_apply_codes(
                command=BatchApplyCodesCommand(**params),
                context=coding_context,
                event_bus=event_bus,
            ),
        ),
        ToolDefinition(
            name="list_codes",
            description="Get all codes in the codebook",
            parameters=[],
            handler=lambda params: get_all_codes(coding_context.code_repo),
        ),
        # ... more tools
    ]
```

---

## Phase 6: Update Imports

### 6.1 Global Search-Replace Patterns

| Old Import | New Import |
|------------|------------|
| `from src.contexts.shared.core.types import` | `from src.shared.common.types import` |
| `from src.application.event_bus import` | `from src.shared.infra.event_bus import` |
| `from src.application.app_context import` | `from src.shared.infra.app_context import` |
| `from src.application.state import` | `from src.shared.infra.state import` |
| `from src.application.{ctx}.usecases import` | `from src.contexts.{ctx}.core.commandHandlers import` |
| `from src.infrastructure.mcp.{ctx}_tools import` | `from src.contexts.{ctx}.interface.mcp_tools import` |
| `from src.infrastructure.ai import` | `from src.shared.infra.ai import` |

---

## Phase 7: Delete Old Structure

After migration and tests pass:

```bash
# Remove old application layer
rm -rf src/application/

# Remove old infrastructure layer
rm -rf src/infrastructure/

# Remove old shared location
rm -rf src/contexts/shared/
```

---

## Final Structure

```
src/
├── contexts/
│   ├── coding/
│   │   ├── __init__.py           # Public API
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── entities.py
│   │   │   ├── events.py
│   │   │   ├── failure_events.py
│   │   │   ├── invariants.py
│   │   │   ├── derivers.py
│   │   │   ├── commands.py
│   │   │   ├── policies.py
│   │   │   ├── services/
│   │   │   ├── commandHandlers/
│   │   │   └── tests/
│   │   ├── infra/
│   │   │   ├── __init__.py
│   │   │   ├── repositories.py
│   │   │   ├── schema.py
│   │   │   └── tests/
│   │   └── interface/
│   │       ├── __init__.py
│   │       ├── mcp_tools.py
│   │       └── tests/
│   ├── cases/
│   │   └── (same structure)
│   ├── sources/
│   │   └── (same structure)
│   ├── folders/
│   │   └── (same structure)
│   ├── projects/
│   │   └── (same structure)
│   ├── settings/
│   │   └── (same structure)
│   └── ai_services/
│       └── (same structure)
├── shared/
│   ├── __init__.py
│   ├── common/
│   │   ├── __init__.py
│   │   ├── types.py
│   │   ├── events.py
│   │   ├── failure_events.py
│   │   ├── operation_result.py
│   │   └── agent.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── validation.py
│   │   ├── policies/
│   │   │   ├── __init__.py
│   │   │   └── framework.py
│   │   └── sync/
│   │       └── source_sync_handler.py
│   └── infra/
│       ├── __init__.py
│       ├── event_bus.py
│       ├── app_context.py
│       ├── state.py
│       ├── lifecycle.py
│       ├── signal_bridge/
│       ├── ai/
│       └── migrations/
├── presentation/
│   └── (unchanged)
├── tests/
│   └── e2e/
└── main.py
```

---

## Migration Order

1. **Phase 1**: Create `src/shared/` and move cross-cutting concerns
2. **Phase 2.1**: Migrate `coding` context (largest, most complex)
3. **Phase 2.2**: Migrate `cases` context
4. **Phase 2.3**: Migrate `sources` context
5. **Phase 2.4**: Extract `folders` context
6. **Phase 2.5**: Migrate `projects` context
7. **Phase 2.6**: Migrate `settings` context
8. **Phase 2.7**: Migrate `ai_services` context
9. **Phase 6**: Update all imports
10. **Phase 7**: Delete old structure

---

## Testing Strategy

After each phase:

```bash
# Run all tests
QT_QPA_PLATFORM=offscreen make test-all

# Run specific context tests
QT_QPA_PLATFORM=offscreen uv run pytest src/contexts/coding/ -v

# Run E2E tests
QT_QPA_PLATFORM=offscreen uv run pytest src/tests/e2e/ -v
```

---

## Benefits of This Refactoring

1. **Complete Vertical Slices**: Each context owns domain → infra → interface
2. **Clear Boundaries**: No cross-context imports except through `shared/`
3. **Easier Navigation**: Find all coding-related code in `contexts/coding/`
4. **Simpler Mental Model**: Matches ddd-workshop pattern exactly
5. **Better Testability**: Each context is independently testable
6. **AI-Agent Friendly**: MCP tools co-located with domain they expose
