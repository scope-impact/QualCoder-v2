"""SQLite Diffable Adapter - Wrapper for sqlite-diffable CLI tool."""

from __future__ import annotations

import subprocess
from pathlib import Path

from src.shared.common.operation_result import OperationResult

VCS_DIR_NAME = ".qualcoder-vcs"

EXCLUDE_TABLES = (
    "sqlite_sequence",
    "source_fulltext_fts",
    "source_fulltext_data",
)


class SqliteDiffableAdapter:
    """Converts SQLite databases to/from Git-friendly JSON format."""

    def __init__(self, exclude_tables: tuple[str, ...] = EXCLUDE_TABLES) -> None:
        self._exclude_tables = exclude_tables

    def dump(self, db_path: Path, output_dir: Path) -> OperationResult:
        """Dump SQLite database to diffable JSON format."""
        db_path = Path(db_path).resolve()
        output_dir = Path(output_dir).resolve()

        if not db_path.exists():
            return OperationResult.fail(
                error=f"Database file not found: {db_path}",
                error_code="VCS_NOT_DUMPED/FILE_NOT_FOUND",
                suggestions=("Check the database path is correct",),
            )

        output_dir.mkdir(parents=True, exist_ok=True)

        cmd = ["sqlite-diffable", "dump", str(db_path), str(output_dir), "--all"]
        for table in self._exclude_tables:
            cmd.extend(["--exclude", table])

        return self._run_cli(cmd, "VCS_NOT_DUMPED")

    def load(self, db_path: Path, snapshot_dir: Path) -> OperationResult:
        """Load database from diffable JSON format."""
        db_path = Path(db_path).resolve()
        snapshot_dir = Path(snapshot_dir).resolve()

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

        cmd = ["sqlite-diffable", "load", str(db_path), str(snapshot_dir), "--replace"]
        return self._run_cli(cmd, "VCS_NOT_LOADED")

    def get_vcs_dir(self, project_path: Path) -> Path:
        """Get path to the .qualcoder-vcs directory."""
        project_path = Path(project_path).resolve()
        if project_path.is_file():
            return project_path.parent / VCS_DIR_NAME
        return project_path / VCS_DIR_NAME

    def _run_cli(self, cmd: list[str], error_prefix: str) -> OperationResult:
        """Run sqlite-diffable CLI command."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                return OperationResult.fail(
                    error=f"sqlite-diffable failed: {error_msg}",
                    error_code=f"{error_prefix}/CLI_ERROR",
                    suggestions=(
                        "Ensure sqlite-diffable is installed: pip install sqlite-diffable",
                    ),
                )
            return OperationResult.ok()
        except FileNotFoundError:
            return OperationResult.fail(
                error="sqlite-diffable command not found",
                error_code=f"{error_prefix}/CLI_NOT_FOUND",
                suggestions=("Install sqlite-diffable: pip install sqlite-diffable",),
            )
        except OSError as e:
            return OperationResult.fail(
                error=f"Failed to run sqlite-diffable: {e}",
                error_code=f"{error_prefix}/OS_ERROR",
            )
