---
id: M-006
title: Agent Experience
status: To Do
created_date: '2026-01-29'
dependencies: [M-002]
---

## Description

Implement the dedicated Agent Experience screens - AI chat, semantic search, and review queue.

**Note:** Agent infrastructure (TrustLevel, sessions, agent server) is in M-001. Agent tools are in each context. This milestone adds the agent-specific UI screens.

## Goals

- AI chat interface for conversational coding assistance
- Semantic search across coded data
- Review queue for pending agent suggestions
- Agent activity dashboard

## Tasks

| ID | Task | Layer | Status |
|----|------|-------|--------|
| QC-020 | Agent Session Management | Application | To Do |
| QC-021 | Agent Presentation | Presentation | To Do |

## Success Criteria

- [ ] AI Chat screen functional (mockup: `ai_chat.html`)
- [ ] AI Search screen functional (mockup: `ai_search.html`)
- [ ] Review Queue screen functional (mockup: `review_queue.html`)
- [ ] Agent statistics and activity history
- [ ] Batch approve/reject in review queue
