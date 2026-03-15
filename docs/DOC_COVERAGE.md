# Documentation Coverage Matrix

This file tracks which features have documentation, screenshots, and E2E test coverage.

## Legend

| Status | Meaning |
|--------|---------|
| :white_check_mark: | Documented with screenshots |
| :construction: | Partial documentation |
| :x: | Missing documentation |

E2E column: number of `@allure.story` test classes covering that task.

---

## Feature Coverage

### QC-026 Open & Navigate Project

| ID | Story | Doc Page | Screenshots | E2E | Status |
|----|-------|----------|-------------|-----|--------|
| QC-026.01 | Open Existing Project | - | - | 2 | :x: |
| QC-026.02 | Create New Project | - | - | 3 | :x: |
| QC-026.03 | View Source List | - | - | 1 | :x: |
| QC-026.04 | Switch Between Screens | - | - | 2 | :x: |
| QC-026.05 | Get Project Context | [mcp-api.md](api/mcp-api.md) | - | 1 | :construction: |
| QC-026.06 | Navigate to Source | [sources.md](user-manual/sources.md), [mcp-api.md](api/mcp-api.md) | - | 1 | :construction: |
| QC-026.07 | Agent Open/Close Project | [mcp-setup.md](user-manual/mcp-setup.md), [mcp-api.md](api/mcp-api.md) | - | 2 | :construction: |

### QC-027 Manage Sources

| ID | Story | Doc Page | Screenshots | E2E | Status |
|----|-------|----------|-------------|-----|--------|
| QC-027.01 | Import Text Document | [sources.md](user-manual/sources.md) | file-manager-empty.png, file-manager-with-folders.png | 1 | :white_check_mark: |
| QC-027.02 | Import PDF Document | [sources.md](user-manual/sources.md) | - | 1 | :construction: |
| QC-027.03 | Import Image | [sources.md](user-manual/sources.md) | image-viewer.png | 1 | :white_check_mark: |
| QC-027.04 | Import Audio/Video | [sources.md](user-manual/sources.md) | media-player.png | 1 | :white_check_mark: |
| QC-027.05 | Organize Sources | [sources.md](user-manual/sources.md) | file-manager-with-folders.png | 6 | :white_check_mark: |
| QC-027.06 | View Source Metadata | - | - | 1 | :x: |
| QC-027.07 | Delete Source | - | - | 1 | :x: |
| QC-027.08 | Agent List Sources | [sources.md](user-manual/sources.md), [mcp-api.md](api/mcp-api.md) | - | 1 | :construction: |
| QC-027.09 | Agent Read Source Content | [sources.md](user-manual/sources.md), [mcp-api.md](api/mcp-api.md) | - | 1 | :construction: |
| QC-027.10 | Agent Extract Source Metadata | [sources.md](user-manual/sources.md), [mcp-api.md](api/mcp-api.md) | - | 1 | :construction: |
| QC-027.11 | Import Folder (Bulk) | - | - | 1 | :x: |
| QC-027.12 | Agent Add Text Source | [sources.md](user-manual/sources.md), [mcp-api.md](api/mcp-api.md) | - | 1 | :construction: |
| QC-027.13 | Agent Manage Folders | [sources.md](user-manual/sources.md), [mcp-api.md](api/mcp-api.md) | - | 1 | :construction: |
| QC-027.14 | Agent Remove Source | [sources.md](user-manual/sources.md), [mcp-api.md](api/mcp-api.md) | - | 1 | :construction: |
| QC-027.15 | Agent Import File Source | [sources.md](user-manual/sources.md), [mcp-api.md](api/mcp-api.md) | - | 3 | :construction: |

### QC-027.05 Organize Sources (Folder Management)

| ID | Story | Doc Page | Screenshots | E2E | Status |
|----|-------|----------|-------------|-----|--------|
| QC-027.05 | Create Folder | [sources.md](user-manual/sources.md), [mcp-api.md](api/mcp-api.md) | file-manager-with-folders.png | 6 | :white_check_mark: |
| QC-027.05 | Rename Folder | [sources.md](user-manual/sources.md), [mcp-api.md](api/mcp-api.md) | file-manager-with-folders.png | 6 | :white_check_mark: |
| QC-027.05 | Delete Folder | [sources.md](user-manual/sources.md), [mcp-api.md](api/mcp-api.md) | file-manager-with-folders.png | 6 | :white_check_mark: |
| QC-027.05 | Move Source to Folder | [sources.md](user-manual/sources.md), [mcp-api.md](api/mcp-api.md) | file-manager-with-folders.png | 6 | :white_check_mark: |
| QC-027.05 | Folder Policies | [sources.md](user-manual/sources.md), [mcp-api.md](api/mcp-api.md) | - | 6 | :construction: |

### QC-028 Manage Codes

| ID | Story | Doc Page | Screenshots | E2E | Status |
|----|-------|----------|-------------|-----|--------|
| QC-028.01 | Create New Code | [codes.md](user-manual/codes.md) | create-code-dialog.png | 3 | :white_check_mark: |
| QC-028.02 | Create Code Category | [codes.md](user-manual/codes.md) | create-category-initial.png, create-category-name.png, create-category-parent.png, create-category-filled.png | 1 | :white_check_mark: |
| QC-028.03 | Edit Code Properties | [codes.md](user-manual/codes.md) | color-picker-presets.png, color-picker-custom-hex.png, color-picker-selected.png | 2 | :white_check_mark: |
| QC-028.04 | Merge Codes | [codes.md](user-manual/codes.md) | duplicate-codes-empty.png, duplicate-codes-list.png, duplicate-codes-similarity.png | 1 | :white_check_mark: |
| QC-028.05 | Delete Code | [codes.md](user-manual/codes.md) | delete-code-simple.png, delete-code-warning.png, delete-code-segments-checked.png | 1 | :white_check_mark: |

### QC-050 Agent Code Management MCP Tools

| ID | Story | Doc Page | Screenshots | E2E | Status |
|----|-------|----------|-------------|-----|--------|
| QC-050.01 | rename_code MCP tool | [ai-features.md](user-manual/ai-features.md), [mcp-api.md](api/mcp-api.md) | - | 1 | :construction: |
| QC-050.02 | update_code_memo MCP tool | [ai-features.md](user-manual/ai-features.md), [mcp-api.md](api/mcp-api.md) | - | 1 | :construction: |
| QC-050.03 | create_category MCP tool | [ai-features.md](user-manual/ai-features.md), [mcp-api.md](api/mcp-api.md) | - | 1 | :construction: |
| QC-050.04 | move_code_to_category MCP tool | [ai-features.md](user-manual/ai-features.md), [mcp-api.md](api/mcp-api.md) | - | 1 | :construction: |
| QC-050.05 | merge_codes MCP tool | [ai-features.md](user-manual/ai-features.md), [mcp-api.md](api/mcp-api.md) | - | 1 | :construction: |
| QC-050.06 | delete_code MCP tool | [ai-features.md](user-manual/ai-features.md), [mcp-api.md](api/mcp-api.md) | - | 1 | :construction: |
| QC-050.07 | list_categories MCP tool | [ai-features.md](user-manual/ai-features.md), [mcp-api.md](api/mcp-api.md) | - | 1 | :construction: |
| QC-050.08 | Tool registration and response format | [mcp-api.md](api/mcp-api.md) | - | 2 | :construction: |

### QC-029 Apply Codes to Text

| ID | Story | Doc Page | Screenshots | E2E | Status |
|----|-------|----------|-------------|-----|--------|
| QC-029.01 | Select Text and Apply Code | [coding.md](user-manual/coding.md) | coding-screen-with-codes.png | 2 | :white_check_mark: |
| QC-029.02 | Apply Multiple Codes | [coding.md](user-manual/coding.md) | coding-multiple-codes.png | 1 | :white_check_mark: |
| QC-029.03 | View Coded Segments | [coding.md](user-manual/coding.md) | coding-screen-selected.png | 1 | :white_check_mark: |
| QC-029.04 | View Segments for Code | [coding.md](user-manual/coding.md) | - | 1 | :construction: |
| QC-029.05 | Remove Coding | [coding.md](user-manual/coding.md) | - | 1 | :construction: |
| QC-029.06 | Add Segment Memo | [coding.md](user-manual/coding.md) | memos-panel.png | 2 | :white_check_mark: |
| QC-029.09 | List Coded Segments | - | - | 0 | :x: |

### QC-028 Manage Codes (Agent Stories)

| ID | Story | Doc Page | Screenshots | E2E | Status |
|----|-------|----------|-------------|-----|--------|
| QC-028.06 | List All Codes | [mcp-api.md](api/mcp-api.md) | - | 1 | :construction: |
| QC-028.07 | Suggest New Code | [ai-features.md](user-manual/ai-features.md), [mcp-api.md](api/mcp-api.md) | code-suggestions.png | 2 | :white_check_mark: |
| QC-028.08 | Detect Duplicate Codes | [ai-features.md](user-manual/ai-features.md), [mcp-api.md](api/mcp-api.md) | duplicate-codes.png | 2 | :white_check_mark: |

### QC-029 Apply Codes to Text (Agent Stories)

| ID | Story | Doc Page | Screenshots | E2E | Status |
|----|-------|----------|-------------|-----|--------|
| QC-029.07 | Apply Code to Text Range | [mcp-api.md](api/mcp-api.md) | - | 1 | :construction: |
| QC-029.08 | Suggest Codes for Text | [ai-features.md](user-manual/ai-features.md), [mcp-api.md](api/mcp-api.md) | - | 1 | :construction: |

### QC-030 AI Features (Researcher Stories)

| ID | Story | Doc Page | Screenshots | E2E | Status |
|----|-------|----------|-------------|-----|--------|
| QC-030.01 | Code Suggestions | [ai-features.md](user-manual/ai-features.md) | code-suggestions-empty.png, code-suggestions-list.png, code-suggestions-details.png | 0 | :white_check_mark: |
| QC-030.02 | Semantic Search | [ai-features.md](user-manual/ai-features.md) | - | 0 | :x: |
| QC-030.03 | Auto-coding | [ai-features.md](user-manual/ai-features.md) | auto-code-pattern.png, auto-code-preview.png | 0 | :white_check_mark: |

### QC-032 Auto-Code

| ID | Story | Doc Page | Screenshots | E2E | Status |
|----|-------|----------|-------------|-----|--------|
| QC-032.01 | Search Text Pattern | - | - | 1 | :x: |
| QC-032.02 | Preview Matches | - | - | 1 | :x: |
| QC-032.03 | Apply Code to All Matches | - | - | 1 | :x: |
| QC-032.04 | Undo Batch Coding | - | - | 1 | :x: |
| QC-032.05 | Auto-Code by Speaker | - | - | 1 | :x: |
| QC-032.06 | Find Similar Passages | - | - | 1 | :x: |

### QC-034 Manage Cases

| ID | Story | Doc Page | Screenshots | E2E | Status |
|----|-------|----------|-------------|-----|--------|
| QC-034.01 | Create Case | [user-manual](user-manual/index.md) | - | 1 | :construction: |
| QC-034.02 | Link Source to Case | [user-manual](user-manual/index.md) | - | 1 | :construction: |
| QC-034.03 | Add Case Attributes | [user-manual](user-manual/index.md) | - | 1 | :construction: |
| QC-034.04 | View Case Data | [user-manual](user-manual/index.md) | case-manager-empty.png, case-manager-list.png | 1 | :white_check_mark: |
| QC-034.05 | List All Cases | - | - | 0 | :x: |
| QC-034.06 | Suggest Case Groupings | - | - | 0 | :x: |
| QC-034.07 | Compare Across Cases | - | - | 0 | :x: |
| QC-034.08 | Case Attribute Detail Panel | - | - | 0 | :x: |

### QC-039 Import Export Formats

| ID | Story | Doc Page | Screenshots | E2E | Status |
|----|-------|----------|-------------|-----|--------|
| QC-039.01 | Export REFI-QDA Project | [exchange.md](user-manual/exchange.md), [mcp-api.md](api/mcp-api.md) | exchange-export-menu.png | 2 | :white_check_mark: |
| QC-039.02 | Import REFI-QDA Project | [exchange.md](user-manual/exchange.md), [mcp-api.md](api/mcp-api.md) | exchange-import-menu.png | 2 | :white_check_mark: |
| QC-039.03 | Import RQDA Project | [exchange.md](user-manual/exchange.md), [mcp-api.md](api/mcp-api.md) | exchange-import-menu.png | 2 | :white_check_mark: |
| QC-039.04 | Export Codebook | [exchange.md](user-manual/exchange.md), [mcp-api.md](api/mcp-api.md) | exchange-export-menu.png | 1 | :white_check_mark: |
| QC-039.05 | Export Coded Text as HTML | [exchange.md](user-manual/exchange.md), [mcp-api.md](api/mcp-api.md) | exchange-export-menu.png | 1 | :white_check_mark: |
| QC-039.06 | Import Survey Data | [exchange.md](user-manual/exchange.md), [mcp-api.md](api/mcp-api.md) | exchange-import-menu.png | 2 | :white_check_mark: |
| QC-039.07 | Import Code List | [exchange.md](user-manual/exchange.md), [mcp-api.md](api/mcp-api.md) | exchange-import-menu.png | 1 | :white_check_mark: |

### QC-038 Settings

| ID | Story | Doc Page | Screenshots | E2E | Status |
|----|-------|----------|-------------|-----|--------|
| QC-038.01 | Configure Backups | [settings.md](user-manual/settings.md) | settings-default-theme.png, settings-dark-theme.png | 1 | :white_check_mark: |
| QC-038.02 | Change UI Theme | [settings.md](user-manual/settings.md) | settings-navigation.png | 1 | :white_check_mark: |
| QC-038.03 | Configure Fonts | [settings.md](user-manual/settings.md) | settings-full.png | 1 | :white_check_mark: |
| QC-038.04 | Select Language | [mcp-setup.md](user-manual/mcp-setup.md) | - | 1 | :construction: |
| QC-038.05 | Configure Timestamp Format | - | - | 1 | :x: |

### QC-049 Observability

| ID | Story | Doc Page | Screenshots | E2E | Status |
|----|-------|----------|-------------|-----|--------|
| QC-049.03 | Configurable Logging Levels | [observability.md](user-manual/observability.md) | - | 6 | :construction: |
| QC-049.05 | User Documentation | [observability.md](user-manual/observability.md) | - | 6 | :white_check_mark: |

### QC-047 S3 Data Store

| ID | Story | Doc Page | Screenshots | E2E | Status |
|----|-------|----------|-------------|-----|--------|
| QC-047.01 | Store Repository Persistence | [data-store.md](user-manual/data-store.md), [storage-tools.md](api/storage-tools.md) | settings-data-store.png | 1 | :white_check_mark: |
| QC-047.06 | MCP Storage Tools | [storage-tools.md](api/storage-tools.md) | - | 1 | :white_check_mark: |
| QC-047.07 | Settings Data Store Configuration | [data-store.md](user-manual/data-store.md) | - | 2 | :white_check_mark: |
| QC-047.08 | Import from S3 Dialog | [data-store.md](user-manual/data-store.md) | import-from-s3-dialog.png | 2 | :white_check_mark: |
| QC-047.10 | E2E Storage Workflow | - | - | 1 | :x: |
| QC-047.11 | AppContext Storage Wiring | - | - | 1 | :x: |

### QC-048 Version Control

| ID | Story | Doc Page | Screenshots | E2E | Status |
|----|-------|----------|-------------|-----|--------|
| QC-048.01 | Initialize VCS | [version-control.md](user-manual/version-control.md), [mcp-api.md](api/mcp-api.md) | - | 5 | :white_check_mark: |
| QC-048.02 | Auto-commit on Changes | [version-control.md](user-manual/version-control.md) | - | 5 | :white_check_mark: |
| QC-048.03 | View History | [version-control.md](user-manual/version-control.md), [mcp-api.md](api/mcp-api.md) | version-history-screen.png | 5 | :white_check_mark: |
| QC-048.04 | Restore Snapshot | [version-control.md](user-manual/version-control.md), [mcp-api.md](api/mcp-api.md) | version-history-screen.png | 5 | :white_check_mark: |
| QC-048.05 | View Diff | [version-control.md](user-manual/version-control.md), [mcp-api.md](api/mcp-api.md) | version-history-screen.png | 5 | :white_check_mark: |
| QC-048.06 | Diff Highlighting | [colors.md](api/tokens/colors.md) | - | 0 | :white_check_mark: |

### QC-051 Replication Tests

| ID | Story | Doc Page | Screenshots | E2E | Status |
|----|-------|----------|-------------|-----|--------|
| QC-051.01 | Thematic Analysis Replication | - | - | 5 | :x: |
| QC-051.02 | Sheffield / CSV Import | - | - | 6 | :x: |
| QC-051.03 | ICPC Replication | - | - | 4 | :x: |
| QC-051.04 | Configurable ID Column | - | - | 1 | :x: |
| QC-051.05 | Case Merge Behavior | - | - | 1 | :x: |
| QC-051.07 | MCP Tool import_firebase | - | - | 1 | :x: |

### QC-054 Thread-Safe Infrastructure

| ID | Story | Doc Page | Screenshots | E2E | Status |
|----|-------|----------|-------------|-----|--------|
| QC-054.01 | SingletonThreadPool Connection Factory | - | - | 1 | :x: |
| QC-054.02 | Repo Worker Thread Access | - | - | 1 | :x: |
| QC-054.03 | Concurrent Repo Access Stress Test | - | - | 1 | :x: |
| QC-054.04 | MCP asyncio.to_thread Integration | - | - | 1 | :x: |
| QC-054.05 | Pool Cleanup on Project Close | - | - | 1 | :x: |

---

## Image Inventory

All images in `docs/user-manual/images/`:

### File Manager
- [x] `file-manager-empty.png`
- [x] `file-manager-with-folders.png`

### Coding Screen
- [x] `coding-screen-with-codes.png`
- [x] `coding-screen-selected.png`

### Create Code Dialog
- [x] `create-code-dialog.png`

### Delete Code
- [x] `delete-code-simple.png`
- [x] `delete-code-warning.png`
- [x] `delete-code-segments-checked.png`

### Color Picker
- [x] `color-picker-presets.png`
- [x] `color-picker-custom-hex.png`
- [x] `color-picker-selected.png`

### Categories
- [x] `create-category-initial.png`
- [x] `create-category-name.png`
- [x] `create-category-parent.png`
- [x] `create-category-filled.png`

### Duplicate Codes
- [x] `duplicate-codes-empty.png`
- [x] `duplicate-codes-list.png`
- [x] `duplicate-codes-similarity.png`

### AI Features
- [x] `code-suggestions-empty.png`
- [x] `code-suggestions-list.png`
- [x] `code-suggestions-details.png`
- [x] `auto-code-pattern.png`
- [x] `auto-code-preview.png`

### Settings
- [x] `settings-default-theme.png`
- [x] `settings-dark-theme.png`
- [x] `settings-navigation.png`
- [x] `settings-full.png`

### Cases
- [x] `case-manager-empty.png`
- [x] `case-manager-list.png`

### Media Viewers
- [x] `image-viewer.png`
- [x] `media-player.png`

### Main Window
- [x] `main-window-startup.png`

### Memos
- [x] `memos-panel.png`

### Additional Coding
- [x] `coding-multiple-codes.png`

### Version Control
- [x] `version-history-screen.png` (includes inline diff viewer)

### Exchange (Import/Export)
- [x] `exchange-import-menu.png`
- [x] `exchange-export-menu.png`

---

## Backlog Dependencies (ASCII)

```
Legend: [x] Done  [~] In Progress  [ ] To Do  ──> depends on

═══════════════════════════════════════════════════════════════════════════════
                        QualCoder v2 Backlog Dependencies
═══════════════════════════════════════════════════════════════════════════════

QC-026 [ ] Open & Navigate Project
├── .01 [ ] Open Existing Project
├── .02 [ ] Create New Project
├── .03 [ ] View Source List
├── .04 [ ] Switch Between Screens
├── .05 [ ] Get Project Context
├── .06 [ ] Navigate to Source
└── .07 [x] Agent Open/Close Project

QC-027 [ ] Manage Sources
├── .01 [ ] Import Text Document
├── .02 [ ] Import PDF Document
├── .03 [ ] Import Image Files ·······················╮
├── .04 [ ] Import Audio Video Files ··········╮      │
├── .05 [ ] Organize Sources                   │      │
├── .06 [ ] View Source Metadata               │      │
├── .07 [ ] Delete Source                      │      │
├── .08 [ ] List Sources                       │      │
├── .09 [ ] Read Source Content                │      │
├── .10 [ ] Extract Source Metadata            │      │
├── .11 [ ] Import Folder (Bulk Import)        │      │
├── .12 [x] Agent Add Text Source              │      │
├── .13 [x] Agent Manage Folders               │      │
├── .14 [x] Agent Remove Source                │      │
└── .15 [x] Agent Import File Source           │      │
                                               │      │
QC-028 [~] Manage Codes                        │      │
├── .01 [x] Create New Code ···········╮       │      │
├── .02 [x] Create Code Category ······│──╮    │      │
├── .03 [x] Edit Code Properties ······│──│─╮  │      │
├── .04 [x] Merge Codes ···············│──│─│  │      │
├── .05 [x] Delete Code                │  │ │  │      │
├── .06 [x] List All Codes            │  │ │  │      │
├── .07 [ ] Suggest New Code           │  │ │  │      │
└── .08 [ ] Detect Duplicate Codes     │  │ │  │      │
                                       │  │ │  │      │
QC-029 [~] Apply Codes to Text ·······─│──│─│──│──────│──╮
├── .01 [x] Select Text & Apply Code   │  │ │  │      │  │
├── .02 [x] Apply Multiple Codes       │  │ │  │      │  │
├── .03 [x] View Coded Segments        │  │ │  │      │  │
├── .04 [x] View Segments for Code     │  │ │  │      │  │
├── .05 [x] Remove Coding              │  │ │  │      │  │
├── .06 [x] Add Segment Memo           │  │ │  │      │  │
├── .07 [ ] Apply Code to Text Range   │  │ │  │      │  │
├── .08 [ ] Suggest Codes for Text     │  │ │  │      │  │
└── .09 [x] List Coded Segments        │  │ │  │      │  │
                                       │  │ │  │      │  │
QC-045 [ ] Complete Coding Context     │  │ │  │      │  │
├── .01 [ ] Image Coding Controller ···│──│─│──│──────│──│──╮
├── .02 [ ] Image Coding Screen ·······│──│─│──│──────│──│──│──╮
├── .03 [ ] AV Coding Controller ······│──│─│──│──╮   │  │  │  │
└── .04 [ ] AV Coding Screen ··········│──│─│──│──│─╮ │  │  │  │
                                       │  │ │  │  │ │ │  │  │  │
QC-030 [ ] Apply Codes to Images ◄─────│──│─│──│──│─│─╯──│──╯──╯
├── .01 [ ] Draw Region on Image       │  │ │  │  │ │    │
├── .02 [ ] Apply Code to Image Region │  │ │  │  │ │    │
├── .03 [ ] View Coded Image Regions   │  │ │  │  │ │    │
├── .04 [ ] Remove Image Region Coding │  │ │  │  │ │    │
├── .05 [ ] Detect Image Regions       │  │ │  │  │ │    │
└── .06 [ ] Suggest Codes for Image    │  │ │  │  │ │    │
      depends on: QC-045.01, .02, 027.03  │ │  │  │ │    │
                                       │  │ │  │  │ │    │
QC-031 [ ] Apply Codes to AV ◄────────│──│─│──│──╯─╯    │
├── .01 [ ] Play Media w/ Transcript   │  │ │  │         │
├── .02 [ ] Mark Time Range            │  │ │  │         │
├── .03 [ ] Apply Code to Time Range   │  │ │  │         │
├── .04 [ ] View Coded Timeline        │  │ │  │         │
├── .05 [ ] Transcribe Media           │  │ │  │         │
├── .06 [ ] Detect Speakers            │  │ │  │         │
└── .07 [ ] Suggest Codes from Trans.  │  │ │  │         │
      depends on: QC-045.03, .04, 027.04  │ │  │         │
                                       │  │ │  │         │
                              ╭────────│──│─│──│─────────╯
                              │        │  │ │  │
                              ▼        │  │ │  │
QC-033 [ ] Search & Find               │  │ │  │
├── .01 [ ] Full-Text Search           │  │ │  │
├── .02 [ ] Filter by Code             │  │ │  │
├── .03 [ ] Filter by Source           │  │ │  │
├── .04 [ ] Navigate to Result         │  │ │  │
├── .05 [ ] Save Search                │  │ │  │
├── .06 [ ] Semantic Search            │  │ │  │
├── .07 [ ] Find Related Segments      │  │ │  │
└── .08 [ ] Answer Data Questions      │  │ │  │
      depends on: QC-029, 030, 031     │  │ │  │
                                       │  │ │  │
QC-034 [~] Manage Cases                │  │ │  │
├── .01 [~] Create Case                │  │ │  │
├── .02 [~] Link Source to Case        │  │ │  │
├── .03 [~] Add Case Attributes ·······│──│─│──│─╮
├── .04 [~] View Case Data             │  │ │  │ │
├── .05 [~] List All Cases             │  │ │  │ │
├── .06 [~] Suggest Case Groupings     │  │ │  │ │
├── .07 [~] Compare Across Cases       │  │ │  │ │
└── .08 [ ] Case Attribute Detail Panel│  │ │  │ │
      depends on: QC-034.03 ◄──────────│──│─│──│─╯
                                       │  │ │  │
QC-035 [ ] Generate Reports            │  │ │  │
├── .01 [ ] Code Frequencies ··········│──│─│──│──╮
├── .02 [ ] Co-occurrence Matrix       │  │ │  │  │
├── .03 [ ] Export to Spreadsheet      │  │ │  │  │
├── .04 [ ] Visualize Code Distrib.    │  │ │  │  │
├── .05 [ ] Summarize Findings         │  │ │  │  │
├── .06 [ ] Identify Themes            │  │ │  │  │
├── .07 [ ] Generate Insight Report    │  │ │  │  │
└── .08 [ ] Code × Attr Cross-Tab ◄────│──│─│──│──╯
      depends on: QC-029, 030, 031     │  │ │  │
      .08 depends on: 034.03, 035.01   │  │ │  │
                                       │  │ │  │
QC-036 [ ] Collaborate                 │  │ │  │
├── .01 [ ] Switch Coder Identity      │  │ │  │
├── .02 [ ] View Coding by Coder       │  │ │  │
├── .03 [ ] Compare Coders             │  │ │  │
├── .04 [ ] Merge Coding               │  │ │  │
├── .05 [ ] Calculate Reliability      │  │ │  │
├── .06 [ ] Detect Coding Conflicts    │  │ │  │
└── .07 [ ] Suggest Conflict Resoln.   │  │ │  │
      depends on: QC-029, 030, 031     │  │ │  │
                                       │  │ │  │
QC-044 [ ] Visualizations              │  │ │  │
├── .01 [ ] Code Network Graph         │  │ │  │
├── .02 [ ] Code Hierarchy Tree        │  │ │  │
├── .03 [ ] Generate Charts            │  │ │  │
├── .04 [ ] Generate Word Cloud        │  │ │  │
├── .05 [ ] Customize Visualizations   │  │ │  │
├── .06 [ ] Export Visualizations      │  │ │  │
└── .07 [ ] Agent Generate Viz         │  │ │  │
      depends on: QC-029, 030, 031     │  │ │  │
                                       │  │ │  │
QC-037 [ ] Chat with Agent             │  │ │  │
├── .01 [ ] Ask Questions About Data   │  │ │  │
├── .02 [ ] Give Coding Instructions   │  │ │  │
├── .03 [ ] Review Pending Suggestions │  │ │  │
├── .04 [ ] Approve Agent Action       │  │ │  │
├── .05 [ ] Reject Agent Action        │  │ │  │
├── .06 [ ] Execute Multi-Step Task    │  │ │  │
├── .07 [ ] Present Findings Clearly   │  │ │  │
└── .08 [ ] Learn from Feedback        │  │ │  │
      depends on: QC-033, 035, 036     │  │ │  │
                                       │  │ │  │
QC-050 [x] Agent Code Mgmt MCP Tools ◄╯──╯─╯  │
      depends on: QC-028.01, .02, .03          │
                                               │
QC-051 [x] Replication Tests                   │
      depends on: QC-027, 028, 029, 050        │
                                               │
═══ STANDALONE (no cross-deps) ════════════════│═════
                                               │
QC-032 [x] Auto-Code                           │
├── .01-.05 [x] (all done)                     │
├── .06 [ ] Find Similar Passages              │
└── .07 [ ] Batch Apply to Similar             │
                                               │
QC-038 [x] Settings and Preferences            │
├── .01-.05 [ ] (subtasks pending)             │
                                               │
QC-039 [x] Import/Export Formats               │
├── .01-.07 [x] (all done)                     │
                                               │
QC-040 [ ] Data Privacy                        │
├── .01-.05 [ ] (all pending)                  │
                                               │
QC-041 [ ] References & Bibliography           │
├── .01-.04 [ ] (all pending)                  │
                                               │
QC-042 [ ] Apply Codes to PDF                  │
├── .01-.05 [ ] (all pending)                  │
                                               │
QC-043 [ ] Journals and Memos                  │
├── .01-.07 [ ] (all pending)                  │
                                               │
QC-046 [x] Remove v1→v2 Migration Code         │
QC-048 [x] SQLite DB Version Control           │
QC-049 [x] Observability (Logging/OTEL)        │
QC-054 [x] Thread-Safe AI/Human Collab         │
                                               │
═══ INFRA PIPELINE ════════════════════════════╯═════

QC-050 [x] Remove Convex Sync
  │
  ▼
QC-047 [ ] S3 Data Store + DVC
  │
  ▼
QC-051 [ ] Firebase Analytics Import Pipeline


═══ CRITICAL PATH (longest chain) ═══════════════════

QC-045 ──> QC-030/031 ──> QC-033 ──╮
                          QC-035 ──┤──> QC-037 Chat with Agent
                          QC-036 ──╯
```

---

## How to Update This File

1. After E2E tests pass, check which `@allure.story` tags were tested
2. Update the corresponding row in the coverage matrix
3. Add new screenshots to the Image Inventory section
4. Change status emoji as appropriate

### Adding a New Feature

```markdown
| QC-XXX.YY | Feature Name | [page.md](user-manual/page.md) | screenshot-name.png | :white_check_mark: |
```

### Marking as Complete

Change `:x:` or `:construction:` to `:white_check_mark:` when:
- [ ] Feature is tested with `@allure.story`
- [ ] Documentation page exists and is accurate
- [ ] Screenshots are captured and referenced
- [ ] All image files exist in `docs/user-manual/images/`
