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
class SourceDTO:
    """A source file in the project."""

    id: str
    name: str
    source_type: str  # text, audio, video, image, pdf
    status: str = "imported"  # imported, transcribing, ready, in_progress, coded
    file_size: int = 0
    code_count: int = 0
    memo: str | None = None
    origin: str | None = None
    cases: list[str] = field(default_factory=list)
    modified_at: str | None = None


@dataclass
class ProjectSummaryDTO:
    """Summary statistics for a project."""

    total_sources: int = 0
    text_count: int = 0
    audio_count: int = 0
    video_count: int = 0
    image_count: int = 0
    pdf_count: int = 0
    total_codes: int = 0
    total_segments: int = 0


@dataclass
class FolderDTO:
    """A folder for organizing sources."""

    id: str
    name: str
    parent_id: str | None = None
    source_count: int = 0


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


@dataclass
class CaseAttributeDTO:
    """A case attribute (demographic or categorical data)."""

    name: str
    attr_type: str  # text, number, boolean, date
    value: str | int | float | bool | None = None


@dataclass
class CaseDTO:
    """A case (participant, site, or other grouping)."""

    id: str
    name: str
    description: str | None = None
    memo: str | None = None
    attributes: list[CaseAttributeDTO] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)
    source_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class CaseSummaryDTO:
    """Summary statistics for cases."""

    total_cases: int = 0
    cases_with_sources: int = 0
    total_attributes: int = 0
    unique_attribute_names: list[str] = field(default_factory=list)


# =============================================================================
# Settings DTOs
# =============================================================================


@dataclass(frozen=True)
class SettingsDTO:
    """All user settings for display."""

    theme: str = "light"
    font_family: str = "Inter"
    font_size: int = 14
    language_code: str = "en"
    language_name: str = "English"
    backup_enabled: bool = False
    backup_interval: int = 30
    backup_max: int = 5
    backup_path: str | None = None
    timestamp_format: str = "HH:MM:SS"
    speaker_format: str = "Speaker {n}"
    # Cloud sync settings (SQLite is always primary)
    cloud_sync_enabled: bool = False
    convex_url: str | None = None


@dataclass(frozen=True)
class LanguageOptionDTO:
    """Available language option."""

    code: str
    name: str


@dataclass(frozen=True)
class FontFamilyOptionDTO:
    """Available font family option."""

    family: str
    display_name: str


# =============================================================================
# Factory Functions
# =============================================================================


def create_empty_text_coding_data() -> TextCodingDataDTO:
    """Create empty placeholder data for the text coding screen.

    Used when no document is selected. Shows a placeholder message
    guiding the user to select a source file.
    """
    return TextCodingDataDTO(
        files=[],
        categories=[],
        document=DocumentDTO(
            id="",
            title="No document selected",
            badge=None,
            content="Select a source file from the Files and Cases screen to begin coding.",
        ),
        document_stats=DocumentStatsDTO(
            overlapping_count=0,
            codes_applied=0,
            word_count=0,
        ),
        selected_code=None,
        overlapping_segments=[],
        file_memo=None,
        navigation=NavigationDTO(current=0, total=0),
        coders=[],
        selected_coder=None,
    )
