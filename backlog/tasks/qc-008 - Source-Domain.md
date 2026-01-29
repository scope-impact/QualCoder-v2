---
id: QC-008
title: Source Domain
status: To Do
milestone: M-003
layer: Domain
created_date: '2026-01-29'
labels: [domain, sources, agent, P2]
dependencies: [QC-001]
---

## Description

Define the domain layer for Source Management: entities, events, invariants, derivers, and agent tool schemas.

**Agent-First:** Agent tool schemas defined so AI can list and read sources.

## Acceptance Criteria

- [ ] Entities: Source, Folder, SourceMetadata
- [ ] Value objects: MediaType, FilePath
- [ ] Domain events (SourceImported, SourceDeleted, etc.)
- [ ] Invariants and derivers
- [ ] Agent tool schemas (list_sources, read_source, get_source_text)

## Implementation

- `src/domain/source/entities.py`
- `src/domain/source/events.py`
- `src/agent_context/schemas/source_tools.py`
