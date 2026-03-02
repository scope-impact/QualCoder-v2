---
id: QC-047
title: Cloud Sync with Convex
status: In Progress
assignee: []
created_date: '2026-02-04 12:00'
updated_date: '2026-02-04 12:00'
labels: [infra, P1]
dependencies: [QC-038]
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Enable optional cloud synchronization for real-time collaboration and backup. All data remains stored locally for offline access, with changes syncing to the cloud when enabled.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Researcher can enable/disable cloud sync in Settings
- [x] #2 Researcher can configure cloud sync connection URL
- [ ] #3 Local changes appear on other connected devices
- [ ] #4 Changes from other devices appear locally
- [ ] #5 App works offline and syncs when reconnected
- [ ] #6 Researcher can see sync connection status
- [ ] #7 Agent can check if cloud sync is active
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
### Completed

**Settings UI** (`src/contexts/settings/presentation/dialogs/settings_dialog.py`):
- Database section with "Enable cloud sync with Convex" checkbox
- Convex URL configuration field (shown when enabled)
- Primary storage always shows "SQLite (Local)"

**Backend Config** (`src/contexts/settings/core/entities.py`):
- `BackendConfig` with `cloud_sync_enabled` and `convex_url`
- `uses_convex` property for checking if sync is active

**Sync Infrastructure** (`src/shared/infra/sync/`):
- `SyncEngine`: Bidirectional sync with outbound queue and inbound subscriptions
- `SyncedRepositories`: Repository wrappers that write to SQLite and queue for Convex

**Convex Schema** (`convex/schema.ts`):
- Tables for all entities: codes, categories, sources, cases, segments, etc.
- Indexes for efficient querying

**Docker Compose** (`docker-compose.yml`):
- Local Convex backend for development/testing
- Dashboard at http://localhost:6791
- Backend at http://127.0.0.1:3210

### Pending

- Wire SyncEngine subscriptions to Convex queries
- Implement conflict resolution strategy
- Add connection status indicator to UI
- E2E tests for sync functionality
- User documentation for cloud sync setup
<!-- SECTION:NOTES:END -->

## Sub-tasks

- [ ] QC-047.01 - Real-time sync to cloud
- [ ] QC-047.02 - Real-time sync from cloud
- [ ] QC-047.03 - Offline queue and reconnection
- [ ] QC-047.04 - Sync status indicator
- [ ] QC-047.05 - Conflict resolution
- [ ] QC-047.06 - E2E tests
- [ ] QC-047.07 - User documentation
