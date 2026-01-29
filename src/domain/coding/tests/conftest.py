"""
Pytest configuration for coding domain tests.
Provides fixtures for testing invariants and derivers.
"""

import pytest
from typing import List

from src.domain.shared.types import CodeId, CategoryId, SourceId, SegmentId
from src.domain.coding.entities import (
    Code,
    Category,
    TextSegment,
    Color,
    TextPosition,
)
from src.domain.coding.derivers import CodingState


@pytest.fixture
def sample_color() -> Color:
    """A valid sample color."""
    return Color(red=100, green=150, blue=200)


@pytest.fixture
def sample_code(sample_color: Color) -> Code:
    """A single sample code."""
    return Code(
        id=CodeId(value=1),
        name="Theme A",
        color=sample_color,
        memo="Test memo",
        category_id=None,
        owner="user1",
    )


@pytest.fixture
def sample_codes(sample_color: Color) -> List[Code]:
    """Multiple sample codes for testing."""
    return [
        Code(
            id=CodeId(value=1),
            name="Theme A",
            color=sample_color,
            memo="First theme",
            category_id=None,
            owner="user1",
        ),
        Code(
            id=CodeId(value=2),
            name="Theme B",
            color=Color(red=200, green=100, blue=50),
            memo="Second theme",
            category_id=CategoryId(value=1),
            owner="user1",
        ),
        Code(
            id=CodeId(value=3),
            name="Theme C",
            color=Color(red=50, green=200, blue=100),
            memo=None,
            category_id=CategoryId(value=1),
            owner="user2",
        ),
    ]


@pytest.fixture
def sample_category() -> Category:
    """A single sample category."""
    return Category(
        id=CategoryId(value=1),
        name="Category 1",
        parent_id=None,
        memo="Parent category",
        owner="user1",
    )


@pytest.fixture
def sample_categories() -> List[Category]:
    """Multiple sample categories for testing hierarchy."""
    return [
        Category(
            id=CategoryId(value=1),
            name="Root Category",
            parent_id=None,
            memo="Top level",
            owner="user1",
        ),
        Category(
            id=CategoryId(value=2),
            name="Child Category",
            parent_id=CategoryId(value=1),
            memo="Second level",
            owner="user1",
        ),
        Category(
            id=CategoryId(value=3),
            name="Grandchild Category",
            parent_id=CategoryId(value=2),
            memo="Third level",
            owner="user1",
        ),
    ]


@pytest.fixture
def sample_text_segment() -> TextSegment:
    """A sample text segment."""
    return TextSegment(
        id=SegmentId(value=1),
        code_id=CodeId(value=1),
        source_id=SourceId(value=1),
        position=TextPosition(start=0, end=50),
        selected_text="Sample selected text",
        memo="Test annotation",
        importance=0,
        owner="user1",
    )


@pytest.fixture
def sample_segments() -> List[TextSegment]:
    """Multiple sample segments for testing."""
    return [
        TextSegment(
            id=SegmentId(value=1),
            code_id=CodeId(value=1),
            source_id=SourceId(value=1),
            position=TextPosition(start=0, end=50),
            selected_text="First segment",
            memo=None,
            importance=0,
            owner="user1",
        ),
        TextSegment(
            id=SegmentId(value=2),
            code_id=CodeId(value=1),
            source_id=SourceId(value=1),
            position=TextPosition(start=100, end=150),
            selected_text="Second segment",
            memo="Important",
            importance=1,
            owner="user1",
        ),
        TextSegment(
            id=SegmentId(value=3),
            code_id=CodeId(value=2),
            source_id=SourceId(value=2),
            position=TextPosition(start=0, end=25),
            selected_text="Third segment",
            memo=None,
            importance=0,
            owner="user2",
        ),
    ]


@pytest.fixture
def empty_state() -> CodingState:
    """Empty coding state for creation tests."""
    return CodingState()


@pytest.fixture
def populated_state(
    sample_codes: List[Code],
    sample_categories: List[Category],
    sample_segments: List[TextSegment],
) -> CodingState:
    """Populated coding state for modification tests."""
    return CodingState(
        existing_codes=tuple(sample_codes),
        existing_categories=tuple(sample_categories),
        existing_segments=tuple(sample_segments),
        source_length=1000,
        source_exists=True,
    )
