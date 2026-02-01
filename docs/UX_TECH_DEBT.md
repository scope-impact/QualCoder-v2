# UX Tech Debt Registry

This document tracks identified UX/usability issues discovered during design reviews and user testing. Issues are prioritized and linked to relevant screens/components.

## How to Use This Document

1. **Add new issues** when discovered during design reviews, user feedback, or testing
2. **Update status** when issues are addressed
3. **Link to tasks** when issues become backlog items
4. **Archive resolved** issues to the bottom section

## Priority Levels

| Priority | Description | Target Resolution |
|----------|-------------|-------------------|
| **P0** | Blocks core workflows or causes user confusion | Before release |
| **P1** | Significantly impacts efficiency or satisfaction | Next sprint |
| **P2** | Minor friction, has workaround | Backlog |
| **P3** | Nice-to-have improvement | Future consideration |

## Status Key

- `Open` - Identified, not yet addressed
- `In Progress` - Being worked on
- `Resolved` - Fixed, pending verification
- `Closed` - Verified fixed
- `Deferred` - Intentionally postponed
- `Won't Fix` - Decided not to address (with rationale)

---

## Open Issues

### File Manager Screen (`phase1_file_manager.html`)

**Review Date:** 2026-01-31
**Reviewer:** UX Audit
**Mockup:** `mockups/phase1_file_manager.html`

#### UX-001: Navigation Redundancy

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Status** | Open |
| **Heuristic** | Nielsen #4: Consistency and Standards |
| **Related Task** | QC-026.04 |

**Problem:**
Menu bar AND Tab bar show overlapping navigation concepts causing user confusion.

```
Menu:  Project | Files & Cases | Coding | Reports | AI | Help
Tabs:  Coding  | Reports       | Manage | Action Log
```

- "Files and Cases" in menu vs "Manage" in tabs point to same screen
- User doesn't know which navigation to use
- Inconsistent mental model

**Recommendation:**
Choose one navigation paradigm:

```
Option A: Remove tab bar, use menu as primary navigation
Option B: Separate concerns:
  - Menu = global functions (File, Edit, View, Tools, Help)
  - Tabs = content switching within current screen (Files, Cases, Journals, Attributes)
```

**Acceptance Criteria:**
- [ ] Single, clear navigation model chosen
- [ ] No duplicate paths to same destination
- [ ] User can navigate without confusion about which nav to use

---

#### UX-002: Empty State Missing

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Status** | Open |
| **Heuristic** | Nielsen #1: Visibility of System Status |
| **Related Task** | QC-026.02, QC-026.03 |

**Problem:**
No empty state design for new projects. New user creates project → sees empty table → confused about next steps.

**Recommendation:**
Add empty state with clear call-to-action:

```
┌──────────────────────────────────────────────┐
│                                              │
│              📁                              │
│         No files yet                         │
│                                              │
│   Import your first source files to          │
│   start coding your qualitative data         │
│                                              │
│   [Import Files]  [Link External Files]      │
│                                              │
│   Supported: TXT, DOCX, PDF, MP3, MP4, JPG   │
└──────────────────────────────────────────────┘
```

**Acceptance Criteria:**
- [ ] Empty state displays when project has no files
- [ ] Clear primary action (Import) visible
- [ ] Brief explanation of what to do next
- [ ] Supported file types shown

---

#### UX-003: Stats Cards Low Utility

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Status** | Open |
| **Heuristic** | Fitts's Law, Information Density |
| **Related Task** | QC-026.03 |

**Problem:**
Stats row takes ~100px vertical space showing only counts. Cards are not interactive, taking prime real estate from the table (main task area).

**Current:** 5 large cards showing counts (not clickable)

**Recommendation:**

Option A - Make cards actionable:
- Click card → filters table to that type
- Visual feedback when filter active

Option B - Compact bar:
```
📄 12 Text  |  🎵 5 Audio  |  🎬 3 Video  |  🖼️ 8 Images  |  📕 4 PDF  [Clear Filter]
```

Option C - Collapsible panel:
- Stats in collapsible sidebar/header
- User can hide when not needed

**Acceptance Criteria:**
- [ ] Stats provide filtering capability OR
- [ ] Stats condensed to reduce vertical space
- [ ] Users can access full table without scrolling past large stats

---

#### UX-004: Primary Action Mismatch

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Status** | Open |
| **Heuristic** | User Task Flow Analysis |
| **Related Task** | QC-026.03, QC-026.04 |

**Problem:**
"Import Files" is styled as primary action (teal button), but the most common user action is **opening a file to code**.

**User Journey Analysis:**
1. Open project ✓
2. See files ✓ (this screen)
3. **Pick a file to code** ← most frequent next step
4. Import happens occasionally

**Recommendation:**
- Double-click row → opens file for coding
- Add visual affordance (cursor: pointer, hover hint)
- When file selected, show "Open for Coding" as primary action
- "Import" becomes secondary button

**Acceptance Criteria:**
- [ ] Double-click opens file for coding
- [ ] Visual hint that rows are clickable
- [ ] Selected file shows contextual primary action

---

#### UX-005: Bulk Actions Hidden

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Status** | Open |
| **Heuristic** | Efficiency of Use |
| **Related Task** | QC-026.03 |

**Problem:**
Selecting multiple files provides no bulk action interface. Users must act on files one at a time.

**Scenario:** User selects 5 files → wants to delete/export/assign to case → no way to do it

**Recommendation:**
Show contextual action bar when selection > 0:

```
┌─────────────────────────────────────────────────────┐
│ ✓ 3 files selected    [Code] [Delete] [Export] [×] │
└─────────────────────────────────────────────────────┘
```

**Acceptance Criteria:**
- [ ] Selection count displayed when files selected
- [ ] Bulk actions appear (Delete, Export, Assign Case)
- [ ] Clear selection button (×) available
- [ ] Actions disabled when nothing selected

---

#### UX-006: Table Column Improvements

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Status** | Open |
| **Heuristic** | Information Architecture |
| **Related Task** | QC-026.03 |

**Problem:**
Current columns don't optimally match researcher mental model.

| Current Column | Issue |
|----------------|-------|
| Type | Redundant - icon already shows type |
| Cases | Shows "ID3", "-" - cryptic |
| Origin | Unclear meaning |
| Status | States not clearly defined |

**Missing useful columns:**
- Code count (how many codes applied?)
- Last modified (often more useful than date added)
- Memo indicator (has notes?)

**Recommendation:**
Default columns:
```
☑ | File Name (with type icon) | Codes | Cases | Modified | Status | Actions
```

- Remove redundant "Type" text column (icon sufficient)
- Show case names, not just IDs
- Add code count badge
- Column chooser for customization

**Acceptance Criteria:**
- [ ] Default columns optimized for researcher workflow
- [ ] Cases show meaningful names, not just IDs
- [ ] Code count visible at glance
- [ ] Column chooser allows customization

---

#### UX-007: Keyboard Accessibility

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Status** | Open |
| **Heuristic** | Accessibility (WCAG), Nielsen #7: Flexibility |
| **Related Task** | QC-026.04 |

**Problem:**
No visible keyboard shortcuts or accessibility hints.

**Missing:**
- No keyboard shortcut indicators (e.g., "Import Files (Ctrl+I)")
- Tab order not defined
- No skip-to-content link
- Focus ring visibility unclear
- No ARIA labels shown

**Recommendation:**
- Add shortcut hints: `Import Files (Ctrl+I)`
- Define logical tab order
- Ensure visible focus ring on all interactive elements
- Add aria-labels for screen readers
- Document keyboard shortcuts in Help

**Acceptance Criteria:**
- [ ] Common actions have keyboard shortcuts
- [ ] Shortcuts displayed in UI (tooltips or inline)
- [ ] Tab navigation works logically
- [ ] Focus states clearly visible

---

#### UX-008: Search Scope Unclear

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Status** | Open |
| **Heuristic** | Nielsen #6: Recognition over Recall |
| **Related Task** | QC-026.03 |

**Problem:**
"Search files..." placeholder doesn't indicate what's being searched (names only? content? metadata?).

**Recommendation:**
- Clarify placeholder: "Search file names..."
- Add scope selector dropdown: `Search in: [Names ▼]`
  - Options: Names, Content, All
- Show search scope in results: "3 results in file names"

**Acceptance Criteria:**
- [ ] Search scope is clear to user
- [ ] Optional: user can change search scope

---

#### UX-009: Status Badge Lifecycle

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Status** | Open |
| **Heuristic** | Nielsen #1: Visibility of System Status |
| **Related Task** | QC-026.03 |

**Problem:**
Status badges shown (Coded, Transcribing, Imported, In Progress) but full lifecycle unclear.

**Missing states:**
- Error (red) - failed import/transcription
- Queued (gray) - waiting for AI processing
- Partial (orange) - partially coded

**Recommendation:**
Document and implement full status lifecycle:

```
Import Flow:    Importing → Imported → Ready
                    ↓
                  Error

Transcription:  Queued → Transcribing → Transcribed
                             ↓
                           Error

Coding:         Ready → In Progress → Coded
                           ↓
                        Partial
```

**Acceptance Criteria:**
- [ ] All possible states documented
- [ ] Error states have visual treatment (red)
- [ ] Transitional states clear (Queued, Processing)
- [ ] Status tooltips explain meaning

---

#### UX-010: Project Context in Header

| Field | Value |
|-------|-------|
| **Priority** | P3 |
| **Status** | Open |
| **Heuristic** | Nielsen #1: Visibility of System Status |
| **Related Task** | QC-026.05 |

**Problem:**
Title bar shows project name but limited context. Researchers working on multiple projects need quick orientation.

**Current:** `QualCoder - research_project.qda`

**Recommendation:**
Enhanced title or status bar:
```
QualCoder - research_project.qda  |  32 files  |  15 codes  |  Dr. Smith
```

Or in status bar:
```
📁 research_project.qda  •  32 sources  •  15 codes  •  Last opened: 2 min ago
```

**Acceptance Criteria:**
- [ ] Project context visible without navigation
- [ ] Key stats (file count, code count) at glance
- [ ] Current user/coder indicated if multi-user

---

## Heuristic Summary Score

**Screen:** File Manager
**Date:** 2026-01-31

| Heuristic | Score | Notes |
|-----------|-------|-------|
| 1. Visibility of System Status | 8/10 | Good status bar, missing loading/empty states |
| 2. Match Between System and Real World | 6/10 | Some jargon (Origin, Cases as IDs) |
| 3. User Control and Freedom | 7/10 | Good escape (Esc modal), missing undo |
| 4. Consistency and Standards | 5/10 | Navigation redundancy is confusing |
| 5. Error Prevention | 6/10 | No bulk delete confirmation shown |
| 6. Recognition Rather Than Recall | 8/10 | Good icons, badges, visual cues |
| 7. Flexibility and Efficiency of Use | 7/10 | Multiple paths, missing keyboard shortcuts |
| 8. Aesthetic and Minimalist Design | 9/10 | Clean Material Design, good contrast |
| 9. Help Users Recover from Errors | N/A | Not demonstrated in mockup |
| 10. Help and Documentation | 4/10 | No tooltips, no onboarding hints |

**Overall Score: 6.6/10** - Good foundation, needs refinement for production

---

## Resolved Issues

_None yet - move issues here when closed_

---

## Appendix: Review Checklist

Use this checklist when reviewing new screens:

### Visual Design
- [ ] Consistent with design system tokens
- [ ] Proper visual hierarchy
- [ ] Adequate contrast ratios (WCAG AA)
- [ ] Responsive considerations

### Information Architecture
- [ ] Logical grouping of related items
- [ ] Clear labeling (no jargon)
- [ ] Appropriate information density

### Interaction Design
- [ ] Clear affordances (what's clickable?)
- [ ] Feedback for all actions
- [ ] Error states defined
- [ ] Empty states defined
- [ ] Loading states defined

### Accessibility
- [ ] Keyboard navigable
- [ ] Screen reader compatible
- [ ] Focus states visible
- [ ] Color not sole indicator

### Efficiency
- [ ] Common tasks are quick
- [ ] Power user shortcuts available
- [ ] Bulk actions where appropriate
- [ ] Search/filter available
