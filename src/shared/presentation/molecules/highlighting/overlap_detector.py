"""
Overlap Detector Molecule

Pure logic for detecting and merging overlapping text ranges.
No Qt dependencies - can be used anywhere ranges need overlap detection.

This is useful for:
- Detecting overlapping code highlights in qualitative analysis
- Merging adjacent/overlapping ranges for efficient processing
- Finding intersection regions between multiple annotations
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from src.shared.infra.telemetry import SpanContext, traced


class HasRange(Protocol):
    """Protocol for objects that have a start and end position."""

    @property
    def start(self) -> int: ...

    @property
    def end(self) -> int: ...


@dataclass(frozen=True)
class Range:
    """An immutable range with start and end positions."""

    start: int
    end: int

    def overlaps(self, other: "Range") -> bool:
        """Check if this range overlaps with another."""
        return self.start < other.end and other.start < self.end

    def intersection(self, other: "Range") -> "Range | None":
        """Get the intersection of two ranges, or None if no overlap."""
        if not self.overlaps(other):
            return None
        return Range(max(self.start, other.start), min(self.end, other.end))

    def __len__(self) -> int:
        return self.end - self.start


class OverlapDetector:
    """
    Detects and merges overlapping ranges.

    This is a stateless utility class - all methods are pure functions
    that take inputs and return outputs without side effects.

    Example:
        detector = OverlapDetector()

        # Find overlapping regions between highlights
        ranges = [Range(0, 10), Range(5, 15), Range(20, 30)]
        overlaps = detector.find_overlaps(ranges)
        # Returns: [Range(5, 10)]

        # Merge adjacent/overlapping ranges
        merged = detector.merge_ranges(ranges)
        # Returns: [Range(0, 15), Range(20, 30)]
    """

    def find_overlaps(self, ranges: Sequence[HasRange]) -> list[Range]:
        """
        Find all overlapping regions between ranges.

        Compares each pair of ranges and returns the intersection
        regions where they overlap.

        Args:
            ranges: Sequence of objects with start and end properties

        Returns:
            List of Range objects representing overlap regions
        """
        n = len(ranges)
        comparisons = n * (n - 1) // 2

        with SpanContext("find_overlaps", {
            "range_count": n,
            "comparisons": comparisons,
        }) as span:
            overlaps: list[Range] = []

            for i, r1 in enumerate(ranges):
                for j, r2 in enumerate(ranges):
                    if i >= j:
                        continue

                    # Check for overlap
                    if r1.start < r2.end and r2.start < r1.end:
                        overlap_start = max(r1.start, r2.start)
                        overlap_end = min(r1.end, r2.end)
                        if overlap_start < overlap_end:
                            overlaps.append(Range(overlap_start, overlap_end))

            span.set_attribute("overlaps_found", len(overlaps))
            return self.merge_ranges(overlaps)

    @traced("merge_ranges")
    def merge_ranges(self, ranges: Sequence[HasRange]) -> list[Range]:
        """
        Merge adjacent or overlapping ranges into consolidated ranges.

        Adjacent ranges (end of one == start of next) are merged.
        Overlapping ranges are combined into their union.

        Args:
            ranges: Sequence of objects with start and end properties

        Returns:
            List of merged Range objects, sorted by start position
        """
        if not ranges:
            return []

        # Convert to Range and deduplicate
        unique_ranges = sorted(
            {Range(r.start, r.end) for r in ranges},
            key=lambda r: r.start,
        )

        merged: list[Range] = [unique_ranges[0]]

        for current in unique_ranges[1:]:
            last = merged[-1]
            if current.start <= last.end:
                # Overlapping or adjacent - merge
                merged[-1] = Range(last.start, max(last.end, current.end))
            else:
                merged.append(current)

        return merged

    def count_overlaps_at(self, ranges: Sequence[HasRange], position: int) -> int:
        """
        Count how many ranges contain a specific position.

        Args:
            ranges: Sequence of objects with start and end properties
            position: The position to check

        Returns:
            Number of ranges that contain the position
        """
        return sum(1 for r in ranges if r.start <= position < r.end)

    def get_ranges_at(self, ranges: Sequence[HasRange], position: int) -> list[int]:
        """
        Get indices of ranges that contain a specific position.

        Args:
            ranges: Sequence of objects with start and end properties
            position: The position to check

        Returns:
            List of indices into the ranges sequence
        """
        return [i for i, r in enumerate(ranges) if r.start <= position < r.end]
