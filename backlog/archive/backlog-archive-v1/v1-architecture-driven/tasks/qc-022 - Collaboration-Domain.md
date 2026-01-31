---
id: QC-022
title: Collaboration Domain
status: To Do
milestone: M-007
layer: Domain
created_date: '2026-01-29'
labels: [domain, collaboration, agent, P3]
dependencies: [QC-001]
---

## Description

Define the domain layer for Collaboration: coders, merging, and comparison.

**Agent-First:** AI is a first-class coder. Agent codings tracked separately for reliability comparison.

## Acceptance Criteria

- [ ] Entities: Coder (human and AI types), MergeConflict, ComparisonResult
- [ ] Value objects: CoderType (Human, AI), VisibilityScope
- [ ] Domain events (CoderCreated, ConflictDetected, MergeCompleted)
- [ ] Kappa score calculation (pure function)
- [ ] Agent tool schemas (set_coder, compare_codings)

## Implementation

- `src/domain/collaboration/entities.py`
- `src/domain/collaboration/events.py`
- `src/domain/collaboration/comparison.py`
- `src/agent_context/schemas/collaboration_tools.py`
