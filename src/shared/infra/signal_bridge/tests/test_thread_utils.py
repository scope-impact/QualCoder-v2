"""Tests for thread utilities."""

import threading
from concurrent.futures import ThreadPoolExecutor

import allure
import pytest

from src.shared.infra.signal_bridge.thread_utils import (
    ThreadChecker,
    get_current_thread_name,
    is_main_thread,
)


@allure.epic("QualCoder v2")
@allure.feature("Shared Infrastructure")
@allure.story("QC-000.08 Signal Bridge")
class TestIsMainThread:
    """Tests for is_main_thread and get_current_thread_name."""

    @allure.title("Detects main/background/pool threads and returns thread names")
    def test_thread_detection_and_names(self) -> None:
        assert is_main_thread() is True

        result: list[bool] = []

        def check_in_thread() -> None:
            result.append(is_main_thread())

        thread = threading.Thread(target=check_in_thread)
        thread.start()
        thread.join()
        assert result[0] is False

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(is_main_thread)
            assert future.result() is False

        # Named thread returns name
        name_result: list[str] = []

        def get_name_in_thread() -> None:
            name_result.append(get_current_thread_name())

        thread = threading.Thread(target=get_name_in_thread, name="TestThread")
        thread.start()
        thread.join()
        assert "TestThread" in name_result[0]

        # Main thread also returns a non-empty string
        assert len(get_current_thread_name()) > 0


@allure.epic("QualCoder v2")
@allure.feature("Shared Infrastructure")
@allure.story("QC-000.08 Signal Bridge")
class TestThreadChecker:
    """Tests for ThreadChecker utility class."""

    @allure.title(
        "assert_main_thread passes on main, fails on background; assert_background_thread inverse"
    )
    def test_assert_main_and_background_thread(self) -> None:
        # Should not raise on main thread
        ThreadChecker.assert_main_thread()

        exception_message: list[str] = []

        def check_in_thread() -> None:
            try:
                ThreadChecker.assert_main_thread("UI operation")
                exception_message.append("")
            except RuntimeError as e:
                exception_message.append(str(e))

        thread = threading.Thread(target=check_in_thread)
        thread.start()
        thread.join()
        assert "UI operation" in exception_message[0]

        # assert_background_thread fails on main
        with pytest.raises(RuntimeError, match="Expected background thread"):
            ThreadChecker.assert_background_thread()

        # assert_background_thread passes on background
        exception_raised: list[bool] = []

        def check_bg_in_thread() -> None:
            try:
                ThreadChecker.assert_background_thread()
                exception_raised.append(False)
            except RuntimeError:
                exception_raised.append(True)

        thread = threading.Thread(target=check_bg_in_thread)
        thread.start()
        thread.join()
        assert exception_raised[0] is False

    @allure.title("warn_if_not_main_thread returns True on main, False on background")
    def test_warn_if_not_main_thread(self) -> None:
        assert ThreadChecker.warn_if_not_main_thread() is True

        result: list[bool] = []

        def check_in_thread() -> None:
            with pytest.warns(UserWarning):
                result.append(ThreadChecker.warn_if_not_main_thread("test"))

        thread = threading.Thread(target=check_in_thread)
        thread.start()
        thread.join()

        assert result[0] is False
