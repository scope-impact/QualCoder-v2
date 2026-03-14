---
id: QC-051
title: Firebase Analytics Import Pipeline
status: To Do
assignee: []
created_date: '2026-03-13'
updated_date: '2026-03-13'
labels: [infrastructure, application, cases, sources, exchange, P1, feature]
dependencies: [QC-047]
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Enable importing Firebase Analytics data into QualCoder for mixed-methods triangulation. Researchers collect behavioral data (Firebase events) alongside qualitative data (interview transcripts). This feature bridges the gap by:

1. **Aggregating** raw Firebase event data into per-participant profiles
2. **Importing** those profiles as Case attributes (engagement_tier, sessions_per_week, etc.)
3. **Linking** cases to transcript sources for cross-tabulation of codes × behavioral segments

Supports the triangulation workflow: Firebase (what users DO) + Transcripts (what users SAY) + Coded themes (what it MEANS).

**Data flow:** S3 (raw Firebase export) → DVC pull → aggregate script → import as Case attributes → link to transcripts → code → cross-tab by Firebase segments.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Researcher can import Firebase BigQuery export (JSON) as aggregated Case attributes
- [ ] #2 Researcher can import pre-aggregated Firebase CSV (one row per participant)
- [ ] #3 Import auto-detects attribute types (NUMBER for metrics, TEXT for segments, DATE for timestamps)
- [ ] #4 Import maps Firebase user_id to Case name (configurable ID column)
- [ ] #5 Import merges with existing Cases (updates attributes, doesn't create duplicates)
- [ ] #6 Researcher can preview data before importing (column mapping UI)
- [ ] #7 Agent can import Firebase data and link to transcript sources via MCP tools
- [ ] #8 Aggregation script template provided for BigQuery → participant profile CSV
- [ ] #9 DVC pipeline stage template for Firebase → QualCoder workflow
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
### Three Import Modes

**Mode 1: Pre-aggregated CSV** (simplest, extends existing `import_survey_csv`)
```
name,sessions_per_week,avg_session_sec,engagement_tier,top_feature,active_days
user_042,12,340,power_user,export,28
user_043,2,120,casual,search,5
```
- Enhance `import_survey_csv` to auto-detect NUMBER/DATE types (currently all TEXT)
- Add merge behavior: update existing case attributes instead of failing on duplicate names

**Mode 2: Firebase BigQuery JSON export**
```json
{"user_id": "abc", "event_name": "screen_view", "event_timestamp": "2026-03-10T...", ...}
{"user_id": "abc", "event_name": "feature_used", "event_params": {"feature": "export"}, ...}
```
- New parser: `firebase_parser.py` in exchange/infra/
- Aggregates raw events per user_id into summary metrics
- Configurable aggregation rules (count, avg, max, first/last, categorical)

**Mode 3: Firebase BigQuery SQL → CSV** (template only)
- Provide a SQL template that researchers run in BigQuery console
- Output is Mode 1 CSV — no parsing needed in QualCoder

### New/Modified Files

```
# New
src/contexts/exchange/infra/firebase_parser.py          # Parse + aggregate Firebase JSON
src/contexts/exchange/core/commandHandlers/import_firebase.py  # Firebase-specific import
scripts/aggregate_firebase.sql                           # BigQuery template
scripts/aggregate_firebase.py                            # Python aggregation script

# Modified
src/contexts/exchange/core/commandHandlers/import_survey_csv.py  # Add type detection, merge
src/contexts/exchange/infra/csv_parser.py                # Add type inference
src/contexts/exchange/interface/mcp_tools.py             # Add import_firebase tool
src/contexts/exchange/core/commands.py                   # ImportFirebaseCommand
```

### Type Detection Logic

```python
def infer_attribute_type(values: list[str]) -> str:
    """Infer CaseAttribute type from sample values."""
    if all(is_numeric(v) for v in values if v):
        return "NUMBER"
    if all(is_date(v) for v in values if v):
        return "DATE"
    if all(v.lower() in ("true", "false") for v in values if v):
        return "BOOLEAN"
    return "TEXT"
```

### Merge Behavior

When importing and a Case with the same name already exists:
- UPDATE existing attributes (overwrite with new values)
- ADD new attributes that didn't exist before
- PRESERVE attributes not in the import (don't delete)
- Publish `CaseAttributeSet` events for each change

### Triangulation Query Support

After import, the existing MCP tools enable triangulation:
- `suggest_case_groupings(attribute_names=["engagement_tier"])` → group cases by Firebase segment
- `compare_cases(case_ids=[...], code_ids=[...])` → compare coded themes across segments
- Cross-tab: codes × engagement_tier → convergence/divergence matrix

### DVC Pipeline Stage

```yaml
# Add to dvc.yaml
stages:
  aggregate-firebase:
    cmd: python scripts/aggregate_firebase.py raw/firebase_export.json processed/profiles.csv
    deps: [raw/firebase_export.json, scripts/aggregate_firebase.py]
    outs: [processed/profiles.csv]
```
<!-- SECTION:NOTES:END -->

## Sub-tasks

- [ ] QC-051.01 - Enhance CSV import: type detection and case merge behavior
- [ ] QC-051.02 - Firebase BigQuery JSON parser and aggregator
- [ ] QC-051.03 - ImportFirebaseCommand handler
- [ ] QC-051.04 - Column mapping preview UI
- [ ] QC-051.05 - MCP tool: import_firebase
- [ ] QC-051.06 - BigQuery SQL template and Python aggregation script
- [ ] QC-051.07 - DVC pipeline stage template
- [ ] QC-051.08 - E2E tests
- [ ] QC-051.09 - User documentation: Firebase triangulation workflow
