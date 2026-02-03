"""
Layout Templates

Reusable layout patterns for screen content areas.
These layouts can be used inside the AppShell's content slot.
"""

from .sidebar_layout import SidebarLayout
from .single_panel import SinglePanelLayout
from .three_panel import ThreePanelLayout

__all__ = [
    "SidebarLayout",
    "ThreePanelLayout",
    "SinglePanelLayout",
]
