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
"""

from .codes_panel import CodesPanel
from .coding_toolbar import CodingToolbar
from .details_panel import DetailsPanel
from .files_panel import FilesPanel
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
    # Text highlighting
    "TextHighlighter",
    "CodeSegment",
    "Annotation",
    "CodedTextHighlight",
    "OverlapIndicator",
    "AnnotationIndicator",
]
