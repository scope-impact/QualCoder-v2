---
id: QC-023
title: Collaboration Infrastructure
status: To Do
milestone: M-007
layer: Infrastructure
created_date: '2026-01-29'
labels: [infrastructure, collaboration, P3]
dependencies: [QC-022]
---

## Description

Implement repositories and merge engine for Collaboration.

## Acceptance Criteria

- [ ] CoderRepository (SQLite)
- [ ] MergeEngine (conflict detection, resolution strategies)
- [ ] Ownership tracking in existing repositories
- [ ] AI coder auto-creation on first agent session

## Implementation

- `src/infrastructure/repositories/collaboration/`
- `src/infrastructure/merge_engine.py`
