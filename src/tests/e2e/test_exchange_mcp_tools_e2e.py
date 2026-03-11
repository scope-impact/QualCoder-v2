"""
Exchange MCP Tools - E2E Tests

Tests for AI agent-facing exchange tools: suggest format, export, import.
"""

from __future__ import annotations

import allure
import pytest

from src.contexts.coding.core.entities import Code, Color
from src.shared.common.types import CodeId

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-039 Import Export Formats"),
]


def _make_tools(
    code_repo, category_repo, segment_repo, source_repo, case_repo, event_bus
):
    """Create ExchangeTools wired through ExchangeCoordinator."""
    from src.contexts.exchange.interface.mcp_tools import ExchangeTools
    from src.contexts.exchange.presentation.coordinator import ExchangeCoordinator

    coordinator = ExchangeCoordinator(
        code_repo=code_repo,
        category_repo=category_repo,
        segment_repo=segment_repo,
        source_repo=source_repo,
        case_repo=case_repo,
        event_bus=event_bus,
    )
    return ExchangeTools(coordinator=coordinator)


class TestExchangeTools:
    """Tests for exchange MCP tools."""

    def test_tool_schemas_suggest_format_and_export(
        self,
        code_repo,
        category_repo,
        segment_repo,
        source_repo,
        event_bus,
        tmp_path,
    ):
        """Verify tool schemas exist and suggest/export flows work end-to-end."""
        from src.contexts.exchange.interface.mcp_tools import ExchangeTools

        with allure.step("Verify tool schemas"):
            tools_for_schema = ExchangeTools.__new__(ExchangeTools)
            tools_for_schema._init_tool_defs()
            schemas = tools_for_schema.get_tool_schemas()
            assert len(schemas) >= 3
            names = {s["name"] for s in schemas}
            assert "suggest_export_format" in names
            assert "export_data" in names
            assert "import_data" in names

        # Seed a code so export is possible
        code = Code(id=CodeId.new(), name="Joy", color=Color.from_hex("#00FF00"))
        code_repo.save(code)

        tools = _make_tools(
            code_repo, category_repo, segment_repo, source_repo, None, event_bus
        )

        with allure.step("Verify suggest_export_format"):
            result = tools.execute("suggest_export_format", {"use_case": "share codebook"})
            assert result["success"] is True
            assert "format" in result["data"] or "formats" in result["data"]

        with allure.step("Verify export_data for codebook"):
            result = tools.execute(
                "export_data",
                {
                    "format": "codebook",
                    "output_path": str(tmp_path / "codebook.txt"),
                },
            )
            assert result["success"] is True

    def test_unknown_tool_returns_error(
        self,
        code_repo,
        category_repo,
        segment_repo,
        source_repo,
        event_bus,
    ):
        tools = _make_tools(
            code_repo, category_repo, segment_repo, source_repo, None, event_bus
        )

        result = tools.execute("nonexistent_tool", {})
        assert result["success"] is False
        assert "TOOL_NOT_FOUND" in result.get("error_code", "")
