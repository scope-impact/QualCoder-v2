"""
QualCoder v2 - Flet Dashboard POC

Proof-of-concept implementation of the dashboard mockup using Flet.
This demonstrates how the EventBus architecture integrates with Flet.

Compatible with Flet 0.80+

Run: uv run python dashboard.py
"""

import flet as ft
import random

from tokens import TYPOGRAPHY, SPACING, RADIUS, get_colors
from event_bus import EventBus, CodeCreated, CodeDeleted, SegmentCoded, SourceImported
from signal_bridge import FletSignalBridge, ActivityItem


class DashboardState:
    """
    Reactive state container for the dashboard.
    In a real app, this would be populated from repositories.
    """

    def __init__(self):
        self.user_name = "Jane"
        self.project_name = "remote work"
        self.sources_count = 24
        self.codes_count = 156
        self.segments_count = 892
        self.completion_percent = 68

        self.codes = [
            {"id": 1, "name": "Work-life balance", "count": 45, "color": "#3d7a63"},
            {"id": 2, "name": "Remote challenges", "count": 38, "color": "#e07356"},
            {"id": 3, "name": "Team collaboration", "count": 32, "color": "#7d9a8a"},
            {"id": 4, "name": "Meeting fatigue", "count": 25, "color": "#c9a9a6"},
            {"id": 5, "name": "Flexibility benefits", "count": 21, "color": "#6d28d9"},
        ]

        self.activities: list[dict] = [
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
        ]

        self.sources_to_code = [
            {"id": 1, "name": "Interview_P12.txt", "words": 2450, "progress": 0, "status": "Not started"},
            {"id": 2, "name": "Focus_Group_2.txt", "words": 4120, "progress": 35, "status": "35% coded"},
            {"id": 3, "name": "Survey_OpenEnd.txt", "words": 1890, "progress": 72, "status": "72% coded"},
        ]

        self._next_code_id = 100
        self._next_source_id = 100

    def add_code(self, name: str, color: str) -> int:
        """Add a new code and return its ID."""
        code_id = self._next_code_id
        self._next_code_id += 1
        self.codes.insert(0, {"id": code_id, "name": name, "count": 0, "color": color})
        self.codes_count += 1
        return code_id

    def delete_code(self, code_id: int) -> str | None:
        """Delete a code by ID, return its name."""
        for i, code in enumerate(self.codes):
            if code["id"] == code_id:
                name = code["name"]
                self.codes.pop(i)
                self.codes_count -= 1
                return name
        return None

    def add_segment(self, code_id: int) -> None:
        """Increment segment count for a code."""
        for code in self.codes:
            if code["id"] == code_id:
                code["count"] += 1
                self.segments_count += 1
                break

    def add_source(self, name: str, words: int) -> int:
        """Add a new source."""
        source_id = self._next_source_id
        self._next_source_id += 1
        self.sources_to_code.insert(0, {
            "id": source_id,
            "name": name,
            "words": words,
            "progress": 0,
            "status": "Not started"
        })
        self.sources_count += 1
        return source_id

    def add_activity(self, text: str, color: str) -> None:
        """Add an activity to the feed."""
        self.activities.insert(0, {
            "text": text,
            "time": "Just now",
            "color": color,
        })
        # Keep only last 10 activities
        self.activities = self.activities[:10]

    def get_top_codes(self, limit: int = 5) -> list[dict]:
        """Get top codes by count."""
        sorted_codes = sorted(self.codes, key=lambda c: c["count"], reverse=True)
        return sorted_codes[:limit]


class Dashboard(ft.Column):
    """
    Main Dashboard component with EventBus integration.

    This demonstrates the pattern:
    1. EventBus publishes domain events
    2. FletSignalBridge receives events and calls callbacks
    3. Callbacks update state and trigger UI rebuild
    """

    def __init__(self, event_bus: EventBus, bridge: FletSignalBridge):
        super().__init__()
        self.event_bus = event_bus
        self.bridge = bridge
        self.state = DashboardState()
        self.dark_mode = False
        self.colors = get_colors(self.dark_mode)

        # Wire up bridge callbacks
        self.bridge.on_code_created = self._on_code_created
        self.bridge.on_code_deleted = self._on_code_deleted
        self.bridge.on_segment_coded = self._on_segment_coded
        self.bridge.on_source_imported = self._on_source_imported
        self.bridge.on_activity = self._on_activity

        self.expand = True
        self.spacing = 0

    def did_mount(self):
        """Called when component is mounted."""
        self.bridge.bind_page(self.page)
        self.bridge.start()
        self._rebuild()

    def will_unmount(self):
        """Called when component is unmounted."""
        self.bridge.stop()

    def _on_code_created(self, event: CodeCreated) -> None:
        """Handle code created event."""
        self.state.add_code(event.name, event.color)

    def _on_code_deleted(self, event: CodeDeleted) -> None:
        """Handle code deleted event."""
        self.state.delete_code(event.code_id)

    def _on_segment_coded(self, event: SegmentCoded) -> None:
        """Handle segment coded event."""
        self.state.add_segment(event.code_id)

    def _on_source_imported(self, event: SourceImported) -> None:
        """Handle source imported event."""
        self.state.add_source(event.name, event.word_count)

    def _on_activity(self, activity: ActivityItem) -> None:
        """Handle activity event."""
        self.state.add_activity(activity.text, activity.color)
        self._rebuild()

    def _toggle_theme(self, e):
        """Toggle dark/light theme."""
        self.dark_mode = not self.dark_mode
        self.page.theme_mode = ft.ThemeMode.DARK if self.dark_mode else ft.ThemeMode.LIGHT
        self.colors = get_colors(self.dark_mode)
        self.page.bgcolor = self.colors.surface_ground
        self._rebuild()

    def _rebuild(self):
        """Rebuild the entire UI."""
        self.controls.clear()
        self.controls.append(self._build_ui())
        if self.page:
            self.page.update()

    def _create_code(self, e):
        """Demo: Create a new code via EventBus."""
        colors = ["#3d7a63", "#e07356", "#7d9a8a", "#6d28d9", "#c9a9a6", "#0369a1"]
        names = ["New Theme", "Emerging Pattern", "Key Insight", "Notable Quote", "Research Finding"]
        event = CodeCreated(
            code_id=random.randint(100, 999),
            name=random.choice(names),
            color=random.choice(colors),
        )
        self.event_bus.publish(event)

    def _import_source(self, e):
        """Demo: Import a source via EventBus."""
        names = ["Interview_P15.txt", "Focus_Group_3.txt", "Survey_Results.csv", "Field_Notes.txt"]
        event = SourceImported(
            source_id=random.randint(100, 999),
            name=random.choice(names),
            word_count=random.randint(1000, 5000),
        )
        self.event_bus.publish(event)

    def _apply_code(self, e):
        """Demo: Apply a code to a segment via EventBus."""
        if self.state.codes:
            code = random.choice(self.state.codes)
            sources = ["Interview_P08.txt", "Focus_Group_2.txt", "Survey_OpenEnd.txt"]
            event = SegmentCoded(
                segment_id=random.randint(1000, 9999),
                code_id=code["id"],
                code_name=code["name"],
                source_name=random.choice(sources),
                text_preview="Lorem ipsum dolor sit amet, consectetur adipiscing elit...",
            )
            self.event_bus.publish(event)

    def _build_ui(self):
        """Build the main UI layout."""
        return ft.Row(
            [
                self._build_sidebar(),
                ft.Container(
                    content=ft.Column(
                        [
                            self._build_header(),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        self._build_hero_section(),
                                        self._build_quick_actions(),
                                        ft.Row(
                                            [
                                                self._build_ai_insight_card(),
                                                self._build_sources_to_code(),
                                            ],
                                            spacing=SPACING.xl,
                                        ),
                                        ft.Row(
                                            [
                                                self._build_code_frequency(),
                                                self._build_activity_feed(),
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
                    bgcolor=self.colors.surface_ground,
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )

    def _build_sidebar(self):
        """Build the navigation sidebar."""

        def nav_item(icon: str, label: str, active: bool = False, badge: str | None = None):
            bg_color = self.colors.primary_700 if active else None
            text_color = self.colors.text_inverse if active else self.colors.text_secondary

            content = [
                ft.Icon(icon, size=20, color=text_color),
                ft.Text(label, size=TYPOGRAPHY.sm, color=text_color, expand=True),
            ]
            if badge:
                content.append(
                    ft.Container(
                        ft.Text(badge, size=10, color=self.colors.text_inverse),
                        bgcolor=self.colors.primary_500,
                        border_radius=RADIUS.full,
                        padding=ft.Padding(left=8, top=2, right=8, bottom=2),
                    )
                )

            return ft.Container(
                content=ft.Row(content, spacing=SPACING.md),
                padding=ft.Padding(left=SPACING.lg, top=SPACING.md, right=SPACING.lg, bottom=SPACING.md),
                border_radius=RADIUS.md,
                bgcolor=bg_color,
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
                                    ft.Text("Q", size=18, weight=ft.FontWeight.BOLD, color=self.colors.text_inverse),
                                    width=36,
                                    height=36,
                                    bgcolor=self.colors.primary_600,
                                    border_radius=RADIUS.md,
                                    alignment=ft.Alignment.CENTER,
                                ),
                                ft.Text("QualCoder", size=TYPOGRAPHY.lg, weight=ft.FontWeight.W_600, color=self.colors.text_primary),
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
                                    ft.Text("JD", size=12, color=self.colors.text_inverse),
                                    width=40,
                                    height=40,
                                    bgcolor=self.colors.primary_500,
                                    border_radius=RADIUS.full,
                                    alignment=ft.Alignment.CENTER,
                                ),
                                ft.Column(
                                    [
                                        ft.Text("Jane Doe", size=TYPOGRAPHY.sm, weight=ft.FontWeight.W_500, color=self.colors.text_primary),
                                        ft.Text("Lead Researcher", size=TYPOGRAPHY.xs, color=self.colors.text_tertiary),
                                    ],
                                    spacing=2,
                                ),
                            ],
                            spacing=SPACING.md,
                        ),
                        padding=ft.Padding(SPACING.xl, SPACING.lg, SPACING.xl, SPACING.lg),
                    ),
                    ft.Divider(height=1, color=self.colors.surface_border),
                    # Navigation
                    ft.Container(
                        ft.Column(
                            [
                                ft.Text("WORKSPACE", size=10, color=self.colors.text_muted, weight=ft.FontWeight.W_600),
                                nav_item(ft.Icons.DASHBOARD_OUTLINED, "Dashboard", active=True),
                                nav_item(ft.Icons.DESCRIPTION_OUTLINED, "Sources", badge=str(self.state.sources_count)),
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
                                ft.Text("ANALYSIS", size=10, color=self.colors.text_muted, weight=ft.FontWeight.W_600),
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
            bgcolor=self.colors.surface_card,
            border=ft.border.only(right=ft.BorderSide(1, self.colors.surface_border)),
        )

    def _build_header(self):
        """Build the header bar."""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Text("Dashboard", size=TYPOGRAPHY.xl, weight=ft.FontWeight.W_600, color=self.colors.text_primary),
                    ft.Container(expand=True),
                    ft.TextField(
                        hint_text="Search codes, sources, cases... (Ctrl+K)",
                        width=400,
                        height=40,
                        border_radius=RADIUS.md,
                        content_padding=ft.Padding(SPACING.lg, 0, SPACING.lg, 0),
                    ),
                    ft.IconButton(
                        ft.Icons.DARK_MODE if not self.dark_mode else ft.Icons.LIGHT_MODE,
                        on_click=self._toggle_theme,
                    ),
                    ft.Button(
                        "Import",
                        icon=ft.Icons.ADD,
                        on_click=self._import_source,
                        style=ft.ButtonStyle(
                            bgcolor=self.colors.primary_600,
                            color=ft.Colors.WHITE,
                        ),
                    ),
                ],
                spacing=SPACING.lg,
            ),
            padding=ft.Padding(SPACING.xxl, SPACING.lg, SPACING.xxl, SPACING.lg),
            bgcolor=self.colors.surface_card,
            border=ft.border.only(bottom=ft.BorderSide(1, self.colors.surface_border)),
        )

    def _build_hero_section(self):
        """Build the hero section with welcome message and stats."""

        def stat_item(value: str, label: str):
            return ft.Column(
                [
                    ft.Text(value, size=TYPOGRAPHY.xxl, weight=ft.FontWeight.W_500, color=self.colors.text_primary),
                    ft.Text(label, size=TYPOGRAPHY.xs, color=self.colors.text_tertiary),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=SPACING.xs,
            )

        return ft.Container(
            content=ft.Stack(
                [
                    ft.Container(
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment.TOP_LEFT,
                            end=ft.Alignment.BOTTOM_RIGHT,
                            colors=[self.colors.primary_700, self.colors.primary_900],
                        ),
                        border_radius=RADIUS.xxl,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(
                                            f"Good afternoon, {self.state.user_name}",
                                            size=TYPOGRAPHY.sm,
                                            color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
                                            weight=ft.FontWeight.W_500,
                                        ),
                                        ft.Text(
                                            f"Your research on {self.state.project_name} is progressing well",
                                            size=TYPOGRAPHY.xxxl,
                                            color=ft.Colors.WHITE,
                                            weight=ft.FontWeight.W_300,
                                        ),
                                        ft.Text(
                                            f"You've coded {self.state.segments_count} segments across {self.state.sources_count} sources. "
                                            f"You have {self.state.codes_count} codes defined.",
                                            size=TYPOGRAPHY.lg,
                                            color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
                                        ),
                                        ft.Row(
                                            [
                                                ft.Button(
                                                    "Continue Coding",
                                                    icon=ft.Icons.CODE,
                                                    on_click=self._apply_code,
                                                    style=ft.ButtonStyle(
                                                        bgcolor=ft.Colors.WHITE,
                                                        color=self.colors.primary_700,
                                                    ),
                                                ),
                                                ft.Button(
                                                    "Create Code",
                                                    icon=ft.Icons.ADD,
                                                    on_click=self._create_code,
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
                                ft.Container(
                                    content=ft.Row(
                                        [
                                            stat_item(str(self.state.sources_count), "Sources"),
                                            ft.VerticalDivider(width=1, color=self.colors.surface_border),
                                            stat_item(str(self.state.codes_count), "Codes"),
                                            ft.VerticalDivider(width=1, color=self.colors.surface_border),
                                            stat_item(str(self.state.segments_count), "Segments"),
                                            ft.VerticalDivider(width=1, color=self.colors.surface_border),
                                            stat_item(f"{self.state.completion_percent}%", "Complete"),
                                        ],
                                        spacing=SPACING.xl,
                                    ),
                                    bgcolor=self.colors.surface_card,
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

    def _build_quick_actions(self):
        """Build the quick actions grid."""
        actions = [
            {"icon": ft.Icons.ADD_CIRCLE_OUTLINE, "title": "Import Sources", "desc": "Add new documents to analyze", "color": self.colors.primary_500, "action": self._import_source},
            {"icon": ft.Icons.CODE, "title": "Apply Code", "desc": "Apply codes to segments", "color": self.colors.accent_500, "action": self._apply_code},
            {"icon": ft.Icons.AUTO_AWESOME, "title": "Create Code", "desc": "Create a new code", "color": self.colors.sage_400, "action": self._create_code},
            {"icon": ft.Icons.INSIGHTS, "title": "View Insights", "desc": "Analyze patterns in your data", "color": self.colors.rose_400, "action": None},
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
                        ft.Text(action["title"], size=TYPOGRAPHY.sm, weight=ft.FontWeight.W_600, color=self.colors.text_primary),
                        ft.Text(action["desc"], size=TYPOGRAPHY.xs, color=self.colors.text_tertiary),
                    ],
                    spacing=SPACING.lg,
                ),
                padding=ft.Padding(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl),
                bgcolor=self.colors.surface_paper,
                border=ft.border.all(1, self.colors.surface_border),
                border_radius=RADIUS.xl,
                on_click=action["action"],
                ink=True,
                expand=True,
            )

        return ft.Row([action_card(a) for a in actions], spacing=SPACING.lg)

    def _build_code_frequency(self):
        """Build the code frequency chart."""
        top_codes = self.state.get_top_codes(5)
        max_count = max(c["count"] for c in top_codes) if top_codes else 1

        def code_bar(code):
            percent = int((code["count"] / max_count) * 100)
            return ft.Row(
                [
                    ft.Container(
                        ft.Text(code["name"], size=TYPOGRAPHY.sm, color=self.colors.text_secondary, text_align=ft.TextAlign.RIGHT),
                        width=120,
                    ),
                    ft.Container(
                        ft.Container(
                            bgcolor=code["color"],
                            border_radius=RADIUS.md,
                            width=f"{percent}%",
                            height=32,
                        ),
                        bgcolor=self.colors.surface_paper,
                        border_radius=RADIUS.md,
                        expand=True,
                        height=32,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    ),
                    ft.Text(str(code["count"]), size=TYPOGRAPHY.sm, weight=ft.FontWeight.W_500, color=self.colors.text_primary, width=40),
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
                                    ft.Text("Most Used Codes", size=TYPOGRAPHY.sm, weight=ft.FontWeight.W_600, color=self.colors.text_primary),
                                    ft.Text("Top 5 by frequency", size=TYPOGRAPHY.xs, color=self.colors.text_muted),
                                ],
                                spacing=SPACING.xs,
                            ),
                            ft.TextButton("See all", style=ft.ButtonStyle(color=self.colors.text_tertiary)),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Column([code_bar(c) for c in top_codes], spacing=SPACING.md),
                ],
                spacing=SPACING.xl,
            ),
            padding=ft.Padding(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl),
            bgcolor=self.colors.surface_card,
            border=ft.border.all(1, self.colors.surface_border),
            border_radius=RADIUS.xl,
            expand=True,
        )

    def _build_activity_feed(self):
        """Build the recent activity feed."""
        color_map = {
            "primary": self.colors.primary_400,
            "accent": self.colors.accent_400,
            "sage": self.colors.sage_400,
            "rose": self.colors.rose_400,
        }

        def activity_item(activity):
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            width=10,
                            height=10,
                            bgcolor=color_map.get(activity["color"], self.colors.primary_400),
                            border_radius=RADIUS.full,
                        ),
                        ft.Column(
                            [
                                ft.Text(activity["text"], size=TYPOGRAPHY.sm, color=self.colors.text_secondary),
                                ft.Text(activity["time"], size=TYPOGRAPHY.xs, color=self.colors.text_muted),
                            ],
                            spacing=SPACING.xs,
                            expand=True,
                        ),
                    ],
                    spacing=SPACING.lg,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                padding=ft.Padding(0, SPACING.lg, 0, SPACING.lg),
                border=ft.border.only(bottom=ft.BorderSide(1, self.colors.surface_border_subtle)),
            )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text("Recent Activity", size=TYPOGRAPHY.sm, weight=ft.FontWeight.W_600, color=self.colors.text_primary),
                                    ft.Text("Your coding timeline", size=TYPOGRAPHY.xs, color=self.colors.text_muted),
                                ],
                                spacing=SPACING.xs,
                            ),
                            ft.TextButton("View all", style=ft.ButtonStyle(color=self.colors.text_tertiary)),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Column([activity_item(a) for a in self.state.activities[:5]], spacing=0),
                ],
                spacing=SPACING.xl,
            ),
            padding=ft.Padding(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl),
            bgcolor=self.colors.surface_card,
            border=ft.border.all(1, self.colors.surface_border),
            border_radius=RADIUS.xl,
            expand=True,
        )

    def _build_ai_insight_card(self):
        """Build the AI insight card."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        ft.Row(
                            [
                                ft.Container(width=6, height=6, bgcolor=self.colors.accent_500, border_radius=RADIUS.full),
                                ft.Text("AI Insight", size=TYPOGRAPHY.xs, weight=ft.FontWeight.W_600, color=self.colors.accent_700),
                            ],
                            spacing=SPACING.sm,
                        ),
                        bgcolor=self.colors.accent_100,
                        border_radius=RADIUS.full,
                        padding=ft.Padding(SPACING.md, SPACING.xs, SPACING.md, SPACING.xs),
                    ),
                    ft.Text(
                        "Strong thematic connection discovered",
                        size=TYPOGRAPHY.lg,
                        weight=ft.FontWeight.W_500,
                        color=self.colors.text_primary,
                    ),
                    ft.Text(
                        '"Work-life balance" and "remote challenges" co-occur in 68% of cases. '
                        "Consider creating a parent category to group these related codes.",
                        size=TYPOGRAPHY.base,
                        color=self.colors.text_secondary,
                    ),
                    ft.Row(
                        [
                            ft.Button(
                                "Create Theme",
                                icon=ft.Icons.ADD,
                                on_click=self._create_code,
                                style=ft.ButtonStyle(bgcolor=self.colors.accent_500, color=ft.Colors.WHITE),
                            ),
                            ft.Button(
                                "View Co-occurrences",
                                style=ft.ButtonStyle(side=ft.BorderSide(1, self.colors.surface_border), bgcolor=ft.Colors.TRANSPARENT),
                            ),
                            ft.TextButton("Dismiss", style=ft.ButtonStyle(color=self.colors.text_muted)),
                        ],
                        spacing=SPACING.md,
                    ),
                ],
                spacing=SPACING.lg,
            ),
            padding=ft.Padding(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl),
            bgcolor=ft.Colors.with_opacity(0.08, self.colors.accent_400),
            border=ft.border.all(1, self.colors.accent_200),
            border_radius=RADIUS.xl,
            expand=2,
        )

    def _build_sources_to_code(self):
        """Build the sources to code list."""

        def source_item(source):
            progress_color = self.colors.stone_300 if source["progress"] == 0 else self.colors.primary_500
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=20, color=self.colors.text_tertiary),
                            width=44,
                            height=44,
                            bgcolor=self.colors.surface_paper,
                            border=ft.border.all(1, self.colors.surface_border),
                            border_radius=RADIUS.lg,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Column(
                            [
                                ft.Text(source["name"], size=TYPOGRAPHY.sm, weight=ft.FontWeight.W_500, color=self.colors.text_primary),
                                ft.Text(f"{source['words']:,} words - {source['status']}", size=TYPOGRAPHY.xs, color=self.colors.text_muted),
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
                            bgcolor=self.colors.surface_paper,
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
                                    ft.Text("Sources to Code", size=TYPOGRAPHY.sm, weight=ft.FontWeight.W_600, color=self.colors.text_primary),
                                    ft.Text(f"{len(self.state.sources_to_code)} files need attention", size=TYPOGRAPHY.xs, color=self.colors.text_muted),
                                ],
                                spacing=SPACING.xs,
                            ),
                            ft.TextButton("View all", style=ft.ButtonStyle(color=self.colors.text_tertiary)),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Column([source_item(s) for s in self.state.sources_to_code[:3]], spacing=SPACING.sm),
                ],
                spacing=SPACING.xl,
            ),
            padding=ft.Padding(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl),
            bgcolor=self.colors.surface_card,
            border=ft.border.all(1, self.colors.surface_border),
            border_radius=RADIUS.xl,
            expand=True,
        )


def main(page: ft.Page):
    """Main entry point for the Flet dashboard."""

    # Page configuration
    page.title = "QualCoder v2 - Dashboard (Flet POC)"
    page.padding = 0
    page.spacing = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = get_colors(False).surface_ground

    # Create EventBus and Signal Bridge
    event_bus = EventBus()
    bridge = FletSignalBridge(event_bus=event_bus)

    # Create dashboard with EventBus integration
    dashboard = Dashboard(event_bus=event_bus, bridge=bridge)

    page.add(dashboard)


if __name__ == "__main__":
    ft.app(target=main)
