"""
Presentation layer dialogs.

This module contains dialog components for user interactions like
memo editing, code creation, and confirmations.

Note: Domain logic has been extracted to proper layers:
- TextMatcher: src/domain/coding/services/text_matcher.py
- SpeakerDetector: src/domain/sources/services/speaker_detector.py
- AutoCodeBatch: src/domain/coding/entities.py
- BatchManager: src/application/coding/services/batch_manager.py
"""

# Re-export MemoListItem from molecules for backward compatibility
from src.presentation.molecules.memo import MemoListItem

from .auto_code_dialog import (
    AutoCodeDialog,
    AutoCodePreview,
)
from .code_suggestion_dialog import (
    CodeSuggestionDialog,
    SuggestionCard,
)
from .color_picker_dialog import ColorPickerDialog
from .delete_source_dialog import (
    DeleteSourceDialog,
    DeleteSourceInfo,
)
from .duplicate_codes_dialog import (
    DuplicateCodesDialog,
    DuplicatePairCard,
)
from .folder_dialog import (
    FolderDialog,
    FolderFormData,
    RenameFolderDialog,
)
from .memo_dialog import (
    CodeMemoDialog,
    FileMemoDialog,
    MemoDialog,
    MemosPanel,
    SegmentMemoDialog,
)
from .project_dialog import (
    CreateProjectDialog,
    OpenProjectDialog,
)
from .source_metadata_dialog import (
    SourceMetadata,
    SourceMetadataDialog,
)

__all__ = [
    "MemoDialog",
    "FileMemoDialog",
    "CodeMemoDialog",
    "SegmentMemoDialog",
    "MemoListItem",
    "MemosPanel",
    "ColorPickerDialog",
    "AutoCodeDialog",
    "AutoCodePreview",
    "OpenProjectDialog",
    "CreateProjectDialog",
    "DeleteSourceDialog",
    "DeleteSourceInfo",
    "FolderDialog",
    "FolderFormData",
    "RenameFolderDialog",
    "SourceMetadata",
    "SourceMetadataDialog",
    "CodeSuggestionDialog",
    "SuggestionCard",
    "DuplicateCodesDialog",
    "DuplicatePairCard",
]
