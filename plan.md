# QC-047: Next Phase — Presentation + Settings + Wiring

## Status Summary

### Completed (Phases 1-3, 8-9)
- **Core domain**: Entities, events, invariants, derivers, 6 command handlers
- **Infrastructure**: SqliteStoreRepository, DvcGateway, S3Scanner
- **Interface**: 6 MCP tools, StorageSignalBridge
- **E2E tests**: 9 tests passing (repository, MCP tools, full workflow, wiring)
- **Documentation**: User manual + API docs

### Remaining (Phases 4-7)
- **Phase 4**: DataStoreViewModel + DataStorePanel (presentation layer)
- **Phase 5**: Settings dialog integration (Data Store tab)
- **Phase 6**: Wiring in main.py (ViewModel → Screen binding)
- **Phase 7**: DVC pipeline template

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

### 4B: DataStorePanel
**File**: `src/contexts/storage/presentation/data_store_panel.py`

```
┌─────────────────────────────────────────────────────────┐
│ Data Store                                              │
├─────────────────────────────────────────────────────────┤
│ ⚙ Bucket: my-research-bucket  Region: us-east-1        │
│   Prefix: project-alpha/       [Configure...]           │
├─────────────────────────────────────────────────────────┤
│ 📁 Remote Files                           [↻ Scan]     │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 📄 raw/firebase_export.json     1.2 MB   [↓ Pull]  │ │
│ │ 📄 raw/transcripts/p01.txt      45 KB    [↓ Pull]  │ │
│ │ 📄 raw/transcripts/p02.txt      52 KB    [↓ Pull]  │ │
│ │ 📄 processed/profiles.csv       12 KB    [↓ Pull]  │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ 📤 Push Export                                          │
│ Format: [Codebook ▼]  Dest: exports/   [↑ Push]        │
├─────────────────────────────────────────────────────────┤
│ Status: Connected — 4 files available                   │
└─────────────────────────────────────────────────────────┘
```

Widget structure:
- **Config bar**: Shows current config, [Configure...] button opens settings
- **File tree**: QTreeWidget populated from scan results
  - Columns: Name, Size, Last Modified
  - Per-row [Pull] button
- **Push section**: Export format dropdown + destination + [Push] button
- **Status bar**: Connection state + last operation result

Follows design_system tokens (SPACING, RADIUS, TYPOGRAPHY, ColorPalette).

### 4C: E2E Tests for Presentation
**Add to**: `src/tests/e2e/test_storage_e2e.py`

```python
@allure.story("QC-047.08 Data Store Panel")
class TestDataStorePanel:
    def test_panel_shows_not_configured_initially(self)
    def test_panel_shows_files_after_scan(self)
    def test_pull_button_triggers_pull(self)
    def test_push_button_triggers_push(self)
    def test_status_updates_on_operations(self)
```

---

## Phase 5: Settings Integration

### 5A: Add "Data Store" Tab to Settings Dialog
**Modify**: `src/contexts/settings/presentation/dialogs/settings_dialog.py`

Add new nav item "Data Store" to the QListWidget sidebar:
```
│ Appearance │
│ Language   │
│ Backup     │
│ AV Coding  │
│ Data Store │  ← new
```

Stacked page content:
```
┌──────────────────────────────────────────────┐
│ S3 Configuration                             │
│                                              │
│ Bucket Name:  [________________________]     │
│ Region:       [us-east-1            ▼]       │
│ Path Prefix:  [________________________]     │
│ DVC Remote:   [origin_______________]        │
│                                              │
│ [Test Connection]     Status: Not configured │
│                                              │
│ [Browse Data Store...]                       │
└──────────────────────────────────────────────┘
```

- [Test Connection] → calls `s3_scanner.list_files()` with limit=1
- [Browse Data Store...] → opens DataStorePanel (or navigates to it)
- Apply/OK → calls `configure_store` command handler

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

## Phase 6: Wiring in main.py

**Modify**: `src/main.py` → `_wire_viewmodels()`

```python
def _wire_viewmodels(self):
    # ... existing wiring ...

    # Storage: DataStoreViewModel
    data_store_vm = DataStoreViewModel(
        store_repo=self._ctx.storage_context.store_repo,
        s3_scanner=self._ctx.storage_context.s3_scanner,
        dvc_gateway=self._ctx.storage_context.dvc_gateway,
        event_bus=self._ctx.event_bus,
        signal_bridge=self._storage_signal_bridge,
    )
    # Wire to DataStorePanel (if embedded in main window)
    # OR wire to Settings dialog as a sub-component
```

Decision: DataStorePanel can be either:
- **Option A**: Standalone panel in main window (like FileManager, TextCoding)
- **Option B**: Embedded in Settings dialog only (accessed via Settings → Data Store → Browse)

Recommend **Option A** for discoverability — researchers need quick access to pull/push.

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
Phase 4A → 4B → 5A → 5B → 6 → 4C+5C → 7
  │         │     │     │    │    │        │
  VM      Panel  Dialog  VM  Wire Tests  Template
```

All phases can be committed incrementally. Tests (4C, 5C) run after wiring (6) since they need the full stack.

## Sub-task Updates (for backlog)

After completion, mark these sub-tasks done:
- [x] QC-047.07 - Presentation: Settings UI for S3/DVC config
- [x] QC-047.08 - Presentation: DataStorePanel (browse, pull, push)
- [x] QC-047.09 - DVC pipeline template

## Screenshots Needed (for DOC_COVERAGE)

After UI is built, capture:
- `data-store-panel.png` — main panel with file list
- `data-store-settings.png` — settings dialog Data Store tab
- `data-store-pull.png` — after pulling a file (status update)
