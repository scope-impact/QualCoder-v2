# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for QualCoder v2.

ADRs capture significant technical decisions: what was decided, why, and what the consequences are. They are immutable once accepted — superseded decisions get a new ADR rather than editing the old one.

## Format

Each ADR follows the [Michael Nygard format](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions):
- **Context** — the situation forcing a decision
- **Decision** — what was decided
- **Consequences** — trade-offs, positive and negative

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](ADR-001-uuidv7-primary-keys.md) | UUIDv7 as Primary Keys for All Entities | Accepted |
| [ADR-002](ADR-002-sync-engine-pattern.md) | Transactional Outbox + Cursor Pull + LWW as Sync Engine Pattern | Accepted |
