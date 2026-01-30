"""
Batch Manager Application Service

Orchestration service for managing auto-code batch operations.
Extracted from presentation layer to maintain proper DDD boundaries.

This service manages:
- Batch creation and tracking
- Undo history for batch operations
- History limits

Usage:
    manager = BatchManager(max_history=10)

    # Create a batch
    batch_id = manager.create_batch(
        code_id=CodeId(value=1),
        pattern="search pattern",
        segment_ids=[SegmentId(value=1), SegmentId(value=2)],
    )

    # Undo last batch
    undone = manager.undo_last_batch()
    if undone:
        print(f"Undone batch with {len(undone.segment_ids)} segments")
"""

from __future__ import annotations

from src.domain.coding.entities import AutoCodeBatch, BatchId
from src.domain.shared.types import CodeId, SegmentId


class BatchManager:
    """
    Application service for managing auto-code batch operations.

    This service maintains an in-memory history of batch operations
    to support undo functionality. It does not persist batches to
    storage - that would be handled by a repository if needed.

    Example:
        manager = BatchManager()
        batch_id = manager.create_batch(
            code_id=CodeId(value=1),
            pattern="test",
            segment_ids=[SegmentId(value=1)],
        )
        manager.undo_last_batch()  # Removes and returns the batch
    """

    DEFAULT_MAX_HISTORY = 50

    def __init__(self, max_history: int | None = None) -> None:
        """
        Initialize the batch manager.

        Args:
            max_history: Maximum number of batches to keep in history.
                        Defaults to 50. Set to None for unlimited.
        """
        self._max_history = max_history or self.DEFAULT_MAX_HISTORY
        self._batches: dict[str, AutoCodeBatch] = {}
        self._history: list[str] = []  # Batch IDs in order (oldest first)

    def create_batch(
        self,
        code_id: CodeId,
        pattern: str,
        segment_ids: list[SegmentId],
    ) -> BatchId:
        """
        Create a new batch record.

        Args:
            code_id: The code that was applied
            pattern: The search pattern used
            segment_ids: IDs of segments created

        Returns:
            The batch ID for the new batch
        """
        batch_id = BatchId.new()
        batch = AutoCodeBatch(
            id=batch_id,
            code_id=code_id,
            pattern=pattern,
            segment_ids=tuple(segment_ids),
        )

        self._batches[batch_id.value] = batch
        self._history.append(batch_id.value)

        # Enforce max history limit
        self._enforce_history_limit()

        return batch_id

    def get_batch(self, batch_id: BatchId) -> AutoCodeBatch | None:
        """
        Get a batch by ID.

        Args:
            batch_id: The batch ID to look up

        Returns:
            The batch if found, None otherwise
        """
        return self._batches.get(batch_id.value)

    def get_last_batch(self) -> AutoCodeBatch | None:
        """
        Get the most recent batch.

        Returns:
            The most recent batch, or None if no batches exist
        """
        if not self._history:
            return None
        return self._batches.get(self._history[-1])

    def undo_last_batch(self) -> AutoCodeBatch | None:
        """
        Remove and return the last batch.

        This removes the batch from the manager's tracking.
        The caller is responsible for actually removing the
        segments from storage.

        Returns:
            The batch that was undone, or None if no batches
        """
        if not self._history:
            return None

        batch_id = self._history.pop()
        batch = self._batches.pop(batch_id, None)

        return batch

    def clear_history(self) -> None:
        """Clear all batch history."""
        self._batches.clear()
        self._history.clear()

    def get_all_batches(self) -> list[AutoCodeBatch]:
        """
        Get all batches in history order (oldest first).

        Returns:
            Copy of the batch list
        """
        return [
            self._batches[batch_id]
            for batch_id in self._history
            if batch_id in self._batches
        ]

    @property
    def batch_count(self) -> int:
        """Number of batches in history."""
        return len(self._history)

    def _enforce_history_limit(self) -> None:
        """Remove oldest batches if over the limit."""
        while len(self._history) > self._max_history:
            oldest_id = self._history.pop(0)
            self._batches.pop(oldest_id, None)
