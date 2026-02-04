"""
Git Repository Adapter - Infrastructure Layer.

Wrapper for Git CLI operations to manage version control of project snapshots.

Implements QC-047 Version Control infrastructure.

Usage:
    adapter = GitRepositoryAdapter(repo_path=Path("/path/to/project"))

    # Initialize repository
    if not adapter.is_initialized():
        adapter.init()

    # Commit changes
    adapter.add_all(Path(".qualcoder-vcs"))
    adapter.commit("Created 2 codes, applied 1 segment")

    # View history
    commits = adapter.log(limit=10)
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.shared.common.operation_result import OperationResult

# ============================================================
# Data Types
# ============================================================


@dataclass(frozen=True)
class CommitInfo:
    """
    Information about a Git commit.

    Immutable value object representing commit metadata.
    """

    sha: str
    message: str
    author: str
    date: datetime

    @classmethod
    def from_git_log_line(cls, line: str) -> CommitInfo | None:
        """
        Parse a CommitInfo from git log --format output.

        Expected format: sha|author|timestamp|message

        Args:
            line: Single line from git log output

        Returns:
            CommitInfo or None if parsing fails
        """
        parts = line.split("|", 3)
        if len(parts) < 4:
            return None

        sha, author, timestamp_str, message = parts

        try:
            # Git timestamp format: Unix epoch
            timestamp = int(timestamp_str)
            date = datetime.fromtimestamp(timestamp, tz=UTC)
        except (ValueError, OSError):
            date = datetime.now(UTC)

        return cls(
            sha=sha.strip(),
            author=author.strip(),
            date=date,
            message=message.strip(),
        )


# ============================================================
# Git Repository Adapter
# ============================================================


class GitRepositoryAdapter:
    """
    Adapter for Git CLI operations.

    Provides Git operations for version controlling project snapshots.
    All operations work within the configured repository path.

    This is a pure I/O adapter with no business logic.

    Example:
        adapter = GitRepositoryAdapter(repo_path=Path("/project"))

        # Initialize if needed
        if not adapter.is_initialized():
            adapter.init()

        # Stage and commit
        adapter.add_all(Path(".qualcoder-vcs"))
        result = adapter.commit("Initial snapshot")
        if result.is_success:
            print(f"Committed: {result.data}")
    """

    def __init__(self, repo_path: Path) -> None:
        """
        Initialize the adapter.

        Args:
            repo_path: Path to the Git repository root
        """
        self._repo_path = Path(repo_path).resolve()

    def is_initialized(self) -> bool:
        """
        Check if the repository is initialized.

        Returns:
            True if .git directory exists, False otherwise
        """
        git_dir = self._repo_path / ".git"
        return git_dir.exists() and git_dir.is_dir()

    def init(self) -> OperationResult:
        """
        Initialize a new Git repository.

        Runs: git init

        Returns:
            OperationResult.ok() on success
            OperationResult.fail() with error details on failure
        """
        if self.is_initialized():
            return OperationResult.ok()  # Already initialized

        try:
            result = subprocess.run(
                ["git", "init"],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                return OperationResult.fail(
                    error=f"git init failed: {error_msg}",
                    error_code="GIT_NOT_INITIALIZED/CLI_ERROR",
                )

            return OperationResult.ok()

        except FileNotFoundError:
            return OperationResult.fail(
                error="git command not found",
                error_code="GIT_NOT_INITIALIZED/CLI_NOT_FOUND",
                suggestions=(
                    "Install Git: https://git-scm.com/downloads",
                    "Ensure git is in your PATH",
                ),
            )
        except OSError as e:
            return OperationResult.fail(
                error=f"Failed to run git: {e}",
                error_code="GIT_NOT_INITIALIZED/OS_ERROR",
            )

    def add_all(self, path: Path) -> OperationResult:
        """
        Stage all changes in a path for commit.

        Runs: git add <path>

        Args:
            path: Path (relative to repo root) to stage

        Returns:
            OperationResult.ok() on success
            OperationResult.fail() with error details on failure
        """
        try:
            result = subprocess.run(
                ["git", "add", str(path)],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                return OperationResult.fail(
                    error=f"git add failed: {error_msg}",
                    error_code="GIT_NOT_STAGED/CLI_ERROR",
                )

            return OperationResult.ok()

        except FileNotFoundError:
            return OperationResult.fail(
                error="git command not found",
                error_code="GIT_NOT_STAGED/CLI_NOT_FOUND",
                suggestions=("Install Git: https://git-scm.com/downloads",),
            )
        except OSError as e:
            return OperationResult.fail(
                error=f"Failed to run git: {e}",
                error_code="GIT_NOT_STAGED/OS_ERROR",
            )

    def commit(self, message: str) -> OperationResult:
        """
        Create a commit with the staged changes.

        Runs: git commit -m <message>

        Args:
            message: Commit message

        Returns:
            OperationResult.ok(data=sha) with commit SHA on success
            OperationResult.fail() with error details on failure
        """
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

                # Check for "nothing to commit" case
                if "nothing to commit" in error_msg.lower():
                    return OperationResult.fail(
                        error="Nothing to commit - no changes staged",
                        error_code="GIT_NOT_COMMITTED/NOTHING_TO_COMMIT",
                    )

                return OperationResult.fail(
                    error=f"git commit failed: {error_msg}",
                    error_code="GIT_NOT_COMMITTED/CLI_ERROR",
                )

            # Get the commit SHA
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
        """
        Get commit history.

        Runs: git log --format='%H|%an|%ct|%s' -n <limit>

        Args:
            limit: Maximum number of commits to return

        Returns:
            OperationResult.ok(data=list[CommitInfo]) on success
            OperationResult.fail() with error details on failure
        """
        try:
            result = subprocess.run(
                [
                    "git",
                    "log",
                    "--format=%H|%an|%ct|%s",
                    f"-n{limit}",
                ],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()

                # Check for empty repository case
                if "does not have any commits yet" in error_msg.lower():
                    return OperationResult.ok(data=[])

                return OperationResult.fail(
                    error=f"git log failed: {error_msg}",
                    error_code="GIT_LOG_FAILED/CLI_ERROR",
                )

            # Parse output into CommitInfo objects
            commits: list[CommitInfo] = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    commit = CommitInfo.from_git_log_line(line)
                    if commit:
                        commits.append(commit)

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
        """
        Get diff between two commits.

        Runs: git diff <from_ref> <to_ref>

        Args:
            from_ref: Starting commit reference (SHA, branch, tag, HEAD~n)
            to_ref: Ending commit reference

        Returns:
            OperationResult.ok(data=diff_text) on success
            OperationResult.fail() with error details on failure
        """
        # Validate refs
        valid_refs = self.get_valid_refs()
        if valid_refs.is_failure:
            return valid_refs

        try:
            result = subprocess.run(
                ["git", "diff", from_ref, to_ref],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                return OperationResult.fail(
                    error=f"git diff failed: {error_msg}",
                    error_code="GIT_DIFF_FAILED/CLI_ERROR",
                    suggestions=(
                        f"Check that '{from_ref}' is a valid reference",
                        f"Check that '{to_ref}' is a valid reference",
                    ),
                )

            return OperationResult.ok(data=result.stdout)

        except FileNotFoundError:
            return OperationResult.fail(
                error="git command not found",
                error_code="GIT_DIFF_FAILED/CLI_NOT_FOUND",
                suggestions=("Install Git: https://git-scm.com/downloads",),
            )
        except OSError as e:
            return OperationResult.fail(
                error=f"Failed to run git: {e}",
                error_code="GIT_DIFF_FAILED/OS_ERROR",
            )

    def checkout(self, ref: str) -> OperationResult:
        """
        Checkout a specific commit or branch.

        Runs: git checkout <ref>

        WARNING: This discards uncommitted changes in the working directory.

        Args:
            ref: Commit reference to checkout (SHA, branch, tag)

        Returns:
            OperationResult.ok() on success
            OperationResult.fail() with error details on failure
        """
        try:
            result = subprocess.run(
                ["git", "checkout", ref],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                return OperationResult.fail(
                    error=f"git checkout failed: {error_msg}",
                    error_code="GIT_CHECKOUT_FAILED/CLI_ERROR",
                    suggestions=(
                        f"Check that '{ref}' is a valid reference",
                        "Ensure there are no uncommitted changes",
                    ),
                )

            return OperationResult.ok()

        except FileNotFoundError:
            return OperationResult.fail(
                error="git command not found",
                error_code="GIT_CHECKOUT_FAILED/CLI_NOT_FOUND",
                suggestions=("Install Git: https://git-scm.com/downloads",),
            )
        except OSError as e:
            return OperationResult.fail(
                error=f"Failed to run git: {e}",
                error_code="GIT_CHECKOUT_FAILED/OS_ERROR",
            )

    def get_valid_refs(self) -> OperationResult:
        """
        Get all valid commit references (SHAs).

        Runs: git rev-list --all

        Returns:
            OperationResult.ok(data=tuple[str, ...]) with all commit SHAs
            OperationResult.fail() with error details on failure
        """
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

                # Empty repository case
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
        """
        Check if there are staged changes ready to commit.

        Runs: git status --porcelain

        Returns:
            OperationResult.ok(data=True) if there are staged changes
            OperationResult.ok(data=False) if no staged changes
            OperationResult.fail() with error details on failure
        """
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                return OperationResult.fail(
                    error=f"git status failed: {error_msg}",
                    error_code="GIT_STATUS_FAILED/CLI_ERROR",
                )

            # Check for staged changes (lines starting with A, M, D, R, C)
            # Porcelain format: XY filename
            # X = staged status, Y = working tree status
            has_staged = False
            for line in result.stdout.strip().split("\n"):
                if line and len(line) >= 2:
                    staged_status = line[0]
                    if staged_status in "AMDRC":
                        has_staged = True
                        break

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
