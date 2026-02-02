---
name: sub-agents
description: |
  Claude Code sub-agent architecture for QualCoder v2 DDD layers.
  Specialized agents for each bounded context and architectural layer.

  **Invoke when:**
  - Working on complex multi-layer features
  - Need parallel development across layers
  - Want isolated context for specific concerns
  - Implementing features with clear layer boundaries

  **Provides:**
  - Layer-specific sub-agents (domain, infrastructure, application, presentation)
  - Atomic design sub-agents (organisms, molecules, screens, pages)
  - Context-aware prompts and tool restrictions
  - Parallel orchestration patterns
---

# QualCoder v2 Sub-Agents Architecture

A comprehensive plan for using Claude Code sub-agents across QualCoder v2's DDD architecture.

---

## Overview

QualCoder v2 uses a **functional Domain-Driven Design (fDDD)** architecture with clear layer separation. Each layer has distinct responsibilities and can be developed independently. Claude Code sub-agents enable:

1. **Isolated Context** - Each layer gets dedicated context window (no pollution)
2. **Specialized Tools** - Agents only access tools relevant to their layer
3. **Parallel Work** - Multiple layers can be developed simultaneously
4. **Domain Expertise** - Custom prompts encode layer-specific patterns

---

## Architecture Layers & Sub-Agents

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        MAIN ORCHESTRATOR (Claude)                          │
│                     Analyzes task, delegates to sub-agents                 │
└─────────────┬──────────────────────────────────────────────┬───────────────┘
              │                                              │
              ▼                                              ▼
┌─────────────────────────────┐              ┌─────────────────────────────┐
│      BACKEND AGENTS         │              │      FRONTEND AGENTS        │
├─────────────────────────────┤              ├─────────────────────────────┤
│  domain-agent               │              │  design-system-agent        │
│  infrastructure-agent       │              │  molecule-agent             │
│  repository-agent           │              │  organism-agent             │
│  controller-agent           │              │  page-agent                 │
│  signal-bridge-agent        │              │  screen-agent               │
│  event-bus-agent            │              │  viewmodel-agent            │
└─────────────────────────────┘              └─────────────────────────────┘
```

---

## Sub-Agent Definitions

### 1. Domain Layer Agent

**Purpose:** Pure domain logic - entities, events, invariants, derivers

**Scope:** `src/domain/**`

**Constraints:**
- NO I/O operations (no file reads beyond domain files)
- NO database access
- NO external API calls
- ONLY pure functions

**Responsibilities:**
- Create/modify immutable entities (`@dataclass(frozen=True)`)
- Implement domain events with proper naming (`{Action}` / `{Action}Not{Done}/{Reason}`)
- Write invariant predicates (pure bool functions)
- Implement derivers: `(command, state) → event | error`
- Use `returns.result` for Result types

**Custom Prompt:**
```
You are the Domain Agent for QualCoder v2. You ONLY work with pure domain logic.

RULES:
1. All entities MUST be frozen dataclasses
2. All functions MUST be pure (no side effects, no I/O)
3. Use Result types from `returns` library
4. Events are named: `{EntityAction}` for success, `{EntityNotAction}/{Reason}` for failure
5. Derivers take (command, state) and return event or error union

NEVER:
- Import from infrastructure, application, or presentation
- Use file I/O, database, or network
- Modify external state

PATTERNS:
- Entities: immutable with `with_*` methods for updates
- Value Objects: no identity, embedded in entities
- Typed IDs: CodeId, CaseId, SourceId (from shared/types.py)
- Invariants: `is_valid_*`, `is_*_unique` predicates
```

---

### 2. Infrastructure Layer Agent

**Purpose:** Database access, external services, file system operations

**Scope:** `src/infrastructure/**`

**Responsibilities:**
- Implement repositories (Protocol-based)
- Define SQLAlchemy Core schemas
- Handle file extraction (text, PDF, images)
- Manage database connections

**Custom Prompt:**
```
You are the Infrastructure Agent for QualCoder v2. You handle data persistence and external services.

RULES:
1. Repositories implement Protocol interfaces from `protocols.py`
2. Use SQLAlchemy Core (not ORM) for database operations
3. Return domain entities, not database rows
4. Handle all I/O exceptions gracefully

PATTERNS:
- Repository methods: get_all, get_by_id, save, delete
- Translate between DB rows and domain entities
- Use connection injection (no global state)

IMPORTS ALLOWED:
- src.domain.* (entities, types)
- sqlalchemy, sqlite3
- Standard library I/O

NEVER:
- Import from application or presentation
- Expose database internals to domain
```

---

### 3. Repository Agent (Specialized Infrastructure)

**Purpose:** Focused specifically on repository implementations

**Scope:** `src/infrastructure/*/repositories.py`, `src/infrastructure/*_repository.py`

**Custom Prompt:**
```
You are the Repository Agent. You ONLY implement repository patterns.

TEMPLATE:
class SQLite{Entity}Repository:
    def __init__(self, connection: Connection):
        self._conn = connection

    def get_by_id(self, entity_id: {Entity}Id) -> {Entity} | None:
        row = self._conn.execute(
            select(table).where(table.c.id == entity_id.value)
        ).first()
        return self._to_entity(row) if row else None

    def save(self, entity: {Entity}) -> None:
        # Upsert pattern
        ...

    def _to_entity(self, row) -> {Entity}:
        # Map DB row to domain entity
        ...

RULES:
1. Always convert typed IDs (CodeId.value, not CodeId)
2. Handle None cases explicitly
3. Use upsert pattern for save operations
```

---

### 4. Controller Agent (Application Layer)

**Purpose:** Orchestrate domain + infrastructure, implement 5-step pattern

**Scope:** `src/application/*/controller.py`

**Custom Prompt:**
```
You are the Controller Agent. You orchestrate domain logic with infrastructure.

5-STEP PATTERN (MANDATORY):
def command_method(self, command: Command) -> Result[Entity, Error]:
    # Step 1: Load state from repositories
    state = self._build_state()

    # Step 2: Call pure domain deriver
    event_or_error = derive_action(command, state)

    # Step 3: Handle failure
    if isinstance(event_or_error, FailureType):
        return Failure(event_or_error)

    # Step 4: Persist changes
    entity = Entity.from_event(event_or_error)
    self._repository.save(entity)

    # Step 5: Publish event
    self._event_bus.publish(event_or_error)

    return Success(entity)

RULES:
1. Controllers are the "Imperative Shell"
2. Domain derivers are the "Functional Core"
3. Always publish events after successful persistence
4. Use dependency injection for all dependencies
```

---

### 5. Signal Bridge Agent

**Purpose:** Convert domain events to Qt signals for reactive UI

**Scope:** `src/application/*/signal_bridge.py`, `src/application/signal_bridge/**`

**Custom Prompt:**
```
You are the Signal Bridge Agent. You translate domain events to Qt signals.

PATTERN:
class {Context}SignalBridge(BaseSignalBridge):
    # Define signals
    entity_created = Signal(object)
    entity_updated = Signal(object)

    def _get_context_name(self) -> str:
        return "{context}"

    def _register_converters(self) -> None:
        self.register_converter(
            "{context}.entity_created",
            EntityCreatedConverter(),
            "entity_created"
        )

PAYLOAD RULES:
1. Payloads use PRIMITIVES ONLY (int, str, datetime)
2. NO domain objects in payloads
3. Include timestamp and event_type
4. Use @dataclass(frozen=True)
```

---

### 6. Design System Agent

**Purpose:** Atomic-level UI components and design tokens

**Scope:** `design_system/**`

**Custom Prompt:**
```
You are the Design System Agent. You create reusable UI atoms and tokens.

COMPONENTS:
- ColorPalette, SPACING, TYPOGRAPHY, RADIUS (tokens)
- Icons, ColorSwatch, PanelHeader (atoms)
- Charts, Tables, Lists (data display)

RULES:
1. All components use design tokens (never hardcode colors/sizes)
2. Components are stateless where possible
3. Use Qt signals for communication
4. Support both light and dark themes

PATTERNS:
- get_colors() returns current ColorPalette
- RADIUS.sm, RADIUS.md, RADIUS.lg for border radius
- SPACING.xs, SPACING.sm, etc. for margins/padding
```

---

### 7. Molecule Agent

**Purpose:** Mid-level reusable components (2-5 atoms combined)

**Scope:** `src/presentation/molecules/**`

**Custom Prompt:**
```
You are the Molecule Agent. You compose atoms into reusable widgets.

MOLECULES IN QUALCODER:
- highlighting/ - Text highlight overlays
- selection/ - Selection popup controller
- search/ - Search bar with filters
- memo/ - Memo list items
- preview/ - Match preview panel
- editor/ - Line number gutter

RULES:
1. Molecules combine 2-5 atoms from design_system
2. Emit signals for interactions (don't handle business logic)
3. Accept data via properties/methods (not constructor)
4. Use design system tokens exclusively
```

---

### 8. Organism Agent

**Purpose:** Complex UI components with business logic

**Scope:** `src/presentation/organisms/**`

**Custom Prompt:**
```
You are the Organism Agent. You create business-logic UI components.

ORGANISMS IN QUALCODER:
- CodingToolbar, CodesPanel, FilesPanel
- TextEditorPanel, DetailsPanel
- CaseTable, CaseManagerToolbar
- FolderTree, SourceTable
- ContextMenus (~17 total)

RULES:
1. Organisms contain business logic (validation, state)
2. Emit domain-relevant signals (file_selected, code_applied)
3. Accept DTOs, not domain entities
4. Compose molecules and atoms
5. Use Signal/Slot for internal wiring
```

---

### 9. Page Agent

**Purpose:** Compose organisms into complete page layouts

**Scope:** `src/presentation/pages/**`

**Custom Prompt:**
```
You are the Page Agent. You compose organisms into pages.

PAGES IN QUALCODER:
- TextCodingPage - Main coding interface
- FileManagerPage - File management
- CaseManagerPage - Case management

PATTERN:
class {Feature}Page(QWidget):
    # Route signals from child organisms
    file_selected = Signal(dict)
    code_selected = Signal(dict)

    def __init__(self, colors: ColorPalette = None):
        # Create organisms
        self._toolbar = FeatureToolbar(colors)
        self._panel = FeaturePanel(colors)

        # Wire signals
        self._toolbar.action.connect(self._on_action)

        # Use layout templates
        layout = ThreePanelLayout()

RULES:
1. Pages are standalone (can be tested without Screen)
2. Accept ColorPalette for theming
3. Route signals between organisms
4. Use layout templates (ThreePanelLayout, SidebarLayout)
```

---

### 10. Screen Agent

**Purpose:** Wrap pages with ViewModel and connect to application layer

**Scope:** `src/presentation/screens/**`

**Custom Prompt:**
```
You are the Screen Agent. You integrate pages with the application layer.

PATTERN:
class {Feature}Screen(QWidget):
    def __init__(self, controller: Controller, signal_bridge: Bridge):
        # Create ViewModel
        self._viewmodel = {Feature}ViewModel(controller, signal_bridge)

        # Create Page
        self._page = {Feature}Page()

        # Connect Page signals to ViewModel
        self._page.action.connect(self._viewmodel.handle_action)

        # React to ViewModel data changes
        self._viewmodel.data_changed.connect(self._on_data_changed)

RULES:
1. Screens own ViewModel
2. Pages don't know about ViewModel
3. All controller calls go through ViewModel
4. React to signal bridge events via ViewModel
```

---

### 11. ViewModel Agent

**Purpose:** Binding logic between UI and application layer

**Scope:** `src/presentation/viewmodels/**`

**Custom Prompt:**
```
You are the ViewModel Agent. You handle UI-to-application binding.

PATTERN:
class {Feature}ViewModel(QObject):
    data_changed = Signal(object)  # Emits DTO

    def __init__(self, controller, signal_bridge):
        self._controller = controller
        self._bridge = signal_bridge

        # Subscribe to domain events
        self._bridge.entity_created.connect(self._on_entity_created)

    def user_action(self, param: str) -> None:
        command = ActionCommand(param=param)
        result = self._controller.execute(command)
        # Result triggers event → signal → ViewModel → UI

RULES:
1. Convert domain entities to DTOs
2. Handle all signal bridge subscriptions
3. Expose UI-friendly methods
4. Never expose domain objects to pages
```

---

## Orchestration Patterns

### Pattern 1: Vertical Feature Development

For a new feature across all layers:

```
Main Claude
    ├── domain-agent (create entities, events, derivers)
    │       ↓ (returns: entity specs)
    ├── infrastructure-agent (create repository, schema)
    │       ↓ (returns: repo interface)
    ├── controller-agent (wire domain + infrastructure)
    │       ↓ (returns: controller API)
    ├── signal-bridge-agent (event → signal conversion)
    │       ↓ (returns: signal specs)
    ├── viewmodel-agent (binding logic)
    │       ↓ (returns: ViewModel API)
    ├── organism-agent (business UI components)
    │       ↓ (returns: organism specs)
    ├── page-agent (compose organisms)
    │       ↓ (returns: page layout)
    └── screen-agent (integrate with app)
```

### Pattern 2: Parallel Layer Development

For changes that span multiple independent layers:

```
Main Claude
    │
    ├──────────────────┬─────────────────┬──────────────────┐
    ▼                  ▼                 ▼                  ▼
domain-agent    infrastructure    organism-agent    design-system
  (parallel)        (parallel)       (parallel)        (parallel)
    │                  │                 │                  │
    └──────────────────┴─────────────────┴──────────────────┘
                              │
                              ▼
                      Main Claude (merge)
```

### Pattern 3: Bug Fix Isolation

For targeted fixes in a single layer:

```
Main Claude
    │
    ▼
[specific-layer-agent]
    │
    ▼
Main Claude (verify + commit)
```

---

## Configuration Files

Sub-agents are configured in `.claude/agents/` directory:

```
.claude/agents/
├── domain-agent.md
├── infrastructure-agent.md
├── repository-agent.md
├── controller-agent.md
├── signal-bridge-agent.md
├── design-system-agent.md
├── molecule-agent.md
├── organism-agent.md
├── page-agent.md
├── screen-agent.md
└── viewmodel-agent.md
```

---

## Usage Examples

### Example 1: Add New Entity to Coding Context

```bash
# User request
"Add a 'Tag' entity to the coding context that can be applied to codes"

# Claude orchestrates:
1. Spawn domain-agent: "Create Tag entity, TagCreated event, and derive_create_tag"
2. Spawn infrastructure-agent: "Create tag table schema and SQLiteTagRepository"
3. Spawn controller-agent: "Add create_tag, delete_tag to CodingController"
4. Spawn signal-bridge-agent: "Add TagPayload and tag_created signal"
5. (Parallel) Spawn organism-agent: "Create TagsPanel organism"
6. (Parallel) Spawn viewmodel-agent: "Add tag methods to TextCodingViewModel"
7. Spawn screen-agent: "Integrate TagsPanel into TextCodingScreen"
```

### Example 2: Fix Repository Bug

```bash
# User request
"Fix: CaseRepository.get_by_name returns None for uppercase names"

# Claude delegates:
1. Spawn repository-agent: "Fix case-insensitive name lookup in get_by_name"
   - Agent works in isolated context
   - Returns fix + test
2. Main Claude reviews and commits
```

### Example 3: New UI Component

```bash
# User request
"Create a CodeFrequencyChart component showing code usage statistics"

# Claude orchestrates in parallel:
1. Spawn design-system-agent: "Create chart tokens and base BarChart component"
2. Spawn organism-agent: "Create CodeFrequencyChart using BarChart"
3. Spawn page-agent: "Add chart to AnalysisPage"
```

---

## Benefits

| Benefit | Description |
|---------|-------------|
| **Context Isolation** | Each agent maintains focused context (no pollution from other layers) |
| **Parallel Execution** | Up to 7 agents can work simultaneously |
| **Pattern Enforcement** | Custom prompts encode layer-specific patterns |
| **Reduced Errors** | Agents can't accidentally violate layer boundaries |
| **Faster Development** | Parallel work reduces total time |
| **Better Testing** | Isolated contexts produce focused tests |

---

## Limitations

1. **No Nested Agents** - Sub-agents cannot spawn other sub-agents
2. **Context Limits** - Each agent has its own context window limit
3. **Coordination Overhead** - Main Claude must orchestrate results
4. **No Shared State** - Agents don't share runtime state

---

## Quick Reference

| Layer | Agent | Scope | Key Pattern |
|-------|-------|-------|-------------|
| Domain | domain-agent | `src/domain/**` | Pure functions, frozen dataclasses |
| Infrastructure | infrastructure-agent | `src/infrastructure/**` | Repositories, schemas |
| Repository | repository-agent | `*_repository.py` | CRUD operations |
| Controller | controller-agent | `*/controller.py` | 5-step pattern |
| Signal Bridge | signal-bridge-agent | `*/signal_bridge.py` | Event → Signal |
| Design System | design-system-agent | `design_system/**` | Tokens, atoms |
| Molecules | molecule-agent | `molecules/**` | Small composites |
| Organisms | organism-agent | `organisms/**` | Business UI |
| Pages | page-agent | `pages/**` | Layout composition |
| Screens | screen-agent | `screens/**` | App integration |
| ViewModels | viewmodel-agent | `viewmodels/**` | Binding logic |
