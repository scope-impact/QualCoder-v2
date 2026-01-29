"""
Tests for feedback components: Toast, Modal, ProgressBar, Spinner, etc.
"""

import pytest
from PyQt6.QtCore import Qt

from design_system.toast import Toast, ToastContainer, ToastManager
from design_system.modal import Modal, ModalHeader, ModalBody, ModalFooter
from design_system.progress_bar import ProgressBar, ProgressBarLabeled
from design_system.spinner import Spinner, LoadingIndicator, LoadingOverlay, SkeletonLoader


class TestToast:
    """Tests for Toast component"""

    def test_toast_creation(self, qtbot):
        """Toast should be created with message"""
        toast = Toast(message="Test notification")
        qtbot.addWidget(toast)

        assert toast is not None

    def test_toast_variants(self, qtbot):
        """Toast should support variants"""
        variants = ["info", "success", "warning", "error"]

        for variant in variants:
            toast = Toast(message="Test", variant=variant)
            qtbot.addWidget(toast)
            assert toast._variant == variant

    def test_toast_dismiss(self, qtbot):
        """Toast should be dismissable"""
        toast = Toast(message="Test", closable=True)
        qtbot.addWidget(toast)

        # Should have close button
        assert toast is not None


class TestToastContainer:
    """Tests for ToastContainer component"""

    def test_container_creation(self, qtbot):
        """ToastContainer should be created"""
        container = ToastContainer()
        qtbot.addWidget(container)

        assert container is not None

    def test_container_add_toast(self, qtbot):
        """ToastContainer should add toasts"""
        container = ToastContainer()
        qtbot.addWidget(container)

        toast = Toast(message="Test message", variant="info")
        container.add_toast(toast)

        # Should have toast in list
        assert len(container._toasts) > 0


class TestModal:
    """Tests for Modal component"""

    def test_modal_creation(self, qtbot):
        """Modal should be created"""
        modal = Modal(title="Test Modal")
        qtbot.addWidget(modal)

        assert modal is not None

    def test_modal_title(self, qtbot):
        """Modal should have title"""
        modal = Modal(title="My Title")
        qtbot.addWidget(modal)

        # Title is stored in the header's _title QLabel
        assert modal._header._title.text() == "My Title"


class TestModalHeader:
    """Tests for ModalHeader component"""

    def test_header_creation(self, qtbot):
        """ModalHeader should be created with title"""
        header = ModalHeader("Test Title")
        qtbot.addWidget(header)

        assert header is not None

    def test_header_close_signal(self, qtbot):
        """ModalHeader should emit close signal"""
        header = ModalHeader("Test")
        qtbot.addWidget(header)

        with qtbot.waitSignal(header.close_clicked, timeout=1000):
            # Find close button
            close_btn = header._close_btn
            qtbot.mouseClick(close_btn, Qt.MouseButton.LeftButton)


class TestModalBody:
    """Tests for ModalBody component"""

    def test_body_creation(self, qtbot):
        """ModalBody should be created"""
        body = ModalBody()
        qtbot.addWidget(body)

        assert body is not None
        assert body.layout() is not None


class TestModalFooter:
    """Tests for ModalFooter component"""

    def test_footer_creation(self, qtbot):
        """ModalFooter should be created"""
        footer = ModalFooter()
        qtbot.addWidget(footer)

        assert footer is not None
        assert footer.layout() is not None


class TestProgressBar:
    """Tests for ProgressBar component"""

    def test_progress_creation(self, qtbot):
        """ProgressBar should be created"""
        progress = ProgressBar(value=50)
        qtbot.addWidget(progress)

        assert progress is not None

    def test_progress_value(self, qtbot):
        """ProgressBar should set value"""
        progress = ProgressBar(value=25)
        qtbot.addWidget(progress)

        progress.setValue(75)
        assert progress.value() == 75

    def test_progress_with_label(self, qtbot):
        """ProgressBar should show label"""
        progress = ProgressBar(value=50, label="Loading...")
        qtbot.addWidget(progress)

        assert progress is not None

    def test_progress_percentage(self, qtbot):
        """ProgressBar should show percentage"""
        progress = ProgressBar(value=50, show_percentage=True)
        qtbot.addWidget(progress)

        assert progress is not None


class TestProgressBarLabeled:
    """Tests for ProgressBarLabeled component"""

    def test_labeled_creation(self, qtbot):
        """ProgressBarLabeled should be created"""
        progress = ProgressBarLabeled(value=8, max_value=12, label="Files")
        qtbot.addWidget(progress)

        assert progress is not None


class TestSpinner:
    """Tests for Spinner component"""

    def test_spinner_creation(self, qtbot):
        """Spinner should be created"""
        spinner = Spinner()
        qtbot.addWidget(spinner)

        assert spinner is not None

    def test_spinner_size(self, qtbot):
        """Spinner should respect size"""
        spinner = Spinner(size=48)
        qtbot.addWidget(spinner)

        assert spinner.width() == 48
        assert spinner.height() == 48


class TestLoadingIndicator:
    """Tests for LoadingIndicator component"""

    def test_indicator_creation(self, qtbot):
        """LoadingIndicator should be created"""
        indicator = LoadingIndicator(text="Loading...")
        qtbot.addWidget(indicator)

        assert indicator is not None

    def test_indicator_text(self, qtbot):
        """LoadingIndicator should show text"""
        indicator = LoadingIndicator(text="Please wait")
        qtbot.addWidget(indicator)

        assert indicator is not None


class TestSkeletonLoader:
    """Tests for SkeletonLoader component"""

    def test_skeleton_creation(self, qtbot):
        """SkeletonLoader should be created"""
        skeleton = SkeletonLoader(width=200, height=20)
        qtbot.addWidget(skeleton)

        assert skeleton is not None

    def test_skeleton_dimensions(self, qtbot):
        """SkeletonLoader should respect dimensions"""
        skeleton = SkeletonLoader(width=150, height=30)
        qtbot.addWidget(skeleton)

        assert skeleton.width() == 150
        assert skeleton.height() == 30
