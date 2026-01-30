---
id: doc-001
title: QualCoder Design System API
type: reference
created_date: '2026-01-30 05:48'
---

A comprehensive PyQt6-based component library for QualCoder v2, featuring 100+ reusable, themeable components following Material Design principles.

## Table of Contents

- [Quick Start](#quick-start)
- [Design Tokens](#design-tokens)
- [Core Components](#core-components)
- [Layout Components](#layout-components)
- [Form Components](#form-components)
- [Navigation Components](#navigation-components)
- [Data Display Components](#data-display-components)
- [List Components](#list-components)
- [Media Components](#media-components)
- [Chat/AI Components](#chatai-components)
- [Document Components](#document-components)
- [Feedback Components](#feedback-components)
- [Visualization Components](#visualization-components)
- [Advanced Components](#advanced-components)

---

## Quick Start

```python
from design_system import (
    # Tokens
    COLORS, SPACING, RADIUS, TYPOGRAPHY, LAYOUT,
    ColorPalette, get_colors, get_theme,

    # Core
    Button, Input, Label, Card, Badge, Alert, Avatar, Chip,

    # Icons
    Icon, IconText, icon, get_pixmap, get_qicon,

    # Layout
    AppContainer, Panel, Sidebar, MainContent, Toolbar,

    # Forms
    SearchBox, Select, Textarea, ColorPicker,

    # Data
    DataTable, CodeTree, FileList,
)

# Basic usage
button = Button("Click Me", variant="primary")
label = Label("Title", variant="title")
card = Card()
card.add_widget(label)
card.add_widget(button)
```

---

## Design Tokens

The foundation of the design system - consistent values for colors, spacing, typography, and layout.

### ColorPalette

Complete color system with 60+ color properties.

```python
from design_system import COLORS, ColorPalette, get_colors, get_theme

# Use default colors
button = Button("Save", colors=COLORS)

# Get default palette
colors = get_colors()

# Create custom palette
custom_colors = ColorPalette(
    primary="#0066CC",
    primary_light="#3399FF",
    primary_dark="#004499",
    secondary="#FF5722",
    background="#FFFFFF",
    surface="#F5F5F5",
    text_primary="#212121",
    # ... other properties
)
```

**Color Categories:**

| Category | Properties |
|----------|------------|
| Primary | `primary`, `primary_light`, `primary_dark`, `primary_hover`, `primary_foreground` |
| Secondary | `secondary`, `secondary_light`, `secondary_dark`, `secondary_hover` |
| Semantic | `success`, `warning`, `error`, `info` (each with `_light` variant) |
| Surface | `background`, `surface`, `surface_light`, `surface_lighter`, `surface_elevated` |
| Text | `text_primary`, `text_secondary`, `text_disabled`, `text_hint` |
| Border | `border`, `border_light`, `divider` |
| File Types | `file_text`, `file_audio`, `file_video`, `file_image`, `file_pdf` |
| Code Highlight | `code_yellow`, `code_red`, `code_green`, `code_purple`, `code_blue`, `code_pink`, `code_orange`, `code_cyan` |

### Spacing

```python
from design_system import SPACING

# Available spacing values
SPACING.xs    # 4px
SPACING.sm    # 8px
SPACING.md    # 12px
SPACING.lg    # 16px
SPACING.xl    # 20px
SPACING.xxl   # 24px
SPACING.xxxl  # 32px
```

### BorderRadius

```python
from design_system import RADIUS

RADIUS.none   # 0px
RADIUS.sm     # 4px
RADIUS.md     # 8px
RADIUS.lg     # 12px
RADIUS.xl     # 16px
RADIUS.full   # 9999px (circular)
```

### Typography

```python
from design_system import TYPOGRAPHY

# Font families
TYPOGRAPHY.font_family       # "Roboto"
TYPOGRAPHY.font_family_mono  # "Roboto Mono"

# Font sizes
TYPOGRAPHY.text_xs   # 10px
TYPOGRAPHY.text_sm   # 12px
TYPOGRAPHY.text_base # 14px
TYPOGRAPHY.text_lg   # 16px
TYPOGRAPHY.text_xl   # 18px
TYPOGRAPHY.text_2xl  # 24px
TYPOGRAPHY.text_3xl  # 28px

# Font weights
TYPOGRAPHY.weight_normal    # 400
TYPOGRAPHY.weight_medium    # 500
TYPOGRAPHY.weight_semibold  # 600
TYPOGRAPHY.weight_bold      # 700
```

### Layout

```python
from design_system import LAYOUT

LAYOUT.sidebar_width   # 300px
LAYOUT.toolbar_height  # 52px
LAYOUT.panel_min_width # 200px
```

---

## Core Components

### Button

Styled button with multiple variants and sizes.

```python
from design_system import Button

# Variants: primary, secondary, outline, ghost, danger, success, icon
button = Button("Save", variant="primary")
button = Button("Cancel", variant="outline")
button = Button("Delete", variant="danger")

# Sizes: sm, md, lg
button = Button("Small", size="sm")
button = Button("Large", size="lg")

# With icon
button = Button("", variant="icon")

# Connect click handler
button.clicked.connect(lambda: print("Clicked!"))
```

### Input

Text input field with validation support.

```python
from design_system import Input

input_field = Input(placeholder="Enter name...")

# Error state
input_field.set_error(True)
is_error = input_field.is_error()

# Get/set value
text = input_field.text()
input_field.setText("Hello")
```

### Label

Text label with style variants.

```python
from design_system import Label

# Variants: default, muted, secondary, title, description, hint, error
title = Label("Main Title", variant="title")
description = Label("Some description", variant="description")
hint = Label("Optional field", variant="hint")
error = Label("Invalid input", variant="error")
```

### Card

Container with elevation and shadow.

```python
from design_system import Card, CardHeader

# Basic card
card = Card()
card.add_widget(Label("Content"))

# Card with header
card = Card()
header = CardHeader(title="Card Title", description="Optional description")
card.add_widget(header)
card.add_widget(Label("Body content"))

# Elevation levels: 1-4
card = Card(elevation=2)
```

### Badge

Small tag/label for status or counts.

```python
from design_system import Badge

# Variants: default, secondary, outline, destructive, success, warning, info, primary
badge = Badge("New", variant="primary")
badge = Badge("3", variant="info")
badge = Badge("Error", variant="destructive")
```

### Alert

Callout component for messages.

```python
from design_system import Alert

# Variants: default, destructive, success, warning, info
alert = Alert(
    title="Success!",
    description="Your changes have been saved.",
    variant="success"
)
```

### Avatar

Circular avatar with text or image.

```python
from design_system import Avatar

avatar = Avatar(text="JD", size=40)  # Shows initials
```

### Chip

Tag with optional close button.

```python
from design_system import Chip

chip = Chip("Python", closable=True)
chip.close_clicked.connect(lambda: print("Closed"))
```

### FileIcon

File type icon with colored background.

```python
from design_system import FileIcon

# Types: text, audio, video, image, pdf
icon = FileIcon(file_type="pdf")
icon = FileIcon(file_type="audio")
```

### Separator

Horizontal or vertical divider line.

```python
from design_system import Separator

h_sep = Separator(orientation="horizontal")
v_sep = Separator(orientation="vertical")
```

---

## Icons

Material Design Icons via qtawesome (mdi6 prefix).

```python
from design_system import Icon, IconText, icon, get_pixmap, get_qicon

# Icon widget
folder_icon = Icon("mdi6.folder", size=24, color="#009688")
folder_icon.set_color("#FF5722")
folder_icon.set_size(32)

# Icon + text side by side
item = IconText(icon="mdi6.file", text="document.txt", icon_size=20)

# Factory functions
icon_widget = icon("mdi6.home", size=20, color="#000")
pixmap = get_pixmap("mdi6.save", size=24, color="#009688")
qicon = get_qicon("mdi6.settings", color="#666")
```

**Common Icon Names:**
- Navigation: `mdi6.home`, `mdi6.menu`, `mdi6.arrow-left`, `mdi6.chevron-right`
- Actions: `mdi6.plus`, `mdi6.delete`, `mdi6.pencil`, `mdi6.check`
- Files: `mdi6.file`, `mdi6.folder`, `mdi6.file-document`, `mdi6.file-image`
- Media: `mdi6.play`, `mdi6.pause`, `mdi6.volume-high`, `mdi6.microphone`

Find more at: https://pictogrammers.com/library/mdi/

---

## Layout Components

### AppContainer

Main application container with section management.

```python
from design_system import AppContainer, TitleBar, MenuBar, Toolbar, StatusBar

app = AppContainer()
app.set_title_bar(TitleBar(title="QualCoder"))
app.set_menu_bar(MenuBar())
app.set_toolbar(Toolbar())
app.set_content(main_content)
app.set_status_bar(StatusBar())
```

### Panel

Side panel with header.

```python
from design_system import Panel, PanelHeader

panel = Panel()
header = PanelHeader(title="Properties")
panel.add_widget(header)
panel.add_widget(content)
```

### Sidebar

Collapsible sidebar.

```python
from design_system import Sidebar

sidebar = Sidebar()
sidebar.add_widget(navigation)
```

### Toolbar

Tool button container.

```python
from design_system import Toolbar, ToolbarGroup, ToolbarButton

toolbar = Toolbar()

# Add groups of buttons
file_group = ToolbarGroup()
file_group.add_widget(ToolbarButton("mdi6.folder-open", "Open"))
file_group.add_widget(ToolbarButton("mdi6.content-save", "Save"))
toolbar.add_widget(file_group)
```

### StatusBar

Bottom status bar.

```python
from design_system import StatusBar

status = StatusBar()
status.add_widget(Label("Ready"))
```

---

## Form Components

### SearchBox

Search input with icon.

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

### Select

Dropdown selection.

```python
from design_system import Select

select = Select(placeholder="Choose option...")
select.add_items(["Option 1", "Option 2", "Option 3"])
select.value_changed.connect(lambda value: print(f"Selected: {value}"))
```

### MultiSelect

Multiple selection dropdown.

```python
from design_system import MultiSelect

multi = MultiSelect()
multi.add_items(["Tag 1", "Tag 2", "Tag 3"])
# User can select multiple items
```

### Textarea

Multi-line text input.

```python
from design_system import Textarea

textarea = Textarea(placeholder="Enter description...")
text = textarea.toPlainText()
textarea.setPlainText("Content here")
```

### NumberInput

Numeric input with spin controls.

```python
from design_system import NumberInput

number = NumberInput(minimum=0, maximum=100, value=50)
```

### RangeSlider

Range selection slider.

```python
from design_system import RangeSlider

slider = RangeSlider(minimum=0, maximum=100)
slider.valueChanged.connect(lambda value: print(f"Value: {value}"))
```

### ColorPicker

Color selection widget.

```python
from design_system import ColorPicker

picker = ColorPicker()
picker.color_changed.connect(lambda color: print(f"Color: {color}"))
```

### FormGroup

Grouped form fields.

```python
from design_system import FormGroup

group = FormGroup(label="User Details")
group.add_widget(Input(placeholder="Name"))
group.add_widget(Input(placeholder="Email"))
```

### CoderSelector

Coder/user selection dropdown.

```python
from design_system import CoderSelector

selector = CoderSelector()
# Populated with available coders
```

---

## Navigation Components

### Tab / TabGroup

Tab navigation.

```python
from design_system import Tab, TabGroup

tabs = TabGroup()
tabs.add_tab("Files", icon="mdi6.file", active=True)
tabs.add_tab("Codes", icon="mdi6.tag")
tabs.add_tab("Cases", icon="mdi6.folder")

tabs.tab_changed.connect(lambda name: print(f"Tab: {name}"))
active = tabs.get_active_tab()
```

### MenuItem

Menu item with optional icon.

```python
from design_system import MenuItem

item = MenuItem("Open Project", icon="mdi6.folder-open")
item.setActive(True)
item.clicked.connect(handler)
```

### Breadcrumb

Breadcrumb navigation path.

```python
from design_system import Breadcrumb

breadcrumb = Breadcrumb()
breadcrumb.set_path(["Home", "Projects", "Current"])
```

### NavList

Vertical navigation list.

```python
from design_system import NavList

nav = NavList()
nav.add_item("Dashboard", icon="mdi6.view-dashboard")
nav.add_item("Settings", icon="mdi6.cog")
```

### StepIndicator

Progress steps display.

```python
from design_system import StepIndicator

steps = StepIndicator()
steps.set_steps(["Upload", "Configure", "Review", "Complete"])
steps.set_current(1)  # 0-indexed
```

### MediaTypeSelector

File type filter selector.

```python
from design_system import MediaTypeSelector

selector = MediaTypeSelector()
# Allows filtering by: text, audio, video, image, pdf
```

---

## Data Display Components

### DataTable

Data table with selection support.

```python
from design_system import DataTable

table = DataTable(
    headers=["Name", "Type", "Size"],
    checkable=True  # Enable row selection
)

# Set data
table.set_data([
    {"name": "file1.txt", "type": "text", "size": "10KB"},
    {"name": "file2.pdf", "type": "pdf", "size": "2MB"},
])

# Signals
table.row_clicked.connect(lambda idx, data: print(f"Clicked row {idx}"))
table.row_double_clicked.connect(lambda idx, data: print(f"Double-clicked {idx}"))
table.selection_changed.connect(lambda selected: print(f"Selected: {selected}"))

# Methods
selected = table.get_selected()
table.clear()
```

### CodeTree

Hierarchical tree for qualitative codes.

```python
from design_system import CodeTree, CodeItem

# Define hierarchical structure
items = [
    CodeItem(
        id="1",
        name="Theme A",
        color="#FFC107",
        count=15,
        children=[
            CodeItem(id="1.1", name="Sub-theme", color="#FFD54F", count=5),
        ]
    ),
    CodeItem(id="2", name="Theme B", color="#4CAF50", count=8),
]

tree = CodeTree()
tree.set_items(items)

# Signals
tree.item_clicked.connect(lambda id: print(f"Clicked: {id}"))
tree.item_double_clicked.connect(lambda id: print(f"Edit: {id}"))
tree.item_expanded.connect(lambda id, expanded: print(f"Expanded: {id} = {expanded}"))

# Methods
tree.add_item(CodeItem("3", "New Code", "#2196F3"), parent_id="1")
tree.remove_item("3")
tree.expand_item("1", True)
```

### InfoCard

Information card with icon.

```python
from design_system import InfoCard

card = InfoCard(
    icon="mdi6.information",
    title="Total Files",
    description="127 files imported"
)
```

### KeyValueList

Key-value pairs display.

```python
from design_system import KeyValueList

kvlist = KeyValueList()
kvlist.set_items([
    ("Name", "Project Alpha"),
    ("Created", "2024-01-15"),
    ("Files", "42"),
])
```

### EmptyState

Placeholder for empty content.

```python
from design_system import EmptyState

empty = EmptyState(
    icon="mdi6.folder-open",
    title="No files yet",
    description="Import files to get started"
)
```

### HeatMapGrid

Heatmap visualization.

```python
from design_system import HeatMapGrid, HeatMapCell

grid = HeatMapGrid(rows=5, cols=5)
# Cells are colored based on values
```

---

## List Components

### FileList

File list with type icons.

```python
from design_system import FileList

files = FileList()
files.add_file(
    id="1",
    name="interview.txt",
    file_type="text",
    size="15KB",
    status="coded"
)

files.item_clicked.connect(lambda id: print(f"Selected: {id}"))
files.item_double_clicked.connect(lambda id: print(f"Open: {id}"))
```

### CaseList

Case/study list.

```python
from design_system import CaseList

cases = CaseList()
cases.add_item(ListItem(id="1", text="Case Study A", subtitle="5 files"))
```

### AttributeList

Attribute list display.

```python
from design_system import AttributeList

attrs = AttributeList()
attrs.add_item(ListItem(id="1", text="Age", subtitle="Numeric"))
```

### QueueList

Queue/task list.

```python
from design_system import QueueList

queue = QueueList()
queue.add_item(ListItem(id="1", text="Review coding", badge="3", badge_variant="warning"))
```

### ListItem

Data structure for list items.

```python
from design_system import ListItem

item = ListItem(
    id="unique-id",
    text="Item Title",
    subtitle="Optional subtitle",
    icon="mdi6.file",
    badge="New",
    badge_variant="primary",
    data={"custom": "data"}
)
```

---

## Media Components

### VideoContainer

Video player container.

```python
from design_system import VideoContainer

video = VideoContainer()
video.set_source("/path/to/video.mp4")
```

### WaveformVisualization

Audio waveform display.

```python
from design_system import WaveformVisualization

waveform = WaveformVisualization()
waveform.set_position(0.5)  # 50% through
waveform.add_segment(start=10.0, end=25.0, color="#009688")

waveform.position_changed.connect(lambda pos: print(f"Position: {pos}"))
```

### Timeline

Playback timeline.

```python
from design_system import Timeline

timeline = Timeline()
timeline.set_duration(300)  # 5 minutes
timeline.set_position(60)   # 1 minute
```

### PlayerControls

Media player controls.

```python
from design_system import PlayerControls

controls = PlayerControls()
controls.play_clicked.connect(play_handler)
controls.pause_clicked.connect(pause_handler)
```

### Thumbnail / ThumbnailStrip

Image thumbnails.

```python
from design_system import Thumbnail, ThumbnailStrip

thumb = Thumbnail(image_path="/path/to/image.jpg", size=100)

strip = ThumbnailStrip()
strip.add_thumbnail("/path/to/img1.jpg")
strip.add_thumbnail("/path/to/img2.jpg")
```

---

## Chat/AI Components

### MessageBubble

Chat message display.

```python
from design_system import MessageBubble

user_msg = MessageBubble(
    text="What codes are most frequent?",
    role="user",
    timestamp="10:30 AM"
)

assistant_msg = MessageBubble(
    text="The most frequent code is 'Theme A' with 15 occurrences.",
    role="assistant",
    timestamp="10:30 AM"
)
```

### TypingIndicator

Animated typing indicator.

```python
from design_system import TypingIndicator

indicator = TypingIndicator()
indicator.start()
# ... AI is thinking ...
indicator.stop()
```

### ChatInput

Message input with send button.

```python
from design_system import ChatInput

chat_input = ChatInput()
chat_input.message_submitted.connect(lambda text: send_message(text))
```

### CodeSuggestion

AI code suggestion display.

```python
from design_system import CodeSuggestion

suggestion = CodeSuggestion(
    code_name="Theme A",
    code_color="#FFC107",
    confidence=0.85,
    text_excerpt="relevant text from document..."
)
```

### AIReasoningPanel

AI reasoning explanation.

```python
from design_system import AIReasoningPanel

panel = AIReasoningPanel()
panel.set_reasoning("Based on the context of...")
```

### ConfidenceScore

Score visualization.

```python
from design_system import ConfidenceScore

score = ConfidenceScore(value=0.92, label="Confidence")
```

---

## Document Components

### TextPanel

Text document display with optional line numbers.

```python
from design_system import TextPanel

panel = TextPanel(
    title="Interview Transcript",
    badge_text="Coded",
    show_header=True,
    editable=False,
    show_line_numbers=True
)

panel.set_text("Document content here...")
text = panel.get_text()
panel.set_stats([("Words", "1,234"), ("Codes", "15")])

panel.text_selected.connect(lambda text, start, end: print(f"Selected: {text}"))
```

### TranscriptPanel

Transcript display with segments.

```python
from design_system import TranscriptPanel, TranscriptSegment

panel = TranscriptPanel()
panel.add_segment(TranscriptSegment(
    speaker="Interviewer",
    timestamp="00:00:15",
    text="Can you describe your experience?"
))
```

### SelectionPopup

Context popup for text selections.

```python
from design_system import SelectionPopup

popup = SelectionPopup()
popup.add_action("Apply Code", lambda: apply_code())
popup.add_action("Add Memo", lambda: add_memo())
popup.show_at(x, y)
```

---

## Feedback Components

### Spinner / LoadingIndicator

Loading spinners.

```python
from design_system import Spinner, LoadingIndicator, LoadingOverlay

# Simple spinner
spinner = Spinner(size=24, color="#009688")
spinner.start()
spinner.stop()

# Spinner with text
loading = LoadingIndicator(text="Loading files...")
loading.start()

# Full-screen overlay
overlay = LoadingOverlay(parent=main_window)
overlay.show()
# ... loading ...
overlay.hide()
```

### SkeletonLoader

Skeleton loading placeholder.

```python
from design_system import SkeletonLoader

skeleton = SkeletonLoader(width=200, height=20)
```

### Toast

Popup notifications.

```python
from design_system import Toast, ToastManager

# Show toast
toast = Toast(
    message="File saved successfully",
    variant="success",  # success, error, warning, info
    duration=3000,      # ms, 0 for infinite
    closable=True
)
toast.show_toast()

# Using manager (handles positioning)
ToastManager.show("Operation complete", variant="success")
```

### ProgressBar

Progress indicator.

```python
from design_system import ProgressBar, ProgressBarLabeled

# Simple progress
progress = ProgressBar()
progress.setValue(50)
progress.setMaxValue(100)

# With label
labeled = ProgressBarLabeled(label="Importing files...")
labeled.setValue(75)
```

### StatCard

Statistics display with trend.

```python
from design_system import StatCard, StatCardRow, MiniStatCard

card = StatCard(
    value="1,234",
    label="Total Codes",
    trend="+12%",
    trend_direction="up",  # or "down"
    icon="mdi6.tag",
    color="#009688"
)

# Multiple stats in row
row = StatCardRow()
row.add_stat(StatCard(...))
row.add_stat(StatCard(...))

# Compact version
mini = MiniStatCard(value="42", label="Files")
```

---

## Visualization Components

### ChartWidget

Charts using PyQtGraph.

```python
from design_system import ChartWidget, ChartDataPoint

chart = ChartWidget(title="Code Frequency", subtitle="Top 10 codes")

# Bar chart
chart.set_bar_data([
    ChartDataPoint("Theme A", 15, "#FFC107"),
    ChartDataPoint("Theme B", 12, "#4CAF50"),
    ChartDataPoint("Theme C", 8, "#2196F3"),
])

# Line chart
chart.set_line_data([
    ChartDataPoint("Jan", 10),
    ChartDataPoint("Feb", 15),
    ChartDataPoint("Mar", 12),
])

# Scatter plot
chart.set_scatter_data([...])

chart.point_clicked.connect(lambda idx, data: print(f"Clicked: {data}"))
chart.clear()
```

### PieChart

Pie chart specialization.

```python
from design_system import PieChart

pie = PieChart(title="Distribution")
pie.set_data([
    ChartDataPoint("Category A", 40, "#FFC107"),
    ChartDataPoint("Category B", 35, "#4CAF50"),
    ChartDataPoint("Category C", 25, "#2196F3"),
])
```

### SparkLine

Mini inline sparkline.

```python
from design_system import SparkLine

spark = SparkLine(data=[10, 15, 12, 18, 14, 20], color="#009688")
```

### NetworkGraphWidget

Interactive network visualization.

```python
from design_system import NetworkGraphWidget, GraphNode, GraphEdge

graph = NetworkGraphWidget()

# Add nodes
graph.add_node(GraphNode(id="1", label="Code A", color="#FFC107", size=20))
graph.add_node(GraphNode(id="2", label="Code B", color="#4CAF50", size=15))

# Add edges
graph.add_edge(GraphEdge(source="1", target="2", weight=5, label="co-occurs"))

# Layout algorithms: spring, circular, kamada-kawai
graph.layout("spring")

# Signals
graph.node_clicked.connect(lambda id, meta: print(f"Node: {id}"))
graph.node_double_clicked.connect(lambda id, meta: print(f"Edit: {id}"))
graph.edge_clicked.connect(lambda src, tgt: print(f"Edge: {src} -> {tgt}"))

graph.clear()
```

### WordCloudWidget

Word cloud visualization.

```python
from design_system import WordCloudWidget

cloud = WordCloudWidget(
    max_words=100,
    min_font_size=10,
    max_font_size=60,
    color_scheme="primary"  # primary, success, error, warning, info
)

# From word frequencies
cloud.set_frequencies({
    "qualitative": 50,
    "research": 45,
    "coding": 40,
    "analysis": 35,
})

# Or from raw text
cloud.set_text("Full text content to analyze...")

cloud.generate()
cloud.word_clicked.connect(lambda word: print(f"Word: {word}"))
```

### PDFPageViewer

PDF document viewer with text selection overlay.

```python
from design_system import PDFPageViewer, PDFSelection

viewer = PDFPageViewer(
    show_toolbar=True,      # Navigation and zoom controls
    show_thumbnails=True,   # Page thumbnail sidebar
    initial_zoom=1.0        # Starting zoom level
)

# Load document
viewer.load_document("/path/to/document.pdf")

# Navigation
viewer.go_to_page(5)        # 0-indexed
viewer.next_page()
viewer.previous_page()

# Zoom
viewer.set_zoom(1.5)        # 150%
viewer.zoom_in()            # +25%
viewer.zoom_out()           # -25%
viewer.fit_to_width()       # Auto-fit

# Signals
viewer.page_changed.connect(lambda page: print(f"Page: {page}"))
viewer.document_loaded.connect(lambda count: print(f"Pages: {count}"))
viewer.zoom_changed.connect(lambda zoom: print(f"Zoom: {zoom}"))

# Text selection (Ctrl+Click and drag)
viewer.text_selected.connect(lambda sel: handle_selection(sel))

def handle_selection(selection: PDFSelection):
    print(f"Page: {selection.page}")
    print(f"Text: {selection.text}")
    print(f"Rect: {selection.rect}")

# Properties
page = viewer.current_page   # Current page (0-indexed)
total = viewer.page_count    # Total pages
zoom = viewer.zoom           # Current zoom level

# Cleanup
viewer.close_document()
```

**Key Features:**
- Page navigation with toolbar or keyboard
- Zoom controls (25% to 400%)
- Fit to width
- Page rotation
- Text selection overlay (Ctrl+Click drag)
- Optional page thumbnails sidebar
- Signals for page changes and text selection

**Dependencies:** Requires `pymupdf` (PyMuPDF) for PDF rendering.

---

## Advanced Components

### Modal

Material Design dialog.

```python
from design_system import Modal, ModalHeader, ModalBody, ModalFooter

modal = Modal(size="default")  # sm, default, lg, xl

# Add header
modal.set_header(ModalHeader(title="Confirm Action"))

# Add content to body
modal.body.addWidget(Label("Are you sure you want to proceed?"))

# Add buttons
modal.add_button("Cancel", variant="outline", on_click=modal.reject)
modal.add_button("Confirm", variant="primary", on_click=modal.accept)

# Show
result = modal.exec()  # Returns QDialog.Accepted or QDialog.Rejected
```

### Toggle

Switch component.

```python
from design_system import Toggle, LabeledToggle

toggle = Toggle()
toggle.setChecked(True)
toggle.toggled.connect(lambda checked: print(f"Toggled: {checked}"))

# With label
labeled = LabeledToggle(label="Enable feature")
```

### ContextMenu

Right-click menu.

```python
from design_system import ContextMenu

menu = ContextMenu()
menu.add_item("Edit", icon="mdi6.pencil", on_click=edit_handler)
menu.add_item("Delete", icon="mdi6.delete", variant="danger", on_click=delete_handler)
menu.add_separator()
submenu = menu.add_submenu("More Options")
submenu.add_item("Option 1", on_click=handler1)

# Show at cursor
menu.exec(QCursor.pos())
```

### FilterPanel

Collapsible filter panel.

```python
from design_system import FilterPanel

filters = FilterPanel()
filters.add_section("File Type", ["Text", "Audio", "Video", "Image"])
filters.add_section("Status", ["Coded", "Uncoded", "In Progress"])

filters.filters_changed.connect(lambda f: print(f"Filters: {f}"))

# Methods
current = filters.get_filters()
filters.clear_filters()
filters.set_collapsed(True)
```

### ViewToggle

Toggle between different view modes.

```python
from design_system import ViewToggle

# Create toggle with view options
toggle = ViewToggle(views=["grid", "list", "table"], current="list")

# Signal emitted when view changes
toggle.view_changed.connect(lambda view: switch_to_view(view))

# Methods
toggle.set_view("grid")
current = toggle.current_view()
```

### ImageAnnotationLayer

Image annotation with drawing tools.

```python
from design_system import ImageAnnotationLayer, ImageAnnotation, AnnotationMode

layer = ImageAnnotationLayer()
layer.load_image("/path/to/image.jpg")

# Set drawing mode
layer.set_mode(AnnotationMode.RECTANGLE)  # SELECT, RECTANGLE, POLYGON, FREEHAND

# Signals
layer.annotation_created.connect(lambda ann: print(f"Created: {ann.id}"))
layer.annotation_selected.connect(lambda id: print(f"Selected: {id}"))
layer.annotation_deleted.connect(lambda id: print(f"Deleted: {id}"))

# Methods
annotations = layer.get_annotations()
layer.clear_annotations()
layer.delete_annotation("annotation-id")
```

### CodeEditor

Code editor with syntax highlighting.

```python
from design_system import CodeEditor

editor = CodeEditor(
    language="python",
    read_only=False,
    show_line_numbers=True
)

editor.set_code("def hello():\n    print('Hello')")
code = editor.get_code()
editor.set_language("sql")

editor.code_changed.connect(lambda code: print("Code changed"))
```

### DiffViewer

Side-by-side diff viewer.

```python
from design_system import DiffViewer

diff = DiffViewer()
diff.set_content("Original content...", "Modified content...")
```

### RichTextEditor

Rich text editor with formatting toolbar.

```python
from design_system import RichTextEditor

editor = RichTextEditor(show_toolbar=True)

# Set content
editor.set_html("<p>Hello <b>World</b></p>")
editor.set_plain_text("Plain text content")

# Get content
html = editor.get_html()
text = editor.get_plain_text()

# Signal emitted when content changes
editor.content_changed.connect(lambda html: save_content(html))
```

### MemoEditor

Memo/note editor for annotations.

```python
from design_system import MemoEditor

memo = MemoEditor(title="Research Notes")

# Set/get content
memo.set_content("My notes here...")
content = memo.get_content()

# Signals
memo.content_changed.connect(lambda text: auto_save(text))
memo.save_clicked.connect(lambda: save_memo())
```

### Pagination

Page navigation.

```python
from design_system import Pagination, SimplePagination

# Full pagination
pager = Pagination(current_page=1, total_pages=10)
pager.page_changed.connect(lambda page: load_page(page))
pager.go_to_page(5)
pager.set_total_pages(20)

# Simple prev/next
simple = SimplePagination()
simple.previous_clicked.connect(prev_handler)
simple.next_clicked.connect(next_handler)
```

### DateRangePicker

Date range selection.

```python
from design_system import DateRangePicker, QuickDateSelect

picker = DateRangePicker()
picker.range_changed.connect(lambda start, end: print(f"Range: {start} to {end}"))

# Quick presets
quick = QuickDateSelect()  # Today, Yesterday, This Week, etc.
```

### DropZone

Drag-and-drop file upload.

```python
from design_system import DropZone

zone = DropZone(
    accepted_types=[".txt", ".pdf", ".docx"],
    max_files=10,
    max_size_mb=50
)

zone.files_dropped.connect(lambda files: handle_upload(files))
zone.browse_clicked.connect(open_file_dialog)

zone.enable_drop()
zone.disable_drop()
```

---

## Stylesheet Generation

Generate complete Qt stylesheets from tokens.

```python
from design_system import generate_stylesheet, COLORS

# Generate default stylesheet
stylesheet = generate_stylesheet(COLORS)

# Apply to application
app.setStyleSheet(stylesheet)

# With custom colors
custom_colors = ColorPalette(primary="#0066CC", ...)
stylesheet = generate_stylesheet(custom_colors)
```

---

## Common Patterns

### Signal-Based Interactivity

```python
# Connect signals to handlers
button.clicked.connect(self.on_button_click)
table.row_clicked.connect(lambda idx, data: self.select_row(idx))
search.text_changed.connect(self.filter_results)

# Emit custom signals
self.data_changed.emit(new_data)
```

### Color Customization

```python
# Override specific colors
custom = ColorPalette(
    primary="#0066CC",
    primary_light="#3399FF",
    success="#22C55E",
    error="#EF4444",
)

# Apply to components
button = Button("Save", variant="primary", colors=custom)
```

### Hierarchical Data

```python
# Tree structures
tree.set_items([
    CodeItem("1", "Parent", "#FFC107", count=10, children=[
        CodeItem("1.1", "Child A", "#FFD54F", count=5),
        CodeItem("1.2", "Child B", "#FFE082", count=5),
    ])
])
```

### Container Composition

```python
# Build complex layouts
card = Card()
card.add_widget(CardHeader(title="Section"))
card.add_widget(Label("Content"))
card.add_widget(Button("Action", variant="primary"))
```

---

## Dependencies

- **PyQt6**: All widgets and layouts
- **qtawesome**: Material Design Icons (mdi6)
- **pyqtgraph**: Charts and plotting
- **networkx**: Graph algorithms
- **wordcloud**: Word cloud generation
- **numpy**: Numerical operations
- **pymupdf**: PDF rendering (PDFPageViewer)

---

## Module Index

| Module | Purpose |
|--------|---------|
| `tokens.py` | Design tokens (colors, spacing, typography) |
| `stylesheet.py` | Qt stylesheet generation |
| `components.py` | Core UI components |
| `icons.py` | Icon system |
| `toggle.py` | Toggle/switch component |
| `modal.py` | Modal dialogs |
| `toast.py` | Toast notifications |
| `context_menu.py` | Context menus |
| `layout.py` | Layout components |
| `forms.py` | Form inputs |
| `navigation.py` | Navigation components |
| `data_display.py` | Data display components |
| `lists.py` | List components |
| `media.py` | Media components |
| `chat.py` | Chat/AI components |
| `document.py` | Document components |
| `pagination.py` | Pagination components |
| `filters.py` | Filter components |
| `pickers.py` | Picker components |
| `upload.py` | Upload components |
| `calendar.py` | Calendar components |
| `editors.py` | Editor components |
| `charts.py` | Chart components |
| `network_graph.py` | Network graph |
| `word_cloud.py` | Word cloud |
| `image_annotation.py` | Image annotation |
| `pdf_viewer.py` | PDF document viewer |
| `code_tree.py` | Code tree |
| `stat_card.py` | Statistics cards |
| `spinner.py` | Loading spinners |
| `progress_bar.py` | Progress bars |
