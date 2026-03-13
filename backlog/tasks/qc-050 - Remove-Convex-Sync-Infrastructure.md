---
id: QC-050
title: Remove Convex Sync Infrastructure
status: To Do
assignee: []
created_date: '2026-03-13'
updated_date: '2026-03-13'
labels: [infrastructure, refactor, P1, tech-debt]
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Convex cloud sync is being replaced by S3 + DVC for data storage and versioning (see QC-047 rewrite). Remove all Convex-specific infrastructure, schemas, and dependencies from the codebase. This is a prerequisite for the new storage context architecture.

QualCoder v2's sync story shifts from real-time cloud database sync (Convex) to explicit research-data-native storage (S3 + DVC) — better suited for large datasets (Firebase exports, transcripts, media) and reproducible research workflows.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Remove `src/shared/infra/convex/` (ConvexClient)
- [ ] #2 Remove `src/shared/infra/sync/` (SyncEngine, outbox, id_map)
- [ ] #3 Remove `src/shared/core/sync/` (sync entities, events, derivers, invariants, commands)
- [ ] #4 Remove `src/shared/infra/app_context/sync_context.py`
- [ ] #5 Remove `src/shared/infra/signal_bridge/sync.py`
- [ ] #6 Remove `src/shared/presentation/molecules/sync_status_button.py`
- [ ] #7 Remove `src/contexts/cases/infra/convex_repository.py`
- [ ] #8 Remove `src/contexts/settings/interface/cloud_sync_mcp_tools.py`
- [ ] #9 Remove `convex/` directory (schema.ts, all table files, tsconfig)
- [ ] #10 Remove `docker-compose.yml` Convex backend service (if only used for Convex)
- [ ] #11 Remove cloud sync UI from Settings dialog (checkbox, URL field)
- [ ] #12 Remove `BackendConfig.cloud_sync_enabled` and `convex_url` from settings entities
- [ ] #13 Remove `src/tests/e2e/test_cloud_sync_e2e.py`
- [ ] #14 Remove Convex dependencies from `pyproject.toml` / `requirements.txt`
- [ ] #15 No remaining references to "convex" or "cloud_sync" in codebase (grep clean)
- [ ] #16 All existing tests pass after removal (`make test-all`)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
### Files to Remove

```
# Convex client
src/shared/infra/convex/

# Sync engine & infrastructure
src/shared/infra/sync/
src/shared/infra/app_context/sync_context.py
src/shared/infra/signal_bridge/sync.py

# Sync domain
src/shared/core/sync/

# UI
src/shared/presentation/molecules/sync_status_button.py

# Context-specific Convex adapters
src/contexts/cases/infra/convex_repository.py
src/contexts/settings/interface/cloud_sync_mcp_tools.py

# Tests
src/tests/e2e/test_cloud_sync_e2e.py

# Convex backend
convex/
docker-compose.yml (review — may have other services)
```

### Files to Edit

- `src/contexts/settings/core/entities.py` — Remove `BackendConfig`, `cloud_sync_enabled`, `convex_url`, `uses_convex`
- `src/contexts/settings/presentation/dialogs/settings_dialog.py` — Remove cloud sync UI section
- `src/shared/infra/app_context/context.py` — Remove SyncContext creation, Convex client wiring
- Any `__init__.py` files that re-export sync/convex modules
- `pyproject.toml` / `requirements.txt` — Remove convex SDK dependency
- `docs/ARCHITECTURE.md` — Remove Convex references
- `docs/decisions/ADR-002-sync-engine-pattern.md` — Mark as superseded

### Approach

1. Remove files bottom-up (leaf dependencies first)
2. Fix imports and references
3. Run `make test-all` to verify nothing breaks
4. Grep for any remaining "convex", "cloud_sync", "SyncEngine" references
<!-- SECTION:NOTES:END -->

## Sub-tasks

- [ ] QC-050.01 - Remove Convex backend (`convex/`, docker-compose)
- [ ] QC-050.02 - Remove sync infrastructure (`src/shared/infra/sync/`, `src/shared/core/sync/`)
- [ ] QC-050.03 - Remove Convex client and context-specific adapters
- [ ] QC-050.04 - Remove cloud sync UI and settings
- [ ] QC-050.05 - Clean up dependencies and documentation
- [ ] QC-050.06 - Verify all tests pass
