"""
Data Transfer Objects for UI components.

These DTOs define the shape of data that flows into Pages/Screens.
They decouple the UI from data sources (real repos, mocks, etc.).
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FileDTO:
    """A file available for coding."""
    id: str
    name: str
    file_type: str = "text"  # text, image, av, pdf
    meta: str = ""
    selected: bool = False


@dataclass
class CodeDTO:
    """A single code."""
    id: str
    name: str
    color: str
    count: int = 0
    memo: Optional[str] = None


@dataclass
class CodeCategoryDTO:
    """A category containing codes."""
    id: str
    name: str
    codes: List[CodeDTO] = field(default_factory=list)
    expanded: bool = True


@dataclass
class DocumentDTO:
    """A document being coded."""
    id: str
    title: str
    badge: Optional[str] = None
    content: str = ""


@dataclass
class DocumentStatsDTO:
    """Statistics about a document."""
    overlapping_count: int = 0
    codes_applied: int = 0
    word_count: int = 0


@dataclass
class SelectedCodeDTO:
    """Details of the currently selected code."""
    id: str
    name: str
    color: str
    memo: str = ""
    example_text: Optional[str] = None


@dataclass
class OverlappingSegmentDTO:
    """A text segment with overlapping codes."""
    segment_label: str
    colors: List[str] = field(default_factory=list)


@dataclass
class FileMemoDTO:
    """Memo and progress for current file."""
    memo: str = ""
    progress: int = 0  # 0-100


@dataclass
class NavigationDTO:
    """File navigation state."""
    current: int = 1
    total: int = 1


@dataclass
class TextCodingDataDTO:
    """
    Complete data bundle for the TextCodingPage.

    This DTO contains all data needed to render the text coding interface.
    It can be populated from real repositories or mock data providers.
    """
    files: List[FileDTO] = field(default_factory=list)
    categories: List[CodeCategoryDTO] = field(default_factory=list)
    document: Optional[DocumentDTO] = None
    document_stats: Optional[DocumentStatsDTO] = None
    selected_code: Optional[SelectedCodeDTO] = None
    overlapping_segments: List[OverlappingSegmentDTO] = field(default_factory=list)
    file_memo: Optional[FileMemoDTO] = None
    navigation: Optional[NavigationDTO] = None
    coders: List[str] = field(default_factory=list)
    selected_coder: Optional[str] = None
