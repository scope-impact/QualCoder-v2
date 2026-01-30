---
id: QC-018
title: Analysis Application
status: To Do
milestone: M-005
layer: Application
created_date: '2026-01-29'
labels: [application, analysis, agent, P2]
dependencies: [QC-003.02, QC-016, QC-017]
---

## Description

Implement the application layer for Analysis with Agent tool registration.

**Agent-First:** Controller serves both UI and agent. AI can answer analytical questions.

## Acceptance Criteria

- [ ] AnalysisController implementation
- [ ] Report generation commands
- [ ] Export commands
- [ ] Query execution
- [ ] Events published for state changes
- [ ] SignalBridge wiring complete (domain events → Qt signals)
- [ ] Agent tools registered (query_codes, get_frequency)
- [ ] AI can answer "How many segments coded with X?"

## Subtasks

Ordered by dependency flow: Controller → Commands → Wiring → Agent

| ID | Subtask | Status | Wires |
|----|---------|--------|-------|
| **Controller & Commands** ||||
| QC-018.01 | Report Generation Commands | To Do | Controller → Query → Repo |
| QC-018.02 | Export Commands | To Do | Controller → Exporter |
| QC-018.03 | Text Mining Commands | To Do | Controller → NLP Service |
| QC-018.04 | Graph Commands | To Do | Controller → Graph Builder |
| QC-018.05 | SQL Query Commands | To Do | Controller → Query Executor |
| QC-018.07 | Journal Commands | To Do | Controller → Deriver → Repo |
| QC-018.08 | Codebook Export Command | To Do | Controller → Exporter |
| **Signal Bridge Wiring** ||||
| QC-018.09 | Analysis Signal Bridge | To Do | EventBus → Bridge → Qt Signals |
| QC-018.10 | Signal Payloads | To Do | Event → Payload DTOs |
| QC-018.11 | Event Converters | To Do | Converter per event type |
| **Agent Integration** ||||
| QC-018.06 | Analysis Agent Tools | To Do | MCP schemas + registration |
| QC-018.12 | Integration Tests | To Do | End-to-end flow tests |

## Event Flow Map

| Domain Event | Signal Bridge Signal | UI Subscribers |
|--------------|---------------------|----------------|
| ReportGenerated | `report_generated` | ReportViewer, ActivityPanel |
| ReportExported | `report_exported` | ExportDialog |
| QueryExecuted | `query_executed` | SQLQueryInterface |
| ChartGenerated | `chart_generated` | ChartsScreen |
| GraphGenerated | `graph_generated` | NetworkGraphView |
| WordCloudGenerated | `wordcloud_generated` | WordCloudGenerator |
| JournalEntryCreated | `journal_entry_created` | JournalPanel |
| JournalEntryUpdated | `journal_entry_updated` | JournalPanel |

## Implementation

- `src/application/controllers/analysis_controller.py`
- `src/application/signal_bridge/analysis_bridge.py`
- `src/application/signal_bridge/analysis_payloads.py`
- `src/application/signal_bridge/analysis_converters.py`
- `src/agent_context/tools/analysis.py`
- `src/agent_context/schemas/analysis_tools.py`
