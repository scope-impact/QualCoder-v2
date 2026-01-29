---
id: QC-001
title: Shared Domain Types & Agent Foundation
status: Done
milestone: M-001
layer: Domain
created_date: '2026-01-29'
labels: [domain, agent, foundation, P0]
---

## Description

Define the shared types used across all bounded contexts, including agent infrastructure.

**Agent-First:** TrustLevel and session types are foundational so every context can be agent-aware.

## Acceptance Criteria

- [x] Result[T, E] monad (Success | Failure)
- [x] Base ID types (CodeId, SourceId, etc.)
- [x] DomainEvent base class
- [x] Common value objects (Color, etc.)
- [x] TrustLevel enum (Autonomous, Notify, Suggest, Require)
- [x] AgentSession base type
- [x] MCP tool schema base protocol

## Implementation

- `src/domain/shared/types.py`
- `src/domain/shared/agent.py`
- `src/agent_context/protocols.py`
