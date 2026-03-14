# QC-051: Firebase Analytics Import Pipeline — Implementation Plan

## Research Summary

### Firebase/GA4 BigQuery Export Schema
Firebase Analytics exports to BigQuery as daily `events_YYYYMMDD` tables. Each row is a single event with:
- **`user_pseudo_id`** — Auto-generated device-scoped user ID
- **`user_id`** — Optional developer-set user ID
- **`event_name`** — e.g. `session_start`, `screen_view`, `first_open`, `purchase`
- **`event_timestamp`** — Microseconds since epoch
- **`event_params`** — Nested RECORD of key-value pairs (`key`, `string_value`, `int_value`, `double_value`, `float_value`)
- **`user_properties`** — Nested RECORD of user-scoped key-value pairs
- **`device`** — Nested: `category`, `mobile_brand_name`, `model_name`, `operating_system`, `language`
- **`geo`** — Nested: `country`, `region`, `city`
- **`traffic_source`** — Nested: `name`, `medium`, `source`
- **`platform`** — `ANDROID`, `IOS`, `WEB`
- **`user_first_touch_timestamp`**, **`user_ltv`** (revenue, currency)

### Export Formats Researchers Will Have
1. **BigQuery JSON export** — NDJSON with nested `event_params` (needs aggregation)
2. **Pre-aggregated CSV** — Already one-row-per-participant (simplest path)
3. **BigQuery SQL → CSV** — Researcher runs SQL in BigQuery console, downloads CSV

### Existing Codebase Patterns
- **CSV import**: `parse_survey_csv()` → `import_survey_csv()` handler → creates `Case` entities with `CaseAttribute(attr_type=TEXT)` for all columns
- **Key gap**: All attributes hardcoded to `AttributeType.TEXT` — no type inference
- **Key gap**: No merge/upsert — creates new cases, fails silently on duplicates
- **Coordinator pattern**: `ExchangeCoordinator` wraps handlers with repo references
- **MCP pattern**: `ExchangeTools` delegates to coordinator methods
- **Event pattern**: Success events (e.g. `SurveyCSVImported`) and `ImportFailed` failure events

Sources:
- [BigQuery Export Schema](https://support.google.com/analytics/answer/7029846?hl=en)
- [Firebase BigQuery Export Docs](https://firebase.google.com/docs/projects/bigquery-export)
- [Basic Queries for GA4 BigQuery](https://developers.google.com/analytics/bigquery/basic-queries)
- [Advanced Queries for GA4 BigQuery](https://developers.google.com/analytics/bigquery/advanced-queries)
- [GA4 Audience Queries](https://support.google.com/firebase/answer/9037342?hl=en)

---

## Implementation Plan (9 slices, ordered by dependency)

### Slice 1: Type Inference for CSV Parser
**Files:** `src/contexts/exchange/infra/csv_parser.py`

Add a pure function `infer_attribute_type(values: list[str]) -> AttributeType` that samples column values and returns the best-fit type:
- All numeric → `NUMBER`
- All ISO date-like → `DATE`
- All true/false → `BOOLEAN`
- Otherwise → `TEXT`

Add `infer_column_types(parse_result: CSVParseResult) -> dict[str, AttributeType]` that runs inference across all rows per column.

**Tests:** Unit tests for type inference (int, float, dates, booleans, mixed, empty).

### Slice 2: Case Merge Behavior in CSV Import
**Files:** `src/contexts/exchange/core/commandHandlers/import_survey_csv.py`

Modify `import_survey_csv()` to:
1. Call `infer_column_types()` on parsed CSV to get typed attributes
2. Before creating a new Case, check `case_repo.get_by_name(case_name)` for existing case
3. If exists: update attributes (overwrite existing, add new, preserve others) via `case_repo.save_attribute()`
4. If not: create new Case as before, but with inferred types
5. Track `cases_created` vs `cases_updated` counts in the event

**Requires:** Add `get_by_name(name: str) -> Case | None` to `CaseRepository` if not present.

**Update events:** Modify `SurveyCSVImported` to include `cases_updated: int` field.

### Slice 3: Firebase JSON Parser
**Files (new):** `src/contexts/exchange/infra/firebase_parser.py`

Parse Firebase BigQuery NDJSON export format:
- `parse_firebase_export(text: str) -> FirebaseParseResult`
- Handle two formats: `{"events": [...]}` (wrapped) and NDJSON (one event per line)
- Extract `user_pseudo_id` / `user_id` as participant identifier
- Flatten `event_params` nested records into simple key-value pairs
- Aggregate per user:
  - `session_count` — count of `session_start` events
  - `total_events` — count of all events
  - `first_seen` / `last_seen` — min/max `event_timestamp`
  - `top_event` — most frequent event_name (excluding session_start)
  - `platform`, `country` — most common value from device/geo
- Return `FirebaseParseResult(participants: list[dict], columns: list[str])`

Configurable aggregation: allow caller to specify which aggregations to compute via an `AggregationConfig` dataclass.

**Tests:** Unit tests with sample Firebase JSON fixtures.

### Slice 4: ImportFirebaseCommand and Handler
**Files:**
- `src/contexts/exchange/core/commands.py` — Add `ImportFirebaseCommand`
- `src/contexts/exchange/core/commandHandlers/import_firebase.py` — New handler
- `src/contexts/exchange/core/events.py` — Add `FirebaseImported` event
- `src/contexts/exchange/core/failure_events.py` — Add Firebase-specific failures

`ImportFirebaseCommand` fields:
```python
@dataclass(frozen=True)
class ImportFirebaseCommand:
    source_path: str
    id_column: str = "user_pseudo_id"  # configurable ID mapping
    merge: bool = True  # merge with existing cases
```

Handler `import_firebase()`:
1. Read file, detect format (JSON vs CSV)
2. If JSON → use `parse_firebase_export()` to aggregate
3. If CSV → use existing `parse_survey_csv()` with type inference
4. For each participant row: create/merge Case with typed attributes
5. Publish `FirebaseImported` event

**Failure events:**
- `ImportFailed.firebase_invalid_json(path)`
- `ImportFailed.firebase_no_events(path)`
- `ImportFailed.firebase_missing_user_id(path, id_column)`

### Slice 5: Wire into Coordinator and MCP Tools
**Files:**
- `src/contexts/exchange/presentation/coordinator.py` — Add `import_firebase()` method
- `src/contexts/exchange/interface/mcp_tools.py` — Add `import_firebase` tool + update `import_data`

Coordinator addition:
```python
def import_firebase(self, command: ImportFirebaseCommand) -> OperationResult:
    from src.contexts.exchange.core.commandHandlers.import_firebase import import_firebase
    return import_firebase(
        command=command,
        case_repo=self._case_repo,
        event_bus=self._event_bus,
        session=self._session,
    )
```

MCP tool: Add `"import_firebase"` to `EXCHANGE_TOOLS` with parameters:
- `source_path` (required) — Path to Firebase export file (JSON or CSV)
- `id_column` (optional, default `"user_pseudo_id"`) — Column to map to case names
- `merge` (optional, default `true`) — Whether to merge with existing cases

Also update `import_data` to accept `format="firebase"`.

### Slice 6: BigQuery SQL Template
**Files (new):** `scripts/aggregate_firebase.sql`

Ready-to-use BigQuery SQL template:
```sql
SELECT
  user_pseudo_id AS participant_id,
  COUNT(DISTINCT (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')) AS sessions,
  COUNT(*) AS total_events,
  MIN(event_timestamp) AS first_seen,
  MAX(event_timestamp) AS last_seen,
  APPROX_TOP_COUNT(event_name, 1)[OFFSET(0)].value AS top_event,
  APPROX_TOP_COUNT(geo.country, 1)[OFFSET(0)].value AS country,
  APPROX_TOP_COUNT(device.category, 1)[OFFSET(0)].value AS device_category
FROM `YOUR_DATASET.events_*`
WHERE _TABLE_SUFFIX BETWEEN 'YYYYMMDD' AND 'YYYYMMDD'
GROUP BY user_pseudo_id
ORDER BY sessions DESC
```

### Slice 7: Update Python Aggregation Script
**Files:** `scripts/aggregate_firebase.py`

Enhance the existing starter script:
- Support both wrapped JSON (`{"events": [...]}`) and NDJSON formats
- Add `--id-column` flag (default: `user_pseudo_id`)
- Add `first_seen`, `last_seen`, `top_event`, `platform`, `country` columns
- Handle `event_params` flattening (nested params → flat key-value)
- Add engagement tier customization via `--tiers` flag

### Slice 8: DVC Pipeline Stage Template
**Files:** `scripts/dvc_pipeline_template.yaml` (append Firebase stage)

```yaml
stages:
  aggregate-firebase:
    cmd: python scripts/aggregate_firebase.py --input raw/firebase_export.json --output processed/profiles.csv
    deps:
      - raw/firebase_export.json
      - scripts/aggregate_firebase.py
    outs:
      - processed/profiles.csv
```

### Slice 9: E2E Tests
**Files (new):** `src/tests/e2e/test_firebase_import_e2e.py`

Test cases with `@allure.story("QC-051.XX ...")` decorators:

1. **AC #1**: Import Firebase BigQuery JSON → aggregated Case attributes
   - Fixture: sample Firebase NDJSON with 3 users, mixed events
   - Assert: Cases created with correct typed attributes (NUMBER for sessions, TEXT for tier)

2. **AC #2**: Import pre-aggregated CSV → Case attributes with type inference
   - Fixture: CSV with numeric/text/date columns
   - Assert: Attributes have correct inferred types (not all TEXT)

3. **AC #3**: Type auto-detection works correctly
   - Assert: NUMBER for "12", DATE for "2026-01-15", BOOLEAN for "true", TEXT for "hello"

4. **AC #4**: Configurable ID column mapping
   - Import with `id_column="custom_id"` → cases named from that column

5. **AC #5**: Merge with existing cases
   - Create cases first, then import → attributes updated, no duplicates, existing attrs preserved

6. **AC #7**: MCP tool `import_firebase` works end-to-end
   - Call via ExchangeTools.execute() → verify result

**Fixture files (new):** `src/tests/e2e/fixtures/firebase/`
- `sample_export.json` — 3 users, ~20 events each
- `pre_aggregated.csv` — 5 users with mixed-type columns

---

## Dependency Graph

```
Slice 1 (type inference) ──┐
                            ├──→ Slice 2 (merge behavior) ──┐
Slice 3 (firebase parser) ──┤                                ├──→ Slice 4 (handler) ──→ Slice 5 (coordinator + MCP)
                            │                                │
                            └────────────────────────────────┘

Slice 6 (SQL template) ─────── independent, can parallel with 1-3
Slice 7 (Python script) ─────── depends on Slice 3 patterns
Slice 8 (DVC template) ──────── independent, can parallel
Slice 9 (E2E tests) ─────────── depends on Slices 1-5
```

## Out of Scope (deferred)
- **Column mapping preview UI** (QC-051.04) — Presentation layer, deferred to separate PR
- **User documentation** (QC-051.09) — After E2E tests pass, use `docs-updater` skill
- **Storage context integration** — QC-047 dependency for DVC pull → auto-import flow
