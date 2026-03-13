"""
E2E tests for Category and Code Management MCP Tools (QC-050).

Tests the MCP handler layer for: rename_code, update_code_memo,
create_category, move_code_to_category, merge_codes, delete_code,
list_categories.

All tests use the CodingTools.execute() interface (same path an AI agent uses).
"""

from __future__ import annotations

from pathlib import Path

import allure
import pytest

from src.contexts.coding.interface.mcp_tools import CodingTools
from src.shared.infra.app_context import AppContext


@pytest.fixture
def project_with_codes(app_context: AppContext, tmp_path: Path) -> dict:
    """Create a project with codes and a source for testing code management MCP tools."""
    project_path = tmp_path / "test_code_mgmt.qda"
    result = app_context.create_project("Code Mgmt Test", str(project_path))
    assert result.is_success
    result = app_context.open_project(str(project_path))
    assert result.is_success

    tools = CodingTools(ctx=app_context)

    # Create test codes
    code1 = tools.execute("create_code", {"name": "Anxiety", "color": "#FF0000"})
    assert code1["success"]
    code2 = tools.execute("create_code", {"name": "Stress", "color": "#FF5500"})
    assert code2["success"]
    code3 = tools.execute("create_code", {"name": "Resilience", "color": "#00FF00"})
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
    tools.execute(
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
        "tools": tools,
        "codes": {
            "anxiety": code1["data"],
            "stress": code2["data"],
            "resilience": code3["data"],
        },
        "source": source,
    }


@allure.story("QC-050.01 rename_code MCP tool")
class TestRenameCodeMCP:
    @allure.title("AC #1: rename_code accepts code_id and new_name")
    def test_rename_code_success(self, project_with_codes):
        tools = project_with_codes["tools"]
        code_id = project_with_codes["codes"]["anxiety"]["code_id"]

        result = tools.execute(
            "rename_code", {"code_id": code_id, "new_name": "Exam Anxiety"}
        )

        assert result["success"]
        assert result["data"]["old_name"] == "Anxiety"
        assert result["data"]["new_name"] == "Exam Anxiety"
        assert result["data"]["code_id"] == code_id

    @allure.title("AC #1: rename_code returns error for missing code_id")
    def test_rename_code_missing_code_id(self, project_with_codes):
        tools = project_with_codes["tools"]

        result = tools.execute("rename_code", {"new_name": "Something"})

        assert not result["success"]
        assert "MISSING_PARAM" in result["error_code"]

    @allure.title("AC #1: rename_code returns error for non-existent code")
    def test_rename_code_not_found(self, project_with_codes):
        tools = project_with_codes["tools"]

        result = tools.execute(
            "rename_code", {"code_id": "nonexistent", "new_name": "Something"}
        )

        assert not result["success"]

    @allure.title("AC #1: renamed code visible via get_code")
    def test_rename_code_persists(self, project_with_codes):
        tools = project_with_codes["tools"]
        code_id = project_with_codes["codes"]["anxiety"]["code_id"]

        tools.execute("rename_code", {"code_id": code_id, "new_name": "Exam Anxiety"})

        get_result = tools.execute("get_code", {"code_id": code_id})
        assert get_result["success"]
        assert get_result["data"]["name"] == "Exam Anxiety"


@allure.story("QC-050.02 update_code_memo MCP tool")
class TestUpdateCodeMemoMCP:
    @allure.title("AC #2: update_code_memo accepts code_id and memo")
    def test_update_memo_success(self, project_with_codes):
        tools = project_with_codes["tools"]
        code_id = project_with_codes["codes"]["anxiety"]["code_id"]

        result = tools.execute(
            "update_code_memo",
            {
                "code_id": code_id,
                "memo": "Feelings of worry or unease about exams and academic performance",
            },
        )

        assert result["success"]
        assert result["data"]["code_id"] == code_id
        assert result["data"]["old_memo"] is None
        assert "worry" in result["data"]["new_memo"]

    @allure.title("AC #2: update_code_memo clears memo when memo is None")
    def test_update_memo_clear(self, project_with_codes):
        tools = project_with_codes["tools"]
        code_id = project_with_codes["codes"]["anxiety"]["code_id"]

        # Set memo first
        tools.execute(
            "update_code_memo", {"code_id": code_id, "memo": "Some memo"}
        )
        # Clear it
        result = tools.execute("update_code_memo", {"code_id": code_id})

        assert result["success"]
        assert result["data"]["old_memo"] == "Some memo"
        assert result["data"]["new_memo"] is None

    @allure.title("AC #2: memo persists via get_code")
    def test_update_memo_persists(self, project_with_codes):
        tools = project_with_codes["tools"]
        code_id = project_with_codes["codes"]["anxiety"]["code_id"]

        tools.execute(
            "update_code_memo", {"code_id": code_id, "memo": "Test memo content"}
        )

        get_result = tools.execute("get_code", {"code_id": code_id})
        assert get_result["data"]["memo"] == "Test memo content"


@allure.story("QC-050.03 create_category MCP tool")
class TestCreateCategoryMCP:
    @allure.title("AC #3: create_category with name only")
    def test_create_category_basic(self, project_with_codes):
        tools = project_with_codes["tools"]

        result = tools.execute("create_category", {"name": "Emotional Responses"})

        assert result["success"]
        assert result["data"]["name"] == "Emotional Responses"
        assert result["data"]["category_id"] is not None
        assert result["data"]["parent_id"] is None

    @allure.title("AC #3: create_category with parent_id and memo")
    def test_create_category_with_parent(self, project_with_codes):
        tools = project_with_codes["tools"]

        parent = tools.execute("create_category", {"name": "Themes"})
        assert parent["success"]
        parent_id = parent["data"]["category_id"]

        child = tools.execute(
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

    @allure.title("AC #3: create_category returns error for missing name")
    def test_create_category_missing_name(self, project_with_codes):
        tools = project_with_codes["tools"]

        result = tools.execute("create_category", {})

        assert not result["success"]
        assert "MISSING_PARAM" in result["error_code"]


@allure.story("QC-050.04 move_code_to_category MCP tool")
class TestMoveCodeToCategoryMCP:
    @allure.title("AC #4: move_code_to_category assigns code to category")
    def test_move_code_to_category(self, project_with_codes):
        tools = project_with_codes["tools"]
        code_id = project_with_codes["codes"]["anxiety"]["code_id"]

        cat = tools.execute("create_category", {"name": "Emotional Responses"})
        cat_id = cat["data"]["category_id"]

        result = tools.execute(
            "move_code_to_category", {"code_id": code_id, "category_id": cat_id}
        )

        assert result["success"]
        assert result["data"]["code_id"] == code_id
        assert result["data"]["old_category_id"] is None
        assert result["data"]["new_category_id"] == cat_id

    @allure.title("AC #4: move_code_to_category uncategorizes with null category_id")
    def test_uncategorize_code(self, project_with_codes):
        tools = project_with_codes["tools"]
        code_id = project_with_codes["codes"]["anxiety"]["code_id"]

        # Move to category first
        cat = tools.execute("create_category", {"name": "Temp"})
        cat_id = cat["data"]["category_id"]
        tools.execute(
            "move_code_to_category", {"code_id": code_id, "category_id": cat_id}
        )

        # Uncategorize
        result = tools.execute("move_code_to_category", {"code_id": code_id})

        assert result["success"]
        assert result["data"]["old_category_id"] == cat_id
        assert result["data"]["new_category_id"] is None

    @allure.title("AC #4: code category visible via get_code")
    def test_move_persists(self, project_with_codes):
        tools = project_with_codes["tools"]
        code_id = project_with_codes["codes"]["anxiety"]["code_id"]

        cat = tools.execute("create_category", {"name": "Emotions"})
        cat_id = cat["data"]["category_id"]
        tools.execute(
            "move_code_to_category", {"code_id": code_id, "category_id": cat_id}
        )

        get_result = tools.execute("get_code", {"code_id": code_id})
        assert get_result["data"]["category_id"] == cat_id


@allure.story("QC-050.05 merge_codes MCP tool")
class TestMergeCodesMCP:
    @allure.title("AC #5: merge_codes merges source into target")
    def test_merge_codes_success(self, project_with_codes):
        tools = project_with_codes["tools"]
        source_id = project_with_codes["codes"]["anxiety"]["code_id"]
        target_id = project_with_codes["codes"]["stress"]["code_id"]

        result = tools.execute(
            "merge_codes",
            {"source_code_id": source_id, "target_code_id": target_id},
        )

        assert result["success"]
        assert result["data"]["source_code_id"] == source_id
        assert result["data"]["target_code_id"] == target_id
        assert result["data"]["segments_moved"] >= 0

    @allure.title("AC #5: source code deleted after merge")
    def test_merge_deletes_source(self, project_with_codes):
        tools = project_with_codes["tools"]
        source_id = project_with_codes["codes"]["anxiety"]["code_id"]
        target_id = project_with_codes["codes"]["stress"]["code_id"]

        tools.execute(
            "merge_codes",
            {"source_code_id": source_id, "target_code_id": target_id},
        )

        get_result = tools.execute("get_code", {"code_id": source_id})
        assert not get_result["success"]  # Source code no longer exists

    @allure.title("AC #5: merge_codes returns error for missing params")
    def test_merge_missing_params(self, project_with_codes):
        tools = project_with_codes["tools"]

        result = tools.execute("merge_codes", {"source_code_id": "abc"})
        assert not result["success"]
        assert "MISSING_PARAM" in result["error_code"]


@allure.story("QC-050.06 delete_code MCP tool")
class TestDeleteCodeMCP:
    @allure.title("AC #6: delete_code removes code")
    def test_delete_code_success(self, project_with_codes):
        tools = project_with_codes["tools"]
        code_id = project_with_codes["codes"]["resilience"]["code_id"]

        result = tools.execute("delete_code", {"code_id": code_id})

        assert result["success"]
        assert result["data"]["deleted"] is True
        assert result["data"]["code_id"] == code_id

    @allure.title("AC #6: delete_code with delete_segments flag")
    def test_delete_code_with_segments(self, project_with_codes):
        tools = project_with_codes["tools"]
        # Anxiety has a segment applied
        code_id = project_with_codes["codes"]["anxiety"]["code_id"]

        result = tools.execute(
            "delete_code", {"code_id": code_id, "delete_segments": True}
        )

        assert result["success"]
        assert result["data"]["deleted"] is True

    @allure.title("AC #6: delete_code returns error for missing code_id")
    def test_delete_code_missing_id(self, project_with_codes):
        tools = project_with_codes["tools"]

        result = tools.execute("delete_code", {})
        assert not result["success"]
        assert "MISSING_PARAM" in result["error_code"]


@allure.story("QC-050.07 list_categories MCP tool")
class TestListCategoriesMCP:
    @allure.title("AC #7: list_categories returns empty list initially")
    def test_list_categories_empty(self, project_with_codes):
        tools = project_with_codes["tools"]

        result = tools.execute("list_categories", {})

        assert result["success"]
        assert result["data"] == []

    @allure.title("AC #7: list_categories returns categories with hierarchy")
    def test_list_categories_with_hierarchy(self, project_with_codes):
        tools = project_with_codes["tools"]

        # Create parent + child categories
        parent = tools.execute("create_category", {"name": "Themes"})
        parent_id = parent["data"]["category_id"]
        tools.execute(
            "create_category", {"name": "Emotional", "parent_id": parent_id}
        )

        result = tools.execute("list_categories", {})

        assert result["success"]
        assert len(result["data"]) == 2
        names = {c["name"] for c in result["data"]}
        assert "Themes" in names
        assert "Emotional" in names

        # Check parent_id relationship
        child = next(c for c in result["data"] if c["name"] == "Emotional")
        assert child["parent_id"] == parent_id

    @allure.title("AC #7: list_categories includes code counts")
    def test_list_categories_code_counts(self, project_with_codes):
        tools = project_with_codes["tools"]
        code_id = project_with_codes["codes"]["anxiety"]["code_id"]

        cat = tools.execute("create_category", {"name": "Emotions"})
        cat_id = cat["data"]["category_id"]

        # Move a code into the category
        tools.execute(
            "move_code_to_category", {"code_id": code_id, "category_id": cat_id}
        )

        result = tools.execute("list_categories", {})

        assert result["success"]
        emotions_cat = next(c for c in result["data"] if c["name"] == "Emotions")
        assert emotions_cat["code_count"] == 1


@allure.story("QC-050.08 Tool registration")
class TestToolRegistration:
    @allure.title("AC #8: All new tools are registered in ALL_HANDLERS and ALL_TOOLS")
    def test_all_tools_registered(self, app_context, tmp_path):
        project_path = tmp_path / "test_reg.qda"
        app_context.create_project("Reg Test", str(project_path))
        app_context.open_project(str(project_path))
        tools = CodingTools(ctx=app_context)

        tool_names = tools.get_tool_names()
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

    @allure.title("AC #10: All tools return OperationResult.to_dict() format")
    def test_tools_return_operation_result_format(self, project_with_codes):
        tools = project_with_codes["tools"]

        # Test each tool returns proper format
        for tool_name, args in [
            ("rename_code", {"code_id": "nonexistent", "new_name": "x"}),
            ("update_code_memo", {"code_id": "nonexistent", "memo": "x"}),
            ("create_category", {}),  # Missing name → error
            ("move_code_to_category", {}),  # Missing code_id → error
            ("merge_codes", {}),  # Missing params → error
            ("delete_code", {}),  # Missing code_id → error
            ("list_categories", {}),
        ]:
            result = tools.execute(tool_name, args)
            assert "success" in result, f"{tool_name} missing 'success' key"
            # Success or error should have proper structure
            if result["success"]:
                assert "data" in result
            else:
                assert "error" in result or "error_code" in result
