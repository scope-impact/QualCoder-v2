"""Git Repository Adapter - Wrapper for Git CLI operations."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.shared.common.operation_result import OperationResult


@dataclass(frozen=True)
class CommitInfo:
    """Git commit metadata."""

    sha: str
    message: str
    author: str
    date: datetime

    @classmethod
    def from_git_log_line(cls, line: str) -> CommitInfo | None:
        """Parse from git log --format='%H|%an|%ct|%s' output."""
        parts = line.split("|", 3)
        if len(parts) < 4:
            return None

        sha, author, timestamp_str, message = parts
        try:
            date = datetime.fromtimestamp(int(timestamp_str), tz=UTC)
        except (ValueError, OSError):
            date = datetime.now(UTC)

        return cls(
            sha=sha.strip(), author=author.strip(), date=date, message=message.strip()
        )


class GitRepositoryAdapter:
    """Git CLI operations for version controlling project snapshots."""

    def __init__(self, repo_path: Path) -> None:
        self._repo_path = Path(repo_path).resolve()

    def is_initialized(self) -> bool:
        """Check if .git directory exists."""
        git_dir = self._repo_path / ".git"
        return git_dir.exists() and git_dir.is_dir()

    def init(self) -> OperationResult:
        """Initialize a new Git repository."""
        if self.is_initialized():
            return OperationResult.ok()
        return self._run_git(["init"], "GIT_NOT_INITIALIZED")

    def add_all(self, path: Path) -> OperationResult:
        """Stage all changes in a path for commit."""
        return self._run_git(["add", str(path)], "GIT_NOT_STAGED")

    def commit(self, message: str) -> OperationResult:
        """Create a commit with staged changes. Returns SHA on success."""
        if not message or not message.strip():
            return OperationResult.fail(
                error="Commit message cannot be empty",
                error_code="GIT_NOT_COMMITTED/EMPTY_MESSAGE",
            )

        result = self._run_git(
            ["commit", "-m", message], "GIT_NOT_COMMITTED", return_output=True
        )
        if result.is_failure:
            # Check for "nothing to commit" case
            if "nothing to commit" in (result.error or "").lower():
                return OperationResult.fail(
                    error="Nothing to commit - no changes staged",
                    error_code="GIT_NOT_COMMITTED/NOTHING_TO_COMMIT",
                )
            return result

        # Get the commit SHA
        sha_result = self._run_git(
            ["rev-parse", "HEAD"], "GIT_NOT_COMMITTED", return_output=True
        )
        return OperationResult.ok(
            data=sha_result.data.strip() if sha_result.data else ""
        )

    def log(self, limit: int = 20) -> OperationResult:
        """Get commit history as list of CommitInfo."""
        result = self._run_git(
            ["log", "--format=%H|%an|%ct|%s", f"-n{limit}"],
            "GIT_LOG_FAILED",
            return_output=True,
        )
        if result.is_failure:
            # Empty repo is not an error
            if "does not have any commits" in (result.error or "").lower():
                return OperationResult.ok(data=[])
            return result

        commits = [
            commit
            for line in (result.data or "").strip().split("\n")
            if line and (commit := CommitInfo.from_git_log_line(line))
        ]
        return OperationResult.ok(data=commits)

    def diff(self, from_ref: str, to_ref: str) -> OperationResult:
        """Get diff between two commits."""
        return self._run_git(
            ["diff", from_ref, to_ref], "GIT_DIFF_FAILED", return_output=True
        )

    def checkout(self, ref: str) -> OperationResult:
        """Checkout a specific commit. WARNING: Discards uncommitted changes."""
        return self._run_git(["checkout", ref], "GIT_CHECKOUT_FAILED")

    def get_valid_refs(self) -> OperationResult:
        """Get all valid commit SHAs."""
        result = self._run_git(
            ["rev-list", "--all"], "GIT_REFS_FAILED", return_output=True
        )
        if result.is_failure:
            # Empty repo is not an error
            if (
                "does not have any commits" in (result.error or "").lower()
                or not result.error
            ):
                return OperationResult.ok(data=())
            return result

        refs = tuple(
            line.strip() for line in (result.data or "").strip().split("\n") if line
        )
        return OperationResult.ok(data=refs)

    def has_staged_changes(self) -> OperationResult:
        """Check if there are staged changes ready to commit."""
        result = self._run_git(
            ["status", "--porcelain"], "GIT_STATUS_FAILED", return_output=True
        )
        if result.is_failure:
            return result

        # Porcelain format: XY filename (X = staged status)
        has_staged = any(
            line and len(line) >= 2 and line[0] in "AMDRC"
            for line in (result.data or "").strip().split("\n")
        )
        return OperationResult.ok(data=has_staged)

    def _run_git(
        self, args: list[str], error_prefix: str, *, return_output: bool = False
    ) -> OperationResult:
        """Run git command with standard error handling."""
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                return OperationResult.fail(
                    error=f"git {args[0]} failed: {error_msg}",
                    error_code=f"{error_prefix}/CLI_ERROR",
                )
            if return_output:
                return OperationResult.ok(data=result.stdout)
            return OperationResult.ok()
        except FileNotFoundError:
            return OperationResult.fail(
                error="git command not found",
                error_code=f"{error_prefix}/CLI_NOT_FOUND",
                suggestions=("Install Git: https://git-scm.com/downloads",),
            )
        except OSError as e:
            return OperationResult.fail(
                error=f"Failed to run git: {e}",
                error_code=f"{error_prefix}/OS_ERROR",
            )
