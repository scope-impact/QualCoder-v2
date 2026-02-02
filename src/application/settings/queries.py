"""
Settings Queries - Pure Read Operations

Query functions for retrieving settings data.
These are pure functions that read from the repository with no side effects.

Global scope - no project required.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.contexts.settings.core.entities import (
        AVCodingConfig,
        BackupConfig,
        FontPreference,
        LanguagePreference,
        ThemePreference,
        UserSettings,
    )
    from src.contexts.settings.infra import UserSettingsRepository


def get_all_settings(settings_repo: UserSettingsRepository) -> UserSettings:
    """
    Get all current settings.

    Args:
        settings_repo: Repository for settings persistence

    Returns:
        Complete UserSettings object
    """
    return settings_repo.load()


def get_theme(settings_repo: UserSettingsRepository) -> ThemePreference:
    """
    Get current theme preference.

    Args:
        settings_repo: Repository for settings persistence

    Returns:
        Current ThemePreference
    """
    return settings_repo.get_theme()


def get_font(settings_repo: UserSettingsRepository) -> FontPreference:
    """
    Get current font preference.

    Args:
        settings_repo: Repository for settings persistence

    Returns:
        Current FontPreference
    """
    return settings_repo.get_font()


def get_language(settings_repo: UserSettingsRepository) -> LanguagePreference:
    """
    Get current language preference.

    Args:
        settings_repo: Repository for settings persistence

    Returns:
        Current LanguagePreference
    """
    return settings_repo.get_language()


def get_backup_config(settings_repo: UserSettingsRepository) -> BackupConfig:
    """
    Get current backup configuration.

    Args:
        settings_repo: Repository for settings persistence

    Returns:
        Current BackupConfig
    """
    return settings_repo.get_backup_config()


def get_av_coding_config(settings_repo: UserSettingsRepository) -> AVCodingConfig:
    """
    Get current AV coding configuration.

    Args:
        settings_repo: Repository for settings persistence

    Returns:
        Current AVCodingConfig
    """
    return settings_repo.get_av_coding_config()
