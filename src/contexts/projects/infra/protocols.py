"""Infrastructure Protocols - Abstract interfaces for external adapters.

These protocols define the contract for external services (Git, sqlite-diffable).
Use for dependency injection in command handlers to enable:
- Unit testing with mocks
- Failure injection for error handling tests
- Alternative implementations (e.g., different VCS backends)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from src.shared.common.operation_result import OperationResult


class GitRepositoryProtocol(Protocol):
    """
    Protocol for Git repository operations.

    Allows mocking for unit tests and failure injection.
    """

    def is_initialized(self) -> bool:
        """Check if .git directory exists."""
        ...

    def init(self) -> OperationResult:
        """Initialize a new Git repository."""
        ...

    def add_all(self, path: Path) -> OperationResult:
        """Stage all changes in a path for commit."""
        ...

    def commit(self, message: str) -> OperationResult:
        """Create a commit with staged changes. Returns SHA on success."""
        ...

    def log(self, limit: int = 20) -> OperationResult:
        """Get commit history as list of CommitInfo."""
        ...

    def diff(self, from_ref: str, to_ref: str) -> OperationResult:
        """Get diff between two commits."""
        ...

    def checkout(self, ref: str) -> OperationResult:
        """Checkout a specific commit."""
        ...

    def get_valid_refs(self) -> OperationResult:
        """Get all valid commit SHAs."""
        ...

    def has_staged_changes(self) -> OperationResult:
        """Check if there are staged changes ready to commit."""
        ...


class SqliteDiffableProtocol(Protocol):
    """
    Protocol for SQLite diffable operations.

    Allows mocking for unit tests and failure injection.
    """

    def dump(self, db_path: Path, output_dir: Path) -> OperationResult:
        """Dump SQLite database to diffable JSON format."""
        ...

    def load(self, db_path: Path, snapshot_dir: Path) -> OperationResult:
        """Load database from diffable JSON format."""
        ...

    def get_vcs_dir(self, project_path: Path) -> Path:
        """Get path to the .qualcoder-vcs directory."""
        ...


__all__ = [
    "GitRepositoryProtocol",
    "SqliteDiffableProtocol",
]
