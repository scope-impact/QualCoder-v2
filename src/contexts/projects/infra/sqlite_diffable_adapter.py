"""
SQLite Diffable Adapter - Infrastructure Layer.

Wrapper for the sqlite-diffable CLI tool that converts SQLite databases
to a directory of JSON files suitable for Git version control.

Implements QC-047 Version Control infrastructure.

Usage:
    adapter = SqliteDiffableAdapter()
    result = adapter.dump(db_path, output_dir)
    if result.is_success:
        print("Database exported successfully")
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from src.shared.common.operation_result import OperationResult

# ============================================================
# Constants
# ============================================================

# Directory name for version control snapshots
VCS_DIR_NAME = ".qualcoder-vcs"

# Tables to exclude from version control
# These are either auto-generated or regenerable
EXCLUDE_TABLES = (
    "sqlite_sequence",  # Auto-increment tracking
    "source_fulltext_fts",  # FTS index (regenerable)
    "source_fulltext_data",  # FTS data (regenerable)
)


# ============================================================
# SQLite Diffable Adapter
# ============================================================


class SqliteDiffableAdapter:
    """
    Adapter for sqlite-diffable CLI tool.

    Provides dump and load operations to convert between SQLite databases
    and Git-friendly JSON format.

    This is a pure I/O adapter with no business logic.

    Example:
        adapter = SqliteDiffableAdapter()

        # Export database to diffable format
        result = adapter.dump(Path("project.qda"), Path(".qualcoder-vcs"))

        # Restore database from diffable format
        result = adapter.load(Path("project.qda"), Path(".qualcoder-vcs"))
    """

    def __init__(self, exclude_tables: tuple[str, ...] = EXCLUDE_TABLES) -> None:
        """
        Initialize the adapter.

        Args:
            exclude_tables: Tables to exclude from dump/load operations.
                           Defaults to EXCLUDE_TABLES constant.
        """
        self._exclude_tables = exclude_tables

    def dump(self, db_path: Path, output_dir: Path) -> OperationResult:
        """
        Dump SQLite database to diffable JSON format.

        Runs: sqlite-diffable dump <db_path> <output_dir> --all [--exclude ...]

        Args:
            db_path: Path to the SQLite database file
            output_dir: Directory to output JSON files

        Returns:
            OperationResult.ok() on success
            OperationResult.fail() with error details on failure
        """
        db_path = Path(db_path).resolve()
        output_dir = Path(output_dir).resolve()

        # Validate database exists
        if not db_path.exists():
            return OperationResult.fail(
                error=f"Database file not found: {db_path}",
                error_code="VCS_NOT_DUMPED/FILE_NOT_FOUND",
                suggestions=("Check the database path is correct",),
            )

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build command
        cmd = [
            "sqlite-diffable",
            "dump",
            str(db_path),
            str(output_dir),
            "--all",
        ]

        # Add exclude flags for each table
        for table in self._exclude_tables:
            cmd.extend(["--exclude", table])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                return OperationResult.fail(
                    error=f"sqlite-diffable dump failed: {error_msg}",
                    error_code="VCS_NOT_DUMPED/CLI_ERROR",
                    suggestions=(
                        "Ensure sqlite-diffable is installed: pip install sqlite-diffable",
                        "Check the database file is not corrupted",
                    ),
                )

            return OperationResult.ok()

        except FileNotFoundError:
            return OperationResult.fail(
                error="sqlite-diffable command not found",
                error_code="VCS_NOT_DUMPED/CLI_NOT_FOUND",
                suggestions=(
                    "Install sqlite-diffable: pip install sqlite-diffable",
                    "Ensure sqlite-diffable is in your PATH",
                ),
            )
        except OSError as e:
            return OperationResult.fail(
                error=f"Failed to run sqlite-diffable: {e}",
                error_code="VCS_NOT_DUMPED/OS_ERROR",
            )

    def load(self, db_path: Path, snapshot_dir: Path) -> OperationResult:
        """
        Load database from diffable JSON format.

        Runs: sqlite-diffable load <db_path> <snapshot_dir> --replace

        Args:
            db_path: Path to the target SQLite database file
            snapshot_dir: Directory containing JSON snapshot files

        Returns:
            OperationResult.ok() on success
            OperationResult.fail() with error details on failure
        """
        db_path = Path(db_path).resolve()
        snapshot_dir = Path(snapshot_dir).resolve()

        # Validate snapshot directory exists
        if not snapshot_dir.exists():
            return OperationResult.fail(
                error=f"Snapshot directory not found: {snapshot_dir}",
                error_code="VCS_NOT_LOADED/DIR_NOT_FOUND",
                suggestions=("Check the snapshot directory path is correct",),
            )

        if not snapshot_dir.is_dir():
            return OperationResult.fail(
                error=f"Snapshot path is not a directory: {snapshot_dir}",
                error_code="VCS_NOT_LOADED/NOT_A_DIRECTORY",
            )

        # Build command
        cmd = [
            "sqlite-diffable",
            "load",
            str(db_path),
            str(snapshot_dir),
            "--replace",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                return OperationResult.fail(
                    error=f"sqlite-diffable load failed: {error_msg}",
                    error_code="VCS_NOT_LOADED/CLI_ERROR",
                    suggestions=(
                        "Ensure sqlite-diffable is installed: pip install sqlite-diffable",
                        "Check the snapshot files are valid",
                    ),
                )

            return OperationResult.ok()

        except FileNotFoundError:
            return OperationResult.fail(
                error="sqlite-diffable command not found",
                error_code="VCS_NOT_LOADED/CLI_NOT_FOUND",
                suggestions=(
                    "Install sqlite-diffable: pip install sqlite-diffable",
                    "Ensure sqlite-diffable is in your PATH",
                ),
            )
        except OSError as e:
            return OperationResult.fail(
                error=f"Failed to run sqlite-diffable: {e}",
                error_code="VCS_NOT_LOADED/OS_ERROR",
            )

    def get_vcs_dir(self, project_path: Path) -> Path:
        """
        Get the path to the version control snapshot directory.

        The VCS directory is stored inside the project folder as .qualcoder-vcs/

        Args:
            project_path: Path to the project .qda file or directory

        Returns:
            Path to the .qualcoder-vcs directory
        """
        project_path = Path(project_path).resolve()

        # If project_path is a file (e.g., project.qda), use its parent
        if project_path.is_file():
            return project_path.parent / VCS_DIR_NAME

        # If it's a directory, use it directly
        return project_path / VCS_DIR_NAME
