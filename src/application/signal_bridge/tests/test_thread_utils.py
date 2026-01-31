"""Tests for thread utilities."""

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from src.application.signal_bridge.thread_utils import (
    ThreadChecker,
    get_current_thread_name,
    is_main_thread,
)


class TestIsMainThread:
    """Tests for is_main_thread function."""

    def test_main_thread_detection(self) -> None:
        """Test that main thread is correctly detected."""
        # We should be on main thread during test execution
        assert is_main_thread() is True

    def test_background_thread_detection(self) -> None:
        """Test that background threads are correctly detected."""
        result = []

        def check_in_thread() -> None:
            result.append(is_main_thread())

        thread = threading.Thread(target=check_in_thread)
        thread.start()
        thread.join()

        assert result[0] is False

    def test_thread_pool_detection(self) -> None:
        """Test detection in thread pool executor."""
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(is_main_thread)
            assert future.result() is False


class TestGetCurrentThreadName:
    """Tests for get_current_thread_name function."""

    def test_main_thread_name(self) -> None:
        """Test getting main thread name."""
        name = get_current_thread_name()
        assert name is not None
        assert isinstance(name, str)
        assert len(name) > 0

    def test_named_thread(self) -> None:
        """Test getting name of a named thread."""
        result = []

        def get_name_in_thread() -> None:
            result.append(get_current_thread_name())

        thread = threading.Thread(target=get_name_in_thread, name="TestThread")
        thread.start()
        thread.join()

        assert "TestThread" in result[0]


class TestThreadChecker:
    """Tests for ThreadChecker utility class."""

    def test_assert_main_thread_passes_on_main(self) -> None:
        """Test assert_main_thread passes on main thread."""
        # Should not raise
        ThreadChecker.assert_main_thread()

    def test_assert_main_thread_fails_on_background(self) -> None:
        """Test assert_main_thread fails on background thread."""
        exception_raised = []

        def check_in_thread() -> None:
            try:
                ThreadChecker.assert_main_thread()
                exception_raised.append(False)
            except RuntimeError:
                exception_raised.append(True)

        thread = threading.Thread(target=check_in_thread)
        thread.start()
        thread.join()

        assert exception_raised[0] is True

    def test_assert_main_thread_with_context(self) -> None:
        """Test assert_main_thread includes context in error."""
        exception_message = []

        def check_in_thread() -> None:
            try:
                ThreadChecker.assert_main_thread("UI operation")
            except RuntimeError as e:
                exception_message.append(str(e))

        thread = threading.Thread(target=check_in_thread)
        thread.start()
        thread.join()

        assert "UI operation" in exception_message[0]

    def test_assert_background_thread_fails_on_main(self) -> None:
        """Test assert_background_thread fails on main thread."""
        with pytest.raises(RuntimeError, match="Expected background thread"):
            ThreadChecker.assert_background_thread()

    def test_assert_background_thread_passes_on_background(self) -> None:
        """Test assert_background_thread passes on background thread."""
        exception_raised = []

        def check_in_thread() -> None:
            try:
                ThreadChecker.assert_background_thread()
                exception_raised.append(False)
            except RuntimeError:
                exception_raised.append(True)

        thread = threading.Thread(target=check_in_thread)
        thread.start()
        thread.join()

        assert exception_raised[0] is False

    def test_warn_if_not_main_thread_returns_true_on_main(self) -> None:
        """Test warn_if_not_main_thread returns True on main."""
        result = ThreadChecker.warn_if_not_main_thread()
        assert result is True

    def test_warn_if_not_main_thread_returns_false_on_background(self) -> None:
        """Test warn_if_not_main_thread returns False on background."""
        result = []

        def check_in_thread() -> None:
            with pytest.warns(UserWarning):
                result.append(ThreadChecker.warn_if_not_main_thread("test"))

        thread = threading.Thread(target=check_in_thread)
        thread.start()
        thread.join()

        assert result[0] is False
