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
Adversarial Empirical Boundary and Data Invariant Test Suite for Galactic Focus.
Challenger 2: Boundaries & Data Invariant Tester.

Coverage:
1. Flagship protection invariants (retire_ship, delete_ship, auto-healing, missing storage).
2. Dynamic deadline calculation across past, today, tomorrow, future, leap days, missing/malformed dates.
3. CSV export generation, header format, special characters, RFC4180 escaping, UTF-8-BOM compliance, high volume.
4. MockPage compatibility and headless environment resilience across Cockpit, Missions, and Hangar views.
"""
import unittest
import tempfile
import os
import sys
import csv
import json
import codecs
from pathlib import Path
from datetime import date, timedelta, datetime
import flet as ft

from galactic_focus.core.models import Ship, FocusSession, Mission, DailyFleetSummary, get_ship_model_for_duration
from galactic_focus.core.storage import StorageManager
from galactic_focus.core.timer_engine import TimerEngine, TimerState
from galactic_focus.ui.cockpit_view import CockpitView
from galactic_focus.ui.missions_view import MissionsView
from galactic_focus.ui.hangar_view import HangarView


class TestFlagshipInvariants(unittest.TestCase):
    """Stress tests for flagship immutability and persistence guarantees."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_file = Path(self.temp_dir.name) / "test_flagship.json"
        self.storage = StorageManager(str(self.temp_file))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_flagship_cannot_be_retired(self):
        flagship = self.storage.get_flagship()
        self.assertTrue(flagship.is_flagship)
        self.assertFalse(flagship.is_retired)

        # Attempt retirement
        res = self.storage.retire_ship(flagship.id)
        self.assertFalse(res.is_retired)
        self.assertIsNone(res.retired_at)

        # Verify in storage
        f_after = self.storage.get_ship_by_id(flagship.id)
        self.assertFalse(f_after.is_retired)
        self.assertNotIn(flagship.id, [s.id for s in self.storage.get_retired_ships()])
        self.assertIn(flagship.id, [s.id for s in self.storage.get_ships(include_retired=False)])

    def test_flagship_cannot_be_deleted(self):
        flagship = self.storage.get_flagship()
        
        # Attempt deletion
        self.storage.delete_ship(flagship.id)
        
        # Flagship must still exist in storage
        f_after = self.storage.get_ship_by_id(flagship.id)
        self.assertIsNotNone(f_after)
        self.assertTrue(f_after.is_flagship)
        self.assertIn(flagship.id, [s.id for s in self.storage.get_ships(include_retired=True)])

    def test_storage_auto_heals_missing_flagship(self):
        # Corrupt data.json by clearing all ships
        with open(self.temp_file, "w", encoding="utf-8") as f:
            json.dump({"ships": [], "missions": [], "sessions": [], "version": 3}, f)

        # Reload storage
        new_storage = StorageManager(str(self.temp_file))
        flagship = new_storage.get_flagship()
        self.assertIsNotNone(flagship)
        self.assertTrue(flagship.is_flagship)
        self.assertEqual(flagship.name, "Vaisseau Amiral")

    def test_storage_auto_heals_when_all_ships_are_non_flagship(self):
        # Create data.json with only regular ships
        custom_ships = [
            {"id": "ship_1", "name": "Chasseur 1", "color": "#FF0000", "icon": "🚀", "is_flagship": False, "is_retired": False},
            {"id": "ship_2", "name": "Chasseur 2", "color": "#00FF00", "icon": "🛸", "is_flagship": False, "is_retired": False},
        ]
        with open(self.temp_file, "w", encoding="utf-8") as f:
            json.dump({"ships": custom_ships, "missions": [], "sessions": [], "version": 3}, f)

        new_storage = StorageManager(str(self.temp_file))
        flagship = new_storage.get_flagship()
        self.assertIsNotNone(flagship)
        self.assertTrue(flagship.is_flagship)
        
        # Flagship must be at index 0 of active fleet
        ships = new_storage.get_ships(include_retired=False)
        self.assertTrue(ships[0].is_flagship)
        self.assertEqual(len(ships), 3)

    def test_flagship_is_always_sorted_first(self):
        # Add multiple ships
        for i in range(5):
            self.storage.add_ship(f"Vaisseau {i}", is_flagship=False)
        
        ships = self.storage.get_ships(include_retired=False)
        self.assertTrue(ships[0].is_flagship)
        self.assertEqual(ships[0].name, "Vaisseau Amiral")


class TestDynamicDeadlines(unittest.TestCase):
    """Exhaustive boundary testing of dynamic deadline calculation."""

    def test_deadline_empty_and_none(self):
        m_empty = Mission(title="Empty Deadline", deadline="")
        self.assertEqual(m_empty.deadline_info["label"], "Sans date limite")
        self.assertFalse(m_empty.deadline_info["is_urgent"])
        self.assertFalse(m_empty.deadline_info["is_expired"])
        self.assertEqual(m_empty.deadline_info["color"], "#64748B")

    def test_deadline_today(self):
        today_str = date.today().strftime("%Y-%m-%d")
        m_today = Mission(title="Today Deadline", deadline=today_str)
        info = m_today.deadline_info
        self.assertEqual(info["label"], "Échéance aujourd'hui !")
        self.assertTrue(info["is_urgent"])
        self.assertFalse(info["is_expired"])
        self.assertEqual(info["color"], "#FF7A00")

    def test_deadline_tomorrow(self):
        tomorrow_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        m_tomorrow = Mission(title="Tomorrow Deadline", deadline=tomorrow_str)
        info = m_tomorrow.deadline_info
        self.assertEqual(info["label"], "Échéance demain")
        self.assertTrue(info["is_urgent"])
        self.assertFalse(info["is_expired"])
        self.assertEqual(info["color"], "#FFB300")

    def test_deadline_past_overdue_various_offsets(self):
        for days_ago in [1, 2, 7, 30, 365, 3650]:
            past_str = (date.today() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            m_past = Mission(title=f"Past {days_ago}", deadline=past_str)
            info = m_past.deadline_info
            self.assertEqual(info["label"], f"En retard ({days_ago}j)")
            self.assertTrue(info["is_urgent"])
            self.assertTrue(info["is_expired"])
            self.assertEqual(info["color"], "#FF3366")

    def test_deadline_near_future_and_distant_future(self):
        # 2 days to 30 days
        for days_ahead in [2, 5, 10, 30, 365, 3650]:
            future_str = (date.today() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
            m_future = Mission(title=f"Future {days_ahead}", deadline=future_str)
            info = m_future.deadline_info
            self.assertEqual(info["label"], f"Dans {days_ahead} jours")
            self.assertFalse(info["is_urgent"])
            self.assertFalse(info["is_expired"])
            self.assertEqual(info["color"], "#00F0FF")

    def test_deadline_leap_years(self):
        # Leap days in 2024, 2028, 2032
        for year in [2024, 2028, 2032]:
            leap_date = f"{year}-02-29"
            m = Mission(title=f"Leap {year}", deadline=leap_date)
            info = m.deadline_info
            self.assertIsInstance(info["label"], str)
            self.assertIn("label", info)

    def test_deadline_malformed_string_resilience(self):
        malformed_inputs = [
            "not-a-date",
            "2026/08/19",
            "19-08-2026",
            "2025-02-29",  # non-leap year invalid date
            "2026-13-45",
            "9999999-99-99",
            "null",
            "12345",
        ]
        for bad_str in malformed_inputs:
            m = Mission(title="Bad Date", deadline=bad_str)
            info = m.deadline_info
            # Must return safely without throwing unhandled exception
            self.assertEqual(info["label"], bad_str)
            self.assertFalse(info["is_urgent"])
            self.assertFalse(info["is_expired"])
            self.assertEqual(info["color"], "#64748B")

    def test_deadline_completed_mission_overrides_overdue(self):
        past_str = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
        m_completed = Mission(
            title="Completed Overdue Mission",
            deadline=past_str,
            status="completed",
            target_seconds=1200,
            progress_seconds=1200,
        )
        info = m_completed.deadline_info
        self.assertIn("Terminée", info["label"])
        self.assertFalse(info["is_urgent"])
        self.assertFalse(info["is_expired"])
        self.assertEqual(info["color"], "#00E676")


class TestCSVExportCompliance(unittest.TestCase):
    """Stress tests for RFC 4180, UTF-8-BOM, special characters, and large datasets."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_storage_file = Path(self.temp_dir.name) / "csv_test.json"
        self.storage = StorageManager(str(self.temp_storage_file))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_utf8_bom_signature(self):
        session = FocusSession(
            ship_id="s1",
            ship_name="Intercepteur Étoilé",
            ship_icon="🚀",
            mission_title="Opération Étoile Polaire",
            actual_seconds=1800,
            overtime_seconds=60,
            completed=True,
        )
        self.storage.add_session(session)

        export_file = Path(self.temp_dir.name) / "export_bom.csv"
        self.storage.export_maintenance_log_csv(str(export_file))

        self.assertTrue(export_file.exists())
        # Check raw bytes for UTF-8-BOM (\xef\xbb\xbf)
        with open(export_file, "rb") as bf:
            raw_bytes = bf.read(3)
            self.assertEqual(raw_bytes, codecs.BOM_UTF8)

    def test_csv_exact_headers(self):
        export_file = Path(self.temp_dir.name) / "export_headers.csv"
        self.storage.export_maintenance_log_csv(str(export_file))

        with open(export_file, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader)
            expected_headers = [
                "ID", "Date", "Heure", "Vaisseau", "Mission", "Temps de Vol (min)",
                "Temps (secondes)", "Overtime (sec)", "Statut de Vol"
            ]
            self.assertEqual(headers, expected_headers)

    def test_csv_special_characters_escaping(self):
        # Stress-test complex inputs: quotes, commas, semicolons, accents, emojis, newlines
        complex_sessions = [
            FocusSession(
                ship_name='Chasseur, "Super-Lourd"; Modèle X',
                ship_icon="🚀",
                mission_title='Mission "Deep-Space, Alpha"; [Tag: #1]',
                actual_seconds=3600,
                overtime_seconds=300,
                completed=True,
            ),
            FocusSession(
                ship_name="Navette Spatiale \n Ligne 2",
                ship_icon="🛸",
                mission_title="Directive : Étoile & Nébuleuse (宇宙 / Космос / 🌌)",
                actual_seconds=900,
                overtime_seconds=0,
                completed=False,
            ),
        ]

        for s in complex_sessions:
            self.storage.add_session(s)

        export_file = Path(self.temp_dir.name) / "export_complex.csv"
        self.storage.export_maintenance_log_csv(str(export_file))

        # Parse with standard csv.DictReader and verify data integrity
        with open(export_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            
            # Find rows
            row_chasseur = next(r for r in rows if "Chasseur" in r["Vaisseau"])
            row_navette = next(r for r in rows if "Navette" in r["Vaisseau"])

            self.assertIn('Chasseur, "Super-Lourd"; Modèle X', row_chasseur["Vaisseau"])
            self.assertIn('Mission "Deep-Space, Alpha"; [Tag: #1]', row_chasseur["Mission"])
            self.assertEqual(row_chasseur["Statut de Vol"], "Vol Réussi")
            
            self.assertIn("Directive : Étoile & Nébuleuse (宇宙 / Космос / 🌌)", row_navette["Mission"])
            self.assertEqual(row_navette["Statut de Vol"], "Vol Interrompu (Dégâts)")

    def test_csv_large_volume_performance(self):
        # Batch insert 1,000 sessions
        raw = self.storage._load_raw()
        for i in range(1000):
            s = FocusSession(
                ship_id=f"ship_{i % 5}",
                ship_name=f"Vaisseau {i % 5}",
                mission_title=f"Mission {i}",
                actual_seconds=1200 + (i % 60),
                overtime_seconds=i % 10,
                completed=(i % 4 != 0),
            )
            raw.setdefault("sessions", []).append(s.to_dict())
        self.storage._save_raw(raw)

        export_file = Path(self.temp_dir.name) / "export_large.csv"
        t0 = datetime.now()
        self.storage.export_maintenance_log_csv(str(export_file))
        duration_ms = (datetime.now() - t0).total_seconds() * 1000

        self.assertTrue(export_file.exists())
        self.assertLess(duration_ms, 500)  # Export should take < 500ms

        with open(export_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 1000)


class TestMockPageHeadlessResilience(unittest.TestCase):
    """Stress tests for UI views in headless/mock environments with zero display crashes."""

    class HeadlessMockPage:
        def __init__(self):
            self.title = "Galactic Focus Mock"
            self.bgcolor = "#030712"
            self.theme_mode = ft.ThemeMode.DARK
            self.padding = 0
            self.window = self.MockWindow()
            self.dialog = None
            self.controls = []

        class MockWindow:
            width = 1260
            height = 860
            min_width = 1080
            min_height = 680
            icon = None

        def add(self, *controls):
            self.controls.extend(controls)

        def update(self):
            pass

        def show_dialog(self, d):
            self.dialog = d

        def pop_dialog(self):
            self.dialog = None

        def run_task(self, handler):
            pass

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = StorageManager(str(Path(self.temp_dir.name) / "ui_headless.json"))
        self.page = self.HeadlessMockPage()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cockpit_view_headless_interactions(self):
        cockpit = CockpitView(self.page, self.storage)
        view = cockpit.get_view()
        self.assertIsNotNone(view)

        # 1. Duration switching
        for dur in [900, 1200, 1500, 1800, 2700, 3600]:
            cockpit._on_duration_selected(str(dur))
            self.assertEqual(cockpit.selected_duration_sec, dur)

        # 2. Ship selection
        new_ship = self.storage.add_ship("Faucon Noir", "#FF0055", "⚡")
        cockpit.reload_fleet()
        cockpit.load_ship(new_ship)
        self.assertEqual(cockpit.selected_ship.id, new_ship.id)

        # 3. Start flight ignition & cancel
        cockpit._on_main_action_clicked(None)
        self.assertEqual(cockpit.timer_engine.state, TimerState.IGNITION)
        cockpit._on_main_action_clicked(None)
        self.assertEqual(cockpit.timer_engine.state, TimerState.IDLE)

        # 4. Start flight & skip ignition to hyperdrive
        cockpit._on_main_action_clicked(None)
        cockpit._on_skip_ignition_clicked(None)
        self.assertEqual(cockpit.timer_engine.state, TimerState.FOCUSING)

        # 5. Abort flight (trigger abort dialog and confirm)
        cockpit._on_abort_clicked(None)
        self.assertIsNotNone(self.page.dialog)
        self.page.dialog.actions[1].on_click(None)
        self.assertEqual(cockpit.timer_engine.state, TimerState.IDLE)

        # 6. Start flight & complete flight
        cockpit._on_main_action_clicked(None)
        cockpit._on_skip_ignition_clicked(None)
        cockpit._on_main_action_clicked(None)
        self.assertEqual(cockpit.timer_engine.state, TimerState.IDLE)

        # Verify session logged in storage
        sessions = self.storage.get_sessions()
        self.assertEqual(len(sessions), 2)  # 1 aborted, 1 completed

    def test_missions_view_headless_interactions(self):
        launched_ships = []
        missions_view = MissionsView(
            self.page,
            self.storage,
            on_launch_ship=lambda ship: launched_ships.append(ship),
        )
        view = missions_view.get_view()
        self.assertIsNotNone(view)

        # 1. Add global & specific missions
        m_glob = self.storage.add_mission("Directive Globale Test", target_seconds=2400, is_global=True)
        ship = self.storage.add_ship("Croiseur Alpha", "#00FFCC", "🛸")
        m_spec = self.storage.add_mission("Mission Croiseur Test", target_seconds=1200, is_global=False, ship_id=ship.id, ship_name=ship.name)
        missions_view.refresh()

        # 2. Filter switches
        for f in ["all", "in_progress", "completed"]:
            missions_view._set_filter(f)
            self.assertEqual(missions_view.current_filter, f)

        # 3. Launch flight action
        missions_view._launch_mission_flight(m_spec)
        self.assertEqual(len(launched_ships), 1)
        self.assertEqual(launched_ships[0].id, ship.id)

        # 4. Toggle completion
        missions_view._toggle_mission(m_spec)
        self.assertTrue(self.storage.get_mission_by_id(m_spec.id).is_completed)

        # 5. Delete mission
        self.storage.delete_mission(m_glob.id)
        missions_view.refresh()
        self.assertIsNone(self.storage.get_mission_by_id(m_glob.id))

    def test_hangar_view_headless_interactions(self):
        hangar = HangarView(self.page, self.storage)
        view = hangar.get_view()
        self.assertIsNotNone(view)

        # 1. Filter switches
        for f in ["ALL", "SERVICE", "REBUT"]:
            hangar.selected_ship_filter = f
            hangar.refresh()
            self.assertEqual(hangar.selected_ship_filter, f)

        # 2. Add ship
        new_ship = self.storage.add_ship("Chasseur Beta", "#FF9900", "🚀")
        hangar.refresh()
        self.assertIn(new_ship.id, [s.id for s in self.storage.get_ships(include_retired=False)])

        # 3. Retire ship (au rebut)
        self.storage.retire_ship(new_ship.id)
        hangar.refresh()
        self.assertIn(new_ship.id, [s.id for s in self.storage.get_retired_ships()])

        # 4. Restore ship
        hangar._restore_ship(new_ship)
        self.assertIn(new_ship.id, [s.id for s in self.storage.get_ships(include_retired=False)])

        # 5. Export CSV trigger
        hangar._export_maintenance_csv(None)
        # Find exported files in app root
        base_dir = Path(hangar.storage.file_path).parent
        # Export with custom path
        custom_export = Path(self.temp_dir.name) / "hangar_custom_export.csv"
        self.storage.export_maintenance_log_csv(str(custom_export))
        self.assertTrue(custom_export.exists())


if __name__ == "__main__":
    unittest.main()
