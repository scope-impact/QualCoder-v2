# QualCoder v2 - Claude Code Instructions

## Skills Reference

Detailed conventions are in `.claude/skills/`:

| Skill | Purpose | Use When |
|-------|---------|----------|
| `developer` | Code style, patterns, testing, E2E | Writing Python code, tests |
| `backlog` | Task management with DDD structure | Creating/editing tasks |
| `c4-architecture` | System architecture diagrams | Understanding codebase structure |
| `docs-updater` | Documentation & screenshots | After tests pass, updating docs |

---

## Task Management (Backlog.md CLI)

**Critical: Never edit task files directly. Always use CLI.**

```bash
# View task
backlog task <id> --plain

# Create task
backlog task create "Title" -d "Description" --ac "Criterion 1" --ac "Criterion 2"

# Start work
backlog task edit <id> -s "In Progress" -a @myself

# Check acceptance criteria
backlog task edit <id> --check-ac 1 --check-ac 2

# Add implementation notes
backlog task edit <id> --append-notes "Progress update"

# Complete task
backlog task edit <id> --final-summary "What was done" -s Done
```

See `.claude/skills/backlog/SKILL.md` for full CLI reference and QualCoder-specific conventions.

---

## Development Workflow

### Architecture (Bounded Context / Vertical Slice)

```
src/
├── contexts/                   # Bounded Contexts (vertical slices)
│   ├── coding/                 # Coding context
│   │   ├── core/               # Domain (entities, events, derivers, invariants)
│   │   │   └── commandHandlers/  # Use cases (command handlers)
│   │   ├── infra/              # Repositories, external services
│   │   ├── interface/          # Signal bridges, MCP tools
│   │   └── presentation/       # Screens, dialogs, viewmodels
│   ├── sources/
│   ├── cases/
│   ├── projects/
│   ├── settings/
│   └── folders/
│
├── shared/                     # Cross-cutting concerns
│   ├── common/                 # Types, OperationResult, failure events
│   ├── core/                   # Shared domain logic
│   ├── infra/                  # EventBus, SignalBridge, AppContext
│   └── presentation/           # Molecules, organisms, templates
│
├── tests/e2e/                  # End-to-end tests
└── main.py                     # Entry point

design_system/                  # Reusable UI components, tokens
```

### Testing

```bash
# Run all tests
QT_QPA_PLATFORM=offscreen make test-all

# Run specific e2e tests
QT_QPA_PLATFORM=offscreen uv run pytest src/tests/e2e/test_case_manager_e2e.py -v
```

### Definition of Done

**AC should only be marked `[x]` when all requirements are met:**

Requirements:
1. E2E test exists in `src/tests/e2e/`
2. Test has `@allure.story("QC-XXX.YY Description")` decorator
3. Test passes with `make test-all`
4. User documentation updated in `docs/user-manual/` (use `docs-updater` skill)
5. API documentation updated in `docs/api/` for MCP tools (use `developer` skill)
6. Coverage matrix updated in `docs/DOC_COVERAGE.md`

```python
# Allure tracing convention
@allure.story("QC-028.03 Rename and Recolor Codes")
class TestColorPickerDialog:
    @allure.title("AC #3.1: Dialog shows preset color grid")
    def test_dialog_shows_preset_colors(self):
        ...
```

```bash
# Check which tasks have test coverage
grep -rh "@allure.story.*QC-" src/tests/e2e/*.py | sort -u
```

See `.claude/skills/developer/SKILL.md` for:
- Code style and naming conventions
- OperationResult pattern for command handlers
- Signal Bridge implementation
- E2E testing with real database fixtures

---

## Quick Reference

### Bounded Contexts

`coding`, `sources`, `cases`, `projects`, `settings`, `folders`

### Context Layer Structure

Each bounded context follows this structure:
- **core/** — Domain (entities, events, derivers, invariants, commandHandlers/)
- **infra/** — Repositories, database schemas, external services
- **interface/** — Signal bridges, MCP tools (adapters)
- **presentation/** — Screens, pages, dialogs, viewmodels

### Task Labels

- Layers: `core`, `infra`, `interface`, `presentation`
- Priority: `P0` (critical), `P1`, `P2`, `P3` (low)

### Commit Convention

```
type(scope): description

feat(cases): add case attribute management
fix(coding): resolve segment overlap detection
test(cases): add e2e tests for case manager
docs: update CLAUDE.md
```

---

## MCP Tools

All 15 MCP tools live in `src/contexts/projects/interface/mcp_tools.py`.

### Tool Inventory

| Category | Tools |
|----------|-------|
| **Project** | `get_project_context`, `open_project`, `close_project` |
| **Sources** | `list_sources`, `read_source_content`, `add_text_source`, `import_file_source`, `remove_source`, `suggest_source_metadata`, `navigate_to_segment` |
| **Folders** | `list_folders`, `create_folder`, `rename_folder`, `delete_folder`, `move_source_to_folder` |
| **Coding** | `list_codes`, `get_code`, `batch_apply_codes`, `list_segments_for_source` |

### Architecture Patterns

- **Handlers dict** built once in `__init__`, not per-call in `execute()`
- **Repo access** via `_source_repo` / `_folder_repo` properties (null-safe)
- **Param checks** use `if x is None` (missing only) — command handlers own content validation
- **No `hasattr()` guards** — all context properties defined on `ProjectToolsContext` protocol
- **Tools return** `Result[dict, str]` (Success/Failure from `returns` library)
- **Command handlers return** `OperationResult` (`.is_success`, `.is_failure`, `.data`, `.error`)
- **Error codes**: `ENTITY_NOT_OP/REASON` (e.g., `SOURCE_NOT_ADDED/DUPLICATE_NAME`)

### ID Generation

All typed IDs use `uuid4().int % 1_000_000` via `.new()` classmethod in `shared/common/types.py`.
Types: `SourceId`, `CodeId`, `SegmentId`, `CaseId`, `FolderId`. Never use `hash()` for IDs.

### API Docs

- `docs/api/mcp-api.md` — compact table reference (agents get full schemas via `tools/list`)
- `docs/user-manual/sources.md` — includes AI Agent Source Management section
- `docs/DOC_COVERAGE.md` — tracks doc status per AC

---

## Common Issues / Wiring Checklist

### Screen ↔ ViewModel Wiring Pattern

Every Screen that needs domain operations must be wired to its ViewModel in `main.py`:

```python
# In _wire_viewmodels() - called when project opens
def _wire_viewmodels(self):
    # 1. Create ViewModel with repos from context
    viewmodel = SomeViewModel(
        some_repo=self._ctx.some_context.some_repo,
        event_bus=self._ctx.event_bus,
        signal_bridge=self._some_signal_bridge,
    )
    # 2. Wire to screen
    self._screens["screen_name"].set_viewmodel(viewmodel)
```

**Checklist when adding a new Screen:**
- [ ] Screen has `set_viewmodel()` method
- [ ] ViewModel created in `_wire_viewmodels()` with correct repos
- [ ] Screen wired after project opens (repos need DB connection)
- [ ] SignalBridge connected for reactive UI updates

**Current wiring status in main.py:**
| Screen | ViewModel | Wired | Status |
|--------|-----------|-------|--------|
| FileManagerScreen | FileManagerViewModel | ✅ | Working |
| TextCodingScreen | TextCodingViewModel | ✅ | Working |
| CaseManagerScreen | CaseManagerViewModel | ❌ | Needs check |
| ProjectScreen | — | N/A | Static UI |

### Why UI clicks do nothing

If clicking UI does nothing, check:
1. **No ViewModel** — Screen created without viewmodel
2. **ViewModel not wired** — `_wire_viewmodels()` missing the screen
3. **Signal not connected** — Screen emits signal but nothing listens
4. **Repos not available** — Project not opened yet (repos need DB)
