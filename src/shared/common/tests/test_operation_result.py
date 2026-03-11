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

import allure
import pytest

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("Shared Common"),
]

from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult


@allure.story("QC-000.03 Operation Result")
class TestOperationResultFactories:
    """Test factory methods: ok(), fail(), from_failure()."""

    @allure.title("ok() creates success result with data, rollback, and defaults")
    def test_ok_creates_success_result(self):
        rollback = {"action": "delete", "id": 123}
        result = OperationResult.ok(data="created_entity", rollback=rollback)

        assert result.success is True
        assert result.is_success is True
        assert result.is_failure is False
        assert result.data == "created_entity"
        assert result.rollback_command == rollback
        assert result.error is None
        assert result.error_code is None
        assert result.suggestions == ()

        # No-data variant
        empty = OperationResult.ok()
        assert empty.success is True
        assert empty.data is None

    @allure.title("fail() creates failure and normalizes suggestions")
    @pytest.mark.parametrize(
        "suggestions_input,expected_suggestions",
        [
            (None, ()),
            (("Try a different name", "Rename existing"), ("Try a different name", "Rename existing")),
            (["Try a different name", "Rename existing"], ("Try a different name", "Rename existing")),
        ],
        ids=["no_suggestions", "tuple_suggestions", "list_suggestions"],
    )
    def test_fail_creates_failure_and_normalizes_suggestions(self, suggestions_input, expected_suggestions):
        kwargs = {"error": "Name exists", "error_code": "CODE_NOT_CREATED/DUPLICATE_NAME"}
        if suggestions_input is not None:
            kwargs["suggestions"] = suggestions_input

        result = OperationResult.fail(**kwargs)

        assert result.success is False
        assert result.is_success is False
        assert result.is_failure is True
        assert result.error == "Name exists"
        assert result.error_code == "CODE_NOT_CREATED/DUPLICATE_NAME"
        assert result.data is None
        assert result.rollback_command is None
        assert result.suggestions == expected_suggestions
        assert isinstance(result.suggestions, tuple)

    @allure.title("from_failure() extracts fields and handles suggestions")
    def test_from_failure_extracts_fields(self):
        event = FailureEvent(
            event_id="evt-1",
            occurred_at=datetime.now(UTC),
            event_type="CODE_NOT_CREATED/DUPLICATE_NAME",
        )

        result = OperationResult.from_failure(event)

        assert result.success is False
        assert result.error_code == "CODE_NOT_CREATED/DUPLICATE_NAME"
        assert "Code Not Created" in result.error
        assert result.suggestions == ()

        # With suggestions
        @dataclass(frozen=True)
        class FailureEventWithSuggestions(FailureEvent):
            suggestions: tuple[str, ...] = ()

        event_with = FailureEventWithSuggestions(
            event_id="evt-2",
            occurred_at=datetime.now(UTC),
            event_type="CODE_NOT_CREATED/DUPLICATE_NAME",
            suggestions=("Use different name", "Delete existing"),
        )

        result_with = OperationResult.from_failure(event_with)
        assert result_with.suggestions == ("Use different name", "Delete existing")


@allure.story("QC-000.03 Operation Result")
class TestOperationResultUnwrap:
    """Test unwrap methods for accessing result data."""

    @allure.title("unwrap, unwrap_or, and unwrap_error behave correctly")
    def test_unwrap_variants(self):
        # unwrap returns data on success
        ok_result = OperationResult.ok(data={"id": 42, "name": "Test"})
        assert ok_result.unwrap() == {"id": 42, "name": "Test"}

        # unwrap raises ValueError on failure
        fail_result = OperationResult.fail(error="Cannot create")
        with pytest.raises(ValueError, match="Cannot unwrap failed result"):
            fail_result.unwrap()

        fail_result2 = OperationResult.fail(error="Duplicate name 'Theme'")
        with pytest.raises(ValueError, match="Duplicate name 'Theme'"):
            fail_result2.unwrap()

        # unwrap_or returns data on success, default on failure
        assert ok_result.unwrap_or("default") == {"id": 42, "name": "Test"}
        assert fail_result.unwrap_or("default") == "default"
        assert fail_result.unwrap_or(None) is None

        # unwrap_error returns error string on failure, raises on success
        assert OperationResult.fail(error="Something broke").unwrap_error() == "Something broke"
        assert OperationResult(success=False, error=None).unwrap_error() == ""

        with pytest.raises(ValueError, match="Cannot unwrap_error on successful"):
            ok_result.unwrap_error()


@allure.story("QC-000.03 Operation Result")
class TestOperationResultTransformAndSerialize:
    """Test map(), with_rollback(), and to_dict()."""

    @allure.title("map transforms success data and passes through failure")
    def test_map(self):
        rollback = {"action": "undo"}
        result = OperationResult.ok(data=5, rollback=rollback)

        mapped = result.map(lambda x: x * 2)
        assert mapped.success is True
        assert mapped.data == 10
        assert mapped.rollback_command == rollback

        # Can transform to a different type
        dict_result = OperationResult.ok(data={"id": 1, "name": "Test"})
        assert dict_result.map(lambda d: d["name"]).data == "Test"

        # Failure passes through unchanged
        fail_result = OperationResult.fail(error="error", error_code="ERR")
        fail_mapped = fail_result.map(lambda x: x * 2)
        assert fail_mapped is fail_result
        assert fail_mapped.is_failure is True

    @allure.title("with_rollback adds command and preserves all fields")
    def test_with_rollback(self):
        result = OperationResult.ok(data="entity", rollback={"old": "cmd"})
        with_rb = result.with_rollback({"new": "cmd"})
        assert with_rb.rollback_command == {"new": "cmd"}
        assert with_rb.data == "entity"
        assert with_rb.success is True

        fail_result = OperationResult.fail(
            error="err", error_code="ERR/CODE", suggestions=("hint1", "hint2"),
        )
        fail_with_rb = fail_result.with_rollback({"cmd": "value"})
        assert fail_with_rb.error == "err"
        assert fail_with_rb.error_code == "ERR/CODE"
        assert fail_with_rb.suggestions == ("hint1", "hint2")
        assert fail_with_rb.rollback_command == {"cmd": "value"}

    @allure.title("to_dict serializes success and failure correctly")
    def test_to_dict(self):
        # Primitive data
        d = OperationResult.ok(data=42).to_dict()
        assert d["success"] is True
        assert d["data"] == 42

        # None data is omitted
        d_none = OperationResult.ok(data=None).to_dict()
        assert d_none["success"] is True
        assert "data" not in d_none

        # Object with to_dict() method
        class Entity:
            def to_dict(self):
                return {"id": 1, "name": "Test"}

        d_entity = OperationResult.ok(data=Entity()).to_dict()
        assert d_entity == {"success": True, "data": {"id": 1, "name": "Test"}}

        # Dataclass with __dict__
        @dataclass
        class SimpleEntity:
            id: int
            name: str

        d_dc = OperationResult.ok(data=SimpleEntity(id=1, name="Test")).to_dict()
        assert d_dc["success"] is True
        assert d_dc["data"]["id"] == 1
        assert d_dc["data"]["name"] == "Test"

        # Full failure with all fields
        result = OperationResult.fail(
            error="Name exists",
            error_code="CODE_NOT_CREATED/DUPLICATE_NAME",
            suggestions=("Try different name", "Delete existing"),
        )
        d = result.to_dict()
        assert d["success"] is False
        assert d["error"] == "Name exists"
        assert d["error_code"] == "CODE_NOT_CREATED/DUPLICATE_NAME"
        assert d["suggestions"] == ["Try different name", "Delete existing"]

        # Minimal failure omits optional fields
        d_minimal = OperationResult.fail(error="Something failed").to_dict()
        assert d_minimal == {"success": False, "error": "Something failed"}
        assert "suggestions" not in d_minimal
