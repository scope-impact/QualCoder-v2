---
id: QC-010
title: Source Application
status: To Do
milestone: M-003
layer: Application
created_date: '2026-01-29'
labels: [application, sources, agent, P2]
dependencies: [QC-008, QC-009]
---

## Description

Implement the application layer for Source Management with MCP tool registration.

**Agent-First:** Controller serves both UI and agent. MCP tools registered.

## Acceptance Criteria

- [ ] SourceController implementation
- [ ] Import commands (ImportFile, ImportFolder)
- [ ] Delete and organize commands
- [ ] Events published
- [ ] MCP tools registered (list_sources, read_source)
- [ ] Trust level enforcement

## Implementation

- `src/application/controllers/source_controller.py`
- `src/agent_context/tools/source.py`
