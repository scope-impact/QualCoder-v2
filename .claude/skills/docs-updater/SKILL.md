---
name: docs-updater
description: |
  Update user documentation and screenshots after Allure E2E tests pass.
  Keeps docs in sync with tested features.

  **Invoke when:**
  - After E2E tests pass and need documentation updates
  - Capturing UI screenshots for user manual
  - Cross-referencing test coverage with documentation
  - Updating feature descriptions after implementation

  **Provides:**
  - Screenshot capture workflow
  - Doc-to-test mapping (QC-XXX → doc pages)
  - Documentation update checklist
  - Missing documentation detection
---

# QualCoder v2 Documentation Updater

## Quick Reference

### Documentation Structure

| Directory | Purpose |
|-----------|---------|
| `docs/user-manual/` | End-user documentation |
| `docs/user-manual/images/` | Screenshots for manual |
| `docs/api/` | MCP tool API documentation |
| `docs/api/components/` | Component API reference |

### Doc-to-Feature Mapping

| Feature (Allure Story) | Doc Page | Image Pattern |
|------------------------|----------|---------------|
| QC-027 Manage Sources | sources.md | file-manager-*.png |
| QC-028 Manage Codes | codes.md | create-code-*.png, color-picker-*.png |
| QC-029 Text Coding | coding.md | coding-screen-*.png |
| QC-030 AI Features | ai-features.md | code-suggestions-*.png |

---

## Workflow

### Step 1: Verify Tests Pass

```bash
# Run all E2E tests
QT_QPA_PLATFORM=offscreen make test-all

# Check Allure report
allure serve allure-results/

# List tested features
grep -rh "@allure.story.*QC-" src/tests/e2e/*.py | sort -u
```

### Step 2: Capture Screenshots

Use the `DocScreenshot` utility in E2E tests:

```python
from src.tests.e2e.utils.doc_screenshot import DocScreenshot

class TestCreateCodeDialog:
    def test_dialog_appearance(self, coding_screen):
        # Open dialog
        coding_screen._on_new_code_shortcut()
        dialog = coding_screen._current_dialog

        # Capture for docs
        DocScreenshot.capture(dialog, "create-code-dialog")

        dialog.close()
```

**Naming Convention:**
- `{feature}-{state}.png`
- Examples: `create-code-dialog.png`, `coding-screen-with-codes.png`

### Step 3: Update Documentation

For each passed test story, update the corresponding doc:

1. **Check screenshot references** - ensure images exist
2. **Update feature description** - match tested behavior
3. **Add keyboard shortcuts** - from E2E test assertions
4. **Update workflow diagrams** - if flow changed

### Step 4: Documentation Checklist

Before marking docs complete:

- [ ] All referenced images exist in `docs/user-manual/images/`
- [ ] Image captions describe what user sees
- [ ] Keyboard shortcuts match actual implementation
- [ ] Workflow matches E2E test steps
- [ ] Links to related pages work

---

## Screenshot Capture Utility

The `DocScreenshot` class provides consistent screenshot capture:

```python
from src.tests.e2e.utils.doc_screenshot import DocScreenshot

# Basic capture
DocScreenshot.capture(widget, "feature-name")

# Capture with Allure attachment
DocScreenshot.capture(widget, "feature-name", attach_to_allure=True)

# Capture only if image doesn't exist (avoid overwriting)
DocScreenshot.capture_if_missing(widget, "feature-name")
```

### Screenshot Guidelines

| State | Suffix | Example |
|-------|--------|---------|
| Empty/initial | `-empty` | `file-manager-empty.png` |
| With data | `-with-{data}` | `coding-screen-with-codes.png` |
| Selected state | `-selected` | `coding-screen-selected.png` |
| Dialog open | `-dialog` | `create-code-dialog.png` |
| Error state | `-error` | `import-error.png` |

---

## Missing Documentation Detection

### Find untested features

```bash
# Get all tested features
grep -rh "@allure.story" src/tests/e2e/*.py | \
  sed 's/.*"\(QC-[0-9]*\.[0-9]*\).*/\1/' | sort -u

# Compare with DOC_COVERAGE.md
cat docs/DOC_COVERAGE.md | grep "QC-" | awk '{print $2}'
```

### Find missing images

```bash
# Check all image references in docs
for doc in docs/user-manual/*.md; do
  echo "=== $doc ==="
  grep -o 'images/[^)]*' "$doc" | while read img; do
    [ ! -f "docs/user-manual/$img" ] && echo "MISSING: $img"
  done
done
```

### Automated check script

```bash
# Run from project root
make docs-check
```

---

## Update Workflow

### After tests pass

1. **Check coverage matrix**
   ```bash
   cat docs/DOC_COVERAGE.md
   ```

2. **Identify docs to update**
   - Look at which QC-XXX tests passed
   - Find corresponding doc page in mapping

3. **Update documentation**
   ```bash
   # Edit the relevant doc
   vim docs/user-manual/coding.md
   ```

4. **Verify images**
   ```bash
   # Check referenced images exist
   grep -o 'images/[^)]*' docs/user-manual/coding.md | \
     xargs -I {} test -f "docs/user-manual/{}" || echo "Missing: {}"
   ```

5. **Update coverage matrix**
   ```bash
   vim docs/DOC_COVERAGE.md
   # Mark feature as documented
   ```

6. **Commit changes**
   ```bash
   git add docs/
   git commit -m "docs(user-manual): update after QC-XXX tests pass"
   ```

---

## Integration with Definition of Done

From CLAUDE.md, documentation is required for Definition of Done:

> 4. User documentation updated in `docs/user-manual/`
> 5. API documentation updated in `docs/api/` for MCP tools

### Checklist per feature

- [ ] E2E test passes with `@allure.story("QC-XXX.YY")`
- [ ] Screenshots captured during test run
- [ ] User manual page updated
- [ ] API docs updated (if MCP tool)
- [ ] DOC_COVERAGE.md updated
- [ ] All image references valid

---

## Quick Commands

```bash
# Capture all screenshots (re-run screenshot tests)
QT_QPA_PLATFORM=offscreen uv run pytest src/tests/e2e/ -k "capture" -v

# Check doc coverage
make docs-check

# Serve docs locally (if using mkdocs)
mkdocs serve

# Build docs
mkdocs build
```

---

## Troubleshooting

### Screenshots look different on CI

- Use `QT_QPA_PLATFORM=offscreen` for consistent rendering
- Set fixed widget sizes before capture
- Use `QApplication.processEvents()` before grabbing

### Image too large

```python
# Scale down for docs
pixmap = widget.grab()
scaled = pixmap.scaled(800, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation)
scaled.save(path)
```

### Dark mode issues

- Capture in both light and dark mode if needed
- Name: `feature-light.png`, `feature-dark.png`
