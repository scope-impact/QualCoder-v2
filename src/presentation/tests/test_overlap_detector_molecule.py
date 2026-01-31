"""
Tests for OverlapDetector Molecule

Tests the pure logic for detecting and merging overlapping ranges.
This is a molecule-level test with no Qt dependencies.
"""


class TestRangeClass:
    """Tests for the Range dataclass."""

    def test_range_creation(self):
        """Range can be created with start and end."""
        from src.presentation.molecules.highlighting.overlap_detector import Range

        r = Range(10, 20)
        assert r.start == 10
        assert r.end == 20

    def test_range_length(self):
        """Range length is end - start."""
        from src.presentation.molecules.highlighting.overlap_detector import Range

        r = Range(10, 25)
        assert len(r) == 15

    def test_range_overlaps_true(self):
        """overlaps() returns True for overlapping ranges."""
        from src.presentation.molecules.highlighting.overlap_detector import Range

        r1 = Range(0, 10)
        r2 = Range(5, 15)
        assert r1.overlaps(r2) is True
        assert r2.overlaps(r1) is True

    def test_range_overlaps_false_adjacent(self):
        """overlaps() returns False for adjacent ranges."""
        from src.presentation.molecules.highlighting.overlap_detector import Range

        r1 = Range(0, 10)
        r2 = Range(10, 20)
        assert r1.overlaps(r2) is False

    def test_range_overlaps_false_disjoint(self):
        """overlaps() returns False for disjoint ranges."""
        from src.presentation.molecules.highlighting.overlap_detector import Range

        r1 = Range(0, 10)
        r2 = Range(20, 30)
        assert r1.overlaps(r2) is False

    def test_range_intersection(self):
        """intersection() returns the overlapping portion."""
        from src.presentation.molecules.highlighting.overlap_detector import Range

        r1 = Range(0, 10)
        r2 = Range(5, 15)
        intersection = r1.intersection(r2)

        assert intersection is not None
        assert intersection.start == 5
        assert intersection.end == 10

    def test_range_intersection_none_if_no_overlap(self):
        """intersection() returns None if no overlap."""
        from src.presentation.molecules.highlighting.overlap_detector import Range

        r1 = Range(0, 10)
        r2 = Range(20, 30)

        assert r1.intersection(r2) is None


class TestFindOverlaps:
    """Tests for find_overlaps method."""

    def test_find_overlaps_empty_list(self):
        """find_overlaps returns empty list for empty input."""
        from src.presentation.molecules.highlighting import OverlapDetector

        detector = OverlapDetector()
        result = detector.find_overlaps([])

        assert result == []

    def test_find_overlaps_single_range(self):
        """find_overlaps returns empty for single range (no overlap possible)."""
        from src.presentation.molecules.highlighting import OverlapDetector
        from src.presentation.molecules.highlighting.overlap_detector import Range

        detector = OverlapDetector()
        result = detector.find_overlaps([Range(0, 10)])

        assert result == []

    def test_find_overlaps_two_overlapping(self):
        """find_overlaps detects overlap between two ranges."""
        from src.presentation.molecules.highlighting import OverlapDetector
        from src.presentation.molecules.highlighting.overlap_detector import Range

        detector = OverlapDetector()
        ranges = [Range(0, 10), Range(5, 15)]
        result = detector.find_overlaps(ranges)

        assert len(result) == 1
        assert result[0].start == 5
        assert result[0].end == 10

    def test_find_overlaps_no_overlap(self):
        """find_overlaps returns empty for non-overlapping ranges."""
        from src.presentation.molecules.highlighting import OverlapDetector
        from src.presentation.molecules.highlighting.overlap_detector import Range

        detector = OverlapDetector()
        ranges = [Range(0, 10), Range(20, 30)]
        result = detector.find_overlaps(ranges)

        assert result == []

    def test_find_overlaps_multiple_overlaps(self):
        """find_overlaps handles multiple overlapping ranges."""
        from src.presentation.molecules.highlighting import OverlapDetector
        from src.presentation.molecules.highlighting.overlap_detector import Range

        detector = OverlapDetector()
        # Three ranges all overlapping in the middle
        ranges = [Range(0, 15), Range(10, 25), Range(20, 35)]
        result = detector.find_overlaps(ranges)

        # Overlaps: (10-15) from 1&2, (20-25) from 2&3
        assert len(result) == 2

    def test_find_overlaps_works_with_highlight_range(self, qapp, colors):
        """find_overlaps works with HighlightRange objects."""
        from src.presentation.molecules.highlighting import OverlapDetector
        from src.presentation.organisms.text_editor_panel import HighlightRange

        detector = OverlapDetector()
        highlights = [
            HighlightRange(start=0, end=10, color="#FF0000"),
            HighlightRange(start=5, end=15, color="#00FF00"),
        ]
        result = detector.find_overlaps(highlights)

        assert len(result) == 1
        assert result[0].start == 5
        assert result[0].end == 10


class TestMergeRanges:
    """Tests for merge_ranges method."""

    def test_merge_ranges_empty(self):
        """merge_ranges returns empty for empty input."""
        from src.presentation.molecules.highlighting import OverlapDetector

        detector = OverlapDetector()
        result = detector.merge_ranges([])

        assert result == []

    def test_merge_ranges_single(self):
        """merge_ranges returns single range unchanged."""
        from src.presentation.molecules.highlighting import OverlapDetector
        from src.presentation.molecules.highlighting.overlap_detector import Range

        detector = OverlapDetector()
        result = detector.merge_ranges([Range(0, 10)])

        assert len(result) == 1
        assert result[0].start == 0
        assert result[0].end == 10

    def test_merge_ranges_overlapping(self):
        """merge_ranges combines overlapping ranges."""
        from src.presentation.molecules.highlighting import OverlapDetector
        from src.presentation.molecules.highlighting.overlap_detector import Range

        detector = OverlapDetector()
        ranges = [Range(0, 10), Range(5, 15)]
        result = detector.merge_ranges(ranges)

        assert len(result) == 1
        assert result[0].start == 0
        assert result[0].end == 15

    def test_merge_ranges_adjacent(self):
        """merge_ranges combines adjacent ranges."""
        from src.presentation.molecules.highlighting import OverlapDetector
        from src.presentation.molecules.highlighting.overlap_detector import Range

        detector = OverlapDetector()
        ranges = [Range(0, 10), Range(10, 20)]
        result = detector.merge_ranges(ranges)

        assert len(result) == 1
        assert result[0].start == 0
        assert result[0].end == 20

    def test_merge_ranges_disjoint(self):
        """merge_ranges keeps disjoint ranges separate."""
        from src.presentation.molecules.highlighting import OverlapDetector
        from src.presentation.molecules.highlighting.overlap_detector import Range

        detector = OverlapDetector()
        ranges = [Range(0, 10), Range(20, 30)]
        result = detector.merge_ranges(ranges)

        assert len(result) == 2

    def test_merge_ranges_unsorted_input(self):
        """merge_ranges handles unsorted input."""
        from src.presentation.molecules.highlighting import OverlapDetector
        from src.presentation.molecules.highlighting.overlap_detector import Range

        detector = OverlapDetector()
        ranges = [Range(20, 30), Range(0, 10), Range(5, 15)]
        result = detector.merge_ranges(ranges)

        # Should merge 0-10 and 5-15, keep 20-30 separate
        assert len(result) == 2
        assert result[0].start == 0
        assert result[0].end == 15
        assert result[1].start == 20


class TestCountOverlapsAt:
    """Tests for count_overlaps_at method."""

    def test_count_overlaps_at_no_ranges(self):
        """count_overlaps_at returns 0 for empty list."""
        from src.presentation.molecules.highlighting import OverlapDetector

        detector = OverlapDetector()
        assert detector.count_overlaps_at([], 5) == 0

    def test_count_overlaps_at_position_in_range(self):
        """count_overlaps_at counts ranges containing position."""
        from src.presentation.molecules.highlighting import OverlapDetector
        from src.presentation.molecules.highlighting.overlap_detector import Range

        detector = OverlapDetector()
        ranges = [Range(0, 10), Range(5, 15), Range(20, 30)]

        # Position 7 is in first two ranges
        assert detector.count_overlaps_at(ranges, 7) == 2

    def test_count_overlaps_at_position_outside(self):
        """count_overlaps_at returns 0 for position outside all ranges."""
        from src.presentation.molecules.highlighting import OverlapDetector
        from src.presentation.molecules.highlighting.overlap_detector import Range

        detector = OverlapDetector()
        ranges = [Range(0, 10), Range(20, 30)]

        assert detector.count_overlaps_at(ranges, 15) == 0


class TestGetRangesAt:
    """Tests for get_ranges_at method."""

    def test_get_ranges_at_returns_indices(self):
        """get_ranges_at returns indices of containing ranges."""
        from src.presentation.molecules.highlighting import OverlapDetector
        from src.presentation.molecules.highlighting.overlap_detector import Range

        detector = OverlapDetector()
        ranges = [Range(0, 10), Range(5, 15), Range(20, 30)]

        indices = detector.get_ranges_at(ranges, 7)
        assert indices == [0, 1]

    def test_get_ranges_at_empty_for_outside(self):
        """get_ranges_at returns empty for position outside."""
        from src.presentation.molecules.highlighting import OverlapDetector
        from src.presentation.molecules.highlighting.overlap_detector import Range

        detector = OverlapDetector()
        ranges = [Range(0, 10), Range(20, 30)]

        assert detector.get_ranges_at(ranges, 15) == []
