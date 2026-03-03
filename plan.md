# QC-039: Import/Export Formats — Implementation Plan

## Overview

Enable researchers to exchange projects and data with other QDA tools and formats.
This epic covers 7 subtasks (039.01–039.07) plus 3 agent-facing ACs (#8–#10).

**Architecture decision**: Create a new **`exchange`** bounded context (vertical slice)
under `src/contexts/exchange/` rather than scattering import/export logic across
existing contexts. Exchange operations are a distinct concern — they read from
multiple contexts to export, and write to multiple contexts to import.

---

## New Bounded Context: `exchange`

```
src/contexts/exchange/
├── core/
│   ├── __init__.py
│   ├── entities.py            # ExchangeFormat enum, ImportManifest, ExportManifest
│   ├── events.py              # ProjectExported, ProjectImported, CodebookExported, etc.
│   ├── failure_events.py      # ImportFailed, ExportFailed (with error_code + suggestions)
│   ├── invariants.py          # is_valid_qdpx(), is_valid_rqda_db(), is_valid_csv()
│   ├── derivers.py            # derive_import_result(), derive_export_format()
│   └── commandHandlers/
│       ├── __init__.py
│       ├── export_refi_qda.py       # QC-039.01
│       ├── import_refi_qda.py       # QC-039.02
│       ├── import_rqda.py           # QC-039.03
│       ├── export_codebook.py       # QC-039.04
│       ├── export_coded_html.py     # QC-039.05
│       ├── import_survey_csv.py     # QC-039.06
│       └── import_code_list.py      # QC-039.07
├── infra/
│   ├── __init__.py
│   ├── refi_qda_writer.py    # XML generation + ZIP packaging (.qdpx)
│   ├── refi_qda_reader.py    # XML parsing + ZIP extraction
│   ├── rqda_reader.py        # SQLite reader for RQDA databases
│   ├── codebook_writer.py    # ODT/text codebook generator
│   ├── html_writer.py        # HTML export with code highlighting
│   ├── csv_reader.py         # CSV survey data parser
│   └── code_list_reader.py   # Plain text code list parser (indentation → hierarchy)
├── interface/
│   ├── __init__.py
│   ├── mcp_tools.py          # MCP tool definitions for agent access (AC #8–#10)
│   └── signal_bridge.py      # ExchangeSignalBridge (optional progress signals)
└── presentation/
    ├── __init__.py
    ├── viewmodels/
    │   └── exchange_viewmodel.py  # UI state for import/export operations
    ├── dialogs/
    │   ├── export_dialog.py       # Format selection + options
    │   └── import_dialog.py       # File selection + preview + mapping
    └── screens/                   # (Optional, may not need a dedicated screen)
```

---

## Implementation Phases

### Phase 1: Foundation (Core + Infra scaffolding)

**Goal**: Set up the exchange context, entities, events, and wire into AppContext.

#### Step 1.1: Domain entities and types
- `ExchangeFormat` enum: `REFI_QDA`, `RQDA`, `CODEBOOK_ODT`, `CODED_HTML`, `SURVEY_CSV`, `CODE_LIST_TXT`
- `ImportManifest` frozen dataclass: summary of what will be imported (codes, sources, cases counts)
- `ExportManifest` frozen dataclass: summary of what was exported
- Commands: `ExportRefiQdaCommand`, `ImportRefiQdaCommand`, etc.

#### Step 1.2: Domain events
- Success events: `ProjectExported`, `ProjectImported`, `CodebookExported`, `CodedHtmlExported`, `SurveyDataImported`, `CodeListImported`
- Failure events: `ExportFailed`, `ImportFailed` with `error_code` + `suggestions`
- All events follow existing `DomainEvent` base class pattern with `ClassVar[str]` event_type

#### Step 1.3: Wire into AppContext
- Add `ExchangeContext` to `bounded_contexts.py` — holds refs to all context repos (read-only for export, write-through command handlers for import)
- Register in `AppContext` as `exchange_context`
- No new DB tables needed (exchange reads/writes existing tables via existing repos)

---

### Phase 2: Simplest Export First — QC-039.04 Export Codebook

**Rationale**: Codebook export is read-only and the simplest format. Proves the
architecture without touching any import (write) path.

#### Step 2.1: `codebook_writer.py` (infra)
- Read all codes + categories from `CodeRepository` and `CategoryRepository`
- Generate ODT using `python-docx` or plain text/markdown
- Include: code name, color swatch, description/memo, category hierarchy
- Optionally include: memo text

#### Step 2.2: `export_codebook.py` command handler
- Command: `ExportCodebookCommand(output_path: str, include_memos: bool)`
- Load state from repos (codes, categories)
- Call deriver to validate (at least 1 code exists)
- Write via `codebook_writer`
- Publish `CodebookExported` event
- Return `OperationResult` with export manifest

#### Step 2.3: E2E test `test_export_codebook_e2e.py`
- Create codes + categories in test DB
- Export codebook
- Verify file exists and contains expected code names

---

### Phase 3: QC-039.07 Import Code List

**Rationale**: Second simplest — text parsing + writing codes via existing
`create_code` command handler. Validates the import path.

#### Step 3.1: `code_list_reader.py` (infra)
- Parse plain text where each line is a code name
- Indentation (2 or 4 spaces, or tab) creates parent category
- Optional: lines starting with `#` are comments
- Return: list of `(name, parent_category_name, depth)` tuples

#### Step 3.2: `import_code_list.py` command handler
- Command: `ImportCodeListCommand(file_path: str, auto_color: bool)`
- Parse file via reader
- For each category level: call `create_category` command handler
- For each code: call `create_code` command handler
- Auto-assign colors from a palette if `auto_color=True`
- Publish `CodeListImported` event with count
- Return `OperationResult`

#### Step 3.3: E2E test

---

### Phase 4: QC-039.06 Import Survey CSV

#### Step 4.1: `csv_reader.py` (infra)
- Read CSV with headers
- First column = case identifier (maps to Case.name)
- Other columns = attributes (auto-detect type: text/number/date/boolean)
- Return: list of `(case_name, attributes_dict)` tuples

#### Step 4.2: `import_survey_csv.py` command handler
- Command: `ImportSurveyCommand(file_path: str, case_column: str)`
- Parse CSV
- For each row: create/update case via `create_case` + `set_attribute` command handlers
- Publish `SurveyDataImported` event
- Return `OperationResult` with import manifest

#### Step 4.3: E2E test

---

### Phase 5: QC-039.05 Export Coded Text as HTML

#### Step 5.1: `html_writer.py` (infra)
- Read source text + segments + codes
- Generate HTML with:
  - Inline `<span>` tags with code color as background
  - CSS for code legend
  - Tooltip showing code name on hover
  - Media links as `<a>` tags
- Self-contained HTML file (embedded CSS, no external deps)

#### Step 5.2: `export_coded_html.py` command handler
- Command: `ExportCodedHtmlCommand(source_ids: list[str], output_path: str)`
- Load sources, segments, codes
- Generate HTML via writer
- Publish `CodedHtmlExported` event
- Return `OperationResult`

#### Step 5.3: E2E test

---

### Phase 6: QC-039.01 Export REFI-QDA Project

**REFI-QDA format summary**:
- `.qdpx` file = ZIP archive containing:
  - `project.qde` — XML file following REFI-QDA 1.0 schema
  - `sources/` — source files (text, media)
- XML structure:
  - `<Project>` root element
  - `<Users>` / `<User>`
  - `<CodeBook>` / `<Codes>` / `<Code>` (nested for hierarchy)
  - `<Sources>` / `<TextSource>` / `<PDFSource>` / etc.
  - `<Cases>` / `<Case>` with variable refs
  - `<Sets>` for groupings
  - `<Coding>` elements linking codes to source positions

#### Step 6.1: `refi_qda_writer.py` (infra)
- Build XML tree using `xml.etree.ElementTree` (stdlib)
- Map QualCoder entities → REFI-QDA XML elements:
  - `Code` → `<Code>` with `guid`, `name`, `color` (as `isCodable="true"`)
  - `Category` → nested `<Code isCodable="false">` (REFI-QDA uses Code for both)
  - `TextSegment` → `<Coding>` with `<CodeRef>` and text range
  - `Source` → `<TextSource>` with `<PlainTextContent>` or file reference
  - `Case` → `<Case>` with `<VariableRef>` for attributes
- Package into ZIP as `.qdpx`

#### Step 6.2: `export_refi_qda.py` command handler
- Command: `ExportRefiQdaCommand(output_path: str, include_sources: bool)`
- Load ALL project data from all repos
- Generate via writer
- Publish `ProjectExported` event
- Return `OperationResult`

#### Step 6.3: E2E test — round-trip validation

---

### Phase 7: QC-039.02 Import REFI-QDA Project

#### Step 7.1: `refi_qda_reader.py` (infra)
- Extract ZIP
- Parse `project.qde` XML
- Map REFI-QDA elements → QualCoder domain commands:
  - `<Code isCodable="true">` → `CreateCodeCommand`
  - `<Code isCodable="false">` → `CreateCategoryCommand`
  - `<TextSource>` → `ImportFileSourceCommand` or `AddTextSourceCommand`
  - `<Coding>` → `ApplyCodeCommand`
  - `<Case>` → `CreateCaseCommand` + `SetAttributeCommand`
- Return: list of commands to execute (preview/dry-run capability)

#### Step 7.2: `import_refi_qda.py` command handler
- Command: `ImportRefiQdaCommand(file_path: str, merge_strategy: str)`
  - `merge_strategy`: "replace" | "merge" | "skip_duplicates"
- Parse QDPX via reader
- Execute commands in dependency order:
  1. Categories (parent-first)
  2. Codes (with category refs)
  3. Sources (extract files)
  4. Segments/Codings
  5. Cases + attributes
- All via existing command handlers (ensures events are published → UI updates)
- Publish `ProjectImported` event
- Return `OperationResult` with import manifest

#### Step 7.3: E2E test — import a test .qdpx fixture, verify data

---

### Phase 8: QC-039.03 Import RQDA Project

#### Step 8.1: `rqda_reader.py` (infra)
- RQDA uses SQLite database with tables:
  - `source` — text documents
  - `coding` — code applications (start/end positions)
  - `freecode` — code definitions
  - `codecat` — code categories
  - `caselinkage` — case-source links
  - `cases` — case definitions
  - `attributes` — case attributes
- Read via `sqlite3` module (stdlib)
- Map to QualCoder domain commands (same pattern as REFI-QDA)

#### Step 8.2: `import_rqda.py` command handler
- Command: `ImportRqdaCommand(file_path: str)`
- Parse RQDA DB via reader
- Execute domain commands in order
- Publish `ProjectImported` event
- Return `OperationResult`

#### Step 8.3: E2E test

---

### Phase 9: MCP Tools for Agent Access (AC #8–#10)

#### Step 9.1: MCP tool definitions (`mcp_tools.py`)
- `suggest_export_format` — AC #8: given use case description, recommend format
- `export_data` — AC #9: export in requested format
- `import_from_text` — AC #10: import code list or data from text

#### Step 9.2: MCP handlers
- All handlers delegate to command handlers (standard pattern)
- `suggest_export_format` is a query (pure logic, no side effects)
- `export_data` calls appropriate export command handler
- `import_from_text` creates temp file, calls appropriate import command handler

#### Step 9.3: Register in `MCPServerManager`

---

### Phase 10: Presentation Layer (UI)

#### Step 10.1: Import/Export dialogs
- `ExportDialog`: format dropdown, options checkboxes, output path picker
- `ImportDialog`: file picker, format auto-detection, preview panel, merge strategy

#### Step 10.2: Wire into AppShell
- Add "Import/Export" to menu or as toolbar actions
- Wire to `ExchangeViewModel`
- Connect to existing signal bridges for progress updates

#### Step 10.3: ViewModel
- `ExchangeViewModel` with methods:
  - `export(format, options)` → delegates to command handler
  - `import_file(path)` → auto-detect format, show preview, delegate
  - `get_supported_formats()` → read-only query

---

## Dependency Order (Build Sequence)

```
Phase 1 (Foundation)
  └─> Phase 2 (Export Codebook) — simplest, proves read path
  └─> Phase 3 (Import Code List) — simplest import, proves write path
  └─> Phase 4 (Import Survey CSV) — validates case import path
  └─> Phase 5 (Export Coded HTML) — richer export with segments
  └─> Phase 6 (Export REFI-QDA) — complex export, full project
  └─> Phase 7 (Import REFI-QDA) — complex import, full project
  └─> Phase 8 (Import RQDA) — variant of Phase 7
  └─> Phase 9 (MCP Tools) — wraps all above for agents
  └─> Phase 10 (UI) — presentation layer, can parallelize with 6-9
```

## Cross-Cutting Concerns

### Import Strategy: Reuse Existing Command Handlers
**Critical**: Import operations MUST go through existing command handlers
(`create_code`, `create_category`, `apply_code`, etc.) rather than writing
directly to repos. This ensures:
1. Domain validation (invariants) is applied
2. Events are published → UI updates via SignalBridge
3. Undo/rollback support via `OperationResult.rollback_command`
4. Consistent behavior between human UI, AI agent, and import

### Error Handling
- Partial import failures return `OperationResult` with:
  - `data`: successfully imported items
  - `error`: description of failures
  - `suggestions`: recovery actions
- File format validation in invariants (pure functions)
- I/O errors caught in command handlers, wrapped in `OperationResult`

### Testing
- Each phase includes E2E tests with Allure stories
- Test fixtures: sample QDPX, RQDA, CSV, and text files in `src/tests/e2e/fixtures/`
- Round-trip test: export → import → verify identical data

### Dependencies (Python packages)
- `xml.etree.ElementTree` (stdlib) for XML
- `python-docx` for ODT codebook export (optional, could use plain text first)
- `zipfile` (stdlib) for QDPX packaging
- `csv` (stdlib) for survey data
- `sqlite3` (stdlib) for RQDA import

## Files to Modify (Existing)

| File | Change |
|------|--------|
| `src/shared/infra/app_context/bounded_contexts.py` | Add `ExchangeContext` |
| `src/shared/infra/app_context/context.py` | Add `exchange_context` attribute |
| `src/shared/infra/app_context/factory.py` | Create `ExchangeContext` |
| `src/shared/infra/mcp_server.py` | Register exchange MCP tools |
| `src/main.py` | Add import/export menu items, wire viewmodel |
| `pyproject.toml` | Add `python-docx` dependency (if ODT) |
