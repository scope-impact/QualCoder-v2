"""
Tests for shared domain types - focusing on behavior and invariants.
"""

from datetime import UTC, datetime

import pytest
from returns.primitives.exceptions import UnwrapFailedError

from src.contexts.shared.core.types import (
    CategoryId,
    CodeId,
    CodeNotFound,
    DomainEvent,
    DuplicateName,
    EmptyName,
    Failure,
    InvalidPosition,
    SegmentId,
    SourceId,
    SourceNotFound,
    Success,
)


class TestTypedIds:
    """Tests for typed identifier value objects"""

    def test_code_id_new_generates_unique_values(self):
        """CodeId.new() should generate different values across calls"""
        ids = [CodeId.new() for _ in range(50)]
        unique_values = {id.value for id in ids}
        assert len(unique_values) == 50

    def test_segment_id_new_generates_unique_values(self):
        """SegmentId.new() should generate different values across calls"""
        ids = [SegmentId.new() for _ in range(50)]
        unique_values = {id.value for id in ids}
        assert len(unique_values) == 50

    def test_ids_are_hashable_for_set_membership(self):
        """IDs should be usable in sets for deduplication"""
        code_id = CodeId(value=42)
        segment_id = SegmentId(value=42)
        source_id = SourceId(value=42)
        CategoryId(value=42)

        # Each can be added to a set
        code_set = {code_id, CodeId(value=42)}
        assert len(code_set) == 1  # Duplicates collapsed

        # Can use as dict keys
        lookup = {code_id: "theme", segment_id: "seg", source_id: "src"}
        assert lookup[CodeId(value=42)] == "theme"


class TestResultMonad:
    """Tests for Result type (Success | Failure) behavior - using returns library"""

    def test_success_map_applies_transformation(self):
        """Success.map(fn) should apply fn and return new Success"""
        result = Success(5)
        mapped = result.map(lambda x: x * 2)

        assert isinstance(mapped, Success)
        assert mapped.unwrap() == 10

    def test_success_map_chaining(self):
        """Multiple map calls should chain correctly"""
        result = Success(2)
        chained = result.map(lambda x: x * 3).map(lambda x: x + 1)

        assert isinstance(chained, Success)
        assert chained.unwrap() == 7  # (2 * 3) + 1

    def test_failure_map_short_circuits(self):
        """Failure.map(fn) should return same Failure without calling fn"""
        call_count = 0

        def should_not_be_called(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result = Failure("oops")
        mapped = result.map(should_not_be_called)

        assert isinstance(mapped, Failure)
        assert mapped.failure() == "oops"
        assert call_count == 0  # Function was never called

    def test_success_unwrap_returns_value(self):
        """Success.unwrap() should return the wrapped value"""
        result = Success("hello")
        assert result.unwrap() == "hello"

    def test_failure_unwrap_raises(self):
        """Failure.unwrap() should raise UnwrapFailedError"""
        result = Failure("something went wrong")

        with pytest.raises(UnwrapFailedError):
            result.unwrap()


class TestDomainEvent:
    """Tests for DomainEvent base class"""

    def test_generate_id_produces_unique_uuids(self):
        """_generate_id() should produce unique UUID strings"""
        ids = [DomainEvent._generate_id() for _ in range(50)]
        unique_ids = set(ids)

        assert len(unique_ids) == 50
        assert all(len(id) == 36 for id in ids)  # UUID format

    def test_now_returns_current_timestamp(self):
        """_now() should return approximately current time"""
        before = datetime.now(UTC)
        event_time = DomainEvent._now()
        after = datetime.now(UTC)

        assert before <= event_time <= after


class TestFailureReasons:
    """Tests for failure reason types - message generation"""

    def test_duplicate_name_message_contains_name(self):
        """DuplicateName message should include the duplicate name"""
        failure = DuplicateName(name="Theme A")
        assert "Theme A" in failure.message
        assert "already exists" in failure.message

    def test_code_not_found_message_contains_id(self):
        """CodeNotFound message should include the code ID"""
        failure = CodeNotFound(code_id=CodeId(value=123))
        assert "123" in failure.message
        assert "not found" in failure.message

    def test_source_not_found_message_contains_id(self):
        """SourceNotFound message should include the source ID"""
        failure = SourceNotFound(source_id=SourceId(value=456))
        assert "456" in failure.message
        assert "not found" in failure.message

    def test_invalid_position_message_contains_all_values(self):
        """InvalidPosition message should include start, end, and source length"""
        failure = InvalidPosition(start=100, end=50, source_length=200)
        assert "100" in failure.message
        assert "50" in failure.message
        assert "200" in failure.message

    def test_empty_name_has_meaningful_message(self):
        """EmptyName should have a default message about empty names"""
        failure = EmptyName()
        assert "empty" in failure.message.lower()
