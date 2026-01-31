"""
Signal Bridge Infrastructure

Thread-safe bridging between domain events and PySide6 signals.

Usage:
    from src.application.signal_bridge import (
        BaseSignalBridge,
        SignalPayload,
        ActivityItem,
        ActivityStatus,
        EventConverter,
    )
    from PySide6.QtCore import Signal

    class CodingSignalBridge(BaseSignalBridge):
        code_created = Signal(object)

        def _get_context_name(self) -> str:
            return "coding"

        def _register_converters(self) -> None:
            self.register_converter(
                "coding.code_created",
                MyConverter(),
                "code_created"
            )
"""

from src.application.signal_bridge.base import (
    BaseSignalBridge,
    ConverterRegistration,
)
from src.application.signal_bridge.payloads import (
    ActivityItem,
    ActivityStatus,
    SignalPayload,
)
from src.application.signal_bridge.protocols import (
    ActivityFormatter,
    EventConverter,
    SignalBridge,
)
from src.application.signal_bridge.thread_utils import (
    ThreadChecker,
    ensure_main_thread,
    get_current_thread_name,
    is_main_thread,
    warn_if_not_main_thread,
)

__all__ = [
    # Payloads
    "SignalPayload",
    "ActivityItem",
    "ActivityStatus",
    # Protocols
    "EventConverter",
    "ActivityFormatter",
    "SignalBridge",
    # Thread utilities
    "is_main_thread",
    "get_current_thread_name",
    "ensure_main_thread",  # deprecated alias for warn_if_not_main_thread
    "warn_if_not_main_thread",
    "ThreadChecker",
    # Base class
    "BaseSignalBridge",
    "ConverterRegistration",
]
