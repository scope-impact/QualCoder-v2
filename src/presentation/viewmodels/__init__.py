"""
ViewModels for the Presentation layer.

ViewModels connect UI components to the application layer (controllers),
handling data transformation and event binding.
"""

# Pure Python ViewModels - always available
from src.presentation.viewmodels.file_manager_viewmodel import FileManagerViewModel
from src.presentation.viewmodels.settings_viewmodel import SettingsViewModel

# Qt-dependent ViewModels - conditional import
try:
    from src.presentation.viewmodels.ai_coding_viewmodel import AICodingViewModel
    from src.presentation.viewmodels.text_coding_viewmodel import TextCodingViewModel

    __all__ = [
        "AICodingViewModel",
        "TextCodingViewModel",
        "FileManagerViewModel",
        "SettingsViewModel",
    ]
except ImportError:
    # Qt not available - only pure Python ViewModels are exported
    __all__ = [
        "FileManagerViewModel",
        "SettingsViewModel",
    ]
