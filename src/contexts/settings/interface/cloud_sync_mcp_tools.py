"""MCP Cloud Sync Tools - AI agent integration for cloud sync settings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from returns.result import Failure

from src.contexts.settings.core.commandHandlers import configure_cloud_sync
from src.contexts.settings.core.commands import ConfigureCloudSyncCommand

if TYPE_CHECKING:
    from src.contexts.settings.infra import UserSettingsRepository
    from src.shared.infra.event_bus import EventBus


@dataclass(frozen=True)
class ToolParameter:
    """MCP tool parameter definition."""

    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None


@dataclass(frozen=True)
class ToolDefinition:
    """MCP tool definition with schema."""

    name: str
    description: str
    parameters: tuple[ToolParameter, ...] = ()
    is_destructive: bool = False

    def to_schema(self) -> dict[str, Any]:
        """Convert to MCP-compatible JSON schema."""
        properties = {}
        required = []

        for param in self.parameters:
            prop: dict[str, Any] = {
                "type": param.type,
                "description": param.description,
            }
            if param.default is not None:
                prop["default"] = param.default
            if param.required:
                required.append(param.name)
            properties[param.name] = prop

        schema: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }
        if self.is_destructive:
            schema["annotations"] = {"destructive": True}
        return schema


# Tool definitions
get_sync_status_tool = ToolDefinition(
    name="get_sync_status",
    description="Check if cloud sync is enabled and get Convex URL configuration.",
    parameters=(),
)

configure_cloud_sync_tool = ToolDefinition(
    name="configure_cloud_sync",
    description="Enable or disable cloud sync with Convex. URL must be configured first.",
    parameters=(
        ToolParameter(
            name="enabled",
            type="boolean",
            description="Whether to enable cloud sync.",
            required=True,
        ),
        ToolParameter(
            name="convex_url",
            type="string",
            description="Convex deployment URL (e.g., https://project.convex.cloud).",
            required=False,
        ),
    ),
)

get_sync_settings_tool = ToolDefinition(
    name="get_sync_settings",
    description="Get current cloud sync settings including enabled state and URL.",
    parameters=(),
)


class CloudSyncMCPTools:
    """
    MCP tools for cloud sync configuration.

    Allows AI agents to:
    - Check sync status (AC #7)
    - Configure cloud sync settings
    - Query sync configuration
    """

    TOOLS = (
        get_sync_status_tool,
        configure_cloud_sync_tool,
        get_sync_settings_tool,
    )

    def __init__(
        self,
        settings_repo: UserSettingsRepository,
        event_bus: EventBus | None = None,
    ) -> None:
        """
        Initialize cloud sync MCP tools.

        Args:
            settings_repo: Repository for settings persistence
            event_bus: Optional event bus for publishing events
        """
        self._settings_repo = settings_repo
        self._event_bus = event_bus

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get list of tool schemas for MCP registration."""
        return [tool.to_schema() for tool in self.TOOLS]

    def handle_tool_call(
        self, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Handle a tool call from an AI agent.

        Args:
            tool_name: Name of the tool to call
            params: Tool parameters

        Returns:
            Tool result as dict with success/data or error fields
        """
        handlers = {
            "get_sync_status": self._handle_get_sync_status,
            "configure_cloud_sync": self._handle_configure_cloud_sync,
            "get_sync_settings": self._handle_get_sync_settings,
        }

        handler = handlers.get(tool_name)
        if handler is None:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "error_code": "UNKNOWN_TOOL",
            }

        return handler(params)

    def _handle_get_sync_status(self, _params: dict[str, Any]) -> dict[str, Any]:
        """Check if cloud sync is active."""
        settings = self._settings_repo.load()
        backend = settings.backend

        return {
            "success": True,
            "data": {
                "cloud_sync_enabled": backend.cloud_sync_enabled,
                "convex_url_configured": bool(backend.convex_url),
                "status": "active" if backend.cloud_sync_enabled else "disabled",
            },
        }

    def _handle_configure_cloud_sync(self, params: dict[str, Any]) -> dict[str, Any]:
        """Configure cloud sync settings."""
        enabled = params.get("enabled", False)
        convex_url = params.get("convex_url")

        # If URL not provided, keep current
        if convex_url is None:
            current_settings = self._settings_repo.load()
            convex_url = current_settings.backend.convex_url

        command = ConfigureCloudSyncCommand(
            enabled=enabled,
            convex_url=convex_url,
        )

        result = configure_cloud_sync(
            command=command,
            settings_repo=self._settings_repo,
            event_bus=self._event_bus,
        )

        if isinstance(result, Failure):
            error_msg = result.failure()
            # Try to extract error_code and suggestions from failure
            error_code = "CONFIGURATION_FAILED"
            suggestions: list[str] = []

            if hasattr(error_msg, "error_code"):
                error_code = error_msg.error_code
            if hasattr(error_msg, "suggestions"):
                suggestions = list(error_msg.suggestions)

            return {
                "success": False,
                "error": str(error_msg),
                "error_code": error_code,
                "suggestions": suggestions,
            }

        return {
            "success": True,
            "data": {
                "enabled": enabled,
                "convex_url": convex_url,
                "message": "Cloud sync enabled" if enabled else "Cloud sync disabled",
            },
        }

    def _handle_get_sync_settings(self, _params: dict[str, Any]) -> dict[str, Any]:
        """Get current sync settings."""
        settings = self._settings_repo.load()
        backend = settings.backend

        return {
            "success": True,
            "data": {
                "cloud_sync_enabled": backend.cloud_sync_enabled,
                "convex_url": backend.convex_url,
            },
        }
