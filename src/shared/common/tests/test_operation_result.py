"""
Tests for OperationResult - the rich result type for use cases.

Key business logic tested:
- Factory methods (ok, fail, from_failure)
- Unwrap variants (unwrap, unwrap_or, unwrap_error)
- Transformation (map, with_rollback)
- Serialization (to_dict)
"""

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult


class TestOperationResultOk:
    """Test OperationResult.ok() factory method."""

    def test_ok_creates_success_result(self):
        result = OperationResult.ok(data="created_entity")

        assert result.success is True
        assert result.is_success is True
        assert result.is_failure is False
        assert result.data == "created_entity"

    def test_ok_with_no_data(self):
        result = OperationResult.ok()

        assert result.success is True
        assert result.data is None

    def test_ok_with_rollback_command(self):
        rollback = {"action": "delete", "id": 123}
        result = OperationResult.ok(data="entity", rollback=rollback)

        assert result.rollback_command == rollback

    def test_ok_has_no_error_fields(self):
        result = OperationResult.ok(data="entity")

        assert result.error is None
        assert result.error_code is None
        assert result.suggestions == ()


class TestOperationResultFail:
    """Test OperationResult.fail() factory method."""

    def test_fail_creates_failure_result(self):
        result = OperationResult.fail(error="Something went wrong")

        assert result.success is False
        assert result.is_success is False
        assert result.is_failure is True
        assert result.error == "Something went wrong"

    def test_fail_with_error_code(self):
        result = OperationResult.fail(
            error="Name exists",
            error_code="CODE_NOT_CREATED/DUPLICATE_NAME",
        )

        assert result.error_code == "CODE_NOT_CREATED/DUPLICATE_NAME"

    def test_fail_with_suggestions_as_tuple(self):
        result = OperationResult.fail(
            error="Name exists",
            suggestions=("Try a different name", "Rename existing"),
        )

        assert result.suggestions == ("Try a different name", "Rename existing")

    def test_fail_with_suggestions_as_list_converts_to_tuple(self):
        result = OperationResult.fail(
            error="Name exists",
            suggestions=["Try a different name", "Rename existing"],
        )

        assert result.suggestions == ("Try a different name", "Rename existing")
        assert isinstance(result.suggestions, tuple)

    def test_fail_has_no_data_or_rollback(self):
        result = OperationResult.fail(error="error")

        assert result.data is None
        assert result.rollback_command is None


class TestOperationResultFromFailure:
    """Test OperationResult.from_failure() for converting failure events."""

    def test_from_failure_extracts_event_type_as_error_code(self):
        event = FailureEvent(
            event_id="evt-1",
            occurred_at=datetime.now(UTC),
            event_type="CODE_NOT_CREATED/DUPLICATE_NAME",
        )

        result = OperationResult.from_failure(event)

        assert result.success is False
        assert result.error_code == "CODE_NOT_CREATED/DUPLICATE_NAME"

    def test_from_failure_uses_event_message(self):
        event = FailureEvent(
            event_id="evt-1",
            occurred_at=datetime.now(UTC),
            event_type="CODE_NOT_CREATED/DUPLICATE_NAME",
        )

        result = OperationResult.from_failure(event)

        # FailureEvent.message is auto-generated from event_type
        assert "Code Not Created" in result.error

    def test_from_failure_extracts_suggestions_if_present(self):
        @dataclass(frozen=True)
        class FailureEventWithSuggestions(FailureEvent):
            suggestions: tuple[str, ...] = ()

        event = FailureEventWithSuggestions(
            event_id="evt-1",
            occurred_at=datetime.now(UTC),
            event_type="CODE_NOT_CREATED/DUPLICATE_NAME",
            suggestions=("Use different name", "Delete existing"),
        )

        result = OperationResult.from_failure(event)

        assert result.suggestions == ("Use different name", "Delete existing")

    def test_from_failure_handles_missing_suggestions(self):
        event = FailureEvent(
            event_id="evt-1",
            occurred_at=datetime.now(UTC),
            event_type="PROJECT_NOT_OPENED/NOT_FOUND",
        )

        result = OperationResult.from_failure(event)

        assert result.suggestions == ()


class TestOperationResultUnwrap:
    """Test unwrap methods for accessing result data."""

    def test_unwrap_returns_data_on_success(self):
        result = OperationResult.ok(data={"id": 42, "name": "Test"})

        assert result.unwrap() == {"id": 42, "name": "Test"}

    def test_unwrap_raises_value_error_on_failure(self):
        result = OperationResult.fail(error="Cannot create")

        with pytest.raises(ValueError, match="Cannot unwrap failed result"):
            result.unwrap()

    def test_unwrap_error_message_includes_original_error(self):
        result = OperationResult.fail(error="Duplicate name 'Theme'")

        with pytest.raises(ValueError, match="Duplicate name 'Theme'"):
            result.unwrap()

    def test_unwrap_or_returns_data_on_success(self):
        result = OperationResult.ok(data="actual_value")

        assert result.unwrap_or("default") == "actual_value"

    def test_unwrap_or_returns_default_on_failure(self):
        result = OperationResult.fail(error="error")

        assert result.unwrap_or("default") == "default"

    def test_unwrap_or_returns_none_default(self):
        result = OperationResult.fail(error="error")

        assert result.unwrap_or(None) is None

    def test_unwrap_error_returns_error_on_failure(self):
        result = OperationResult.fail(error="Something broke")

        assert result.unwrap_error() == "Something broke"

    def test_unwrap_error_raises_on_success(self):
        result = OperationResult.ok(data="value")

        with pytest.raises(ValueError, match="Cannot unwrap_error on successful"):
            result.unwrap_error()

    def test_unwrap_error_returns_empty_string_when_error_is_none(self):
        # Edge case: failure result with None error (shouldn't happen, but handle it)
        result = OperationResult(success=False, error=None)

        assert result.unwrap_error() == ""


class TestOperationResultMap:
    """Test map() transformation method."""

    def test_map_transforms_data_on_success(self):
        result = OperationResult.ok(data=5)

        mapped = result.map(lambda x: x * 2)

        assert mapped.success is True
        assert mapped.data == 10

    def test_map_preserves_rollback_command(self):
        rollback = {"action": "undo"}
        result = OperationResult.ok(data=5, rollback=rollback)

        mapped = result.map(lambda x: x * 2)

        assert mapped.rollback_command == rollback

    def test_map_returns_self_on_failure(self):
        result = OperationResult.fail(error="error", error_code="ERR")

        mapped = result.map(lambda x: x * 2)

        assert mapped is result  # Same object, not transformed
        assert mapped.is_failure is True
        assert mapped.error == "error"

    def test_map_can_transform_to_different_type(self):
        result = OperationResult.ok(data={"id": 1, "name": "Test"})

        mapped = result.map(lambda d: d["name"])

        assert mapped.data == "Test"


class TestOperationResultWithRollback:
    """Test with_rollback() method."""

    def test_with_rollback_adds_command_to_success(self):
        result = OperationResult.ok(data="entity")

        with_rb = result.with_rollback({"action": "delete"})

        assert with_rb.rollback_command == {"action": "delete"}
        assert with_rb.data == "entity"
        assert with_rb.success is True

    def test_with_rollback_replaces_existing_command(self):
        result = OperationResult.ok(data="entity", rollback={"old": "cmd"})

        with_rb = result.with_rollback({"new": "cmd"})

        assert with_rb.rollback_command == {"new": "cmd"}

    def test_with_rollback_preserves_all_other_fields(self):
        result = OperationResult.fail(
            error="err",
            error_code="ERR/CODE",
            suggestions=("hint1", "hint2"),
        )

        with_rb = result.with_rollback({"cmd": "value"})

        assert with_rb.error == "err"
        assert with_rb.error_code == "ERR/CODE"
        assert with_rb.suggestions == ("hint1", "hint2")
        assert with_rb.rollback_command == {"cmd": "value"}


class TestOperationResultToDict:
    """Test to_dict() serialization for MCP tools."""

    def test_to_dict_success_with_primitive_data(self):
        result = OperationResult.ok(data=42)

        d = result.to_dict()

        assert d == {"success": True, "data": 42}

    def test_to_dict_success_with_none_data(self):
        result = OperationResult.ok()

        d = result.to_dict()

        assert d == {"success": True}

    def test_to_dict_success_with_object_having_to_dict(self):
        class Entity:
            def to_dict(self):
                return {"id": 1, "name": "Test"}

        result = OperationResult.ok(data=Entity())

        d = result.to_dict()

        assert d == {"success": True, "data": {"id": 1, "name": "Test"}}

    def test_to_dict_success_with_object_having_dict_attribute(self):
        @dataclass
        class SimpleEntity:
            id: int
            name: str

        result = OperationResult.ok(data=SimpleEntity(id=1, name="Test"))

        d = result.to_dict()

        assert d["success"] is True
        assert d["data"]["id"] == 1
        assert d["data"]["name"] == "Test"

    def test_to_dict_failure_minimal(self):
        result = OperationResult.fail(error="Something failed")

        d = result.to_dict()

        assert d == {"success": False, "error": "Something failed"}

    def test_to_dict_failure_with_error_code(self):
        result = OperationResult.fail(
            error="Name exists",
            error_code="CODE_NOT_CREATED/DUPLICATE_NAME",
        )

        d = result.to_dict()

        assert d["error_code"] == "CODE_NOT_CREATED/DUPLICATE_NAME"

    def test_to_dict_failure_with_suggestions(self):
        result = OperationResult.fail(
            error="Name exists",
            suggestions=("Try different name", "Delete existing"),
        )

        d = result.to_dict()

        assert d["suggestions"] == ["Try different name", "Delete existing"]

    def test_to_dict_failure_does_not_include_empty_suggestions(self):
        result = OperationResult.fail(error="error")

        d = result.to_dict()

        assert "suggestions" not in d


class TestOperationResultImmutability:
    """Test that OperationResult is immutable (frozen dataclass)."""

    def test_cannot_modify_success_field(self):
        result = OperationResult.ok(data="value")

        with pytest.raises(AttributeError):
            result.success = False

    def test_cannot_modify_data_field(self):
        result = OperationResult.ok(data="value")

        with pytest.raises(AttributeError):
            result.data = "new_value"
