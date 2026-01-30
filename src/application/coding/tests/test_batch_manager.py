"""
Tests for BatchManager application service.

TDD tests written BEFORE implementation.
Extracted from presentation/dialogs/auto_code_dialog.py AutoCodeManager.
"""

import pytest

from src.application.coding.services.batch_manager import BatchManager
from src.domain.coding.entities import BatchId
from src.domain.shared.types import CodeId, SegmentId


class TestBatchManagerCreation:
    """Tests for creating batches."""

    def test_creates_batch_with_segments(self):
        """Should create and track a batch."""
        manager = BatchManager()

        batch_id = manager.create_batch(
            code_id=CodeId(value=1),
            pattern="test pattern",
            segment_ids=[SegmentId(value=1), SegmentId(value=2)],
        )

        assert batch_id is not None
        batch = manager.get_batch(batch_id)
        assert batch is not None
        assert batch.code_id == CodeId(value=1)
        assert batch.pattern == "test pattern"
        assert len(batch.segment_ids) == 2

    def test_creates_empty_batch(self):
        """Should allow creating batch with no segments."""
        manager = BatchManager()

        batch_id = manager.create_batch(
            code_id=CodeId(value=1),
            pattern="empty batch",
            segment_ids=[],
        )

        assert batch_id is not None
        batch = manager.get_batch(batch_id)
        assert batch is not None
        assert len(batch.segment_ids) == 0

    def test_batch_ids_are_unique(self):
        """Each batch should have unique ID."""
        manager = BatchManager()

        id1 = manager.create_batch(
            code_id=CodeId(value=1),
            pattern="first",
            segment_ids=[],
        )
        id2 = manager.create_batch(
            code_id=CodeId(value=1),
            pattern="second",
            segment_ids=[],
        )

        assert id1 != id2


class TestBatchManagerRetrieval:
    """Tests for retrieving batches."""

    def test_get_batch_returns_batch(self):
        """Should return existing batch."""
        manager = BatchManager()
        batch_id = manager.create_batch(
            code_id=CodeId(value=1),
            pattern="test",
            segment_ids=[SegmentId(value=1)],
        )

        batch = manager.get_batch(batch_id)

        assert batch is not None
        assert batch.id == batch_id

    def test_get_batch_returns_none_for_nonexistent(self):
        """Should return None for non-existent batch."""
        manager = BatchManager()

        batch = manager.get_batch(BatchId(value="nonexistent"))

        assert batch is None

    def test_get_last_batch_returns_most_recent(self):
        """Should return the most recently created batch."""
        manager = BatchManager()
        manager.create_batch(
            code_id=CodeId(value=1),
            pattern="first",
            segment_ids=[],
        )
        last_id = manager.create_batch(
            code_id=CodeId(value=2),
            pattern="second",
            segment_ids=[],
        )

        last_batch = manager.get_last_batch()

        assert last_batch is not None
        assert last_batch.id == last_id
        assert last_batch.pattern == "second"

    def test_get_last_batch_returns_none_when_empty(self):
        """Should return None when no batches exist."""
        manager = BatchManager()

        last_batch = manager.get_last_batch()

        assert last_batch is None


class TestBatchManagerUndo:
    """Tests for undo functionality."""

    def test_undo_last_batch_removes_from_history(self):
        """Should remove last batch from history."""
        manager = BatchManager()
        manager.create_batch(
            code_id=CodeId(value=1),
            pattern="first",
            segment_ids=[SegmentId(value=1)],
        )
        manager.create_batch(
            code_id=CodeId(value=2),
            pattern="second",
            segment_ids=[SegmentId(value=2)],
        )

        undone = manager.undo_last_batch()

        assert undone is not None
        assert undone.pattern == "second"

        # Last batch should now be "first"
        last = manager.get_last_batch()
        assert last is not None
        assert last.pattern == "first"

    def test_undo_last_batch_returns_none_when_empty(self):
        """Should return None when no batches to undo."""
        manager = BatchManager()

        undone = manager.undo_last_batch()

        assert undone is None

    def test_undo_removes_batch_from_storage(self):
        """Undone batch should no longer be retrievable."""
        manager = BatchManager()
        batch_id = manager.create_batch(
            code_id=CodeId(value=1),
            pattern="test",
            segment_ids=[SegmentId(value=1)],
        )

        manager.undo_last_batch()

        batch = manager.get_batch(batch_id)
        assert batch is None


class TestBatchManagerHistory:
    """Tests for history management."""

    def test_clear_history_removes_all_batches(self):
        """Should remove all batches from history."""
        manager = BatchManager()
        manager.create_batch(
            code_id=CodeId(value=1),
            pattern="first",
            segment_ids=[],
        )
        manager.create_batch(
            code_id=CodeId(value=2),
            pattern="second",
            segment_ids=[],
        )

        manager.clear_history()

        assert manager.get_last_batch() is None
        assert manager.batch_count == 0

    def test_batch_count_tracks_batches(self):
        """Should track number of batches."""
        manager = BatchManager()

        assert manager.batch_count == 0

        manager.create_batch(
            code_id=CodeId(value=1),
            pattern="first",
            segment_ids=[],
        )
        assert manager.batch_count == 1

        manager.create_batch(
            code_id=CodeId(value=2),
            pattern="second",
            segment_ids=[],
        )
        assert manager.batch_count == 2

        manager.undo_last_batch()
        assert manager.batch_count == 1

    def test_get_all_batches_returns_copy(self):
        """Should return copy of batch history."""
        manager = BatchManager()
        manager.create_batch(
            code_id=CodeId(value=1),
            pattern="test",
            segment_ids=[],
        )

        batches = manager.get_all_batches()

        assert len(batches) == 1
        # Should be a copy, not the internal storage
        batches.clear()
        assert manager.batch_count == 1


class TestBatchManagerMaxHistory:
    """Tests for history limit."""

    def test_respects_max_history_limit(self):
        """Should limit number of stored batches."""
        manager = BatchManager(max_history=3)

        for i in range(5):
            manager.create_batch(
                code_id=CodeId(value=i),
                pattern=f"batch_{i}",
                segment_ids=[],
            )

        assert manager.batch_count == 3
        # Should have batches 2, 3, 4 (oldest dropped)
        last = manager.get_last_batch()
        assert last is not None
        assert last.pattern == "batch_4"


class TestBatchManagerImmutability:
    """Tests verifying returned batches are immutable."""

    def test_returned_batch_is_immutable(self):
        """Returned batches should be immutable."""
        manager = BatchManager()
        batch_id = manager.create_batch(
            code_id=CodeId(value=1),
            pattern="test",
            segment_ids=[SegmentId(value=1)],
        )

        batch = manager.get_batch(batch_id)

        assert batch is not None
        with pytest.raises(AttributeError):
            batch.pattern = "modified"
