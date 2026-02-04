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
Enable optional cloud synchronization using Convex database. SQLite remains the primary local storage (offline-first), with Convex providing real-time sync for collaboration and backup.

Architecture:
- SQLite: Always primary, works offline
- Convex: Optional cloud sync layer
- SyncEngine: Bidirectional sync between SQLite and Convex
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Researcher can enable/disable cloud sync in Settings > Database
- [x] #2 Researcher can configure Convex deployment URL
- [ ] #3 Local changes sync to Convex in real-time when enabled
- [ ] #4 Remote changes from Convex sync back to local SQLite
- [ ] #5 App works offline with SQLite, syncs when reconnected
- [x] #6 Researcher can test locally using Docker Compose
- [ ] #7 Connection status indicator shows sync state
- [ ] #8 Agent can access cloud sync status via MCP
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

- [ ] QC-047.01 - Wire SyncEngine to Convex subscriptions
- [ ] QC-047.02 - Implement conflict resolution
- [ ] QC-047.03 - Add sync status indicator
- [ ] QC-047.04 - E2E tests for cloud sync
- [ ] QC-047.05 - User documentation
