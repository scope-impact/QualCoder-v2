# QualCoder v2 Refactoring Plan

> **STATUS: COMPLETED** (2025-02-03)
> All items in this plan have been implemented.

Based on analysis against `.claude/skills/developer/SKILL.md` guidelines.

---

## Summary of Gaps

| Area | Issue | Priority | Status |
|------|-------|----------|--------|
| MCP CaseTools | Calls repos directly, bypasses use cases | P0 | ✅ Done |
| OperationResult | Use cases return `Result[T, str]`, no error_code/suggestions | P0 | ✅ Done |
| Cases domain | Missing derivers, failure_events, DomainEvent inheritance | P1 | ✅ Done |
| Projects domain | Missing derivers, DomainEvent inheritance | P1 | ✅ Done |
| Batch use cases | No `batch_apply_codes()` for AI efficiency | P2 | ✅ Done |
| CaseManagerViewModel | Not connected to SignalBridge | P2 | ✅ Done |
| SKILL.md | E2E test path outdated | P3 | ✅ Done |

---

## Phase 1: Foundation

### 1.1 OperationResult Type
**Create:** `src/contexts/shared/core/operation_result.py`

```python
@dataclass(frozen=True)
class OperationResult:
    success: bool
    data: Any | None = None
    error: str | None = None
    error_code: str | None = None
    suggestions: tuple[str, ...] = ()
    rollback_command: Any | None = None
```

### 1.2 Cases Domain Completion
**Create:**
- `src/contexts/cases/core/failure_events.py`
- `src/contexts/cases/core/derivers.py`

**Modify:**
- `src/contexts/cases/core/events.py` → inherit DomainEvent

### 1.3 Projects Domain Completion
**Create:**
- `src/contexts/projects/core/derivers.py`

**Modify:**
- `src/contexts/projects/core/events.py` → inherit DomainEvent

---

## Phase 2: Use Cases

### 2.1 Migrate to OperationResult
**Modify:** All `src/application/*/usecases/*.py`

Change from:
```python
def create_code(...) -> Result[Code, str]:
    return Failure("Name exists")
```

To:
```python
def create_code(...) -> OperationResult:
    return OperationResult(
        success=False,
        error="Name exists",
        error_code="CODE_NOT_CREATED/DUPLICATE_NAME",
        suggestions=("Use a different name",),
    )
```

### 2.2 Add Batch Use Cases
**Create:** `src/application/coding/usecases/batch_apply_codes.py`

---

## Phase 3: Presentation

### 3.1 MCP CaseTools → Use Cases (P0)
**Modify:** `src/infrastructure/mcp/case_tools.py`

Change from:
```python
def create_case(self, params):
    case = Case(...)
    self._case_repo.save(case)  # ❌ Direct repo
```

To:
```python
def create_case(self, params):
    result = create_case_usecase(  # ✅ Use case
        CreateCaseCommand(...),
        self._cases_ctx,
        self._event_bus,
    )
```

### 3.2 CaseManagerViewModel + SignalBridge
**Modify:** `src/presentation/viewmodels/case_manager_viewmodel.py`

Add signal subscriptions for reactive updates.

---


## Execution Order

```
Week 1: Foundation
  └── 1.1 OperationResult
  └── 1.2 Cases domain
  └── 1.3 Projects domain

Week 2: Use Cases
  └── 2.1 Migrate coding use cases first (reference)
  └── 2.1 Migrate remaining use cases
  └── 2.2 Batch use cases

Week 3: Presentation
  └── 3.1 MCP CaseTools (critical fix)
  └── 3.2 SignalBridge connection


```

---

## Dependencies

```
OperationResult ──┬──→ Use Case Migration ──→ MCP CaseTools
                  │
Cases Domain ─────┘
Projects Domain ──┘
```

---

## Decision: Provider Pattern

**Current:** ViewModels use Provider protocols for dependency injection.

**Guide says:** "Use direct wiring for internal, stable dependencies."

**Decision:** Keep providers for testability, but ensure:
1. MCP Tools call same use cases as ViewModels
2. Document that providers are for testing convenience

---

## Files Affected

### New Files (5)
- `src/contexts/shared/core/operation_result.py`
- `src/contexts/cases/core/failure_events.py`
- `src/contexts/cases/core/derivers.py`
- `src/contexts/projects/core/derivers.py`
- `src/application/coding/usecases/batch_apply_codes.py`

### Modified Files (~20)
- `src/contexts/cases/core/events.py`
- `src/contexts/projects/core/events.py`
- `src/application/coding/usecases/*.py` (6 files)
- `src/application/cases/usecases/*.py` (4 files)
- `src/application/ai_services/usecases/*.py` (3 files)
- `src/infrastructure/mcp/case_tools.py`
- `src/presentation/viewmodels/case_manager_viewmodel.py`
- `.claude/skills/developer/SKILL.md`

---

## Completion Notes

**Completed: 2025-02-03**

### Implementation Summary

1. **OperationResult** - Created `src/contexts/shared/core/operation_result.py` with full error handling pattern
2. **Cases domain** - Created `src/contexts/cases/core/derivers.py` with full validation
3. **Projects domain** - Created `src/contexts/projects/core/derivers.py`
4. **Batch use cases** - Created `src/application/coding/usecases/batch_apply_codes.py`
5. **CaseManagerViewModel + SignalBridge** - Integrated via `src/application/cases/signal_bridge.py`
6. **MCP CaseTools** - Refactored to use `CaseToolsContext` protocol (like `ProjectTools`)
   - Now reads from `ProjectState` instead of direct repo calls
   - Backward compatible with legacy `case_repo` parameter (emits deprecation warning)
   - 31 tests passing

### Key Patterns Established

- **MCP Tools** should accept `AppContext` (or protocol) rather than individual repos
- **Query operations** read from `ProjectState` cache
- **Write operations** call use cases which publish domain events
- **Deprecation path** maintained for backward compatibility
