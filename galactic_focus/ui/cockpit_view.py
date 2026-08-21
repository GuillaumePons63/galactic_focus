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
Cockpit view for Galactic Focus V5.0: Cyberpunk Synthwave & Nova Command Bridge.
Features atmospheric cockpit backdrop, central Hyperdrive HUD with dynamic propulsion pulsation,
floating capsule duration switcher, and daily squadron flight registry.
"""
import asyncio
import time
import threading
from datetime import date
from typing import Callable, Optional, List, Tuple
import flet as ft

from ..core.models import Ship, FocusSession, Mission, get_ship_model_for_duration
from ..core.storage import StorageManager
from ..core.timer_engine import TimerEngine, TimerState
from .theme import (
    BG_DEEP_SPACE, BG_PANEL, BG_PANEL_HOVER, BG_CARD_INNER,
    BORDER_CYBER, BORDER_CYBER_LIGHT, BORDER_GLOW_CYAN, BORDER_GLOW_AMBER, BORDER_GLOW_PURPLE,
    NEON_CYAN, NEON_ICE, NEON_GREEN, NEON_AMBER, NEON_GOLD, NEON_ORANGE, NEON_PURPLE, NEON_RED, NEON_MAGENTA,
    TEXT_TITLE, TEXT_SUBTITLE, TEXT_BODY, TEXT_MUTED, TEXT_CYAN, TEXT_AMBER, TEXT_GREEN, TEXT_MAGENTA, TEXT_PURPLE,
    FONT_HEADER, FONT_BODY, FONT_NUM,
    SHIP_COLORS, SHIP_ICONS,
    interactive_card, sci_fi_button, floating_capsule_pill_switch, get_asset_path
)


class CockpitView:
    def __init__(self, page: ft.Page, storage: StorageManager, on_data_changed: Optional[Callable] = None):
        self.page = page
        self.storage = storage
        self.on_data_changed = on_data_changed

        self.timer_engine = TimerEngine(default_target_seconds=1200, ignition_duration_seconds=10)
        self.selected_duration_sec: int = 1200
        self.selected_ship: Optional[Ship] = None
        self.targeted_mission: Optional[Mission] = None
        self._stop_ticker: bool = False
        self._pulse_tick: int = 0

        self._init_ship_selection()
        self._build_ui()

    def _init_ship_selection(self):
        ships = self.storage.get_ships(include_retired=False)
        if ships:
            self.selected_ship = ships[0]
        else:
            self.selected_ship = self.storage.get_flagship()

    def _build_duration_switch(self) -> ft.Container:
        options = [
            ("15m", "900"),
            ("20m", "1200"),
            ("25m", "1500"),
            ("30m", "1800"),
            ("45m", "2700"),
            ("60m", "3600"),
        ]
        return floating_capsule_pill_switch(
            options=options,
            selected_key=str(self.selected_duration_sec),
            on_change=self._on_duration_selected,
            active_color=NEON_CYAN,
            active_text_color="#030712",
        )

    def _on_duration_selected(self, key_str: str):
        if self.timer_engine.is_running:
            return
        sec = int(key_str)
        self._set_target_duration(sec)

    def _set_target_duration(self, sec: int):
        if self.timer_engine.is_running:
            return
        self.selected_duration_sec = sec
        mins = sec // 60
        self.timer_text.value = f"{mins:02d}:00"

        if hasattr(self, "btn_main_action") and self.btn_main_action and hasattr(self.btn_main_action, "content"):
            if hasattr(self.btn_main_action.content, "controls") and len(self.btn_main_action.content.controls) > 1:
                self.btn_main_action.content.controls[1].value = f"LANCER LE SAUT ({mins} MIN)"

        if hasattr(self, "duration_switcher_container"):
            self.duration_switcher_container.content = self._build_duration_switch()

        try:
            self.page.update()
        except Exception:
            pass

    def _build_ui(self):
        # 1. Top Controls Bar: Ship Selector & Duration Capsule Switcher
        active_ships = self.storage.get_ships(include_retired=False)
        ship_options = []
        for s in active_ships:
            tag = " (Amiral • Global)" if s.is_flagship else ""
            ship_options.append(ft.dropdown.Option(key=s.id, text=f"{s.icon}  {s.name}{tag}"))

        self.ship_dropdown = ft.Dropdown(
            value=self.selected_ship.id if self.selected_ship else (active_ships[0].id if active_ships else None),
            options=ship_options,
            on_select=self._on_ship_selected,
            bgcolor=BG_CARD_INNER,
            border_color=BORDER_CYBER,
            focused_border_color=NEON_CYAN,
            color=TEXT_TITLE,
            width=260,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=6),
        )

        self.btn_new_ship = ft.IconButton(
            icon=ft.Icons.ADD_ROUNDED,
            icon_color=NEON_CYAN,
            bgcolor=BG_CARD_INNER,
            tooltip="Appareiller un nouveau vaisseau",
            on_click=self._open_new_ship_dialog,
        )

        self.duration_switcher_container = ft.Container(
            content=self._build_duration_switch(),
        )

        self.top_control_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Container(
                                        width=6,
                                        height=6,
                                        bgcolor=NEON_CYAN,
                                        border_radius=3,
                                        shadow=[ft.BoxShadow(spread_radius=1, blur_radius=4, color=NEON_CYAN)],
                                    ),
                                    ft.Text("Vaisseau actif", size=12, weight=ft.FontWeight.W_700, color=TEXT_TITLE, font_family=FONT_HEADER),
                                ],
                                spacing=6,
                            ),
                            ft.Row([self.ship_dropdown, self.btn_new_ship], spacing=4),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Container(
                                        width=6,
                                        height=6,
                                        bgcolor=NEON_AMBER,
                                        border_radius=3,
                                        shadow=[ft.BoxShadow(spread_radius=1, blur_radius=4, color=NEON_AMBER)],
                                    ),
                                    ft.Text("Durée du vol", size=12, weight=ft.FontWeight.W_700, color=TEXT_TITLE, font_family=FONT_HEADER),
                                ],
                                spacing=6,
                            ),
                            self.duration_switcher_container,
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                wrap=True,
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=10),
            bgcolor=BG_PANEL,
            border=ft.Border.all(1, BORDER_CYBER),
            border_radius=8,
        )

        # 2. Main Hyperdrive HUD (Centered, width=480, 220px Ring)
        self.progress_ring = ft.ProgressRing(
            value=0.0,
            stroke_width=10,
            color=NEON_CYAN,
            bgcolor=f"{BORDER_CYBER}99",
            width=220,
            height=220,
        )

        self.status_badge = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        width=6,
                        height=6,
                        bgcolor=NEON_CYAN,
                        border_radius=3,
                        shadow=[ft.BoxShadow(spread_radius=1, blur_radius=6, color=NEON_CYAN)],
                    ),
                    ft.Text("SYS // PRÊT AU DÉCOLLAGE", size=10, weight=ft.FontWeight.W_700, color=NEON_CYAN, font_family=FONT_HEADER),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
            ),
            padding=ft.Padding.symmetric(horizontal=10, vertical=3),
            bgcolor=f"{NEON_CYAN}15",
            border_radius=4,
            border=ft.Border.all(1, f"{NEON_CYAN}44"),
        )

        self.timer_text = ft.Text(
            "20:00",
            size=52,
            weight=ft.FontWeight.W_900,
            color=TEXT_TITLE,
            font_family=FONT_NUM,
        )

        self.ship_pill_text = ft.Text(
            self._get_ship_label(),
            size=11,
            color=TEXT_TITLE,
            weight=ft.FontWeight.W_700,
            font_family=FONT_HEADER,
        )

        self.mission_auto_pill_text = ft.Text(
            self._get_auto_mission_label(),
            size=10,
            color=TEXT_CYAN,
            font_family=FONT_BODY,
        )

        self.ship_pill = ft.Container(
            content=ft.Column(
                [
                    self.ship_pill_text,
                    self.mission_auto_pill_text,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=1,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=4),
            bgcolor=BG_CARD_INNER,
            border_radius=4,
            border=ft.Border.all(1, BORDER_CYBER),
        )

        self.timer_center_stack = ft.Stack(
            [
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    width=230,
                    height=230,
                    content=self.progress_ring,
                ),
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    width=230,
                    height=230,
                    content=ft.Column(
                        [
                            self.status_badge,
                            ft.Container(height=2),
                            self.timer_text,
                            ft.Container(height=2),
                            self.ship_pill,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                    ),
                ),
            ],
            width=230,
            height=230,
            alignment=ft.Alignment.CENTER,
        )

        self.btn_main_action = sci_fi_button(
            text="Lancer le Saut (20 min)",
            icon=ft.Icons.ROCKET_LAUNCH_ROUNDED,
            color_neon=NEON_CYAN,
            text_color="#030712",
            on_click=self._on_main_action_clicked,
            width=320,
            height=46,
        )

        self.btn_skip_ignition = ft.TextButton(
            "⚡ Décoller immédiatement (Court-circuiter l'allumage)",
            style=ft.ButtonStyle(color=NEON_CYAN),
            on_click=self._on_skip_ignition_clicked,
            visible=False,
        )

        self.btn_abort_action = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CANCEL_ROUNDED, color=NEON_RED, size=14),
                    ft.Text(
                        "INTERROMPRE LE VOL",
                        size=11,
                        weight=ft.FontWeight.W_700,
                        color=NEON_RED,
                        font_family=FONT_HEADER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
            ),
            padding=ft.Padding.symmetric(horizontal=14, vertical=6),
            bgcolor=f"{NEON_RED}15",
            border_radius=4,
            border=ft.Border.all(1, f"{NEON_RED}44"),
            on_click=self._on_abort_clicked,
            visible=False,
            ink=True,
        )

        center_hud_content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    width=6,
                                    height=6,
                                    bgcolor=NEON_CYAN,
                                    border_radius=3,
                                    shadow=[ft.BoxShadow(spread_radius=1, blur_radius=4, color=NEON_CYAN)],
                                ),
                                ft.Text("HUD CENTRAL // VISEUR DE VOL HYPERDRIVE", size=13, weight=ft.FontWeight.W_700, color=TEXT_TITLE, font_family=FONT_HEADER),
                            ],
                            spacing=6,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(
                            content=ft.Text("WARP READY", size=9, weight=ft.FontWeight.BOLD, color=NEON_CYAN, font_family=FONT_HEADER),
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                            bgcolor=f"{NEON_CYAN}18",
                            border=ft.Border.all(1, f"{NEON_CYAN}44"),
                            border_radius=4,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=8),
                ft.Container(
                    content=self.timer_center_stack,
                    alignment=ft.Alignment.CENTER,
                    padding=10,
                ),
                ft.Container(height=8),
                ft.Column(
                    [
                        self.btn_main_action,
                        ft.Container(height=2),
                        self.btn_skip_ignition,
                        self.btn_abort_action,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=2,
        )

        self.center_hud_card = interactive_card(center_hud_content, padding=20, width=500)

        # 3. Bottom Daily Fleet Radar Deck
        self.daily_fleet_container = ft.Container()
        self._refresh_daily_fleet_view()

        self.bottom_radar_card = interactive_card(
            self.daily_fleet_container,
            padding=14,
        )

    def _get_ship_label(self) -> str:
        if self.selected_ship:
            tag = " • (Travail Global)" if self.selected_ship.is_flagship else ""
            return f"{self.selected_ship.icon} {self.selected_ship.name}{tag}"
        return "🪐 Vaisseau Amiral"

    def _get_auto_mission_label(self) -> str:
        active_global = self.storage.get_active_global_mission()

        if self.targeted_mission:
            fresh_m = self.storage.get_mission_by_id(self.targeted_mission.id)
            if fresh_m and not fresh_m.is_completed:
                self.targeted_mission = fresh_m
                if fresh_m.is_global or fresh_m.ship_id == "":
                    return f"🎯 Mission Globale Ciblée : {fresh_m.title}"
                else:
                    glob_tag = f" (+ Globale {active_global.title[:12]})" if active_global else ""
                    return f"🎯 Mission Ciblée : {fresh_m.title}{glob_tag}"
            else:
                self.targeted_mission = None

        if not self.selected_ship:
            return "Propulsion Libre"

        if self.selected_ship.is_flagship:
            if active_global:
                return f"🌌 Décompte sur Mission Globale : {active_global.title}"
            return "🌌 Décompte sur les missions globales"

        ship_mission = self.storage.get_active_mission_for_ship(self.selected_ship.id)
        if ship_mission and active_global:
            return f"🎯 {ship_mission.title} (+ Globale {active_global.title[:12]})"
        elif ship_mission:
            return f"🎯 {ship_mission.title}"
        elif active_global:
            return f"🌌 Avance mission globale : {active_global.title}"
        return "Propulsion Libre (Travail sans mission)"

    def _on_ship_selected(self, e):
        ship_id = self.ship_dropdown.value
        self.selected_ship = self.storage.get_ship_by_id(ship_id)
        if self.targeted_mission and not self.targeted_mission.is_global and self.targeted_mission.ship_id != ship_id:
            self.targeted_mission = None
        self.ship_pill_text.value = self._get_ship_label()
        self.mission_auto_pill_text.value = self._get_auto_mission_label()
        self.page.update()

    def load_mission(self, ship: Ship, mission: Optional[Mission] = None):
        """Loads a ship (category of work) and sets an optional targeted mission."""
        self.selected_ship = ship
        self.targeted_mission = mission
        self.ship_dropdown.value = ship.id

        if mission and not self.timer_engine.is_running:
            rem_sec = max(60, mission.target_seconds - mission.progress_seconds)
            if rem_sec >= 3600:
                self._set_target_duration(3600)
            elif rem_sec >= 2700:
                self._set_target_duration(2700)
            elif rem_sec >= 1800:
                self._set_target_duration(1800)
            elif rem_sec >= 1500:
                self._set_target_duration(1500)
            elif rem_sec >= 1200:
                self._set_target_duration(1200)
            elif rem_sec >= 900:
                self._set_target_duration(900)

        self.ship_pill_text.value = self._get_ship_label()
        self.mission_auto_pill_text.value = self._get_auto_mission_label()

        if mission:
            self._show_notification(f"🎯 Mission '{mission.title}' configurée sur le pont de commande !")
        else:
            self._show_notification(f"Vaisseau '{ship.name}' configuré sur le pont de commande !")
        self.page.update()

    def load_ship(self, ship: Ship):
        self.load_mission(ship, None)

    def _refresh_daily_fleet_view(self):
        daily = self.storage.get_daily_summary()
        
        if daily.ships:
            ship_chips = [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(ship, size=16),
                            ft.Text("VOL VALIDÉ" if ship != "💥" else "AVARIE", size=10, weight=ft.FontWeight.W_700, color=NEON_GREEN if ship != "💥" else NEON_RED, font_family=FONT_HEADER),
                        ],
                        spacing=6,
                    ),
                    padding=ft.Padding.symmetric(horizontal=10, vertical=5),
                    bgcolor=BG_CARD_INNER,
                    border_radius=4,
                    border=ft.Border.all(1, BORDER_CYBER),
                )
                for ship in daily.ships
            ]
            ships_view = ft.Row(
                ship_chips,
                spacing=8,
                wrap=True,
                alignment=ft.MainAxisAlignment.START,
            )
        else:
            ships_view = ft.Text(
                "Aucun vol spatial enregistré aujourd'hui. Configurez votre vaisseau et lancez votre premier saut.",
                size=12,
                color=TEXT_MUTED,
                font_family=FONT_BODY,
            )

        self.daily_fleet_container.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    width=6,
                                    height=6,
                                    bgcolor=NEON_PURPLE,
                                    border_radius=3,
                                    shadow=[ft.BoxShadow(spread_radius=1, blur_radius=4, color=NEON_PURPLE)],
                                ),
                                ft.Text("ESCADRON DU JOUR // REGISTRE DE VOLS", size=12, weight=ft.FontWeight.W_700, color=TEXT_TITLE, font_family=FONT_HEADER),
                            ],
                            spacing=6,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(
                            content=ft.Text(
                                f"{daily.completed_sessions} vols accomplis • {daily.formatted_total_time}",
                                size=11,
                                color=NEON_CYAN,
                                weight=ft.FontWeight.W_700,
                                font_family=FONT_HEADER,
                            ),
                            padding=ft.Padding.symmetric(horizontal=10, vertical=3),
                            bgcolor=f"{NEON_CYAN}15",
                            border_radius=4,
                            border=ft.Border.all(1, f"{NEON_CYAN}33"),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    wrap=True,
                ),
                ft.Container(height=4),
                ships_view,
            ],
            spacing=4,
        )

    def _on_main_action_clicked(self, e):
        state = self.timer_engine.state

        if state == TimerState.IDLE:
            ship = self.selected_ship or self.storage.get_flagship()
            ship_id = ship.id
            ship_name = ship.name
            ship_icon = ship.icon

            if self.targeted_mission and not self.targeted_mission.is_completed:
                m_id = self.targeted_mission.id
                m_title = self.targeted_mission.title
            else:
                ship_mission = self.storage.get_active_mission_for_ship(ship_id)
                m_id = ship_mission.id if ship_mission else ""
                m_title = ship_mission.title if ship_mission else ("Travail Global" if ship.is_flagship else "")

            self.timer_engine.start(
                ship_id=ship_id,
                ship_name=ship_name,
                ship_icon=ship_icon,
                target_seconds=self.selected_duration_sec,
                with_ignition=True,
                mission_id=m_id,
                mission_title=m_title,
            )
            self._update_timer_display(self.timer_engine.get_status())
            self._update_view_for_ignition()
            self._start_ticker()

        elif state == TimerState.IGNITION:
            self._stop_ticker = True
            self.timer_engine.cancel_ignition()
            self._show_notification("Décollage annulé. Réacteurs coupés.")
            self._update_view_for_idle()
            self.page.update()

        elif state == TimerState.OVERTIME or state == TimerState.FOCUSING:
            self._stop_ticker = True
            session = self.timer_engine.complete()
            res = self.storage.add_session(session)
            
            self._show_flight_success_dialog(session, res)

            self._update_view_for_idle()
            self._refresh_daily_fleet_view()
            if self.on_data_changed:
                self.on_data_changed()
            self.page.update()

    def _on_skip_ignition_clicked(self, e):
        if self.timer_engine.state == TimerState.IGNITION:
            self.timer_engine.skip_ignition()
            self._update_timer_display(self.timer_engine.get_status())
            self._update_view_for_focusing()
            self.page.update()

    def _on_abort_clicked(self, e):
        def confirm_abort(ev):
            self.page.pop_dialog()
            self._stop_ticker = True
            session = self.timer_engine.abort()
            self.storage.add_session(session)
            self._show_notification("Vol interrompu. Vaisseau endommagé.")
            self._update_view_for_idle()
            self._refresh_daily_fleet_view()
            if self.on_data_changed:
                self.on_data_changed()
            self.page.update()

        def cancel_dialog(ev):
            self.page.pop_dialog()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=NEON_RED, size=20),
                    ft.Text("Alerte • Avarie Imminente", size=15, weight=ft.FontWeight.W_700, color=TEXT_TITLE, font_family=FONT_HEADER),
                ],
                spacing=8,
            ),
            content=ft.Text(
                "Interrompre la propulsion avant terme enregistrera une avarie technique dans votre carnet d'entretien.",
                size=13,
                color=TEXT_BODY,
            ),
            actions=[
                ft.TextButton("Poursuivre le Vol", on_click=cancel_dialog),
                ft.ElevatedButton("Confirmer l'Abandon", bgcolor=NEON_RED, color="#FFFFFF", on_click=confirm_abort),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=BG_PANEL,
        )
        self.page.show_dialog(dlg)

    def _start_ticker(self):
        self._stop_ticker = False
        try:
            self.page.run_task(self._ticker_async)
        except Exception:
            threading.Thread(target=self._ticker_sync, daemon=True).start()

    async def _ticker_async(self):
        while not self._stop_ticker and self.timer_engine.is_running:
            await asyncio.sleep(0.5)
            self._pulse_tick += 1
            status = self.timer_engine.tick()
            self._update_timer_display(status)
            try:
                self.page.update()
            except Exception:
                break

    def _ticker_sync(self):
        while not self._stop_ticker and self.timer_engine.is_running:
            time.sleep(0.5)
            self._pulse_tick += 1
            status = self.timer_engine.tick()
            self._update_timer_display(status)
            try:
                self.page.update()
            except Exception:
                break

    def _update_timer_display(self, status: dict):
        self.timer_text.value = status["display_time"]
        self.progress_ring.value = status["progress_ratio"]
        pulse = (self._pulse_tick % 2 == 0)

        if status["is_ignition"]:
            self.progress_ring.color = NEON_ORANGE if pulse else NEON_AMBER
            self.timer_text.color = NEON_ORANGE if pulse else NEON_AMBER
            self.status_badge.bgcolor = f"{NEON_ORANGE}18"
            self.status_badge.border = ft.Border.all(1, f"{NEON_ORANGE}60")
            self.status_badge.content.controls[0].bgcolor = NEON_ORANGE
            self.status_badge.content.controls[0].shadow = [ft.BoxShadow(spread_radius=1, blur_radius=6, color=NEON_ORANGE)]
            self.status_badge.content.controls[1].value = f"IGNITION EN COURS ({status['ignition_remaining']}s)"
            self.status_badge.content.controls[1].color = NEON_ORANGE

            self.btn_main_action.bgcolor = NEON_ORANGE
            self.btn_main_action.shadow = [ft.BoxShadow(spread_radius=1, blur_radius=14, color=f"{NEON_ORANGE}77")]
            self.btn_main_action.content.controls[0].icon = ft.Icons.CANCEL_ROUNDED
            self.btn_main_action.content.controls[0].color = "#030712"
            self.btn_main_action.content.controls[1].value = f"ANNULER LE DÉCOLLAGE ({status['ignition_remaining']}s)"
            self.btn_main_action.content.controls[1].color = "#030712"
            self.btn_skip_ignition.visible = True
            self.btn_abort_action.visible = False

        elif status["is_overtime"]:
            self.progress_ring.color = NEON_GREEN if pulse else NEON_CYAN
            self.timer_text.color = NEON_GREEN if pulse else NEON_CYAN
            
            self.status_badge.bgcolor = f"{NEON_GREEN}18"
            self.status_badge.border = ft.Border.all(1, f"{NEON_GREEN}60")
            self.status_badge.content.controls[0].bgcolor = NEON_GREEN
            self.status_badge.content.controls[0].shadow = [ft.BoxShadow(spread_radius=1, blur_radius=6, color=NEON_GREEN)]
            self.status_badge.content.controls[1].value = "OVERDRIVE ACTIF // VOL VALIDÉ"
            self.status_badge.content.controls[1].color = NEON_GREEN

            self.btn_main_action.bgcolor = NEON_GREEN
            self.btn_main_action.shadow = [ft.BoxShadow(spread_radius=1, blur_radius=14, color=f"{NEON_GREEN}77")]
            self.btn_main_action.content.controls[0].icon = ft.Icons.FLAG_ROUNDED
            self.btn_main_action.content.controls[0].color = "#030712"
            self.btn_main_action.content.controls[1].value = f"ATTERRIR & ENREGISTRER ({status['display_time']})"
            self.btn_main_action.content.controls[1].color = "#030712"
            self.btn_skip_ignition.visible = False
            self.btn_abort_action.visible = False

        else:
            self.progress_ring.color = NEON_CYAN
            self.timer_text.color = TEXT_TITLE

            self.status_badge.bgcolor = f"{NEON_CYAN}15"
            self.status_badge.border = ft.Border.all(1, f"{NEON_CYAN}44")
            self.status_badge.content.controls[0].bgcolor = NEON_CYAN
            self.status_badge.content.controls[0].shadow = [ft.BoxShadow(spread_radius=1, blur_radius=6, color=NEON_CYAN)]
            self.status_badge.content.controls[1].value = "HYPERDRIVE // PROPULSION ACTIVE"
            self.status_badge.content.controls[1].color = NEON_CYAN

            self.btn_main_action.bgcolor = BG_CARD_INNER
            self.btn_main_action.shadow = []
            self.btn_main_action.content.controls[0].icon = ft.Icons.HOURGLASS_TOP_ROUNDED
            self.btn_main_action.content.controls[0].color = TEXT_MUTED
            self.btn_main_action.content.controls[1].value = "PROPULSION EN COURS..."
            self.btn_main_action.content.controls[1].color = TEXT_MUTED
            self.btn_skip_ignition.visible = False
            self.btn_abort_action.visible = True

    def _update_view_for_ignition(self):
        self.ship_dropdown.disabled = True
        self.btn_new_ship.disabled = True
        self.duration_switcher_container.visible = False
        self.btn_skip_ignition.visible = True
        self.btn_abort_action.visible = False
        self.page.update()

    def _update_view_for_focusing(self):
        self.ship_dropdown.disabled = True
        self.btn_new_ship.disabled = True
        self.duration_switcher_container.visible = False
        self.btn_skip_ignition.visible = False
        self.btn_abort_action.visible = True
        self.page.update()

    def _update_view_for_idle(self):
        self.ship_dropdown.disabled = False
        self.btn_new_ship.disabled = False
        self.btn_abort_action.visible = False
        self.btn_skip_ignition.visible = False
        self.duration_switcher_container.visible = True

        mins = self.selected_duration_sec // 60
        self.timer_text.value = f"{mins:02d}:00"
        self.timer_text.color = TEXT_TITLE

        self.status_badge.bgcolor = f"{NEON_CYAN}15"
        self.status_badge.border = ft.Border.all(1, f"{NEON_CYAN}44")
        self.status_badge.content.controls[0].bgcolor = NEON_CYAN
        self.status_badge.content.controls[0].shadow = [ft.BoxShadow(spread_radius=1, blur_radius=6, color=NEON_CYAN)]
        self.status_badge.content.controls[1].value = "SYS // PRÊT AU DÉCOLLAGE"
        self.status_badge.content.controls[1].color = NEON_CYAN

        self.btn_main_action.bgcolor = NEON_CYAN
        self.btn_main_action.shadow = [ft.BoxShadow(spread_radius=1, blur_radius=12, color=f"{NEON_CYAN}77")]
        self.btn_main_action.content.controls[0].icon = ft.Icons.ROCKET_LAUNCH_ROUNDED
        self.btn_main_action.content.controls[0].color = "#030712"
        self.btn_main_action.content.controls[1].value = f"LANCER LE SAUT ({mins} MIN)"
        self.btn_main_action.content.controls[1].color = "#030712"

    def _show_flight_success_dialog(self, session: FocusSession, resolution_info: dict):
        def close_dialog(e):
            self.page.pop_dialog()

        advanced_list = resolution_info.get("advanced_missions", [])
        completed_list = resolution_info.get("completed_missions", [])

        rows = [
            ft.Row(
                [
                    ft.Text("Vaisseau :", size=12, color=TEXT_MUTED, font_family=FONT_BODY),
                    ft.Text(f"{session.ship_icon} {session.ship_name}", size=12, weight=ft.FontWeight.W_700, color=TEXT_TITLE),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Row(
                [
                    ft.Text("Temps de vol :", size=12, color=TEXT_MUTED, font_family=FONT_BODY),
                    ft.Text(f"{session.formatted_duration}", size=12, weight=ft.FontWeight.W_700, color=NEON_GREEN, font_family=FONT_HEADER),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        ]

        if session.overtime_seconds > 0:
            rows.append(
                ft.Row(
                    [
                        ft.Text("Overtime extra :", size=12, color=TEXT_MUTED, font_family=FONT_BODY),
                        ft.Text(f"{session.formatted_overtime}", size=12, weight=ft.FontWeight.W_700, color=NEON_AMBER, font_family=FONT_HEADER),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )

        mission_feedback = []
        if completed_list:
            for m_title in completed_list:
                mission_feedback.append(
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=NEON_GREEN, size=15),
                            ft.Text(f"Mission accomplie : {m_title} ! 🎉", size=11, weight=ft.FontWeight.W_700, color=NEON_GREEN, font_family=FONT_HEADER),
                        ],
                        spacing=6,
                    )
                )
        elif advanced_list:
            for m_title in advanced_list:
                mission_feedback.append(
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color=NEON_CYAN, size=14),
                            ft.Text(f"Mission avancée : {m_title}", size=11, color=TEXT_BODY, font_family=FONT_BODY),
                        ],
                        spacing=6,
                    )
                )

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Text(session.ship_icon, size=22),
                    ft.Text("Vol Spatial Accompli", size=16, weight=ft.FontWeight.W_700, color=TEXT_TITLE, font_family=FONT_HEADER),
                ],
                spacing=8,
            ),
            content=ft.Column(
                [
                    ft.Text(
                        "Rapport de mission : Le temps de vol a été enregistré et décompté sur vos objectifs.",
                        size=12,
                        color=TEXT_BODY,
                    ),
                    ft.Container(height=4),
                    interactive_card(
                        ft.Column(rows, spacing=4),
                        bgcolor=BG_CARD_INNER,
                        padding=10,
                    ),
                    ft.Column(mission_feedback, spacing=3) if mission_feedback else ft.Container(),
                ],
                spacing=6,
                tight=True,
            ),
            actions=[
                ft.ElevatedButton("Retour au Cockpit", bgcolor=NEON_CYAN, color="#030712", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=BG_PANEL,
        )
        self.page.show_dialog(dlg)

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
                width=22,
                height=22,
                bgcolor=color,
                border_radius=11,
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
            new_ship = self.storage.add_ship(
                name=name,
                color=selected_color[0],
                icon=selected_icon[0],
            )
            self.page.pop_dialog()
            self.selected_ship = new_ship
            self.reload_fleet()
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
                    ft.Icon(ft.Icons.ROCKET_ROUNDED, color=NEON_CYAN, size=20),
                    ft.Text("Appareiller un nouveau vaisseau", size=15, weight=ft.FontWeight.W_700, color=TEXT_TITLE, font_family=FONT_HEADER),
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

    def reload_fleet(self):
        active_ships = self.storage.get_ships(include_retired=False)
        ship_options = []
        for s in active_ships:
            tag = " (Amiral • Global)" if s.is_flagship else ""
            ship_options.append(ft.dropdown.Option(key=s.id, text=f"{s.icon}  {s.name}{tag}"))

        self.ship_dropdown.options = ship_options

        if self.selected_ship and not self.selected_ship.is_retired and any(s.id == self.selected_ship.id for s in active_ships):
            latest = self.storage.get_ship_by_id(self.selected_ship.id)
            if latest and not latest.is_retired:
                self.selected_ship = latest
                self.ship_dropdown.value = latest.id
            elif active_ships:
                self.selected_ship = active_ships[0]
                self.ship_dropdown.value = self.selected_ship.id
        elif active_ships:
            self.selected_ship = active_ships[0]
            self.ship_dropdown.value = self.selected_ship.id
        else:
            self.selected_ship = self.storage.get_flagship()
            self.ship_dropdown.value = self.selected_ship.id

        self.ship_pill_text.value = self._get_ship_label()
        self.mission_auto_pill_text.value = self._get_auto_mission_label()
        self._refresh_daily_fleet_view()

    def reload_projects(self):
        self.reload_fleet()

    def _show_notification(self, text: str):
        sb = ft.SnackBar(
            content=ft.Text(text, color="#FFFFFF", size=12, font_family=FONT_BODY),
            bgcolor=BG_PANEL_HOVER,
            duration=2500,
        )
        self.page.show_dialog(sb)

    def get_view(self) -> ft.Control:
        bg_image_path = get_asset_path("cockpit_bg.jpg")
        main_content = ft.Column(
            [
                # Section Header
                ft.Column(
                    [
                        ft.Text("COMMAND CENTER // OVERVIEW", size=24, weight=ft.FontWeight.W_900, color=TEXT_TITLE, font_family=FONT_HEADER),
                        ft.Text("Supervision de la propulsion spatiale, télémétrie des réacteurs et pont de commandement", size=12, color=TEXT_SUBTITLE, font_family=FONT_BODY),
                    ],
                    spacing=2,
                ),
                ft.Container(height=12),
                # Top Control Bar
                self.top_control_bar,
                ft.Container(height=16),
                # Central Flight Deck HUD (Centered)
                ft.Row(
                    [self.center_hud_card],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(height=16),
                # Bottom Radar Escadron
                self.bottom_radar_card,
                ft.Container(height=24),
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

        return ft.Container(
            content=main_content,
            expand=True,
            padding=ft.Padding.symmetric(horizontal=24, vertical=16),
            image=ft.DecorationImage(
                src=bg_image_path,
                fit=ft.BoxFit.COVER,
                opacity=0.20,
            ),
        )
