---
id: QC-018
title: Analysis Application
status: To Do
milestone: M-005
layer: Application
created_date: '2026-01-29'
labels: [application, analysis, agent, P2]
dependencies: [QC-016, QC-017]
---

## Description

Implement the application layer for Analysis with Agent tool registration.

**Agent-First:** Controller serves both UI and agent. AI can answer analytical questions.

## Acceptance Criteria

- [ ] AnalysisController implementation
- [ ] Report generation commands
- [ ] Export commands
- [ ] Query execution
- [ ] Agent tools registered (query_codes, get_frequency)
- [ ] AI can answer "How many segments coded with X?"

## Implementation

- `src/application/controllers/analysis_controller.py`
- `src/agent_context/tools/analysis.py`
