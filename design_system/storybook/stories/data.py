"""
Data display component stories: tables, lists, stats, codetree
"""

from typing import List, Tuple

from ...qt_compat import QWidget, QHBoxLayout

from ...tokens import SPACING, ColorPalette
from ...data_display import DataTable, KeyValueList, EmptyState
from ...lists import FileList, CaseList, QueueList
from ...stat_card import StatCard, MiniStatCard
from ...code_tree import CodeTree, CodeItem
from ..page import StoryPage


def create_tables_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Data table
    table = DataTable(columns=["Name", "Type", "Size", "Date"], colors=colors)
    table.set_data([
        {"Name": "Interview_01.txt", "Type": "Text", "Size": "12.4 KB", "Date": "Jan 15, 2024"},
        {"Name": "Focus_group.mp3", "Type": "Audio", "Size": "45.2 MB", "Date": "Jan 14, 2024"},
        {"Name": "Survey_results.pdf", "Type": "PDF", "Size": "2.1 MB", "Date": "Jan 13, 2024"},
    ])
    examples.append((
        "Data Table",
        table,
        'table = DataTable(columns=["Name", "Type"])\ntable.set_data([{"Name": "File.txt", ...}])'
    ))

    # Key-value list
    kvlist = KeyValueList(colors=colors)
    kvlist.add_item("Project", "QualCoder Research")
    kvlist.add_item("Created", "January 10, 2024")
    kvlist.add_item("Files", "24")
    kvlist.add_item("Codes", "156")
    examples.append((
        "Key-Value List",
        kvlist,
        'kvlist = KeyValueList()\nkvlist.add_item("Project", "Name")'
    ))

    # Empty state
    empty = EmptyState(
        icon="📁",
        title="No files yet",
        message="Import files to get started with your analysis.",
        colors=colors
    )
    examples.append((
        "Empty State",
        empty,
        'EmptyState(icon="📁", title="No files", message="...")'
    ))

    return StoryPage(
        "Tables & Data",
        "Components for displaying tabular and structured data.",
        examples,
        colors=colors
    )


def create_lists_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # File list
    file_list = FileList(colors=colors)
    file_list.add_file("1", "Interview_01.txt", "text", "12.4 KB", "coded")
    file_list.add_file("2", "Focus_group.mp3", "audio", "45.2 MB", "in progress")
    file_list.add_file("3", "Survey.pdf", "pdf", "2.1 MB", "pending")
    file_list.setMaximumHeight(200)
    examples.append((
        "File List",
        file_list,
        'file_list = FileList()\nfile_list.add_file("1", "File.txt", "text", "12 KB")'
    ))

    # Case list
    case_list = CaseList(colors=colors)
    case_list.add_case("1", "Participant 01", "3 files", color="#4CAF50")
    case_list.add_case("2", "Participant 02", "5 files", color="#2196F3")
    case_list.add_case("3", "Participant 03", "2 files", color="#FF9800")
    case_list.setMaximumHeight(180)
    examples.append((
        "Case List",
        case_list,
        'case_list = CaseList()\ncase_list.add_case("1", "Name", "subtitle")'
    ))

    # Queue list
    queue = QueueList(colors=colors)
    queue.add_item("1", "Create code 'Learning'", "pending", "John")
    queue.add_item("2", "Merge codes", "reviewing", "Sarah")
    queue.add_item("3", "Delete segment", "approved", "Mike")
    queue.setMaximumHeight(150)
    examples.append((
        "Queue List",
        queue,
        'queue = QueueList()\nqueue.add_item("1", "Task", "pending", "Author")'
    ))

    return StoryPage(
        "Lists",
        "List components for displaying collections of items.",
        examples,
        colors=colors
    )


def create_stats_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Stat card
    stat = StatCard(
        value="24",
        label="Total Files",
        trend="+3 this week",
        trend_direction="up",
        icon="📁",
        colors=colors
    )
    examples.append((
        "Stat Card",
        stat,
        'StatCard(value="24", label="Total Files", icon="📁")'
    ))

    # Mini stat cards
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setSpacing(SPACING.md)
    layout.addWidget(MiniStatCard(value="24", label="Files", colors=colors))
    layout.addWidget(MiniStatCard(value="156", label="Codes", colors=colors))
    layout.addWidget(MiniStatCard(value="42", label="Memos", colors=colors))
    layout.addStretch()
    examples.append((
        "Mini Stat Cards",
        container,
        'MiniStatCard(value="24", label="Files")'
    ))

    return StoryPage(
        "Stat Cards",
        "Display key metrics and statistics prominently.",
        examples,
        colors=colors
    )


def create_codetree_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Code tree
    tree = CodeTree(colors=colors)
    tree.set_items([
        CodeItem("1", "Learning", "#FFC107", 24, children=[
            CodeItem("1.1", "Formal Learning", "#FFC107", 12),
            CodeItem("1.2", "Informal Learning", "#FFC107", 8),
        ]),
        CodeItem("2", "Experience", "#4CAF50", 18, children=[
            CodeItem("2.1", "Work Experience", "#4CAF50", 10),
            CodeItem("2.2", "Life Experience", "#4CAF50", 8),
        ]),
        CodeItem("3", "Emotions", "#E91E63", 15),
    ])
    tree.setMaximumHeight(250)
    examples.append((
        "Code Tree",
        tree,
        'tree = CodeTree()\ntree.set_items([CodeItem("1", "Learning", "#FFC107", 24)])'
    ))

    return StoryPage(
        "Code Tree",
        "Hierarchical code/category tree for qualitative analysis.",
        examples,
        colors=colors
    )


def get_stories(colors: ColorPalette) -> List[Tuple[str, str, StoryPage]]:
    """Return all data display stories"""
    return [
        ("tables", "Tables", create_tables_story(colors)),
        ("lists", "Lists", create_lists_story(colors)),
        ("stats", "Stat Cards", create_stats_story(colors)),
        ("codetree", "Code Tree", create_codetree_story(colors)),
    ]
