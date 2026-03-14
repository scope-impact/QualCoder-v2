# QC-047: S3 Data Store with DVC Versioning — Implementation Plan

## Current State Assessment

The storage bounded context already has **substantial core + infra code** in place:

### Done (core domain + infra)
- **Entities**: `DataStore`, `RemoteFile`, `StoreId` — all complete
- **Events**: `StoreConfigured`, `StoreScanned`, `FilePulled`, `ExportPushed` — complete
- **Failure Events**: `StoreNotConfigured`, `StoreNotScanned`, `FileNotPulled`, `ExportNotPushed` — complete
- **Invariants**: bucket name validation, S3 key validation, store config validation — complete
- **Derivers**: `derive_configure_store`, `derive_scan_store`, `derive_pull_file`, `derive_push_export` — complete
- **Commands**: `ConfigureStoreCommand`, `ScanStoreCommand`, `PullFileCommand`, `PushExportCommand`, `ExportAndPushCommand`, `ScanAndImportCommand` — complete
- **Command Handlers** (6 total): `configure_store`, `scan_store`, `pull_file`, `push_export`, `export_and_push`, `scan_and_import` — all complete
- **Protocols**: `StoreRepository`, `S3ScannerProtocol`, `DvcGatewayProtocol` — complete
- **Infra**: `DvcGateway` (DVC Python API wrapper), `S3Scanner` (boto3 wrapper) — complete
- **Unit Tests**: ~1600 lines covering entities, invariants, derivers, command handlers, S3 scanner, export/push, scan/import
- **E2E Tests**: Full workflow test (configure→scan→pull→push) + offline graceful failure test

### Missing (interface + presentation + wiring)
- **No `store_repository.py`** in infra (persistence layer for `DataStore` config in project DB)
- **No MCP tools** in `interface/` (empty `__init__.py`)
- **No SignalBridge** for storage events
- **No presentation layer** (empty `__init__.py`) — no panel, no viewmodel
- **No wiring in `main.py`** — storage context not registered in `AppContext`
- **No settings UI** for S3/DVC configuration
- **No DVC pipeline template** (`dvc.yaml`)
- **No sub-task files** in backlog

## Implementation Plan

### Phase 1: Infrastructure — Store Repository (AC #1)
**File**: `src/contexts/storage/infra/store_repository.py`

Create a `SqliteStoreRepository` implementing `StoreRepository` protocol:
- `save(store: DataStore)` → INSERT/REPLACE into `data_store` table
- `get() → DataStore | None` → SELECT (singleton per project)
- Schema: `data_store` table with `id, bucket_name, region, prefix, dvc_remote_name, created_at`
- Follows existing repo pattern (e.g., `src/contexts/sources/infra/source_repository.py`)

### Phase 2: Interface — MCP Tools (AC #6)
**Files**:
- `src/contexts/storage/interface/mcp_tools.py` — tool definitions + handlers

Tools to register:
1. `configure_datastore` — configure S3 bucket + DVC remote
2. `scan_datastore` — list files in S3
3. `pull_source` — pull file from S3 to local project
4. `push_results` — push export to S3
5. `export_and_push` — export + push combo
6. `scan_and_import` — pull + auto-import combo

Pattern: Follow `src/contexts/sources/interface/mcp_tools.py`:
- `ToolDefinition` with `ToolParameter` schemas
- `ALL_STORAGE_TOOLS` dict for registration
- Context protocol for accessing repos/gateways
- Wire into `MCPServerManager._get_tool_schemas()` and `_execute_tool()`

### Phase 3: Interface — SignalBridge (AC #1-4 reactive UI)
**File**: `src/contexts/storage/interface/signal_bridge.py`

Create `StorageSignalBridge` following `src/shared/infra/signal_bridge/coding.py`:
- Listens to: `StoreConfigured`, `StoreScanned`, `FilePulled`, `ExportPushed`
- Emits Qt signals for UI updates
- Payload dataclasses: `StorePayload`, `ScanPayload`, `PullPayload`, `PushPayload`

### Phase 4: Presentation — ViewModel + Panel (AC #2, #6)
**Files**:
- `src/contexts/storage/presentation/data_store_viewmodel.py`
- `src/contexts/storage/presentation/data_store_panel.py`

ViewModel:
- `configure(bucket, region, prefix, remote)` → delegates to `configure_store`
- `scan(prefix)` → delegates to `scan_store`
- `pull(key, local_path)` → delegates to `pull_file`
- `push(local_path, dest_key)` → delegates to `push_export`
- Exposes signals: `files_loaded`, `status_changed`

Panel (PySide6):
- File browser tree (populated from scan results)
- Pull/Push buttons
- Status bar (configured/not configured, last sync)

### Phase 5: Settings Integration (AC #1)
**Modify**: `src/contexts/settings/presentation/` (settings dialog)

Add "Data Store" section:
- S3 bucket URL field
- Region dropdown
- DVC remote name
- Test connection button
- "Browse Store" → opens DataStorePanel

### Phase 6: Wiring in main.py
**Modify**: `src/main.py`

- Add storage context to `AppContext`
- Create `SqliteStoreRepository` when project opens
- Wire `StorageSignalBridge` to `EventBus`
- Create `DataStoreViewModel` with repos
- Wire `DataStorePanel` to viewmodel
- Register storage tools in MCP server

### Phase 7: DVC Pipeline Template (AC #7, #9)
**File**: `scripts/dvc_pipeline_template.yaml`

Template `dvc.yaml` for research workflows:
- `aggregate-firebase` stage
- `import-profiles` stage
- `export-results` stage

### Phase 8: E2E Tests (AC #10)
**Modify**: `src/tests/e2e/test_storage_e2e.py`

Add tests for:
- MCP tool calls (configure, scan, pull, push via tool interface)
- Settings UI → configure flow
- DataStorePanel browse/pull/push
- DVC versioning verification (mock)
- Offline mode (no S3 connection)

### Phase 9: Documentation (AC #11)
**Files**: `docs/user-manual/data-store.md`, `docs/api/storage-tools.md`

## Execution Order

1. **Phase 1** (store_repository) — unblocks everything else
2. **Phase 2** (MCP tools) — highest value, enables AI agent workflows
3. **Phase 3** (signal bridge) — needed for reactive UI
4. **Phase 4+5** (presentation + settings) — UI layer
5. **Phase 6** (wiring) — connects all pieces
6. **Phase 7** (DVC template) — standalone artifact
7. **Phase 8+9** (tests + docs) — validation and documentation

## AC Coverage Map

| AC | Description | Phase |
|----|-------------|-------|
| #1 | Configure S3 bucket in Settings | Phase 1, 5, 6 |
| #2 | Scan/browse S3 files | Phase 4 |
| #3 | Pull file from S3 as source | Phase 4 |
| #4 | Push coded exports to S3 | Phase 4 |
| #5 | DVC versioning | Already done (DvcGateway) |
| #6 | MCP tools for AI agents | Phase 2 |
| #7 | DVC pipeline support | Phase 7 |
| #8 | Works offline | Already tested |
