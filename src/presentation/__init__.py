"""
Presentation Layer - PySide6 UI Components

Part of the DDD architecture (Domain → Application → Infrastructure → Presentation).
This layer handles all user interface concerns using Atomic Design methodology.

Components:
- Templates: App shell and layout patterns specific to QualCoder
- Organisms: Reusable, self-contained complex components
- Pages: Composed views that combine organisms
- Screens: Individual screen content that fills the templates
- DTOs: Data transfer objects for decoupling UI from domain entities
- Sample Data: Mock data providers for development/testing

Architecture (Atomic Design):
    Design System (Atoms/Molecules) → Organisms → Pages → Screens → Templates

Data Flow:
    Application Controller → DTO → Screen → Page → Organisms
    Sample Data Provider → DTO → Screen (for development/testing)

Usage:
    # Import organisms for standalone development/testing
    from src.presentation.organisms import CodingToolbar, FilesPanel, CodesPanel

    # Import pages for composed views
    from src.presentation.pages import TextCodingPage

    # Import screens for full application
    from src.presentation.screens import TextCodingScreen
    from src.presentation.templates import AppShell

    # Import DTOs for data contracts
    from src.presentation.dto import TextCodingDataDTO, FileDTO, CodeDTO

    # Import sample data for mocking
    from src.presentation.sample_data import create_sample_text_coding_data
"""

from .templates import AppShell, ThreePanelLayout
from .screens import TextCodingScreen
from .pages import TextCodingPage
from .organisms import (
    CodingToolbar,
    FilesPanel,
    CodesPanel,
    TextEditorPanel,
    DetailsPanel,
)
from .dto import (
    FileDTO,
    CodeDTO,
    CodeCategoryDTO,
    DocumentDTO,
    DocumentStatsDTO,
    SelectedCodeDTO,
    OverlappingSegmentDTO,
    FileMemoDTO,
    NavigationDTO,
    TextCodingDataDTO,
)
from .sample_data import create_sample_text_coding_data

__all__ = [
    # Templates
    "AppShell",
    "ThreePanelLayout",
    # Screens
    "TextCodingScreen",
    # Pages
    "TextCodingPage",
    # Organisms
    "CodingToolbar",
    "FilesPanel",
    "CodesPanel",
    "TextEditorPanel",
    "DetailsPanel",
    # DTOs
    "FileDTO",
    "CodeDTO",
    "CodeCategoryDTO",
    "DocumentDTO",
    "DocumentStatsDTO",
    "SelectedCodeDTO",
    "OverlappingSegmentDTO",
    "FileMemoDTO",
    "NavigationDTO",
    "TextCodingDataDTO",
    # Sample Data
    "create_sample_text_coding_data",
]
