"""
Bounded Context Classes for QualCoder.

These classes bundle repositories for each bounded context.
They are created when a project is opened and cleared when it closes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy import Connection

    from src.contexts.projects.infra.project_repository import SQLiteProjectRepository
    from src.contexts.projects.infra.settings_repository import (
        SQLiteProjectSettingsRepository,
    )
    from src.shared.infra.repositories import (
        CaseRepositoryProtocol,
        CategoryRepositoryProtocol,
        CodeRepositoryProtocol,
        FolderRepositoryProtocol,
        SegmentRepositoryProtocol,
        SourceRepositoryProtocol,
    )


@dataclass
class SourcesContext:
    """
    Sources bounded context - manages source files.

    Provides access to:
    - SourceRepository: CRUD for source files
    """

    source_repo: SourceRepositoryProtocol

    @classmethod
    def create(
        cls,
        connection: Connection | None = None,
    ) -> SourcesContext:
        """Create a SourcesContext with all repositories."""
        if connection is None:
            raise ValueError("Connection required")
        from src.contexts.sources.infra.source_repository import (
            SQLiteSourceRepository,
        )

        return cls(
            source_repo=SQLiteSourceRepository(connection),
        )


@dataclass
class FoldersContext:
    """
    Folders bounded context - manages folder hierarchy for organizing sources.

    Provides access to:
    - FolderRepository: CRUD for folder hierarchy
    """

    folder_repo: FolderRepositoryProtocol

    @classmethod
    def create(
        cls,
        connection: Connection | None = None,
    ) -> FoldersContext:
        """Create a FoldersContext with all repositories."""
        if connection is None:
            raise ValueError("Connection required")
        from src.contexts.folders.infra.folder_repository import (
            SQLiteFolderRepository,
        )

        return cls(
            folder_repo=SQLiteFolderRepository(connection),
        )


@dataclass
class CasesContext:
    """
    Cases bounded context - manages research cases and attributes.

    Provides access to:
    - CaseRepository: CRUD for cases and their attributes
    """

    case_repo: CaseRepositoryProtocol

    @classmethod
    def create(
        cls,
        connection: Connection | None = None,
    ) -> CasesContext:
        """Create a CasesContext with all repositories."""
        if connection is None:
            raise ValueError("Connection required")
        from src.contexts.cases.infra.case_repository import SQLiteCaseRepository

        return cls(case_repo=SQLiteCaseRepository(connection))


@dataclass
class CodingContext:
    """
    Coding bounded context - manages codes, categories, and segments.

    Provides access to:
    - CodeRepository: CRUD for codes
    - CategoryRepository: CRUD for code categories
    - SegmentRepository: CRUD for coded text segments
    """

    code_repo: CodeRepositoryProtocol
    category_repo: CategoryRepositoryProtocol
    segment_repo: SegmentRepositoryProtocol

    @classmethod
    def create(
        cls,
        connection: Connection | None = None,
    ) -> CodingContext:
        """Create a CodingContext with all repositories."""
        if connection is None:
            raise ValueError("Connection required")
        from src.contexts.coding.infra.repositories import (
            SQLiteCategoryRepository,
            SQLiteCodeRepository,
            SQLiteSegmentRepository,
        )

        return cls(
            code_repo=SQLiteCodeRepository(connection),
            category_repo=SQLiteCategoryRepository(connection),
            segment_repo=SQLiteSegmentRepository(connection),
        )


@dataclass
class StorageContext:
    """
    Storage bounded context - manages S3 data store and DVC versioning.

    Provides access to:
    - StoreRepository: Persistence for DataStore config
    - S3Scanner: S3 file operations
    - DvcGateway: DVC version control for data
    """

    store_repo: Any  # StoreRepository protocol
    s3_scanner: Any  # S3ScannerProtocol
    dvc_gateway: Any  # DvcGatewayProtocol

    @classmethod
    def create(
        cls,
        connection: Connection | None = None,
        project_path: str | None = None,
    ) -> StorageContext:
        """Create a StorageContext with all repositories and gateways."""
        if connection is None:
            raise ValueError("Connection required")
        from src.contexts.storage.infra.store_repository import SQLiteStoreRepository

        store_repo = SQLiteStoreRepository(connection)

        # Create S3 scanner (boto3 client created lazily on first use)
        s3_scanner = _create_s3_scanner()

        # Create DVC gateway (needs project working directory)
        dvc_gateway = _create_dvc_gateway(project_path)

        return cls(
            store_repo=store_repo,
            s3_scanner=s3_scanner,
            dvc_gateway=dvc_gateway,
        )


def _create_s3_scanner() -> Any:
    """Create an S3Scanner with a lazy boto3 client."""
    try:
        import boto3

        client = boto3.client("s3")
    except Exception:
        # S3 not available (offline mode) — return a no-op scanner
        client = None

    if client is None:
        return _NullS3Scanner()

    from src.contexts.storage.infra.s3_scanner import S3Scanner

    return S3Scanner(client)


def _create_dvc_gateway(project_path: str | None) -> Any:
    """Create a DvcGateway for the project directory."""
    if project_path is None:
        return _NullDvcGateway()

    from pathlib import Path

    from src.contexts.storage.infra.dvc_gateway import DvcGateway

    return DvcGateway(str(Path(project_path).parent))


class _NullS3Scanner:
    """Null object for S3Scanner when boto3 is not available."""

    def list_files(self, bucket: str, prefix: str = "") -> list:
        return []

    def download_file(self, bucket: str, key: str, local_path: str) -> None:
        raise RuntimeError("S3 not available — check AWS credentials and boto3 installation")

    def upload_file(self, bucket: str, key: str, local_path: str) -> None:
        raise RuntimeError("S3 not available — check AWS credentials and boto3 installation")


class _NullDvcGateway:
    """Null object for DvcGateway when project path is not available."""

    from dataclasses import dataclass as _dc

    @_dc(frozen=True)
    class _Result:
        success: bool = False
        message: str = "DVC not available — no project path"
        transferred: int = 0

    def init(self):
        return self._Result()

    def remote_add(self, name, url):
        return self._Result()

    def remote_modify(self, name, key, value):
        return self._Result()

    def remote_default(self, name):
        return self._Result()

    def add(self, path):
        return self._Result()

    def push(self, remote=None):
        return self._Result()

    def pull(self, remote=None):
        return self._Result()

    def status(self, remote=None):
        return self._Result()

    @staticmethod
    def s3_url(bucket, prefix=""):
        if prefix:
            return f"s3://{bucket}/{prefix.strip('/')}"
        return f"s3://{bucket}"


@dataclass
class ProjectsContext:
    """
    Projects bounded context - manages project metadata and settings.

    Provides access to:
    - ProjectRepository: Project creation, validation, loading
    - SettingsRepository: Project-level settings
    - GitAdapter: Git repository operations (for VCS)
    - DiffableAdapter: SQLite to JSON conversion (for VCS)
    """

    project_repo: SQLiteProjectRepository | Any
    settings_repo: SQLiteProjectSettingsRepository | Any
    git_adapter: Any | None = None  # GitRepositoryAdapter
    diffable_adapter: Any | None = None  # SqliteDiffableAdapter

    @classmethod
    def create(
        cls,
        connection: Connection | None = None,
        project_path: str | None = None,
    ) -> ProjectsContext:
        """Create a ProjectsContext with all repositories."""
        if connection is None:
            raise ValueError("SQLAlchemy connection required for project management")

        from pathlib import Path

        from src.contexts.projects.infra.git_repository_adapter import (
            GitRepositoryAdapter,
        )
        from src.contexts.projects.infra.project_repository import (
            SQLiteProjectRepository,
        )
        from src.contexts.projects.infra.settings_repository import (
            SQLiteProjectSettingsRepository,
        )
        from src.contexts.projects.infra.sqlite_diffable_adapter import (
            SqliteDiffableAdapter,
        )

        # Create VCS adapters if project path is provided
        git_adapter = None
        diffable_adapter = None
        if project_path:
            project_dir = Path(project_path).parent
            git_adapter = GitRepositoryAdapter(project_dir)
            diffable_adapter = SqliteDiffableAdapter()

        return cls(
            project_repo=SQLiteProjectRepository(connection),
            settings_repo=SQLiteProjectSettingsRepository(connection),
            git_adapter=git_adapter,
            diffable_adapter=diffable_adapter,
        )
