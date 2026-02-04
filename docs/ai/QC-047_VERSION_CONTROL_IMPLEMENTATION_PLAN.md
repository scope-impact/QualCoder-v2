# QC-047: SQLite Database Version Control - Implementation Plan

## Overview

Implement automatic version control for QualCoder project databases using:
- **sqlite-diffable** - Convert SQLite to diffable JSON
- **Git** - Version control the JSON files
- **Auto-commit with 500ms debounce** - Every mutation triggers a commit

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        EventBus                              │
│                           │                                  │
│    ┌──────────────────────┼──────────────────────┐          │
│    ▼                      ▼                      ▼          │
│ CodeCreated        SegmentCoded           SourceImported    │
│    │                      │                      │          │
│    └──────────────────────┼──────────────────────┘          │
│                           ▼                                  │
│              ┌────────────────────────┐                     │
│              │ VersionControlListener │                     │
│              │  - collect events      │                     │
│              │  - debounce 500ms      │                     │
│              │  - dump + commit       │                     │
│              └────────────────────────┘                     │
│                           │                                  │
│         ┌─────────────────┼─────────────────┐               │
│         ▼                                   ▼               │
│  SQLiteDiffableAdapter              GitRepositoryAdapter    │
│  (dump/load JSON)                   (commit/log/checkout)   │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Infrastructure Layer

**Files to create:**

| File | Responsibility |
|------|----------------|
| `src/contexts/projects/infra/sqlite_diffable_adapter.py` | Wrapper for sqlite-diffable CLI (dump/load) |
| `src/contexts/projects/infra/git_repository_adapter.py` | Wrapper for Git CLI (init/commit/log/checkout) |

**SQLiteDiffableAdapter:**
```python
class SQLiteDiffableAdapter:
    def dump(self, db_path: Path, output_dir: Path, exclude: list[str]) -> OperationResult
    def load(self, db_path: Path, snapshot_dir: Path, replace: bool) -> OperationResult
    def get_vcs_dir(self, project_path: Path) -> Path
```

**GitRepositoryAdapter:**
```python
class GitRepositoryAdapter:
    def is_initialized(self) -> bool
    def init(self) -> OperationResult
    def add_all(self) -> OperationResult
    def commit(self, message: str) -> OperationResult  # Returns SHA
    def log(self, limit: int) -> OperationResult  # Returns list[CommitInfo]
    def diff(self, from_ref: str, to_ref: str) -> OperationResult
    def checkout(self, ref: str) -> OperationResult
    def has_uncommitted_changes(self) -> bool
```

---

### Phase 2: Core Layer - Entities & Events

**Files to create:**

| File | Responsibility |
|------|----------------|
| `src/contexts/projects/core/vcs_entities.py` | Snapshot, SnapshotDiff, DiffEntry |
| `src/contexts/projects/core/vcs_events.py` | SnapshotCreated, SnapshotRestored |
| `src/contexts/projects/core/vcs_failure_events.py` | SnapshotNotCreated, etc. |
| `src/contexts/projects/core/vcs_commands.py` | RestoreSnapshotCommand, etc. |

**Key Entities:**
```python
@dataclass(frozen=True)
class Snapshot:
    id: SnapshotId
    message: str
    author: str
    created_at: datetime
    git_sha: str

@dataclass(frozen=True)
class DiffEntry:
    table_name: str
    change_type: str  # "added", "modified", "deleted"
    row_count: int
```

---

### Phase 3: Auto-Commit Listener

**File:** `src/contexts/projects/infra/version_control_listener.py`

This is the core component that makes auto-commit work.

```python
class VersionControlListener:
    """
    Subscribes to mutation events and auto-commits with 500ms debounce.
    """

    DEBOUNCE_MS = 500

    MUTATION_EVENTS = (
        # Coding context
        "coding.code_created",
        "coding.code_updated",
        "coding.code_deleted",
        "coding.category_created",
        "coding.segment_coded",
        "coding.segment_uncoded",
        "coding.segment_memo_updated",
        # Sources context
        "sources.source_imported",
        "sources.source_deleted",
        "sources.source_updated",
        # Cases context
        "cases.case_created",
        "cases.case_updated",
        "cases.case_deleted",
        "cases.attribute_added",
        # Folders context
        "folders.folder_created",
        "folders.folder_deleted",
    )

    def __init__(
        self,
        event_bus: EventBus,
        diffable_adapter: SQLiteDiffableAdapter,
        git_adapter: GitRepositoryAdapter,
        project_path: Path,
    ):
        self._event_bus = event_bus
        self._diffable = diffable_adapter
        self._git = git_adapter
        self._project_path = project_path
        self._pending_events: list[DomainEvent] = []
        self._timer: QTimer | None = None
        self._enabled = False

        # Subscribe to all mutation events
        for event_type in self.MUTATION_EVENTS:
            event_bus.subscribe(event_type, self._on_mutation)

    def enable(self):
        """Enable auto-commit (call after VCS initialized)."""
        self._enabled = True

    def disable(self):
        """Disable auto-commit."""
        self._enabled = False
        if self._timer:
            self._timer.stop()

    def _on_mutation(self, event: DomainEvent):
        """Queue event and reset debounce timer."""
        if not self._enabled:
            return

        self._pending_events.append(event)
        self._reset_timer()

    def _reset_timer(self):
        if self._timer:
            self._timer.stop()

        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._flush)
        self._timer.start(self.DEBOUNCE_MS)

    def _flush(self):
        """Dump database and commit all pending events."""
        if not self._pending_events:
            return

        try:
            # 1. Dump database to JSON
            db_path = self._project_path / "data.sqlite"
            vcs_dir = self._diffable.get_vcs_dir(self._project_path)
            self._diffable.dump(db_path, vcs_dir)

            # 2. Generate commit message
            message = self._generate_message(self._pending_events)

            # 3. Git add + commit
            self._git.add_all()
            self._git.commit(message)

        finally:
            self._pending_events.clear()

    def _generate_message(self, events: list[DomainEvent]) -> str:
        """Generate commit message from batched events."""
        if len(events) == 1:
            return self._format_single(events[0])

        # Group by event type prefix
        groups = {}
        for event in events:
            prefix = event.event_type.split(".")[0]
            groups.setdefault(prefix, []).append(event)

        parts = []
        for prefix, group_events in groups.items():
            parts.append(f"{len(group_events)} {prefix} changes")

        return ", ".join(parts)

    def _format_single(self, event: DomainEvent) -> str:
        """Format a single event as commit message."""
        # e.g., "coding.code_created" -> "code: Created 'Theme A'"
        event_type = event.event_type
        if hasattr(event, "name"):
            return f"{event_type}: {event.name}"
        return event_type
```

---

### Phase 4: Command Handlers

**Files to create:**

| File | Responsibility |
|------|----------------|
| `src/contexts/projects/core/commandHandlers/initialize_version_control.py` | Git init + initial dump |
| `src/contexts/projects/core/commandHandlers/list_snapshots.py` | Parse git log |
| `src/contexts/projects/core/commandHandlers/view_diff.py` | Parse git diff |
| `src/contexts/projects/core/commandHandlers/restore_snapshot.py` | Checkout + load |

**initialize_version_control.py:**
```python
def initialize_version_control(
    command: InitializeVersionControlCommand,
    diffable_adapter: SQLiteDiffableAdapter,
    git_adapter: GitRepositoryAdapter,
    event_bus: EventBus,
) -> OperationResult:
    """
    Initialize version control for a project.

    Steps:
    1. Check if already initialized
    2. Git init
    3. Create .gitignore
    4. Initial dump
    5. Initial commit
    6. Publish event
    """
    project_path = Path(command.project_path)

    # 1. Check if already initialized
    if git_adapter.is_initialized():
        return OperationResult.fail(
            error="Version control already initialized",
            error_code="VCS_INIT_FAILED/ALREADY_EXISTS",
        )

    # 2. Git init
    init_result = git_adapter.init()
    if init_result.is_failure:
        return init_result

    # 3. Create .gitignore
    gitignore = project_path / ".gitignore"
    gitignore.write_text("data.sqlite\n*.sqlite-journal\n*.sqlite-wal\n")

    # 4. Initial dump
    db_path = project_path / "data.sqlite"
    vcs_dir = diffable_adapter.get_vcs_dir(project_path)
    dump_result = diffable_adapter.dump(db_path, vcs_dir)
    if dump_result.is_failure:
        return dump_result

    # 5. Initial commit
    git_adapter.add_all()
    commit_result = git_adapter.commit("Initial version control setup")
    if commit_result.is_failure:
        return commit_result

    # 6. Publish event
    event_bus.publish(VersionControlInitialized.create(str(project_path)))

    return OperationResult.ok(data={"git_sha": commit_result.data})
```

---

### Phase 5: MCP Tools

**File:** `src/contexts/projects/interface/vcs_mcp_tools.py`

```python
class VersionControlMCPTools:
    """MCP tools for AI agent access to version control."""

    def __init__(self, diffable, git, event_bus, state):
        self._diffable = diffable
        self._git = git
        self._event_bus = event_bus
        self._state = state

    def get_tool_schemas(self) -> list[dict]:
        return [
            {
                "name": "list_snapshots",
                "description": "List version control snapshots (commits)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 20}
                    }
                }
            },
            {
                "name": "view_diff",
                "description": "View changes between two snapshots",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "from_ref": {"type": "string", "default": "HEAD~1"},
                        "to_ref": {"type": "string", "default": "HEAD"}
                    }
                }
            },
            {
                "name": "restore_snapshot",
                "description": "Restore database to a previous state (WARNING: destructive)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ref": {"type": "string", "description": "Git SHA or HEAD~N"}
                    },
                    "required": ["ref"]
                }
            },
        ]
```

---

### Phase 6: Presentation Layer

**Files to create:**

| File | Responsibility |
|------|----------------|
| `src/contexts/projects/presentation/viewmodels/version_control_viewmodel.py` | UI state management |
| `src/contexts/projects/presentation/pages/version_history_page.py` | List snapshots, actions |
| `src/contexts/projects/presentation/dialogs/diff_viewer_dialog.py` | Show diff details |

---

### Phase 7: Wiring in main.py

```python
# In QualCoderApp._open_project() or similar

def _setup_version_control(self, project_path: Path):
    """Wire up version control components."""
    # Create adapters
    diffable = SQLiteDiffableAdapter()
    git = GitRepositoryAdapter(project_path)

    # Create listener (disabled until VCS initialized)
    self._vcs_listener = VersionControlListener(
        event_bus=self._ctx.event_bus,
        diffable_adapter=diffable,
        git_adapter=git,
        project_path=project_path,
    )

    # Enable if VCS already initialized
    if git.is_initialized():
        self._vcs_listener.enable()
```

---

## Testing Strategy

### Unit Tests (Pure Domain)
- `test_vcs_entities.py` - Snapshot, DiffEntry creation
- `test_vcs_events.py` - Event construction

### Integration Tests (Adapters)
- `test_sqlite_diffable_adapter.py` - dump/load with real files
- `test_git_repository_adapter.py` - Git operations with temp repo

### E2E Tests
```python
@allure.story("QC-047.02 Auto-commit on mutations")
class TestAutoCommit:

    @allure.title("AC #2: Every mutation auto-commits")
    def test_code_creation_triggers_commit(self, app_with_vcs):
        # 1. Create a code
        app_with_vcs.viewmodel.create_code("Theme A", "#FF0000")

        # 2. Wait for debounce
        QTest.qWait(600)

        # 3. Verify commit exists
        log = app_with_vcs.git.log(limit=1)
        assert "code" in log[0].message.lower()
```

---

## Commit Message Examples

| Event(s) | Generated Message |
|----------|-------------------|
| Single CodeCreated | `coding.code_created: Theme A` |
| Multiple codes | `3 coding changes` |
| Mixed batch | `2 coding changes, 1 sources changes` |
| Source import | `sources.source_imported: interview_01.txt` |

---

## Dependencies

```toml
[project.dependencies]
sqlite-diffable = ">=1.0"
```

**System requirements:**
- Git CLI in PATH
- sqlite-diffable CLI (installed via pip)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large DB slow to dump | Medium | Exclude fulltext, run async |
| Git history grows large | Low | Periodic `git gc`, exclude blobs |
| Debounce too short | Low | Make configurable (500ms default) |
| User restores by accident | High | Confirmation dialog, auto-snapshot before restore |

---

## Related Files

- **Task:** `backlog/tasks/qc-047 - SQLite-Database-Version-Control.md`
- **Decision:** `backlog/decisions/decision-006 sqlite-version-control-sqlite-diffable.md`
- **Developer Guide:** `.claude/skills/developer/SKILL.md`
