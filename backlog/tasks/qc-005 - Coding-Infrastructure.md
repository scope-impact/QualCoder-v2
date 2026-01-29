---
id: QC-005
title: Coding Infrastructure
status: To Do
milestone: M-002
layer: Infrastructure
created_date: '2026-01-29'
labels: [infrastructure, coding, P1]
dependencies: [QC-004]
---

## Description

Implement repositories for the Coding bounded context with SQLite persistence.

## Acceptance Criteria

- [ ] Repository protocols (interfaces)
- [ ] In-memory repositories (for testing)
- [ ] SQLite repositories (for production)
- [ ] Data mapping (entity ↔ database)

## Subtasks

| ID | Subtask | Status |
|----|---------|--------|
| QC-005.1 | Repository Protocols | To Do |
| QC-005.2 | In-Memory Repositories | To Do |
| QC-005.3 | SQLite Code Repository | To Do |
| QC-005.4 | SQLite Category Repository | To Do |
| QC-005.5 | SQLite Segment Repository | To Do |
| QC-005.6 | Repository Tests | To Do |

## Implementation

- `src/infrastructure/protocols.py`
- `src/infrastructure/repositories/coding/`
