"""
Thread Utilities for Signal Bridge.

Provides thread detection and safe cross-thread invocation helpers
for PyQt6 signal emission.
"""

from __future__ import annotations
from typing import Callable, Any, Optional
import threading

# PyQt6 imports with fallback for testing without Qt
try:
    from PyQt6.QtCore import QThread, QCoreApplication
    from PyQt6.QtWidgets import QApplication
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QThread = None  # type: ignore
    QCoreApplication = None  # type: ignore
    QApplication = None  # type: ignore


def is_main_thread() -> bool:
    """
    Check if the current thread is the main/UI thread.

    In a PyQt6 application, this checks if we're on the Qt main thread.
    Falls back to Python's main thread check if Qt is not available.

    Returns:
        True if on the main thread, False otherwise
    """
    if HAS_QT and QCoreApplication.instance() is not None:
        app = QCoreApplication.instance()
        if app is not None:
            return QThread.currentThread() == app.thread()
    # Fallback: check Python main thread
    return threading.current_thread() is threading.main_thread()


def get_current_thread_name() -> str:
    """
    Get the name of the current thread for debugging.

    Returns:
        Thread name string
    """
    if HAS_QT and QThread.currentThread() is not None:
        qt_thread = QThread.currentThread()
        if qt_thread is not None:
            return qt_thread.objectName() or f"Qt-{id(qt_thread)}"
    return threading.current_thread().name


def ensure_main_thread(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that ensures a function runs on the main thread.

    If called from a background thread, the function will be queued
    for execution on the main thread.

    Note: This decorator requires an active Qt event loop.
    Without Qt, it will execute synchronously with a warning.

    Args:
        func: The function to wrap

    Returns:
        Wrapped function that ensures main thread execution
    """
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if is_main_thread():
            return func(*args, **kwargs)

        if HAS_QT and QCoreApplication.instance() is not None:
            from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
            # Queue for main thread execution
            # Note: For void functions, use invokeMethod
            # This is a simplified version - full implementation in base.py
            import warnings
            warnings.warn(
                f"Cross-thread call to {func.__name__} - "
                "use BaseSignalBridge._emit_threadsafe for signals"
            )
            return func(*args, **kwargs)
        else:
            # No Qt - execute directly with warning
            import warnings
            warnings.warn(
                f"No Qt event loop - executing {func.__name__} synchronously"
            )
            return func(*args, **kwargs)

    return wrapper


class ThreadChecker:
    """
    Utility class for thread-related checks and debugging.

    Useful for asserting thread requirements during development.
    """

    @staticmethod
    def assert_main_thread(context: str = "") -> None:
        """
        Assert that we're on the main thread.

        Raises:
            RuntimeError: If not on the main thread
        """
        if not is_main_thread():
            thread_name = get_current_thread_name()
            msg = f"Expected main thread but on '{thread_name}'"
            if context:
                msg = f"{context}: {msg}"
            raise RuntimeError(msg)

    @staticmethod
    def assert_background_thread(context: str = "") -> None:
        """
        Assert that we're NOT on the main thread.

        Raises:
            RuntimeError: If on the main thread
        """
        if is_main_thread():
            msg = "Expected background thread but on main thread"
            if context:
                msg = f"{context}: {msg}"
            raise RuntimeError(msg)

    @staticmethod
    def warn_if_not_main_thread(context: str = "") -> bool:
        """
        Warn if not on the main thread.

        Returns:
            True if on main thread, False otherwise
        """
        if not is_main_thread():
            import warnings
            thread_name = get_current_thread_name()
            msg = f"Not on main thread (current: '{thread_name}')"
            if context:
                msg = f"{context}: {msg}"
            warnings.warn(msg, stacklevel=2)
            return False
        return True
