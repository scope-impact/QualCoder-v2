---
id: QC-028
title: Manage Codes
status: In Progress
assignee: []
created_date: '2026-01-30 20:25'
updated_date: '2026-02-03 22:40'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Enable researchers and agents to create, organize, and manage the coding scheme (codes and categories).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Researcher can create new codes with name and color
- [x] #2 Researcher can organize codes into categories
- [x] #3 Researcher can rename and recolor codes
- [x] #4 Researcher can add memos to codes
- [x] #5 Researcher can merge duplicate codes
- [x] #6 Researcher can delete codes
- [x] #7 Agent can list all codes
- [x] #8 Agent can suggest new codes based on content
- [x] #9 Agent can detect potential duplicate codes
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added CreateCategoryDialog and DeleteCodeDialog with full black-box E2E tests (16 new tests)
<!-- SECTION:NOTES:END -->
