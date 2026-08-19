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
Hangar view for Galactic Focus V5.0: Nova Spacedock & Fleet Maintenance.
Cyberpunk Synthwave & Nova Space Command Center aesthetics:
Interactive telemetry KPI cards, armed fleet docking bay with flagship protection,
scrap archives (au rebut) with 1-click rearm/restore & delete, and filterable maintenance
logbook with 1-click UTF-8-BOM CSV export.
"""
import os
import flet as ft
from typing import Callable, Optional
from datetime import datetime

from ..core.models import Ship, FocusSession
from ..core.storage import StorageManager
from .theme import (
    BG_DEEP_SPACE, BG_DEEP_SPACE_ALT, BG_PANEL, BG_PANEL_HOVER, BG_CARD_INNER,
    BORDER_CYBER, BORDER_CYBER_LIGHT, BORDER_GLOW_CYAN, BORDER_GLOW_AMBER, BORDER_GLOW_PURPLE,
    NEON_CYAN, NEON_ICE, NEON_GREEN, NEON_AMBER, NEON_ORANGE, NEON_PURPLE, NEON_MAGENTA, NEON_RED, NEON_GOLD,
    TEXT_TITLE, TEXT_SUBTITLE, TEXT_BODY, TEXT_MUTED, TEXT_CYAN, TEXT_AMBER, TEXT_GREEN, TEXT_MAGENTA, TEXT_PURPLE,
    FONT_HEADER, FONT_BODY, FONT_NUM,
    SHIP_COLORS, SHIP_ICONS,
    interactive_card, sci_fi_button, get_asset_path
)


class HangarView:
    def __init__(self, page: ft.Page, storage: StorageManager, on_data_changed: Optional[Callable] = None):
        self.page = page
        self.storage = storage
        self.on_data_changed = on_data_changed

        self.selected_ship_filter = "ALL"
        self.container = ft.Container(expand=True)
        self.refresh()

    def refresh(self):
        """Rebuilds the entire hangar, fleet ships, archives (au rebut), and maintenance log."""
        stats = self.storage.get_global_stats()
        active_ships = self.storage.get_ships(include_retired=False)
        retired_ships = self.storage.get_retired_ships()
        sessions = self.storage.get_sessions(limit=100)

        # 1. Telemetry KPI Cards
        kpi_row = ft.Row(
            [
                self._build_kpi_card(
                    "TEMPS DE VOL TOTAL",
                    stats["formatted_total_time"],
                    "+18.5k kph",
                    ft.Icons.FLIGHT_TAKEOFF_ROUNDED,
                    NEON_CYAN,
                ),
                self._build_kpi_card(
                    "FLOTTE EN SERVICE",
                    f"{len(active_ships)}",
                    "Appareillés & prêts",
                    ft.Icons.ROCKET_LAUNCH_ROUNDED,
                    NEON_GREEN,
                ),
                self._build_kpi_card(
                    "AU REBUT / ARCHIVES",
                    f"{len(retired_ships)}",
                    "Projets finis",
                    ft.Icons.INVENTORY_2_ROUNDED,
                    NEON_PURPLE if len(retired_ships) > 0 else TEXT_MUTED,
                ),
                self._build_kpi_card(
                    "SORTIES RÉUSSIES",
                    f"{stats['total_sessions']}",
                    "Vols spatiaux",
                    ft.Icons.EXPLORE_ROUNDED,
                    NEON_AMBER,
                ),
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # 2. Active Fleet Section (Vaisseaux en Service)
        total_active_sec = max(1, sum(s.total_seconds for s in active_ships))
        active_ship_cards = []
        for ship in active_ships:
            active_ship_cards.append(self._build_active_ship_card(ship, total_active_sec))

        # Build ship cards grid: 2 cards per row (no wrap=True to avoid Flutter Wrap layout issue inside scrollable Column)
        if active_ship_cards:
            card_rows = []
            for i in range(0, len(active_ship_cards), 2):
                chunk = active_ship_cards[i : i + 2]
                card_rows.append(ft.Row(chunk, spacing=12))
            ships_grid = ft.Column(card_rows, spacing=12)
        else:
            ships_grid = interactive_card(
                ft.Column(
                    [
                        ft.Icon(ft.Icons.ROCKET_OUTLINED, size=32, color=TEXT_MUTED),
                        ft.Text("// AUCUN VAISSEAU ACTIF //", size=12, color=TEXT_MUTED, font_family=FONT_HEADER),
                        ft.Container(height=4),
                        sci_fi_button(
                            "+ Appareiller un vaisseau",
                            icon=ft.Icons.ROCKET_ROUNDED,
                            on_click=self._open_new_ship_dialog,
                            width=200,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                ),
                padding=20,
                expand=True,
            )

        active_fleet_section = ft.Column(
            [
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    width=8,
                                    height=8,
                                    bgcolor=NEON_CYAN,
                                    border_radius=4,
                                    shadow=[ft.BoxShadow(spread_radius=1, blur_radius=8, color=NEON_CYAN)],
                                ),
                                ft.Text("FLOTTE EN SERVICE ACTIF // BAIE DE DOCKING", size=14, weight=ft.FontWeight.BOLD, color=TEXT_TITLE, font_family=FONT_HEADER),
                                ft.Container(
                                    content=ft.Text(f"{len(active_ships)} APPAREILLÉS", size=10, color=NEON_CYAN, weight=ft.FontWeight.BOLD, font_family=FONT_HEADER),
                                    padding=ft.Padding.symmetric(horizontal=7, vertical=2),
                                    bgcolor=f"{NEON_CYAN}18",
                                    border_radius=4,
                                    border=ft.Border.all(1, f"{NEON_CYAN}44"),
                                ),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        sci_fi_button(
                            "+ Appareiller un Nouveau Vaisseau",
                            icon=ft.Icons.ROCKET_ROUNDED,
                            color_neon=NEON_CYAN,
                            on_click=self._open_new_ship_dialog,
                            width=290,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=8),
                ships_grid,
            ],
            spacing=4,
        )


        # 3. Retired Ships Section (Vaisseaux au Rebut / Archives)
        retired_cards = []
        for r_ship in retired_ships:
            retired_cards.append(self._build_retired_ship_card(r_ship))

        retired_section_content = ft.Container()
        if retired_ships:
            # Build retired cards grid: 2 per row (no wrap=True to avoid Flutter layout crash)
            retired_rows = []
            for i in range(0, len(retired_cards), 2):
                chunk = retired_cards[i : i + 2]
                retired_rows.append(ft.Row(chunk, spacing=10))
            retired_grid = ft.Column(retired_rows, spacing=10)

            retired_section_content = interactive_card(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Row(
                                    [
                                        ft.Container(
                                            width=8,
                                            height=8,
                                            bgcolor=NEON_PURPLE,
                                            border_radius=4,
                                            shadow=[ft.BoxShadow(spread_radius=1, blur_radius=8, color=NEON_PURPLE)],
                                        ),
                                        ft.Text("ARCHIVES DU HANGAR // VAISSEAUX AU REBUT", size=13, weight=ft.FontWeight.BOLD, color=TEXT_TITLE, font_family=FONT_HEADER),
                                        ft.Container(
                                            content=ft.Text(f"{len(retired_ships)} ARCHIVÉS", size=10, color=NEON_PURPLE, weight=ft.FontWeight.BOLD, font_family=FONT_HEADER),
                                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                            bgcolor=f"{NEON_PURPLE}20",
                                            border_radius=4,
                                            border=ft.Border.all(1, f"{NEON_PURPLE}44"),
                                        ),
                                    ],
                                    spacing=8,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.Text("// PROJETS TERMINÉS & HISTORIQUE PRÉSERVÉ //", size=11, color=TEXT_MUTED, font_family=FONT_HEADER),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(height=8),
                        retired_grid,
                    ],
                    spacing=6,
                ),
                padding=16,
                hover_border_color=NEON_PURPLE,
            )

        # 4. Maintenance Logbook Section
        all_ships_list = self.storage.get_ships(include_retired=True)
        if self.selected_ship_filter == "ALL":
            filtered_sessions = sessions
        else:
            filtered_sessions = [s for s in sessions if s.ship_id == self.selected_ship_filter or s.project_id == self.selected_ship_filter]

        filter_options = [ft.dropdown.Option(key="ALL", text="Toute la Flotte (Tous les Vaisseaux)")]
        for s in all_ships_list:
            status_tag = " [AU REBUT]" if s.is_retired else (" [AMIRAL]" if s.is_flagship else "")
            filter_options.append(ft.dropdown.Option(key=s.id, text=f"{s.icon}  {s.name}{status_tag}"))

        self.maintenance_filter_dropdown = ft.Dropdown(
            value=self.selected_ship_filter,
            options=filter_options,
            on_select=self._on_maintenance_filter_changed,
            bgcolor=BG_CARD_INNER,
            border_color=BORDER_CYBER,
            color=TEXT_TITLE,
            width=290,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=6),
        )

        log_cards = []
        for s in filtered_sessions[:50]:
            log_cards.append(self._build_maintenance_entry_row(s))

        maintenance_section = interactive_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Container(
                                        width=8,
                                        height=8,
                                        bgcolor=NEON_AMBER,
                                        border_radius=4,
                                        shadow=[ft.BoxShadow(spread_radius=1, blur_radius=8, color=NEON_AMBER)],
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text("REGISTRE DE VOL & CARNET D'ENTRETIEN", size=13, weight=ft.FontWeight.BOLD, color=TEXT_TITLE, font_family=FONT_HEADER),
                                            ft.Text("Télémétrie des sorties, durées de vol et statut des avaries", size=10, color=TEXT_MUTED, font_family=FONT_BODY),
                                        ],
                                        spacing=1,
                                    ),
                                ],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Row(
                                [
                                    self.maintenance_filter_dropdown,
                                    sci_fi_button(
                                        "Exporter CSV",
                                        icon=ft.Icons.DOWNLOAD_ROUNDED,
                                        color_neon=NEON_CYAN,
                                        outlined=True,
                                        on_click=self._export_maintenance_csv,
                                        height=36,
                                    ),
                                ],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=6),
                    ft.Column(
                        log_cards if log_cards else [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Icon(ft.Icons.HISTORY_ROUNDED, size=28, color=TEXT_MUTED),
                                        ft.Text("// AUCUN ENREGISTREMENT DANS LE CARNET D'ENTRETIEN //", size=12, color=TEXT_MUTED, font_family=FONT_HEADER),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=4,
                                ),
                                padding=24,
                                alignment=ft.Alignment.CENTER,
                            )
                        ],
                        spacing=6,
                    ),
                ],
                spacing=6,
            ),
            padding=16,
            hover_border_color=NEON_AMBER,
        )

        # Assemble Full Scrollable Layout
        self.container.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("SPACEDOCK // FLEET & MAINTENANCE", size=24, weight=ft.FontWeight.BOLD, color=TEXT_TITLE, font_family=FONT_HEADER),
                                ft.Text("Supervision de la flotte spatiale, diagnostic technique et carnet d'entretien", size=12, color=TEXT_SUBTITLE),
                            ],
                            spacing=2,
                        ),
                    ],
                ),
                ft.Container(height=12),
                kpi_row,
                ft.Container(height=16),
                active_fleet_section,
                ft.Container(height=16) if retired_ships else ft.Container(height=0),
                retired_section_content if retired_ships else ft.Container(),
                ft.Container(height=16),
                maintenance_section,
                ft.Container(height=24),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        )

    def _build_kpi_card(self, title: str, value: str, sub_label: str, icon, color: str):
        return interactive_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Container(
                                        content=ft.Icon(icon, color=color, size=15),
                                        padding=6,
                                        bgcolor=f"{color}15",
                                        border_radius=6,
                                        border=ft.Border.all(1, f"{color}33"),
                                    ),
                                    ft.Text(title, size=10, weight=ft.FontWeight.W_700, color=TEXT_MUTED, font_family=FONT_HEADER),
                                ],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Container(
                                content=ft.Text(sub_label, size=9, weight=ft.FontWeight.BOLD, color=color, font_family=FONT_HEADER),
                                padding=ft.Padding.symmetric(horizontal=7, vertical=2),
                                bgcolor=f"{color}18",
                                border_radius=4,
                                border=ft.Border.all(1, f"{color}44"),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=8),
                    ft.Text(value, size=22, weight=ft.FontWeight.BOLD, color=TEXT_TITLE, font_family=FONT_HEADER),
                ],
                spacing=0,
            ),
            bgcolor=BG_PANEL,
            hover_border_color=color,
            padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            expand=True,
        )

    def _build_active_ship_card(self, ship: Ship, total_active_sec: int):
        ratio = min(1.0, max(0.0, ship.total_seconds / total_active_sec))
        pct = (ship.total_seconds / total_active_sec) * 100

        if ship.is_flagship:
            flagship_tag = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.SHIELD_ROUNDED, size=10, color="#030712"),
                        ft.Text("AMIRAL • GLOBAL", size=9, weight=ft.FontWeight.BOLD, color="#030712", font_family=FONT_HEADER),
                    ],
                    spacing=3,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=7, vertical=2),
                bgcolor=NEON_CYAN,
                border_radius=4,
                shadow=[ft.BoxShadow(spread_radius=1, blur_radius=8, color=f"{NEON_CYAN}66")],
            )
            actions_row = ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.EDIT_ROUNDED,
                        icon_color=TEXT_SUBTITLE,
                        icon_size=16,
                        tooltip="Personnaliser le Vaisseau Amiral",
                        on_click=lambda e, s=ship: self._open_edit_ship_dialog(s),
                    ),
                ],
                spacing=0,
            )
        else:
            flagship_tag = ft.Container()
            actions_row = ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARCHIVE_ROUNDED,
                        icon_color=NEON_PURPLE,
                        icon_size=16,
                        tooltip="Mettre au rebut (Archiver quand le projet est terminé)",
                        on_click=lambda e, s=ship: self._confirm_retire_ship(s),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.EDIT_ROUNDED,
                        icon_color=TEXT_SUBTITLE,
                        icon_size=16,
                        tooltip="Modifier le vaisseau",
                        on_click=lambda e, s=ship: self._open_edit_ship_dialog(s),
                    ),
                ],
                spacing=0,
            )

        return interactive_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Container(
                                        content=ft.Text(ship.icon, size=22),
                                        padding=8,
                                        bgcolor=BG_CARD_INNER,
                                        border_radius=8,
                                        border=ft.Border.all(1, ship.color),
                                        shadow=[ft.BoxShadow(spread_radius=1, blur_radius=8, color=f"{ship.color}33")],
                                    ),
                                    ft.Column(
                                        [
                                            ft.Row(
                                                [
                                                    ft.Text(
                                                        ship.name,
                                                        size=14,
                                                        weight=ft.FontWeight.BOLD,
                                                        color=TEXT_TITLE,
                                                        font_family=FONT_HEADER,
                                                        max_lines=1,
                                                        overflow=ft.TextOverflow.ELLIPSIS,
                                                    ),
                                                    flagship_tag,
                                                ],
                                                spacing=6,
                                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                            ),
                                            ft.Row(
                                                [
                                                    ft.Icon(ft.Icons.FLIGHT_ROUNDED, size=12, color=TEXT_MUTED),
                                                    ft.Text(f"{ship.sessions_count} sortie(s)", size=11, color=TEXT_MUTED, font_family=FONT_HEADER),
                                                ],
                                                spacing=4,
                                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                            ),
                                        ],
                                        spacing=2,
                                        expand=True,
                                    ),
                                ],
                                spacing=10,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                expand=True,
                            ),
                            actions_row,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=4),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text("TEMPS TOTAL EN VOL", size=10, color=TEXT_MUTED, font_family=FONT_HEADER),
                                        ft.Text(ship.formatted_total_time.upper(), size=12, weight=ft.FontWeight.BOLD, color=ship.color, font_family=FONT_HEADER),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Container(height=4),
                                ft.ProgressBar(
                                    value=ratio,
                                    color=ship.color,
                                    bgcolor=f"{BORDER_CYBER}BB",
                                    height=6,
                                    border_radius=3,
                                ),
                                ft.Container(height=2),
                                ft.Row(
                                    [
                                        ft.Text("PART FLOTTE", size=9, color=TEXT_MUTED, font_family=FONT_BODY),
                                        ft.Text(f"{pct:.1f}% DU TEMPS GLOBAL", size=9, weight=ft.FontWeight.W_600, color=TEXT_SUBTITLE, font_family=FONT_HEADER),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                            ],
                            spacing=0,
                        ),
                        padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                        bgcolor=BG_CARD_INNER,
                        border_radius=6,
                        border=ft.Border.all(1, f"{BORDER_CYBER}88"),
                    ),
                ],
                spacing=6,
            ),
            width=380,
            bgcolor=BG_PANEL,
            hover_border_color=ship.color,
            padding=14,
        )

    def _build_retired_ship_card(self, ship: Ship):
        return interactive_card(
            ft.Row(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Text(ship.icon, size=18),
                                padding=6,
                                bgcolor=BG_CARD_INNER,
                                border_radius=6,
                                border=ft.Border.all(1, f"{NEON_PURPLE}55"),
                            ),
                            ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(ship.name, size=13, weight=ft.FontWeight.BOLD, color=TEXT_SUBTITLE, font_family=FONT_HEADER),
                                            ft.Container(
                                                content=ft.Text("AU REBUT", size=9, weight=ft.FontWeight.BOLD, color=NEON_PURPLE, font_family=FONT_HEADER),
                                                padding=ft.Padding.symmetric(horizontal=5, vertical=1),
                                                bgcolor=f"{NEON_PURPLE}20",
                                                border_radius=3,
                                                border=ft.Border.all(1, f"{NEON_PURPLE}50"),
                                            ),
                                        ],
                                        spacing=6,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    ),
                                    ft.Text(f"{ship.formatted_total_time} de vol  •  {ship.sessions_count} sorties", size=10, color=TEXT_MUTED, font_family=FONT_HEADER),
                                ],
                                spacing=2,
                            ),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.UNARCHIVE_ROUNDED,
                                icon_color=NEON_GREEN,
                                icon_size=18,
                                tooltip="Réarmer (Remettre en service actif)",
                                on_click=lambda e, s=ship: self._restore_ship(s),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_FOREVER_ROUNDED,
                                icon_color=NEON_RED,
                                icon_size=18,
                                tooltip="Supprimer définitivement",
                                on_click=lambda e, s=ship: self._confirm_delete_ship(s),
                            ),
                        ],
                        spacing=2,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=360,
            bgcolor=BG_CARD_INNER,
            hover_border_color=NEON_PURPLE,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
        )

    def _build_maintenance_entry_row(self, session: FocusSession):
        is_succ = session.completed
        status_col = NEON_GREEN if is_succ else NEON_RED
        status_text = "VOL VALIDÉ" if is_succ else "AVARIE"
        status_icon = ft.Icons.CHECK_CIRCLE_ROUNDED if is_succ else ft.Icons.WARNING_AMBER_ROUNDED

        return ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Text(session.ship_icon if is_succ else "💥", size=18),
                                padding=6,
                                bgcolor=BG_PANEL,
                                border_radius=6,
                                border=ft.Border.all(1, f"{status_col}44"),
                            ),
                            ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(session.ship_name, size=13, weight=ft.FontWeight.BOLD, color=TEXT_TITLE, font_family=FONT_HEADER),
                                            ft.Container(
                                                content=ft.Row(
                                                    [
                                                        ft.Icon(
                                                            ft.Icons.ADS_CLICK_ROUNDED if session.mission_title else ft.Icons.PUBLIC_ROUNDED,
                                                            size=11,
                                                            color=NEON_CYAN if session.mission_title else TEXT_MUTED,
                                                        ),
                                                        ft.Text(
                                                            session.mission_title if session.mission_title else ("Travail Global" if session.ship_is_flagship else "Vol Libre"),
                                                            size=10,
                                                            weight=ft.FontWeight.W_600,
                                                            color=NEON_CYAN if session.mission_title else TEXT_MUTED,
                                                            font_family=FONT_HEADER,
                                                        ),
                                                    ],
                                                    spacing=4,
                                                ),
                                                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                                bgcolor=f"{BG_DEEP_SPACE}CC",
                                                border_radius=4,
                                                border=ft.Border.all(1, f"{NEON_CYAN}33" if session.mission_title else f"{BORDER_CYBER}66"),
                                            ),
                                        ],
                                        spacing=8,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    ),
                                    ft.Row(
                                        [
                                            ft.Icon(ft.Icons.CALENDAR_TODAY_ROUNDED, size=11, color=TEXT_MUTED),
                                            ft.Text(f"{session.date_str}  •  {session.time_str}", size=10, color=TEXT_MUTED, font_family=FONT_HEADER),
                                        ],
                                        spacing=4,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    ),
                                ],
                                spacing=2,
                            ),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Icon(ft.Icons.TIMELAPSE_ROUNDED, size=12, color=status_col),
                                        ft.Text(session.formatted_duration, size=11, weight=ft.FontWeight.BOLD, color=status_col, font_family=FONT_HEADER),
                                    ],
                                    spacing=4,
                                ),
                                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                bgcolor=f"{status_col}15",
                                border_radius=4,
                                border=ft.Border.all(1, f"{status_col}33"),
                            ),
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Icon(ft.Icons.BOLT_ROUNDED, size=12, color=NEON_AMBER),
                                        ft.Text(f"Overtime {session.formatted_overtime}", size=10, weight=ft.FontWeight.BOLD, color=NEON_AMBER, font_family=FONT_HEADER),
                                    ],
                                    spacing=4,
                                ),
                                padding=ft.Padding.symmetric(horizontal=6, vertical=4),
                                bgcolor=f"{NEON_AMBER}15",
                                border_radius=4,
                                border=ft.Border.all(1, f"{NEON_AMBER}44"),
                                visible=session.overtime_seconds > 0,
                            ) if session.overtime_seconds > 0 else ft.Container(),
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Icon(status_icon, size=12, color=status_col),
                                        ft.Text(status_text, size=10, weight=ft.FontWeight.BOLD, color=status_col, font_family=FONT_HEADER),
                                    ],
                                    spacing=4,
                                ),
                                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                bgcolor=f"{status_col}20",
                                border_radius=4,
                                border=ft.Border.all(1, f"{status_col}55"),
                            ),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            bgcolor=BG_CARD_INNER,
            border_radius=6,
            border=ft.Border.all(1, BORDER_CYBER),
        )

    def _on_maintenance_filter_changed(self, e):
        self.selected_ship_filter = self.maintenance_filter_dropdown.value
        self.refresh()
        self.page.update()

    def _export_maintenance_csv(self, e):
        path = self.storage.export_maintenance_log_csv()
        self._show_notification(f"Carnet d'entretien exporté : {os.path.basename(path)}")

    def _confirm_retire_ship(self, ship: Ship):
        if ship.is_flagship:
            self._show_notification("Le Vaisseau Amiral ne peut pas être mis au rebut.")
            return

        def do_retire(ev):
            self.storage.retire_ship(ship.id)
            self.page.pop_dialog()
            self.refresh()
            if self.on_data_changed:
                self.on_data_changed()
            self._show_notification(f"Vaisseau '{ship.name}' mis au rebut (archivé).")
            self.page.update()

        def cancel(ev):
            self.page.pop_dialog()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.ARCHIVE_ROUNDED, color=NEON_PURPLE, size=20),
                    ft.Text("METTRE LE VAISSEAU AU REBUT", size=16, weight=ft.FontWeight.BOLD, color=TEXT_TITLE, font_family=FONT_HEADER),
                ],
                spacing=8,
            ),
            content=ft.Text(
                f"Voulez-vous archiver '{ship.name}' ?\n\nLe vaisseau sera déplacé dans les archives du hangar avec tout son historique de vol préservé, et ne sera plus proposé pour les nouveaux vols.",
                color=TEXT_BODY,
                size=13,
            ),
            actions=[
                ft.TextButton("Annuler", on_click=cancel),
                ft.ElevatedButton("Mettre au Rebut", bgcolor=NEON_PURPLE, color="#FFFFFF", on_click=do_retire),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=BG_PANEL,
        )
        self.page.show_dialog(dlg)

    def _restore_ship(self, ship: Ship):
        self.storage.restore_ship(ship.id)
        self.refresh()
        if self.on_data_changed:
            self.on_data_changed()
        self._show_notification(f"Vaisseau '{ship.name}' réarmé en service actif !")
        self.page.update()

    def _open_new_ship_dialog(self, e):
        name_input = ft.TextField(
            label="Nom du Vaisseau",
            hint_text="ex: Faucon Millenium, Croiseur Gamma...",
            bgcolor=BG_CARD_INNER,
            border_color=BORDER_CYBER,
            focused_border_color=NEON_CYAN,
            color=TEXT_TITLE,
            autofocus=True,
        )

        selected_icon = ["🚀"]
        selected_color = ["#00F0FF"]

        icon_controls = []
        for icon in SHIP_ICONS:
            def make_icon_click(ic):
                def handler(ev):
                    selected_icon[0] = ic
                    for c in icon_controls:
                        c.border = ft.Border.all(1, NEON_CYAN if c.data == ic else BORDER_CYBER)
                    self.page.update()
                return handler

            c = ft.Container(
                content=ft.Text(icon, size=18),
                padding=6,
                border_radius=4,
                border=ft.Border.all(1, NEON_CYAN if icon == "🚀" else BORDER_CYBER),
                on_click=make_icon_click(icon),
                data=icon,
                ink=True,
            )
            icon_controls.append(c)

        color_controls = []
        for color in SHIP_COLORS:
            def make_color_click(col):
                def handler(ev):
                    selected_color[0] = col
                    for c in color_controls:
                        c.border = ft.Border.all(2, "#FFFFFF" if c.data == col else "#00000000")
                    self.page.update()
                return handler

            c = ft.Container(
                width=24,
                height=24,
                bgcolor=color,
                border_radius=12,
                border=ft.Border.all(2, "#FFFFFF" if color == "#00F0FF" else "#00000000"),
                on_click=make_color_click(color),
                data=color,
                ink=True,
            )
            color_controls.append(c)

        def save_ship(ev):
            name = name_input.value.strip()
            if not name:
                return
            self.storage.add_ship(
                name=name,
                color=selected_color[0],
                icon=selected_icon[0],
            )
            self.page.pop_dialog()
            self.refresh()
            if self.on_data_changed:
                self.on_data_changed()
            self._show_notification(f"Vaisseau '{name}' appareillé et prêt au vol !")
            self.page.update()

        def cancel_dlg(ev):
            self.page.pop_dialog()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.ROCKET_ROUNDED, color=NEON_CYAN, size=22),
                    ft.Text("APPAREILLER UN NOUVEAU VAISSEAU", size=16, weight=ft.FontWeight.BOLD, color=TEXT_TITLE, font_family=FONT_HEADER),
                ],
                spacing=8,
            ),
            content=ft.Column(
                [
                    name_input,
                    ft.Container(height=4),
                    ft.Text("Modèle de vaisseau :", size=12, color=TEXT_MUTED),
                    ft.Row(icon_controls, spacing=6, wrap=True),
                    ft.Container(height=4),
                    ft.Text("Couleur de propulsion :", size=12, color=TEXT_MUTED),
                    ft.Row(color_controls, spacing=8),
                ],
                spacing=6,
                tight=True,
            ),
            actions=[
                ft.TextButton("Annuler", on_click=cancel_dlg),
                ft.ElevatedButton("Appareiller le Vaisseau", bgcolor=NEON_CYAN, color="#030712", on_click=save_ship),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=BG_PANEL,
        )
        self.page.show_dialog(dlg)

    def _open_edit_ship_dialog(self, ship: Ship):
        name_input = ft.TextField(
            label="Nom du Vaisseau",
            value=ship.name,
            bgcolor=BG_CARD_INNER,
            border_color=BORDER_CYBER,
            focused_border_color=NEON_CYAN,
            color=TEXT_TITLE,
        )

        selected_icon = [ship.icon]
        selected_color = [ship.color]

        icon_controls = []
        for icon in SHIP_ICONS:
            def make_icon_click(ic):
                def handler(ev):
                    selected_icon[0] = ic
                    for c in icon_controls:
                        c.border = ft.Border.all(1, NEON_CYAN if c.data == ic else BORDER_CYBER)
                    self.page.update()
                return handler

            c = ft.Container(
                content=ft.Text(icon, size=18),
                padding=6,
                border_radius=4,
                border=ft.Border.all(1, NEON_CYAN if icon == ship.icon else BORDER_CYBER),
                on_click=make_icon_click(icon),
                data=icon,
                ink=True,
            )
            icon_controls.append(c)

        color_controls = []
        for color in SHIP_COLORS:
            def make_color_click(col):
                def handler(ev):
                    selected_color[0] = col
                    for c in color_controls:
                        c.border = ft.Border.all(2, "#FFFFFF" if c.data == col else "#00000000")
                    self.page.update()
                return handler

            c = ft.Container(
                width=24,
                height=24,
                bgcolor=color,
                border_radius=12,
                border=ft.Border.all(2, "#FFFFFF" if color == ship.color else "#00000000"),
                on_click=make_color_click(color),
                data=color,
                ink=True,
            )
            color_controls.append(c)

        def save_changes(ev):
            name = name_input.value.strip()
            if not name:
                return
            ship.name = name
            ship.icon = selected_icon[0]
            ship.color = selected_color[0]
            self.storage.update_ship(ship)
            self.page.pop_dialog()
            self.refresh()
            if self.on_data_changed:
                self.on_data_changed()
            self._show_notification("Vaisseau mis à jour !")
            self.page.update()

        def cancel_dlg(ev):
            self.page.pop_dialog()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.EDIT_ROUNDED, color=NEON_CYAN, size=22),
                    ft.Text("MODIFIER LE VAISSEAU", size=16, weight=ft.FontWeight.BOLD, color=TEXT_TITLE, font_family=FONT_HEADER),
                ],
                spacing=8,
            ),
            content=ft.Column(
                [
                    name_input,
                    ft.Container(height=4),
                    ft.Text("Modèle de vaisseau :", size=12, color=TEXT_MUTED),
                    ft.Row(icon_controls, spacing=6, wrap=True),
                    ft.Container(height=4),
                    ft.Text("Couleur de propulsion :", size=12, color=TEXT_MUTED),
                    ft.Row(color_controls, spacing=8),
                ],
                spacing=6,
                tight=True,
            ),
            actions=[
                ft.TextButton("Annuler", on_click=cancel_dlg),
                ft.ElevatedButton("Enregistrer", bgcolor=NEON_CYAN, color="#030712", on_click=save_changes),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=BG_PANEL,
        )
        self.page.show_dialog(dlg)

    def _confirm_delete_ship(self, ship: Ship):
        if ship.is_flagship:
            self._show_notification("Le Vaisseau Amiral ne peut pas être supprimé.")
            return

        def do_delete(ev):
            self.storage.delete_ship(ship.id)
            self.page.pop_dialog()
            self.refresh()
            if self.on_data_changed:
                self.on_data_changed()
            self._show_notification(f"Vaisseau '{ship.name}' définitivement supprimé.")
            self.page.update()

        def cancel(ev):
            self.page.pop_dialog()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.DELETE_FOREVER_ROUNDED, color=NEON_RED, size=22),
                    ft.Text("SUPPRIMER DÉFINITIVEMENT", size=16, weight=ft.FontWeight.BOLD, color=TEXT_TITLE, font_family=FONT_HEADER),
                ],
                spacing=8,
            ),
            content=ft.Text(f"Voulez-vous supprimer définitivement le vaisseau '{ship.name}' du hangar ?", color=TEXT_BODY, size=13),
            actions=[
                ft.TextButton("Annuler", on_click=cancel),
                ft.ElevatedButton("Supprimer", bgcolor=NEON_RED, color="#FFFFFF", on_click=do_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=BG_PANEL,
        )
        self.page.show_dialog(dlg)

    def _show_notification(self, text: str):
        sb = ft.SnackBar(
            content=ft.Text(text, color="#FFFFFF", size=13, font_family=FONT_HEADER),
            bgcolor=BG_PANEL_HOVER,
            duration=2500,
        )
        self.page.show_dialog(sb)

    def get_view(self) -> ft.Control:
        bg_image_path = get_asset_path("hangar_bg.jpg")
        return ft.Container(
            content=self.container,
            expand=True,
            padding=ft.Padding.symmetric(horizontal=24, vertical=16),
            image=ft.DecorationImage(
                src=bg_image_path,
                fit=ft.BoxFit.COVER,
                opacity=0.18,
            ),
        )


# Backward compatibility alias
StatsView = HangarView
