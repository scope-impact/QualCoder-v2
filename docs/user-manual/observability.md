# Observability — Logging & Telemetry

QualCoder v2 includes structured logging and OpenTelemetry (OTEL) metrics to help you diagnose issues, monitor performance, and understand application behaviour.

## Overview

| Feature | What it provides |
|---------|-----------------|
| Structured logging | Timestamped, levelled log messages for every bounded context |
| File logging | Persistent log output saved to disk |
| OTEL metrics | Operation latency, event counts, and resource usage metrics |

All logging follows the naming hierarchy `qualcoder.<context>.<layer>`, for example `qualcoder.coding.core` or `qualcoder.sources.infra`.

## Configuring Log Levels

### Via Settings UI

1. Open **Settings** (gear icon in the sidebar).
2. Select **Observability** in the left navigation.
3. Choose a log level from the dropdown:

| Level | When to use |
|-------|-------------|
| **DEBUG** | Troubleshooting — shows detailed internal operations |
| **INFO** | Normal usage (default) — shows key actions and results |
| **WARNING** | Quiet mode — only unexpected situations |
| **ERROR** | Minimal — only failures |

Changes to the log level take effect immediately.

### Via Environment Variable

Set the `QUALCODER_LOG_LEVEL` environment variable to override the UI setting. This is useful for debugging without changing saved preferences.

```bash
# macOS / Linux
export QUALCODER_LOG_LEVEL=DEBUG
uv run python -m src.main

# Windows PowerShell
$env:QUALCODER_LOG_LEVEL = "DEBUG"
uv run python -m src.main
```

The environment variable takes highest priority — it overrides both the saved setting and the `QUALCODER_DEV` flag.

## File Logging

When **Enable file logging** is checked in Settings > Observability, log output is also written to:

```
~/.qualcoder/qualcoder.log
```

The file uses the same structured format as console output:

```
14:32:05.123 INFO  [qualcoder.coding.core] Code created: id=abc123
14:32:05.456 DEBUG [qualcoder.sources.infra] Source loaded: name=interview_01.txt
```

File logging changes require an application restart to take effect.

## Telemetry / Metrics

When **Enable telemetry metrics** is checked (enabled by default), QualCoder collects OTEL metrics locally:

```
~/.qualcoder/telemetry.jsonl
```

Metrics include:
- Operation latency (how long commands take)
- Event throughput (events published per interval)
- Error rates by bounded context

All telemetry data stays on your machine. No data is sent to external services.

Telemetry changes require an application restart to take effect.

## Troubleshooting

### Logs are too noisy

Set the log level to **WARNING** or **ERROR** to reduce output. Only unexpected situations and failures will be logged.

### Need detailed logs for a bug report

1. Set `QUALCODER_LOG_LEVEL=DEBUG` in your environment.
2. Enable file logging in Settings > Observability.
3. Reproduce the issue.
4. Attach `~/.qualcoder/qualcoder.log` to your bug report.

### Log level setting is ignored

The `QUALCODER_LOG_LEVEL` environment variable overrides the UI setting. Check if it is set:

```bash
echo $QUALCODER_LOG_LEVEL
```

Unset it to use the UI-configured value:

```bash
unset QUALCODER_LOG_LEVEL
```
