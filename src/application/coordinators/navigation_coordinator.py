"""
Navigation Coordinator - Screen and Segment Navigation.

Handles navigation between screens and to specific segments.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from returns.result import Result

from src.application.coordinators.base import BaseCoordinator

if TYPE_CHECKING:
    from src.presentation.screens.text_coding import TextCodingScreen


class NavigationCoordinator(BaseCoordinator):
    """
    Coordinator for navigation operations.

    Manages:
    - Navigating to different screens
    - Navigating to specific segments within sources
    - Connecting screens to navigation events

    Navigation is used by both the UI and MCP tools to move
    the user's view to specific locations.
    """

    def __init__(self, infra) -> None:
        """Initialize with infrastructure and connected screen storage."""
        super().__init__(infra)
        self._text_coding_screen: TextCodingScreen | None = None

    # =========================================================================
    # Navigation Commands
    # =========================================================================

    def navigate_to_screen(self, command) -> Result:
        """
        Navigate to a different screen.

        Args:
            command: NavigateToScreenCommand or string with target screen name

        Returns:
            Success with ScreenChanged event
        """
        from src.application.navigation.usecases import navigate_to_screen
        from src.application.projects.commands import NavigateToScreenCommand

        # Accept either command or string for convenience
        if isinstance(command, str):
            command = NavigateToScreenCommand(screen_name=command)

        return navigate_to_screen(
            command=command,
            state=self.state,
            event_bus=self.event_bus,
        )

    def navigate_to_segment(self, command) -> Result:
        """
        Navigate to a specific segment in a source.

        Args:
            command: NavigateToSegmentCommand with source ID and position

        Returns:
            Success with event, or Failure with error
        """
        from src.application.navigation.usecases import navigate_to_segment

        return navigate_to_segment(
            command=command,
            state=self.state,
            event_bus=self.event_bus,
        )

    # =========================================================================
    # Navigation Queries
    # =========================================================================

    def get_current_screen(self) -> str | None:
        """Get the current screen name."""
        return self.state.current_screen

    # =========================================================================
    # Screen Connection
    # =========================================================================

    def connect_text_coding_screen(self, screen: TextCodingScreen) -> None:
        """
        Connect a TextCodingScreen to receive navigation events.

        When the signal bridge emits navigated_to_segment, the screen
        will scroll to and highlight the specified segment.

        Args:
            screen: The TextCodingScreen to connect
        """
        self._text_coding_screen = screen

        if self.signal_bridge is not None:
            self.signal_bridge.navigated_to_segment.connect(
                screen.on_navigated_to_segment
            )

    def disconnect_text_coding_screen(self, screen: TextCodingScreen) -> None:
        """Disconnect a TextCodingScreen from navigation events."""
        if self.signal_bridge is not None:
            with contextlib.suppress(RuntimeError):
                self.signal_bridge.navigated_to_segment.disconnect(
                    screen.on_navigated_to_segment
                )

        if self._text_coding_screen is screen:
            self._text_coding_screen = None
