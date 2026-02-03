"""
Settings ViewModel

Connects the SettingsDialog to the settings use cases via the Coordinator.
Handles data transformation between domain entities and UI DTOs.

Implements QC-038 presentation layer:
- AC #1: Researcher can change UI theme
- AC #2: Researcher can configure font size and family
- AC #3: Researcher can select application language
- AC #4: Researcher can configure automatic backups
- AC #5: Researcher can set timestamp format for AV coding
- AC #6: Researcher can configure speaker name format
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from returns.result import Success

from src.contexts.settings.core.invariants import (
    VALID_FONT_FAMILIES,
    VALID_LANGUAGES,
    VALID_THEMES,
    VALID_TIMESTAMP_FORMATS,
)
from src.shared.presentation.dto import (
    FontFamilyOptionDTO,
    LanguageOptionDTO,
    SettingsDTO,
)

if TYPE_CHECKING:
    from returns.result import Result

    from src.contexts.settings.core.entities import UserSettings


class SettingsProvider(Protocol):
    """Protocol for settings access - can be Coordinator or test double."""

    def get_all_settings(self) -> UserSettings: ...
    def change_theme(self, theme: str) -> Result: ...
    def change_font(self, family: str, size: int) -> Result: ...
    def change_language(self, language_code: str) -> Result: ...
    def configure_backup(
        self,
        enabled: bool,
        interval_minutes: int,
        max_backups: int,
        backup_path: str | None = None,
    ) -> Result: ...
    def configure_av_coding(
        self,
        timestamp_format: str,
        speaker_format: str,
    ) -> Result: ...
    def change_backend(self, backend_type: str) -> Result: ...
    def set_convex_url(self, url: str | None) -> Result: ...


class SettingsViewModel:
    """
    ViewModel for the Settings dialog.

    Responsibilities:
    - Transform domain settings to UI DTOs
    - Handle user actions by calling use cases via provider
    - Provide available options for dropdowns
    - Track pending changes before applying

    This is a pure Python class (no Qt dependency) so it can be
    tested without a Qt event loop.
    """

    def __init__(
        self,
        settings_provider: SettingsProvider,
    ) -> None:
        """
        Initialize the ViewModel.

        Args:
            settings_provider: Provider for settings access (typically Coordinator)
        """
        self._provider = settings_provider

    # =========================================================================
    # Load Data
    # =========================================================================

    def get_settings(self) -> SettingsDTO:
        """
        Load current settings as DTO.

        Returns:
            SettingsDTO with current values
        """
        settings = self._provider.get_all_settings()
        return SettingsDTO(
            theme=settings.theme.name,
            font_family=settings.font.family,
            font_size=settings.font.size,
            language_code=settings.language.code,
            language_name=settings.language.name,
            backup_enabled=settings.backup.enabled,
            backup_interval=settings.backup.interval_minutes,
            backup_max=settings.backup.max_backups,
            backup_path=settings.backup.backup_path,
            timestamp_format=settings.av_coding.timestamp_format,
            speaker_format=settings.av_coding.speaker_format,
            backend_type=settings.backend.backend_type,
            convex_url=settings.backend.convex_url,
        )

    # =========================================================================
    # Available Options
    # =========================================================================

    def get_available_themes(self) -> list[str]:
        """Get list of available theme names."""
        return list(VALID_THEMES)

    def get_available_languages(self) -> list[LanguageOptionDTO]:
        """Get list of available languages."""
        return [
            LanguageOptionDTO(code=code, name=name)
            for code, name in VALID_LANGUAGES.items()
        ]

    def get_available_fonts(self) -> list[FontFamilyOptionDTO]:
        """Get list of available font families."""
        display_names = {
            "Inter": "Inter",
            "Roboto": "Roboto",
            "Open Sans": "Open Sans",
            "Source Sans Pro": "Source Sans Pro",
            "Noto Sans": "Noto Sans",
            "JetBrains Mono": "JetBrains Mono (Monospace)",
            "Fira Code": "Fira Code (Monospace)",
            "system-ui": "System Default",
        }
        return [
            FontFamilyOptionDTO(
                family=family,
                display_name=display_names.get(family, family),
            )
            for family in VALID_FONT_FAMILIES
        ]

    def get_available_timestamp_formats(self) -> list[str]:
        """Get list of available timestamp formats."""
        return list(VALID_TIMESTAMP_FORMATS)

    # =========================================================================
    # Theme Actions (AC #1)
    # =========================================================================

    def change_theme(self, theme: str) -> bool:
        """
        Change the application theme.

        Args:
            theme: New theme name (light, dark, system)

        Returns:
            True if successful, False otherwise
        """
        result = self._provider.change_theme(theme)
        return isinstance(result, Success)

    # =========================================================================
    # Font Actions (AC #2)
    # =========================================================================

    def change_font(self, family: str, size: int) -> bool:
        """
        Change font settings.

        Args:
            family: Font family name
            size: Font size in pixels

        Returns:
            True if successful, False otherwise
        """
        result = self._provider.change_font(family, size)
        return isinstance(result, Success)

    # =========================================================================
    # Language Actions (AC #3)
    # =========================================================================

    def change_language(self, code: str) -> bool:
        """
        Change application language.

        Args:
            code: ISO 639-1 language code

        Returns:
            True if successful, False otherwise
        """
        result = self._provider.change_language(code)
        return isinstance(result, Success)

    # =========================================================================
    # Backup Actions (AC #4)
    # =========================================================================

    def configure_backup(
        self,
        enabled: bool,
        interval: int,
        max_backups: int,
        path: str | None = None,
    ) -> bool:
        """
        Configure backup settings.

        Args:
            enabled: Whether automatic backups are enabled
            interval: Backup interval in minutes
            max_backups: Maximum number of backups to keep
            path: Optional custom backup path

        Returns:
            True if successful, False otherwise
        """
        result = self._provider.configure_backup(
            enabled=enabled,
            interval_minutes=interval,
            max_backups=max_backups,
            backup_path=path,
        )
        return isinstance(result, Success)

    # =========================================================================
    # AV Coding Actions (AC #5, #6)
    # =========================================================================

    def configure_av_coding(
        self,
        timestamp_format: str,
        speaker_format: str,
    ) -> bool:
        """
        Configure AV coding settings.

        Args:
            timestamp_format: Timestamp display format
            speaker_format: Speaker name format template

        Returns:
            True if successful, False otherwise
        """
        result = self._provider.configure_av_coding(
            timestamp_format=timestamp_format,
            speaker_format=speaker_format,
        )
        return isinstance(result, Success)

    # =========================================================================
    # Validation Helpers
    # =========================================================================

    def validate_speaker_format(self, format_str: str) -> bool:
        """Check if speaker format is valid."""
        return "{n}" in format_str and len(format_str.strip()) > 0

    def get_speaker_format_preview(self, format_str: str, speaker_num: int = 1) -> str:
        """Get a preview of the speaker format."""
        try:
            return format_str.replace("{n}", str(speaker_num))
        except Exception:
            return format_str

    # =========================================================================
    # Backend Actions
    # =========================================================================

    def change_backend(self, backend_type: str) -> bool:
        """
        Change the database backend type.

        Args:
            backend_type: Backend type ("sqlite" or "convex")

        Returns:
            True if successful, False otherwise
        """
        result = self._provider.change_backend(backend_type)
        return isinstance(result, Success)

    def set_convex_url(self, url: str | None) -> bool:
        """
        Set the Convex deployment URL.

        Args:
            url: Convex deployment URL or None to clear

        Returns:
            True if successful, False otherwise
        """
        result = self._provider.set_convex_url(url)
        return isinstance(result, Success)
