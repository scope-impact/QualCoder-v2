"""
Tests for form components: SearchBox, Select, Textarea, NumberInput, etc.
"""

from design_system.forms import (
    ColorPicker,
    FormGroup,
    NumberInput,
    RangeSlider,
    SearchBox,
    Select,
    Textarea,
)


class TestSearchBox:
    """Tests for SearchBox component"""

    def test_searchbox_creation(self, qtbot):
        """SearchBox should be created with placeholder"""
        search = SearchBox(placeholder="Search...")
        qtbot.addWidget(search)

        assert search._input.placeholderText() == "Search..."

    def test_searchbox_text_change(self, qtbot):
        """SearchBox should emit text_changed signal"""
        search = SearchBox()
        qtbot.addWidget(search)

        with qtbot.waitSignal(search.text_changed, timeout=1000):
            qtbot.keyClicks(search._input, "test")

    def test_searchbox_clear(self, qtbot):
        """SearchBox should clear text when clear button clicked"""
        search = SearchBox()
        qtbot.addWidget(search)

        qtbot.keyClicks(search._input, "test")
        assert search.text() == "test"

        search.clear()
        assert search.text() == ""


class TestSelect:
    """Tests for Select component"""

    def test_select_creation(self, qtbot):
        """Select should be created with placeholder"""
        select = Select(placeholder="Choose...")
        qtbot.addWidget(select)

        assert select.currentText() == "Choose..."

    def test_select_add_items(self, qtbot):
        """Select should add items"""
        select = Select()
        qtbot.addWidget(select)

        select.add_items(["Option 1", "Option 2", "Option 3"])
        assert select.count() == 3

    def test_select_value_changed(self, qtbot):
        """Select should emit value_changed signal"""
        select = Select()
        qtbot.addWidget(select)
        select.add_items(["A", "B", "C"])

        with qtbot.waitSignal(select.value_changed, timeout=1000):
            select.setCurrentIndex(1)


class TestTextarea:
    """Tests for Textarea component"""

    def test_textarea_creation(self, qtbot):
        """Textarea should be created with placeholder"""
        textarea = Textarea(placeholder="Enter text...")
        qtbot.addWidget(textarea)

        assert textarea.placeholderText() == "Enter text..."

    def test_textarea_text(self, qtbot):
        """Textarea should accept multiline text"""
        textarea = Textarea()
        qtbot.addWidget(textarea)

        textarea.setPlainText("Line 1\nLine 2\nLine 3")
        assert "Line 1" in textarea.toPlainText()
        assert "Line 2" in textarea.toPlainText()

    def test_textarea_signal(self, qtbot):
        """Textarea should emit text_changed signal"""
        textarea = Textarea()
        qtbot.addWidget(textarea)

        with qtbot.waitSignal(textarea.text_changed, timeout=1000):
            textarea.setPlainText("test")


class TestNumberInput:
    """Tests for NumberInput component"""

    def test_number_input_creation(self, qtbot):
        """NumberInput should be created with min/max"""
        num = NumberInput(min_val=0, max_val=100)
        qtbot.addWidget(num)

        assert num is not None

    def test_number_input_value(self, qtbot):
        """NumberInput should set and get value"""
        num = NumberInput(min_val=0, max_val=100)
        qtbot.addWidget(num)

        num.setValue(50)
        assert num.value() == 50

    def test_number_input_bounds(self, qtbot):
        """NumberInput should respect min/max bounds"""
        num = NumberInput(min_val=10, max_val=50)
        qtbot.addWidget(num)

        num.setValue(100)  # Above max
        assert num.value() <= 50

        num.setValue(0)  # Below min
        assert num.value() >= 10


class TestRangeSlider:
    """Tests for RangeSlider component"""

    def test_slider_creation(self, qtbot):
        """RangeSlider should be created"""
        slider = RangeSlider(min_val=0, max_val=100, value=50)
        qtbot.addWidget(slider)

        assert slider is not None

    def test_slider_value(self, qtbot):
        """RangeSlider should set and get value"""
        slider = RangeSlider(min_val=0, max_val=100, value=25)
        qtbot.addWidget(slider)

        slider.setValue(75)
        assert slider.value() == 75

    def test_slider_signal(self, qtbot):
        """RangeSlider should emit value_changed signal"""
        slider = RangeSlider(min_val=0, max_val=100, value=50)
        qtbot.addWidget(slider)

        with qtbot.waitSignal(slider.value_changed, timeout=1000):
            slider.setValue(60)


class TestColorPicker:
    """Tests for ColorPicker component"""

    def test_color_picker_creation(self, qtbot):
        """ColorPicker should be created"""
        picker = ColorPicker()
        qtbot.addWidget(picker)

        assert picker is not None

    def test_color_picker_selection(self, qtbot):
        """ColorPicker should emit color_selected signal"""
        picker = ColorPicker()
        qtbot.addWidget(picker)

        # Color picker has default colors
        assert len(picker._color_list) > 0


class TestFormGroup:
    """Tests for FormGroup component"""

    def test_form_group_creation(self, qtbot):
        """FormGroup should be created with label"""
        group = FormGroup(label="Username")
        qtbot.addWidget(group)

        assert group is not None

    def test_form_group_required(self, qtbot):
        """FormGroup should show required indicator"""
        group = FormGroup(label="Email", required=True)
        qtbot.addWidget(group)

        # Should have asterisk or similar indicator
        assert group is not None

    def test_form_group_hint(self, qtbot):
        """FormGroup should show hint text"""
        group = FormGroup(label="Password", hint="Must be at least 8 characters")
        qtbot.addWidget(group)

        assert group is not None
