"""Tests for Coding context SQLAlchemy repositories."""

from __future__ import annotations

from src.domain.coding.entities import (
    Category,
    Code,
    Color,
    TextPosition,
    TextSegment,
)
from src.domain.shared.types import CategoryId, CodeId, SegmentId, SourceId


class TestSQLiteCodeRepository:
    """Tests for SQLiteCodeRepository."""

    def test_save_and_get_by_id(self, code_repo):
        """Test saving and retrieving a code."""
        code = Code(
            id=CodeId(value=1),
            name="Test Code",
            color=Color(255, 0, 0),
            memo="Test memo",
        )
        code_repo.save(code)

        retrieved = code_repo.get_by_id(CodeId(value=1))
        assert retrieved is not None
        assert retrieved.name == "Test Code"
        assert retrieved.color.to_hex() == "#ff0000"
        assert retrieved.memo == "Test memo"

    def test_get_by_id_not_found(self, code_repo):
        """Test getting a non-existent code returns None."""
        result = code_repo.get_by_id(CodeId(value=999))
        assert result is None

    def test_get_all(self, code_repo):
        """Test getting all codes."""
        code1 = Code(id=CodeId(value=1), name="Alpha", color=Color(255, 0, 0))
        code2 = Code(id=CodeId(value=2), name="Beta", color=Color(0, 255, 0))
        code_repo.save(code1)
        code_repo.save(code2)

        codes = code_repo.get_all()
        assert len(codes) == 2
        # Should be ordered by name
        assert codes[0].name == "Alpha"
        assert codes[1].name == "Beta"

    def test_get_by_name_case_insensitive(self, code_repo):
        """Test case-insensitive name lookup."""
        code = Code(id=CodeId(value=1), name="TestCode", color=Color(255, 0, 0))
        code_repo.save(code)

        result = code_repo.get_by_name("testcode")
        assert result is not None
        assert result.name == "TestCode"

    def test_update_existing_code(self, code_repo):
        """Test updating an existing code."""
        code = Code(id=CodeId(value=1), name="Original", color=Color(255, 0, 0))
        code_repo.save(code)

        updated = Code(id=CodeId(value=1), name="Updated", color=Color(0, 255, 0))
        code_repo.save(updated)

        retrieved = code_repo.get_by_id(CodeId(value=1))
        assert retrieved.name == "Updated"
        assert retrieved.color.to_hex() == "#00ff00"

    def test_delete(self, code_repo):
        """Test deleting a code."""
        code = Code(id=CodeId(value=1), name="ToDelete", color=Color(255, 0, 0))
        code_repo.save(code)
        assert code_repo.exists(CodeId(value=1))

        code_repo.delete(CodeId(value=1))
        assert not code_repo.exists(CodeId(value=1))

    def test_name_exists(self, code_repo):
        """Test checking if name exists."""
        code = Code(id=CodeId(value=1), name="Existing", color=Color(255, 0, 0))
        code_repo.save(code)

        assert code_repo.name_exists("Existing")
        assert code_repo.name_exists("existing")  # case insensitive
        assert not code_repo.name_exists("NonExistent")

    def test_name_exists_with_exclude(self, code_repo):
        """Test name_exists excludes specified ID."""
        code = Code(id=CodeId(value=1), name="MyCode", color=Color(255, 0, 0))
        code_repo.save(code)

        # Same name exists, but excluding its own ID should return False
        assert not code_repo.name_exists("MyCode", exclude_id=CodeId(value=1))
        assert code_repo.name_exists("MyCode", exclude_id=CodeId(value=2))

    def test_get_by_category(self, code_repo, category_repo):
        """Test getting codes by category."""
        cat = Category(id=CategoryId(value=1), name="Cat1")
        category_repo.save(cat)

        code1 = Code(
            id=CodeId(value=1),
            name="Code1",
            color=Color(255, 0, 0),
            category_id=CategoryId(value=1),
        )
        code2 = Code(
            id=CodeId(value=2),
            name="Code2",
            color=Color(0, 255, 0),
            category_id=CategoryId(value=1),
        )
        code3 = Code(id=CodeId(value=3), name="Code3", color=Color(0, 0, 255))
        code_repo.save(code1)
        code_repo.save(code2)
        code_repo.save(code3)

        codes = code_repo.get_by_category(CategoryId(value=1))
        assert len(codes) == 2
        names = {c.name for c in codes}
        assert names == {"Code1", "Code2"}


class TestSQLiteCategoryRepository:
    """Tests for SQLiteCategoryRepository."""

    def test_save_and_get_by_id(self, category_repo):
        """Test saving and retrieving a category."""
        cat = Category(id=CategoryId(value=1), name="Test Category", memo="A memo")
        category_repo.save(cat)

        retrieved = category_repo.get_by_id(CategoryId(value=1))
        assert retrieved is not None
        assert retrieved.name == "Test Category"
        assert retrieved.memo == "A memo"

    def test_get_all(self, category_repo):
        """Test getting all categories."""
        cat1 = Category(id=CategoryId(value=1), name="Zebra")
        cat2 = Category(id=CategoryId(value=2), name="Alpha")
        category_repo.save(cat1)
        category_repo.save(cat2)

        cats = category_repo.get_all()
        assert len(cats) == 2
        # Should be ordered by name
        assert cats[0].name == "Alpha"
        assert cats[1].name == "Zebra"

    def test_get_by_parent_root(self, category_repo):
        """Test getting root categories (no parent)."""
        root1 = Category(id=CategoryId(value=1), name="Root1")
        root2 = Category(id=CategoryId(value=2), name="Root2")
        child = Category(
            id=CategoryId(value=3), name="Child", parent_id=CategoryId(value=1)
        )
        category_repo.save(root1)
        category_repo.save(root2)
        category_repo.save(child)

        roots = category_repo.get_by_parent(None)
        assert len(roots) == 2
        names = {c.name for c in roots}
        assert names == {"Root1", "Root2"}

    def test_get_by_parent_children(self, category_repo):
        """Test getting children of a parent."""
        parent = Category(id=CategoryId(value=1), name="Parent")
        child1 = Category(
            id=CategoryId(value=2), name="Child1", parent_id=CategoryId(value=1)
        )
        child2 = Category(
            id=CategoryId(value=3), name="Child2", parent_id=CategoryId(value=1)
        )
        category_repo.save(parent)
        category_repo.save(child1)
        category_repo.save(child2)

        children = category_repo.get_by_parent(CategoryId(value=1))
        assert len(children) == 2

    def test_delete(self, category_repo):
        """Test deleting a category."""
        cat = Category(id=CategoryId(value=1), name="ToDelete")
        category_repo.save(cat)

        category_repo.delete(CategoryId(value=1))
        assert category_repo.get_by_id(CategoryId(value=1)) is None


class TestSQLiteSegmentRepository:
    """Tests for SQLiteSegmentRepository."""

    def test_save_and_get_by_id(self, segment_repo, code_repo):
        """Test saving and retrieving a segment."""
        code = Code(id=CodeId(value=1), name="Code1", color=Color(255, 0, 0))
        code_repo.save(code)

        segment = TextSegment(
            id=SegmentId(value=1),
            source_id=SourceId(value=100),
            code_id=CodeId(value=1),
            position=TextPosition(start=10, end=20),
            selected_text="hello world",
            memo="segment memo",
        )
        segment_repo.save(segment)

        retrieved = segment_repo.get_by_id(SegmentId(value=1))
        assert retrieved is not None
        assert retrieved.selected_text == "hello world"
        assert retrieved.position.start == 10
        assert retrieved.position.end == 20

    def test_get_by_source(self, segment_repo, code_repo):
        """Test getting segments by source."""
        code = Code(id=CodeId(value=1), name="Code1", color=Color(255, 0, 0))
        code_repo.save(code)

        seg1 = TextSegment(
            id=SegmentId(value=1),
            source_id=SourceId(value=100),
            code_id=CodeId(value=1),
            position=TextPosition(start=0, end=10),
            selected_text="first",
        )
        seg2 = TextSegment(
            id=SegmentId(value=2),
            source_id=SourceId(value=100),
            code_id=CodeId(value=1),
            position=TextPosition(start=20, end=30),
            selected_text="second",
        )
        seg3 = TextSegment(
            id=SegmentId(value=3),
            source_id=SourceId(value=200),
            code_id=CodeId(value=1),
            position=TextPosition(start=0, end=5),
            selected_text="other",
        )
        segment_repo.save(seg1)
        segment_repo.save(seg2)
        segment_repo.save(seg3)

        segments = segment_repo.get_by_source(SourceId(value=100))
        assert len(segments) == 2
        # Should be ordered by position
        assert segments[0].selected_text == "first"
        assert segments[1].selected_text == "second"

    def test_get_by_code(self, segment_repo, code_repo):
        """Test getting segments by code."""
        code1 = Code(id=CodeId(value=1), name="Code1", color=Color(255, 0, 0))
        code2 = Code(id=CodeId(value=2), name="Code2", color=Color(0, 255, 0))
        code_repo.save(code1)
        code_repo.save(code2)

        seg1 = TextSegment(
            id=SegmentId(value=1),
            source_id=SourceId(value=100),
            code_id=CodeId(value=1),
            position=TextPosition(start=0, end=10),
            selected_text="code1 seg",
        )
        seg2 = TextSegment(
            id=SegmentId(value=2),
            source_id=SourceId(value=100),
            code_id=CodeId(value=2),
            position=TextPosition(start=20, end=30),
            selected_text="code2 seg",
        )
        segment_repo.save(seg1)
        segment_repo.save(seg2)

        segments = segment_repo.get_by_code(CodeId(value=1))
        assert len(segments) == 1
        assert segments[0].selected_text == "code1 seg"

    def test_count_by_code(self, segment_repo, code_repo):
        """Test counting segments by code."""
        code = Code(id=CodeId(value=1), name="Code1", color=Color(255, 0, 0))
        code_repo.save(code)

        for i in range(5):
            seg = TextSegment(
                id=SegmentId(value=i),
                source_id=SourceId(value=100),
                code_id=CodeId(value=1),
                position=TextPosition(start=i * 10, end=i * 10 + 5),
                selected_text=f"seg{i}",
            )
            segment_repo.save(seg)

        count = segment_repo.count_by_code(CodeId(value=1))
        assert count == 5

    def test_delete_by_code(self, segment_repo, code_repo):
        """Test deleting all segments for a code."""
        code = Code(id=CodeId(value=1), name="Code1", color=Color(255, 0, 0))
        code_repo.save(code)

        for i in range(3):
            seg = TextSegment(
                id=SegmentId(value=i),
                source_id=SourceId(value=100),
                code_id=CodeId(value=1),
                position=TextPosition(start=i * 10, end=i * 10 + 5),
                selected_text=f"seg{i}",
            )
            segment_repo.save(seg)

        deleted = segment_repo.delete_by_code(CodeId(value=1))
        assert deleted == 3
        assert segment_repo.count_by_code(CodeId(value=1)) == 0

    def test_reassign_code(self, segment_repo, code_repo):
        """Test reassigning segments from one code to another."""
        code1 = Code(id=CodeId(value=1), name="Code1", color=Color(255, 0, 0))
        code2 = Code(id=CodeId(value=2), name="Code2", color=Color(0, 255, 0))
        code_repo.save(code1)
        code_repo.save(code2)

        seg = TextSegment(
            id=SegmentId(value=1),
            source_id=SourceId(value=100),
            code_id=CodeId(value=1),
            position=TextPosition(start=0, end=10),
            selected_text="test",
        )
        segment_repo.save(seg)

        reassigned = segment_repo.reassign_code(CodeId(value=1), CodeId(value=2))
        assert reassigned == 1

        # Segment should now have code2
        retrieved = segment_repo.get_by_id(SegmentId(value=1))
        assert retrieved.code_id == CodeId(value=2)

    def test_delete_by_source_removes_all_segments(self, segment_repo, code_repo):
        """Test delete_by_source removes all segments for a source."""
        code = Code(id=CodeId(value=1), name="Code1", color=Color(255, 0, 0))
        code_repo.save(code)

        # Create segments for source 100
        for i in range(3):
            seg = TextSegment(
                id=SegmentId(value=i),
                source_id=SourceId(value=100),
                code_id=CodeId(value=1),
                position=TextPosition(start=i * 10, end=i * 10 + 5),
                selected_text=f"seg{i}",
            )
            segment_repo.save(seg)

        # Delete all segments for source 100
        deleted = segment_repo.delete_by_source(SourceId(value=100))
        assert deleted == 3

        # Verify no segments remain for source 100
        segments = segment_repo.get_by_source(SourceId(value=100))
        assert len(segments) == 0

    def test_delete_by_source_returns_correct_count(self, segment_repo, code_repo):
        """Test delete_by_source returns correct count of deleted rows."""
        code = Code(id=CodeId(value=1), name="Code1", color=Color(255, 0, 0))
        code_repo.save(code)

        # Create 5 segments
        for i in range(5):
            seg = TextSegment(
                id=SegmentId(value=i),
                source_id=SourceId(value=200),
                code_id=CodeId(value=1),
                position=TextPosition(start=i * 10, end=i * 10 + 5),
                selected_text=f"seg{i}",
            )
            segment_repo.save(seg)

        # Delete should return count of 5
        deleted = segment_repo.delete_by_source(SourceId(value=200))
        assert deleted == 5

    def test_delete_by_source_doesnt_affect_other_sources(
        self, segment_repo, code_repo
    ):
        """Test delete_by_source doesn't affect other sources' segments."""
        code = Code(id=CodeId(value=1), name="Code1", color=Color(255, 0, 0))
        code_repo.save(code)

        # Create segments for source 100
        seg1 = TextSegment(
            id=SegmentId(value=1),
            source_id=SourceId(value=100),
            code_id=CodeId(value=1),
            position=TextPosition(start=0, end=10),
            selected_text="source100",
        )
        segment_repo.save(seg1)

        # Create segments for source 200
        seg2 = TextSegment(
            id=SegmentId(value=2),
            source_id=SourceId(value=200),
            code_id=CodeId(value=1),
            position=TextPosition(start=0, end=10),
            selected_text="source200",
        )
        segment_repo.save(seg2)

        # Delete segments for source 100
        deleted = segment_repo.delete_by_source(SourceId(value=100))
        assert deleted == 1

        # Source 200 segments should still exist
        segments = segment_repo.get_by_source(SourceId(value=200))
        assert len(segments) == 1
        assert segments[0].selected_text == "source200"

    def test_delete_by_source_with_no_segments(self, segment_repo):
        """Test delete_by_source returns 0 when source has no segments."""
        deleted = segment_repo.delete_by_source(SourceId(value=999))
        assert deleted == 0
