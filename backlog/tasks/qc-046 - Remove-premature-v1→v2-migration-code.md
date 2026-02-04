---
id: QC-046
title: Remove premature v1→v2 migration code
status: Done
assignee: []
created_date: '2026-02-03 19:42'
labels:
  - infrastructure
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
QualCoder v2 is a fresh rewrite. Migration infrastructure for upgrading v1 databases is premature and adds unnecessary complexity. The migrations folder (src/shared/infra/migrations/) was deleted. When v2 is complete and users need upgrade paths from v1, migration code should be added based on actual requirements.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Delete src/shared/infra/migrations/ folder
- [ ] #2 Verify no code references migrations module
<!-- AC:END -->
