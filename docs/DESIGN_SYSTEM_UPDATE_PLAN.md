# Design System Update Plan

## Objective

Update the design system with components needed to build the Text Coding screen (`code_text.html`), while keeping components generic and reusable.

---

## Gap Analysis

### Components Already Available

| Component | Module | Status |
|-----------|--------|--------|
| Panel, PanelHeader | `layout.py` | ✅ Ready |
| Toolbar, ToolbarGroup, ToolbarButton | `layout.py` | ✅ Ready |
| SearchBox, Select | `forms.py` | ✅ Ready |
| Badge, Chip | `components.py` | ✅ Ready |
| Card, CardHeader | `components.py` | ✅ Ready |
| Modal, ModalHeader, ModalBody, ModalFooter | `modal.py` | ✅ Ready |
| Toast, ToastContainer | `toast.py` | ✅ Ready |
| ProgressBar | `progress_bar.py` | ✅ Ready |
| CodeTree, CodeTreeNode | `code_tree.py` | ✅ Ready |
| Button, Icon, Label | `components.py`, `icons.py` | ✅ Ready |
| FileList, FileListItem | `lists.py` | ✅ Ready |

### Components to Add/Update

| Component | Module | Priority | Effort |
|-----------|--------|----------|--------|
| InfoCard | `data_display.py` | P1 | Small |
| CodeDetailCard | `data_display.py` | P1 | Small |
| TextPanel (update) | `document.py` | P1 | Medium |
| CodedTextHighlight (update) | `document.py` | P1 | Medium |
| OverlapIndicator | `document.py` | P2 | Small |
| SelectionPopup (update) | `document.py` | P1 | Medium |
| MediaTypeSelector | `navigation.py` | P2 | Small |
| CoderSelector | `forms.py` | P3 | Small |

---

## Phase 1: Data Display Components

### 1.1 InfoCard

A titled card for displaying contextual information in side panels.

**File:** `design_system/data_display.py`

**Props:**
- `title: str` - Card title
- `icon: str` - qtawesome icon name (e.g., "mdi6.information")
- `content: QWidget` - Content widget (slot)
- `collapsible: bool = False` - Allow collapse/expand
- `colors: ColorPalette`

**Usage:**
```python
info = InfoCard(
    title="Selected Code",
    icon="mdi6.information",
    collapsible=False,
)
info.set_content(code_details_widget)
```

**Reference HTML:**
```html
<div class="info-card">
    <div class="info-card-title">
        <span class="material-icons">info</span>
        Selected Code
    </div>
    <!-- content here -->
</div>
```

---

### 1.2 CodeDetailCard

Displays details of a selected code (color, name, memo, example).

**File:** `design_system/data_display.py`

**Props:**
- `color: str` - Code color hex
- `name: str` - Code name
- `memo: str` - Code memo/description
- `example: str = None` - Example text snippet
- `colors: ColorPalette`

**Signals:**
- `edit_clicked` - User wants to edit code
- `delete_clicked` - User wants to delete code

**Usage:**
```python
detail = CodeDetailCard(
    color="#FFC107",
    name="soccer playing",
    memo="Code for references to playing soccer...",
    example="I have not studied much before...",
)
```

**Reference HTML:**
```html
<div class="code-details">
    <div class="code-detail-header">
        <span class="code-detail-color" style="background: #FFC107;"></span>
        <span class="code-detail-name">soccer playing</span>
    </div>
    <div class="code-detail-memo">...</div>
    <div class="example-text">"I have not studied much before..."</div>
</div>
```

---

## Phase 2: Document Components

### 2.1 TextPanel (Update)

Update existing `TextPanel` to support:
- Header with title, badge, and stats
- Scrollable text content area
- Text selection tracking

**File:** `design_system/document.py`

**New Props:**
- `title: str` - Document title
- `badge_text: str = None` - Optional badge (e.g., "Case: ID2")
- `stats: list[tuple[str, str]]` - List of (icon, text) stats

**New Methods:**
- `set_stats(stats: list)` - Update stats display
- `get_selection() -> tuple[int, int]` - Get selected text range
- `scroll_to_position(pos: int)` - Scroll to text position

**Reference HTML:**
```html
<div class="editor-header">
    <span class="editor-title">
        <span class="material-icons">edit_document</span>
        ID2.odt
        <span class="badge info">Case: ID2</span>
    </span>
    <div class="editor-stats">
        <span class="chip"><span class="material-icons">layers</span> 2 overlapping</span>
        ...
    </div>
</div>
<div class="editor-content">
    <div class="text-content">...</div>
</div>
```

---

### 2.2 CodedTextHighlight (Update)

Update to support:
- Multiple color variants
- Overlap indication (overline style)
- Code count badge for overlapping segments
- Click handling to select coded segment

**File:** `design_system/document.py`

**Props:**
- `color: str` - Highlight color
- `overlap_count: int = 0` - Number of overlapping codes (0 = no overlap)
- `clickable: bool = True`

**Signals:**
- `clicked(segment_id: str)` - Segment was clicked

**Styles (from HTML):**
```css
.coded {
    padding: 2px 0;
    border-radius: 2px;
    cursor: pointer;
    background: rgba(color, 0.3);
    border-bottom: 2px solid color;
}
.coded.overlap {
    text-decoration: overline;
    text-decoration-color: warning;
}
.code-indicator { /* badge for overlap count */
    position: absolute; top: -8px; right: -4px;
    background: primary; color: white;
    font-size: 9px; padding: 1px 4px; border-radius: 8px;
}
```

---

### 2.3 OverlapIndicator

Shows that a text segment has multiple codes applied.

**File:** `design_system/document.py`

**Props:**
- `count: int` - Number of overlapping codes
- `colors: ColorPalette`

**Usage:**
```python
indicator = OverlapIndicator(count=2)
```

---

### 2.4 SelectionPopup (Update)

Floating toolbar that appears when text is selected.

**File:** `design_system/document.py`

**Props:**
- `actions: list[tuple[str, str, Callable]]` - List of (icon, tooltip, callback)
- `colors: ColorPalette`

**Methods:**
- `show_at(x: int, y: int)` - Show popup at position
- `hide()` - Hide popup

**Signals:**
- `action_triggered(action_id: str)` - Action button clicked

**Default Actions:**
- Apply selected code (`mdi6.label`)
- Quick code (`mdi6.plus`)
- Add annotation (`mdi6.note-edit`)
- Add memo (`mdi6.note-plus`)

**Reference HTML:**
```html
<div class="selection-popup">
    <button class="toolbar-btn" title="Apply selected code">
        <span class="material-icons">label</span>
    </button>
    <button class="toolbar-btn" title="Quick code">
        <span class="material-icons">add</span>
    </button>
    ...
</div>
```

---

## Phase 3: Navigation Components

### 3.1 MediaTypeSelector

Tab-style selector for media types (Text, Image, A/V, PDF).

**File:** `design_system/navigation.py`

**Props:**
- `options: list[tuple[str, str, str]]` - List of (id, label, icon)
- `selected: str` - Currently selected option id
- `colors: ColorPalette`

**Signals:**
- `selection_changed(id: str)` - Selection changed

**Usage:**
```python
selector = MediaTypeSelector(
    options=[
        ("text", "Text", "mdi6.file-document"),
        ("image", "Image", "mdi6.image"),
        ("av", "A/V", "mdi6.video"),
        ("pdf", "PDF", "mdi6.file-pdf-box"),
    ],
    selected="text",
)
selector.selection_changed.connect(on_media_type_changed)
```

---

## Phase 4: Form Components

### 4.1 CoderSelector

Labeled dropdown for selecting current coder. Uses existing `Select` component with a label prefix.

---

## Implementation Order

```
Phase 1: Data Display
├── InfoCard
├── CodeDetailCard
└── Tests

Phase 2: Document Features
├── TextPanel updates
├── CodedTextHighlight updates
├── OverlapIndicator
├── SelectionPopup updates
└── Tests

Phase 3: Navigation
├── MediaTypeSelector
└── Tests

Phase 4: Forms
├── CoderSelector (light - uses existing Select)
└── Storybook stories
```

---

## Testing Strategy

### Unit Tests (per component)
- Component creation with default props
- Component creation with custom props
- Signal emission on user interaction
- Style updates based on state changes
- Theme compatibility (dark/light)

### Integration Tests
- Components work together in layouts
- Selection popup appears on text selection
- Code highlights render correctly
- InfoCard updates when code selected

### Visual Tests (Storybook)
- Each component has a story
- Stories show all variants/states
- Screenshot comparison for regressions

---

## Files to Modify

| File | Changes |
|------|---------|
| `design_system/data_display.py` | Add `InfoCard`, `CodeDetailCard` |
| `design_system/document.py` | Update `TextPanel`, `CodedTextHighlight`, `SelectionPopup`; Add `OverlapIndicator` |
| `design_system/navigation.py` | Add `MediaTypeSelector` |
| `design_system/forms.py` | Add `CoderSelector` (light) |
| `design_system/__init__.py` | Export new components |
| `design_system/tests/test_data_display.py` | Add tests |
| `design_system/tests/test_document.py` | Add/update tests |
| `design_system/storybook/stories/` | Add stories |

---

## Success Criteria

1. All new components pass unit tests
2. Components render correctly in both dark and light themes
3. Storybook shows all component variants
4. Components can be composed to build the Text Coding screen
5. No regressions in existing components
