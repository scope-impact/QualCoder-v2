---
id: QC-047
title: S3 Data Store with DVC Versioning
status: To Do
assignee: []
created_date: '2026-02-04 12:00'
updated_date: '2026-03-13'
labels: [infra, infrastructure, sources, P1, feature]
dependencies: [QC-050]
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Enable S3 as an external data store for research data (Firebase exports, transcripts, media files) with DVC (Data Version Control) for versioning and sync. Replaces the previous Convex cloud sync approach with a research-data-native architecture.

**Why S3 + DVC instead of Convex:**
- Research datasets are large (Firebase exports, media, transcripts) — S3 is purpose-built for blob storage
- DVC provides reproducible data versioning tied to git commits — critical for research audit trails
- Explicit pull/push workflow matches research methodology (deliberate, not real-time)
- Team collaboration via `dvc pull` — no proprietary sync service required
- Supports mixed-methods triangulation: quantitative data (Firebase) alongside qualitative data (transcripts)

**New bounded context:** `storage` — manages external data stores, scanning, pulling, and pushing research data.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Researcher can configure an S3 bucket as a data store in Settings
- [ ] #2 Researcher can scan/browse available files in the S3 data store
- [ ] #3 Researcher can pull a file from S3 into the local project as a source
- [ ] #4 Researcher can push coded exports (codebook, segments CSV, QDPX) back to S3
- [ ] #5 All data transfers are versioned via DVC (hash-tracked, reproducible)
- [ ] #6 Agent can scan data store, pull sources, and push exports via MCP tools
- [ ] #7 DVC pipeline support: aggregate → import → code → export stages
- [ ] #8 Works offline — S3 interaction only on explicit pull/push
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
### Architecture: New `storage` Bounded Context

```
src/contexts/storage/
├── core/
│   ├── entities.py           # DataStore, RemoteFile, SyncManifest
│   ├── events.py             # StoreConfigured, FileDiscovered, FilePulled, ExportPushed
│   ├── invariants.py         # Valid S3 config, valid DVC workspace
│   └── commandHandlers/
│       ├── configure_store.py    # Set S3 bucket + DVC remote
│       ├── scan_store.py         # List files in S3 via DVC
│       ├── pull_file.py          # DVC pull → local → import_file_source
│       └── push_export.py        # Export → DVC push to S3
├── infra/
│   ├── dvc_adapter.py        # Wraps DVC CLI (pull, push, list, status)
│   ├── s3_scanner.py         # Direct boto3 listing for discovery
│   └── store_repository.py   # Persists DataStore config in project DB
├── interface/
│   ├── mcp_tools.py          # scan_datastore, pull_source, push_results
│   └── signal_bridge.py      # StorePayload signals for UI updates
└── presentation/
    ├── data_store_panel.py   # Browse S3 files, pull/push buttons
    └── data_store_viewmodel.py
```

### DVC Adapter (core infrastructure)

```python
class DVCAdapter:
    """Wraps DVC CLI for S3 data versioning."""

    def pull(self, path: str) -> OperationResult:
        """Pull specific file/dir from S3 remote to local."""

    def push(self, path: str) -> OperationResult:
        """Push local file/dir to S3 remote."""

    def list_remote(self, prefix: str = "") -> OperationResult:
        """List files in S3 remote via DVC."""

    def status(self) -> OperationResult:
        """Check sync status between local and remote."""
```

### Data Flow

```
Scan:   MCP/UI → scan_store → DVCAdapter.list_remote() → file list
Pull:   MCP/UI → pull_file → DVCAdapter.pull() → import_file_source (existing)
Push:   MCP/UI → push_export → export_codebook/refi_qda → DVCAdapter.push()
```

### DVC Pipeline Integration (dvc.yaml)

```yaml
stages:
  aggregate-firebase:
    cmd: python scripts/aggregate_firebase.py
    deps: [raw/firebase_export.json]
    outs: [processed/participant_profiles.csv]

  import-profiles:
    cmd: qualcoder import-csv processed/participant_profiles.csv
    deps: [processed/participant_profiles.csv]

  export-results:
    cmd: qualcoder export coded/
    outs: [coded/codebook.txt, coded/segments.csv]
```

### Settings Integration

Add to Settings dialog (replaces removed Convex section):
- "Data Store" section
- S3 bucket URL field
- DVC remote name (default: "origin")
- Test connection button
- Browse button → opens DataStorePanel
<!-- SECTION:NOTES:END -->

## Sub-tasks

- [ ] QC-047.01 - Domain: DataStore entities, events, invariants
- [ ] QC-047.02 - Infrastructure: DVC adapter (pull, push, list, status)
- [ ] QC-047.03 - Infrastructure: S3 scanner (boto3 discovery)
- [ ] QC-047.04 - Infrastructure: Store repository (config persistence)
- [ ] QC-047.05 - Application: configure_store, scan_store, pull_file, push_export handlers
- [ ] QC-047.06 - Interface: MCP tools (scan_datastore, pull_source, push_results)
- [ ] QC-047.07 - Presentation: Settings UI for S3/DVC config
- [ ] QC-047.08 - Presentation: DataStorePanel (browse, pull, push)
- [ ] QC-047.09 - DVC pipeline template (dvc.yaml for research workflows)
- [ ] QC-047.10 - E2E tests
- [ ] QC-047.11 - User documentation
