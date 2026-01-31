---
id: QC-004
title: Coding Domain
status: Done
milestone: M-002
layer: Domain
created_date: '2026-01-29'
labels: [domain, coding, agent, P0]
dependencies: [QC-001]
---

## Description

Define the domain layer for the Coding bounded context: entities, events, invariants, derivers, and agent tool schemas.

**Agent-First:** Agent tool schemas are defined alongside domain entities.

## Acceptance Criteria

- [x] Entities: Code, Category, TextSegment, ImageSegment, AVSegment
- [x] Value objects: Color, TextPosition, ImageRegion, TimeRange
- [x] Domain events (13 events)
- [x] Invariants (business rule predicates)
- [x] Derivers (pure functions → Result[Event, Failure])
- [x] Agent tool schemas (create_code, apply_code, list_codes, etc.)

## Subtasks

| ID | Subtask | Status |
|----|---------|--------|
| QC-004.1 | Entities & Value Objects | Done |
| QC-004.2 | Domain Events | Done |
| QC-004.3 | Invariants | Done |
| QC-004.4 | Derivers | Done |
| QC-004.5 | Agent Tool Schemas | Done |
| QC-004.6 | Unit Tests | Done |

## Implementation

- `src/domain/coding/entities.py`
- `src/domain/coding/events.py`
- `src/domain/coding/invariants.py`
- `src/domain/coding/derivers.py`
- `src/agent_context/schemas/coding_tools.py`
