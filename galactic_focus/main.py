# Copyright 2026 Guillaume Pons
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Galactic Focus V5.0 - Cyberpunk Synthwave & Nova Mission Command Center.
Features clean navigation rail, rich CRT tactical deck, and smooth micro-interactions.
"""
import sys
import os
from pathlib import Path

# Add project root to sys.path if running directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import flet as ft

from galactic_focus.core.storage import StorageManager
from galactic_focus.core.models import Ship
from galactic_focus.ui.cockpit_view import CockpitView
from galactic_focus.ui.missions_view import MissionsView
from galactic_focus.ui.hangar_view import HangarView
from galactic_focus.ui.theme import (
    BG_DEEP_SPACE, BG_DEEP_SPACE_ALT, BG_SIDEBAR, BG_PANEL, BG_PANEL_HOVER, BG_CARD_INNER, BORDER_CYBER,
    NEON_CYAN, NEON_ICE, NEON_GREEN, NEON_AMBER, NEON_PURPLE, NEON_MAGENTA,
    TEXT_TITLE, TEXT_SUBTITLE, TEXT_BODY, TEXT_MUTED, TEXT_CYAN, FONT_HEADER, FONT_BODY,
    sci_fi_button, get_asset_path
)


def main(page: ft.Page):
    # Window & Page Configuration
    page.title = "🪐 NOVA GALACTIC FOCUS // MISSION COMMAND CENTER"
    page.bgcolor = BG_DEEP_SPACE
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0

    # Explicit Window Geometry (1260x860, min 1080x680) with headless/mock guards
    if hasattr(page, "window") and page.window:
        try:
            page.window.width = 1260
            page.window.height = 860
            page.window.min_width = 1080
            page.window.min_height = 680
        except Exception:
            pass

    # Set Window Icon dynamically (for title bar & taskbar)
    if hasattr(page, "window") and page.window:
        try:
            base_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
            for ic in [
                base_dir / "galactic_focus" / "assets" / "icon.png",
                base_dir / "galactic_focus" / "assets" / "icon.ico",
                Path(__file__).resolve().parent / "assets" / "icon.png",
                Path(__file__).resolve().parent / "assets" / "icon.ico",
                base_dir / "icon.png",
                base_dir / "icon.ico",
            ]:
                if ic.exists():
                    page.window.icon = str(ic)
                    break
        except Exception:
            pass

    storage = StorageManager()

    # Callback when data changes in any view to keep everything synchronized
    def on_data_changed():
        missions_view.refresh()
        hangar_view.refresh()
        cockpit_view.reload_fleet()
        _update_sidebar_badges()

    def on_launch_ship_from_board(ship: Ship, mission: Optional[Mission] = None):
        cockpit_view.load_mission(ship, mission)
        switch_tab("cockpit")

    cockpit_view = CockpitView(page, storage, on_data_changed=on_data_changed)
    missions_view = MissionsView(
        page,
        storage,
        on_data_changed=on_data_changed,
        on_launch_ship=on_launch_ship_from_board,
    )
    hangar_view = HangarView(page, storage, on_data_changed=on_data_changed)

    # Active view container
    active_content = ft.Container(
        content=cockpit_view.get_view(),
        expand=True,
    )

    current_tab = ["cockpit"]

    # Top Breadcrumb Text
    breadcrumb_text = ft.Text(
        "COMMAND CENTER  ›  OVERVIEW",
        size=12,
        weight=ft.FontWeight.W_700,
        color=TEXT_SUBTITLE,
        font_family=FONT_HEADER,
    )

    def switch_tab(tab_name: str):
        current_tab[0] = tab_name

        # Reset all sidebar items
        for item in [nav_item_cockpit, nav_item_missions, nav_item_hangar]:
            item.bgcolor = "transparent"
            item.border = None
            item.shadow = None
            item.content.controls[0].color = TEXT_MUTED
            item.content.controls[1].color = TEXT_MUTED
            item.content.controls[1].weight = ft.FontWeight.NORMAL

        active_shadow = [
            ft.BoxShadow(
                spread_radius=1,
                blur_radius=12,
                color=f"{NEON_CYAN}26",
                offset=ft.Offset(0, 2),
            )
        ]

        if tab_name == "cockpit":
            cockpit_view.reload_fleet()
            active_content.content = cockpit_view.get_view()
            breadcrumb_text.value = "COMMAND CENTER  ›  OVERVIEW"
            nav_item_cockpit.bgcolor = f"{NEON_CYAN}18"
            nav_item_cockpit.border = ft.Border.all(1, f"{NEON_CYAN}55")
            nav_item_cockpit.shadow = active_shadow
            nav_item_cockpit.content.controls[0].color = NEON_CYAN
            nav_item_cockpit.content.controls[1].color = TEXT_TITLE
            nav_item_cockpit.content.controls[1].weight = ft.FontWeight.W_700

        elif tab_name == "missions":
            missions_view.refresh()
            active_content.content = missions_view.get_view()
            breadcrumb_text.value = "COMMAND CENTER  ›  CAMPAIGNS & DIRECTIVES"
            nav_item_missions.bgcolor = f"{NEON_CYAN}18"
            nav_item_missions.border = ft.Border.all(1, f"{NEON_CYAN}55")
            nav_item_missions.shadow = active_shadow
            nav_item_missions.content.controls[0].color = NEON_CYAN
            nav_item_missions.content.controls[1].color = TEXT_TITLE
            nav_item_missions.content.controls[1].weight = ft.FontWeight.W_700

        elif tab_name == "hangar":
            hangar_view.refresh()
            active_content.content = hangar_view.get_view()
            breadcrumb_text.value = "COMMAND CENTER  ›  SPACEDOCK & FLEET"
            nav_item_hangar.bgcolor = f"{NEON_CYAN}18"
            nav_item_hangar.border = ft.Border.all(1, f"{NEON_CYAN}55")
            nav_item_hangar.shadow = active_shadow
            nav_item_hangar.content.controls[0].color = NEON_CYAN
            nav_item_hangar.content.controls[1].color = TEXT_TITLE
            nav_item_hangar.content.controls[1].weight = ft.FontWeight.W_700

        _update_sidebar_badges()
        page.update()

    # Sidebar Badge Counters
    missions_count_badge = ft.Container(
        content=ft.Text(
            str(len([m for m in storage.get_missions() if not m.is_completed])),
            size=10,
            weight=ft.FontWeight.BOLD,
            color="#030712",
            font_family=FONT_HEADER,
        ),
        padding=ft.Padding.symmetric(horizontal=7, vertical=2),
        bgcolor=NEON_CYAN,
        border_radius=4,
        shadow=[ft.BoxShadow(spread_radius=1, blur_radius=6, color=f"{NEON_CYAN}66")],
    )

    fleet_count_badge = ft.Container(
        content=ft.Text(
            str(len(storage.get_ships(include_retired=False))),
            size=10,
            weight=ft.FontWeight.BOLD,
            color="#FFFFFF",
            font_family=FONT_HEADER,
        ),
        padding=ft.Padding.symmetric(horizontal=7, vertical=2),
        bgcolor=f"{NEON_PURPLE}99",
        border_radius=4,
        shadow=[ft.BoxShadow(spread_radius=1, blur_radius=6, color=f"{NEON_PURPLE}44")],
    )

    def _update_sidebar_badges():
        active_m = len([m for m in storage.get_missions() if not m.is_completed])
        missions_count_badge.content.value = str(active_m)
        missions_count_badge.visible = (active_m > 0)

        active_ships_cnt = len(storage.get_ships(include_retired=False))
        fleet_count_badge.content.value = str(active_ships_cnt)

    # Sidebar Nav Items (Styled like Nova Workspace Rail)
    def make_nav_item(label: str, icon, tab_key: str, badge_ctrl=None):
        is_active = (current_tab[0] == tab_key)
        controls = [
            ft.Icon(icon, color=NEON_CYAN if is_active else TEXT_MUTED, size=18),
            ft.Text(
                label,
                size=12,
                weight=ft.FontWeight.W_700 if is_active else ft.FontWeight.NORMAL,
                color=TEXT_TITLE if is_active else TEXT_MUTED,
                font_family=FONT_HEADER,
            ),
        ]
        if badge_ctrl:
            controls.append(ft.Container(expand=True))
            controls.append(badge_ctrl)

        item = ft.Container(
            content=ft.Row(
                controls,
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            border_radius=6,
            bgcolor=f"{NEON_CYAN}18" if is_active else "transparent",
            border=ft.Border.all(1, f"{NEON_CYAN}55") if is_active else None,
            shadow=[ft.BoxShadow(spread_radius=1, blur_radius=12, color=f"{NEON_CYAN}26", offset=ft.Offset(0, 2))] if is_active else None,
            on_click=lambda e, k=tab_key: switch_tab(k),
            animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
            ink=True,
        )
        return item

    nav_item_cockpit = make_nav_item("Cockpit / Overview", ft.Icons.GRID_VIEW_ROUNDED, "cockpit")
    nav_item_missions = make_nav_item("Missions & Directives", ft.Icons.TRACK_CHANGES_ROUNDED, "missions", missions_count_badge)
    nav_item_hangar = make_nav_item("Hangar & Flotte", ft.Icons.SHIELD_ROUNDED, "hangar", fleet_count_badge)

    # Left Sidebar Column
    sidebar = ft.Container(
        content=ft.Column(
            [
                # Brand Logo
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text("🪐", size=20),
                            padding=6,
                            bgcolor=f"{NEON_CYAN}22",
                            border=ft.Border.all(1, NEON_CYAN),
                            border_radius=6,
                            shadow=[ft.BoxShadow(spread_radius=1, blur_radius=10, color=f"{NEON_CYAN}55")],
                        ),
                        ft.Column(
                            [
                                ft.Text("NOVA FOCUS", size=15, weight=ft.FontWeight.W_900, color=TEXT_TITLE, font_family=FONT_HEADER),
                                ft.Text("COMMAND // V5.0", size=9, weight=ft.FontWeight.W_600, color=TEXT_CYAN, font_family=FONT_HEADER),
                            ],
                            spacing=0,
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=16),
                ft.Text("NAVIGATION", size=10, weight=ft.FontWeight.BOLD, color=TEXT_MUTED, font_family=FONT_HEADER),
                ft.Container(height=4),
                nav_item_cockpit,
                nav_item_missions,
                nav_item_hangar,
                ft.Container(expand=True),
            ],
            spacing=4,
        ),
        width=230,
        bgcolor=BG_SIDEBAR,
        padding=ft.Padding.all(16),
        border=ft.Border.only(right=ft.BorderSide(1, BORDER_CYBER)),
    )

    # Top Header Bar (Breadcrumbs + Live Status Beacon)
    top_header = ft.Container(
        content=ft.Row(
            [
                breadcrumb_text,
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(
                                width=6,
                                height=6,
                                bgcolor=NEON_GREEN,
                                border_radius=3,
                                shadow=[ft.BoxShadow(spread_radius=1, blur_radius=6, color=NEON_GREEN)],
                            ),
                            ft.Text("SYS // ORBITAL NOMINAL", size=11, weight=ft.FontWeight.W_700, color=TEXT_BODY, font_family=FONT_HEADER),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                    bgcolor=BG_PANEL,
                    border=ft.Border.all(1, BORDER_CYBER),
                    border_radius=6,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=24, vertical=12),
        bgcolor=BG_DEEP_SPACE,
        border=ft.Border.only(bottom=ft.BorderSide(1, BORDER_CYBER)),
    )

    # Main App Layout (Sidebar + Top Bar + Responsive Content Deck)
    page.add(
        ft.Row(
            [
                sidebar,
                ft.Column(
                    [
                        top_header,
                        active_content,
                    ],
                    expand=True,
                    spacing=0,
                ),
            ],
            expand=True,
            spacing=0,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)

