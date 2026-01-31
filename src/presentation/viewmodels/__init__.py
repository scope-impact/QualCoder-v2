"""
ViewModels for the Presentation layer.

ViewModels connect UI components to the application layer (controllers),
handling data transformation and event binding.
"""

# Pure Python ViewModels - always available
from src.presentation.viewmodels.file_manager_viewmodel import FileManagerViewModel

# Qt-dependent ViewModels - conditional import
try:
    from src.presentation.viewmodels.text_coding_viewmodel import TextCodingViewModel

    __all__ = [
        "TextCodingViewModel",
        "FileManagerViewModel",
    ]
except ImportError:
    # Qt not available - only pure Python ViewModels are exported
    __all__ = [
        "FileManagerViewModel",
    ]
