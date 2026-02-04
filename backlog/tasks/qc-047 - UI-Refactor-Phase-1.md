---
id: QC-047
title: UI Refactor Phase 1 - Modern Layout
status: To Do
milestone: M-002
layer: Presentation
created_date: '2026-02-04'
labels: [presentation, coding, refactor, P1]
dependencies: []
---

## Description

Refactor UI components to match modern design mockup: unified navigation, simplified code list, streamlined toolbar, and collapsible details panel.

**Scope:** Focus on navigation and toolbar refactoring. Other components (CodesPanel, DetailsPanel, FilesPanel) deferred.

**Target Design:**
- Single horizontal navigation bar (no separate menu + tab bars)
- Minimal toolbar with source type tabs + search + "Show Details" toggle

**Estimated Effort:** 12-24 hours total

## Acceptance Criteria

- [ ] AppShell uses single unified navigation bar (Project | Files | Coding | Reports | AI)
- [ ] CodingToolbar simplified to source tabs + search + details toggle
- [ ] All existing keyboard shortcuts preserved
- [ ] E2E tests pass

## Subtasks

| ID | Subtask | Status | Effort |
|----|---------|--------|--------|
| QC-047.01 | AppShell Navigation Refactor | To Do | 8-16h |
| QC-047.03 | CodingToolbar Simplification | To Do | 4-8h |

## Implementation

**Files to modify:**
- `src/shared/presentation/templates/app_shell.py`
- `src/shared/presentation/organisms/coding_toolbar.py`
- `src/contexts/coding/presentation/screens/text_coding.py`

## Technical Notes

### Current vs Target Architecture

```
CURRENT:
┌─────────────────────────────────────────┐
│ Title Bar                               │
│ Menu Bar (Project|Files|Coding|...)     │
│ Tab Bar (Coding|Reports|Manage|...)     │
│ Toolbar (many buttons)                  │
│ ┌─────────┬───────────────┬──────────┐  │
│ │ Files   │ Text Editor   │ Details  │  │
│ │ Panel   │               │ Panel    │  │
│ ├─────────┤               │          │  │
│ │ Codes   │               │          │  │
│ │ Tree    │               │          │  │
│ └─────────┴───────────────┴──────────┘  │
│ Status Bar                              │
└─────────────────────────────────────────┘

TARGET:
┌─────────────────────────────────────────┐
│ QUALCODER | Project | Files | Coding... │  ← unified nav
│ ┌─────────┬───────────────────────────┐ │
│ │ CODES ← │ [Text][A/V][Image][PDF]   │ │
│ │         │ Search...    [Show Details]│ │
│ │ • Edu 12│                           │ │
│ │ • Fam  8│   (transcript content)    │ │
│ │ • Hea 15│                           │ │
│ │         │                           │ │
│ └─────────┴───────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Risk Mitigation

1. **Signal routing:** Keep ViewModel interface stable
2. **Keyboard shortcuts:** Test each after changes
3. **Screen switching:** Ensure navigation still routes correctly
