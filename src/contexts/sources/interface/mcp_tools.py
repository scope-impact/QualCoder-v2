"""
MCP Source Tools

Provides MCP-compatible tools for AI agent interaction with sources.

Implements:
- QC-027.08: Agent can list sources
- QC-027.09: Agent can read source content
- QC-027.10: Agent can extract/suggest metadata
- QC-027.12: Agent can add text sources
- QC-027.14: Agent can remove sources
- QC-027.15: Agent can import file-based sources
- QC-026.06: Agent can navigate to a segment
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from returns.result import Failure, Result, Success

from src.shared.common.mcp_types import ToolDefinition, ToolParameter
from src.shared.common.types import SourceId

if TYPE_CHECKING:
    from src.shared.infra.state import ProjectState


@runtime_checkable
class SourceToolsContext(Protocol):
    """Protocol defining context requirements for SourceTools."""

    @property
    def state(self) -> ProjectState: ...

    @property
    def event_bus(self): ...

    @property
    def sources_context(self): ...

    @property
    def coding_context(self): ...

    @property
    def cases_context(self): ...


# ============================================================
# Tool Definitions
# ============================================================

list_sources_tool = ToolDefinition(
    name="list_sources",
    description=(
        "List all sources (documents, media files) in the current project. "
        "Optionally filter by source type."
    ),
    parameters=(
        ToolParameter(
            name="source_type",
            type="string",
            description="Filter by source type: 'text', 'audio', 'video', 'image', 'pdf'. Leave empty for all.",
            required=False,
            default=None,
        ),
    ),
)

read_source_content_tool = ToolDefinition(
    name="read_source_content",
    description=(
        "Read the text content of a source document. "
        "Supports reading full content or a specific position range. "
        "Large documents are paginated with max_length parameter."
    ),
    parameters=(
        ToolParameter(
            name="source_id",
            type="integer",
            description="The ID of the source document to read.",
            required=True,
        ),
        ToolParameter(
            name="start_pos",
            type="integer",
            description="Starting character position. Default 0.",
            required=False,
            default=0,
        ),
        ToolParameter(
            name="end_pos",
            type="integer",
            description="Ending character position. Default: end of content.",
            required=False,
            default=None,
        ),
        ToolParameter(
            name="max_length",
            type="integer",
            description="Maximum characters to return. Default 50000 for pagination.",
            required=False,
            default=50000,
        ),
    ),
)

navigate_to_segment_tool = ToolDefinition(
    name="navigate_to_segment",
    description=(
        "Navigate to a specific segment position within a source document. "
        "Opens the source in the coding screen and scrolls to the specified position. "
        "Optionally highlights the segment."
    ),
    parameters=(
        ToolParameter(
            name="source_id",
            type="integer",
            description="The ID of the source document to navigate to.",
            required=True,
        ),
        ToolParameter(
            name="start_pos",
            type="integer",
            description="The character position where the segment starts.",
            required=True,
        ),
        ToolParameter(
            name="end_pos",
            type="integer",
            description="The character position where the segment ends.",
            required=True,
        ),
        ToolParameter(
            name="highlight",
            type="boolean",
            description="Whether to highlight the segment. Default true.",
            required=False,
            default=True,
        ),
    ),
)

suggest_source_metadata_tool = ToolDefinition(
    name="suggest_source_metadata",
    description=(
        "Submit metadata suggestions for a source document. "
        "Agent provides extracted/suggested language, topics, and organization hints. "
        "Suggestions are stored with pending status for researcher approval."
    ),
    parameters=(
        ToolParameter(
            name="source_id",
            type="integer",
            description="The ID of the source document.",
            required=True,
        ),
        ToolParameter(
            name="language",
            type="string",
            description="Detected language code (e.g., 'en', 'es', 'fr').",
            required=False,
            default=None,
        ),
        ToolParameter(
            name="topics",
            type="array",
            description="List of extracted key topics/themes.",
            required=False,
            default=None,
        ),
        ToolParameter(
            name="organization_suggestion",
            type="string",
            description="Suggestion for organizing/grouping this source.",
            required=False,
            default=None,
        ),
    ),
)

add_text_source_tool = ToolDefinition(
    name="add_text_source",
    description=(
        "Add a new text source to the current project. "
        "Provide a name and text content. "
        "Optionally include memo and origin metadata."
    ),
    parameters=(
        ToolParameter(
            name="name",
            type="string",
            description="Name for the new source (must be unique within project).",
            required=True,
        ),
        ToolParameter(
            name="content",
            type="string",
            description="The full text content of the source.",
            required=True,
        ),
        ToolParameter(
            name="memo",
            type="string",
            description="Optional memo/notes about the source.",
            required=False,
            default=None,
        ),
        ToolParameter(
            name="origin",
            type="string",
            description="Optional origin description (e.g., 'interview transcript', 'field notes').",
            required=False,
            default=None,
        ),
    ),
)

remove_source_tool = ToolDefinition(
    name="remove_source",
    description=(
        "Remove a source from the project. "
        "This deletes the source, its content, and all coded segments. "
        "Use confirm=false to preview what would be deleted."
    ),
    parameters=(
        ToolParameter(
            name="source_id",
            type="integer",
            description="ID of the source to remove.",
            required=True,
        ),
        ToolParameter(
            name="confirm",
            type="boolean",
            description="Set to true to actually delete. Default false returns a preview.",
            required=False,
            default=False,
        ),
    ),
)

import_file_source_tool = ToolDefinition(
    name="import_file_source",
    description=(
        "Import a file-based source (document, PDF, image, audio, video) "
        "into the current project by providing its absolute file path. "
        "The file type is auto-detected from the extension."
    ),
    parameters=(
        ToolParameter(
            name="file_path",
            type="string",
            description="Absolute path to the source file on the local filesystem.",
            required=True,
        ),
        ToolParameter(
            name="name",
            type="string",
            description="Optional name override. Defaults to the filename.",
            required=False,
            default=None,
        ),
        ToolParameter(
            name="memo",
            type="string",
            description="Optional memo/notes about the source.",
            required=False,
            default=None,
        ),
        ToolParameter(
            name="origin",
            type="string",
            description="Optional origin description (e.g., 'field recording', 'scan').",
            required=False,
            default=None,
        ),
        ToolParameter(
            name="dry_run",
            type="boolean",
            description="If true, validate the file without importing. Default false.",
            required=False,
            default=False,
        ),
    ),
)

ALL_SOURCE_TOOLS = {
    "list_sources": list_sources_tool,
    "read_source_content": read_source_content_tool,
    "navigate_to_segment": navigate_to_segment_tool,
    "suggest_source_metadata": suggest_source_metadata_tool,
    "add_text_source": add_text_source_tool,
    "remove_source": remove_source_tool,
    "import_file_source": import_file_source_tool,
}


# ============================================================
# Tool Implementation
# ============================================================


class SourceTools:
    """MCP-compatible source tools for AI agent integration."""

    def __init__(self, ctx: SourceToolsContext) -> None:
        self._ctx = ctx
        self._tools = ALL_SOURCE_TOOLS
        self._handlers = {
            "list_sources": self._execute_list_sources,
            "read_source_content": self._execute_read_source_content,
            "navigate_to_segment": self._execute_navigate_to_segment,
            "suggest_source_metadata": self._execute_suggest_source_metadata,
            "add_text_source": self._execute_add_text_source,
            "remove_source": self._execute_remove_source,
            "import_file_source": self._execute_import_file_source,
        }

    @property
    def _state(self):
        return self._ctx.state

    @property
    def _source_repo(self):
        ctx = self._ctx.sources_context
        return ctx.source_repo if ctx else None

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

    def _execute_list_sources(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        source_type = arguments.get("source_type")
        sources_ctx = self._ctx.sources_context
        all_sources = sources_ctx.source_repo.get_all() if sources_ctx else []

        if source_type:
            sources = [s for s in all_sources if s.source_type.value == source_type]
        else:
            sources = all_sources

        return Success(
            {
                "count": len(sources),
                "sources": [
                    {
                        "id": s.id.value,
                        "name": s.name,
                        "type": s.source_type.value,
                        "status": s.status.value,
                        "file_path": str(s.file_path),
                        "memo": s.memo,
                        "file_size": s.file_size,
                        "origin": s.origin,
                        "code_count": s.code_count,
                    }
                    for s in sources
                ],
            }
        )

    def _execute_read_source_content(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        source_id = arguments.get("source_id")
        if source_id is None:
            return Failure("Missing required parameter: source_id")

        sources_ctx = self._ctx.sources_context
        if not sources_ctx:
            return Failure("No project open")

        source = sources_ctx.source_repo.get_by_id(SourceId(value=str(source_id)))
        if source is None:
            return Failure(f"Source not found: {source_id}")

        content = source.fulltext or ""
        total_length = len(content)
        start_pos = arguments.get("start_pos", 0) or 0
        end_pos = arguments.get("end_pos")
        max_length = arguments.get("max_length", 50000) or 50000

        if end_pos is None:
            end_pos = total_length

        actual_end = min(end_pos, start_pos + max_length)
        extracted_content = content[start_pos:actual_end]
        has_more = actual_end < total_length

        return Success(
            {
                "source_id": source_id,
                "source_name": source.name,
                "content": extracted_content,
                "start_pos": start_pos,
                "end_pos": actual_end,
                "total_length": total_length,
                "has_more": has_more,
            }
        )

    def _execute_navigate_to_segment(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        source_id = arguments.get("source_id")
        start_pos = arguments.get("start_pos")
        end_pos = arguments.get("end_pos")

        if source_id is None:
            return Failure("Missing required parameter: source_id")
        if start_pos is None:
            return Failure("Missing required parameter: start_pos")
        if end_pos is None:
            return Failure("Missing required parameter: end_pos")

        highlight = arguments.get("highlight", True)

        source_repo = self._source_repo
        if not source_repo:
            return Failure("No project open")

        source = source_repo.get_by_id(SourceId(value=str(source_id)))
        if source is None:
            return Failure(f"Source not found: {source_id}")

        return Success(
            {
                "success": True,
                "navigated_to": {
                    "source_id": source_id,
                    "start_pos": start_pos,
                    "end_pos": end_pos,
                    "highlight": highlight,
                },
                "current_screen": self._state.current_screen,
            }
        )

    def _execute_suggest_source_metadata(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        source_id = arguments.get("source_id")
        if source_id is None:
            return Failure("Missing required parameter: source_id")

        sources_ctx = self._ctx.sources_context
        if not sources_ctx:
            return Failure("No project open")

        source = sources_ctx.source_repo.get_by_id(SourceId(value=str(source_id)))
        if source is None:
            return Failure(f"Source not found: {source_id}")

        language = arguments.get("language")
        topics = arguments.get("topics", []) or []
        organization_suggestion = arguments.get("organization_suggestion")

        suggested = {}
        if language:
            suggested["language"] = language
        if topics:
            suggested["topics"] = topics
        if organization_suggestion:
            suggested["organization_suggestion"] = organization_suggestion

        return Success(
            {
                "source_id": source_id,
                "source_name": source.name,
                "suggested": suggested,
                "status": "pending_approval",
                "requires_approval": True,
            }
        )

    def _execute_add_text_source(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        from src.contexts.projects.core.commands import AddTextSourceCommand
        from src.contexts.sources.core.commandHandlers.add_text_source import (
            add_text_source,
        )

        name = arguments.get("name")
        content = arguments.get("content")

        if name is None:
            return Failure("Missing required parameter: name")
        if content is None:
            return Failure("Missing required parameter: content")

        command = AddTextSourceCommand(
            name=name,
            content=content,
            memo=arguments.get("memo"),
            origin=arguments.get("origin"),
        )

        result = add_text_source(
            command=command,
            state=self._state,
            source_repo=self._source_repo,
            event_bus=self._ctx.event_bus,
        )

        if result.is_failure:
            return Failure(result.error or "Failed to add source")

        source = result.data
        return Success(
            {
                "success": True,
                "source_id": source.id.value,
                "name": source.name,
                "type": source.source_type.value,
                "status": source.status.value,
                "file_size": source.file_size,
            }
        )

    def _execute_remove_source(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        source_id = arguments.get("source_id")
        if source_id is None:
            return Failure("Missing required parameter: source_id")

        confirm = arguments.get("confirm", False)

        sources_ctx = self._ctx.sources_context
        if not sources_ctx:
            return Failure("No project open")

        source = sources_ctx.source_repo.get_by_id(SourceId(value=str(source_id)))
        if source is None:
            return Failure(f"Source not found: {source_id}")

        if not confirm:
            return Success(
                {
                    "preview": True,
                    "source_id": source.id.value,
                    "source_name": source.name,
                    "source_type": source.source_type.value,
                    "coded_segments_count": source.code_count,
                    "requires_approval": True,
                    "message": (
                        f"This will delete source '{source.name}' "
                        f"and {source.code_count} coded segment(s)"
                    ),
                }
            )

        from src.contexts.projects.core.commands import RemoveSourceCommand
        from src.contexts.sources.core.commandHandlers.remove_source import (
            remove_source,
        )

        command = RemoveSourceCommand(source_id=source_id)
        segment_repo = (
            self._ctx.coding_context.segment_repo if self._ctx.coding_context else None
        )

        result = remove_source(
            command=command,
            state=self._state,
            source_repo=sources_ctx.source_repo,
            segment_repo=segment_repo,
            event_bus=self._ctx.event_bus,
        )

        if result.is_failure:
            return Failure(result.error or "Failed to remove source")

        event = result.data
        return Success(
            {
                "success": True,
                "removed": True,
                "source_id": event.source_id.value,
                "source_name": event.name,
                "segments_removed": event.segments_removed,
            }
        )

    def _execute_import_file_source(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        from src.contexts.projects.core.commands import ImportFileSourceCommand
        from src.contexts.sources.core.commandHandlers.import_file_source import (
            import_file_source,
        )

        file_path = arguments.get("file_path")
        if file_path is None:
            return Failure("Missing required parameter: file_path")

        command = ImportFileSourceCommand(
            file_path=str(file_path),
            name=arguments.get("name"),
            memo=arguments.get("memo"),
            origin=arguments.get("origin"),
            dry_run=arguments.get("dry_run", False),
        )

        result = import_file_source(
            command=command,
            state=self._state,
            source_repo=self._source_repo,
            event_bus=self._ctx.event_bus,
        )

        if result.is_failure:
            return Failure(result.error or "Failed to import file source")

        if command.dry_run:
            return Success(result.data)

        source = result.data
        return Success(
            {
                "success": True,
                "source_id": source.id.value,
                "name": source.name,
                "type": source.source_type.value,
                "status": source.status.value,
                "file_size": source.file_size,
            }
        )
