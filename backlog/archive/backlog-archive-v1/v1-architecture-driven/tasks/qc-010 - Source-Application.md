---
id: QC-010
title: Source Application
status: To Do
milestone: M-003
layer: Application
created_date: '2026-01-29'
labels: [application, sources, agent, P2]
dependencies: [QC-003.02, QC-008, QC-009]
---

## Description

Implement the application layer for Source Management with Agent tool registration.

**Agent-First:** Controller serves both UI and agent. Agent tools registered.

## Acceptance Criteria

- [ ] SourceController implementation
- [ ] Import commands (ImportFile, ImportFolder)
- [ ] Delete and organize commands
- [ ] Events published for state changes
- [ ] SignalBridge wiring complete (domain events → Qt signals)
- [ ] Agent tools registered (list_sources, read_source)
- [ ] Trust level enforcement

## Subtasks

Ordered by dependency flow: Controller → Commands → Wiring → Agent

| ID | Subtask | Status | Wires |
|----|---------|--------|-------|
| **Controller & Commands** ||||
| QC-010.01 | File Import Commands | To Do | Controller → Deriver → Repo |
| QC-010.02 | File Management Commands | To Do | Controller → Deriver → Repo |
| QC-010.03 | Speaker Detection Commands | To Do | Controller → Deriver → Repo |
| QC-010.04 | Case Linking Commands | To Do | Controller → Deriver → Repo |
| QC-010.05 | Survey Import Command | To Do | Controller → Batch Import |
| QC-010.08 | Pseudonym Commands | To Do | Controller → Deriver → Repo |
| QC-010.09 | Reference Commands | To Do | Controller → Deriver → Repo |
| **Signal Bridge Wiring** ||||
| QC-010.06 | Source Signal Bridge | To Do | EventBus → Bridge → Qt Signals |
| QC-010.10 | Signal Payloads | To Do | Event → Payload DTOs |
| QC-010.11 | Event Converters | To Do | Converter per event type |
| **Agent Integration** ||||
| QC-010.07 | Source Agent Tools | To Do | MCP schemas + registration |
| QC-010.12 | Integration Tests | To Do | End-to-end flow tests |

## Event Flow Map

| Domain Event | Signal Bridge Signal | UI Subscribers |
|--------------|---------------------|----------------|
| SourceImported | `source_imported` | SourceTable, ActivityPanel |
| SourceRenamed | `source_renamed` | SourceTable |
| SourceDeleted | `source_deleted` | SourceTable, CodingScreens |
| SourceMemoUpdated | `source_memo_updated` | SourcePreview |
| SpeakerDetected | `speaker_detected` | SpeakerDialog |
| TranscriptUpdated | `transcript_updated` | AVCodingScreen |
| TextExtracted | `text_extracted` | PDFCodingScreen |
| CaseLinked | `case_linked` | CaseLinkingPanel |
| CaseUnlinked | `case_unlinked` | CaseLinkingPanel |

## Implementation

- `src/application/controllers/source_controller.py`
- `src/application/signal_bridge/source_bridge.py`
- `src/application/signal_bridge/source_payloads.py`
- `src/application/signal_bridge/source_converters.py`
- `src/agent_context/tools/source.py`
- `src/agent_context/schemas/source_tools.py`
