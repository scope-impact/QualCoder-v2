---
id: QC-049
title: 'Observability: Structured Logging and OTEL Metrics'
status: Done
assignee: []
created_date: '2026-03-02 07:53'
updated_date: '2026-03-02 09:37'
labels:
  - infrastructure
  - P2
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add structured logging and OpenTelemetry metrics instrumentation across the codebase for monitoring, debugging, and performance analysis. Covers async flow paths, sync engine, MCP server, and repository operations.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Structured logging configured with consistent format across all bounded contexts
- [x] #2 OTEL metrics instrumented for key operations (MCP tool calls, sync events, repository operations)
- [x] #3 Logging levels configurable via settings or environment
- [x] #4 Exploratory test validates logging output and metric collection
- [x] #5 User documentation for enabling/configuring observability
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
### Completed (on convex-with-git-sqlite branch)

**Structured Logging** (`src/shared/infra/logging_config.py`):
- Consistent JSON-structured logging format
- Per-module loggers across bounded contexts
- Async flow path logging in sync engine, MCP server, repositories

**OTEL Metrics** (`src/shared/infra/metrics.py`):
- Counters and histograms for MCP tool calls, sync events, repo operations
- Telemetry helper in `src/shared/infra/telemetry.py`

**Exploratory Test** (`src/tests/exploratory_observability.py`):
- 494-line test validating logging output and OTEL metric collection

### Pending
- AC #3: Logging level configuration via settings/env not fully wired
- AC #5: No user documentation yet for enabling/configuring observability
- No `@allure.story("QC-049")` decorators on tests

### AC #3 & AC #5 Completed (commits fe1f1e5a, 14f62158)

**AC #3 – Configurable Logging:**
- ObservabilityConfig entity with log_level, enable_file_logging, enable_telemetry
- Full DDD stack: entity → command → deriver → handler → repository serialization
- Settings Dialog Observability section with log level dropdown + checkboxes
- QUALCODER_LOG_LEVEL env var override (highest priority)
- Startup wiring in main.py reads saved settings

**AC #5 – User Documentation:**
- docs/user-manual/observability.md covering log levels, file logging, telemetry, troubleshooting
- Linked from docs/user-manual/index.md
- Coverage rows added to docs/DOC_COVERAGE.md

**E2E Tests** (src/tests/e2e/test_observability_settings_e2e.py):
- 15 tests with @allure.story(QC-049) decorators
- Covers UI persistence, env var override, file logging integration, round-trip, docs existence

All 5 acceptance criteria complete.
<!-- SECTION:NOTES:END -->
