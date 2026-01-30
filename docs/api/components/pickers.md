# Picker Components

Selection widgets for types, colors, and options.

## TypeSelector / TypeOptionCard

Type selection with visual cards.

```python
from design_system import TypeSelector, TypeOptionCard

selector = TypeSelector()
selector.add_type(TypeOptionCard(
    type_id="text",
    title="Text Document",
    description="Import text files",
    icon="mdi6.file-document"
))
selector.add_type(TypeOptionCard(
    type_id="audio",
    title="Audio File",
    description="Import audio recordings",
    icon="mdi6.microphone"
))

selector.type_selected.connect(lambda type_id: handle_selection(type_id))
```

### TypeOptionCard Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `type_id` | str | required | Unique identifier |
| `title` | str | required | Card title |
| `description` | str | `""` | Card description |
| `icon` | str | `None` | Icon name |

### TypeSelector Signals

| Signal | Description |
|--------|-------------|
| `type_selected(type_id)` | Type selected |

---

## ColorSchemeSelector

Color scheme picker for visualizations.

```python
from design_system import ColorSchemeSelector, ColorSchemeOption

selector = ColorSchemeSelector()
selector.add_scheme(ColorSchemeOption(
    name="primary",
    colors=["#3B82F6", "#60A5FA", "#93C5FD"]
))
selector.add_scheme(ColorSchemeOption(
    name="success",
    colors=["#22C55E", "#4ADE80", "#86EFAC"]
))

selector.scheme_selected.connect(lambda name: apply_scheme(name))
```

### ColorSchemeOption Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | str | Scheme identifier |
| `colors` | list | List of hex colors |

### ColorSchemeSelector Signals

| Signal | Description |
|--------|-------------|
| `scheme_selected(name)` | Scheme selected |

---

## ChartTypeSelector

Chart type picker for data visualization.

```python
from design_system import ChartTypeSelector

selector = ChartTypeSelector()
# Includes options: bar, line, pie, scatter

selector.type_selected.connect(lambda chart_type: update_chart(chart_type))
```

### ChartTypeSelector Signals

| Signal | Description |
|--------|-------------|
| `type_selected(chart_type)` | Chart type selected |

---

## RadioCardGroup / RadioCard

Radio button selection with card layout.

```python
from design_system import RadioCardGroup, RadioCard

group = RadioCardGroup()
group.add_card(RadioCard(
    value="option1",
    title="Option 1",
    description="Description for option 1"
))
group.add_card(RadioCard(
    value="option2",
    title="Option 2",
    description="Description for option 2"
))

group.value_changed.connect(lambda value: print(f"Selected: {value}"))
```

### RadioCard Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `value` | str | required | Option value |
| `title` | str | required | Card title |
| `description` | str | `""` | Card description |

### RadioCardGroup Signals

| Signal | Description |
|--------|-------------|
| `value_changed(value)` | Selection changed |

---

## Picker Example

File import type selector:

```python
from design_system import (
    Modal, ModalHeader, TypeSelector, TypeOptionCard,
    Button
)

class ImportTypeDialog(Modal):
    def __init__(self, parent=None):
        super().__init__(parent, size="lg")

        self.set_header(ModalHeader(title="Select Import Type"))

        # Type selector
        self.selector = TypeSelector()

        self.selector.add_type(TypeOptionCard(
            type_id="text",
            title="Text Documents",
            description="Import .txt, .docx, .rtf files",
            icon="mdi6.file-document"
        ))

        self.selector.add_type(TypeOptionCard(
            type_id="audio",
            title="Audio Files",
            description="Import .mp3, .wav, .m4a files",
            icon="mdi6.microphone"
        ))

        self.selector.add_type(TypeOptionCard(
            type_id="video",
            title="Video Files",
            description="Import .mp4, .mov, .avi files",
            icon="mdi6.video"
        ))

        self.selector.add_type(TypeOptionCard(
            type_id="pdf",
            title="PDF Documents",
            description="Import .pdf files",
            icon="mdi6.file-pdf-box"
        ))

        self.selector.add_type(TypeOptionCard(
            type_id="image",
            title="Images",
            description="Import .jpg, .png, .gif files",
            icon="mdi6.image"
        ))

        self.body.addWidget(self.selector)

        self.selected_type = None
        self.selector.type_selected.connect(self.on_type_selected)

        # Buttons
        self.add_button("Cancel", variant="outline", on_click=self.reject)
        self.add_button("Continue", variant="primary", on_click=self.accept)

    def on_type_selected(self, type_id):
        self.selected_type = type_id

    def get_selected_type(self):
        return self.selected_type
```
