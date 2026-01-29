"""
PyQt6 Design System - Material Design Theme
Based on QualCoder mockups/css/material-theme.css
"""

# Tokens
from .tokens import (
    ColorPalette,
    COLORS,
    SPACING,
    RADIUS,
    TYPOGRAPHY,
    LAYOUT,
    get_colors,
    get_theme,  # Compatibility wrapper
)

# Stylesheet
from .stylesheet import generate_stylesheet

# Core Components
from .components import (
    Button,
    Input,
    Label,
    Card,
    CardHeader,
    Badge,
    Separator,
    Alert,
    Avatar,
    Chip,
    FileIcon,
)

# Icons (uses qtawesome - browse icons at https://pictogrammers.com/library/mdi/)
from .icons import Icon, IconText, icon, get_pixmap, get_qicon

# Toggle
from .toggle import Toggle, LabeledToggle

# Modal
from .modal import Modal, ModalHeader, ModalBody, ModalFooter

# Toast
from .toast import Toast, ToastContainer, ToastManager

# Context Menu
from .context_menu import (
    ContextMenu,
    ContextMenuItem,
    ContextMenuWidget,
    ContextMenuItemWidget,
)

# Code Tree
from .code_tree import CodeTree, CodeTreeNode, CodeItem

# Stat Card
from .stat_card import StatCard, StatCardRow, MiniStatCard

# Progress Bar
from .progress_bar import (
    ProgressBar,
    ProgressBarWidget,
    ProgressBarLabeled,
    RelevanceScoreBar,
    RelevanceBarWidget,
    ScoreIndicator,
)

# Spinner
from .spinner import Spinner, LoadingIndicator, LoadingOverlay, SkeletonLoader

# Layout Components
from .layout import (
    AppContainer,
    TitleBar,
    MenuBar,
    TabBar,
    Toolbar,
    ToolbarGroup,
    ToolbarButton,
    StatusBar,
    Panel,
    PanelHeader,
    Sidebar,
    MainContent,
)

# Form Components
from .forms import (
    SearchBox,
    Select,
    MultiSelect,
    Textarea,
    NumberInput,
    RangeSlider,
    ColorPicker,
    FormGroup,
    CoderSelector,
)

# Navigation Components
from .navigation import (
    MenuItem,
    Tab,
    TabGroup,
    Breadcrumb,
    NavList,
    StepIndicator,
    MediaTypeSelector,
)

# Data Display Components
from .data_display import (
    DataTable,
    FileCell,
    EntityCell,
    InfoCard,
    CodeDetailCard,
    StatRow,
    KeyValueList,
    EmptyState,
    HeatMapCell,
    HeatMapGrid,
)

# List Components
from .lists import (
    ListItem,
    BaseList,
    FileList,
    FileListItem,
    CaseList,
    CaseListItem,
    AttributeList,
    AttributeListItem,
    QueueList,
    QueueListItem,
)

# Media Components
from .media import (
    VideoContainer,
    WaveformVisualization,
    Timeline,
    PlayerControls,
    Thumbnail,
    ThumbnailStrip,
)

# Chat/AI Components
from .chat import (
    MessageBubble,
    TypingIndicator,
    CodeSuggestion,
    QuickPrompts,
    ChatInput,
    AIReasoningPanel,
    ConfidenceScore,
)

# Document/Text Components
from .document import (
    TextPanel,
    LineNumberArea,
    SelectionPopup,
    TranscriptPanel,
    TranscriptSegment,
    TextColor,
)

# Pagination Components
from .pagination import (
    Pagination,
    PageButton,
    PaginationInfo,
    SimplePagination,
)

# Filter/Search Components
from .filters import (
    FilterPanel,
    FilterSection,
    FilterChip,
    FilterChipGroup,
    SearchInput,
    SearchOptions,
    ViewToggle,
)

# Selection/Picker Components
from .pickers import (
    TypeSelector,
    TypeOptionCard,
    ColorSchemeSelector,
    ColorSchemeOption,
    ChartTypeSelector,
    RadioCardGroup,
    RadioCard,
)

# Upload Components
from .upload import (
    DropZone,
    FileTypeBadges,
    FileTypeBadge,
    UploadProgress,
    UploadList,
    CompactDropZone,
)

# Calendar Components
from .calendar import (
    CalendarMini,
    CalendarDay,
    CalendarNavigation,
    DateRangePicker,
    QuickDateSelect,
)

# Editor Components
from .editors import (
    CodeEditor,
    LineNumbers,
    SimpleSyntaxHighlighter,
    RichTextEditor,
    EditorToolbar,
    MemoEditor,
    DiffViewer,
)

# Chart/Visualization Components (ADR-001)
from .charts import (
    ChartWidget,
    PieChart,
    ChartDataPoint,
    SparkLine,
    LegendItem,
)

# Network Graph Components
from .network_graph import (
    NetworkGraphWidget,
    GraphNode,
    GraphEdge,
)

# Word Cloud Components
from .word_cloud import (
    WordCloudWidget,
    WordCloudPreview,
)

# Image Annotation Components
from .image_annotation import (
    ImageAnnotationLayer,
    ImageAnnotation,
    AnnotationMode,
    AnnotationToolbar,
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
]
