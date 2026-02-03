"""
Tests for shared types - typed identifiers and failure reasons.

Key business logic tested:
- Failure reason classes auto-generate human-readable messages
- Typed identifiers are frozen and hashable
"""

import pytest

from src.shared.common.types import (
    CaseId,
    CodeId,
    CodeNotFound,
    DomainEvent,
    DuplicateName,
    EmptyName,
    FolderId,
    FolderNotFound,
    InvalidPosition,
    SegmentId,
    SourceId,
    SourceNotFound,
)


class TestTypedIdentifiers:
    """Test typed identifier classes."""

    def test_code_id_new_generates_unique_ids(self):
        id1 = CodeId.new()
        id2 = CodeId.new()

        assert id1.value != id2.value

    def test_segment_id_new_generates_unique_ids(self):
        id1 = SegmentId.new()
        id2 = SegmentId.new()

        assert id1.value != id2.value

    def test_case_id_new_generates_unique_ids(self):
        id1 = CaseId.new()
        id2 = CaseId.new()

        assert id1.value != id2.value

    def test_folder_id_new_generates_unique_ids(self):
        id1 = FolderId.new()
        id2 = FolderId.new()

        assert id1.value != id2.value

    def test_typed_ids_are_frozen(self):
        code_id = CodeId(value=1)

        with pytest.raises(AttributeError):
            code_id.value = 2

    def test_typed_ids_are_hashable(self):
        code_id = CodeId(value=1)

        # Should be usable as dict key
        d = {code_id: "test"}
        assert d[code_id] == "test"

    def test_typed_ids_equality(self):
        id1 = CodeId(value=42)
        id2 = CodeId(value=42)
        id3 = CodeId(value=99)

        assert id1 == id2
        assert id1 != id3


class TestDuplicateName:
    """Test DuplicateName failure reason."""

    def test_auto_generates_message(self):
        failure = DuplicateName(name="Theme")

        assert failure.message == "Code name 'Theme' already exists"

    def test_message_includes_name(self):
        failure = DuplicateName(name="My Special Code")

        assert "My Special Code" in failure.message


class TestCodeNotFound:
    """Test CodeNotFound failure reason."""

    def test_auto_generates_message(self):
        failure = CodeNotFound(code_id=CodeId(value=42))

        assert failure.message == "Code with id 42 not found"

    def test_message_includes_id(self):
        failure = CodeNotFound(code_id=CodeId(value=12345))

        assert "12345" in failure.message


class TestSourceNotFound:
    """Test SourceNotFound failure reason."""

    def test_auto_generates_message(self):
        failure = SourceNotFound(source_id=SourceId(value=99))

        assert failure.message == "Source with id 99 not found"


class TestInvalidPosition:
    """Test InvalidPosition failure reason."""

    def test_auto_generates_message(self):
        failure = InvalidPosition(start=100, end=200, source_length=50)

        assert "Position [100:200]" in failure.message
        assert "length 50" in failure.message

    def test_message_shows_all_values(self):
        failure = InvalidPosition(start=0, end=10, source_length=5)

        assert "0" in failure.message
        assert "10" in failure.message
        assert "5" in failure.message


class TestEmptyName:
    """Test EmptyName failure reason."""

    def test_has_default_message(self):
        failure = EmptyName()

        assert failure.message == "Code name cannot be empty"


class TestFolderNotFound:
    """Test FolderNotFound failure reason."""

    def test_auto_generates_message(self):
        failure = FolderNotFound(folder_id=FolderId(value=7))

        assert failure.message == "Folder with id 7 not found"


class TestFailureReasonsAreFrozen:
    """Test that failure reasons are immutable."""

    def test_duplicate_name_frozen(self):
        failure = DuplicateName(name="Test")

        with pytest.raises(AttributeError):
            failure.name = "Other"

    def test_code_not_found_frozen(self):
        failure = CodeNotFound(code_id=CodeId(value=1))

        with pytest.raises(AttributeError):
            failure.code_id = CodeId(value=2)


class TestDomainEvent:
    """Test DomainEvent base class."""

    def test_generate_id_creates_unique_ids(self):
        id1 = DomainEvent._generate_id()
        id2 = DomainEvent._generate_id()

        assert id1 != id2
        assert isinstance(id1, str)

    def test_now_returns_utc_datetime(self):
        from datetime import UTC

        ts = DomainEvent._now()

        assert ts.tzinfo == UTC
