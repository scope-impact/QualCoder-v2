"""
ViewModels for the Presentation layer.

ViewModels connect UI components to the application layer (services),
handling data transformation and event binding.

All ViewModels use Protocol-based dependency injection for testability.
"""

# Pure Python ViewModels - always available
from src.presentation.viewmodels.case_manager_viewmodel import CaseManagerViewModel
from src.presentation.viewmodels.file_manager_viewmodel import FileManagerViewModel
from src.presentation.viewmodels.protocols import (
    AICodingProvider,
    CaseManagerProvider,
    FileManagerController,
)
from src.presentation.viewmodels.settings_viewmodel import SettingsViewModel

# Qt-dependent ViewModels - conditional import
try:
    from src.presentation.viewmodels.ai_coding_viewmodel import AICodingViewModel
    from src.presentation.viewmodels.text_coding_viewmodel import TextCodingViewModel

    __all__ = [
        # Qt ViewModels
        "AICodingViewModel",
        "TextCodingViewModel",
        # Pure Python ViewModels
        "CaseManagerViewModel",
        "FileManagerViewModel",
        "SettingsViewModel",
        # Protocols
        "AICodingProvider",
        "CaseManagerProvider",
        "FileManagerController",
    ]
except ImportError:
    # Qt not available - only pure Python ViewModels are exported
    __all__ = [
        "CaseManagerViewModel",
        "FileManagerViewModel",
        "SettingsViewModel",
        # Protocols
        "AICodingProvider",
        "CaseManagerProvider",
        "FileManagerController",
    ]
