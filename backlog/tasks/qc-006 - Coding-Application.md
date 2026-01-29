---
id: QC-006
title: Coding Application
status: To Do
milestone: M-002
layer: Application
created_date: '2026-01-29'
labels: [application, coding, agent, P1]
dependencies: [QC-004, QC-005]
---

## Description

Implement the application layer for Coding: controller, event bus, command handling, and agent tool registration.

**Agent-First:** The controller serves both UI and agent. Agent tools are registered here.

## Acceptance Criteria

- [ ] Event bus (publish/subscribe)
- [ ] CodingController implementation
- [ ] All commands working (create, rename, delete, apply code, etc.)
- [ ] Events published for state changes
- [ ] Agent tools registered and functional
- [ ] Trust level enforcement on agent operations

## Subtasks

| ID | Subtask | Status |
|----|---------|--------|
| QC-006.1 | Event Bus | To Do |
| QC-006.2 | Controller Protocol | To Do |
| QC-006.3 | CodingController | To Do |
| QC-006.4 | Agent Tool Registration | To Do |
| QC-006.5 | Trust Enforcement | To Do |
| QC-006.6 | Integration Tests | To Do |

## Implementation

- `src/application/event_bus.py`
- `src/application/controllers/coding_controller.py`
- `src/agent_context/tools/coding.py`
