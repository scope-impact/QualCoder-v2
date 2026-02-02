"""
DEPRECATED: Use src.contexts.settings.core.events instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.settings.core.events import (
    AVCodingConfigChanged,
    BackupConfigChanged,
    FontChanged,
    LanguageChanged,
    ThemeChanged,
)

__all__ = [
    "AVCodingConfigChanged",
    "BackupConfigChanged",
    "FontChanged",
    "LanguageChanged",
    "ThemeChanged",
]
