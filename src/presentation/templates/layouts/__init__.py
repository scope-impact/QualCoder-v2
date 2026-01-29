"""
Layout Templates

Reusable layout patterns for screen content areas.
These layouts can be used inside the AppShell's content slot.
"""

from .sidebar_layout import SidebarLayout
from .three_panel import ThreePanelLayout
from .single_panel import SinglePanelLayout

__all__ = [
    "SidebarLayout",
    "ThreePanelLayout",
    "SinglePanelLayout",
]
