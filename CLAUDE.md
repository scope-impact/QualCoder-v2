# QualCoder v2 - Claude Code Instructions

## Skills Reference

Detailed conventions are in `.claude/skills/`:

| Skill | Purpose | Use When |
|-------|---------|----------|
| `developer` | Code style, patterns, testing, E2E | Writing Python code, tests |
| `backlog` | Task management with DDD structure | Creating/editing tasks |
| `c4-architecture` | System architecture diagrams | Understanding codebase structure |
| `sub-agents` | Layer-specific Claude sub-agents | Complex multi-layer features, parallel development |

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

### Architecture (DDD Layers)

```
src/
├── domain/           # Pure functions, entities, events (NO I/O)
├── infrastructure/   # Repositories, database, external services
├── application/      # Controllers, Signal Bridges, orchestration
├── presentation/     # PySide6 widgets, screens, dialogs
design_system/        # Reusable UI components, tokens
```

### Testing

```bash
# Run all tests
QT_QPA_PLATFORM=offscreen make test-all

# Run specific e2e tests
QT_QPA_PLATFORM=offscreen uv run pytest src/presentation/tests/test_case_manager_e2e.py -v
```

See `.claude/skills/developer/SKILL.md` for:
- Code style and naming conventions
- Result type patterns (`returns` library)
- Controller 5-step pattern
- Signal Bridge implementation
- E2E testing with real database fixtures

---

## Quick Reference

### Bounded Contexts

`coding`, `sources`, `cases`, `journals`, `analysis`, `ai-assistant`, `projects`

### Task Labels

- Layers: `domain`, `infrastructure`, `application`, `presentation`
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

## Sub-Agents Architecture

For complex multi-layer features, use specialized sub-agents from `.claude/agents/`:

| Agent | Layer | Scope |
|-------|-------|-------|
| `domain-agent` | Domain | Pure functions, entities, events, derivers |
| `infrastructure-agent` | Infrastructure | Repositories, schemas, external services |
| `repository-agent` | Infrastructure | Repository implementations specifically |
| `controller-agent` | Application | 5-step pattern controllers |
| `signal-bridge-agent` | Application | Event → Qt signal translation |
| `design-system-agent` | Presentation | Design tokens, atoms |
| `molecule-agent` | Presentation | Small composite widgets (2-5 atoms) |
| `organism-agent` | Presentation | Business-logic UI components |
| `page-agent` | Presentation | Organism compositions with layouts |
| `screen-agent` | Presentation | Page + ViewModel integration |
| `viewmodel-agent` | Presentation | UI ↔ Application binding |

See `.claude/skills/sub-agents/SKILL.md` for full orchestration patterns.
