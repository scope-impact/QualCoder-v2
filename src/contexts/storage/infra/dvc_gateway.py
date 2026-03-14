"""
Storage Infrastructure: DVC Gateway

Uses dvc.repo.Repo Python API for data versioning with S3 remote.
Assumes `dvc` pip package is installed and the project is a Git repo.

Repo class supports context manager (``with Repo(path) as repo``),
push() returns int (transferred count), pull() returns dict with stats.
See: https://github.com/iterative/dvc/blob/main/dvc/repo/__init__.py
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("qualcoder.storage.infra")


@dataclass(frozen=True)
class DvcResult:
    """Result of a DVC operation."""

    success: bool
    message: str = ""
    transferred: int = 0


class DvcGateway:
    """
    Gateway to DVC Python API for data versioning with S3 remotes.

    Uses dvc.repo.Repo internally — the same API the DVC CLI uses.
    Supports context manager for automatic resource cleanup.
    """

    def __init__(self, working_dir: str) -> None:
        self._cwd = working_dir
        self._repo = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _get_repo(self):
        """Lazy-load DVC Repo to avoid import cost at startup."""
        if self._repo is None:
            from dvc.repo import Repo

            self._repo = Repo(self._cwd)
        return self._repo

    def init(self) -> DvcResult:
        """Initialize DVC in the project (idempotent)."""
        try:
            from dvc.repo import Repo

            Repo.init(self._cwd, no_scm=True)
            self._repo = None  # Reset so next _get_repo picks up new init
            return DvcResult(success=True, message="DVC initialized")
        except Exception as e:
            # Already initialized is not an error
            if "already initialized" in str(e).lower():
                return DvcResult(success=True, message="DVC already initialized")
            logger.exception("dvc init failed")
            return DvcResult(success=False, message=str(e))

    def remote_add(self, name: str, url: str) -> DvcResult:
        """Add a DVC remote (S3 URL). Overwrites if exists."""
        try:
            repo = self._get_repo()
            with repo.config.edit() as conf:
                conf.setdefault("remote", {})[name] = {"url": url}
            return DvcResult(success=True, message=f"Remote '{name}' set to {url}")
        except Exception as e:
            logger.exception("dvc remote add failed")
            return DvcResult(success=False, message=str(e))

    def remote_modify(self, name: str, key: str, value: str) -> DvcResult:
        """Modify a DVC remote setting (e.g., region, profile)."""
        try:
            repo = self._get_repo()
            with repo.config.edit() as conf:
                remote = conf.get("remote", {}).get(name, {})
                remote[key] = value
                conf.setdefault("remote", {})[name] = remote
            return DvcResult(success=True, message=f"Remote '{name}' {key}={value}")
        except Exception as e:
            logger.exception("dvc remote modify failed")
            return DvcResult(success=False, message=str(e))

    def remote_default(self, name: str) -> DvcResult:
        """Set the default DVC remote."""
        try:
            repo = self._get_repo()
            with repo.config.edit() as conf:
                conf["core"] = conf.get("core", {})
                conf["core"]["remote"] = name
            return DvcResult(success=True, message=f"Default remote set to '{name}'")
        except Exception as e:
            logger.exception("dvc remote default failed")
            return DvcResult(success=False, message=str(e))

    def add(self, path: str) -> DvcResult:
        """Track a file/directory with DVC (creates .dvc file)."""
        try:
            repo = self._get_repo()
            repo.add(path)
            return DvcResult(success=True, message=f"Tracked: {path}")
        except Exception as e:
            logger.exception("dvc add failed for %s", path)
            return DvcResult(success=False, message=str(e))

    def push(self, remote: str | None = None) -> DvcResult:
        """Push tracked data to remote storage. Returns transferred count."""
        try:
            repo = self._get_repo()
            kwargs = {}
            if remote:
                kwargs["remote"] = remote
            count = repo.push(**kwargs)
            return DvcResult(
                success=True,
                message=f"Pushed {count} file(s)",
                transferred=count if isinstance(count, int) else 0,
            )
        except Exception as e:
            logger.exception("dvc push failed")
            return DvcResult(success=False, message=str(e))

    def pull(self, remote: str | None = None) -> DvcResult:
        """Pull tracked data from remote storage. DVC handles sync internally."""
        try:
            repo = self._get_repo()
            kwargs = {}
            if remote:
                kwargs["remote"] = remote
            result = repo.pull(**kwargs)
            # pull() returns dict with "stats" key containing fetched count
            fetched = 0
            if isinstance(result, dict):
                fetched = result.get("fetched", 0)
            return DvcResult(
                success=True,
                message=f"Pulled (fetched {fetched})",
                transferred=fetched if isinstance(fetched, int) else 0,
            )
        except Exception as e:
            logger.exception("dvc pull failed")
            return DvcResult(success=False, message=str(e))

    def status(self, remote: str | None = None) -> DvcResult:
        """Show changed/new files vs remote or cache."""
        try:
            repo = self._get_repo()
            kwargs = {}
            if remote:
                kwargs["remote"] = remote
            result = repo.status(**kwargs)
            return DvcResult(success=True, message=str(result))
        except Exception as e:
            logger.exception("dvc status failed")
            return DvcResult(success=False, message=str(e))

    def close(self) -> None:
        """Close the DVC repo to release SCM, state, and filesystem resources."""
        if self._repo is not None:
            self._repo.close()
            self._repo = None

    @staticmethod
    def s3_url(bucket: str, prefix: str = "") -> str:
        """Build an S3 URL for DVC remote config."""
        if prefix:
            prefix = prefix.strip("/")
            return f"s3://{bucket}/{prefix}"
        return f"s3://{bucket}"
