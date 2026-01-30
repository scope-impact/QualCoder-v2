"""
QualCoder UI Templates

App shell and layout patterns that compose design system components
into the standard QualCoder application structure.
"""

from .app_shell import AppShell, ScreenProtocol
from .layouts import (
    SidebarLayout,
    SinglePanelLayout,
    ThreePanelLayout,
)

__all__ = [
    # App Shell
    "AppShell",
    "ScreenProtocol",
    # Layouts
    "SidebarLayout",
    "ThreePanelLayout",
    "SinglePanelLayout",
]
