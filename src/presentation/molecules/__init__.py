"""
UI Molecules

Reusable combinations of atoms that form functional UI units.
Each molecule is a small, composable piece that can be combined into organisms.

Following Atomic Design methodology:
- Atoms: Basic UI elements (buttons, icons, inputs) - in design_system
- Molecules: Simple combinations of atoms - THIS LAYER
- Organisms: Complex, self-contained sections of UI
- Templates: Page-level layouts
- Pages: Specific instances with data

Molecules in this module:
- SearchBar: Search input with navigation and options
- LineNumberGutter: Line numbers for text editors
- OverlapDetector: Detect and merge overlapping ranges
- SelectionPopupController: Timer-based popup management
- MemoListItem: Clickable memo preview card
- MatchPreviewPanel: Scrollable list of match previews with summary
- MatchPreviewItem: Single match preview card
"""

from .editor import LineNumberGutter
from .highlighting import OverlapDetector
from .memo import MemoListItem
from .preview import MatchPreviewItem, MatchPreviewPanel
from .search import SearchBar
from .selection import SelectionPopupController

__all__ = [
    "LineNumberGutter",
    "MatchPreviewItem",
    "MatchPreviewPanel",
    "MemoListItem",
    "OverlapDetector",
    "SearchBar",
    "SelectionPopupController",
]
