"""
Navigation Service - Stateful Navigation Management.

Provides a stateful interface for navigation operations, tracking
current screen state and managing UI connections.

This service wraps the functional navigation use cases while adding:
- Current screen state tracking
- TextCodingScreen connection management for segment navigation
- Signal bridge integration for reactive UI updates

Usage:
    from src.application.navigation.service import NavigationService

    service = NavigationService(ctx)
    service.navigate_to_screen("coding")
    service.connect_text_coding_screen(screen)
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from returns.result import Result

from src.application.navigation.usecases import navigate_to_screen, navigate_to_segment
from src.application.projects.commands import (
    NavigateToScreenCommand,
    NavigateToSegmentCommand,
)

if TYPE_CHECKING:
    from src.application.event_bus import EventBus
    from src.application.projects.signal_bridge import ProjectSignalBridge
    from src.application.state import ProjectState
    from src.contexts.projects.core.events import NavigatedToSegment, ScreenChanged
    from src.presentation.screens.text_coding import TextCodingScreen


@runtime_checkable
class NavigationContext(Protocol):
    """
    Protocol defining the context requirements for NavigationService.

    This protocol allows NavigationService to work with both AppContext
    (the target architecture) and CoordinatorInfrastructure (legacy).
    """

    @property
    def state(self) -> ProjectState:
        """Get the project state cache."""
        ...

    @property
    def event_bus(self) -> EventBus:
        """Get the event bus for publishing domain events."""
        ...

    @property
    def signal_bridge(self) -> ProjectSignalBridge | None:
        """Get the signal bridge for UI updates (optional)."""
        ...


class NavigationService:
    """
    Stateful service for navigation operations.

    Manages:
    - Navigating to different screens
    - Navigating to specific segments within sources
    - Connecting screens to navigation events

    This service is stateful because:
    1. It tracks the current screen state
    2. It maintains connections to TextCodingScreen instances
    3. It bridges domain events to UI updates

    The service wraps the functional use cases (navigate_to_screen,
    navigate_to_segment) and adds stateful management on top.

    Example:
        # Create service with context
        nav_service = NavigationService(app_context)

        # Navigate to a screen
        nav_service.navigate_to_screen("coding")

        # Connect a screen for segment navigation
        nav_service.connect_text_coding_screen(text_coding_screen)

        # Navigate to a specific segment
        cmd = NavigateToSegmentCommand(source_id=1, start_pos=100, end_pos=200)
        nav_service.navigate_to_segment(cmd)
    """

    def __init__(self, ctx: NavigationContext) -> None:
        """
        Initialize NavigationService with a context.

        Args:
            ctx: Context providing state, event_bus, and signal_bridge.
                 Can be either AppContext or CoordinatorInfrastructure.
        """
        self._ctx = ctx
        self._text_coding_screen: TextCodingScreen | None = None

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def state(self) -> ProjectState:
        """Get the project state cache."""
        return self._ctx.state

    @property
    def event_bus(self) -> EventBus:
        """Get the event bus."""
        return self._ctx.event_bus

    @property
    def signal_bridge(self) -> ProjectSignalBridge | None:
        """Get the signal bridge (None if Qt not available)."""
        return self._ctx.signal_bridge

    # =========================================================================
    # Navigation Commands
    # =========================================================================

    def navigate_to_screen(
        self, command: NavigateToScreenCommand | str
    ) -> Result[ScreenChanged, str]:
        """
        Navigate to a different screen.

        Updates the current screen state and publishes a ScreenChanged event.
        The signal bridge will emit screen_changed for UI updates.

        Args:
            command: NavigateToScreenCommand or string with target screen name.
                    Accepts string for convenience (e.g., "coding", "file_manager").

        Returns:
            Success with ScreenChanged event containing from_screen and to_screen.

        Example:
            # Using string (convenience)
            service.navigate_to_screen("coding")

            # Using command object
            cmd = NavigateToScreenCommand(screen_name="coding")
            service.navigate_to_screen(cmd)
        """
        # Accept either command or string for convenience
        if isinstance(command, str):
            command = NavigateToScreenCommand(screen_name=command)

        return navigate_to_screen(
            command=command,
            state=self.state,
            event_bus=self.event_bus,
        )

    def navigate_to_segment(
        self, command: NavigateToSegmentCommand
    ) -> Result[NavigatedToSegment, str]:
        """
        Navigate to a specific segment in a source.

        This will:
        1. Open the specified source
        2. Navigate to the coding screen
        3. Publish events for UI to scroll to and highlight the position

        The connected TextCodingScreen will receive the navigated_to_segment
        signal and scroll to the specified position.

        Args:
            command: NavigateToSegmentCommand with:
                - source_id: ID of the source to navigate to
                - start_pos: Start character position in the source
                - end_pos: End character position in the source
                - highlight: Whether to highlight the segment (default True)

        Returns:
            Success with NavigatedToSegment event, or Failure with error message.
            Possible failures:
            - "No project is currently open"
            - "Source {id} not found"

        Example:
            cmd = NavigateToSegmentCommand(
                source_id=42,
                start_pos=100,
                end_pos=250,
                highlight=True
            )
            result = service.navigate_to_segment(cmd)
        """
        return navigate_to_segment(
            command=command,
            state=self.state,
            event_bus=self.event_bus,
        )

    # =========================================================================
    # Navigation Queries
    # =========================================================================

    def get_current_screen(self) -> str | None:
        """
        Get the current screen name.

        Returns:
            The name of the currently active screen (e.g., "coding",
            "file_manager"), or None if no screen is active.
        """
        return self.state.current_screen

    # =========================================================================
    # Screen Connection Management
    # =========================================================================

    def connect_text_coding_screen(self, screen: TextCodingScreen) -> None:
        """
        Connect a TextCodingScreen to receive navigation events.

        When the signal bridge emits navigated_to_segment, the connected
        screen will scroll to and highlight the specified segment.

        This enables agent-driven navigation: when an MCP tool or AI assistant
        calls navigate_to_segment(), the UI will respond automatically.

        Args:
            screen: The TextCodingScreen instance to connect.

        Note:
            Only one screen can be connected at a time. Connecting a new
            screen will not automatically disconnect the previous one.
            Call disconnect_text_coding_screen() first if needed.
        """
        self._text_coding_screen = screen

        if self.signal_bridge is not None:
            self.signal_bridge.navigated_to_segment.connect(
                screen.on_navigated_to_segment
            )

    def disconnect_text_coding_screen(self, screen: TextCodingScreen) -> None:
        """
        Disconnect a TextCodingScreen from navigation events.

        The screen will no longer receive navigated_to_segment signals.

        Args:
            screen: The TextCodingScreen instance to disconnect.
        """
        if self.signal_bridge is not None:
            with contextlib.suppress(RuntimeError):
                self.signal_bridge.navigated_to_segment.disconnect(
                    screen.on_navigated_to_segment
                )

        if self._text_coding_screen is screen:
            self._text_coding_screen = None

    def get_connected_screen(self) -> TextCodingScreen | None:
        """
        Get the currently connected TextCodingScreen.

        Returns:
            The connected TextCodingScreen, or None if no screen is connected.
        """
        return self._text_coding_screen
