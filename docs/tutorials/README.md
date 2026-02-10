# Onboarding Tutorial: QualCoder v2 fDDD Architecture

Welcome to the QualCoder v2 architecture tutorial! This hands-on guide teaches you the **Functional Domain-Driven Design (fDDD)** patterns through a practical example: adding a "priority" field to Codes.

## Prerequisites

- Python 3.10+ familiarity
- Basic understanding of classes and dataclasses
- No prior DDD or functional programming experience required

## Learning Path

Work through these parts in order. Each builds on the previous.

| Part | Topic | What You'll Learn |
|------|-------|-------------------|
| [Part 0](./00-big-picture.md) | The Big Picture | Why this architecture exists |
| [Part 1](./01-first-invariant.md) | Your First Invariant | Write a pure validation function |
| [Part 2](./02-first-deriver.md) | Your First Deriver | Compose invariants into events |
| [Part 3](./03-result-type.md) | The Result Type | Why `Success \| Failure` beats exceptions |
| [Part 4](./04-event-flow.md) | Events Flow Through | Trace events from domain to UI |
| [Part 5](./05-signal-bridge.md) | SignalBridge Payloads | Connect domain to PySide6 |
| [Part 6](./06-testing.md) | Testing Without Mocks | Appreciate pure function testability |
| [Part 7](./07-complete-flow.md) | Complete Flow Reference | Full diagram of Code creation |

## Appendices

| Appendix | Topic |
|----------|-------|
| [Appendix A](./appendices/A-common-patterns.md) | Common Patterns & Recipes |
| [Appendix B](./appendices/B-when-to-create.md) | When to Create New Patterns |

## The Toy Example: Adding Priority to Codes

Throughout this tutorial, we use one consistent example: adding an optional "priority" field (1-5) to Codes. This simple feature touches every layer of the architecture:

```
Priority: Optional[int]  # 1 (low) to 5 (high), or None
```

You'll learn:
- How to validate priority with a pure **Invariant**
- How to integrate validation into a **Deriver**
- How events carry the new field through the system
- How the UI receives updates via **SignalBridge**

## How to Use This Tutorial

1. **Read with the codebase open** - Reference the actual files as you go
2. **Follow along** - The code snippets show patterns, not copy-paste solutions
3. **Experiment** - Try modifying examples to solidify understanding

## Architecture Overview

```mermaid
graph LR
    subgraph Domain ["Domain (Pure)"]
        I[Invariants] --> D[Derivers]
        D --> E[Events]
    end

    subgraph Application ["Application (Orchestration)"]
        CH[CommandHandlers]
        EB[EventBus]
        SB[SignalBridge]
    end

    subgraph Presentation ["Presentation"]
        VM[ViewModel]
        MCP[MCP Tools]
        W[Qt Widgets]
    end

    VM --> CH
    MCP --> CH
    CH --> D
    CH --> EB --> SB --> W
```

**Key Insight**: ViewModels and MCP Tools both call the same CommandHandlers, ensuring consistent behavior for human and AI consumers.

## Key Files Reference

As you work through the tutorial, you'll reference these files:

```
src/contexts/coding/core/
├── invariants.py          # Pure validation functions (is_*, can_*)
├── derivers.py            # Event derivation (derive_*)
├── events.py              # Success events (CodeCreated, etc.)
├── failure_events.py      # Failure events (CodeNotCreated, etc.)
├── entities.py            # Code, Category, Segment entities
├── commands.py            # Command dataclasses
├── commandHandlers/       # Use cases (orchestration)
│   ├── create_code.py     # create_code() command handler
│   ├── rename_code.py     # rename_code() command handler
│   └── _state.py          # build_coding_state() helper
└── tests/
    ├── test_invariants.py
    ├── test_derivers.py
    └── test_command_handlers.py

src/shared/common/
├── types.py               # DomainEvent base, typed IDs (CodeId, etc.)
├── operation_result.py    # OperationResult pattern
└── failure_events.py      # FailureEvent base class

src/shared/infra/
├── event_bus.py           # Pub/sub for domain events
└── signal_bridge/
    ├── base.py            # BaseSignalBridge abstract class
    ├── payloads.py        # SignalPayload, ActivityItem DTOs
    └── thread_utils.py    # Thread-safe emission helpers

src/tests/e2e/             # End-to-end tests with Allure
├── test_manage_sources_e2e.py
└── conftest.py            # Real database fixtures
```

## After the Tutorial

You should be able to:

1. Explain why invariants are pure functions
2. Write a new invariant and its tests
3. Modify a deriver to use new invariants
4. Create a command handler that orchestrates the flow
5. Trace an event from command handler to UI via SignalBridge
6. Write E2E tests with Allure decorators
7. Know where to look when adding new features

Ready? Start with [Part 0: The Big Picture](./00-big-picture.md).
