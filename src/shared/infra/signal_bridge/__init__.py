"""
Signal Bridge Infrastructure

Thread-safe bridging between domain events and PySide6 signals.

Usage:
    from src.shared.infra.signal_bridge import (
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

from src.shared.infra.signal_bridge.base import (
    BaseSignalBridge,
    ConverterRegistration,
    EventConverter,
)
from src.shared.infra.signal_bridge.payloads import (
    ActivityItem,
    ActivityStatus,
    SignalPayload,
)
from src.shared.infra.signal_bridge.thread_utils import (
    ThreadChecker,
    get_current_thread_name,
    is_main_thread,
    warn_if_not_main_thread,
)
from src.shared.infra.signal_bridge.sync import (
    SyncSignalBridge,
    SyncStatusPayload,
    SyncResultPayload,
)

__all__ = [
    # Payloads
    "SignalPayload",
    "ActivityItem",
    "ActivityStatus",
    "SyncStatusPayload",
    "SyncResultPayload",
    # Converter type
    "EventConverter",
    # Thread utilities
    "is_main_thread",
    "get_current_thread_name",
    "warn_if_not_main_thread",
    "ThreadChecker",
    # Base class
    "BaseSignalBridge",
    "ConverterRegistration",
    # Sync bridge
    "SyncSignalBridge",
]
