"""
UI Pages

Pages compose organisms into complete views that represent specific application states.
Each page is a concrete implementation that can be plugged into a screen/template.

Pages handle:
- Composing organisms into a cohesive layout
- Managing data flow between organisms
- Providing sample data for standalone development
- Connecting organism signals to page-level actions

Structure:
    Screen (Template) → Page → Organisms → Design System Components
"""

from .case_manager_page import CaseManagerPage
from .file_manager_page import FileManagerPage
from .references_page import ReferencesPage
from .text_coding_page import TextCodingPage

__all__ = [
    "TextCodingPage",
    "FileManagerPage",
    "CaseManagerPage",
    "ReferencesPage",
]
