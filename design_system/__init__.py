"""
PySide6 Design System for QualCoder.

A scholarly, refined design system for qualitative research applications.

Features:
- Distinctive indigo/coral color palette
- Inter typography for excellent readability
- Light and dark theme support
- Comprehensive component library
- Animation and shadow tokens

Usage:
    from design_system import Button, Card, COLORS, set_theme
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Use light theme (default)
    set_theme("light")

    # Or switch to dark theme
    set_theme("dark")

    # Components automatically use the current theme
    btn = Button("Click me")
"""

# Tokens
# Chart/Visualization Components (ADR-001)
from .charts import (
    ChartDataPoint,
    ChartWidget,
    LegendItem,
    PieChart,
    SparkLine,
)

# Chat/AI Components
from .chat import (
    AIReasoningPanel,
    ChatInput,
    CodeSuggestion,
    ConfidenceScore,
    MessageBubble,
    QuickPrompts,
    TypingIndicator,
)

# Code Tree
from .code_tree import CodeItem, CodeTree, CodeTreeNode

# Core Components
from .components import (
    Alert,
    Avatar,
    Badge,
    Button,
    Card,
    CardHeader,
    Chip,
    FileIcon,
    Input,
    Label,
    Separator,
)

# Context Menu
from .context_menu import (
    ContextMenu,
    ContextMenuItem,
    ContextMenuItemWidget,
    ContextMenuWidget,
)

# Data Display Components
from .data_display import (
    CodeDetailCard,
    DataTable,
    EmptyState,
    EntityCell,
    FileCell,
    HeatMapCell,
    HeatMapGrid,
    InfoCard,
    KeyValueList,
    StatRow,
)

# Calendar Components
from .date_picker import (
    CalendarDay,
    CalendarMini,
    CalendarNavigation,
    DateRangePicker,
    QuickDateSelect,
)

# Document/Text Components
from .document import (
    LineNumberArea,
    SelectionPopup,
    TextColor,
    TextPanel,
    TranscriptPanel,
    TranscriptSegment,
)

# Editor Components
from .editors import (
    CodeEditor,
    DiffViewer,
    EditorToolbar,
    LineNumbers,
    MemoEditor,
    RichTextEditor,
    SimpleSyntaxHighlighter,
)

# Filter/Search Components
from .filters import (
    FilterChip,
    FilterChipGroup,
    FilterPanel,
    FilterSection,
    SearchInput,
    SearchOptions,
    ViewToggle,
)

# Form Components
from .forms import (
    CoderSelector,
    ColorPicker,
    FormGroup,
    MultiSelect,
    NumberInput,
    RangeSlider,
    SearchBox,
    Select,
    Textarea,
)

# Icons (uses qtawesome - browse icons at https://pictogrammers.com/library/mdi/)
from .icons import Icon, IconText, get_pixmap, get_qicon, icon

# Image Annotation Components
from .image_annotation import (
    AnnotationMode,
    AnnotationToolbar,
    ImageAnnotation,
    ImageAnnotationLayer,
)

# Layout Components
from .layout import (
    AppContainer,
    MainContent,
    MenuBar,
    Panel,
    PanelHeader,
    Sidebar,
    StatusBar,
    TabBar,
    TitleBar,
    Toolbar,
    ToolbarButton,
    ToolbarGroup,
)

# List Components
from .lists import (
    AttributeList,
    AttributeListItem,
    BaseList,
    CaseList,
    CaseListItem,
    FileList,
    FileListItem,
    ListItem,
    QueueList,
    QueueListItem,
)

# Media Components
from .media import (
    PlayerControls,
    Thumbnail,
    ThumbnailStrip,
    Timeline,
    VideoContainer,
    WaveformVisualization,
)

# Modal
from .modal import Modal, ModalBody, ModalFooter, ModalHeader

# Navigation Components
from .navigation import (
    Breadcrumb,
    MediaTypeSelector,
    MenuItem,
    NavList,
    StepIndicator,
    Tab,
    TabGroup,
)

# Network Graph Components
from .network_graph import (
    GraphEdge,
    GraphNode,
    NetworkGraphWidget,
)

# Pagination Components
from .pagination import (
    PageButton,
    Pagination,
    PaginationInfo,
    SimplePagination,
)

# PDF Viewer Components
from .pdf_viewer import (
    PDFGraphicsView,
    PDFPageViewer,
    PDFSelection,
    PDFTextBlock,
    PDFThumbnail,
)

# Selection/Picker Components
from .pickers import (
    ChartTypeSelector,
    ColorSchemeOption,
    ColorSchemeSelector,
    ColorSwatch,
    RadioCard,
    RadioCardGroup,
    TypeOptionCard,
    TypeSelector,
)

# Progress Bar
from .progress_bar import (
    ProgressBar,
    ProgressBarLabeled,
    ProgressBarWidget,
    RelevanceBarWidget,
    RelevanceScoreBar,
    ScoreIndicator,
)

# Spinner
from .spinner import LoadingIndicator, LoadingOverlay, SkeletonLoader, Spinner

# Stat Card
from .stat_card import MiniStatCard, StatCard, StatCardRow

# Stylesheet
from .stylesheet import generate_stylesheet

# Toast
from .toast import Toast, ToastContainer, ToastManager

# Toggle
from .toggle import LabeledToggle, Toggle
from .tokens import (
    ANIMATION,
    # Theme instances
    COLORS,
    COLORS_DARK,
    COLORS_LIGHT,
    GRADIENTS,
    LAYOUT,
    RADIUS,
    SHADOWS,
    # Scale tokens
    SPACING,
    TYPOGRAPHY,
    ZINDEX,
    # Core types
    ColorPalette,
    # Theme functions
    get_colors,
    get_theme,
    register_theme,
    set_theme,
)

# Upload Components
from .upload import (
    CompactDropZone,
    DropZone,
    FileTypeBadge,
    FileTypeBadges,
    UploadList,
    UploadProgress,
)

# Word Cloud Components
from .word_cloud import (
    WordCloudPreview,
    WordCloudWidget,
)

__all__ = [
    # Tokens
    "ColorPalette",
    "COLORS",
    "SPACING",
    "RADIUS",
    "TYPOGRAPHY",
    "LAYOUT",
    "get_colors",
    "get_theme",
    # Stylesheet
    "generate_stylesheet",
    # Core Components
    "Button",
    "Input",
    "Label",
    "Card",
    "CardHeader",
    "Badge",
    "Separator",
    "Alert",
    "Avatar",
    "Chip",
    "FileIcon",
    # Icons
    "Icon",
    "IconText",
    "icon",
    "get_pixmap",
    "get_qicon",
    # Toggle
    "Toggle",
    "LabeledToggle",
    # Modal
    "Modal",
    "ModalHeader",
    "ModalBody",
    "ModalFooter",
    # Toast
    "Toast",
    "ToastContainer",
    "ToastManager",
    # Context Menu
    "ContextMenu",
    "ContextMenuItem",
    "ContextMenuWidget",
    "ContextMenuItemWidget",
    # Code Tree
    "CodeTree",
    "CodeTreeNode",
    "CodeItem",
    # Stat Card
    "StatCard",
    "StatCardRow",
    "MiniStatCard",
    # Progress Bar
    "ProgressBar",
    "ProgressBarWidget",
    "ProgressBarLabeled",
    "RelevanceScoreBar",
    "RelevanceBarWidget",
    "ScoreIndicator",
    # Spinner
    "Spinner",
    "LoadingIndicator",
    "LoadingOverlay",
    "SkeletonLoader",
    # Layout
    "AppContainer",
    "TitleBar",
    "MenuBar",
    "TabBar",
    "Toolbar",
    "ToolbarGroup",
    "ToolbarButton",
    "StatusBar",
    "Panel",
    "PanelHeader",
    "Sidebar",
    "MainContent",
    # Forms
    "SearchBox",
    "Select",
    "MultiSelect",
    "Textarea",
    "NumberInput",
    "RangeSlider",
    "ColorPicker",
    "FormGroup",
    "CoderSelector",
    # Navigation
    "MenuItem",
    "Tab",
    "TabGroup",
    "Breadcrumb",
    "NavList",
    "StepIndicator",
    "MediaTypeSelector",
    # Data Display
    "DataTable",
    "FileCell",
    "EntityCell",
    "InfoCard",
    "CodeDetailCard",
    "StatRow",
    "KeyValueList",
    "EmptyState",
    "HeatMapCell",
    "HeatMapGrid",
    # Lists
    "ListItem",
    "BaseList",
    "FileList",
    "FileListItem",
    "CaseList",
    "CaseListItem",
    "AttributeList",
    "AttributeListItem",
    "QueueList",
    "QueueListItem",
    # Media
    "VideoContainer",
    "WaveformVisualization",
    "Timeline",
    "PlayerControls",
    "Thumbnail",
    "ThumbnailStrip",
    # Chat/AI
    "MessageBubble",
    "TypingIndicator",
    "CodeSuggestion",
    "QuickPrompts",
    "ChatInput",
    "AIReasoningPanel",
    "ConfidenceScore",
    # Document/Text
    "TextPanel",
    "LineNumberArea",
    "SelectionPopup",
    "TranscriptPanel",
    "TranscriptSegment",
    "TextColor",
    # Pagination
    "Pagination",
    "PageButton",
    "PaginationInfo",
    "SimplePagination",
    # Filters
    "FilterPanel",
    "FilterSection",
    "FilterChip",
    "FilterChipGroup",
    "SearchInput",
    "SearchOptions",
    "ViewToggle",
    # Pickers
    "TypeSelector",
    "TypeOptionCard",
    "ColorSchemeSelector",
    "ColorSchemeOption",
    "ChartTypeSelector",
    "RadioCardGroup",
    "RadioCard",
    # Upload
    "DropZone",
    "FileTypeBadges",
    "FileTypeBadge",
    "UploadProgress",
    "UploadList",
    "CompactDropZone",
    # Calendar
    "CalendarMini",
    "CalendarDay",
    "CalendarNavigation",
    "DateRangePicker",
    "QuickDateSelect",
    # Editors
    "CodeEditor",
    "LineNumbers",
    "SimpleSyntaxHighlighter",
    "RichTextEditor",
    "EditorToolbar",
    "MemoEditor",
    "DiffViewer",
    # Charts/Visualization
    "ChartWidget",
    "PieChart",
    "ChartDataPoint",
    "SparkLine",
    "LegendItem",
    # Network Graph
    "NetworkGraphWidget",
    "GraphNode",
    "GraphEdge",
    # Word Cloud
    "WordCloudWidget",
    "WordCloudPreview",
    # Image Annotation
    "ImageAnnotationLayer",
    "ImageAnnotation",
    "AnnotationMode",
    "AnnotationToolbar",
    # PDF Viewer
    "PDFPageViewer",
    "PDFGraphicsView",
    "PDFThumbnail",
    "PDFTextBlock",
    "PDFSelection",
]
