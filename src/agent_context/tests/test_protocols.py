"""
Tests for agent context protocols - MCPToolSchema.
TDD RED phase: These tests verify runtime protocol checking.
"""

from dataclasses import dataclass

from src.agent_context.protocols import MCPToolSchema
from src.domain.shared.agent import TrustLevel


class TestMCPToolSchemaProtocol:
    """Tests for MCPToolSchema protocol - runtime checking"""

    def test_valid_tool_satisfies_protocol(self):
        """A class with all required properties should satisfy the protocol"""

        class ValidTool:
            @property
            def name(self) -> str:
                return "test_tool"

            @property
            def description(self) -> str:
                return "A test tool for verification"

            @property
            def input_schema(self) -> dict:
                return {"type": "object", "properties": {}}

            @property
            def trust_level(self) -> TrustLevel:
                return TrustLevel.SUGGEST

        tool = ValidTool()
        assert isinstance(tool, MCPToolSchema)

    def test_missing_property_fails_protocol_check(self):
        """A class missing required properties should not satisfy the protocol"""

        class IncompleteToolMissingTrustLevel:
            @property
            def name(self) -> str:
                return "incomplete"

            @property
            def description(self) -> str:
                return "Missing trust_level"

            @property
            def input_schema(self) -> dict:
                return {}

            # Missing trust_level property

        tool = IncompleteToolMissingTrustLevel()
        assert not isinstance(tool, MCPToolSchema)

    def test_dataclass_tool_satisfies_protocol(self):
        """A frozen dataclass with properties should satisfy the protocol"""

        @dataclass(frozen=True)
        class DataclassTool:
            _name: str
            _description: str
            _input_schema: dict
            _trust_level: TrustLevel

            @property
            def name(self) -> str:
                return self._name

            @property
            def description(self) -> str:
                return self._description

            @property
            def input_schema(self) -> dict:
                return self._input_schema

            @property
            def trust_level(self) -> TrustLevel:
                return self._trust_level

        tool = DataclassTool(
            _name="create_code",
            _description="Create a new code",
            _input_schema={"type": "object", "required": ["name"]},
            _trust_level=TrustLevel.SUGGEST,
        )
        assert isinstance(tool, MCPToolSchema)
        assert tool.name == "create_code"
        assert tool.trust_level == TrustLevel.SUGGEST
