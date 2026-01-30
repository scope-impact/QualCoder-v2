# Module Index

Complete module listing for the QualCoder Design System.

## Core Modules

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `tokens.py` | Design tokens | `COLORS`, `SPACING`, `RADIUS`, `TYPOGRAPHY`, `LAYOUT`, `ANIMATION`, `SHADOWS`, `ZINDEX`, `ColorPalette` |
| `stylesheet.py` | Qt stylesheet generation | `generate_stylesheet` |
| `components.py` | Core UI components | `Button`, `Input`, `Label`, `Card`, `Badge`, `Alert`, `Avatar`, `Chip`, `FileIcon`, `Separator` |
| `icons.py` | Icon system | `Icon`, `IconText`, `icon`, `get_pixmap`, `get_qicon` |

## Layout Modules

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `layout.py` | Layout components | `AppContainer`, `TitleBar`, `MenuBar`, `MainContent`, `Panel`, `PanelHeader`, `Sidebar`, `Toolbar`, `ToolbarGroup`, `ToolbarButton`, `StatusBar`, `TabBar` |

## Form Modules

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `forms.py` | Form inputs | `SearchBox`, `Select`, `MultiSelect`, `Textarea`, `NumberInput`, `RangeSlider`, `ColorPicker`, `FormGroup`, `CoderSelector` |

## Navigation Modules

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `navigation.py` | Navigation components | `Tab`, `TabGroup`, `MenuItem`, `Breadcrumb`, `NavList`, `StepIndicator`, `MediaTypeSelector` |

## Data Display Modules

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `data_display.py` | Data display components | `DataTable`, `InfoCard`, `KeyValueList`, `EmptyState`, `HeatMapGrid`, `HeatMapCell`, `CodeDetailCard`, `FileCell`, `EntityCell`, `StatRow` |
| `code_tree.py` | Code tree | `CodeTree`, `CodeItem`, `CodeTreeNode` |

## List Modules

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `lists.py` | List components | `FileList`, `CaseList`, `AttributeList`, `QueueList`, `ListItem`, `BaseList`, `FileListItem`, `CaseListItem`, `AttributeListItem`, `QueueListItem` |

## Media Modules

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `media.py` | Media components | `VideoContainer`, `WaveformVisualization`, `Timeline`, `PlayerControls`, `Thumbnail`, `ThumbnailStrip` |

## Chat/AI Modules

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `chat.py` | Chat/AI components | `MessageBubble`, `TypingIndicator`, `ChatInput`, `QuickPrompts`, `CodeSuggestion`, `AIReasoningPanel`, `ConfidenceScore` |

## Document Modules

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `document.py` | Document components | `TextPanel`, `LineNumberArea`, `TranscriptPanel`, `TranscriptSegment`, `SelectionPopup`, `TextColor` |

## Feedback Modules

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `spinner.py` | Loading spinners | `Spinner`, `LoadingIndicator`, `LoadingOverlay`, `SkeletonLoader` |
| `toast.py` | Toast notifications | `Toast`, `ToastManager`, `ToastContainer` |
| `progress_bar.py` | Progress bars | `ProgressBar`, `ProgressBarLabeled`, `ProgressBarWidget`, `RelevanceScoreBar`, `RelevanceBarWidget`, `ScoreIndicator` |
| `stat_card.py` | Statistics cards | `StatCard`, `StatCardRow`, `MiniStatCard` |

## Visualization Modules

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `charts.py` | Chart components | `ChartWidget`, `ChartDataPoint`, `PieChart`, `SparkLine`, `LegendItem` |
| `network_graph.py` | Network graph | `NetworkGraphWidget`, `GraphNode`, `GraphEdge` |
| `word_cloud.py` | Word cloud | `WordCloudWidget`, `WordCloudPreview` |
| `pdf_viewer.py` | PDF document viewer | `PDFPageViewer`, `PDFSelection`, `PDFGraphicsView`, `PDFThumbnail`, `PDFTextBlock` |

## Picker Modules

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `pickers.py` | Picker components | `TypeSelector`, `TypeOptionCard`, `ColorSchemeSelector`, `ColorSchemeOption`, `ChartTypeSelector`, `RadioCardGroup`, `RadioCard` |

## Advanced Modules

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `modal.py` | Modal dialogs | `Modal`, `ModalHeader`, `ModalBody`, `ModalFooter` |
| `toggle.py` | Toggle/switch | `Toggle`, `LabeledToggle` |
| `context_menu.py` | Context menus | `ContextMenu`, `ContextMenuItem`, `ContextMenuWidget`, `ContextMenuItemWidget` |
| `filters.py` | Filter components | `FilterPanel`, `FilterSection`, `FilterChip`, `FilterChipGroup`, `SearchInput`, `SearchOptions`, `ViewToggle` |
| `editors.py` | Editor components | `CodeEditor`, `LineNumbers`, `SimpleSyntaxHighlighter`, `EditorToolbar`, `DiffViewer`, `RichTextEditor`, `MemoEditor` |
| `pagination.py` | Pagination | `Pagination`, `SimplePagination`, `PageButton`, `PaginationInfo` |
| `calendar.py` | Calendar components | `DateRangePicker`, `QuickDateSelect`, `CalendarMini`, `CalendarDay`, `CalendarNavigation` |
| `upload.py` | Upload components | `DropZone`, `CompactDropZone`, `FileTypeBadges`, `FileTypeBadge`, `UploadProgress`, `UploadList` |
| `image_annotation.py` | Image annotation | `ImageAnnotationLayer`, `ImageAnnotation`, `AnnotationMode`, `AnnotationToolbar` |

## Theme Functions

| Function | Purpose |
|----------|---------|
| `get_theme()` | Get current theme name |
| `set_theme(name)` | Set active theme |
| `get_colors()` | Get current color palette |
| `register_theme(name, palette)` | Register custom theme |
| `generate_stylesheet(colors)` | Generate Qt stylesheet |

## Data Classes

| Class | Module | Purpose |
|-------|--------|---------|
| `ColorPalette` | `tokens.py` | Color palette definition |
| `ListItem` | `lists.py` | List item data |
| `CodeItem` | `code_tree.py` | Code tree node data |
| `ChartDataPoint` | `charts.py` | Chart data point |
| `GraphNode` | `network_graph.py` | Network node data |
| `GraphEdge` | `network_graph.py` | Network edge data |
| `TranscriptSegment` | `document.py` | Transcript segment data |
| `PDFSelection` | `pdf_viewer.py` | PDF text selection |
| `ImageAnnotation` | `image_annotation.py` | Image annotation data |
