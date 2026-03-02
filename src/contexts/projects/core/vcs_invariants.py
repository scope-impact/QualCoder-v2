"""Version Control Invariants - Pure validation predicates for business rules."""

from __future__ import annotations

from pathlib import Path


def is_valid_snapshot_message(message: str) -> bool:
    """
    Validate a commit message.

    Valid if:
    - Non-empty
    - Not whitespace-only
    - <= 500 characters

    Args:
        message: The commit message to validate

    Returns:
        True if the message is valid
    """
    if not message:
        return False
    stripped = message.strip()
    return bool(stripped) and len(stripped) <= 500


def is_valid_git_ref(ref: str, valid_refs: tuple[str, ...]) -> bool:
    """
    Validate a git reference.

    Valid if:
    - HEAD or HEAD~N syntax (e.g., "HEAD", "HEAD~1", "HEAD~10")
    - Matches a known commit SHA from valid_refs

    Args:
        ref: The git reference to validate
        valid_refs: Tuple of known valid commit SHAs

    Returns:
        True if the ref is valid
    """
    if not ref:
        return False
    # HEAD or HEAD~N syntax is always valid
    if ref.startswith("HEAD"):
        return True
    # Otherwise, must be a known SHA
    return ref in valid_refs


def resolve_project_dir(project_path: Path) -> Path:
    """
    Resolve the project directory where VCS operations (git, .gitignore) occur.

    For v2 format (.qda directory): returns the directory itself.
    For v1 format (.qda file): returns the parent directory.

    Args:
        project_path: Path to the .qda project (directory or file)

    Returns:
        Path to the directory where git should operate
    """
    project_path = Path(project_path).resolve()
    if project_path.is_dir():
        return project_path
    return project_path.parent


def resolve_db_path(project_path: Path, db_filename: str = "qualcoder.db") -> Path:
    """
    Resolve a project path to the actual database file path.

    For v2 format (.qda directory): returns directory / db_filename.
    For v1 format (.qda file): returns the file itself (it IS the database).

    Args:
        project_path: Path to the .qda project (directory or file)
        db_filename: Name of the database file within the project directory

    Returns:
        Path to the database file
    """
    project_path = Path(project_path).resolve()
    if project_path.is_dir():
        return project_path / db_filename
    return project_path


__all__ = [
    "is_valid_snapshot_message",
    "is_valid_git_ref",
    "resolve_db_path",
    "resolve_project_dir",
]
