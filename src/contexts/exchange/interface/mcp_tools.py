"""
Exchange MCP Tools for AI Agent Integration.

Provides tools for:
- suggest_export_format: Recommend export format based on use case
- export_data: Export data in a given format
- import_data: Import data from a file
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.contexts.exchange.core.commands import (
    ExportCodebookCommand,
    ExportCodedHTMLCommand,
    ExportRefiQdaCommand,
    ImportCodeListCommand,
    ImportRefiQdaCommand,
    ImportRqdaCommand,
    ImportSurveyCSVCommand,
)
from src.shared.common.mcp_types import ToolDefinition, ToolParameter
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.exchange.presentation.coordinator import ExchangeCoordinator


EXCHANGE_TOOLS = {
    "suggest_export_format": ToolDefinition(
        name="suggest_export_format",
        description=(
            "Suggest the best export format based on the researcher's use case. "
            "Returns recommended format and rationale."
        ),
        parameters=(
            ToolParameter(
                name="use_case",
                type="string",
                description="What the researcher wants to do (e.g., 'share codebook', 'interop with NVivo', 'backup project')",
            ),
        ),
    ),
    "export_data": ToolDefinition(
        name="export_data",
        description="Export project data in the specified format.",
        parameters=(
            ToolParameter(
                name="format",
                type="string",
                description="Export format: codebook, html, refi_qda",
            ),
            ToolParameter(
                name="output_path",
                type="string",
                description="Path to write the exported file",
            ),
            ToolParameter(
                name="include_memos",
                type="boolean",
                description="Include memos in export (codebook only)",
                required=False,
                default=True,
            ),
        ),
    ),
    "import_data": ToolDefinition(
        name="import_data",
        description="Import data from a file in the specified format.",
        parameters=(
            ToolParameter(
                name="format",
                type="string",
                description="Import format: code_list, csv, firebase_csv, refi_qda, rqda",
            ),
            ToolParameter(
                name="source_path",
                type="string",
                description="Path to the file to import",
            ),
            ToolParameter(
                name="name_column",
                type="string",
                description="Column to use as case name (CSV and firebase_csv only)",
                required=False,
            ),
        ),
    ),
}

FORMAT_SUGGESTIONS = {
    "share codebook": {
        "format": "codebook",
        "rationale": "Plain text codebook is universally readable and easy to share.",
    },
    "interop": {
        "format": "refi_qda",
        "rationale": "REFI-QDA (.qdpx) is the standard for inter-tool exchange.",
    },
    "nvivo": {
        "format": "refi_qda",
        "rationale": "NVivo supports REFI-QDA import. Export as .qdpx.",
    },
    "atlas": {
        "format": "refi_qda",
        "rationale": "ATLAS.ti supports REFI-QDA import. Export as .qdpx.",
    },
    "review": {
        "format": "html",
        "rationale": "HTML export shows coded text with highlights — ideal for review.",
    },
    "presentation": {
        "format": "html",
        "rationale": "HTML export with color-coded segments works well for presentations.",
    },
    "backup": {
        "format": "refi_qda",
        "rationale": "REFI-QDA preserves all project data (codes, sources, segments).",
    },
}


class ExchangeTools:
    """MCP-compatible exchange tools for AI agent integration."""

    def __init__(self, coordinator: ExchangeCoordinator) -> None:
        self._coordinator = coordinator
        self._init_tool_defs()

    def _init_tool_defs(self):
        self._tools = EXCHANGE_TOOLS
        self._handlers = {
            "suggest_export_format": self._handle_suggest_format,
            "export_data": self._handle_export,
            "import_data": self._handle_import,
        }

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        return [tool.to_schema() for tool in self._tools.values()]

    def get_tool_names(self) -> list[str]:
        return list(self._tools.keys())

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name not in self._tools:
            return OperationResult.fail(
                error=f"Unknown tool: {tool_name}",
                error_code="TOOL_NOT_FOUND",
                suggestions=(f"Available tools: {', '.join(self._tools.keys())}",),
            ).to_dict()

        handler = self._handlers.get(tool_name)
        if handler is None:
            return OperationResult.fail(
                error=f"No handler for tool: {tool_name}",
                error_code="HANDLER_NOT_FOUND",
            ).to_dict()

        try:
            return handler(arguments)
        except Exception as e:
            return OperationResult.fail(
                error=f"Tool execution error: {e!s}",
                error_code="TOOL_EXECUTION_ERROR",
            ).to_dict()

    def _handle_suggest_format(self, args: dict) -> dict:
        use_case = args.get("use_case", "").lower()

        # Find best match
        for keyword, suggestion in FORMAT_SUGGESTIONS.items():
            if keyword in use_case:
                return OperationResult.ok(
                    data={
                        "format": suggestion["format"],
                        "rationale": suggestion["rationale"],
                        "formats": list(FORMAT_SUGGESTIONS.keys()),
                    }
                ).to_dict()

        # Default suggestion
        return OperationResult.ok(
            data={
                "format": "refi_qda",
                "rationale": "REFI-QDA is the most comprehensive format for project exchange.",
                "formats": list(FORMAT_SUGGESTIONS.keys()),
            }
        ).to_dict()

    def _handle_export(self, args: dict) -> dict:
        fmt = args.get("format", "")
        output_path = args.get("output_path", "")

        if fmt == "codebook":
            result = self._coordinator.export_codebook(
                ExportCodebookCommand(
                    output_path=output_path,
                    include_memos=args.get("include_memos", True),
                ),
            )
            return result.to_dict()

        elif fmt == "html":
            result = self._coordinator.export_coded_html(
                ExportCodedHTMLCommand(output_path=output_path),
            )
            return result.to_dict()

        elif fmt == "refi_qda":
            result = self._coordinator.export_refi_qda(
                ExportRefiQdaCommand(output_path=output_path),
            )
            return result.to_dict()

        return OperationResult.fail(
            error=f"Unknown export format: {fmt}",
            error_code="UNKNOWN_FORMAT",
            suggestions=("Use one of: codebook, html, refi_qda",),
        ).to_dict()

    def _handle_import(self, args: dict) -> dict:
        fmt = args.get("format", "")
        source_path = args.get("source_path", "")

        if fmt == "code_list":
            result = self._coordinator.import_code_list(
                ImportCodeListCommand(source_path=source_path),
            )
            return result.to_dict()

        elif fmt in ("csv", "firebase_csv"):
            result = self._coordinator.import_survey_csv(
                ImportSurveyCSVCommand(
                    source_path=source_path,
                    name_column=args.get("name_column"),
                ),
            )
            return result.to_dict()

        elif fmt == "refi_qda":
            result = self._coordinator.import_refi_qda(
                ImportRefiQdaCommand(source_path=source_path),
            )
            return result.to_dict()

        elif fmt == "rqda":
            result = self._coordinator.import_rqda(
                ImportRqdaCommand(source_path=source_path),
            )
            return result.to_dict()

        return OperationResult.fail(
            error=f"Unknown import format: {fmt}",
            error_code="UNKNOWN_FORMAT",
            suggestions=("Use one of: code_list, csv, refi_qda, rqda",),
        ).to_dict()
