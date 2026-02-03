"""
QualCoder v2 - Flet Dashboard POC

Proof-of-concept implementation of the dashboard mockup using Flet.
This demonstrates how the EventBus architecture will integrate with Flet.

Compatible with Flet 0.80+
"""

import flet as ft

from tokens import LIGHT, DARK, TYPOGRAPHY, SPACING, RADIUS, get_colors


class DashboardState:
    """Simple state container (would connect to EventBus in real app)."""

    def __init__(self):
        self.user_name = "Jane"
        self.project_name = "remote work"
        self.sources_count = 24
        self.codes_count = 156
        self.segments_count = 892
        self.completion_percent = 68
        self.top_codes = [
            {"name": "Work-life balance", "count": 45, "percent": 85, "color": "primary"},
            {"name": "Remote challenges", "count": 38, "percent": 72, "color": "accent"},
            {"name": "Team collaboration", "count": 32, "percent": 60, "color": "sage"},
            {"name": "Meeting fatigue", "count": 25, "percent": 48, "color": "rose"},
            {"name": "Flexibility benefits", "count": 21, "percent": 40, "color": "violet"},
        ]
        self.recent_activity = [
            {
                "text": "Applied Work-life balance to 3 segments in Interview_P08.txt",
                "time": "2 minutes ago",
                "color": "primary",
            },
            {
                "text": "Imported Interview_P12.txt to the Interviews folder",
                "time": "15 minutes ago",
                "color": "sage",
            },
            {
                "text": "AI suggested 5 new code applications for review",
                "time": "1 hour ago",
                "color": "accent",
            },
            {
                "text": "Created new case Participant 12 with 2 linked sources",
                "time": "2 hours ago",
                "color": "rose",
            },
        ]
        self.sources_to_code = [
            {"name": "Interview_P12.txt", "words": 2450, "progress": 0, "status": "Not started"},
            {"name": "Focus_Group_2.txt", "words": 4120, "progress": 35, "status": "35% coded"},
            {"name": "Survey_OpenEnd.txt", "words": 1890, "progress": 72, "status": "72% coded"},
        ]


def create_sidebar(colors, on_nav_click, dark_mode: bool = False):
    """Create the navigation sidebar."""

    def nav_item(icon: str, label: str, active: bool = False, badge: str | None = None):
        bg_color = colors.primary_700 if active else None
        text_color = colors.text_inverse if active else colors.text_secondary

        content = [
            ft.Icon(icon, size=20, color=text_color),
            ft.Text(label, size=TYPOGRAPHY.sm, color=text_color, expand=True),
        ]
        if badge:
            content.append(
                ft.Container(
                    ft.Text(badge, size=10, color=colors.text_inverse),
                    bgcolor=colors.primary_500,
                    border_radius=RADIUS.full,
                    padding=ft.Padding(left=8, top=2, right=8, bottom=2),
                )
            )

        return ft.Container(
            content=ft.Row(content, spacing=SPACING.md),
            padding=ft.Padding(left=SPACING.lg, top=SPACING.md, right=SPACING.lg, bottom=SPACING.md),
            border_radius=RADIUS.md,
            bgcolor=bg_color,
            on_click=lambda e: on_nav_click(label),
            ink=True,
        )

    return ft.Container(
        content=ft.Column(
            [
                # Logo
                ft.Container(
                    ft.Row(
                        [
                            ft.Container(
                                ft.Text("Q", size=18, weight=ft.FontWeight.BOLD, color=colors.text_inverse),
                                width=36,
                                height=36,
                                bgcolor=colors.primary_600,
                                border_radius=RADIUS.md,
                                alignment=ft.Alignment.CENTER,
                            ),
                            ft.Text("QualCoder", size=TYPOGRAPHY.lg, weight=ft.FontWeight.W_600, color=colors.text_primary),
                        ],
                        spacing=SPACING.md,
                    ),
                    padding=ft.Padding(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl),
                ),
                # User info
                ft.Container(
                    ft.Row(
                        [
                            ft.Container(
                                ft.Text("JD", size=12, color=colors.text_inverse),
                                width=40,
                                height=40,
                                bgcolor=colors.primary_500,
                                border_radius=RADIUS.full,
                                alignment=ft.Alignment.CENTER,
                            ),
                            ft.Column(
                                [
                                    ft.Text("Jane Doe", size=TYPOGRAPHY.sm, weight=ft.FontWeight.W_500, color=colors.text_primary),
                                    ft.Text("Lead Researcher", size=TYPOGRAPHY.xs, color=colors.text_tertiary),
                                ],
                                spacing=2,
                            ),
                        ],
                        spacing=SPACING.md,
                    ),
                    padding=ft.Padding(SPACING.xl, SPACING.lg, SPACING.xl, SPACING.lg),
                ),
                ft.Divider(height=1, color=colors.surface_border),
                # Navigation
                ft.Container(
                    ft.Column(
                        [
                            ft.Text("WORKSPACE", size=10, color=colors.text_muted, weight=ft.FontWeight.W_600),
                            nav_item(ft.Icons.DASHBOARD_OUTLINED, "Dashboard", active=True),
                            nav_item(ft.Icons.DESCRIPTION_OUTLINED, "Sources", badge="24"),
                            nav_item(ft.Icons.CODE, "Coding"),
                            nav_item(ft.Icons.PEOPLE_OUTLINED, "Cases", badge="12"),
                        ],
                        spacing=SPACING.xs,
                    ),
                    padding=ft.Padding(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg),
                ),
                ft.Container(
                    ft.Column(
                        [
                            ft.Text("ANALYSIS", size=10, color=colors.text_muted, weight=ft.FontWeight.W_600),
                            nav_item(ft.Icons.BAR_CHART, "Insights"),
                            nav_item(ft.Icons.ARTICLE_OUTLINED, "Reports"),
                        ],
                        spacing=SPACING.xs,
                    ),
                    padding=ft.Padding(SPACING.lg, 0, SPACING.lg, 0),
                ),
                ft.Container(expand=True),
                # Footer
                ft.Container(
                    nav_item(ft.Icons.SETTINGS_OUTLINED, "Settings"),
                    padding=ft.Padding(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg),
                ),
            ],
            spacing=0,
        ),
        width=260,
        bgcolor=colors.surface_card,
        border=ft.border.only(right=ft.BorderSide(1, colors.surface_border)),
    )


def create_hero_section(state: DashboardState, colors):
    """Create the hero section with welcome message and stats."""

    return ft.Container(
        content=ft.Stack(
            [
                # Background gradient container
                ft.Container(
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment.TOP_LEFT,
                        end=ft.Alignment.BOTTOM_RIGHT,
                        colors=[colors.primary_700, colors.primary_900],
                    ),
                    border_radius=RADIUS.xxl,
                    expand=True,
                ),
                # Content
                ft.Container(
                    content=ft.Row(
                        [
                            # Left content
                            ft.Column(
                                [
                                    ft.Text(
                                        f"Good afternoon, {state.user_name}",
                                        size=TYPOGRAPHY.sm,
                                        color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    ft.Text(
                                        f"Your research on {state.project_name} is progressing well",
                                        size=TYPOGRAPHY.xxxl,
                                        color=ft.Colors.WHITE,
                                        weight=ft.FontWeight.W_300,
                                    ),
                                    ft.Text(
                                        f"You've coded {state.segments_count} segments across {state.sources_count} sources. "
                                        "3 sources are ready for coding and the AI has 5 new suggestions.",
                                        size=TYPOGRAPHY.lg,
                                        color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
                                    ),
                                    ft.Row(
                                        [
                                            ft.Button(
                                                "Continue Coding",
                                                icon=ft.Icons.CODE,
                                                style=ft.ButtonStyle(
                                                    bgcolor=ft.Colors.WHITE,
                                                    color=colors.primary_700,
                                                ),
                                            ),
                                            ft.Button(
                                                "Review AI Suggestions",
                                                icon=ft.Icons.AUTO_AWESOME,
                                                style=ft.ButtonStyle(
                                                    color=ft.Colors.WHITE,
                                                    side=ft.BorderSide(1, ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),
                                                    bgcolor=ft.Colors.TRANSPARENT,
                                                ),
                                            ),
                                        ],
                                        spacing=SPACING.md,
                                    ),
                                ],
                                spacing=SPACING.lg,
                                width=500,
                            ),
                            ft.Container(expand=True),
                            # Stats card
                            ft.Container(
                                content=ft.Row(
                                    [
                                        _stat_item(str(state.sources_count), "Sources", colors),
                                        ft.VerticalDivider(width=1, color=colors.surface_border),
                                        _stat_item(str(state.codes_count), "Codes", colors),
                                        ft.VerticalDivider(width=1, color=colors.surface_border),
                                        _stat_item(str(state.segments_count), "Segments", colors),
                                        ft.VerticalDivider(width=1, color=colors.surface_border),
                                        _stat_item(f"{state.completion_percent}%", "Complete", colors),
                                    ],
                                    spacing=SPACING.xl,
                                ),
                                bgcolor=colors.surface_card,
                                border_radius=RADIUS.xl,
                                padding=ft.Padding(SPACING.xl, SPACING.lg, SPACING.xl, SPACING.lg),
                                shadow=ft.BoxShadow(
                                    spread_radius=0,
                                    blur_radius=24,
                                    color=ft.Colors.with_opacity(0.12, ft.Colors.BLACK),
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                    ),
                    padding=ft.Padding(SPACING.xxxl, SPACING.xxxl, SPACING.xxxl, SPACING.xxxl),
                ),
            ],
        ),
        height=280,
        border_radius=RADIUS.xxl,
    )


def _stat_item(value: str, label: str, colors):
    """Create a stat item for the hero section."""
    return ft.Column(
        [
            ft.Text(value, size=TYPOGRAPHY.xxl, weight=ft.FontWeight.W_500, color=colors.text_primary),
            ft.Text(label, size=TYPOGRAPHY.xs, color=colors.text_tertiary),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=SPACING.xs,
    )


def create_quick_actions(colors):
    """Create the quick actions grid."""

    actions = [
        {"icon": ft.Icons.ADD_CIRCLE_OUTLINE, "title": "Import Sources", "desc": "Add new documents to analyze", "color": colors.primary_500},
        {"icon": ft.Icons.CODE, "title": "Start Coding", "desc": "Apply codes to your sources", "color": colors.accent_500},
        {"icon": ft.Icons.AUTO_AWESOME, "title": "AI Auto-Code", "desc": "Let AI suggest codes", "color": colors.sage_400},
        {"icon": ft.Icons.INSIGHTS, "title": "View Insights", "desc": "Analyze patterns in your data", "color": colors.rose_400},
    ]

    def action_card(action):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        ft.Icon(action["icon"], size=20, color=action["color"]),
                        width=40,
                        height=40,
                        bgcolor=ft.Colors.with_opacity(0.1, action["color"]),
                        border_radius=RADIUS.lg,
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Text(action["title"], size=TYPOGRAPHY.sm, weight=ft.FontWeight.W_600, color=colors.text_primary),
                    ft.Text(action["desc"], size=TYPOGRAPHY.xs, color=colors.text_tertiary),
                ],
                spacing=SPACING.lg,
            ),
            padding=ft.Padding(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl),
            bgcolor=colors.surface_paper,
            border=ft.border.all(1, colors.surface_border),
            border_radius=RADIUS.xl,
            on_hover=lambda e: _on_card_hover(e, colors),
            ink=True,
            expand=True,
        )

    return ft.Row(
        [action_card(a) for a in actions],
        spacing=SPACING.lg,
    )


def _on_card_hover(e, colors):
    """Handle card hover state."""
    e.control.border = ft.border.all(1, colors.primary_300 if e.data == "true" else colors.surface_border)
    e.control.update()


def create_code_frequency(state: DashboardState, colors):
    """Create the code frequency chart."""

    color_map = {
        "primary": colors.primary_500,
        "accent": colors.accent_400,
        "sage": colors.sage_400,
        "rose": colors.rose_400,
        "violet": "#6d28d9",
    }

    def code_bar(code):
        return ft.Row(
            [
                ft.Container(
                    ft.Text(code["name"], size=TYPOGRAPHY.sm, color=colors.text_secondary, text_align=ft.TextAlign.RIGHT),
                    width=120,
                ),
                ft.Container(
                    ft.Container(
                        bgcolor=color_map.get(code["color"], colors.primary_500),
                        border_radius=RADIUS.md,
                        width=f"{code['percent']}%",
                        height=32,
                    ),
                    bgcolor=colors.surface_paper,
                    border_radius=RADIUS.md,
                    expand=True,
                    height=32,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
                ft.Text(str(code["count"]), size=TYPOGRAPHY.sm, weight=ft.FontWeight.W_500, color=colors.text_primary, width=40),
            ],
            spacing=SPACING.md,
        )

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("Most Used Codes", size=TYPOGRAPHY.sm, weight=ft.FontWeight.W_600, color=colors.text_primary),
                                ft.Text("Top 5 by frequency", size=TYPOGRAPHY.xs, color=colors.text_muted),
                            ],
                            spacing=SPACING.xs,
                        ),
                        ft.TextButton("See all", style=ft.ButtonStyle(color=colors.text_tertiary)),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Column([code_bar(c) for c in state.top_codes], spacing=SPACING.md),
            ],
            spacing=SPACING.xl,
        ),
        padding=ft.Padding(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl),
        bgcolor=colors.surface_card,
        border=ft.border.all(1, colors.surface_border),
        border_radius=RADIUS.xl,
        expand=True,
    )


def create_activity_feed(state: DashboardState, colors):
    """Create the recent activity feed."""

    color_map = {
        "primary": colors.primary_400,
        "accent": colors.accent_400,
        "sage": colors.sage_400,
        "rose": colors.rose_400,
    }

    def activity_item(activity):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        width=10,
                        height=10,
                        bgcolor=color_map.get(activity["color"], colors.primary_400),
                        border_radius=RADIUS.full,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                activity["text"],
                                size=TYPOGRAPHY.sm,
                                color=colors.text_secondary,
                            ),
                            ft.Text(activity["time"], size=TYPOGRAPHY.xs, color=colors.text_muted),
                        ],
                        spacing=SPACING.xs,
                        expand=True,
                    ),
                ],
                spacing=SPACING.lg,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=ft.Padding(0, SPACING.lg, 0, SPACING.lg),
            border=ft.border.only(bottom=ft.BorderSide(1, colors.surface_border_subtle)),
        )

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("Recent Activity", size=TYPOGRAPHY.sm, weight=ft.FontWeight.W_600, color=colors.text_primary),
                                ft.Text("Your coding timeline", size=TYPOGRAPHY.xs, color=colors.text_muted),
                            ],
                            spacing=SPACING.xs,
                        ),
                        ft.TextButton("View all", style=ft.ButtonStyle(color=colors.text_tertiary)),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Column([activity_item(a) for a in state.recent_activity], spacing=0),
            ],
            spacing=SPACING.xl,
        ),
        padding=ft.Padding(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl),
        bgcolor=colors.surface_card,
        border=ft.border.all(1, colors.surface_border),
        border_radius=RADIUS.xl,
        expand=True,
    )


def create_ai_insight_card(colors):
    """Create the AI insight card."""

    return ft.Container(
        content=ft.Column(
            [
                # AI Badge
                ft.Container(
                    ft.Row(
                        [
                            ft.Container(width=6, height=6, bgcolor=colors.accent_500, border_radius=RADIUS.full),
                            ft.Text("AI Insight", size=TYPOGRAPHY.xs, weight=ft.FontWeight.W_600, color=colors.accent_700),
                        ],
                        spacing=SPACING.sm,
                    ),
                    bgcolor=colors.accent_100,
                    border_radius=RADIUS.full,
                    padding=ft.Padding(SPACING.md, SPACING.xs, SPACING.md, SPACING.xs),
                ),
                ft.Text(
                    "Strong thematic connection discovered",
                    size=TYPOGRAPHY.lg,
                    weight=ft.FontWeight.W_500,
                    color=colors.text_primary,
                ),
                ft.Text(
                    '"Work-life balance" and "remote challenges" co-occur in 68% of cases. '
                    "Participants frequently discuss these topics together, "
                    "suggesting they may be different aspects of a broader theme.",
                    size=TYPOGRAPHY.base,
                    color=colors.text_secondary,
                ),
                ft.Row(
                    [
                        ft.Button(
                            "Create Theme",
                            icon=ft.Icons.ADD,
                            style=ft.ButtonStyle(
                                bgcolor=colors.accent_500,
                                color=ft.Colors.WHITE,
                            ),
                        ),
                        ft.Button(
                            "View Co-occurrences",
                            style=ft.ButtonStyle(
                                side=ft.BorderSide(1, colors.surface_border),
                                bgcolor=ft.Colors.TRANSPARENT,
                            ),
                        ),
                        ft.TextButton("Dismiss", style=ft.ButtonStyle(color=colors.text_muted)),
                    ],
                    spacing=SPACING.md,
                ),
            ],
            spacing=SPACING.lg,
        ),
        padding=ft.Padding(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl),
        bgcolor=ft.Colors.with_opacity(0.08, colors.accent_400),
        border=ft.border.all(1, colors.accent_200),
        border_radius=RADIUS.xl,
        expand=2,
    )


def create_sources_to_code(state: DashboardState, colors):
    """Create the sources to code list."""

    def source_item(source):
        progress_color = colors.stone_300 if source["progress"] == 0 else colors.primary_500
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=20, color=colors.text_tertiary),
                        width=44,
                        height=44,
                        bgcolor=colors.surface_paper,
                        border=ft.border.all(1, colors.surface_border),
                        border_radius=RADIUS.lg,
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column(
                        [
                            ft.Text(source["name"], size=TYPOGRAPHY.sm, weight=ft.FontWeight.W_500, color=colors.text_primary),
                            ft.Text(f"{source['words']:,} words - {source['status']}", size=TYPOGRAPHY.xs, color=colors.text_muted),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Container(
                        ft.Container(
                            bgcolor=progress_color,
                            border_radius=RADIUS.full,
                            width=f"{max(source['progress'], 0)}%",
                            height=6,
                        ),
                        width=60,
                        height=6,
                        bgcolor=colors.surface_paper,
                        border_radius=RADIUS.full,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    ),
                ],
                spacing=SPACING.lg,
            ),
            padding=ft.Padding(SPACING.md, SPACING.md, SPACING.md, SPACING.md),
            border_radius=RADIUS.lg,
            ink=True,
        )

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("Sources to Code", size=TYPOGRAPHY.sm, weight=ft.FontWeight.W_600, color=colors.text_primary),
                                ft.Text("3 files need attention", size=TYPOGRAPHY.xs, color=colors.text_muted),
                            ],
                            spacing=SPACING.xs,
                        ),
                        ft.TextButton("View all", style=ft.ButtonStyle(color=colors.text_tertiary)),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Column([source_item(s) for s in state.sources_to_code], spacing=SPACING.sm),
            ],
            spacing=SPACING.xl,
        ),
        padding=ft.Padding(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl),
        bgcolor=colors.surface_card,
        border=ft.border.all(1, colors.surface_border),
        border_radius=RADIUS.xl,
        expand=True,
    )


def main(page: ft.Page):
    """Main entry point for the Flet dashboard."""

    # Page configuration
    page.title = "QualCoder v2 - Dashboard"
    page.padding = 0
    page.spacing = 0
    page.theme_mode = ft.ThemeMode.LIGHT

    # State
    dark_mode = False
    state = DashboardState()
    colors = get_colors(dark_mode)

    def toggle_theme(e):
        nonlocal dark_mode, colors
        dark_mode = not dark_mode
        page.theme_mode = ft.ThemeMode.DARK if dark_mode else ft.ThemeMode.LIGHT
        colors = get_colors(dark_mode)
        page.bgcolor = colors.surface_ground
        rebuild_ui()

    def on_nav_click(label):
        print(f"Navigate to: {label}")

    def rebuild_ui():
        page.controls.clear()
        page.add(build_ui())
        page.update()

    def build_ui():
        return ft.Row(
            [
                # Sidebar
                create_sidebar(colors, on_nav_click, dark_mode),
                # Main content
                ft.Container(
                    content=ft.Column(
                        [
                            # Header
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Text("Dashboard", size=TYPOGRAPHY.xl, weight=ft.FontWeight.W_600, color=colors.text_primary),
                                        ft.Container(expand=True),
                                        ft.TextField(
                                            hint_text="Search codes, sources, cases... (Ctrl+K)",
                                            width=400,
                                            height=40,
                                            border_radius=RADIUS.md,
                                            content_padding=ft.Padding(SPACING.lg, 0, SPACING.lg, 0),
                                        ),
                                        ft.IconButton(
                                            ft.Icons.DARK_MODE if not dark_mode else ft.Icons.LIGHT_MODE,
                                            on_click=toggle_theme,
                                        ),
                                        ft.Button(
                                            "Import",
                                            icon=ft.Icons.ADD,
                                            style=ft.ButtonStyle(
                                                bgcolor=colors.primary_600,
                                                color=ft.Colors.WHITE,
                                            ),
                                        ),
                                    ],
                                    spacing=SPACING.lg,
                                ),
                                padding=ft.Padding(SPACING.xxl, SPACING.lg, SPACING.xxl, SPACING.lg),
                                bgcolor=colors.surface_card,
                                border=ft.border.only(bottom=ft.BorderSide(1, colors.surface_border)),
                            ),
                            # Page content
                            ft.Container(
                                content=ft.Column(
                                    [
                                        # Hero
                                        create_hero_section(state, colors),
                                        # Quick actions
                                        create_quick_actions(colors),
                                        # Bento grid
                                        ft.Row(
                                            [
                                                create_ai_insight_card(colors),
                                                create_sources_to_code(state, colors),
                                            ],
                                            spacing=SPACING.xl,
                                        ),
                                        ft.Row(
                                            [
                                                create_code_frequency(state, colors),
                                                create_activity_feed(state, colors),
                                            ],
                                            spacing=SPACING.xl,
                                        ),
                                    ],
                                    spacing=SPACING.xl,
                                    scroll=ft.ScrollMode.AUTO,
                                ),
                                padding=ft.Padding(SPACING.xxl, SPACING.xxl, SPACING.xxl, SPACING.xxl),
                                expand=True,
                            ),
                        ],
                        spacing=0,
                    ),
                    bgcolor=colors.surface_ground,
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )

    page.bgcolor = colors.surface_ground
    page.add(build_ui())


if __name__ == "__main__":
    ft.app(target=main)
