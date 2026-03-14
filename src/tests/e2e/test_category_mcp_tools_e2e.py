"""
E2E tests for Category and Code Management MCP Tools (QC-050).

Tests the MCP handler layer for: rename_code, update_code_memo,
create_category, move_code_to_category, merge_codes, delete_code,
list_categories.

All tests use the MCP server dispatch pipeline (same path an AI agent uses).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import allure
import pytest

from src.shared.infra.app_context import AppContext

if TYPE_CHECKING:
    from src.tests.e2e.conftest import MCPClient


@pytest.fixture
def project_with_codes(
    mcp_server: MCPClient, app_context: AppContext, tmp_path: Path
) -> dict:
    """Create a project with codes and a source for testing code management MCP tools."""
    project_path = tmp_path / "test_code_mgmt.qda"
    result = app_context.create_project("Code Mgmt Test", str(project_path))
    assert result.is_success
    result = app_context.open_project(str(project_path))
    assert result.is_success

    # Create test codes
    code1 = mcp_server.execute("create_code", {"name": "Anxiety", "color": "#FF0000"})
    assert code1["success"]
    code2 = mcp_server.execute("create_code", {"name": "Stress", "color": "#FF5500"})
    assert code2["success"]
    code3 = mcp_server.execute(
        "create_code", {"name": "Resilience", "color": "#00FF00"}
    )
    assert code3["success"]

    # Import a source and apply a code to it
    from src.contexts.sources.core.entities import Source, SourceType
    from src.shared.common.types import SourceId

    source = Source(
        id=SourceId.new(),
        name="interview.txt",
        fulltext="I felt anxious during exams. The stress was overwhelming. But I persevered.",
        source_type=SourceType.TEXT,
    )
    app_context.sources_context.source_repo.save(source)
    if app_context.session:
        app_context.session.commit()

    # Apply code1 to a segment
    mcp_server.execute(
        "batch_apply_codes",
        {
            "operations": [
                {
                    "code_id": code1["data"]["code_id"],
                    "source_id": source.id.value,
                    "start_position": 0,
                    "end_position": 30,
                }
            ]
        },
    )

    return {
        "codes": {
            "anxiety": code1["data"],
            "stress": code2["data"],
            "resilience": code3["data"],
        },
        "source": source,
    }


@allure.story("QC-050.01 rename_code MCP tool")
class TestRenameCodeMCP:
    @allure.title("AC #1: rename_code renames and persists via get_code")
    def test_rename_code_success_and_persists(self, mcp_server, project_with_codes):
        code_id = project_with_codes["codes"]["anxiety"]["code_id"]

        result = mcp_server.execute(
            "rename_code", {"code_id": code_id, "new_name": "Exam Anxiety"}
        )

        assert result["success"]
        assert result["data"]["old_name"] == "Anxiety"
        assert result["data"]["new_name"] == "Exam Anxiety"
        assert result["data"]["code_id"] == code_id

        # Verify persistence
        get_result = mcp_server.execute("get_code", {"code_id": code_id})
        assert get_result["data"]["name"] == "Exam Anxiety"

    @allure.title("AC #1: rename_code errors for missing params or non-existent code")
    def test_rename_code_errors(self, mcp_server, project_with_codes):
        # Missing code_id
        result = mcp_server.execute("rename_code", {"new_name": "Something"})
        assert not result["success"]
        assert "MISSING_PARAM" in result["error_code"]

        # Non-existent code
        result = mcp_server.execute(
            "rename_code", {"code_id": "nonexistent", "new_name": "Something"}
        )
        assert not result["success"]


@allure.story("QC-050.02 update_code_memo MCP tool")
class TestUpdateCodeMemoMCP:
    @allure.title("AC #2: update_code_memo sets and clears memo, persists via get_code")
    def test_update_memo_lifecycle(self, mcp_server, project_with_codes):
        code_id = project_with_codes["codes"]["anxiety"]["code_id"]

        # Set memo
        result = mcp_server.execute(
            "update_code_memo",
            {
                "code_id": code_id,
                "memo": "Feelings of worry or unease about exams",
            },
        )
        assert result["success"]
        assert result["data"]["old_memo"] is None
        assert "worry" in result["data"]["new_memo"]

        # Verify persistence
        get_result = mcp_server.execute("get_code", {"code_id": code_id})
        assert get_result["data"]["memo"] == "Feelings of worry or unease about exams"

        # Clear memo
        result = mcp_server.execute("update_code_memo", {"code_id": code_id})
        assert result["success"]
        assert result["data"]["old_memo"] == "Feelings of worry or unease about exams"
        assert result["data"]["new_memo"] is None


@allure.story("QC-050.03 create_category MCP tool")
class TestCreateCategoryMCP:
    @allure.title("AC #3: create_category with name, parent, memo, and error handling")
    def test_create_category(self, mcp_server, project_with_codes):
        # Basic creation
        result = mcp_server.execute("create_category", {"name": "Emotional Responses"})
        assert result["success"]
        assert result["data"]["name"] == "Emotional Responses"
        assert result["data"]["category_id"] is not None
        assert result["data"]["parent_id"] is None

        # With parent and memo
        parent_id = result["data"]["category_id"]
        child = mcp_server.execute(
            "create_category",
            {
                "name": "Coping Mechanisms",
                "parent_id": parent_id,
                "memo": "How students cope with challenges",
            },
        )
        assert child["success"]
        assert child["data"]["parent_id"] == parent_id
        assert child["data"]["memo"] == "How students cope with challenges"

        # Missing name error
        result = mcp_server.execute("create_category", {})
        assert not result["success"]
        assert "MISSING_PARAM" in result["error_code"]


@allure.story("QC-050.04 move_code_to_category MCP tool")
class TestMoveCodeToCategoryMCP:
    @allure.title("AC #4: move_code_to_category assigns, persists, and uncategorizes")
    def test_move_and_uncategorize(self, mcp_server, project_with_codes):
        code_id = project_with_codes["codes"]["anxiety"]["code_id"]

        # Create category and move code into it
        cat = mcp_server.execute("create_category", {"name": "Emotional Responses"})
        cat_id = cat["data"]["category_id"]

        result = mcp_server.execute(
            "move_code_to_category", {"code_id": code_id, "category_id": cat_id}
        )
        assert result["success"]
        assert result["data"]["old_category_id"] is None
        assert result["data"]["new_category_id"] == cat_id

        # Verify persistence
        get_result = mcp_server.execute("get_code", {"code_id": code_id})
        assert get_result["data"]["category_id"] == cat_id

        # Uncategorize
        result = mcp_server.execute("move_code_to_category", {"code_id": code_id})
        assert result["success"]
        assert result["data"]["old_category_id"] == cat_id
        assert result["data"]["new_category_id"] is None


@allure.story("QC-050.05 merge_codes MCP tool")
class TestMergeCodesMCP:
    @allure.title("AC #5: merge_codes merges source into target, deletes source")
    def test_merge_codes(self, mcp_server, project_with_codes):
        source_id = project_with_codes["codes"]["anxiety"]["code_id"]
        target_id = project_with_codes["codes"]["stress"]["code_id"]

        result = mcp_server.execute(
            "merge_codes",
            {"source_code_id": source_id, "target_code_id": target_id},
        )

        assert result["success"]
        assert result["data"]["source_code_id"] == source_id
        assert result["data"]["target_code_id"] == target_id
        assert result["data"]["segments_moved"] >= 0

        # Source code should be gone
        get_result = mcp_server.execute("get_code", {"code_id": source_id})
        assert not get_result["success"]

        # Target should still exist
        all_codes = mcp_server.execute("list_codes", {})
        code_ids = {c["id"] for c in all_codes["data"]}
        assert target_id in code_ids
        assert source_id not in code_ids

    @allure.title("AC #5: merge_codes returns error for missing params")
    def test_merge_missing_params(self, mcp_server, project_with_codes):
        result = mcp_server.execute("merge_codes", {"source_code_id": "abc"})
        assert not result["success"]
        assert "MISSING_PARAM" in result["error_code"]


@allure.story("QC-050.06 delete_code MCP tool")
class TestDeleteCodeMCP:
    @allure.title("AC #6: delete_code removes code, with and without segments")
    def test_delete_code(self, mcp_server, project_with_codes):
        # Delete code without segments
        code_id = project_with_codes["codes"]["resilience"]["code_id"]
        result = mcp_server.execute("delete_code", {"code_id": code_id})
        assert result["success"]
        assert result["data"]["deleted"] is True
        assert result["data"]["code_id"] == code_id

        # Delete code with segments (anxiety has a segment applied)
        code_id = project_with_codes["codes"]["anxiety"]["code_id"]
        result = mcp_server.execute(
            "delete_code", {"code_id": code_id, "delete_segments": True}
        )
        assert result["success"]
        assert result["data"]["deleted"] is True

        # Missing code_id error
        result = mcp_server.execute("delete_code", {})
        assert not result["success"]
        assert "MISSING_PARAM" in result["error_code"]


@allure.story("QC-050.07 list_categories MCP tool")
class TestListCategoriesMCP:
    @allure.title("AC #7: list_categories returns hierarchy with code counts")
    def test_list_categories(self, mcp_server, project_with_codes):
        code_id = project_with_codes["codes"]["anxiety"]["code_id"]

        # Initially empty
        result = mcp_server.execute("list_categories", {})
        assert result["success"]
        assert result["data"] == []

        # Create parent + child categories
        parent = mcp_server.execute("create_category", {"name": "Themes"})
        parent_id = parent["data"]["category_id"]
        mcp_server.execute(
            "create_category", {"name": "Emotional", "parent_id": parent_id}
        )

        result = mcp_server.execute("list_categories", {})
        assert result["success"]
        assert len(result["data"]) == 2
        names = {c["name"] for c in result["data"]}
        assert "Themes" in names
        assert "Emotional" in names

        # Check parent_id relationship
        child = next(c for c in result["data"] if c["name"] == "Emotional")
        assert child["parent_id"] == parent_id

        # Move code into Emotional and verify code_count
        mcp_server.execute(
            "move_code_to_category",
            {"code_id": code_id, "category_id": child["id"]},
        )
        result = mcp_server.execute("list_categories", {})
        emotional_cat = next(c for c in result["data"] if c["name"] == "Emotional")
        assert emotional_cat["code_count"] == 1


@allure.story("QC-050.08 Tool registration and response format")
class TestToolRegistration:
    @allure.title("AC #8,10: All tools registered and return OperationResult format")
    def test_tools_registered_and_response_format(self, mcp_server, project_with_codes):
        # Verify all new tools are registered via MCP server
        tool_names = mcp_server.list_tools()
        expected = [
            "rename_code",
            "update_code_memo",
            "create_category",
            "move_code_to_category",
            "merge_codes",
            "delete_code",
            "list_categories",
        ]
        for name in expected:
            assert name in tool_names, f"Tool '{name}' not registered"

        # Verify each tool returns OperationResult.to_dict() format
        for tool_name, args in [
            ("rename_code", {"code_id": "nonexistent", "new_name": "x"}),
            ("update_code_memo", {"code_id": "nonexistent", "memo": "x"}),
            ("create_category", {}),
            ("move_code_to_category", {}),
            ("merge_codes", {}),
            ("delete_code", {}),
            ("list_categories", {}),
        ]:
            result = mcp_server.execute(tool_name, args)
            assert "success" in result, f"{tool_name} missing 'success' key"
            if result["success"]:
                assert "data" in result
            else:
                assert "error" in result or "error_code" in result
