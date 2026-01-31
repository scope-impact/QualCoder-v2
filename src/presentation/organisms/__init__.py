"""
UI Organisms

Reusable, self-contained complex components that can be composed into pages.
Each organism is a meaningful section of UI that can be developed and tested independently.

Following Atomic Design methodology:
- Atoms: Basic UI elements (buttons, icons, inputs)
- Molecules: Simple combinations of atoms
- Organisms: Complex, self-contained sections of UI
- Templates: Page-level layouts
- Pages: Specific instances with data

Organisms in this module:
- CodingToolbar: Toolbar with media selector, coder dropdown, actions, search
- FilesPanel: File list with header and actions
- CodesPanel: Code tree with navigation
- TextEditorPanel: Text display with selection and highlighting
- DetailsPanel: Contextual info cards (selected code, overlaps, memo, AI)
- SourceStatsRow: Clickable stat cards for filtering sources by type
- SourceTable: Data table for source files with selection and actions
- FileManagerToolbar: Actions and search for File Manager
- EmptyState: Empty state display for new projects
"""

from .codes_panel import CodesPanel
from .coding_toolbar import CodingToolbar
from .details_panel import DetailsPanel
from .file_manager_toolbar import EmptyState, FileManagerToolbar
from .files_panel import FilesPanel
from .folder_tree import FolderNode, FolderTree
from .image_viewer import ImageMetadata, ImageViewer
from .media_player import MediaPlayer
from .source_stats_row import SourceStatCard, SourceStatsRow
from .source_table import BulkActionsBar, SourceTable
from .text_editor_panel import TextEditorPanel

# QualCoder-specific text highlighting (moved from design_system)
from .text_highlighter import (
    Annotation,
    AnnotationIndicator,
    CodedTextHighlight,
    CodeSegment,
    OverlapIndicator,
    TextHighlighter,
)

__all__ = [
    "CodingToolbar",
    "FilesPanel",
    "CodesPanel",
    "TextEditorPanel",
    "DetailsPanel",
    # File Manager organisms
    "SourceStatCard",
    "SourceStatsRow",
    "SourceTable",
    "BulkActionsBar",
    "FileManagerToolbar",
    "EmptyState",
    # Folder organization
    "FolderNode",
    "FolderTree",
    # Media viewers
    "ImageViewer",
    "ImageMetadata",
    "MediaPlayer",
    # Text highlighting
    "TextHighlighter",
    "CodeSegment",
    "Annotation",
    "CodedTextHighlight",
    "OverlapIndicator",
    "AnnotationIndicator",
]
