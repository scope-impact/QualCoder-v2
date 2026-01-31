---
id: QC-016
title: Analysis Domain
status: To Do
milestone: M-005
layer: Domain
created_date: '2026-01-29'
labels: [domain, analysis, agent, P2]
dependencies: [QC-004, QC-008, QC-012]
---

## Description

Define the domain layer for Analysis: query specifications, report definitions, graph structures, and agent tool schemas.

**Agent-First:** Agent tools so AI can query patterns and answer analytical questions.

## Acceptance Criteria

- [ ] Query specifications (filters, groupings)
- [ ] Report definitions (frequency, co-occurrence)
- [ ] Graph structures (nodes, edges)
- [ ] Export format specifications
- [ ] Agent tool schemas (query_codes, get_frequency, find_patterns)

## Implementation

- `src/domain/analysis/entities.py`
- `src/domain/analysis/queries.py`
- `src/agent_context/schemas/analysis_tools.py`
