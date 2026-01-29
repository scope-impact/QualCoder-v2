---
id: QC-025
title: Collaboration Presentation
status: To Do
milestone: M-007
layer: Presentation
created_date: '2026-01-29'
labels: [presentation, collaboration, agent, P3]
dependencies: [QC-024]
---

## Description

Build the UI components for Collaboration.

**Agent-First:** AI coder visible in coder selector. Comparison shows human vs AI reliability.

## Acceptance Criteria

- [ ] Coder selector widget (shows human and AI coders)
- [ ] Coder manager dialog
- [ ] Merge UI with conflict display
- [ ] Comparison report (human vs human, human vs AI)
- [ ] AI coder visibility toggle
- [ ] Promote AI coding action

## Implementation

- `src/presentation/widgets/coder_selector.py`
- `src/presentation/screens/collaboration/`
- `src/presentation/dialogs/merge_dialog.py`
