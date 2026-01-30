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
from .color_picker_dialog import ColorPickerDialog
from .memo_dialog import (
    CodeMemoDialog,
    FileMemoDialog,
    MemoDialog,
    MemosPanel,
    SegmentMemoDialog,
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
]
