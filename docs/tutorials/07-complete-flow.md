# Part 7: Complete Flow Reference

This is your reference for the complete Code creation flow with priority.

## The Full Diagram

```mermaid
flowchart TB
    subgraph User ["User Action"]
        UA[User clicks 'Create Code' button]
    end

    subgraph Presentation ["Presentation Layer"]
        Dialog[CreateCodeDialog]
        TreeView[CodebookTreeView]
        ActivityPanel[ActivityPanel]
    end

    subgraph Controller ["Controller (Application)"]
        Ctrl[CodingController.create_code]
        BuildState["Build CodingState from repos"]
        Persist["repo.save_from_event()"]
        Publish["event_bus.publish()"]
    end

    subgraph Domain ["Domain Layer (Pure)"]
        Deriver[derive_create_code]
        Inv1{is_valid_code_name?}
        Inv2{is_code_name_unique?}
        Inv3{is_valid_priority?}
        Event[CodeCreated Event]
        Fail[Failure]
    end

    subgraph EventBus ["EventBus"]
        EB[Route to subscribers]
    end

    subgraph SignalBridge ["SignalBridge"]
        SB[CodingSignalBridge]
        Convert[Convert event → payload]
        Emit[Thread-safe emit]
    end

    UA --> Dialog
    Dialog --> Ctrl
    Ctrl --> BuildState
    BuildState --> Deriver

    Deriver --> Inv1
    Inv1 -->|No| Fail
    Inv1 -->|Yes| Inv2
    Inv2 -->|No| Fail
    Inv2 -->|Yes| Inv3
    Inv3 -->|No| Fail
    Inv3 -->|Yes| Event

    Event --> Persist
    Persist --> Publish
    Publish --> EB
    EB --> SB
    SB --> Convert
    Convert --> Emit
    Emit --> TreeView
    Emit --> ActivityPanel

    Fail -.->|Return to UI| Dialog
```

## Layer Summary

| Layer | Responsibility | Pure? | Side Effects |
|-------|---------------|-------|--------------|
| Presentation | User input, rendering | No | UI events |
| Controller | Orchestration | No | Read/write repos, publish |
| Domain | Business logic | **Yes** | None |
| EventBus | Message routing | No | Handler invocation |
| SignalBridge | Event→Signal conversion | No | Thread marshaling |
| UI Widgets | Display updates | No | Qt rendering |

## Key Files

```
src/contexts/coding/core/
├── invariants.py          # is_valid_priority()
├── derivers.py            # derive_create_code()
├── events.py              # CodeCreated (with priority)
├── failure_events.py      # CodeNotCreated, CodeNotDeleted, etc.
└── entities.py            # Code entity

src/contexts/shared/core/
├── types.py               # DomainEvent, typed IDs
└── failure_events.py      # FailureEvent base class

src/application/
├── event_bus.py           # EventBus
└── signal_bridge/
    ├── base.py            # BaseSignalBridge
    └── payloads.py        # CodeCreatedPayload (with priority)
```

## Detailed Sequence

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant D as Dialog
    participant C as Controller
    participant R as Repository
    participant DV as Deriver
    participant EB as EventBus
    participant SB as SignalBridge
    participant TV as TreeView
    participant AP as ActivityPanel

    U->>D: Click "Create Code"
    D->>C: create_code(name, color, priority)

    Note over C: Build state from repositories
    C->>R: get_all_codes()
    R-->>C: existing_codes
    C->>R: get_all_categories()
    R-->>C: existing_categories

    Note over C,DV: Call pure deriver
    C->>DV: derive_create_code(name, color, priority, state)

    Note over DV: Validate with invariants
    DV->>DV: is_valid_code_name(name)
    DV->>DV: is_code_name_unique(name, codes)
    DV->>DV: is_valid_priority(priority)

    alt All validations pass
        DV-->>C: CodeCreated event
        Note over C: Persist change
        C->>R: save_from_event(event)

        Note over C: Publish event
        C->>EB: publish(CodeCreated)

        Note over EB: Route to subscribers
        EB->>SB: handler(event)

        Note over SB: Convert and emit
        SB->>SB: converter.convert(event)
        SB->>TV: code_created.emit(payload)
        SB->>AP: activity_logged.emit(activity)

        TV->>TV: Add code to tree
        AP->>AP: Show "Code created"
    else Validation fails
        DV-->>C: FailureEvent(reason)
        C-->>D: Failure
        D->>D: Show error message
    end
```

## Testing at Each Layer

```mermaid
graph TB
    subgraph INV ["Invariants (src/contexts/coding/core/tests/test_invariants.py)"]
        INV_TEST["def test_valid_priority():<br/>    assert is_valid_priority(3) is True<br/>    assert is_valid_priority(10) is False"]
        INV_PROPS["✓ No setup<br/>✓ No mocks<br/>✓ Microseconds"]
    end

    subgraph DER ["Derivers (src/contexts/coding/core/tests/test_derivers.py)"]
        DER_TEST["def test_create_code_with_priority(empty_state):<br/>    result = derive_create_code(..., priority=3, state=empty_state)<br/>    assert isinstance(result, CodeCreated)<br/>    assert result.priority == 3"]
        DER_PROPS["✓ Data fixtures<br/>✓ No database<br/>✓ Fast"]
    end

    subgraph CONV ["Converters (src/application/signal_bridge/tests/test_payloads.py)"]
        CONV_TEST["def test_converter_includes_priority():<br/>    event = CodeCreated(..., priority=3)<br/>    payload = converter.convert(event)<br/>    assert payload.priority == 3"]
        CONV_PROPS["✓ Pure transformation<br/>✓ No Qt required"]
    end

    subgraph INT ["Integration (test_integration.py)"]
        INT_TEST["def test_full_flow():<br/>    event_bus = EventBus()<br/>    # Subscribe, derive, publish, verify"]
        INT_PROPS["✓ No database<br/>✓ No Qt<br/>✓ Core logic only"]
    end

    INV --> DER --> CONV --> INT
```

## Quick Reference: Adding a New Field

To add a new field (like `priority`) to an existing flow:

```mermaid
flowchart LR
    subgraph Step1 ["1. Invariant"]
        I["core/invariants.py<br/>is_valid_priority()"]
    end

    subgraph Step2 ["2. Failure Event"]
        F["core/failure_events.py<br/>CodeNotCreated.invalid_priority()"]
    end

    subgraph Step3 ["3. Deriver"]
        D["core/derivers.py<br/>Add parameter<br/>Add validation"]
    end

    subgraph Step4 ["4. Event"]
        E["core/events.py<br/>Add field to CodeCreated"]
    end

    subgraph Step5 ["5. Payload"]
        P["signal_bridge/payloads.py<br/>Add field to payload"]
    end

    subgraph Step6 ["6. Converter"]
        C["Map event.priority<br/>to payload.priority"]
    end

    subgraph Step7 ["7. Tests"]
        T["core/tests/test_invariants.py<br/>core/tests/test_derivers.py"]
    end

    Step1 --> Step2 --> Step3 --> Step4 --> Step5 --> Step6 --> Step7
```

### Checklist

1. **Invariant** (`src/contexts/coding/core/invariants.py`)
   - [ ] Add `is_valid_<field>()` pure predicate

2. **Failure Event** (`src/contexts/coding/core/failure_events.py`)
   - [ ] Add factory method to existing failure event class (e.g., `CodeNotCreated.invalid_priority()`)

3. **Deriver** (`src/contexts/coding/core/derivers.py`)
   - [ ] Add parameter to function signature
   - [ ] Add validation call
   - [ ] Return failure event if invalid (e.g., `CodeNotCreated.invalid_priority(value)`)

4. **Event** (`src/contexts/coding/core/events.py`)
   - [ ] Add field to event dataclass
   - [ ] Add to `create()` factory method

5. **Payload** (`src/application/signal_bridge/payloads.py`)
   - [ ] Add field to payload dataclass

6. **Converter** (context-specific)
   - [ ] Map `event.<field>` to `payload.<field>`

7. **Tests**
   - [ ] `src/contexts/coding/core/tests/test_invariants.py`: Test the predicate
   - [ ] `src/contexts/coding/core/tests/test_derivers.py`: Test valid/invalid cases

## You're Ready!

You now understand the complete fDDD architecture:

- **Invariants** validate business rules (pure)
- **Derivers** compose invariants and produce events (pure)
- **Events** are immutable records of what happened
- **EventBus** routes events to subscribers
- **SignalBridge** converts events to UI payloads
- **Payloads** carry data to Qt widgets

For common patterns and recipes, see the appendices.

---

**Appendices:**
- [Appendix A: Common Patterns & Recipes](./appendices/A-common-patterns.md)
- [Appendix B: When to Create New Patterns](./appendices/B-when-to-create.md)
