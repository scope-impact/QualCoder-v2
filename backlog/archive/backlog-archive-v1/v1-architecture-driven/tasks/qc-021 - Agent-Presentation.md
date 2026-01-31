---
id: QC-021
title: Agent Presentation
status: To Do
milestone: M-006
layer: Presentation
created_date: '2026-01-29'
labels: [presentation, agent, P1]
dependencies: [QC-020]
---

## Description

Build the dedicated Agent Experience screens.

## Acceptance Criteria

- [ ] AI Chat screen (mockup: `ai_chat.html`)
  - Conversational interface for coding assistance
  - Message history with agent responses
  - Quick actions (suggest codes, explain segment)
- [ ] AI Search screen (mockup: `ai_search.html`)
  - Semantic search across coded data
  - Natural language queries
  - Results with relevance scores
- [ ] Review Queue screen (mockup: `review_queue.html`)
  - Pending suggestions list
  - Batch approve/reject
  - Agent statistics dashboard
  - Session history

## Implementation

- `src/presentation/screens/agent/ai_chat.py`
- `src/presentation/screens/agent/ai_search.py`
- `src/presentation/screens/agent/review_queue.py`
- Mockups: `mockups/ai_chat.html`, `mockups/ai_search.html`, `mockups/review_queue.html`
