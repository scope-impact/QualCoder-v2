# Documentation Coverage Matrix

This file tracks which features have documentation and screenshots.

## Legend

| Status | Meaning |
|--------|---------|
| :white_check_mark: | Documented with screenshots |
| :construction: | Partial documentation |
| :x: | Missing documentation |

---

## Feature Coverage

### QC-027 Manage Sources

| ID | Story | Doc Page | Screenshots | Status |
|----|-------|----------|-------------|--------|
| QC-027.01 | Import Text Document | [sources.md](user-manual/sources.md) | file-manager-empty.png, file-manager-with-sources.png | :white_check_mark: |
| QC-027.02 | Import PDF Document | [sources.md](user-manual/sources.md) | - | :construction: |
| QC-027.03 | Import Image | [sources.md](user-manual/sources.md) | image-viewer.png | :white_check_mark: |
| QC-027.04 | Import Audio/Video | [sources.md](user-manual/sources.md) | media-player.png | :white_check_mark: |

### QC-028 Manage Codes

| ID | Story | Doc Page | Screenshots | Status |
|----|-------|----------|-------------|--------|
| QC-028.01 | Create New Code | [codes.md](user-manual/codes.md) | create-code-dialog.png | :white_check_mark: |
| QC-028.02 | Delete Code | [codes.md](user-manual/codes.md) | delete-code-simple.png, delete-code-warning.png, delete-code-segments-checked.png | :white_check_mark: |
| QC-028.03 | Color Picker | [codes.md](user-manual/codes.md) | color-picker-presets.png, color-picker-custom-hex.png, color-picker-selected.png | :white_check_mark: |
| QC-028.04 | Create Category | [codes.md](user-manual/codes.md) | create-category-initial.png, create-category-name.png, create-category-parent.png, create-category-filled.png | :white_check_mark: |
| QC-028.05 | Find Duplicate Codes | [codes.md](user-manual/codes.md) | duplicate-codes-empty.png, duplicate-codes-list.png, duplicate-codes-similarity.png | :white_check_mark: |

### QC-029 Text Coding

| ID | Story | Doc Page | Screenshots | Status |
|----|-------|----------|-------------|--------|
| QC-029.01 | Quick Mark (Q key) | [coding.md](user-manual/coding.md) | coding-screen-with-codes.png | :white_check_mark: |
| QC-029.02 | Create Code (N key) | [coding.md](user-manual/coding.md) | create-code-dialog.png | :white_check_mark: |
| QC-029.03 | In-Vivo Coding (V key) | [coding.md](user-manual/coding.md) | - | :construction: |
| QC-029.04 | Unmark (U key) | [coding.md](user-manual/coding.md) | - | :construction: |
| QC-029.05 | Text Selection | [coding.md](user-manual/coding.md) | coding-screen-selected.png | :white_check_mark: |
| QC-029.06 | Multiple Codes | [coding.md](user-manual/coding.md) | coding-multiple-codes.png | :white_check_mark: |
| QC-029.07 | Segment Memos | [coding.md](user-manual/coding.md) | memos-panel.png | :white_check_mark: |

### QC-030 AI Features

| ID | Story | Doc Page | Screenshots | Status |
|----|-------|----------|-------------|--------|
| QC-030.01 | Code Suggestions | [ai-features.md](user-manual/ai-features.md) | code-suggestions-empty.png, code-suggestions-list.png, code-suggestions-details.png | :white_check_mark: |
| QC-030.02 | Semantic Search | [ai-features.md](user-manual/ai-features.md) | - | :x: |
| QC-030.03 | Auto-coding | [ai-features.md](user-manual/ai-features.md) | auto-code-pattern.png, auto-code-preview.png | :white_check_mark: |

### QC-034 Cases

| ID | Story | Doc Page | Screenshots | Status |
|----|-------|----------|-------------|--------|
| QC-034.01 | View Cases | [cases.md](user-manual/cases.md) | case-manager-empty.png, case-manager-list.png | :white_check_mark: |
| QC-034.02 | Create Case | [cases.md](user-manual/cases.md) | - | :construction: |
| QC-034.03 | Case Attributes | [cases.md](user-manual/cases.md) | - | :construction: |

### QC-038 Settings

| ID | Story | Doc Page | Screenshots | Status |
|----|-------|----------|-------------|--------|
| QC-038.01 | Theme Settings | [settings.md](user-manual/settings.md) | settings-default-theme.png, settings-dark-theme.png | :white_check_mark: |
| QC-038.02 | Font Settings | [settings.md](user-manual/settings.md) | settings-navigation.png | :white_check_mark: |
| QC-038.03 | All Settings | [settings.md](user-manual/settings.md) | settings-full.png | :white_check_mark: |
| QC-038.04 | MCP Server Settings | [mcp-setup.md](user-manual/mcp-setup.md) | - | :construction: |

### QC-047 Version Control

| ID | Story | Doc Page | Screenshots | Status |
|----|-------|----------|-------------|--------|
| QC-047.01 | Initialize VCS | [version-control.md](user-manual/version-control.md) | - | :construction: |
| QC-047.02 | Auto-commit on Changes | [version-control.md](user-manual/version-control.md) | - | :construction: |
| QC-047.03 | View History | [version-control.md](user-manual/version-control.md) | version-history-screen.png | :white_check_mark: |
| QC-047.04 | Restore Snapshot | [version-control.md](user-manual/version-control.md) | version-history-screen.png | :white_check_mark: |
| QC-047.05 | View Diff | [version-control.md](user-manual/version-control.md) | diff-viewer-dialog.png | :white_check_mark: |
| QC-047.06 | Diff Highlighting | [colors.md](api/tokens/colors.md) | - | :white_check_mark: |

---

## Image Inventory

All images in `docs/user-manual/images/`:

### File Manager
- [x] `file-manager-empty.png`
- [x] `file-manager-with-sources.png`

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
- [x] `version-history-screen.png`
- [x] `diff-viewer-dialog.png`

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
