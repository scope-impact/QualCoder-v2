"""
Tests for the Icon component (using qtawesome)
"""

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


class TestIcon:
    """Tests for Icon component"""

    def test_icon_creation(self, qapp, dark_theme):
        """Icon should create without errors"""
        from design_system import Icon

        icon = Icon("mdi6.code-tags", colors=dark_theme)
        assert icon is not None

    def test_icon_with_size(self, qapp, dark_theme):
        """Icon should accept custom size"""
        from design_system import Icon

        icon = Icon("mdi6.folder", size=24, colors=dark_theme)
        # Size is icon size + 4 padding
        assert icon.width() == 28
        assert icon.height() == 28

    def test_icon_with_color(self, qapp, dark_theme):
        """Icon should accept custom color"""
        from design_system import Icon

        icon = Icon("mdi6.cog", color="#FF0000", colors=dark_theme)
        assert icon._color == "#FF0000"

    def test_icon_set_color(self, qapp, dark_theme):
        """Icon should update color"""
        from design_system import Icon

        icon = Icon("mdi6.code-tags", colors=dark_theme)
        icon.set_color("#00FF00")
        assert icon._color == "#00FF00"

    def test_icon_common_icons(self, qapp, dark_theme):
        """Common icons should render without error"""
        from design_system import Icon

        # Test common icons
        common_icons = [
            "mdi6.code-tags",
            "mdi6.folder",
            "mdi6.cog",
            "mdi6.magnify",
            "mdi6.plus",
            "mdi6.close",
            "mdi6.check",
        ]
        for name in common_icons:
            icon = Icon(name, colors=dark_theme)
            assert icon is not None
            assert icon.name == name

    def test_icon_unknown_fallback(self, qapp, dark_theme):
        """Icon should handle unknown icon names gracefully"""
        from design_system import Icon

        # Unknown icon should still create (with text fallback)
        icon = Icon("mdi6.nonexistent-icon-xyz", colors=dark_theme)
        assert icon is not None


class TestIconText:
    """Tests for IconText component"""

    def test_icon_text_creation(self, qapp, dark_theme):
        """IconText should create without errors"""
        from design_system import IconText

        widget = IconText("mdi6.folder", "Documents", colors=dark_theme)
        assert widget is not None

    def test_icon_text_set_color(self, qapp, dark_theme):
        """IconText should update color"""
        from design_system import IconText

        widget = IconText("mdi6.folder", "Documents", colors=dark_theme)
        widget.set_color("#FF0000")
        assert widget._color == "#FF0000"

    def test_icon_text_set_text(self, qapp, dark_theme):
        """IconText should update text"""
        from design_system import IconText

        widget = IconText("mdi6.folder", "Documents", colors=dark_theme)
        widget.set_text("New Folder")
        assert widget._label.text() == "New Folder"


class TestIconFunction:
    """Tests for icon() convenience function"""

    def test_icon_function(self, qapp, dark_theme):
        """icon() function should create Icon"""
        from design_system import icon

        i = icon("mdi6.code-tags", colors=dark_theme)
        assert i is not None
        assert i._name == "mdi6.code-tags"

    def test_icon_function_with_params(self, qapp, dark_theme):
        """icon() function should accept parameters"""
        from design_system import icon

        i = icon("mdi6.folder", size=32, color="#123456", colors=dark_theme)
        assert i._size == 32
        assert i._color == "#123456"


class TestHelperFunctions:
    """Tests for get_pixmap and get_qicon helpers"""

    def test_get_pixmap(self, qapp, dark_theme):
        """get_pixmap should return a QPixmap"""
        from design_system import get_pixmap
        from PyQt6.QtGui import QPixmap

        pixmap = get_pixmap("mdi6.folder", size=24, colors=dark_theme)
        assert isinstance(pixmap, QPixmap)
        assert not pixmap.isNull()

    def test_get_qicon(self, qapp, dark_theme):
        """get_qicon should return a QIcon"""
        from design_system import get_qicon
        from PyQt6.QtGui import QIcon

        qicon = get_qicon("mdi6.folder", colors=dark_theme)
        assert isinstance(qicon, QIcon)
        assert not qicon.isNull()
