---
id: QC-012
title: Case Domain
status: To Do
milestone: M-004
layer: Domain
created_date: '2026-01-29'
labels: [domain, cases, agent, P2]
dependencies: [QC-001]
---

## Description

Define the domain layer for Case Management: entities, events, invariants, derivers, and agent tool schemas.

**Agent-First:** MCP tool schemas so AI can create cases and assign attributes.

## Acceptance Criteria

- [ ] Entities: Case, Attribute, AttributeValue
- [ ] Value objects: AttributeType
- [ ] Domain events (CaseCreated, MemberAdded, etc.)
- [ ] Invariants and derivers
- [ ] Agent tool schemas (create_case, list_cases, add_member, set_attribute)

## Implementation

- `src/domain/case/entities.py`
- `src/domain/case/events.py`
- `src/agent_context/schemas/case_tools.py`
