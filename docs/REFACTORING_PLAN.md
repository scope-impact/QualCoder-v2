# QualCoder v2 Refactoring Plan

Based on analysis against `.claude/skills/developer/SKILL.md` guidelines.

---

## Summary of Gaps

| Area | Issue | Priority |
|------|-------|----------|
| MCP CaseTools | Calls repos directly, bypasses use cases | P0 |
| OperationResult | Use cases return `Result[T, str]`, no error_code/suggestions | P0 |
| Cases domain | Missing derivers, failure_events, DomainEvent inheritance | P1 |
| Projects domain | Missing derivers, DomainEvent inheritance | P1 |
| Batch use cases | No `batch_apply_codes()` for AI efficiency | P2 |
| CaseManagerViewModel | Not connected to SignalBridge | P2 |
| SKILL.md | E2E test path outdated | P3 |

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

## Phase 4: Documentation

### 4.1 Fix SKILL.md
**Modify:** `.claude/skills/developer/SKILL.md`
- Line 580: Change `src/presentation/tests/e2e/` → `src/tests/e2e/`

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

Anytime: Documentation
  └── 4.1 SKILL.md fixes
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
