---
id: M-007
title: Collaboration
status: To Do
created_date: '2026-01-29'
dependencies: [M-002]
---

## Description

Implement the Collaboration bounded context end-to-end - multi-coder workflows, project merging, and inter-rater reliability.

**Agent-First:** AI is treated as a coder. Agent codings are tracked separately for comparison and can be promoted to human codings after review.

## Goals

- Multiple coders per project (including AI as a coder)
- Code ownership tracking
- Project merge with conflict resolution
- Coder comparison (Kappa scores)
- MCP tools for coder context

## Tasks

| ID | Task | Layer | Status |
|----|------|-------|--------|
| QC-022 | Collaboration Domain | Domain | To Do |
| QC-023 | Collaboration Infrastructure | Infrastructure | To Do |
| QC-024 | Collaboration Application | Application | To Do |
| QC-025 | Collaboration Presentation | Presentation | To Do |

## Success Criteria

- [ ] Coder entity with ownership (human and AI coders)
- [ ] Merge engine with conflict detection
- [ ] Kappa score calculation
- [ ] Coder selector and comparison UI
- [ ] MCP tools: set_coder, compare_coders
- [ ] AI coder visibility toggle
