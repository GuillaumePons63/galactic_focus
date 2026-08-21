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
Missions & Directives Strategic Command Center for Galactic Focus (Nova Cyberpunk Synthwave Style).
Features rich KPI metrics, floating capsule filter switcher, global & specific mission cards,
neon segmented progress gauges, dynamic deadline urgency badges, direct takeoff actions,
inline ship arming modals, and historical mission logbook.
"""
from datetime import datetime, date, timedelta
from typing import Callable, Optional, List, Tuple, Dict, Union
import flet as ft

from ..core.models import Mission, Ship, FocusSession
from ..core.storage import StorageManager
from .theme import (
    BG_DEEP_SPACE, BG_DEEP_SPACE_ALT, BG_PANEL, BG_PANEL_HOVER, BG_CARD_INNER,
    BORDER_CYBER, BORDER_CYBER_LIGHT, BORDER_GLOW_CYAN, BORDER_GLOW_AMBER,
    BORDER_GLOW_PURPLE, BORDER_GLOW_MAGENTA,
    NEON_CYAN, NEON_ICE, NEON_GREEN, NEON_AMBER, NEON_GOLD, NEON_ORANGE,
    NEON_PURPLE, NEON_PINK, NEON_MAGENTA, NEON_RED,
    TEXT_TITLE, TEXT_SUBTITLE, TEXT_BODY, TEXT_MUTED, TEXT_CYAN, TEXT_AMBER, TEXT_GREEN,
    TEXT_MAGENTA, TEXT_PURPLE,
    FONT_HEADER, FONT_BODY, FONT_NUM,
    SHIP_COLORS, SHIP_ICONS,
    interactive_card, sci_fi_button, floating_capsule_pill_switch, get_asset_path
)


class MissionsView:
    def __init__(
        self,
        page: ft.Page,
        storage: StorageManager,
        on_data_changed: Optional[Callable] = None,
        on_launch_ship: Optional[Callable[[Ship], None]] = None
    ):
        self.page = page
        self.storage = storage
        self.on_data_changed = on_data_changed
        self.on_launch_ship = on_launch_ship

        self.current_filter = "all"  # "all", "in_progress", "completed"
        self.container = ft.Container(expand=True)
        self.refresh()

    def refresh(self):
        """Rebuilds the entire missions tactical command screen and logbook."""
        all_missions = self.storage.get_missions()
        sessions = self.storage.get_sessions(limit=50)

        active_missions = [m for m in all_missions if not m.is_completed]
        completed_missions = [m for m in all_missions if m.is_completed]

        # Filter missions according to active capsule
        if self.current_filter == "in_progress":
            displayed_missions = active_missions
        elif self.current_filter == "completed":
            displayed_missions = completed_missions
        else:
            displayed_missions = all_missions

        total_mission_sec = sum(m.progress_seconds for m in all_missions)
        comp_rate = (len(completed_missions) / max(1, len(all_missions))) * 100
        urgent_count = sum(1 for m in active_missions if self._is_mission_urgent(m))

        # 1. Telemetry KPI Cards Row
        total_time_str = (
            f"{total_mission_sec // 3600}h {(total_mission_sec % 3600) // 60:02d}m"
            if total_mission_sec >= 3600
            else f"{total_mission_sec // 60} min"
        )
        kpi_row = ft.Row(
            [
                self._build_kpi_card(
                    title="MISSIONS ACTIVES",
                    value=f"{len(active_missions)}",
                    sub_label=f"{len(active_missions)} en vol",
                    icon=ft.Icons.TRACK_CHANGES_ROUNDED,
                    color=NEON_CYAN,
                ),
                self._build_kpi_card(
                    title="TAUX DE SUCCÈS",
                    value=f"{comp_rate:.0f}%",
                    sub_label=f"{len(completed_missions)}/{len(all_missions)} validées",
                    icon=ft.Icons.CHECK_CIRCLE_ROUNDED,
                    color=NEON_GREEN,
                ),
                self._build_kpi_card(
                    title="TEMPS TOTAL INVESTI",
                    value=total_time_str,
                    sub_label="Fleet deep work",
                    icon=ft.Icons.TIMELAPSE_ROUNDED,
                    color=NEON_AMBER,
                ),
                self._build_kpi_card(
                    title="ÉCHÉANCES CRITIQUES",
                    value=f"{urgent_count}",
                    sub_label="Urgentes" if urgent_count > 0 else "Aucune alerte",
                    icon=ft.Icons.ALARM_ROUNDED,
                    color=NEON_RED if urgent_count > 0 else TEXT_MUTED,
                ),
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # 2. Floating Capsule Filter Bar (Nova Pill Switcher)
        filter_switcher = floating_capsule_pill_switch(
            options=[
                (f"Toutes ({len(all_missions)})", "all"),
                (f"En cours ({len(active_missions)})", "in_progress"),
                (f"Accomplies ({len(completed_missions)})", "completed"),
            ],
            selected_key=self.current_filter,
            on_change=self._set_filter,
            active_color=NEON_CYAN,
            active_text_color="#030712",
        )

        # 3. Mission Dossiers List
        mission_cards = []
        for m in displayed_missions:
            mission_cards.append(self._build_mission_card(m))

        missions_column = ft.Column(
            mission_cards if mission_cards else [
                interactive_card(
                    ft.Column(
                        [
                            ft.Icon(ft.Icons.EXPLORE_OFF_ROUNDED, size=36, color=TEXT_MUTED),
                            ft.Text("// AUCUNE MISSION DANS CE SECTEUR //", size=13, weight=ft.FontWeight.BOLD, color=TEXT_MUTED, font_family=FONT_HEADER),
                            ft.Text("Créez une nouvelle directive ou modifiez vos filtres pour afficher des objectifs.", size=11, color=TEXT_MUTED),
                            ft.Container(height=6),
                            sci_fi_button(
                                "+ Créer une nouvelle mission",
                                icon=ft.Icons.ADD_ROUNDED,
                                color_neon=NEON_CYAN,
                                on_click=self._open_new_mission_dialog,
                                width=260,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                    ),
                    padding=32,
                    hover_border_color=NEON_CYAN,
                )
            ],
            spacing=12,
        )

        # 4. Mission Logbook (Journal des Dernières Missions)
        mission_sessions = [s for s in sessions if s.completed][:15]
        log_rows = []
        for s in mission_sessions:
            log_rows.append(self._build_mission_log_row(s))

        journal_missions_section = interactive_card(
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
                                        shadow=[ft.BoxShadow(spread_radius=1, blur_radius=6, color=NEON_PURPLE)],
                                    ),
                                    ft.Text("JOURNAL DE BORD DES MISSIONS ACCOMPLIES", size=13, weight=ft.FontWeight.BOLD, color=TEXT_TITLE, font_family=FONT_HEADER),
                                ],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Container(
                                content=ft.Text(f"// {len(mission_sessions)} ENTRÉES //", size=10, weight=ft.FontWeight.BOLD, color=NEON_PURPLE, font_family=FONT_HEADER),
                                padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                bgcolor=f"{NEON_PURPLE}18",
                                border=ft.Border.all(1, f"{NEON_PURPLE}44"),
                                border_radius=4,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=4),
                    ft.Column(
                        log_rows if log_rows else [
                            ft.Container(
                                content=ft.Text("// AUCUN HISTORIQUE D'ENREGISTREMENT POUR LE MOMENT //", size=11, color=TEXT_MUTED, font_family=FONT_HEADER),
                                padding=12,
                                alignment=ft.Alignment.CENTER,
                            )
                        ],
                        spacing=6,
                    ),
                ],
                spacing=8,
            ),
            padding=16,
            hover_border_color=NEON_PURPLE,
            secondary_glow=NEON_CYAN,
        )

        # Main Layout Column
        self.container.content = ft.Column(
            [
                # Section Title + Action Button
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Icon(ft.Icons.TRACK_CHANGES_ROUNDED, color=NEON_CYAN, size=24),
                                    padding=8,
                                    bgcolor=f"{NEON_CYAN}15",
                                    border=ft.Border.all(1, f"{NEON_CYAN}55"),
                                    border_radius=8,
                                    shadow=[ft.BoxShadow(spread_radius=1, blur_radius=8, color=f"{NEON_CYAN}33")],
                                ),
                                ft.Column(
                                    [
                                        ft.Text("MISSION CONTROL // CAMPAIGNS & DIRECTIVES", size=22, weight=ft.FontWeight.BOLD, color=TEXT_TITLE, font_family=FONT_HEADER),
                                        ft.Text("Directives stratégiques, suivi des objectifs et progression de la flotte", size=12, color=TEXT_SUBTITLE),
                                    ],
                                    spacing=2,
                                ),
                            ],
                            spacing=12,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        sci_fi_button(
                            "+ Nouvelle Mission",
                            icon=ft.Icons.POST_ADD_ROUNDED,
                            color_neon=NEON_CYAN,
                            on_click=self._open_new_mission_dialog,
                            width=200,
                            height=42,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=14),
                kpi_row,
                ft.Container(height=16),
                ft.Row([filter_switcher], alignment=ft.MainAxisAlignment.START),
                ft.Container(height=12),
                missions_column,
                ft.Container(height=18),
                journal_missions_section,
                ft.Container(height=24),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        )

    def _set_filter(self, filter_key: str):
        self.current_filter = filter_key
        self.refresh()
        self.page.update()

    def _is_mission_urgent(self, mission: Mission) -> bool:
        """Determines if a mission deadline is urgent (<= 1 day or overdue)."""
        if mission.is_completed or not mission.deadline:
            return False
        try:
            deadline_date = datetime.strptime(mission.deadline[:10], "%Y-%m-%d").date()
            today = date.today()
            diff_days = (deadline_date - today).days
            return diff_days <= 1
        except Exception:
            return False

    def _get_deadline_badge_data(self, mission: Mission) -> Tuple[str, str, str]:
        """
        Calculates deadline badge label, icon, and cyberpunk color:
        - Overdue: #EF4444 (NEON_RED)
        - Today: #F59E0B (NEON_AMBER)
        - Tomorrow: #FBBF24 (NEON_GOLD)
        - Future (> 1 day): #00F0FF (NEON_CYAN)
        - Completed: #10B981 (NEON_GREEN)
        - None: #556987 (TEXT_MUTED)
        """
        if mission.is_completed:
            lbl = f"ACCOMPLIE ({mission.deadline})" if mission.deadline else "ACCOMPLIE"
            return (lbl, NEON_GREEN, ft.Icons.CHECK_CIRCLE_ROUNDED)

        if not mission.deadline:
            return ("SANS ÉCHÉANCE", TEXT_MUTED, ft.Icons.CALENDAR_TODAY_ROUNDED)

        try:
            deadline_date = datetime.strptime(mission.deadline[:10], "%Y-%m-%d").date()
            today = date.today()
            diff_days = (deadline_date - today).days

            if diff_days < 0:
                return (f"EN RETARD ({abs(diff_days)}j)", NEON_RED, ft.Icons.WARNING_ROUNDED)
            elif diff_days == 0:
                return ("ÉCHÉANCE AUJOURD'HUI !", NEON_AMBER, ft.Icons.BOLT_ROUNDED)
            elif diff_days == 1:
                return ("ÉCHÉANCE DEMAIN", NEON_GOLD, ft.Icons.ALARM_ROUNDED)
            else:
                return (f"DANS {diff_days} JOURS", NEON_CYAN, ft.Icons.CALENDAR_MONTH_ROUNDED)
        except Exception:
            return (mission.deadline.upper(), TEXT_MUTED, ft.Icons.CALENDAR_TODAY_ROUNDED)

    def _build_kpi_card(self, title: str, value: str, sub_label: str, icon, color: str) -> ft.Container:
        return interactive_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(icon, color=color, size=18),
                            ft.Container(
                                content=ft.Text(sub_label, size=9, weight=ft.FontWeight.BOLD, color=color, font_family=FONT_HEADER),
                                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                bgcolor=f"{color}18",
                                border=ft.Border.all(1, f"{color}44"),
                                border_radius=4,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=4),
                    ft.Text(value, size=22, weight=ft.FontWeight.BOLD, color=TEXT_TITLE, font_family=FONT_HEADER),
                    ft.Text(title, size=10, weight=ft.FontWeight.W_700, color=TEXT_MUTED, font_family=FONT_HEADER),
                ],
                spacing=2,
            ),
            bgcolor=BG_PANEL,
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            hover_border_color=color,
            secondary_glow=NEON_PURPLE if color == NEON_CYAN else NEON_CYAN,
            expand=True,
        )

    def _build_mission_card(self, mission: Mission) -> ft.Container:
        ratio = mission.progress_ratio
        is_glob = mission.is_global
        card_accent_color = NEON_GREEN if mission.is_completed else (NEON_CYAN if is_glob else mission.ship_color)

        # 1. Status Pill
        if mission.is_completed:
            status_chip = ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            width=6,
                            height=6,
                            bgcolor=NEON_GREEN,
                            border_radius=3,
                            shadow=[ft.BoxShadow(spread_radius=1, blur_radius=4, color=NEON_GREEN)],
                        ),
                        ft.Text("ACCOMPLIE", size=10, weight=ft.FontWeight.BOLD, color=NEON_GREEN, font_family=FONT_HEADER),
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                bgcolor=f"{NEON_GREEN}15",
                border_radius=4,
                border=ft.Border.all(1, f"{NEON_GREEN}55"),
            )
        else:
            status_chip = ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            width=6,
                            height=6,
                            bgcolor=NEON_CYAN,
                            border_radius=3,
                            shadow=[ft.BoxShadow(spread_radius=1, blur_radius=4, color=NEON_CYAN)],
                        ),
                        ft.Text("EN COURS", size=10, weight=ft.FontWeight.BOLD, color=NEON_CYAN, font_family=FONT_HEADER),
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                bgcolor=f"{NEON_CYAN}15",
                border_radius=4,
                border=ft.Border.all(1, f"{NEON_CYAN}55"),
            )

        # 2. Assignment Pill
        if is_glob:
            assignment_pill = ft.Container(
                content=ft.Row(
                    [
                        ft.Text("🌌", size=13),
                        ft.Text("DIRECTIVE GLOBALE (TOUTE LA FLOTTE)", size=10, weight=ft.FontWeight.BOLD, color=NEON_CYAN, font_family=FONT_HEADER),
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                bgcolor=f"{NEON_CYAN}18",
                border_radius=4,
                border=ft.Border.all(1, f"{NEON_CYAN}66"),
            )
        else:
            assignment_pill = ft.Container(
                content=ft.Row(
                    [
                        ft.Text(mission.ship_icon, size=13),
                        ft.Text(f"VAISSEAU : {mission.ship_name.upper()}", size=10, weight=ft.FontWeight.BOLD, color=TEXT_TITLE, font_family=FONT_HEADER),
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                bgcolor=BG_CARD_INNER,
                border_radius=4,
                border=ft.Border.all(1, mission.ship_color),
            )

        # 3. Dynamic Deadline Badge
        deadline_label, deadline_color, deadline_icon = self._get_deadline_badge_data(mission)
        deadline_pill = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(deadline_icon, size=13, color=deadline_color),
                    ft.Text(deadline_label, size=10, weight=ft.FontWeight.BOLD, color=deadline_color, font_family=FONT_HEADER),
                ],
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
            bgcolor=f"{deadline_color}18",
            border_radius=4,
            border=ft.Border.all(1, f"{deadline_color}55"),
        )

        # 4. Direct Takeoff Button
        launch_btn = ft.Container()
        if not mission.is_completed:
            btn_label = "DÉCOLLER (AMIRAL)" if is_glob else f"DÉCOLLER AVEC {mission.ship_name.upper()}"
            launch_btn = sci_fi_button(
                text=btn_label,
                icon=ft.Icons.ROCKET_LAUNCH_ROUNDED,
                color_neon=NEON_CYAN,
                text_color="#030712",
                on_click=lambda e, m=mission: self._launch_mission_flight(m),
                height=42,
            )

        return interactive_card(
            ft.Column(
                [
                    # Top Badges Row
                    ft.Row(
                        [
                            ft.Row([assignment_pill, deadline_pill], spacing=6, wrap=True),
                            status_chip,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=4),
                    # Mission Title & Description
                    ft.Text(
                        mission.title,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT_TITLE if not mission.is_completed else TEXT_MUTED,
                        font_family=FONT_HEADER,
                    ),
                    ft.Text(
                        mission.description,
                        size=12,
                        color=TEXT_SUBTITLE,
                        visible=bool(mission.description),
                    ) if mission.description else ft.Container(),
                    ft.Container(height=4),
                    # Neon Segmented Progress Bar & Details
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Row(
                                        [
                                            ft.Text("PROGRESSION :", size=11, weight=ft.FontWeight.W_700, color=TEXT_MUTED, font_family=FONT_HEADER),
                                            ft.Text(
                                                f"{mission.formatted_progress_time} / {mission.formatted_target_time}",
                                                size=11,
                                                weight=ft.FontWeight.BOLD,
                                                color=NEON_GREEN if mission.is_completed else (NEON_CYAN if is_glob else mission.ship_color),
                                                font_family=FONT_HEADER,
                                            ),
                                        ],
                                        spacing=4,
                                    ),
                                    ft.Text(f"{ratio * 100:.0f}%", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TITLE if not mission.is_completed else TEXT_MUTED, font_family=FONT_HEADER),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.ProgressBar(
                                value=ratio,
                                color=NEON_GREEN if mission.is_completed else (NEON_CYAN if is_glob else mission.ship_color),
                                bgcolor=f"{BORDER_CYBER}99",
                                height=7,
                                border_radius=4,
                            ),
                        ],
                        spacing=4,
                    ),
                    ft.Container(height=4),
                    # Action Footer Row
                    ft.Row(
                        [
                            launch_btn,
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED if not mission.is_completed else ft.Icons.REPLAY_ROUNDED,
                                        icon_color=NEON_GREEN if not mission.is_completed else TEXT_MUTED,
                                        icon_size=19,
                                        tooltip="Marquer comme accomplie" if not mission.is_completed else "Réactiver la mission",
                                        on_click=lambda e, m=mission: self._toggle_mission(m),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT_ROUNDED,
                                        icon_color=TEXT_SUBTITLE,
                                        icon_size=19,
                                        tooltip="Modifier la mission",
                                        on_click=lambda e, m=mission: self._open_edit_mission_dialog(m),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                                        icon_color=NEON_RED,
                                        icon_size=19,
                                        tooltip="Supprimer la mission",
                                        on_click=lambda e, m=mission: self._confirm_delete_mission(m),
                                    ),
                                ],
                                spacing=2,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=6,
            ),
            padding=ft.Padding.symmetric(horizontal=18, vertical=14),
            hover_border_color=card_accent_color,
            secondary_glow=NEON_PURPLE if card_accent_color == NEON_CYAN else NEON_CYAN,
        )

    def _build_mission_log_row(self, session: FocusSession) -> ft.Container:
        is_succ = session.completed
        return ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Text(session.ship_icon, size=16),
                                padding=6,
                                bgcolor=BG_DEEP_SPACE,
                                border_radius=6,
                                border=ft.Border.all(1, BORDER_CYBER),
                            ),
                            ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(session.ship_name, size=12, weight=ft.FontWeight.BOLD, color=TEXT_TITLE, font_family=FONT_HEADER),
                                            ft.Container(
                                                content=ft.Text(f"🎯 {session.mission_title}", size=10, color=NEON_CYAN, font_family=FONT_HEADER),
                                                padding=ft.Padding.symmetric(horizontal=6, vertical=1),
                                                bgcolor=f"{NEON_CYAN}15",
                                                border_radius=3,
                                                visible=bool(session.mission_title),
                                            ) if session.mission_title else ft.Container(),
                                        ],
                                        spacing=6,
                                    ),
                                    ft.Text(f"{session.date_str} // {session.time_str}", size=10, color=TEXT_MUTED, font_family=FONT_HEADER),
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
                                content=ft.Text(session.formatted_duration, size=11, weight=ft.FontWeight.BOLD, color=NEON_GREEN if is_succ else NEON_RED, font_family=FONT_HEADER),
                                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                bgcolor=f"{NEON_GREEN}15" if is_succ else f"{NEON_RED}15",
                                border=ft.Border.all(1, f"{NEON_GREEN}44" if is_succ else f"{NEON_RED}44"),
                                border_radius=4,
                            ),
                            ft.Container(
                                content=ft.Text(f"Overtime {session.formatted_overtime}", size=10, weight=ft.FontWeight.BOLD, color=NEON_AMBER, font_family=FONT_HEADER),
                                padding=ft.Padding.symmetric(horizontal=6, vertical=3),
                                bgcolor=f"{NEON_AMBER}15",
                                border=ft.Border.all(1, f"{NEON_AMBER}44"),
                                border_radius=4,
                                visible=session.overtime_seconds > 0,
                            ) if session.overtime_seconds > 0 else ft.Container(),
                            ft.Container(
                                content=ft.Text("VOL VALIDÉ" if is_succ else "AVARIE", size=10, weight=ft.FontWeight.BOLD, color=NEON_GREEN if is_succ else NEON_RED, font_family=FONT_HEADER),
                                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                bgcolor=f"{NEON_GREEN}15" if is_succ else f"{NEON_RED}15",
                                border=ft.Border.all(1, f"{NEON_GREEN}44" if is_succ else f"{NEON_RED}44"),
                                border_radius=4,
                            ),
                        ],
                        spacing=6,
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

    def _launch_mission_flight(self, mission: Mission):
        """Launches flight in Cockpit for this mission (invokes on_launch_ship callback with ship and mission)."""
        if mission.is_global or not mission.ship_id:
            ship_to_launch = self.storage.get_flagship()
        else:
            ship = self.storage.get_ship_by_id(mission.ship_id)
            ship_to_launch = ship or self.storage.get_flagship()

        if self.on_launch_ship and ship_to_launch:
            try:
                self.on_launch_ship(ship_to_launch, mission)
            except TypeError:
                self.on_launch_ship(ship_to_launch)

    def _toggle_mission(self, mission_or_id: Union[Mission, str]):
        if isinstance(mission_or_id, str):
            mission = self.storage.get_mission_by_id(mission_or_id)
            mission_id = mission_or_id
        else:
            mission = mission_or_id
            mission_id = mission.id if mission else ""

        if not mission_id:
            return

        was_completed = mission.is_completed if mission else False
        self.storage.toggle_mission_completed(mission_id)
        self.refresh()
        if self.on_data_changed:
            self.on_data_changed()
        status_msg = "Mission terminée ! 🎉" if not was_completed else "Mission réactivée."
        self._show_notification(status_msg)
        self.page.update()

    def _confirm_delete_mission(self, mission: Mission):
        def do_delete(ev):
            self.storage.delete_mission(mission.id)
            self.page.pop_dialog()
            self.refresh()
            if self.on_data_changed:
                self.on_data_changed()
            self._show_notification(f"Mission '{mission.title}' supprimée.")
            self.page.update()

        def cancel(ev):
            self.page.pop_dialog()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.DELETE_FOREVER_ROUNDED, color=NEON_RED, size=22),
                    ft.Text("SUPPRIMER LA MISSION", size=16, weight=ft.FontWeight.BOLD, color=TEXT_TITLE, font_family=FONT_HEADER),
                ],
                spacing=8,
            ),
            content=ft.Text(f"Voulez-vous vraiment supprimer définitivement la mission '{mission.title}' ?", color=TEXT_BODY, size=14),
            actions=[
                ft.TextButton("Annuler", on_click=cancel),
                ft.ElevatedButton("Supprimer", bgcolor=NEON_RED, color="#FFFFFF", on_click=do_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=BG_PANEL,
        )
        self.page.show_dialog(dlg)

    def _open_new_ship_inline_dialog(self, on_created: Callable[[Ship], None]):
        name_input = ft.TextField(
            label="Nom du Vaisseau",
            hint_text="ex: Faucon Stellaire, Navette Alpha...",
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
                        c.bgcolor = f"{NEON_CYAN}22" if c.data == ic else BG_CARD_INNER
                    self.page.update()
                return handler

            c = ft.Container(
                content=ft.Text(icon, size=18),
                padding=6,
                border_radius=4,
                border=ft.Border.all(1, NEON_CYAN if icon == "🚀" else BORDER_CYBER),
                bgcolor=f"{NEON_CYAN}22" if icon == "🚀" else BG_CARD_INNER,
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

        def save_ship_inline(ev):
            name = name_input.value.strip()
            if not name:
                return
            new_ship = self.storage.add_ship(
                name=name,
                color=selected_color[0],
                icon=selected_icon[0],
            )
            self.page.pop_dialog()
            if self.on_data_changed:
                self.on_data_changed()
            on_created(new_ship)
            self._show_notification(f"Vaisseau '{name}' appareillé et assigné !")

        def cancel_sub(ev):
            self.page.pop_dialog()

        sub_dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.ROCKET_ROUNDED, color=NEON_CYAN, size=20),
                    ft.Text("APPAREILLER UN NOUVEAU VAISSEAU", size=15, weight=ft.FontWeight.BOLD, color=TEXT_TITLE, font_family=FONT_HEADER),
                ],
                spacing=8,
            ),
            content=ft.Column(
                [
                    name_input,
                    ft.Container(height=4),
                    ft.Text("Modèle de vaisseau :", size=11, color=TEXT_MUTED, font_family=FONT_HEADER),
                    ft.Row(icon_controls, spacing=6, wrap=True),
                    ft.Container(height=4),
                    ft.Text("Couleur de propulsion :", size=11, color=TEXT_MUTED, font_family=FONT_HEADER),
                    ft.Row(color_controls, spacing=8),
                ],
                spacing=6,
                tight=True,
            ),
            actions=[
                ft.TextButton("Annuler", on_click=cancel_sub),
                ft.ElevatedButton("Appareiller & Assigner", bgcolor=NEON_CYAN, color="#030712", on_click=save_ship_inline),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=BG_PANEL,
        )
        self.page.show_dialog(sub_dlg)

    def _open_new_mission_dialog(self, e=None):
        ships = self.storage.get_ships(include_retired=False)
        is_global_val = [True]

        title_input = ft.TextField(
            label="Titre de la Mission",
            hint_text="ex: Rédiger le bilan, Développer l'API, Objectif 5h de Deep Work...",
            bgcolor=BG_CARD_INNER,
            border_color=BORDER_CYBER,
            focused_border_color=NEON_CYAN,
            color=TEXT_TITLE,
            autofocus=True,
        )

        desc_input = ft.TextField(
            label="Description / Objectifs (Optionnel)",
            hint_text="Détails, critères de réussite...",
            bgcolor=BG_CARD_INNER,
            border_color=BORDER_CYBER,
            focused_border_color=NEON_CYAN,
            color=TEXT_TITLE,
            multiline=True,
            max_lines=3,
        )

        target_minutes_input = ft.TextField(
            label="Durée Cible (minutes)",
            value="40",
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor=BG_CARD_INNER,
            border_color=BORDER_CYBER,
            focused_border_color=NEON_CYAN,
            color=TEXT_TITLE,
            width=180,
        )

        # Quick preset buttons for duration
        def set_preset_min(m_val: int):
            target_minutes_input.value = str(m_val)
            self.page.update()

        preset_row = ft.Row(
            [
                ft.Container(
                    content=ft.Text(f"{m}m", size=10, weight=ft.FontWeight.BOLD, color=NEON_CYAN),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    bgcolor=BG_CARD_INNER,
                    border=ft.Border.all(1, BORDER_CYBER),
                    border_radius=4,
                    on_click=lambda e, val=m: set_preset_min(val),
                    ink=True,
                )
                for m in [15, 25, 40, 60, 90, 120]
            ],
            spacing=4,
        )

        non_flagship_ships = [s for s in ships if not s.is_flagship]
        ship_options = []
        for s in non_flagship_ships:
            ship_options.append(ft.dropdown.Option(key=s.id, text=f"{s.icon}  {s.name}"))

        ship_dropdown = ft.Dropdown(
            label="Vaisseau Assigné",
            options=ship_options,
            value=non_flagship_ships[0].id if non_flagship_ships else (ships[0].id if ships else ""),
            bgcolor=BG_CARD_INNER,
            border_color=BORDER_CYBER,
            focused_border_color=NEON_CYAN,
            color=TEXT_TITLE,
            expand=True,
        )

        def update_ship_dropdown_selection(new_ship: Ship):
            current_ships = self.storage.get_ships(include_retired=False)
            curr_non_flagship = [s for s in current_ships if not s.is_flagship]
            ship_dropdown.options = [
                ft.dropdown.Option(key=s.id, text=f"{s.icon}  {s.name}")
                for s in (curr_non_flagship if curr_non_flagship else current_ships)
            ]
            ship_dropdown.value = new_ship.id
            self.page.update()

        def on_add_ship_click(ev):
            self._open_new_ship_inline_dialog(on_created=update_ship_dropdown_selection)

        btn_add_ship = sci_fi_button(
            text="Nouveau Vaisseau",
            icon=ft.Icons.ADD_ROUNDED,
            on_click=on_add_ship_click,
            height=40,
        )

        ship_assignment_row = ft.Row(
            [
                ship_dropdown,
                btn_add_ship,
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            visible=False,
        )

        btn_type_global = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ALL_INCLUSIVE_ROUNDED, size=16, color=NEON_CYAN),
                    ft.Text("Mission Globale (Toute la flotte)", size=11, weight=ft.FontWeight.BOLD, color=NEON_CYAN, font_family=FONT_HEADER),
                ],
                spacing=6,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            bgcolor=f"{NEON_CYAN}22",
            border_radius=6,
            border=ft.Border.all(1, NEON_CYAN),
            ink=True,
        )

        btn_type_specific = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ROCKET_ROUNDED, size=16, color=TEXT_MUTED),
                    ft.Text("Mission de Vaisseau Spécifique", size=11, color=TEXT_MUTED, font_family=FONT_HEADER),
                ],
                spacing=6,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            bgcolor=BG_CARD_INNER,
            border_radius=6,
            border=ft.Border.all(1, BORDER_CYBER),
            ink=True,
        )

        type_info_text = ft.Text(
            "💡 Une mission globale comptabilise TOUT votre temps de travail, quel que soit le vaisseau piloté.",
            size=11,
            color=TEXT_MUTED,
            italic=True,
        )

        def switch_type(to_global: bool):
            is_global_val[0] = to_global
            if to_global:
                btn_type_global.bgcolor = f"{NEON_CYAN}22"
                btn_type_global.border = ft.Border.all(1, NEON_CYAN)
                btn_type_global.content.controls[0].color = NEON_CYAN
                btn_type_global.content.controls[1].color = NEON_CYAN
                btn_type_global.content.controls[1].weight = ft.FontWeight.BOLD

                btn_type_specific.bgcolor = BG_CARD_INNER
                btn_type_specific.border = ft.Border.all(1, BORDER_CYBER)
                btn_type_specific.content.controls[0].color = TEXT_MUTED
                btn_type_specific.content.controls[1].color = TEXT_MUTED
                btn_type_specific.content.controls[1].weight = ft.FontWeight.NORMAL

                ship_assignment_row.visible = False
                type_info_text.value = "💡 Une mission globale comptabilise TOUT votre temps de travail, quel que soit le vaisseau piloté."
            else:
                btn_type_specific.bgcolor = f"{NEON_PURPLE}22"
                btn_type_specific.border = ft.Border.all(1, NEON_PURPLE)
                btn_type_specific.content.controls[0].color = NEON_PURPLE
                btn_type_specific.content.controls[1].color = NEON_PURPLE
                btn_type_specific.content.controls[1].weight = ft.FontWeight.BOLD

                btn_type_global.bgcolor = BG_CARD_INNER
                btn_type_global.border = ft.Border.all(1, BORDER_CYBER)
                btn_type_global.content.controls[0].color = TEXT_MUTED
                btn_type_global.content.controls[1].color = TEXT_MUTED
                btn_type_global.content.controls[1].weight = ft.FontWeight.NORMAL

                ship_assignment_row.visible = True
                type_info_text.value = "💡 Cette mission se décomptera automatiquement chaque fois que vous volerez avec ce vaisseau spécifique."
            self.page.update()

        btn_type_global.on_click = lambda e: switch_type(True)
        btn_type_specific.on_click = lambda e: switch_type(False)

        default_deadline = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")
        deadline_input = ft.TextField(
            label="Date Limite (AAAA-MM-JJ)",
            value=default_deadline,
            bgcolor=BG_CARD_INNER,
            border_color=BORDER_CYBER,
            focused_border_color=NEON_CYAN,
            color=TEXT_TITLE,
            width=200,
        )

        def set_deadline_offset(days: int):
            deadline_input.value = (date.today() + timedelta(days=days)).strftime("%Y-%m-%d")
            self.page.update()

        deadline_preset_row = ft.Row(
            [
                ft.Container(
                    content=ft.Text(lbl, size=10, weight=ft.FontWeight.BOLD, color=NEON_AMBER),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    bgcolor=BG_CARD_INNER,
                    border=ft.Border.all(1, BORDER_CYBER),
                    border_radius=4,
                    on_click=lambda e, d=days: set_deadline_offset(d),
                    ink=True,
                )
                for lbl, days in [("+1j", 1), ("+3j", 3), ("+7j", 7), ("+14j", 14), ("+30j", 30)]
            ],
            spacing=4,
        )

        def save_mission(ev):
            title = title_input.value.strip()
            if not title:
                return

            try:
                mins = int(target_minutes_input.value.strip())
                target_sec = max(60, mins * 60)
            except Exception:
                target_sec = 2400

            if is_global_val[0]:
                self.storage.add_mission(
                    title=title,
                    target_seconds=target_sec,
                    is_global=True,
                    deadline=deadline_input.value.strip(),
                    description=desc_input.value.strip(),
                )
            else:
                selected_ship_id = ship_dropdown.value or ""
                selected_ship = self.storage.get_ship_by_id(selected_ship_id)
                s_name = selected_ship.name if selected_ship else "Vaisseau"
                s_icon = selected_ship.icon if selected_ship else "🚀"
                s_color = selected_ship.color if selected_ship else "#00F0FF"

                self.storage.add_mission(
                    title=title,
                    target_seconds=target_sec,
                    is_global=False,
                    ship_id=selected_ship_id,
                    ship_name=s_name,
                    ship_icon=s_icon,
                    ship_color=s_color,
                    deadline=deadline_input.value.strip(),
                    description=desc_input.value.strip(),
                )

            self.page.pop_dialog()
            self.refresh()
            if self.on_data_changed:
                self.on_data_changed()
            self._show_notification(f"Mission '{title}' créée !")
            self.page.update()

        def cancel(ev):
            self.page.pop_dialog()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.POST_ADD_ROUNDED, color=NEON_CYAN, size=22),
                    ft.Text("CRÉER UNE NOUVELLE MISSION", size=16, weight=ft.FontWeight.BOLD, color=TEXT_TITLE, font_family=FONT_HEADER),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    [
                        title_input,
                        desc_input,
                        ft.Container(height=2),
                        ft.Text("Type d'attribution :", size=11, color=TEXT_MUTED, font_family=FONT_HEADER),
                        ft.Row([btn_type_global, btn_type_specific], spacing=8),
                        type_info_text,
                        ship_assignment_row,
                        ft.Container(height=2),
                        ft.Row(
                            [
                                target_minutes_input,
                                ft.Column([ft.Text("Préréglages :", size=10, color=TEXT_MUTED), preset_row], spacing=2),
                            ],
                            spacing=12,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            [
                                deadline_input,
                                ft.Column([ft.Text("Échéance rapide :", size=10, color=TEXT_MUTED), deadline_preset_row], spacing=2),
                            ],
                            spacing=12,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=8,
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=540,
            ),
            actions=[
                ft.TextButton("Annuler", on_click=cancel),
                ft.ElevatedButton("Créer la Mission", bgcolor=NEON_CYAN, color="#030712", on_click=save_mission),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=BG_PANEL,
        )
        self.page.show_dialog(dlg)

    def _open_edit_mission_dialog(self, mission: Mission):
        ships = self.storage.get_ships(include_retired=False)

        title_input = ft.TextField(
            label="Titre de la Mission",
            value=mission.title,
            bgcolor=BG_CARD_INNER,
            border_color=BORDER_CYBER,
            focused_border_color=NEON_CYAN,
            color=TEXT_TITLE,
        )

        desc_input = ft.TextField(
            label="Description / Objectifs",
            value=mission.description,
            bgcolor=BG_CARD_INNER,
            border_color=BORDER_CYBER,
            focused_border_color=NEON_CYAN,
            color=TEXT_TITLE,
            multiline=True,
            max_lines=3,
        )

        target_minutes_input = ft.TextField(
            label="Durée Cible (minutes)",
            value=str(mission.target_seconds // 60),
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor=BG_CARD_INNER,
            border_color=BORDER_CYBER,
            focused_border_color=NEON_CYAN,
            color=TEXT_TITLE,
            width=180,
        )

        ship_options = [ft.dropdown.Option(key="", text="🌌  [ DIRECTIVE GLOBALE ]")]
        for s in ships:
            if not s.is_flagship:
                ship_options.append(ft.dropdown.Option(key=s.id, text=f"{s.icon}  {s.name}"))

        ship_dropdown = ft.Dropdown(
            label="Attribution",
            options=ship_options,
            value="" if mission.is_global else mission.ship_id,
            bgcolor=BG_CARD_INNER,
            border_color=BORDER_CYBER,
            focused_border_color=NEON_CYAN,
            color=TEXT_TITLE,
            expand=True,
        )

        def update_edit_ship_selection(new_ship: Ship):
            current_ships = self.storage.get_ships(include_retired=False)
            curr_opts = [ft.dropdown.Option(key="", text="🌌  [ DIRECTIVE GLOBALE ]")]
            for s in current_ships:
                if not s.is_flagship:
                    curr_opts.append(ft.dropdown.Option(key=s.id, text=f"{s.icon}  {s.name}"))
            ship_dropdown.options = curr_opts
            ship_dropdown.value = new_ship.id
            self.page.update()

        def on_add_ship_edit_click(ev):
            self._open_new_ship_inline_dialog(on_created=update_edit_ship_selection)

        btn_add_ship_edit = sci_fi_button(
            text="Nouveau Vaisseau",
            icon=ft.Icons.ADD_ROUNDED,
            on_click=on_add_ship_edit_click,
            height=40,
        )

        deadline_input = ft.TextField(
            label="Date Limite (AAAA-MM-JJ)",
            value=mission.deadline,
            bgcolor=BG_CARD_INNER,
            border_color=BORDER_CYBER,
            focused_border_color=NEON_CYAN,
            color=TEXT_TITLE,
            width=220,
        )

        def save_changes(ev):
            title = title_input.value.strip()
            if not title:
                return

            try:
                mins = int(target_minutes_input.value.strip())
                mission.target_seconds = max(60, mins * 60)
            except Exception:
                pass

            mission.title = title
            mission.description = desc_input.value.strip()
            mission.deadline = deadline_input.value.strip()

            selected_ship_id = ship_dropdown.value or ""
            if not selected_ship_id:
                mission.is_global = True
                mission.ship_id = ""
                mission.ship_name = "Mission Globale"
                mission.ship_icon = "🌌"
                mission.ship_color = "#00F0FF"
            else:
                mission.is_global = False
                mission.ship_id = selected_ship_id
                selected_ship = self.storage.get_ship_by_id(selected_ship_id)
                if selected_ship:
                    mission.ship_name = selected_ship.name
                    mission.ship_icon = selected_ship.icon
                    mission.ship_color = selected_ship.color

            self.storage.update_mission(mission)
            self.page.pop_dialog()
            self.refresh()
            if self.on_data_changed:
                self.on_data_changed()
            self._show_notification("Mission mise à jour !")
            self.page.update()

        def cancel(ev):
            self.page.pop_dialog()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.EDIT_NOTE_ROUNDED, color=NEON_CYAN, size=22),
                    ft.Text("MODIFIER LA MISSION", size=16, weight=ft.FontWeight.BOLD, color=TEXT_TITLE, font_family=FONT_HEADER),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    [
                        title_input,
                        desc_input,
                        ft.Row([ship_dropdown, btn_add_ship_edit], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        target_minutes_input,
                        deadline_input,
                    ],
                    spacing=8,
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=520,
            ),
            actions=[
                ft.TextButton("Annuler", on_click=cancel),
                ft.ElevatedButton("Enregistrer", bgcolor=NEON_CYAN, color="#030712", on_click=save_changes),
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
        bg_image_path = get_asset_path("missions_bg.jpg")
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
