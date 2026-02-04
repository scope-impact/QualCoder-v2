# Refactoring Plan: Coordinator → AppContext

## Goal

Replace the 3-layer pattern (Coordinator → Sub-coordinators → Use Cases) with the ddd-workshop pattern (AppContext + direct use case calls).

## Current State

```
ApplicationCoordinator
├── CasesCoordinator      → usecases/create_case.py, etc.
├── SourcesCoordinator    → usecases/add_source.py, etc.
├── FoldersCoordinator    → usecases/create_folder.py, etc.
├── CodingCoordinator     → usecases/create_code.py, etc.
├── ProjectsCoordinator   → usecases/open_project.py, etc.
├── NavigationCoordinator → usecases/navigate.py, etc.
├── SettingsCoordinator   → settings repo calls
└── Dialog methods        → show_*_dialog()
```

**Problems:**
- 3 layers of indirection
- Sub-coordinators are just pass-through wrappers
- Doesn't match ddd-workshop command handler pattern

## Target State

```
AppContext (dependency container only)
├── event_bus: EventBus
├── state: ProjectState
├── lifecycle: ProjectLifecycle
├── settings_repo: UserSettingsRepository
├── sources_context: SourcesContext | None
├── cases_context: CasesContext | None
├── coding_context: CodingContext | None
├── projects_context: ProjectsContext | None
└── start() / stop()

DialogService (separate)
├── show_open_project_dialog()
├── show_create_project_dialog()
└── show_settings_dialog()

Consumers call use cases directly:
    from src.application.cases.usecases import create_case
    result = create_case(cmd, ctx.state, ctx.cases_context, ctx.event_bus)
```

---

## Phase 1: Create AppContext

**Files to create:**
- `src/application/app_context.py`

**AppContext responsibilities:**
1. Hold infrastructure (event_bus, state, lifecycle, settings_repo)
2. Hold bounded contexts (sources_context, cases_context, etc.)
3. Lifecycle methods: `start()`, `stop()`
4. Project open/close wiring

**NOT in AppContext:**
- No use case methods
- No dialog methods
- No query methods

```python
# src/application/app_context.py
@dataclass
class AppContext:
    event_bus: EventBus
    state: ProjectState
    lifecycle: ProjectLifecycle
    settings_repo: UserSettingsRepository
    signal_bridge: ProjectSignalBridge | None = None

    # Contexts (populated when project opens)
    sources_context: SourcesContext | None = None
    cases_context: CasesContext | None = None
    coding_context: CodingContext | None = None
    projects_context: ProjectsContext | None = None

    def start(self) -> None: ...
    def stop(self) -> None: ...
    def open_project(self, path: str) -> Result: ...
    def close_project(self) -> None: ...
```

---

## Phase 2: Create DialogService

**Files to create:**
- `src/presentation/services/dialog_service.py`

**Move from Coordinator:**
- `show_open_project_dialog()`
- `show_create_project_dialog()`
- `show_settings_dialog()`

```python
# src/presentation/services/dialog_service.py
class DialogService:
    def __init__(self, ctx: AppContext):
        self._ctx = ctx

    def show_open_project_dialog(self, parent=None) -> Result: ...
    def show_create_project_dialog(self, parent=None) -> Result: ...
    def show_settings_dialog(self, parent=None) -> Any: ...
```

---

## Phase 3: Update Consumers

### 3.1 FileManagerViewModel

**Current:**
```python
self._coordinator.sources.add_source(command)
self._coordinator.cases.get_cases()
```

**After:**
```python
from src.application.sources.usecases import add_source
from src.application.cases.usecases import get_cases

add_source(command, self._ctx.state, self._ctx.sources_context, self._ctx.event_bus)
get_cases(self._ctx.state)
```

### 3.2 ProjectTools (MCP)

**Current:**
```python
self._coordinator.sources.get_sources()
self._coordinator.navigation.navigate_to_segment(command)
```

**After:**
```python
from src.application.sources.usecases import get_sources
from src.application.navigation.usecases import navigate_to_segment

get_sources(self._ctx.state)
navigate_to_segment(command, self._ctx.state, self._ctx.event_bus)
```

### 3.3 main.py

**Current:**
```python
self._coordinator.show_settings_dialog(...)
self._coordinator.navigation.connect_text_coding_screen(...)
```

**After:**
```python
self._dialog_service.show_settings_dialog(...)
# Navigation connection moves to signal_bridge or AppContext
```

---

## Phase 4: Handle Navigation

Navigation is special - it has state (current_screen) and connects to UI.

**Options:**
1. Keep NavigationCoordinator as NavigationService
2. Move navigation state to AppContext
3. Make navigation a use case pattern

**Recommendation:** Keep as `NavigationService` - it's stateful and UI-connected.

```python
# src/application/navigation/service.py
class NavigationService:
    def __init__(self, ctx: AppContext):
        self._ctx = ctx
        self._current_screen: str | None = None

    def navigate_to_screen(self, command) -> Result: ...
    def navigate_to_segment(self, command) -> Result: ...
    def get_current_screen(self) -> str | None: ...
```

---

## Phase 5: Remove Sub-Coordinators

**Files to delete:**
- `src/application/coordinators/cases_coordinator.py`
- `src/application/coordinators/sources_coordinator.py`
- `src/application/coordinators/folders_coordinator.py`
- `src/application/coordinators/coding_coordinator.py`
- `src/application/coordinators/projects_coordinator.py`
- `src/application/coordinators/settings_coordinator.py`
- `src/application/coordinators/base.py`
- `src/application/coordinators/__init__.py`

**Keep but refactor:**
- `src/application/coordinators/navigation_coordinator.py` → `navigation/service.py`

**Delete after migration:**
- `src/application/coordinator.py`

---

## Phase 6: Update Tests

1. Replace `ApplicationCoordinator` fixtures with `AppContext`
2. Update test imports to use direct use case calls
3. Add DialogService to test fixtures where needed

---

## Migration Order

1. **Create AppContext** (new file, no breaking changes)
2. **Create DialogService** (new file, no breaking changes)
3. **Create NavigationService** (new file, no breaking changes)
4. **Migrate FileManagerViewModel** (update imports)
5. **Migrate ProjectTools** (update imports)
6. **Migrate main.py** (update wiring)
7. **Update test fixtures** (AppContext replaces Coordinator)
8. **Delete sub-coordinators** (cleanup)
9. **Delete ApplicationCoordinator** (final cleanup)

---

## Estimated Impact

| Category | Count |
|----------|-------|
| Files to create | 3 |
| Files to modify | ~15 |
| Files to delete | 9 |
| Sub-coordinators removed | 7 |
| Use cases (unchanged) | 47 |

---

## Benefits

1. **Matches ddd-workshop** - Direct command handler calls
2. **Less indirection** - 1 layer instead of 3
3. **Clearer dependencies** - Use cases declare what they need
4. **Easier testing** - Test use cases directly, mock only dependencies
5. **No god object** - AppContext is just a container

## Risks

1. **Breaking changes** - All consumers need updating
2. **Verbose calls** - Must pass 4 args instead of `coordinator.sources.add_source(cmd)`
3. **Import sprawl** - Many use case imports in ViewModels

---

## Mitigation for Verbosity

Create helper functions if needed:

```python
# src/application/cases/__init__.py
def create_case(ctx: AppContext, command: CreateCaseCommand) -> Result:
    """Convenience wrapper for create_case use case."""
    from src.application.cases.usecases.create_case import create_case as _create
    return _create(command, ctx.state, ctx.cases_context, ctx.event_bus)
```

This keeps the simple API while maintaining direct use case pattern.
