---
id: decision-003
title: Localization Framework Selection
status: Accepted
date: '2026-01-30'
deciders: []
labels:
  - infrastructure
  - i18n
  - architecture
---

## Context

QualCoder v2 requires internationalization (i18n) support to serve a global user base. The application needs to:

1. Display user interface text in multiple languages
2. Support the 9 languages already translated in v1 (de, en, es, fr, it, ja, pt, sv, zh)
3. Allow community contributions of new translations
4. Optionally support runtime language switching (vs restart requirement)

### QualCoder v1 Approach

QualCoder v1 uses a **hybrid localization system**:

| System | Format | Use Case | Files |
|--------|--------|----------|-------|
| GNU gettext | `.po` → `.mo` | Python code strings via `_()` | `{lang}.po`, `locale/{lang}/LC_MESSAGES/{lang}.mo` |
| Qt Linguist | `.ts` → `.qm` | Qt Designer UI widgets | `GUI/app_{lang}.ts`, `locale/{lang}/app_{lang}.qm` |

**Rationale for v1 hybrid:** Qt Designer `.ui` files required Qt Linguist, while Python code used standard gettext.

**v1 Language Switching:** Requires application restart (loads translations at startup in `__main__.py:3300-3353`).

### QualCoder v2 State

- **No Qt Designer files** - All UI is code-only (design system components)
- **PySide6** - Native Qt translation APIs available
- **~100-120 user-facing strings** in presentation layer
- **Design system pattern** - Theme tokens architecture can be replicated for translations

## Decision

**Use Qt Linguist (`.ts`/`.qm`) as the sole localization framework.**

### Evaluation Matrix

| Criteria | Qt Linguist | GNU gettext | Winner |
|----------|-------------|-------------|--------|
| **PySide6 Integration** | Native, built-in | Requires separate setup | Qt Linguist |
| **Tooling** | pyside6-linguist, Qt Linguist app | xgettext, msgfmt, poedit | Tie |
| **Plural Forms** | Native support | Native support | Tie |
| **Context Support** | XML contexts | msgctxt | Tie |
| **Runtime Language Switch** | LanguageChange events | Requires reload | Qt Linguist |
| **v1 Compatibility** | Can convert `.po` → `.ts` | Direct reuse | gettext |
| **Maintenance Burden** | Single system | Hybrid complexity | Qt Linguist |
| **Qt Designer Support** | Yes | No | Qt Linguist |

### Decision Drivers

1. **Single System Simplicity** - v2 has no Qt Designer files, so the primary reason for v1's hybrid approach doesn't apply
2. **Native PySide6 Support** - `QTranslator`, `tr()`, and `LanguageChange` events are first-class citizens
3. **Runtime Language Switching** - Qt's event system enables language changes without restart
4. **Consistent Tooling** - `pyside6-lupdate` and `pyside6-lrelease` integrate with the build pipeline

### Migration from v1 Translations

The `.po` files from v1 can be converted to `.ts` format:

```bash
# Using po2ts from translate-toolkit
po2ts input.po output.ts
```

Alternatively, manual extraction of high-value strings for the ~100 strings in v2.

## Consequences

### Positive

- **Simpler build and maintenance** - Single translation system vs hybrid
- **Better IDE tooling** - Qt Linguist provides visual context for translators
- **Runtime language switch** - Users can change language without restarting
- **Native Qt integration** - No impedance mismatch with PySide6
- **Consistent contributor experience** - One format to learn

### Negative

- **v1 translation migration** - Need to convert `.po` files to `.ts` format
- **Contributor learning curve** - Some contributors familiar with gettext will need to learn Qt Linguist
- **Format lock-in** - Qt Linguist format is less universal than gettext

### Neutral

- **Similar translation platform support** - Both Weblate and Crowdin support `.ts` files
- **Comparable tooling quality** - Qt Linguist is mature, as is gettext ecosystem

## Implementation

### Dependencies

No additional dependencies required - PySide6 includes all necessary modules:

```python
from PySide6.QtCore import QTranslator, QCoreApplication, QLocale
```

### File Structure

```
src/infrastructure/
├── i18n/
│   ├── __init__.py
│   ├── protocols.py          # TranslationService protocol
│   ├── qt_translation.py     # QTranslator implementation
│   └── translations/         # Compiled .qm files
│       ├── qualcoder_de.qm
│       ├── qualcoder_es.qm
│       ├── qualcoder_fr.qm
│       ├── qualcoder_it.qm
│       ├── qualcoder_ja.qm
│       ├── qualcoder_pt.qm
│       ├── qualcoder_sv.qm
│       └── qualcoder_zh.qm
│
translations/                   # Source .ts files (version controlled)
├── qualcoder_de.ts
├── qualcoder_es.ts
├── qualcoder_fr.ts
├── ...
└── qualcoder.pro              # Project file for lupdate
```

### Build Integration

```bash
# Extract strings from source
pyside6-lupdate src/ -ts translations/qualcoder_en.ts

# Compile for release
pyside6-lrelease translations/*.ts -qm src/infrastructure/i18n/translations/
```

### Translation Loading Pattern

```python
from PySide6.QtCore import QTranslator, QCoreApplication, QLocale

class TranslationService:
    def __init__(self, app: QCoreApplication):
        self._app = app
        self._translator = QTranslator()
        self._current_locale = "en"

    def load_language(self, locale_code: str) -> bool:
        """Load translations for the specified locale."""
        path = f":/translations/qualcoder_{locale_code}.qm"
        if self._translator.load(path):
            self._app.installTranslator(self._translator)
            self._current_locale = locale_code
            return True
        return False

    def switch_language(self, locale_code: str) -> bool:
        """Switch language at runtime (triggers LanguageChange events)."""
        self._app.removeTranslator(self._translator)
        return self.load_language(locale_code)
```

### String Marking Convention

```python
# In presentation layer components
from PySide6.QtCore import QCoreApplication

def tr(text: str, context: str = "QualCoder") -> str:
    """Translation wrapper for consistency."""
    return QCoreApplication.translate(context, text)

# Usage in components
label = QLabel(tr("Codes"))
button.setToolTip(tr("Add a new code"))
```

### Related Tasks

- QC-003.03 Localization Analysis (this ADR)
- QC-003.04 Translation Infrastructure (implementation)
- QC-003.05 String Extraction and Initial Translations

## References

- [Qt Internationalization](https://doc.qt.io/qt-6/internationalization.html)
- [PySide6 Translation Tutorial](https://doc.qt.io/qtforpython-6/tutorials/basictutorial/translations.html)
- [pyside6-linguist Tool](https://doc.qt.io/qtforpython-6/tools/pyside-linguist.html)
- [translate-toolkit po2ts](https://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/po2ts.html)
- QualCoder v1 source: `src/qualcoder/__main__.py` (lines 3300-3353)
