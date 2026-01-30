"""
Data Transfer Objects for UI components.

These DTOs define the shape of data that flows into Pages/Screens.
They decouple the UI from data sources (real repos, mocks, etc.).
"""

from dataclasses import dataclass, field


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
    memo: str | None = None


@dataclass
class CodeCategoryDTO:
    """A category containing codes."""

    id: str
    name: str
    codes: list[CodeDTO] = field(default_factory=list)
    expanded: bool = True


@dataclass
class DocumentDTO:
    """A document being coded."""

    id: str
    title: str
    badge: str | None = None
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
    example_text: str | None = None


@dataclass
class OverlappingSegmentDTO:
    """A text segment with overlapping codes."""

    segment_label: str
    colors: list[str] = field(default_factory=list)


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

    files: list[FileDTO] = field(default_factory=list)
    categories: list[CodeCategoryDTO] = field(default_factory=list)
    document: DocumentDTO | None = None
    document_stats: DocumentStatsDTO | None = None
    selected_code: SelectedCodeDTO | None = None
    overlapping_segments: list[OverlappingSegmentDTO] = field(default_factory=list)
    file_memo: FileMemoDTO | None = None
    navigation: NavigationDTO | None = None
    coders: list[str] = field(default_factory=list)
    selected_coder: str | None = None
