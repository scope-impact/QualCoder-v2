"""
Thread Utilities for Signal Bridge.

Provides thread detection and safe cross-thread invocation helpers
for Qt signal emission.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

# Qt imports with fallback for testing without Qt
try:
    from PySide6.QtCore import QCoreApplication, QThread
    from PySide6.QtWidgets import QApplication

    HAS_QT = True
except ImportError:
    HAS_QT = False
    QThread = None  # type: ignore
    QCoreApplication = None  # type: ignore
    QApplication = None  # type: ignore


def is_main_thread() -> bool:
    """
    Check if the current thread is the main/UI thread.

    In a PySide6 application, this checks if we're on the Qt main thread.
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
    # First try Python thread name (works for both Python threads and QThreads)
    python_name = threading.current_thread().name

    # If it's not the MainThread and has a custom name, use that
    if python_name != "MainThread":
        return python_name

    # For the main thread, try to get Qt's name if available
    if HAS_QT and QThread.currentThread() is not None:
        qt_thread = QThread.currentThread()
        if qt_thread is not None:
            qt_name = qt_thread.objectName()
            if qt_name:
                return qt_name

    return python_name


def warn_if_not_main_thread(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that warns if a function is called from a non-main thread.

    This decorator does NOT dispatch to the main thread - it only emits
    a warning. For actual thread-safe signal emission, use
    BaseSignalBridge._emit_threadsafe().

    Use this decorator to flag functions that should ideally be called
    from the main thread, helping identify threading issues during development.

    Args:
        func: The function to wrap

    Returns:
        Wrapped function that warns on non-main-thread calls
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if is_main_thread():
            return func(*args, **kwargs)

        import warnings

        if HAS_QT and QCoreApplication.instance() is not None:
            warnings.warn(
                f"Cross-thread call to {func.__name__} - "
                "use BaseSignalBridge._emit_threadsafe for signals",
                stacklevel=2,
            )
        else:
            warnings.warn(
                f"No Qt event loop - executing {func.__name__} synchronously",
                stacklevel=2,
            )
        return func(*args, **kwargs)

    return wrapper


# Keep old name as alias for backwards compatibility
ensure_main_thread = warn_if_not_main_thread


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
