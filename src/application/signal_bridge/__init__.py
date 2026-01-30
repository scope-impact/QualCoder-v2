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

    class CodingSignalBridge(BaseSignalBridge):
        code_created = pyqtSignal(object)

        def _get_context_name(self) -> str:
            return "coding"

        def _register_converters(self) -> None:
            self.register_converter(
                "coding.code_created",
                MyConverter(),
                "code_created"
            )
"""

from src.application.signal_bridge.payloads import (
    SignalPayload,
    ActivityItem,
    ActivityStatus,
)
from src.application.signal_bridge.protocols import (
    EventConverter,
    ActivityFormatter,
    SignalBridge,
)
from src.application.signal_bridge.thread_utils import (
    is_main_thread,
    get_current_thread_name,
    ensure_main_thread,
    ThreadChecker,
)
from src.application.signal_bridge.base import (
    BaseSignalBridge,
    ConverterRegistration,
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
    "ensure_main_thread",
    "ThreadChecker",
    # Base class
    "BaseSignalBridge",
    "ConverterRegistration",
]
