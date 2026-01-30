"""
Base Signal Bridge - Foundation for all context-specific signal bridges.

Provides thread-safe event→signal bridging between the domain layer
and PySide6 UI components.

Architecture:
    Domain Events (background thread)
         ↓ EventBus subscription
    BaseSignalBridge
         ↓ Converter (event → payload)
         ↓ Thread-safe emission
    Qt Signals (main thread)
         ↓
    UI Widgets (slot connections)
"""

from __future__ import annotations

import queue
from abc import ABCMeta, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import (
    Any,
    ClassVar,
    TypeVar,
)
from weakref import WeakValueDictionary

# Qt imports with fallback for testing without Qt
try:
    from PySide6.QtCore import QMetaObject, QObject, Qt, Signal, Slot

    HAS_QT = True

    # Create combined metaclass for QObject + ABC compatibility
    class QObjectABCMeta(type(QObject), ABCMeta):
        """Combined metaclass for QObject and ABC."""

        pass
except ImportError:
    HAS_QT = False

    # Mock for testing without Qt
    class QObject:  # type: ignore
        def __init__(self, parent: Any = None) -> None:
            pass

    def Signal(*_args: Any) -> Any:  # type: ignore
        return None

    def Slot(*_args: Any) -> Callable:  # type: ignore
        def decorator(func: Callable) -> Callable:
            return func

        return decorator

    class Qt:  # type: ignore
        class ConnectionType:
            QueuedConnection = 0

    class QMetaObject:  # type: ignore
        @staticmethod
        def invokeMethod(*_args: Any, **_kwargs: Any) -> bool:
            return True

    # For no-Qt case, ABCMeta is sufficient
    QObjectABCMeta = ABCMeta  # type: ignore

from src.application.signal_bridge.payloads import (
    ActivityItem,
    ActivityStatus,
    SignalPayload,
)
from src.application.signal_bridge.protocols import EventConverter
from src.application.signal_bridge.thread_utils import is_main_thread

T = TypeVar("T", bound=SignalPayload)
E = TypeVar("E")


@dataclass
class ConverterRegistration:
    """Registration entry for an event converter."""

    event_type: str
    converter: EventConverter
    signal_name: str


class BaseSignalBridge(QObject, metaclass=QObjectABCMeta):
    """
    Abstract base class for all context-specific signal bridges.

    Provides:
    - Singleton pattern with instance() class method
    - Thread-safe signal emission
    - Event Bus subscription management
    - Converter registry for event→payload transformation
    - Signal mapping for event→signal routing
    - Activity feed integration

    Subclasses must:
    - Define context-specific Signals
    - Implement _register_converters() to set up event handling
    - Implement _get_context_name() for activity logging

    Example subclass:
        class CodingSignalBridge(BaseSignalBridge):
            code_created = Signal(object)
            code_deleted = Signal(object)

            def _get_context_name(self) -> str:
                return "coding"

            def _register_converters(self) -> None:
                self.register_converter(
                    "coding.code_created",
                    CodeCreatedConverter(),
                    "code_created"
                )
    """

    # Class-level registry for singleton instances
    _instances: ClassVar[WeakValueDictionary[type, BaseSignalBridge]] = (
        WeakValueDictionary()
    )

    # Common signal for activity feed (all bridges emit here)
    activity_logged = Signal(object)

    def __init__(self, event_bus: Any, parent: QObject | None = None) -> None:
        """
        Initialize the signal bridge.

        Args:
            event_bus: The application event bus for subscribing to domain events
            parent: Optional Qt parent object
        """
        super().__init__(parent)
        self._event_bus = event_bus
        self._running = False

        # Converter registry: event_type → (converter, signal_name)
        self._converters: dict[str, tuple[EventConverter, str]] = {}

        # Signal registry: signal_name → Signal
        self._signals: dict[str, Any] = {}

        # Subscription handles for cleanup
        self._subscriptions: list[tuple[str, Callable]] = []

        # Thread-safe queue for cross-thread signal emissions
        self._emission_queue: queue.Queue[tuple[Any, Any]] = queue.Queue()

        # Build signal registry from class attributes
        self._build_signal_registry()

        # Let subclasses register their converters
        self._register_converters()

    @classmethod
    def instance(cls, event_bus: Any | None = None) -> BaseSignalBridge:
        """
        Get or create the singleton instance.

        Args:
            event_bus: Required on first call, optional thereafter

        Returns:
            The singleton instance of this bridge class

        Raises:
            ValueError: If event_bus not provided on first instantiation
        """
        if cls not in cls._instances:
            if event_bus is None:
                raise ValueError(
                    f"{cls.__name__}.instance() requires event_bus on first call"
                )
            instance = cls(event_bus)
            cls._instances[cls] = instance
        return cls._instances[cls]

    @classmethod
    def clear_instance(cls) -> None:
        """Clear the singleton instance (useful for testing)."""
        if cls in cls._instances:
            instance = cls._instances[cls]
            instance.stop()
            del cls._instances[cls]

    def _build_signal_registry(self) -> None:
        """Build registry of available signals from class attributes."""
        for name in dir(self.__class__):
            attr = getattr(self.__class__, name, None)
            # Check if it's a Signal (has 'emit' when bound)
            if hasattr(attr, "emit") or (
                HAS_QT and hasattr(attr, "__class__") and "Signal" in str(type(attr))
            ):
                # Get the bound signal from the instance
                self._signals[name] = getattr(self, name)

    @abstractmethod
    def _register_converters(self) -> None:
        """
        Register event converters for this context.

        Subclasses implement this to set up their event→signal mappings.

        Example:
            def _register_converters(self) -> None:
                self.register_converter(
                    "coding.code_created",
                    CodeCreatedConverter(),
                    "code_created"
                )
        """
        pass

    @abstractmethod
    def _get_context_name(self) -> str:
        """
        Return the bounded context name for activity logging.

        Returns:
            Context name (e.g., "coding", "sources", "cases")
        """
        pass

    def register_converter(
        self, event_type: str, converter: EventConverter, signal_name: str
    ) -> None:
        """
        Register a converter for an event type.

        Args:
            event_type: The domain event type string (e.g., "coding.code_created")
            converter: Converter instance to transform event→payload
            signal_name: Name of the signal to emit (must exist on this class)

        Raises:
            ValueError: If signal_name doesn't exist on this bridge
        """
        if signal_name not in self._signals:
            raise ValueError(
                f"Signal '{signal_name}' not found on {self.__class__.__name__}. "
                f"Available: {list(self._signals.keys())}"
            )
        self._converters[event_type] = (converter, signal_name)

    def start(self) -> None:
        """
        Start listening to domain events.

        Subscribes to all registered event types on the event bus.
        """
        if self._running:
            return

        for event_type in self._converters:
            handler = self._make_handler(event_type)
            self._event_bus.subscribe(event_type, handler)
            self._subscriptions.append((event_type, handler))

        self._running = True

    def stop(self) -> None:
        """
        Stop listening and clean up subscriptions.
        """
        if not self._running:
            return

        import contextlib

        for event_type, handler in self._subscriptions:
            with contextlib.suppress(Exception):
                self._event_bus.unsubscribe(event_type, handler)

        self._subscriptions.clear()
        self._running = False

    def is_running(self) -> bool:
        """Check if the bridge is currently listening."""
        return self._running

    def _make_handler(self, event_type: str) -> Callable[[Any], None]:
        """Create an event handler for the given event type."""

        def handler(event: Any) -> None:
            self._dispatch_event(event_type, event)

        return handler

    def _dispatch_event(self, event_type: str, event: Any) -> None:
        """
        Dispatch a domain event to the appropriate signal.

        Args:
            event_type: The event type string
            event: The domain event instance
        """
        if event_type not in self._converters:
            return

        converter, signal_name = self._converters[event_type]

        try:
            # Convert event to payload
            payload = converter.convert(event)

            # Get the signal
            signal = self._signals.get(signal_name)
            if signal is None:
                return

            # Emit thread-safely
            self._emit_threadsafe(signal, payload)

            # Also emit to activity feed
            activity = self._create_activity_item(event, payload)
            if activity:
                self._emit_threadsafe(self.activity_logged, activity)

        except Exception as e:
            # Log error but don't crash the event bus
            import warnings

            warnings.warn(
                f"Error dispatching {event_type}: {e}", RuntimeWarning, stacklevel=2
            )

    def _emit_threadsafe(self, signal: Any, payload: Any) -> None:
        """
        Emit a signal in a thread-safe manner.

        If already on the main thread, emits directly.
        Otherwise, queues the emission for the main thread using a thread-safe
        queue to avoid race conditions with concurrent background threads.

        Args:
            signal: The PySide6 signal to emit
            payload: The payload to emit
        """
        if is_main_thread():
            # Already on main thread - emit directly
            signal.emit(payload)
        elif HAS_QT:
            # Add to thread-safe queue and trigger main thread processing
            self._emission_queue.put((signal, payload))
            QMetaObject.invokeMethod(
                self,
                "_do_emit",
                Qt.ConnectionType.QueuedConnection,
            )
        else:
            # No Qt - emit directly (testing mode)
            signal.emit(payload)

    @Slot()
    def _do_emit(self) -> None:
        """Slot for queued signal emission on main thread.

        Processes all pending emissions from the thread-safe queue.
        """
        while True:
            try:
                signal, payload = self._emission_queue.get_nowait()
                signal.emit(payload)
            except queue.Empty:
                break

    def _create_activity_item(
        self, event: Any, payload: SignalPayload
    ) -> ActivityItem | None:
        """
        Create an activity item from an event and payload.

        Override in subclasses for context-specific formatting.

        Args:
            event: The original domain event
            payload: The converted signal payload

        Returns:
            ActivityItem for the activity feed, or None to skip
        """
        # Default implementation - subclasses can override for richer formatting
        event_type = getattr(event, "event_type", payload.event_type)
        return ActivityItem(
            timestamp=payload.timestamp,
            session_id=payload.session_id,
            description=f"{event_type}",
            status=ActivityStatus.COMPLETED,
            context=self._get_context_name(),
            entity_type=event_type.split(".")[-1] if "." in event_type else event_type,
            is_ai_action=payload.is_ai_action,
        )

    def emit_activity(
        self,
        description: str,
        entity_type: str,
        entity_id: str | None = None,
        status: ActivityStatus = ActivityStatus.COMPLETED,
        session_id: str = "local",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Emit an activity item directly.

        Convenience method for logging activities outside of event handling.

        Args:
            description: Human-readable description
            entity_type: Type of entity (e.g., "code", "segment")
            entity_id: Optional entity identifier
            status: Activity status
            session_id: Session that triggered the activity
            metadata: Additional context
        """
        activity = ActivityItem(
            timestamp=datetime.utcnow(),
            session_id=session_id,
            description=description,
            status=status,
            context=self._get_context_name(),
            entity_type=entity_type,
            entity_id=entity_id,
            is_ai_action=session_id != "local",
            metadata=metadata or {},
        )
        self._emit_threadsafe(self.activity_logged, activity)

    def __enter__(self) -> BaseSignalBridge:
        """Context manager entry - start listening."""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - stop listening."""
        self.stop()
