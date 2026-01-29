---
id: QC-024
title: Collaboration Application
status: To Do
milestone: M-007
layer: Application
created_date: '2026-01-29'
labels: [application, collaboration, agent, P3]
dependencies: [QC-022, QC-023]
---

## Description

Implement the application layer for Collaboration with Agent tool registration.

**Agent-First:** Agent can identify itself, compare its codings with human coders.

## Acceptance Criteria

- [ ] CollaborationController implementation
- [ ] Coder management commands
- [ ] Merge commands with conflict handling
- [ ] Comparison commands
- [ ] Agent tools registered (set_coder, compare_codings)
- [ ] Promote AI coding to human coding

## Implementation

- `src/application/controllers/collaboration_controller.py`
- `src/agent_context/tools/collaboration.py`
