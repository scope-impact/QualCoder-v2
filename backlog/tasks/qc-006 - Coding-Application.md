---
id: QC-006
title: Coding Application
status: To Do
milestone: M-002
layer: Application
created_date: '2026-01-29'
labels: [application, coding, agent, P1]
dependencies: [QC-003.02, QC-004, QC-005]
---

## Description

Implement the application layer for Coding: controller, event bus, command handling, and agent tool registration.

**Agent-First:** The controller serves both UI and agent. Agent tools are registered here.

## Acceptance Criteria

- [ ] CodingController implementation
- [ ] All commands working (create, rename, delete, apply code, etc.)
- [ ] Events published for state changes
- [ ] SignalBridge wiring complete (domain events → Qt signals)
- [ ] Agent tools registered and functional
- [ ] Trust level enforcement on agent operations

## Subtasks

Ordered by dependency flow: Controller → Commands → Wiring → Services → Agent

| ID | Subtask | Status | Wires |
|----|---------|--------|-------|
| **Controller & Commands** ||||
| QC-006.01 | Coding Controller Core | To Do | Controller → Deriver → Repo |
| QC-006.02 | Image and AV Coding Commands | To Do | Controller → Deriver → Repo |
| QC-006.03 | Auto-Coding Commands | To Do | Controller → Batch Deriver → Repo |
| QC-006.04 | Navigation Queries | To Do | Controller → Query Repo (read-only) |
| **Signal Bridge Wiring** ||||
| QC-006.05 | Coding Signal Bridge | To Do | EventBus → Bridge → Qt Signals |
| QC-006.06 | Signal Payloads | To Do | Event → Payload DTOs |
| QC-006.07 | Event Converters | To Do | Converter per event type |
| **Services & Policies** ||||
| QC-006.08 | Recent Codes Service | To Do | Policy → on_segment_coded |
| **Agent Integration** ||||
| QC-006.09 | Agent Tool Schemas | To Do | MCP schemas for tools |
| QC-006.10 | Agent Tool Registration | To Do | Register tools with MCP server |
| QC-006.11 | Trust Enforcement | To Do | Permission checks per tool |
| **Testing** ||||
| QC-006.12 | Integration Tests | To Do | End-to-end flow tests |

## Event Flow Map

| Domain Event | Signal Bridge Signal | UI Subscribers |
|--------------|---------------------|----------------|
| CodeCreated | `code_created` | CodeTree, ActivityPanel |
| CodeRenamed | `code_renamed` | CodeTree |
| CodeDeleted | `code_deleted` | CodeTree, SegmentList |
| CodeColorChanged | `code_color_changed` | CodeTree, SegmentHighlights |
| SegmentCoded | `segment_coded` | TextCodingScreen, SegmentList |
| SegmentUncoded | `segment_uncoded` | TextCodingScreen, SegmentList |
| ImageSegmentCoded | `image_segment_coded` | ImageCodingScreen |
| AVSegmentCoded | `av_segment_coded` | AVCodingScreen |
| CategoryCreated | `category_created` | CodeTree |
| CategoryDeleted | `category_deleted` | CodeTree |

## Implementation

- `src/application/controllers/coding_controller.py`
- `src/application/signal_bridge/coding_bridge.py`
- `src/application/signal_bridge/coding_payloads.py`
- `src/application/signal_bridge/coding_converters.py`
- `src/application/services/recent_codes_service.py`
- `src/agent_context/tools/coding.py`
- `src/agent_context/schemas/coding_tools.py`
