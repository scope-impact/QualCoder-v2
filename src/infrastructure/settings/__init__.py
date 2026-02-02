"""
DEPRECATED: Use src.contexts.settings.infra instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

# Re-export from new location
from src.contexts.settings.infra.user_settings_repository import (
    UserSettingsRepository,
)

__all__ = [
    "UserSettingsRepository",
]
