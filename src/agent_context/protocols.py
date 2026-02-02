"""
Agent Context Protocols - MCP Tool Schema Contracts

These interfaces define the CONTRACT for MCP tool definitions.
All tool adapters must conform to these protocols.
"""

from typing import Protocol, runtime_checkable

from src.contexts.shared.core import TrustLevel


@runtime_checkable
class MCPToolSchema(Protocol):
    """
    Contract for MCP-compatible tool definitions.

    Tools expose capabilities to AI agents via the Model Context Protocol.
    Each tool has a schema defining its inputs and a trust level
    determining approval requirements.

    This is a structural protocol - classes don't need to inherit from it,
    they just need to implement the required properties.

    Example:
        class CreateCodeTool:
            @property
            def name(self) -> str:
                return "create_code"
            ...

        tool = CreateCodeTool()
        assert isinstance(tool, MCPToolSchema)  # True
    """

    @property
    def name(self) -> str:
        """Unique tool name (e.g., 'create_code')"""
        ...

    @property
    def description(self) -> str:
        """Human-readable description of what the tool does"""
        ...

    @property
    def input_schema(self) -> dict:
        """JSON Schema for tool input validation"""
        ...

    @property
    def trust_level(self) -> TrustLevel:
        """Permission level required to execute this tool"""
        ...
