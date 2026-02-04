# QC-047: SQLite Database Version Control - Implementation Plan

## Overview

Implement automatic version control for QualCoder project databases using:
- **sqlite-diffable** - Convert SQLite to diffable JSON
- **Git** - Version control the JSON files
- **Auto-commit with 500ms debounce** - Every mutation triggers a commit

## Architecture (fDDD Compliant)

```
┌─────────────────────────────────────────────────────────────────┐
│ Presentation                                                     │
│   VersionHistoryPage ──→ VersionControlViewModel                │
│   VersionControlMCPTools ───────────────┐                       │
├─────────────────────────────────────────┼───────────────────────┤
│ Application (Orchestration Only)        │                       │
│                                         │                       │
│   VersionControlListener ───────────────┼──→ auto_commit()      │
│   (collects events, debounces,          │    restore_snapshot() │
│    calls command handler)               │    list_snapshots()   │
│                                         │                       │
│   SignalBridge ◄────────────────────────┼─── events             │
├─────────────────────────────────────────┼───────────────────────┤
│ Domain (PURE - No I/O)                  │                       │
│                                         │                       │
│   Invariants:                           │                       │
│     is_version_control_initialized()    │                       │
│     is_valid_snapshot_message()         │                       │
│     is_valid_git_ref()                  │                       │
│                                         │                       │
│   Derivers:                   ◄─────────┘                       │
│     derive_auto_commit()                                        │
│     derive_restore_snapshot()                                   │
│                                                                 │
│   State Container:                                              │
│     VersionControlState (frozen)                                │
│                                                                 │
│   Events:                                                       │
│     SnapshotCreated, SnapshotRestored                          │
│     AutoCommitSkipped (failure)                                 │
├─────────────────────────────────────────────────────────────────┤
│ Infrastructure (I/O)                                            │
│   SQLiteDiffableAdapter - dump/load JSON                        │
│   GitRepositoryAdapter - git CLI wrapper                        │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Infrastructure Layer (I/O Only)

**Files to create:**

| File | Responsibility |
|------|----------------|
| `src/contexts/projects/infra/sqlite_diffable_adapter.py` | CLI wrapper for sqlite-diffable |
| `src/contexts/projects/infra/git_repository_adapter.py` | CLI wrapper for git |

**SQLiteDiffableAdapter:**
```python
"""SQLite-Diffable Adapter - I/O wrapper for sqlite-diffable CLI."""

from pathlib import Path
from src.shared.common.operation_result import OperationResult


class SQLiteDiffableAdapter:
    """I/O adapter - no business logic."""

    VCS_DIR_NAME = ".qualcoder-vcs"

    EXCLUDE_TABLES = (
        "sqlite_sequence",
        "source_fulltext_fts",
        "source_fulltext_data",
    )

    def dump(self, db_path: Path, output_dir: Path) -> OperationResult:
        """Dump database to JSON. Pure I/O."""
        ...

    def load(self, db_path: Path, snapshot_dir: Path) -> OperationResult:
        """Load database from JSON. Pure I/O."""
        ...

    def get_vcs_dir(self, project_path: Path) -> Path:
        return project_path / self.VCS_DIR_NAME
```

**GitRepositoryAdapter:**
```python
"""Git Repository Adapter - I/O wrapper for git CLI."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from src.shared.common.operation_result import OperationResult


@dataclass(frozen=True)
class CommitInfo:
    sha: str
    message: str
    author: str
    timestamp: datetime


class GitRepositoryAdapter:
    """I/O adapter - no business logic."""

    def __init__(self, repo_path: Path):
        self._repo_path = repo_path

    def is_initialized(self) -> bool:
        """Check if .git exists."""
        ...

    def init(self) -> OperationResult:
        """Run git init."""
        ...

    def add_all(self, path: Path) -> OperationResult:
        """Run git add on path."""
        ...

    def commit(self, message: str) -> OperationResult:
        """Run git commit. Returns SHA on success."""
        ...

    def log(self, limit: int = 50) -> OperationResult:
        """Run git log. Returns list[CommitInfo]."""
        ...

    def diff(self, from_ref: str, to_ref: str) -> OperationResult:
        """Run git diff."""
        ...

    def checkout(self, ref: str) -> OperationResult:
        """Run git checkout."""
        ...

    def get_valid_refs(self) -> tuple[str, ...]:
        """Get all valid commit SHAs."""
        ...

    def has_staged_changes(self) -> bool:
        """Check git status for staged changes."""
        ...
```

---

### Phase 2: Domain Layer (Pure - No I/O)

**Files to create:**

| File | Responsibility |
|------|----------------|
| `src/contexts/projects/core/vcs_invariants.py` | Pure validation predicates |
| `src/contexts/projects/core/vcs_entities.py` | Frozen dataclasses |
| `src/contexts/projects/core/vcs_events.py` | Success events |
| `src/contexts/projects/core/vcs_failure_events.py` | Failure events |
| `src/contexts/projects/core/vcs_derivers.py` | Pure event derivation |
| `src/contexts/projects/core/vcs_commands.py` | Command DTOs |

#### 2.1 Invariants (Pure Predicates)

```python
"""Version Control Invariants - Pure validation predicates."""


def is_version_control_initialized(git_initialized: bool) -> bool:
    """VCS must be initialized before operations."""
    return git_initialized


def is_valid_snapshot_message(message: str) -> bool:
    """Message must be non-empty and reasonable length."""
    return bool(message and message.strip() and len(message.strip()) <= 500)


def is_valid_git_ref(ref: str, valid_refs: tuple[str, ...]) -> bool:
    """Ref must exist in repository."""
    if ref.startswith("HEAD"):
        return True  # HEAD~N syntax always valid
    return ref in valid_refs


def has_events_to_commit(events: tuple) -> bool:
    """Must have at least one event to commit."""
    return len(events) > 0


def can_restore_snapshot(
    is_initialized: bool,
    has_uncommitted: bool,
    ref_valid: bool,
) -> bool:
    """All conditions must be met to restore."""
    return is_initialized and not has_uncommitted and ref_valid
```

#### 2.2 State Container (Frozen)

```python
"""Version Control State - Immutable state container for derivers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class VersionControlState:
    """State container for VCS derivers. Immutable."""

    is_initialized: bool = False
    has_uncommitted_changes: bool = False
    valid_refs: tuple[str, ...] = ()
    current_ref: str = "HEAD"
```

#### 2.3 Events (Past Tense)

```python
"""Version Control Events - Immutable domain events."""

from dataclasses import dataclass
from typing import ClassVar
from src.shared.common.types import DomainEvent


@dataclass(frozen=True)
class SnapshotCreated(DomainEvent):
    """Success: A snapshot was created."""

    event_type: ClassVar[str] = "projects.snapshot_created"

    git_sha: str
    message: str
    event_count: int


@dataclass(frozen=True)
class SnapshotRestored(DomainEvent):
    """Success: Database was restored to a snapshot."""

    event_type: ClassVar[str] = "projects.snapshot_restored"

    ref: str
    git_sha: str


@dataclass(frozen=True)
class VersionControlInitialized(DomainEvent):
    """Success: VCS was initialized."""

    event_type: ClassVar[str] = "projects.version_control_initialized"

    project_path: str
```

#### 2.4 Failure Events

```python
"""Version Control Failure Events - Rich failure context."""

from dataclasses import dataclass
from src.shared.common.failure_events import FailureEvent


@dataclass(frozen=True)
class AutoCommitSkipped(FailureEvent):
    """Failure: Auto-commit was skipped."""

    @classmethod
    def not_initialized(cls) -> "AutoCommitSkipped":
        return cls(
            error_code="AUTO_COMMIT_SKIPPED/NOT_INITIALIZED",
            reason="Version control not initialized",
            suggestions=("Initialize version control first",),
        )

    @classmethod
    def no_events(cls) -> "AutoCommitSkipped":
        return cls(
            error_code="AUTO_COMMIT_SKIPPED/NO_EVENTS",
            reason="No events to commit",
        )


@dataclass(frozen=True)
class SnapshotNotRestored(FailureEvent):
    """Failure: Snapshot restoration failed."""

    ref: str | None = None

    @classmethod
    def not_initialized(cls) -> "SnapshotNotRestored":
        return cls(
            error_code="SNAPSHOT_NOT_RESTORED/NOT_INITIALIZED",
            reason="Version control not initialized",
        )

    @classmethod
    def uncommitted_changes(cls) -> "SnapshotNotRestored":
        return cls(
            error_code="SNAPSHOT_NOT_RESTORED/UNCOMMITTED_CHANGES",
            reason="Cannot restore with uncommitted changes",
            suggestions=("Wait for auto-commit to complete", "Or discard changes"),
        )

    @classmethod
    def invalid_ref(cls, ref: str) -> "SnapshotNotRestored":
        return cls(
            error_code="SNAPSHOT_NOT_RESTORED/INVALID_REF",
            reason=f"Invalid snapshot reference: {ref}",
            ref=ref,
        )
```

#### 2.5 Derivers (Pure Functions)

```python
"""Version Control Derivers - Pure event derivation."""

from src.contexts.projects.core.vcs_invariants import (
    has_events_to_commit,
    is_valid_git_ref,
    is_version_control_initialized,
)
from src.contexts.projects.core.vcs_events import SnapshotCreated, SnapshotRestored
from src.contexts.projects.core.vcs_failure_events import (
    AutoCommitSkipped,
    SnapshotNotRestored,
)


def derive_auto_commit(
    events: tuple,
    state: VersionControlState,
) -> SnapshotCreated | AutoCommitSkipped:
    """
    Derive auto-commit event. PURE - no I/O.

    Pattern: (events, state) → SuccessEvent | FailureEvent
    """
    if not is_version_control_initialized(state.is_initialized):
        return AutoCommitSkipped.not_initialized()

    if not has_events_to_commit(events):
        return AutoCommitSkipped.no_events()

    # Generate message from events
    message = _generate_commit_message(events)

    return SnapshotCreated(
        git_sha="pending",  # Filled in by command handler after actual commit
        message=message,
        event_count=len(events),
    )


def derive_restore_snapshot(
    ref: str,
    state: VersionControlState,
) -> SnapshotRestored | SnapshotNotRestored:
    """
    Derive restore event. PURE - no I/O.
    """
    if not is_version_control_initialized(state.is_initialized):
        return SnapshotNotRestored.not_initialized()

    if state.has_uncommitted_changes:
        return SnapshotNotRestored.uncommitted_changes()

    if not is_valid_git_ref(ref, state.valid_refs):
        return SnapshotNotRestored.invalid_ref(ref)

    return SnapshotRestored(ref=ref, git_sha=ref)


def _generate_commit_message(events: tuple) -> str:
    """Generate commit message from events. Pure function."""
    if len(events) == 1:
        event = events[0]
        return f"{event.event_type}"

    # Group by context
    groups: dict[str, int] = {}
    for event in events:
        context = event.event_type.split(".")[0]
        groups[context] = groups.get(context, 0) + 1

    parts = [f"{count} {ctx}" for ctx, count in groups.items()]
    return ", ".join(parts)
```

---

### Phase 3: Command Handlers (Orchestration Only)

**Files to create:**

| File | Responsibility |
|------|----------------|
| `src/contexts/projects/core/commandHandlers/auto_commit.py` | Debounced auto-commit |
| `src/contexts/projects/core/commandHandlers/restore_snapshot.py` | Restore to ref |
| `src/contexts/projects/core/commandHandlers/list_snapshots.py` | Query git log |
| `src/contexts/projects/core/commandHandlers/view_diff.py` | Query git diff |
| `src/contexts/projects/core/commandHandlers/initialize_version_control.py` | Git init |

#### 3.1 auto_commit.py

```python
"""
Auto-Commit Command Handler

Orchestrates the debounced auto-commit workflow.
Command handlers do orchestration only - domain decides.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from src.contexts.projects.core.vcs_commands import AutoCommitCommand
from src.contexts.projects.core.vcs_derivers import (
    VersionControlState,
    derive_auto_commit,
)
from src.contexts.projects.core.vcs_events import SnapshotCreated
from src.contexts.projects.core.vcs_failure_events import AutoCommitSkipped
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.projects.infra.git_repository_adapter import GitRepositoryAdapter
    from src.contexts.projects.infra.sqlite_diffable_adapter import SQLiteDiffableAdapter
    from src.shared.infra.event_bus import EventBus


def auto_commit(
    command: AutoCommitCommand,
    diffable_adapter: SQLiteDiffableAdapter,
    git_adapter: GitRepositoryAdapter,
    event_bus: EventBus,
) -> OperationResult:
    """
    Execute auto-commit for batched events.

    5-step pattern:
    1. Build state from adapters (I/O)
    2. Call deriver (PURE - domain decides)
    3. Handle failure
    4. Execute I/O (dump, git add, commit)
    5. Publish event
    """
    project_path = Path(command.project_path)
    events = tuple(command.events)

    # Step 1: Build state from adapters
    state = VersionControlState(
        is_initialized=git_adapter.is_initialized(),
        has_uncommitted_changes=git_adapter.has_staged_changes(),
    )

    # Step 2: Call deriver (THE DOMAIN DECIDES)
    result = derive_auto_commit(events, state)

    # Step 3: Handle failure
    if isinstance(result, AutoCommitSkipped):
        return OperationResult.from_failure(result)

    # Step 4: Execute I/O
    db_path = project_path / "data.sqlite"
    vcs_dir = diffable_adapter.get_vcs_dir(project_path)

    dump_result = diffable_adapter.dump(db_path, vcs_dir)
    if dump_result.is_failure:
        return dump_result

    add_result = git_adapter.add_all(vcs_dir)
    if add_result.is_failure:
        return add_result

    commit_result = git_adapter.commit(result.message)
    if commit_result.is_failure:
        return commit_result

    git_sha = commit_result.data

    # Step 5: Publish event (with real SHA)
    final_event = SnapshotCreated(
        git_sha=git_sha,
        message=result.message,
        event_count=result.event_count,
    )
    event_bus.publish(final_event)

    return OperationResult.ok(
        data={"git_sha": git_sha, "message": result.message},
    )
```

#### 3.2 restore_snapshot.py

```python
"""
Restore Snapshot Command Handler

Orchestrates restoring database to a previous state.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from src.contexts.projects.core.vcs_commands import RestoreSnapshotCommand
from src.contexts.projects.core.vcs_derivers import (
    VersionControlState,
    derive_restore_snapshot,
)
from src.contexts.projects.core.vcs_failure_events import SnapshotNotRestored
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.projects.infra.git_repository_adapter import GitRepositoryAdapter
    from src.contexts.projects.infra.sqlite_diffable_adapter import SQLiteDiffableAdapter
    from src.shared.infra.event_bus import EventBus


def restore_snapshot(
    command: RestoreSnapshotCommand,
    diffable_adapter: SQLiteDiffableAdapter,
    git_adapter: GitRepositoryAdapter,
    event_bus: EventBus,
) -> OperationResult:
    """
    Restore database to a previous snapshot.

    5-step pattern:
    1. Build state
    2. Call deriver (domain decides)
    3. Handle failure
    4. Execute I/O (checkout, load)
    5. Publish event
    """
    project_path = Path(command.project_path)

    # Step 1: Build state
    state = VersionControlState(
        is_initialized=git_adapter.is_initialized(),
        has_uncommitted_changes=git_adapter.has_staged_changes(),
        valid_refs=git_adapter.get_valid_refs(),
    )

    # Step 2: Call deriver
    result = derive_restore_snapshot(command.ref, state)

    # Step 3: Handle failure
    if isinstance(result, SnapshotNotRestored):
        return OperationResult.from_failure(result)

    # Step 4: Execute I/O
    vcs_dir = diffable_adapter.get_vcs_dir(project_path)

    checkout_result = git_adapter.checkout(command.ref)
    if checkout_result.is_failure:
        return checkout_result

    db_path = project_path / "data.sqlite"
    load_result = diffable_adapter.load(db_path, vcs_dir)
    if load_result.is_failure:
        return load_result

    # Step 5: Publish event
    event_bus.publish(result)

    return OperationResult.ok(
        data={"ref": command.ref, "git_sha": result.git_sha},
    )
```

---

### Phase 4: VersionControlListener (Application Layer)

**File:** `src/contexts/projects/infra/version_control_listener.py`

The listener collects events and delegates to command handler - no I/O in listener.

```python
"""
Version Control Listener - Debounced auto-commit trigger.

Subscribes to mutation events and delegates to command handler.
Does NOT do I/O directly - that's the command handler's job.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer

from src.contexts.projects.core.vcs_commands import AutoCommitCommand

if TYPE_CHECKING:
    from src.contexts.projects.infra.git_repository_adapter import GitRepositoryAdapter
    from src.contexts.projects.infra.sqlite_diffable_adapter import SQLiteDiffableAdapter
    from src.shared.common.types import DomainEvent
    from src.shared.infra.event_bus import EventBus


class VersionControlListener:
    """
    Listens to mutation events and triggers auto-commit with debounce.

    Delegates to command handler - does not do I/O directly.
    """

    DEBOUNCE_MS = 500

    MUTATION_EVENTS = (
        # Coding context
        "coding.code_created",
        "coding.code_updated",
        "coding.code_deleted",
        "coding.category_created",
        "coding.category_deleted",
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
        "cases.attribute_updated",
        # Folders context
        "folders.folder_created",
        "folders.folder_deleted",
        "folders.source_moved",
    )

    def __init__(
        self,
        event_bus: EventBus,
        diffable_adapter: SQLiteDiffableAdapter,
        git_adapter: GitRepositoryAdapter,
        project_path: Path,
    ) -> None:
        self._event_bus = event_bus
        self._diffable = diffable_adapter
        self._git = git_adapter
        self._project_path = project_path
        self._pending_events: list[DomainEvent] = []
        self._timer: QTimer | None = None
        self._enabled = False

    def enable(self) -> None:
        """Enable auto-commit (call after VCS initialized)."""
        self._enabled = True

        # Subscribe to all mutation events
        for event_type in self.MUTATION_EVENTS:
            self._event_bus.subscribe(event_type, self._on_mutation)

    def disable(self) -> None:
        """Disable auto-commit and flush pending."""
        self._enabled = False
        if self._timer:
            self._timer.stop()
        self._flush()  # Commit any pending events

    def _on_mutation(self, event: DomainEvent) -> None:
        """Queue event and reset debounce timer."""
        if not self._enabled:
            return

        self._pending_events.append(event)
        self._reset_timer()

    def _reset_timer(self) -> None:
        """Reset the debounce timer."""
        if self._timer:
            self._timer.stop()

        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._flush)
        self._timer.start(self.DEBOUNCE_MS)

    def _flush(self) -> None:
        """Delegate to command handler."""
        if not self._pending_events:
            return

        # Import here to avoid circular dependency
        from src.contexts.projects.core.commandHandlers.auto_commit import auto_commit

        command = AutoCommitCommand(
            project_path=str(self._project_path),
            events=list(self._pending_events),
        )

        # Delegate to command handler (which does actual I/O)
        auto_commit(
            command,
            self._diffable,
            self._git,
            self._event_bus,
        )

        self._pending_events.clear()
```

---

### Phase 5: SignalBridge Integration

**File:** `src/shared/infra/signal_bridge/projects.py` (additions)

```python
"""Add VCS signals to ProjectSignalBridge."""

from PySide6.QtCore import Signal
from src.shared.infra.signal_bridge.base import BaseSignalBridge, EventConverter


# Add to ProjectSignalBridge class:

class ProjectSignalBridge(BaseSignalBridge):
    # Existing signals...
    project_opened = Signal(object)
    project_closed = Signal(object)

    # New VCS signals
    snapshot_created = Signal(object)
    snapshot_restored = Signal(object)
    version_control_initialized = Signal(object)

    def _register_converters(self) -> None:
        # Existing converters...

        # VCS converters
        self.register_converter(
            "projects.snapshot_created",
            SnapshotCreatedConverter(),
            "snapshot_created",
        )
        self.register_converter(
            "projects.snapshot_restored",
            SnapshotRestoredConverter(),
            "snapshot_restored",
        )
        self.register_converter(
            "projects.version_control_initialized",
            VCSInitializedConverter(),
            "version_control_initialized",
        )


@dataclass(frozen=True)
class SnapshotPayload:
    """UI payload for snapshot events. Primitives only."""

    event_type: str
    git_sha: str
    message: str
    event_count: int


class SnapshotCreatedConverter(EventConverter):
    def convert(self, event) -> SnapshotPayload:
        return SnapshotPayload(
            event_type=event.event_type,
            git_sha=event.git_sha,
            message=event.message,
            event_count=event.event_count,
        )
```

---

### Phase 6: Interface Layer (MCP Tools)

**File:** `src/contexts/projects/interface/vcs_mcp_tools.py`

```python
"""Version Control MCP Tools - AI Agent Interface."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.contexts.projects.infra.git_repository_adapter import GitRepositoryAdapter
    from src.contexts.projects.infra.sqlite_diffable_adapter import SQLiteDiffableAdapter
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.state import ProjectState


class VersionControlMCPTools:
    """
    MCP tools for AI agents.

    Calls SAME command handlers as ViewModel.
    """

    def __init__(
        self,
        diffable: SQLiteDiffableAdapter,
        git: GitRepositoryAdapter,
        event_bus: EventBus,
        state: ProjectState,
    ) -> None:
        self._diffable = diffable
        self._git = git
        self._event_bus = event_bus
        self._state = state

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "list_snapshots",
                "description": "List version control snapshots (commits)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 20},
                    },
                },
            },
            {
                "name": "view_diff",
                "description": "View changes between two snapshots",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "from_ref": {"type": "string", "default": "HEAD~1"},
                        "to_ref": {"type": "string", "default": "HEAD"},
                    },
                },
            },
            {
                "name": "restore_snapshot",
                "description": "Restore database to previous state (destructive)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ref": {"type": "string"},
                    },
                    "required": ["ref"],
                },
            },
        ]

    def execute_list_snapshots(self, arguments: dict) -> dict:
        from src.contexts.projects.core.commandHandlers.list_snapshots import (
            list_snapshots,
        )

        result = list_snapshots(
            limit=arguments.get("limit", 20),
            git_adapter=self._git,
        )
        return result.to_dict()

    def execute_restore_snapshot(self, arguments: dict) -> dict:
        from src.contexts.projects.core.commandHandlers.restore_snapshot import (
            restore_snapshot,
        )
        from src.contexts.projects.core.vcs_commands import RestoreSnapshotCommand

        command = RestoreSnapshotCommand(
            project_path=str(self._state.project.path),
            ref=arguments["ref"],
        )

        result = restore_snapshot(
            command,
            self._diffable,
            self._git,
            self._event_bus,
        )
        return result.to_dict()
```

---

### Phase 7: Presentation Layer

**Files to create:**

| File | Responsibility |
|------|----------------|
| `src/contexts/projects/presentation/viewmodels/version_control_viewmodel.py` | UI state |
| `src/contexts/projects/presentation/pages/version_history_page.py` | Snapshot list |
| `src/contexts/projects/presentation/dialogs/diff_viewer_dialog.py` | Diff display |

---

### Phase 8: Wiring in main.py

```python
def _setup_version_control(self, project_path: Path) -> None:
    """Wire up version control components."""
    from src.contexts.projects.infra.git_repository_adapter import GitRepositoryAdapter
    from src.contexts.projects.infra.sqlite_diffable_adapter import SQLiteDiffableAdapter
    from src.contexts.projects.infra.version_control_listener import (
        VersionControlListener,
    )

    # Create adapters
    diffable = SQLiteDiffableAdapter()
    git = GitRepositoryAdapter(project_path)

    # Create listener
    self._vcs_listener = VersionControlListener(
        event_bus=self._ctx.event_bus,
        diffable_adapter=diffable,
        git_adapter=git,
        project_path=project_path,
    )

    # Enable if already initialized
    if git.is_initialized():
        self._vcs_listener.enable()
```

---

## File Summary

| Layer | Files | Count |
|-------|-------|-------|
| Infrastructure | adapters (2), listener (1) | 3 |
| Domain | invariants, entities, events, failure_events, derivers, commands | 6 |
| Command Handlers | auto_commit, restore, list, view_diff, initialize | 5 |
| Interface | vcs_mcp_tools | 1 |
| Presentation | viewmodel, page, dialog | 3 |
| SignalBridge | projects.py (additions) | 1 |
| **Total** | | **19** |

---

## Testing Strategy

### Unit Tests (Pure Domain)

```python
# test_vcs_derivers.py
class TestDeriveAutoCommit:
    def test_success_with_events(self):
        state = VersionControlState(is_initialized=True)
        events = (MockEvent("coding.code_created"),)
        result = derive_auto_commit(events, state)
        assert isinstance(result, SnapshotCreated)

    def test_skipped_when_not_initialized(self):
        state = VersionControlState(is_initialized=False)
        result = derive_auto_commit((), state)
        assert isinstance(result, AutoCommitSkipped)
        assert result.error_code == "AUTO_COMMIT_SKIPPED/NOT_INITIALIZED"
```

### Integration Tests (Adapters)

```python
# test_git_repository_adapter.py
class TestGitRepositoryAdapter:
    def test_init_creates_repo(self, tmp_path):
        adapter = GitRepositoryAdapter(tmp_path)
        result = adapter.init()
        assert result.is_success
        assert (tmp_path / ".git").exists()
```

### E2E Tests

```python
@allure.story("QC-047.02 Auto-commit on mutations")
class TestAutoCommit:

    @allure.title("AC #2: Every mutation auto-commits")
    def test_code_creation_triggers_commit(self, app_with_vcs):
        app_with_vcs.viewmodel.create_code("Theme A", "#FF0000")
        QTest.qWait(600)  # Wait for debounce

        log = app_with_vcs.git.log(limit=1)
        assert "coding" in log[0].message
```

---

## References

- **Task:** `backlog/tasks/qc-047 - SQLite-Database-Version-Control.md`
- **Decision:** `backlog/decisions/decision-006 sqlite-version-control-sqlite-diffable.md`
- **Guidelines:** `.github/copilot-instructions.md`
- **Developer Guide:** `.claude/skills/developer/SKILL.md`
