"""
Tests for AutoCodeBatch entity and batch operation derivers.

TDD tests written BEFORE implementation.
Extracted from presentation/dialogs/auto_code_dialog.py AutoCodeBatch.
"""

from datetime import datetime

import pytest

from src.domain.coding.derivers import (
    CodingState,
    derive_create_batch,
    derive_undo_batch,
)
from src.domain.coding.entities import AutoCodeBatch, BatchId
from src.domain.coding.events import BatchCreated, BatchUndone
from src.domain.shared.types import CodeId, Failure, SegmentId


class TestAutoCodeBatchEntity:
    """Tests for AutoCodeBatch entity."""

    def test_creates_batch_with_valid_data(self):
        """Should create batch with required attributes."""
        batch = AutoCodeBatch(
            id=BatchId.new(),
            code_id=CodeId(value=1),
            pattern="test pattern",
            segment_ids=(SegmentId(value=1), SegmentId(value=2)),
        )

        assert batch.code_id == CodeId(value=1)
        assert batch.pattern == "test pattern"
        assert len(batch.segment_ids) == 2

    def test_batch_is_frozen(self):
        """Batch should be immutable."""
        batch = AutoCodeBatch(
            id=BatchId.new(),
            code_id=CodeId(value=1),
            pattern="pattern",
            segment_ids=(),
        )

        with pytest.raises(AttributeError):
            batch.pattern = "new pattern"

    def test_batch_has_created_at_timestamp(self):
        """Batch should have creation timestamp."""
        batch = AutoCodeBatch(
            id=BatchId.new(),
            code_id=CodeId(value=1),
            pattern="pattern",
            segment_ids=(),
        )

        assert batch.created_at is not None
        assert isinstance(batch.created_at, datetime)

    def test_can_undo_returns_true_with_segments(self):
        """can_undo should return True when batch has segments."""
        batch = AutoCodeBatch(
            id=BatchId.new(),
            code_id=CodeId(value=1),
            pattern="pattern",
            segment_ids=(SegmentId(value=1),),
        )

        assert batch.can_undo() is True

    def test_can_undo_returns_false_without_segments(self):
        """can_undo should return False when batch has no segments."""
        batch = AutoCodeBatch(
            id=BatchId.new(),
            code_id=CodeId(value=1),
            pattern="pattern",
            segment_ids=(),
        )

        assert batch.can_undo() is False

    def test_batch_id_is_unique(self):
        """Each batch should have unique ID."""
        batch1 = AutoCodeBatch(
            id=BatchId.new(),
            code_id=CodeId(value=1),
            pattern="pattern",
            segment_ids=(),
        )
        batch2 = AutoCodeBatch(
            id=BatchId.new(),
            code_id=CodeId(value=1),
            pattern="pattern",
            segment_ids=(),
        )

        assert batch1.id != batch2.id


class TestBatchIdValueObject:
    """Tests for BatchId value object."""

    def test_creates_new_batch_id(self):
        """Should create new unique batch ID."""
        batch_id = BatchId.new()

        assert batch_id is not None
        assert batch_id.value is not None

    def test_batch_ids_are_unique(self):
        """Multiple new() calls should produce unique IDs."""
        ids = [BatchId.new() for _ in range(100)]
        unique_values = {id.value for id in ids}

        assert len(unique_values) == 100

    def test_batch_id_equality(self):
        """Same value should be equal."""
        id1 = BatchId(value="batch_abc123")
        id2 = BatchId(value="batch_abc123")

        assert id1 == id2

    def test_batch_id_is_frozen(self):
        """BatchId should be immutable."""
        batch_id = BatchId.new()

        with pytest.raises(AttributeError):
            batch_id.value = "new_value"


class TestDeriveCreateBatch:
    """Tests for derive_create_batch deriver."""

    def test_creates_batch_event(self, populated_state: CodingState):
        """Should create BatchCreated event for valid operation."""
        result = derive_create_batch(
            code_id=CodeId(value=1),
            pattern="search pattern",
            segment_ids=(SegmentId(value=10), SegmentId(value=11)),
            owner="user1",
            state=populated_state,
        )

        assert isinstance(result, BatchCreated)
        assert result.code_id == CodeId(value=1)
        assert result.pattern == "search pattern"
        assert len(result.segment_ids) == 2

    def test_creates_batch_with_empty_segments(self, populated_state: CodingState):
        """Should allow batch with no segments (dry run)."""
        result = derive_create_batch(
            code_id=CodeId(value=1),
            pattern="pattern",
            segment_ids=(),
            owner="user1",
            state=populated_state,
        )

        assert isinstance(result, BatchCreated)
        assert len(result.segment_ids) == 0

    def test_fails_with_invalid_code(self, populated_state: CodingState):
        """Should fail when code doesn't exist."""
        from src.domain.shared.types import CodeNotFound

        result = derive_create_batch(
            code_id=CodeId(value=999),
            pattern="pattern",
            segment_ids=(),
            owner="user1",
            state=populated_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), CodeNotFound)


class TestDeriveUndoBatch:
    """Tests for derive_undo_batch deriver."""

    def test_undoes_existing_batch(self, state_with_batch: CodingState):
        """Should create BatchUndone event for existing batch."""
        batch_id = state_with_batch.existing_batches[0].id

        result = derive_undo_batch(
            batch_id=batch_id,
            state=state_with_batch,
        )

        assert isinstance(result, BatchUndone)
        assert result.batch_id == batch_id

    def test_fails_for_nonexistent_batch(self, populated_state: CodingState):
        """Should fail when batch doesn't exist."""
        from src.domain.coding.derivers import BatchNotFound

        result = derive_undo_batch(
            batch_id=BatchId(value="nonexistent"),
            state=populated_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), BatchNotFound)


# Fixtures for batch tests
@pytest.fixture
def state_with_batch(populated_state: CodingState) -> CodingState:
    """State with an existing batch for undo tests."""
    batch = AutoCodeBatch(
        id=BatchId(value="batch_test123"),
        code_id=CodeId(value=1),
        pattern="test",
        segment_ids=(SegmentId(value=100), SegmentId(value=101)),
    )
    return CodingState(
        existing_codes=populated_state.existing_codes,
        existing_categories=populated_state.existing_categories,
        existing_segments=populated_state.existing_segments,
        existing_batches=(batch,),
        source_length=populated_state.source_length,
        source_exists=populated_state.source_exists,
    )
