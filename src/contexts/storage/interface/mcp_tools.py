"""
MCP Storage Tools

Provides MCP-compatible tools for AI agent interaction with S3 data stores.

Implements:
- QC-047.01: Configure S3 bucket via MCP
- QC-047.02: Scan/browse S3 files via MCP
- QC-047.03: Pull file from S3 via MCP
- QC-047.04: Push coded exports to S3 via MCP
- QC-047.06: Export and push combo via MCP
- QC-047.07: Scan and auto-import via MCP
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from returns.result import Failure, Result, Success

from src.shared.common.mcp_types import ToolDefinition, ToolParameter

if TYPE_CHECKING:
    from src.shared.infra.state import ProjectState


@runtime_checkable
class StorageToolsContext(Protocol):
    """Protocol defining context requirements for StorageTools."""

    @property
    def state(self) -> ProjectState: ...

    @property
    def event_bus(self): ...

    @property
    def storage_context(self): ...


# ============================================================
# Tool Definitions
# ============================================================

configure_datastore_tool = ToolDefinition(
    name="configure_datastore",
    description=(
        "Configure an S3 bucket as the project's data store. "
        "Sets up DVC remote for version-controlled data management. "
        "Required before any scan/pull/push operations."
    ),
    parameters=(
        ToolParameter(
            name="bucket_name",
            type="string",
            description="S3 bucket name (e.g., 'my-research-data').",
            required=True,
        ),
        ToolParameter(
            name="region",
            type="string",
            description="AWS region (e.g., 'us-east-1').",
            required=True,
        ),
        ToolParameter(
            name="prefix",
            type="string",
            description="S3 key prefix to scope store to a subfolder. Default empty.",
            required=False,
            default="",
        ),
        ToolParameter(
            name="dvc_remote_name",
            type="string",
            description="DVC remote name. Default 'origin'.",
            required=False,
            default="origin",
        ),
    ),
)

scan_datastore_tool = ToolDefinition(
    name="scan_datastore",
    description=(
        "List files in the configured S3 data store. "
        "Optionally filter by prefix. Returns file metadata "
        "(key, size, last modified)."
    ),
    parameters=(
        ToolParameter(
            name="prefix",
            type="string",
            description="S3 key prefix to filter files. Default: use store prefix.",
            required=False,
            default="",
        ),
    ),
)

pull_source_tool = ToolDefinition(
    name="pull_source",
    description=(
        "Pull a file from the S3 data store to the local project via DVC. "
        "The file is tracked by DVC for version control."
    ),
    parameters=(
        ToolParameter(
            name="key",
            type="string",
            description="S3 object key of the file to pull.",
            required=True,
        ),
        ToolParameter(
            name="local_path",
            type="string",
            description="Local filesystem path where the file should be saved.",
            required=True,
        ),
    ),
)

push_results_tool = ToolDefinition(
    name="push_results",
    description=(
        "Push a local file (coded export, analysis results) to the S3 data store "
        "via DVC. The file is tracked and versioned."
    ),
    parameters=(
        ToolParameter(
            name="local_path",
            type="string",
            description="Path to the local file to push.",
            required=True,
        ),
        ToolParameter(
            name="destination_key",
            type="string",
            description="S3 key where the file should be stored.",
            required=True,
        ),
    ),
)

export_and_push_tool = ToolDefinition(
    name="export_and_push",
    description=(
        "Export project data in a specified format and push to S3. "
        "Supported formats: qdpx, codebook, sqlite, html."
    ),
    parameters=(
        ToolParameter(
            name="export_format",
            type="string",
            description="Export format: 'qdpx', 'codebook', 'sqlite', or 'html'.",
            required=True,
        ),
        ToolParameter(
            name="destination_key",
            type="string",
            description="S3 key where the exported file should be stored.",
            required=True,
        ),
    ),
)

scan_and_import_tool = ToolDefinition(
    name="scan_and_import",
    description=(
        "Pull a file from S3 and auto-import it based on file extension. "
        "Supports: .qdpx, .rqda, .csv, .txt, .db, .sqlite formats."
    ),
    parameters=(
        ToolParameter(
            name="key",
            type="string",
            description="S3 object key of the file to import.",
            required=True,
        ),
    ),
)

ALL_STORAGE_TOOLS = {
    "configure_datastore": configure_datastore_tool,
    "scan_datastore": scan_datastore_tool,
    "pull_source": pull_source_tool,
    "push_results": push_results_tool,
    "export_and_push": export_and_push_tool,
    "scan_and_import": scan_and_import_tool,
}


# ============================================================
# Tool Implementation
# ============================================================


class StorageTools:
    """MCP-compatible storage tools for AI agent integration."""

    def __init__(self, ctx: StorageToolsContext) -> None:
        self._ctx = ctx
        self._tools = ALL_STORAGE_TOOLS
        self._handlers = {
            "configure_datastore": self._execute_configure_datastore,
            "scan_datastore": self._execute_scan_datastore,
            "pull_source": self._execute_pull_source,
            "push_results": self._execute_push_results,
            "export_and_push": self._execute_export_and_push,
            "scan_and_import": self._execute_scan_and_import,
        }

    @property
    def _storage_ctx(self):
        return self._ctx.storage_context

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        return [tool.to_schema() for tool in self._tools.values()]

    def get_tool_names(self) -> list[str]:
        return list(self._tools.keys())

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> Result:
        handler = self._handlers.get(tool_name)
        if handler is None:
            return Failure(f"Unknown tool: {tool_name}")
        try:
            return handler(arguments)
        except Exception as e:
            return Failure(f"Tool execution error: {e!s}")

    # ── Handlers ──────────────────────────────────────────────

    def _execute_configure_datastore(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        from src.contexts.storage.core.commandHandlers.configure_store import (
            configure_store,
        )
        from src.contexts.storage.core.commands import ConfigureStoreCommand

        bucket_name = arguments.get("bucket_name")
        region = arguments.get("region")
        if not bucket_name:
            return Failure("Missing required parameter: bucket_name")
        if not region:
            return Failure("Missing required parameter: region")

        storage_ctx = self._storage_ctx
        if not storage_ctx:
            return Failure("No project open")

        command = ConfigureStoreCommand(
            bucket_name=bucket_name,
            region=region,
            prefix=arguments.get("prefix", ""),
            dvc_remote_name=arguments.get("dvc_remote_name", "origin"),
        )

        result = configure_store(
            command=command,
            store_repo=storage_ctx.store_repo,
            dvc_gateway=storage_ctx.dvc_gateway,
            event_bus=self._ctx.event_bus,
        )

        if result.is_failure:
            return Failure(result.error or "Failed to configure data store")

        store = result.data
        if store is None:
            return Failure("Configure succeeded but returned no store data")
        return Success(
            {
                "store_id": store.id.value,
                "bucket_name": store.bucket_name,
                "region": store.region,
                "prefix": store.prefix,
                "dvc_remote_name": store.dvc_remote_name,
            }
        )

    def _execute_scan_datastore(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        from src.contexts.storage.core.commandHandlers.scan_store import scan_store
        from src.contexts.storage.core.commands import ScanStoreCommand

        storage_ctx = self._storage_ctx
        if not storage_ctx:
            return Failure("No project open")

        command = ScanStoreCommand(prefix=arguments.get("prefix", ""))

        result = scan_store(
            command=command,
            store_repo=storage_ctx.store_repo,
            s3_scanner=storage_ctx.s3_scanner,
            event_bus=self._ctx.event_bus,
        )

        if result.is_failure:
            return Failure(result.error or "Failed to scan data store")

        files = result.data or []
        return Success(
            {
                "file_count": len(files),
                "files": [
                    {
                        "key": f.key,
                        "size_bytes": f.size_bytes,
                        "last_modified": str(f.last_modified),
                        "extension": f.extension,
                    }
                    for f in files
                ],
            }
        )

    def _execute_pull_source(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        from src.contexts.storage.core.commandHandlers.pull_file import pull_file
        from src.contexts.storage.core.commands import PullFileCommand

        key = arguments.get("key")
        local_path = arguments.get("local_path")
        if not key:
            return Failure("Missing required parameter: key")
        if not local_path:
            return Failure("Missing required parameter: local_path")

        storage_ctx = self._storage_ctx
        if not storage_ctx:
            return Failure("No project open")

        command = PullFileCommand(key=key, local_path=local_path)

        result = pull_file(
            command=command,
            store_repo=storage_ctx.store_repo,
            dvc_gateway=storage_ctx.dvc_gateway,
            event_bus=self._ctx.event_bus,
        )

        if result.is_failure:
            return Failure(result.error or "Failed to pull file")

        return Success(
            {
                "key": key,
                "local_path": result.data,
            }
        )

    def _execute_push_results(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        from src.contexts.storage.core.commandHandlers.push_export import push_export
        from src.contexts.storage.core.commands import PushExportCommand

        local_path = arguments.get("local_path")
        destination_key = arguments.get("destination_key")
        if not local_path:
            return Failure("Missing required parameter: local_path")
        if not destination_key:
            return Failure("Missing required parameter: destination_key")

        storage_ctx = self._storage_ctx
        if not storage_ctx:
            return Failure("No project open")

        command = PushExportCommand(
            local_path=local_path,
            destination_key=destination_key,
        )

        result = push_export(
            command=command,
            store_repo=storage_ctx.store_repo,
            dvc_gateway=storage_ctx.dvc_gateway,
            event_bus=self._ctx.event_bus,
        )

        if result.is_failure:
            return Failure(result.error or "Failed to push export")

        return Success(
            {
                "destination_key": result.data,
                "local_path": local_path,
            }
        )

    def _execute_export_and_push(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        from src.contexts.storage.core.commandHandlers.export_and_push import (
            export_and_push,
        )
        from src.contexts.storage.core.commands import ExportAndPushCommand

        export_format = arguments.get("export_format")
        destination_key = arguments.get("destination_key")
        if not export_format:
            return Failure("Missing required parameter: export_format")
        if not destination_key:
            return Failure("Missing required parameter: destination_key")

        storage_ctx = self._storage_ctx
        if not storage_ctx:
            return Failure("No project open")

        import tempfile

        with tempfile.TemporaryDirectory() as staging_dir:
            command = ExportAndPushCommand(
                export_format=export_format,
                destination_key=destination_key,
                local_staging_dir=staging_dir,
            )

            # Use a no-op exporter placeholder — the real exporter
            # would come from the exchange context coordinator
            def _noop_exporter(**_kwargs):
                from src.shared.common.operation_result import OperationResult

                return OperationResult.fail(
                    error="Export not yet wired to exchange context",
                    error_code="EXPORT_AND_PUSH/NOT_WIRED",
                )

            result = export_and_push(
                command=command,
                store_repo=storage_ctx.store_repo,
                dvc_gateway=storage_ctx.dvc_gateway,
                exporter=_noop_exporter,
                event_bus=self._ctx.event_bus,
            )

        if result.is_failure:
            return Failure(result.error or "Failed to export and push")

        return Success(result.data)

    def _execute_scan_and_import(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        from src.contexts.storage.core.commandHandlers.scan_and_import import (
            scan_and_import,
        )
        from src.contexts.storage.core.commands import ScanAndImportCommand

        key = arguments.get("key")
        if not key:
            return Failure("Missing required parameter: key")

        storage_ctx = self._storage_ctx
        if not storage_ctx:
            return Failure("No project open")

        import tempfile

        with tempfile.TemporaryDirectory() as staging_dir:
            command = ScanAndImportCommand(key=key, local_staging_dir=staging_dir)

            result = scan_and_import(
                command=command,
                store_repo=storage_ctx.store_repo,
                s3_scanner=storage_ctx.s3_scanner,
                importers={},  # Importers wired when exchange context is available
                event_bus=self._ctx.event_bus,
            )

        if result.is_failure:
            return Failure(result.error or "Failed to scan and import")

        return Success(
            {
                "key": key,
                "result": str(result.data),
            }
        )
