---
id: QC-020
title: Agent Session Management
status: To Do
milestone: M-006
layer: Application
created_date: '2026-01-29'
labels: [application, agent, P1]
dependencies: [QC-001, QC-003.02, QC-006]
---

## Description

Implement session management and statistics tracking for AI agent interactions.

**Note:** Trust levels and agent infrastructure are in M-001. This task adds session lifecycle, statistics, and suggestion queue management.

## Acceptance Criteria

- [ ] Session lifecycle (create, active, end)
- [ ] Statistics tracking (actions, approvals, rejections)
- [ ] Suggestion queue management
- [ ] Batch operations (approve all, reject all)
- [ ] Session history persistence
- [ ] SignalBridge wiring complete (agent events → Qt signals)

## Subtasks

Ordered by dependency flow: Services → Wiring → Testing

| ID | Subtask | Status | Wires |
|----|---------|--------|-------|
| **Services** ||||
| QC-020.01 | Suggestion Queue Service | To Do | Service → Suggestion Store |
| QC-020.02 | Agent Statistics Service | To Do | Service → Stats Store |
| QC-020.03 | Chat Session Service | To Do | Service → LLM Client |
| QC-020.04 | Trust Level Controller | To Do | Controller → Trust Policies |
| QC-020.05 | Agent Activity Log | To Do | Service → Activity Store |
| **Signal Bridge Wiring** ||||
| QC-020.06 | Agent Signal Bridge | To Do | EventBus → Bridge → Qt Signals |
| QC-020.07 | Signal Payloads | To Do | Event → Payload DTOs |
| QC-020.08 | Event Converters | To Do | Converter per event type |
| **Testing** ||||
| QC-020.09 | Integration Tests | To Do | End-to-end flow tests |

## Event Flow Map

| Domain Event | Signal Bridge Signal | UI Subscribers |
|--------------|---------------------|----------------|
| SuggestionGenerated | `suggestion_generated` | SuggestionPanel, ReviewQueue |
| SuggestionApproved | `suggestion_approved` | SuggestionPanel, ActivityPanel |
| SuggestionRejected | `suggestion_rejected` | SuggestionPanel, ActivityPanel |
| SessionStarted | `session_started` | AgentControlPanel |
| SessionEnded | `session_ended` | AgentControlPanel |
| TrustLevelChanged | `trust_level_changed` | AgentControlPanel |
| AgentActionExecuted | `agent_action_executed` | ActivityPanel, Badges |
| AgentMessageReceived | `agent_message_received` | AIChatScreen |

## Implementation

- `src/application/services/agent_session_service.py`
- `src/application/services/suggestion_queue_service.py`
- `src/application/signal_bridge/agent_bridge.py`
- `src/application/signal_bridge/agent_payloads.py`
- `src/application/signal_bridge/agent_converters.py`
- `src/infrastructure/repositories/agent/`
