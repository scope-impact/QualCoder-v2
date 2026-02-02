"""
Tests for SettingsCoordinator.
"""

from returns.result import Success

from src.application.coordinators.base import CoordinatorInfrastructure
from src.application.coordinators.settings_coordinator import SettingsCoordinator


class TestSettingsCoordinatorCommands:
    """Tests for settings command methods."""

    def test_change_theme(self, coordinator_infra: CoordinatorInfrastructure):
        """Can change theme."""
        coordinator = SettingsCoordinator(coordinator_infra)

        result = coordinator.change_theme("dark")

        assert isinstance(result, Success)

    def test_change_font(self, coordinator_infra: CoordinatorInfrastructure):
        """Can change font."""
        coordinator = SettingsCoordinator(coordinator_infra)

        # Use a valid font family (Inter is the default)
        result = coordinator.change_font("Inter", 16)

        assert isinstance(result, Success)

    def test_change_language(self, coordinator_infra: CoordinatorInfrastructure):
        """Can change language."""
        coordinator = SettingsCoordinator(coordinator_infra)

        result = coordinator.change_language("es")

        assert isinstance(result, Success)

    def test_configure_backup(self, coordinator_infra: CoordinatorInfrastructure):
        """Can configure backup settings."""
        coordinator = SettingsCoordinator(coordinator_infra)

        result = coordinator.configure_backup(
            enabled=True,
            interval_minutes=30,
            max_backups=5,
        )

        assert isinstance(result, Success)

    def test_configure_av_coding(self, coordinator_infra: CoordinatorInfrastructure):
        """Can configure AV coding settings."""
        coordinator = SettingsCoordinator(coordinator_infra)

        # Use valid format with {n} placeholder
        result = coordinator.configure_av_coding(
            timestamp_format="HH:MM:SS",
            speaker_format="Speaker {n}:",
        )

        assert isinstance(result, Success)


class TestSettingsCoordinatorQueries:
    """Tests for settings query methods."""

    def test_get_all_settings(self, coordinator_infra: CoordinatorInfrastructure):
        """Can get all settings."""
        coordinator = SettingsCoordinator(coordinator_infra)

        settings = coordinator.get_all_settings()

        assert settings is not None

    def test_get_theme(self, coordinator_infra: CoordinatorInfrastructure):
        """Can get theme preference."""
        coordinator = SettingsCoordinator(coordinator_infra)

        theme = coordinator.get_theme()

        assert theme is not None

    def test_get_font(self, coordinator_infra: CoordinatorInfrastructure):
        """Can get font preference."""
        coordinator = SettingsCoordinator(coordinator_infra)

        font = coordinator.get_font()

        assert font is not None

    def test_get_language(self, coordinator_infra: CoordinatorInfrastructure):
        """Can get language preference."""
        coordinator = SettingsCoordinator(coordinator_infra)

        language = coordinator.get_language()

        assert language is not None

    def test_get_backup_config(self, coordinator_infra: CoordinatorInfrastructure):
        """Can get backup configuration."""
        coordinator = SettingsCoordinator(coordinator_infra)

        backup = coordinator.get_backup_config()

        assert backup is not None

    def test_get_av_coding_config(self, coordinator_infra: CoordinatorInfrastructure):
        """Can get AV coding configuration."""
        coordinator = SettingsCoordinator(coordinator_infra)

        av_config = coordinator.get_av_coding_config()

        assert av_config is not None


class TestSettingsCoordinatorIntegration:
    """Integration tests for settings coordinator."""

    def test_change_theme_then_get(self, coordinator_infra: CoordinatorInfrastructure):
        """Changed theme is reflected in query."""
        coordinator = SettingsCoordinator(coordinator_infra)

        coordinator.change_theme("dark")
        theme = coordinator.get_theme()

        assert theme.name == "dark"

    def test_change_font_then_get(self, coordinator_infra: CoordinatorInfrastructure):
        """Changed font is reflected in query."""
        coordinator = SettingsCoordinator(coordinator_infra)

        # Use valid font family (Inter is the default, change size)
        coordinator.change_font("Inter", 18)
        font = coordinator.get_font()

        assert font.family == "Inter"
        assert font.size == 18
