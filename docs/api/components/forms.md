# Form Components

User input components: search boxes, selects, textareas, and pickers.

## SearchBox

Search input with icon.

![SearchBox States](../../../design_system/assets/screenshots/search_box_states.png)

```python
from design_system import SearchBox

search = SearchBox(placeholder="Search files...")

# Signals
search.text_changed.connect(lambda text: print(f"Typing: {text}"))
search.search_submitted.connect(lambda text: print(f"Search: {text}"))

# Methods
text = search.text()
search.setText("query")
search.clear()
```

### SearchBox Signals

| Signal | Description |
|--------|-------------|
| `text_changed(text)` | Emitted as user types |
| `search_submitted(text)` | Emitted on Enter press |

---

## Select

Dropdown selection.

![Select Dropdown](../../../design_system/assets/screenshots/select_dropdown.png)

```python
from design_system import Select

select = Select(placeholder="Choose option...")
select.add_items(["Option 1", "Option 2", "Option 3"])
select.value_changed.connect(lambda value: print(f"Selected: {value}"))
```

### Select Methods

| Method | Description |
|--------|-------------|
| `add_items(items)` | Add list of options |
| `current_value()` | Get selected value |
| `set_value(value)` | Set selected value |
| `clear()` | Clear selection |

### Select Signals

| Signal | Description |
|--------|-------------|
| `value_changed(value)` | Emitted when selection changes |

---

## MultiSelect

Multiple selection dropdown.

```python
from design_system import MultiSelect

multi = MultiSelect()
multi.add_items(["Tag 1", "Tag 2", "Tag 3"])
# User can select multiple items
```

### MultiSelect Methods

| Method | Description |
|--------|-------------|
| `add_items(items)` | Add options |
| `selected_items()` | Get selected values |
| `set_selected(items)` | Set selected values |

---

## Textarea

Multi-line text input.

![Textarea](../../../design_system/assets/screenshots/textarea_with_content.png)

```python
from design_system import Textarea

textarea = Textarea(placeholder="Enter description...")
text = textarea.toPlainText()
textarea.setPlainText("Content here")
```

### Textarea Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `placeholder` | str | `""` | Placeholder text |

---

## NumberInput

Numeric input with spin controls.

```python
from design_system import NumberInput

number = NumberInput(minimum=0, maximum=100, value=50)
```

### NumberInput Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `minimum` | int | `0` | Minimum value |
| `maximum` | int | `100` | Maximum value |
| `value` | int | `0` | Initial value |

---

## RangeSlider

Range selection slider.

```python
from design_system import RangeSlider

slider = RangeSlider(minimum=0, maximum=100)
slider.valueChanged.connect(lambda value: print(f"Value: {value}"))
```

### RangeSlider Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `minimum` | int | `0` | Minimum value |
| `maximum` | int | `100` | Maximum value |

---

## ColorPicker

Color selection widget.

![Color Picker](../../../design_system/assets/screenshots/color_picker.png)

```python
from design_system import ColorPicker

picker = ColorPicker()
picker.color_changed.connect(lambda color: print(f"Color: {color}"))
```

### ColorPicker Signals

| Signal | Description |
|--------|-------------|
| `color_changed(color)` | Emitted when color selected |

---

## FormGroup

Grouped form fields with label.

![Form Groups](../../../design_system/assets/screenshots/form_groups.png)

```python
from design_system import FormGroup, Input

group = FormGroup(label="User Details")
group.add_widget(Input(placeholder="Name"))
group.add_widget(Input(placeholder="Email"))
```

### FormGroup Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `label` | str | `""` | Group label |

---

## CoderSelector

Coder/user selection dropdown.

```python
from design_system import CoderSelector

selector = CoderSelector()
# Populated with available coders
```

---

## Form Example

Complete form with validation:

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout
from design_system import (
    Card, CardHeader, FormGroup, Input, Select,
    Textarea, Button, Label
)

class ContactForm(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        card = Card()
        card.add_widget(CardHeader(title="Contact Form"))

        # Name field
        name_group = FormGroup(label="Name")
        self.name_input = Input(placeholder="Enter your name")
        name_group.add_widget(self.name_input)
        card.add_widget(name_group)

        # Category select
        category_group = FormGroup(label="Category")
        self.category_select = Select(placeholder="Select category")
        self.category_select.add_items(["General", "Support", "Sales"])
        category_group.add_widget(self.category_select)
        card.add_widget(category_group)

        # Message
        message_group = FormGroup(label="Message")
        self.message_input = Textarea(placeholder="Enter your message")
        message_group.add_widget(self.message_input)
        card.add_widget(message_group)

        # Submit button
        submit_btn = Button("Submit", variant="primary")
        submit_btn.clicked.connect(self.submit)
        card.add_widget(submit_btn)

        layout.addWidget(card)

    def submit(self):
        name = self.name_input.text()
        category = self.category_select.current_value()
        message = self.message_input.toPlainText()

        if not name:
            self.name_input.set_error(True)
            return

        print(f"Submitted: {name}, {category}, {message}")
```
