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

        try:
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                if "nothing to commit" in error_msg.lower():
                    return OperationResult.fail(
                        error="Nothing to commit - no changes staged",
                        error_code="GIT_NOT_COMMITTED/NOTHING_TO_COMMIT",
                    )
                return OperationResult.fail(
                    error=f"git commit failed: {error_msg}",
                    error_code="GIT_NOT_COMMITTED/CLI_ERROR",
                )

            sha_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            sha = sha_result.stdout.strip() if sha_result.returncode == 0 else ""
            return OperationResult.ok(data=sha)

        except FileNotFoundError:
            return OperationResult.fail(
                error="git command not found",
                error_code="GIT_NOT_COMMITTED/CLI_NOT_FOUND",
                suggestions=("Install Git: https://git-scm.com/downloads",),
            )
        except OSError as e:
            return OperationResult.fail(
                error=f"Failed to run git: {e}",
                error_code="GIT_NOT_COMMITTED/OS_ERROR",
            )

    def log(self, limit: int = 20) -> OperationResult:
        """Get commit history as list of CommitInfo."""
        try:
            result = subprocess.run(
                ["git", "log", "--format=%H|%an|%ct|%s", f"-n{limit}"],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                if "does not have any commits yet" in error_msg.lower():
                    return OperationResult.ok(data=[])
                return OperationResult.fail(
                    error=f"git log failed: {error_msg}",
                    error_code="GIT_LOG_FAILED/CLI_ERROR",
                )

            commits = [
                commit
                for line in result.stdout.strip().split("\n")
                if line and (commit := CommitInfo.from_git_log_line(line))
            ]
            return OperationResult.ok(data=commits)

        except FileNotFoundError:
            return OperationResult.fail(
                error="git command not found",
                error_code="GIT_LOG_FAILED/CLI_NOT_FOUND",
                suggestions=("Install Git: https://git-scm.com/downloads",),
            )
        except OSError as e:
            return OperationResult.fail(
                error=f"Failed to run git: {e}",
                error_code="GIT_LOG_FAILED/OS_ERROR",
            )

    def diff(self, from_ref: str, to_ref: str) -> OperationResult:
        """Get diff between two commits."""
        valid_refs = self.get_valid_refs()
        if valid_refs.is_failure:
            return valid_refs

        result = self._run_git(["diff", from_ref, to_ref], "GIT_DIFF_FAILED")
        if result.is_failure:
            return result

        # _run_git doesn't capture output for data, so run directly
        try:
            proc = subprocess.run(
                ["git", "diff", from_ref, to_ref],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode != 0:
                return OperationResult.fail(
                    error=f"git diff failed: {proc.stderr.strip()}",
                    error_code="GIT_DIFF_FAILED/CLI_ERROR",
                )
            return OperationResult.ok(data=proc.stdout)
        except (FileNotFoundError, OSError) as e:
            return OperationResult.fail(
                error=f"git diff failed: {e}",
                error_code="GIT_DIFF_FAILED/CLI_ERROR",
            )

    def checkout(self, ref: str) -> OperationResult:
        """Checkout a specific commit. WARNING: Discards uncommitted changes."""
        return self._run_git(["checkout", ref], "GIT_CHECKOUT_FAILED")

    def get_valid_refs(self) -> OperationResult:
        """Get all valid commit SHAs."""
        try:
            result = subprocess.run(
                ["git", "rev-list", "--all"],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                if not error_msg or "does not have any commits" in error_msg.lower():
                    return OperationResult.ok(data=())
                return OperationResult.fail(
                    error=f"git rev-list failed: {error_msg}",
                    error_code="GIT_REFS_FAILED/CLI_ERROR",
                )

            refs = tuple(
                line.strip() for line in result.stdout.strip().split("\n") if line
            )
            return OperationResult.ok(data=refs)

        except FileNotFoundError:
            return OperationResult.fail(
                error="git command not found",
                error_code="GIT_REFS_FAILED/CLI_NOT_FOUND",
                suggestions=("Install Git: https://git-scm.com/downloads",),
            )
        except OSError as e:
            return OperationResult.fail(
                error=f"Failed to run git: {e}",
                error_code="GIT_REFS_FAILED/OS_ERROR",
            )

    def has_staged_changes(self) -> OperationResult:
        """Check if there are staged changes ready to commit."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                return OperationResult.fail(
                    error=f"git status failed: {result.stderr.strip()}",
                    error_code="GIT_STATUS_FAILED/CLI_ERROR",
                )

            # Porcelain format: XY filename (X = staged status)
            has_staged = any(
                line and len(line) >= 2 and line[0] in "AMDRC"
                for line in result.stdout.strip().split("\n")
            )
            return OperationResult.ok(data=has_staged)

        except FileNotFoundError:
            return OperationResult.fail(
                error="git command not found",
                error_code="GIT_STATUS_FAILED/CLI_NOT_FOUND",
                suggestions=("Install Git: https://git-scm.com/downloads",),
            )
        except OSError as e:
            return OperationResult.fail(
                error=f"Failed to run git: {e}",
                error_code="GIT_STATUS_FAILED/OS_ERROR",
            )

    def _run_git(self, args: list[str], error_prefix: str) -> OperationResult:
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
                return OperationResult.fail(
                    error=f"git {args[0]} failed: {result.stderr.strip() or result.stdout.strip()}",
                    error_code=f"{error_prefix}/CLI_ERROR",
                )
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
