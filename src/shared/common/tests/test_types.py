"""
Tests for shared types - typed identifiers and failure reasons.

Consolidated tests for:
- Typed identifiers (uniqueness, equality, hashability)
- Failure reason message generation
- DomainEvent utilities
"""

import allure
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


@allure.epic("QualCoder v2")
@allure.feature("Shared Common")
@allure.story("QC-000.04 Domain Types")
class TestTypedIdentifiers:
    """Test typed identifier classes."""

    @allure.title(
        "Typed IDs generate unique values, support equality, and are hashable"
    )
    def test_uniqueness_equality_and_hashability(self):
        for id_cls in (CodeId, SegmentId, CaseId, FolderId):
            id1 = id_cls.new()
            id2 = id_cls.new()
            assert id1.value != id2.value, (
                f"{id_cls.__name__} did not generate unique IDs"
            )

        # Equality and hashing
        id1 = CodeId(value="42")
        id2 = CodeId(value="42")
        id3 = CodeId(value="99")

        assert id1 == id2
        assert id1 != id3
        d = {id1: "test"}
        assert d[id2] == "test"


@allure.epic("QualCoder v2")
@allure.feature("Shared Common")
@allure.story("QC-000.04 Domain Types")
class TestFailureReasons:
    """Test failure reason message generation."""

    @allure.title("Failure reason '{reason_type}' generates correct message")
    @pytest.mark.parametrize(
        "reason_type,create_fn,check_fn",
        [
            (
                "DuplicateName",
                lambda: DuplicateName(name="Theme"),
                lambda f: "Theme" in f.message
                and f.message == "Code name 'Theme' already exists",
            ),
            (
                "CodeNotFound",
                lambda: CodeNotFound(code_id=CodeId(value="42")),
                lambda f: f.message == "Code with id 42 not found",
            ),
            (
                "SourceNotFound",
                lambda: SourceNotFound(source_id=SourceId(value="99")),
                lambda f: f.message == "Source with id 99 not found",
            ),
            (
                "InvalidPosition",
                lambda: InvalidPosition(start=100, end=200, source_length=50),
                lambda f: "Position [100:200]" in f.message
                and "length 50" in f.message,
            ),
            (
                "EmptyName",
                lambda: EmptyName(),
                lambda f: f.message == "Code name cannot be empty",
            ),
            (
                "FolderNotFound",
                lambda: FolderNotFound(folder_id=FolderId(value="7")),
                lambda f: f.message == "Folder with id 7 not found",
            ),
        ],
        ids=[
            "duplicate_name",
            "code_not_found",
            "source_not_found",
            "invalid_position",
            "empty_name",
            "folder_not_found",
        ],
    )
    def test_failure_reason_messages(self, reason_type, create_fn, check_fn):
        failure = create_fn()
        assert check_fn(failure), (
            f"Message check failed for {reason_type}: {failure.message}"
        )


@allure.epic("QualCoder v2")
@allure.feature("Shared Common")
@allure.story("QC-000.04 Domain Types")
class TestDomainEvent:
    """Test DomainEvent base class."""

    @allure.title("DomainEvent generates unique IDs and UTC timestamps")
    def test_generate_id_and_timestamp(self):
        from datetime import UTC

        id1 = DomainEvent._generate_id()
        id2 = DomainEvent._generate_id()
        assert id1 != id2
        assert isinstance(id1, str)

        ts = DomainEvent._now()
        assert ts.tzinfo == UTC
