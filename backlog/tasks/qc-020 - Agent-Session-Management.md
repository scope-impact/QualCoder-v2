---
id: QC-020
title: Agent Session Management
status: To Do
milestone: M-006
layer: Application
created_date: '2026-01-29'
labels: [application, agent, P1]
dependencies: [QC-001, QC-006]
---

## Description

Implement session management and statistics tracking for AI agent interactions.

**Note:** Trust levels and MCP infrastructure are in M-001. This task adds session lifecycle, statistics, and suggestion queue management.

## Acceptance Criteria

- [ ] Session lifecycle (create, active, end)
- [ ] Statistics tracking (actions, approvals, rejections)
- [ ] Suggestion queue management
- [ ] Batch operations (approve all, reject all)
- [ ] Session history persistence

## Implementation

- `src/application/services/agent_session_service.py`
- `src/infrastructure/repositories/agent/`
