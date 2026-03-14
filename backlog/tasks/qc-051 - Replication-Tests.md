---
id: QC-051
title: Replication Tests - Validated Research Methodology Workflows
status: Done
assignee: [@myself]
created_date: '2026-03-14'
updated_date: '2026-03-14'
labels: [e2e, cross-cutting, coding, sources, P2]
dependencies: [QC-027, QC-028, QC-029, QC-050]
parent_task_id: ''
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Cross-cutting E2E tests that replicate published qualitative research studies end-to-end. Each test exercises the full coding pipeline (import sources → create codes → apply codes → build themes → audit trail) following real methodology frameworks.

These tests validate that QualCoder v2 can faithfully reproduce established research workflows where AI and human researchers collaborate. Each replication follows a published study's methodology and uses real or realistic transcript data.

**Why separate from feature stories:** Each replication test exercises multiple bounded contexts (sources, coding, categories) and multiple backlog items (QC-027 import, QC-028 codes, QC-029 coding, QC-050 MCP tools) simultaneously. They cannot be mapped to a single feature story without losing their cross-cutting nature.

**Methodology frameworks tested:**
- Braun & Clarke's 6-phase Reflexive Thematic Analysis (RTA)
- Saldana's First/Second Cycle coding methods
- Lincoln & Guba's trustworthiness criteria (audit trail)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 RTA replication: 6-phase Braun & Clarke Reflexive Thematic Analysis with MCP tools (familiarization → initial codes → themes → review → define → audit)
- [x] #2 Sheffield replication: RTA with real Sheffield University ORDA interview transcripts (Ana, David, Jessica)
- [x] #3 ICPC replication: Code review study with published codebook, real transcripts (P5R1, P5R2, P9R1), and theme hierarchy
- [x] #4 All replication tests pass with `make test-all`
<!-- AC:END -->

## Subtasks

| ID | Subtask | Status |
|----|---------|--------|
| QC-051.01 | RTA replication (test_thematic_analysis_replication_e2e.py) | Done |
| QC-051.02 | Sheffield replication (test_sheffield_replication_e2e.py) | Done |
| QC-051.03 | ICPC replication (test_code_review_replication_e2e.py) | Done |

## Implementation

### Test files

```
src/tests/e2e/test_thematic_analysis_replication_e2e.py  # QC-051.01 (was QC-RTA)
src/tests/e2e/test_sheffield_replication_e2e.py          # QC-051.02 (was QC-SHEF)
src/tests/e2e/test_code_review_replication_e2e.py        # QC-051.03 (was QC-ICPC)
```

### Phase-to-feature mapping

Each replication test phase exercises multiple features:

| Phase | Features Exercised | Backlog Items |
|-------|-------------------|---------------|
| Phase 1: Familiarization | Import sources, read content | QC-027.01, QC-027.09 |
| Phase 2: Initial Coding | Create codes, apply to text via MCP | QC-028.01, QC-029.07, QC-050 |
| Phase 3: Searching for Themes | Create categories, move codes | QC-028.02, QC-050.03, QC-050.04 |
| Phase 4-5: Reviewing/Defining | Merge codes, rename, add memos | QC-050.05, QC-050.01, QC-050.02 |
| Phase 6: Audit Trail | List codes, verify segments | QC-028.06, QC-029.04 |

## Methodology Context

These tests serve as acceptance tests for the entire QualCoder v2 platform by replicating real research workflows:

- **RTA (Braun & Clarke, 2006):** The gold-standard thematic analysis framework. Tests all 6 phases with synthetic interview data about remote work experiences.
- **Sheffield (ORDA dataset):** Uses real, publicly available semi-structured interview transcripts about researchers' experiences with open qualitative data.
- **ICPC (code review):** Uses real code review observation transcripts with a published codebook, validating that QualCoder can reproduce a deductive coding study.
