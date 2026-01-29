---
id: QC-007
title: Coding Presentation
status: To Do
milestone: M-002
layer: Presentation
created_date: '2026-01-29'
labels: [presentation, coding, agent, P1]
dependencies: [QC-006]
---

## Description

Build the UI screens for the Coding bounded context with agent observation.

**Agent-First:** UI shows agent activity. Agent actions appear with badges. Approval dialogs for Require trust level.

## Acceptance Criteria

- [ ] Text coding screen (mockup: `code_text.html`)
- [ ] Image coding screen (mockup: `code_image.html`)
- [ ] Audio/Video coding screen (mockup: `code_av.html`)
- [ ] PDF coding screen (mockup: `code_pdf.html`)
- [ ] Code tree panel (shared widget)
- [ ] Segment list panel (shared widget)
- [ ] Agent activity badges on agent-created items
- [ ] Approval dialog for Require-level operations
- [ ] Signal bridge (domain events → Qt signals)

## Subtasks

| ID | Subtask | Status |
|----|---------|--------|
| QC-007.1 | Code Tree Widget | To Do |
| QC-007.2 | Segment List Widget | To Do |
| QC-007.3 | Text Coding Screen | To Do |
| QC-007.4 | Image Coding Screen | To Do |
| QC-007.5 | A/V Coding Screen | To Do |
| QC-007.6 | PDF Coding Screen | To Do |
| QC-007.7 | Agent Activity Badges | To Do |
| QC-007.8 | Approval Dialog | To Do |

## Implementation

- `src/presentation/screens/coding/`
- `src/presentation/widgets/agent_badge.py`
- `src/presentation/dialogs/approval_dialog.py`
- Mockups: `mockups/code_*.html`
