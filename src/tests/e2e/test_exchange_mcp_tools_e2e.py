"""
Exchange MCP Tools - E2E Tests

Tests for AI agent-facing exchange tools: suggest format, export, import.
"""
from __future__ import annotations

import allure
import pytest

from src.contexts.coding.core.entities import Code, Color

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-039 Import Export Formats"),
]
from src.shared.common.types import CodeId


def _make_tools(code_repo, category_repo, segment_repo, source_repo, case_repo, event_bus):
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

    def test_get_tool_schemas(self):
        from src.contexts.exchange.interface.mcp_tools import ExchangeTools

        tools = ExchangeTools.__new__(ExchangeTools)
        tools._init_tool_defs()

        schemas = tools.get_tool_schemas()
        assert len(schemas) >= 3
        names = {s["name"] for s in schemas}
        assert "suggest_export_format" in names
        assert "export_data" in names
        assert "import_data" in names

    def test_suggest_export_format(
        self, code_repo, category_repo, segment_repo, source_repo, event_bus,
    ):
        # Seed a code so export is possible
        code = Code(id=CodeId.new(), name="Joy", color=Color.from_hex("#00FF00"))
        code_repo.save(code)

        tools = _make_tools(code_repo, category_repo, segment_repo, source_repo, None, event_bus)

        result = tools.execute("suggest_export_format", {"use_case": "share codebook"})

        assert result["success"] is True
        assert "format" in result["data"] or "formats" in result["data"]

    def test_export_codebook_via_mcp(
        self, code_repo, category_repo, segment_repo, source_repo, event_bus, tmp_path,
    ):
        code = Code(id=CodeId.new(), name="Joy", color=Color.from_hex("#00FF00"))
        code_repo.save(code)

        tools = _make_tools(code_repo, category_repo, segment_repo, source_repo, None, event_bus)

        result = tools.execute("export_data", {
            "format": "codebook",
            "output_path": str(tmp_path / "codebook.txt"),
        })

        assert result["success"] is True

    def test_unknown_tool_returns_error(
        self, code_repo, category_repo, segment_repo, source_repo, event_bus,
    ):
        tools = _make_tools(code_repo, category_repo, segment_repo, source_repo, None, event_bus)

        result = tools.execute("nonexistent_tool", {})
        assert result["success"] is False
        assert "TOOL_NOT_FOUND" in result.get("error_code", "")
