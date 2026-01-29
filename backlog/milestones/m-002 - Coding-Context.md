---
id: M-002
title: Coding Context
status: In Progress
created_date: '2026-01-29'
---

## Description

Implement the Coding bounded context end-to-end - the **Core Domain** where researchers apply semantic codes to qualitative data.

**Agent-First:** Both human UI and agent tools are delivered together. An AI assistant can code data just like a human user.

## Goals

- Pure, testable domain logic (Functional Core)
- Persistent storage with SQLite
- Controller orchestration (serves both UI and agent)
- Full coding UI screens
- MCP tools for agent coding

## Tasks

| ID | Task | Layer | Status |
|----|------|-------|--------|
| QC-004 | Coding Domain | Domain | Done |
| QC-005 | Coding Infrastructure | Infrastructure | To Do |
| QC-006 | Coding Application | Application | To Do |
| QC-007 | Coding Presentation | Presentation | To Do |

## Success Criteria

- [ ] Entities: Code, Category, Segment (text, image, A/V)
- [ ] Events emitted for all state changes
- [ ] SQLite repositories working
- [ ] Controller coordinates operations
- [ ] All 4 coding screens functional (text, image, A/V, PDF)
- [ ] MCP tools: create_code, apply_code, list_codes, etc.
- [ ] Agent actions visible in UI (badges, activity panel)
