# QC-047: Next Phase — Presentation + Settings + Wiring

## Status Summary

### Completed (Phases 1-3, 8-9)
- **Core domain**: Entities, events, invariants, derivers, 6 command handlers
- **Infrastructure**: SqliteStoreRepository, DvcGateway, S3Scanner
- **Interface**: 6 MCP tools, StorageSignalBridge
- **E2E tests**: 9 tests passing (repository, MCP tools, full workflow, wiring)
- **Documentation**: User manual + API docs

### Remaining (Phases 4-7)
- **Phase 4**: DataStoreViewModel + Import from S3 Dialog (presentation layer)
- **Phase 5**: Settings dialog integration (Data Store tab)
- **Phase 6**: Wiring in main.py + FileManager toolbar integration
- **Phase 7**: DVC pipeline template

### UI Decision (resolved)
**Import from S3 = Modal dialog**, not a standalone panel or tab.
- Triggered by `[Import from S3]` button in FileManager toolbar
- Same UX pattern as `[Import Files]` (opens QFileDialog) but for S3
- No layout changes to FileManager — just one new toolbar button
- Pull = download from S3 + auto-import via `import_file_source()`
- Already-imported files shown greyed out with `●` status

---

## Phase 4: Presentation — ViewModel + Panel

### 4A: DataStoreViewModel
**File**: `src/contexts/storage/presentation/data_store_viewmodel.py`

Follow pattern from `src/contexts/settings/presentation/viewmodels/settings_viewmodel.py`.

```
DataStoreViewModel
├── Properties (reactive via signals)
│   ├── is_configured: bool
│   ├── bucket_name: str
│   ├── files: list[RemoteFile]
│   ├── status_message: str
│   └── is_loading: bool
│
├── Actions (delegate to command handlers)
│   ├── configure(bucket, region, prefix, remote) → OperationResult
│   ├── scan(prefix="") → OperationResult
│   ├── pull(key, local_path) → OperationResult
│   └── push(local_path, dest_key) → OperationResult
│
├── Signals (Qt)
│   ├── files_changed()         # after scan completes
│   ├── status_changed(str)     # status bar updates
│   ├── configuration_changed() # after configure
│   └── operation_failed(str)   # error display
│
└── Dependencies
    ├── store_repo: StoreRepository
    ├── s3_scanner: S3ScannerProtocol
    ├── dvc_gateway: DvcGatewayProtocol
    ├── event_bus: EventBus
    └── signal_bridge: StorageSignalBridge
```

Key behaviors:
- On init, load existing config from `store_repo.get()`
- Connect to `StorageSignalBridge` signals to update state reactively
- All actions are non-blocking (run in QThread or ThreadPool)

### 4B: ImportFromS3Dialog (Modal)
**File**: `src/contexts/storage/presentation/dialogs/import_from_s3_dialog.py`

Triggered by `[Import from S3]` button in FileManager toolbar.
Uses `design_system.modal.Modal` — same pattern as import progress modal.

```
┌─ Import from Data Store ──────────────────────────────┐
│                                                        │
│ S3: my-bucket/project-alpha/            [Refresh]     │
│                                                        │
│ +==+========================+==========+==============+│
│ |  | Name                   | Size     | Status       |│
│ +--+------------------------+----------+--------------+│
│ |x | interview_02.txt       | 12 KB    |  remote      |│
│ |x | field_notes.pdf        | 45 KB    |  remote      |│
│ |  | notes_draft.docx       | 8 KB     |  remote      |│
│ |  | interview_01.txt       | 23 KB    |  imported    |│
│ |  | survey.pdf             | 2.1 MB   |  imported    |│
│ +==+========================+==========+==============+│
│                                                        │
│                        [Cancel]  [Pull 2 Selected]    │
└────────────────────────────────────────────────────────┘
```

Widget structure:
- **Header**: Shows current S3 prefix + [Refresh] button
- **File table**: QTableWidget with checkbox column
  - Columns: Checkbox, Name, Size, Status
  - `remote` = available to pull (checkable)
  - `imported` = already in Sources (greyed out, not checkable)
  - Status determined by cross-referencing S3 files with source_repo
- **Action buttons**: Cancel + Pull Selected (count updates dynamically)

Flow:
1. Dialog opens → calls `scan_store` to list S3 files
2. Cross-references with `source_repo` to mark already-imported files
3. User checks files to pull
4. Click "Pull Selected" → for each file:
   a. Download from S3 via `pull_file` command handler
   b. Auto-import via `import_file_source` command handler
   c. Update status to `imported` in dialog
5. Dialog closes → FileManager reloads via `sources_changed` signal

Follows design_system tokens (SPACING, RADIUS, TYPOGRAPHY, ColorPalette).

### 4C: E2E Tests for Presentation
**Add to**: `src/tests/e2e/test_storage_e2e.py`

```python
@allure.story("QC-047.08 Import from S3 Dialog")
class TestImportFromS3Dialog:
    def test_dialog_shows_remote_files_after_scan(self)
    def test_already_imported_files_greyed_out(self)
    def test_pull_selected_downloads_and_imports(self)
    def test_status_updates_to_imported_after_pull(self)
    def test_cancel_closes_dialog(self)
```

---

## Phase 5: Settings Integration

### 5A: Add "Data Store" Tab to Settings Dialog
**Modify**: `src/contexts/settings/presentation/dialogs/settings_dialog.py`

Add new nav item "Data Store" to the QListWidget sidebar:
```
| Appearance |
| Language   |
| Backup     |
| AV Coding  |
| Data Store |  <-- new
```

Stacked page content:
```
+----------------------------------------------+
| S3 Configuration                             |
|                                              |
| Bucket Name:  [________________________]     |
| Region:       [us-east-1            v]       |
| Path Prefix:  [________________________]     |
| DVC Remote:   [origin_______________]        |
|                                              |
| [Test Connection]     Status: Not configured |
+----------------------------------------------+
```

- [Test Connection] → calls `s3_scanner.list_files()` with limit=1
- Apply/OK → calls `configure_store` command handler
- No "Browse" button here — browsing happens via FileManager toolbar

### 5B: SettingsViewModel Extension
**Modify**: `src/contexts/settings/presentation/viewmodels/settings_viewmodel.py`

Add data store settings to the viewmodel:
- `data_store_bucket: str`
- `data_store_region: str`
- `data_store_prefix: str`
- `data_store_remote: str`
- `save_data_store_settings()` → delegates to `configure_store`
- `test_connection()` → async check via S3Scanner

### 5C: E2E Tests for Settings
**Add to**: `src/tests/e2e/test_storage_e2e.py`

```python
@allure.story("QC-047.07 Settings Data Store Configuration")
class TestSettingsDataStore:
    def test_settings_shows_data_store_tab(self)
    def test_configure_from_settings_dialog(self)
    def test_test_connection_button(self)
```

---

## Phase 6: Wiring in main.py + FileManager Integration

### 6A: DataStoreViewModel Wiring
**Modify**: `src/main.py` → `_wire_viewmodels()`

```python
def _wire_viewmodels(self):
    # ... existing wiring ...

    # Storage: DataStoreViewModel
    data_store_vm = DataStoreViewModel(
        store_repo=self._ctx.storage_context.store_repo,
        source_repo=self._ctx.sources_context.source_repo,  # for cross-referencing
        s3_scanner=self._ctx.storage_context.s3_scanner,
        dvc_gateway=self._ctx.storage_context.dvc_gateway,
        event_bus=self._ctx.event_bus,
        signal_bridge=self._storage_signal_bridge,
    )
    # Wire to FileManagerScreen (provides the dialog's viewmodel)
    self._screens["file_manager"].set_data_store_viewmodel(data_store_vm)
```

### 6B: FileManager Toolbar Integration
**Modify**: `src/contexts/sources/presentation/screens/file_manager.py`

Add `[Import from S3]` button to toolbar (next to existing `[Import Files]`):
- Button only enabled when Data Store is configured (`data_store_vm.is_configured`)
- Click → opens `ImportFromS3Dialog` modal
- Dialog receives `DataStoreViewModel` for S3 operations
- On pull completion → `import_file_source()` auto-imports → `sources_changed` signal fires

```python
def _on_import_from_s3_clicked(self):
    dialog = ImportFromS3Dialog(
        viewmodel=self._data_store_vm,
        colors=self._colors,
        parent=self,
    )
    dialog.exec()
```

**Modify**: `src/shared/presentation/organisms/file_manager_toolbar.py`
- Add `import_from_s3_clicked` signal
- Add `[Import from S3]` button after `[Import Files]`

---

## Phase 7: DVC Pipeline Template

**File**: `scripts/dvc_pipeline_template.yaml`

```yaml
# Template dvc.yaml for mixed-methods research workflow
# Copy to project root and customize

stages:
  aggregate-firebase:
    cmd: python scripts/aggregate_firebase.py
    deps:
      - raw/firebase_export.json
    outs:
      - processed/participant_profiles.csv

  import-profiles:
    cmd: qualcoder import-csv processed/participant_profiles.csv
    deps:
      - processed/participant_profiles.csv

  export-results:
    cmd: qualcoder export coded/
    outs:
      - coded/codebook.txt
      - coded/segments.csv
```

Also create `scripts/aggregate_firebase.py` as a starter script.

---

## Execution Order

```
Phase 4A → 4B → 5A → 5B → 6A → 6B → 4C+5C → 7
  |         |     |     |    |     |     |       |
  VM     Dialog  Sett  SVM  Wire  Toolbar Tests Template
```

All phases can be committed incrementally. Tests (4C, 5C) run after wiring (6B) since they need the full stack.

## Sub-task Updates (for backlog)

After completion, mark these sub-tasks done:
- [x] QC-047.07 - Presentation: Settings UI for S3/DVC config
- [x] QC-047.08 - Presentation: Import from S3 dialog (browse, pull + auto-import)
- [x] QC-047.09 - DVC pipeline template

## Screenshots Needed (for DOC_COVERAGE)

After UI is built, capture:
- `import-from-s3-dialog.png` — modal with file list, checkboxes, status
- `data-store-settings.png` — settings dialog Data Store tab
- `import-from-s3-pulling.png` — dialog during pull (progress indicator)
