---
name: backlog
description: |
  Manage QualCoder v2 tasks using the backlog.md CLI tool. Create, edit, and refine
  tasks following DDD architecture and agent-first conventions.

  **Invoke when:**
  - Creating new tasks or features for QualCoder v2
  - Breaking down features by DDD layer (Domain → Infrastructure → Application → Presentation)
  - Editing or refining existing tasks
  - Managing task status and priorities

  **Provides:**
  - CLI commands for task management
  - DDD-aware task structure (by bounded context and layer)
  - Agent-first task conventions (MCP tool schemas alongside domain)
  - QualCoder-specific labels and bounded contexts
---

# QualCoder v2 Backlog Management

Manage QualCoder v2 tasks using the `backlog` CLI tool. Tasks follow DDD architecture with agent-first design.

## Project Configuration

```yaml
task_prefix: qc              # Tasks are qc-001, qc-002, etc.
zero_padded_ids: 3           # qc-001, not qc-1
```

## Quick Start

```bash
# List all tasks
backlog task list --plain

# Create a task (always include layer and bounded context)
backlog task create "Coding Domain" -d "Define domain entities" -l domain,coding,P0

# View task details
backlog task qc-004 --plain

# Edit task status
backlog task edit qc-004 -s "In Progress"

# Create subtask
backlog task create -p qc-004 "Unit Tests"
```

---

## Directory Structure

```
backlog/
├── config.yml                # Project config (labels, bounded contexts)
├── milestones/               # Epics by bounded context (m-001, m-002...)
│   ├── m-001 - Foundation.md
│   ├── m-002 - Coding-Context.md
│   ├── m-003 - Source-Management.md
│   └── ...
├── tasks/                    # Tasks (qc-NNN - Title.md)
├── completed/                # Archived completed tasks
└── decisions/                # Architecture Decision Records
```

---

## Bounded Contexts

QualCoder v2 is organized into bounded contexts. Always tag tasks with the appropriate context:

| Context | Label | Description |
|---------|-------|-------------|
| Coding | `coding` | Core: applying codes to text/image/AV/PDF segments |
| Sources | `sources` | File import and media management |
| Cases | `cases` | Participant/case groupings and attributes |
| Journals | `journals` | Research memos, field notes, reflections |
| Analysis | `analysis` | Reports, visualizations, exports |
| AI Assistant | `ai-assistant` | AI chat, semantic search, code suggestions |
| Collaboration | `collaboration` | Multi-coder workflows, inter-rater reliability |
| Projects | `projects` | Project-level operations |

---

## Architecture Layers

Tasks are organized by DDD layer. Create tasks in dependency order:

| Layer | Label | Depends On | Contains |
|-------|-------|------------|----------|
| **Domain** | `domain` | Shared types | Entities, events, invariants, derivers, agent schemas |
| **Infrastructure** | `infrastructure` | Domain | Repositories, persistence, external services |
| **Application** | `application` | Infrastructure | Use cases, command handlers |
| **Presentation** | `presentation` | Application | PyQt6 widgets, screens |
| **Design System** | `design-system` | — | Tokens, components, patterns |

**Task creation order per bounded context:**
1. `qc-XXX` Domain (entities, events, derivers, **agent tool schemas**)
2. `qc-XXX` Infrastructure (repositories, persistence)
3. `qc-XXX` Application (use cases)
4. `qc-XXX` Presentation (UI widgets)

---

## Agent-First Design

**IMPORTANT:** MCP tool schemas are defined alongside domain entities, not as an afterthought.

Every domain task should include:
- [ ] Agent tool schemas (create_X, get_X, list_X, update_X, delete_X)
- [ ] Tool input/output types
- [ ] Permission requirements (trust levels)

```python
# Domain task includes agent schemas
src/domain/coding/entities.py      # Entities
src/agent_context/schemas/coding_tools.py  # Agent tools for this context
```

---

## CLI Commands

| Action | Command |
|--------|---------|
| Create task | `backlog task create "Title" -d "Desc" -l domain,coding,P0` |
| Create subtask | `backlog task create -p qc-004 "Subtask title"` |
| List tasks | `backlog task list --plain` |
| List by status | `backlog task list -s "In Progress" --plain` |
| List by label | `backlog task list -l coding --plain` |
| View task | `backlog task qc-004 --plain` |
| Edit status | `backlog task edit qc-004 -s "Done"` |
| Add label | `backlog task edit qc-004 -l agent-tools` |
| Archive | `backlog task archive qc-004` |

**Always use `--plain` flag** for AI-friendly output.

---

## Labels Reference

### Architecture Layers
`domain`, `application`, `infrastructure`, `presentation`, `design-system`

### Bounded Contexts
`coding`, `sources`, `cases`, `journals`, `analysis`, `ai-assistant`, `collaboration`, `projects`

### Media Types
`text-coding`, `image-coding`, `av-coding`, `pdf-coding`

### Feature Types
`feature`, `enhancement`, `bug`, `refactor`, `documentation`, `testing`, `security`

### AI/Agent
`agent-tools`, `agent-ui`, `trust-level`

### Priority
`P0` (critical), `P1` (high), `P2` (medium), `P3` (low)

---

## Task Format

```markdown
---
id: QC-004
title: Coding Domain
status: To Do
milestone: M-002
layer: Domain
created_date: '2026-01-29'
labels: [domain, coding, agent-tools, P0]
dependencies: [QC-001]
---

## Description

Define the domain layer for the Coding bounded context: entities, events, invariants, derivers, and agent tool schemas.

**Agent-First:** MCP tool schemas are defined alongside domain entities.

## Acceptance Criteria

- [ ] Entities: Code, Category, TextSegment, ImageSegment, AVSegment
- [ ] Value objects: Color, TextPosition, ImageRegion, TimeRange
- [ ] Domain events (CodeCreated, CodeApplied, etc.)
- [ ] Invariants (business rule predicates)
- [ ] Derivers (pure functions → Result[Event, Failure])
- [ ] Agent tool schemas (create_code, apply_code, list_codes, etc.)

## Subtasks

| ID | Subtask | Status |
|----|---------|--------|
| QC-004.1 | Entities & Value Objects | To Do |
| QC-004.2 | Domain Events | To Do |
| QC-004.3 | Agent Tool Schemas | To Do |
| QC-004.4 | Unit Tests | To Do |

## Implementation

- `src/domain/coding/entities.py`
- `src/domain/coding/events.py`
- `src/domain/coding/derivers.py`
- `src/agent_context/schemas/coding_tools.py`
```

---

## Task Breakdown Strategy

### Per Bounded Context Pattern

For each bounded context (coding, sources, cases, etc.), create tasks in this order:

1. **Domain Task** - Entities, events, derivers, agent schemas
2. **Infrastructure Task** - Repositories, persistence adapters
3. **Application Task** - Use cases, command handlers
4. **Presentation Task** - PyQt6 widgets and screens

### Example: Coding Context (M-002)

```
QC-004 Coding Domain        → entities, events, agent schemas
QC-005 Coding Infrastructure → repositories, SQLite adapters
QC-006 Coding Application   → use cases (apply_code, remove_code)
QC-007 Coding Presentation  → CodeTreeWidget, CodingPanel
```

### Dependencies

- Domain depends on Shared Types (QC-001)
- Infrastructure depends on Domain
- Application depends on Infrastructure
- Presentation depends on Application

---

## Quality Checks

Before finalizing task creation:
- [ ] Layer label is set (domain/infrastructure/application/presentation)
- [ ] Bounded context label is set (coding/sources/cases/etc.)
- [ ] Priority is set (P0/P1/P2/P3)
- [ ] Dependencies reference only existing tasks
- [ ] Agent tool schemas included for domain tasks
- [ ] Implementation paths follow `src/{layer}/{context}/` structure

---

## Milestones Reference

| ID | Name | Description |
|----|------|-------------|
| M-001 | Foundation | Shared types, design system, app shell |
| M-002 | Coding Context | Code tree, text/image/AV/PDF coding |
| M-003 | Source Management | File import, media handling |
| M-004 | Case Management | Cases, attributes, linking |
| M-005 | Analysis | Reports, visualizations, exports |
| M-006 | Agent Context | AI chat, semantic search, suggestions |
| M-007 | Collaboration | Multi-coder, inter-rater reliability |

---

## File Structure Convention

```
src/
├── domain/
│   ├── shared/              # QC-001: Shared types
│   ├── coding/              # QC-004: Coding domain
│   ├── sources/             # QC-008: Source domain
│   └── ...
├── infrastructure/
│   ├── coding/              # QC-005: Coding infra
│   └── ...
├── application/
│   ├── coding/              # QC-006: Coding use cases
│   └── ...
├── presentation/
│   ├── coding/              # QC-007: Coding UI
│   └── ...
└── agent_context/
    └── schemas/             # Agent tool schemas (all contexts)
```

---

## Tips for AI Agents

- Always use `--plain` flag for list/view commands
- Include both layer AND bounded context labels
- For domain tasks, always include agent tool schemas
- Follow the layer dependency order: Domain → Infra → App → UI
- Use subtask tables for complex tasks
- Reference implementation paths in the Implementation section
