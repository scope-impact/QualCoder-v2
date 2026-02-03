# QualCoder v2 - Claude Code Instructions

## Skills Reference

Detailed conventions are in `.claude/skills/`:

| Skill | Purpose | Use When |
|-------|---------|----------|
| `developer` | Code style, patterns, testing, E2E | Writing Python code, tests |
| `backlog` | Task management with DDD structure | Creating/editing tasks |
| `c4-architecture` | System architecture diagrams | Understanding codebase structure |

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
