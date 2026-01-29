---
id: QC-014
title: Case Application
status: To Do
milestone: M-004
layer: Application
created_date: '2026-01-29'
labels: [application, cases, agent, P2]
dependencies: [QC-012, QC-013]
---

## Description

Implement the application layer for Case Management with Agent tool registration.

**Agent-First:** Controller serves both UI and agent. Agent tools registered.

## Acceptance Criteria

- [ ] CaseController implementation
- [ ] CRUD commands for cases
- [ ] Membership commands (AddMember, RemoveMember)
- [ ] Attribute commands
- [ ] Agent tools registered
- [ ] Trust level enforcement

## Implementation

- `src/application/controllers/case_controller.py`
- `src/agent_context/tools/case.py`
