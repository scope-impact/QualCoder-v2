---
id: QC-014
title: Case Application
status: To Do
milestone: M-004
layer: Application
created_date: '2026-01-29'
labels: [application, cases, agent, P2]
dependencies: [QC-003.02, QC-012, QC-013]
---

## Description

Implement the application layer for Case Management with Agent tool registration.

**Agent-First:** Controller serves both UI and agent. Agent tools registered.

## Acceptance Criteria

- [ ] CaseController implementation
- [ ] CRUD commands for cases
- [ ] Membership commands (AddMember, RemoveMember)
- [ ] Attribute commands
- [ ] Events published for state changes
- [ ] SignalBridge wiring complete (domain events → Qt signals)
- [ ] Agent tools registered
- [ ] Trust level enforcement

## Subtasks

Ordered by dependency flow: Controller → Commands → Wiring → Agent

| ID | Subtask | Status | Wires |
|----|---------|--------|-------|
| **Controller & Commands** ||||
| QC-014.01 | Case CRUD Commands | To Do | Controller → Deriver → Repo |
| QC-014.02 | Attribute Commands | To Do | Controller → Deriver → Repo |
| QC-014.03 | Case Membership Commands | To Do | Controller → Deriver → Repo |
| QC-014.04 | Case Import/Export Commands | To Do | Controller → Batch Operations |
| **Signal Bridge Wiring** ||||
| QC-014.05 | Case Signal Bridge | To Do | EventBus → Bridge → Qt Signals |
| QC-014.07 | Signal Payloads | To Do | Event → Payload DTOs |
| QC-014.08 | Event Converters | To Do | Converter per event type |
| **Agent Integration** ||||
| QC-014.06 | Case Agent Tools | To Do | MCP schemas + registration |
| QC-014.09 | Integration Tests | To Do | End-to-end flow tests |

## Event Flow Map

| Domain Event | Signal Bridge Signal | UI Subscribers |
|--------------|---------------------|----------------|
| CaseCreated | `case_created` | CaseTable, ActivityPanel |
| CaseRenamed | `case_renamed` | CaseTable |
| CaseDeleted | `case_deleted` | CaseTable |
| CaseMemoUpdated | `case_memo_updated` | CaseDetailView |
| MemberAdded | `member_added` | CaseFileManager |
| MemberRemoved | `member_removed` | CaseFileManager |
| AttributeTypeCreated | `attribute_type_created` | AttributeManager |
| AttributeTypeDeleted | `attribute_type_deleted` | AttributeManager |
| AttributeValueSet | `attribute_value_set` | CaseTable, CaseDetailView |

## Implementation

- `src/application/controllers/case_controller.py`
- `src/application/signal_bridge/case_bridge.py`
- `src/application/signal_bridge/case_payloads.py`
- `src/application/signal_bridge/case_converters.py`
- `src/agent_context/tools/case.py`
- `src/agent_context/schemas/case_tools.py`
