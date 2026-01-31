"""
TDD Tests for Signal Routing Completion (QC-007.05)

Tests that all orphaned signals are properly connected:
- CodesPanel.navigation_clicked
- TextEditorPanel.code_applied
- DetailsPanel.ai_chat_clicked
- DetailsPanel.ai_suggest_clicked
- CodingToolbar.media_type_changed
- CodingToolbar.search_changed
"""

from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from design_system import get_colors
from src.presentation.pages.text_coding_page import TextCodingPage
from src.presentation.screens.text_coding import TextCodingScreen

_colors = get_colors()


class TestCodesNavigationClicked:
    """CodesPanel.navigation_clicked should be routed to page/screen."""

    def test_page_has_navigation_clicked_signal(self, qtbot):
        """TextCodingPage should expose navigation_clicked signal."""
        page = TextCodingPage(colors=_colors)
        qtbot.addWidget(page)

        assert hasattr(page, "navigation_clicked")

    def test_codes_panel_navigation_routes_to_page(self, qtbot):
        """navigation_clicked from CodesPanel should emit on page."""
        page = TextCodingPage(colors=_colors)
        qtbot.addWidget(page)

        spy = QSignalSpy(page.navigation_clicked)
        page.codes_panel.navigation_clicked.emit("prev")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "prev"

    def test_screen_has_navigation_clicked_signal(self, qtbot):
        """TextCodingScreen should expose navigation_clicked signal."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        assert hasattr(screen, "navigation_clicked")

    def test_page_navigation_routes_to_screen(self, qtbot):
        """navigation_clicked from page should emit on screen."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        spy = QSignalSpy(screen.navigation_clicked)
        screen.page.codes_panel.navigation_clicked.emit("next")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "next"


class TestEditorCodeApplied:
    """TextEditorPanel.code_applied should be routed to page/screen."""

    def test_page_has_editor_code_applied_signal(self, qtbot):
        """TextCodingPage should expose editor_code_applied signal."""
        page = TextCodingPage(colors=_colors)
        qtbot.addWidget(page)

        assert hasattr(page, "editor_code_applied")

    def test_editor_code_applied_routes_to_page(self, qtbot):
        """code_applied from TextEditorPanel should emit on page."""
        page = TextCodingPage(colors=_colors)
        qtbot.addWidget(page)

        spy = QSignalSpy(page.editor_code_applied)
        page.editor_panel.code_applied.emit("code1", 0, 10)
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "code1"
        assert spy.at(0)[1] == 0
        assert spy.at(0)[2] == 10

    def test_editor_code_applied_routes_to_screen(self, qtbot):
        """code_applied from editor should emit on screen via page."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        spy = QSignalSpy(screen.editor_code_applied)
        screen.page.editor_panel.code_applied.emit("code2", 5, 15)
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "code2"


class TestAIChatClicked:
    """DetailsPanel.ai_chat_clicked should be routed to page/screen."""

    def test_page_has_ai_chat_clicked_signal(self, qtbot):
        """TextCodingPage should expose ai_chat_clicked signal."""
        page = TextCodingPage(colors=_colors)
        qtbot.addWidget(page)

        assert hasattr(page, "ai_chat_clicked")

    def test_details_ai_chat_routes_to_page(self, qtbot):
        """ai_chat_clicked from DetailsPanel should emit on page."""
        page = TextCodingPage(colors=_colors)
        qtbot.addWidget(page)

        spy = QSignalSpy(page.ai_chat_clicked)
        page.details_panel.ai_chat_clicked.emit()
        QApplication.processEvents()

        assert spy.count() == 1

    def test_screen_has_ai_chat_clicked_signal(self, qtbot):
        """TextCodingScreen should expose ai_chat_clicked signal."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        assert hasattr(screen, "ai_chat_clicked")

    def test_ai_chat_routes_to_screen(self, qtbot):
        """ai_chat_clicked should emit on screen."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        spy = QSignalSpy(screen.ai_chat_clicked)
        screen.page.details_panel.ai_chat_clicked.emit()
        QApplication.processEvents()

        assert spy.count() == 1


class TestAISuggestClicked:
    """DetailsPanel.ai_suggest_clicked should be routed to page/screen."""

    def test_page_has_ai_suggest_clicked_signal(self, qtbot):
        """TextCodingPage should expose ai_suggest_clicked signal."""
        page = TextCodingPage(colors=_colors)
        qtbot.addWidget(page)

        assert hasattr(page, "ai_suggest_clicked")

    def test_details_ai_suggest_routes_to_page(self, qtbot):
        """ai_suggest_clicked from DetailsPanel should emit on page."""
        page = TextCodingPage(colors=_colors)
        qtbot.addWidget(page)

        spy = QSignalSpy(page.ai_suggest_clicked)
        page.details_panel.ai_suggest_clicked.emit()
        QApplication.processEvents()

        assert spy.count() == 1

    def test_screen_has_ai_suggest_clicked_signal(self, qtbot):
        """TextCodingScreen should expose ai_suggest_clicked signal."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        assert hasattr(screen, "ai_suggest_clicked")

    def test_ai_suggest_routes_to_screen(self, qtbot):
        """ai_suggest_clicked should emit on screen."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        spy = QSignalSpy(screen.ai_suggest_clicked)
        screen.page.details_panel.ai_suggest_clicked.emit()
        QApplication.processEvents()

        assert spy.count() == 1


class TestMediaTypeChanged:
    """CodingToolbar.media_type_changed should be routed to page/screen."""

    def test_page_has_media_type_changed_signal(self, qtbot):
        """TextCodingPage should expose media_type_changed signal."""
        page = TextCodingPage(colors=_colors)
        qtbot.addWidget(page)

        assert hasattr(page, "media_type_changed")

    def test_toolbar_media_type_routes_to_page(self, qtbot):
        """media_type_changed from CodingToolbar should emit on page."""
        page = TextCodingPage(colors=_colors)
        qtbot.addWidget(page)

        spy = QSignalSpy(page.media_type_changed)
        page.toolbar.media_type_changed.emit("image")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "image"

    def test_screen_has_media_type_changed_signal(self, qtbot):
        """TextCodingScreen should expose media_type_changed signal."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        assert hasattr(screen, "media_type_changed")

    def test_media_type_routes_to_screen(self, qtbot):
        """media_type_changed should emit on screen."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        spy = QSignalSpy(screen.media_type_changed)
        screen.page.toolbar.media_type_changed.emit("pdf")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "pdf"


class TestSearchChanged:
    """CodingToolbar.search_changed should be routed to page/screen."""

    def test_page_has_search_changed_signal(self, qtbot):
        """TextCodingPage should expose search_changed signal."""
        page = TextCodingPage(colors=_colors)
        qtbot.addWidget(page)

        assert hasattr(page, "search_changed")

    def test_toolbar_search_routes_to_page(self, qtbot):
        """search_changed from CodingToolbar should emit on page."""
        page = TextCodingPage(colors=_colors)
        qtbot.addWidget(page)

        spy = QSignalSpy(page.search_changed)
        page.toolbar.search_changed.emit("test query")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "test query"

    def test_screen_has_search_changed_signal(self, qtbot):
        """TextCodingScreen should expose search_changed signal."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        assert hasattr(screen, "search_changed")

    def test_search_routes_to_screen(self, qtbot):
        """search_changed should emit on screen."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        spy = QSignalSpy(screen.search_changed)
        screen.page.toolbar.search_changed.emit("find me")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "find me"


class TestIntegration:
    """Integration tests for complete signal routing."""

    def test_all_signals_accessible_from_screen(self, qtbot):
        """All signals should be accessible from screen for controller binding."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        # File and code signals (already existed)
        assert hasattr(screen, "file_selected")
        assert hasattr(screen, "code_selected")
        assert hasattr(screen, "text_selected")

        # New routed signals
        assert hasattr(screen, "navigation_clicked")
        assert hasattr(screen, "editor_code_applied")
        assert hasattr(screen, "ai_chat_clicked")
        assert hasattr(screen, "ai_suggest_clicked")
        assert hasattr(screen, "media_type_changed")
        assert hasattr(screen, "search_changed")

    def test_signal_chain_codes_to_screen(self, qtbot):
        """Signal should flow: CodesPanel → Page → Screen."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        spy = QSignalSpy(screen.navigation_clicked)

        # Emit at organism level
        screen.page.codes_panel.navigation_clicked.emit("prev")
        QApplication.processEvents()

        # Should arrive at screen level
        assert spy.count() == 1

    def test_signal_chain_toolbar_to_screen(self, qtbot):
        """Signal should flow: Toolbar → Page → Screen."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        media_spy = QSignalSpy(screen.media_type_changed)
        search_spy = QSignalSpy(screen.search_changed)

        # Emit at organism level
        screen.page.toolbar.media_type_changed.emit("av")
        screen.page.toolbar.search_changed.emit("query")
        QApplication.processEvents()

        # Should arrive at screen level
        assert media_spy.count() == 1
        assert search_spy.count() == 1
