---
id: QC-024
title: Collaboration Application
status: To Do
milestone: M-007
layer: Application
created_date: '2026-01-29'
labels: [application, collaboration, agent, P3]
dependencies: [QC-003.02, QC-022, QC-023]
---

## Description

Implement the application layer for Collaboration with Agent tool registration.

**Agent-First:** Agent can identify itself, compare its codings with human coders.

## Acceptance Criteria

- [ ] CollaborationController implementation
- [ ] Coder management commands
- [ ] Merge commands with conflict handling
- [ ] Comparison commands
- [ ] Events published for state changes
- [ ] SignalBridge wiring complete (domain events → Qt signals)
- [ ] Agent tools registered (set_coder, compare_codings)
- [ ] Promote AI coding to human coding

## Subtasks

Ordered by dependency flow: Controller → Commands → Wiring → Agent

| ID | Subtask | Status | Wires |
|----|---------|--------|-------|
| **Controller & Commands** ||||
| QC-024.01 | Coder Management Commands | To Do | Controller → Deriver → Repo |
| QC-024.02 | Merge Commands | To Do | Controller → Merge Deriver → Repo |
| QC-024.03 | Comparison Commands | To Do | Controller → Comparison Service |
| QC-024.04 | AI Promotion Commands | To Do | Controller → Deriver → Repo |
| **Signal Bridge Wiring** ||||
| QC-024.05 | Collaboration Signal Bridge | To Do | EventBus → Bridge → Qt Signals |
| QC-024.07 | Signal Payloads | To Do | Event → Payload DTOs |
| QC-024.08 | Event Converters | To Do | Converter per event type |
| **Agent Integration** ||||
| QC-024.06 | Collaboration Agent Tools | To Do | MCP schemas + registration |
| QC-024.09 | Integration Tests | To Do | End-to-end flow tests |

## Event Flow Map

| Domain Event | Signal Bridge Signal | UI Subscribers |
|--------------|---------------------|----------------|
| CoderCreated | `coder_created` | CoderSelector, CoderManager |
| CoderSwitched | `coder_switched` | CoderSelector, StatusBar |
| CoderVisibilityChanged | `coder_visibility_changed` | CoderSelector, CodingScreens |
| MergeStarted | `merge_started` | MergeDialog |
| ConflictDetected | `conflict_detected` | MergeDialog |
| ConflictResolved | `conflict_resolved` | MergeDialog |
| MergeCompleted | `merge_completed` | MergeDialog, ActivityPanel |
| ComparisonGenerated | `comparison_generated` | ComparisonScreen |
| CodingPromoted | `coding_promoted` | CoderManager, ActivityPanel |

## Implementation

- `src/application/controllers/collaboration_controller.py`
- `src/application/signal_bridge/collaboration_bridge.py`
- `src/application/signal_bridge/collaboration_payloads.py`
- `src/application/signal_bridge/collaboration_converters.py`
- `src/agent_context/tools/collaboration.py`
- `src/agent_context/schemas/collaboration_tools.py`
