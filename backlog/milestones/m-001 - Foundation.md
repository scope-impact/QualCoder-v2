---
id: M-001
title: Foundation
status: In Progress
created_date: '2026-01-29'
---

## Description

Establish the foundational layers of QualCoder v2: shared domain types, agent infrastructure, design system, and application shell.

**Agent-First:** The agent context foundation is established here so every subsequent vertical slice can expose both human UI and agent tools.

## Goals

- Shared types (Result monad, IDs, base protocols)
- Agent infrastructure (TrustLevel, session, agent server base)
- Reusable UI component library
- Application shell with navigation

## Tasks

| ID | Task | Layer | Status |
|----|------|-------|--------|
| QC-001 | Shared Domain Types & Agent Foundation | Domain | Done |
| QC-002 | Design System Components | Presentation | Done |
| QC-003 | Application Shell | Presentation | Done |
| QC-003.01 | Base Signal Bridge Infrastructure | Application | Done |
| QC-003.02 | Event Bus Infrastructure | Application | To Do |

## Success Criteria

- [x] Result[T, E] type with Success/Failure
- [x] Base ID types and protocols
- [x] TrustLevel, AgentSession, approval workflow base
- [x] Agent server skeleton ready to register tools
- [x] 50+ reusable UI components
- [x] Navigation and layout system
- [x] BaseSignalBridge with thread-safe event→signal bridging
- [ ] EventBus with pub/sub for domain events
