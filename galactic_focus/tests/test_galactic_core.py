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
Comprehensive unit & integration test suite for Galactic Focus V3.4.
Covers Models, Storage, Automatic Mission Resolution, Timer Engine, CSV Exports, and UI View Workflows.
"""
import unittest
import tempfile
import time
import csv
from pathlib import Path
from datetime import date, timedelta, datetime
import flet as ft

from galactic_focus.core.models import Ship, FocusSession, Mission, DailyFleetSummary, get_ship_model_for_duration
from galactic_focus.core.storage import StorageManager
from galactic_focus.core.timer_engine import TimerEngine, TimerState
from galactic_focus.ui.cockpit_view import CockpitView
from galactic_focus.ui.missions_view import MissionsView
from galactic_focus.ui.hangar_view import HangarView


class TestGalacticModels(unittest.TestCase):
    def test_ship_serialization_and_flagship(self):
        s = Ship(name="Vaisseau Amiral", color="#00F0FF", icon="🪐", is_flagship=True, total_seconds=7300, sessions_count=5)
        d = s.to_dict()
        s2 = Ship.from_dict(d)
        self.assertEqual(s2.name, "Vaisseau Amiral")
        self.assertTrue(s2.is_flagship)
        self.assertFalse(s2.is_retired)
        self.assertEqual(s2.sessions_count, 5)
        self.assertEqual(s2.formatted_total_time, "2h 01m")

    def test_ship_retirement_model(self):
        s = Ship(name="Navette Cargo", is_retired=True, retired_at="2026-08-19T12:00:00")
        d = s.to_dict()
        s2 = Ship.from_dict(d)
        self.assertTrue(s2.is_retired)
        self.assertEqual(s2.retired_at, "2026-08-19T12:00:00")

    def test_mission_progress_and_formatting(self):
        m = Mission(
            title="Module Propulsion",
            target_seconds=3600,
            progress_seconds=1800,
            is_global=False,
            ship_id="ship_1",
            ship_name="Intercepteur",
        )
        self.assertAlmostEqual(m.progress_ratio, 0.5)
        self.assertFalse(m.is_completed)
        self.assertEqual(m.formatted_target_time, "1h 00m")
        self.assertEqual(m.formatted_progress_time, "30 min")

    def test_mission_deadlines_dynamic_badges(self):
        today_str = date.today().strftime("%Y-%m-%d")
        tomorrow_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        in_3_days_str = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")
        overdue_str = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")

        # 1. Without deadline
        m_none = Mission(title="M1", deadline="")
        self.assertEqual(m_none.deadline_info["label"], "Sans date limite")
        self.assertFalse(m_none.deadline_info["is_urgent"])

        # 2. Overdue
        m_overdue = Mission(title="M2", deadline=overdue_str)
        self.assertTrue(m_overdue.deadline_info["is_urgent"])
        self.assertTrue(m_overdue.deadline_info["is_expired"])
        self.assertIn("En retard", m_overdue.deadline_info["label"])

        # 3. Today
        m_today = Mission(title="M3", deadline=today_str)
        self.assertTrue(m_today.deadline_info["is_urgent"])
        self.assertIn("aujourd'hui", m_today.deadline_info["label"])

        # 4. Tomorrow
        m_tomorrow = Mission(title="M4", deadline=tomorrow_str)
        self.assertTrue(m_tomorrow.deadline_info["is_urgent"])
        self.assertIn("demain", m_tomorrow.deadline_info["label"])

        # 5. In 3 days
        m_3j = Mission(title="M5", deadline=in_3_days_str)
        self.assertFalse(m_3j.deadline_info["is_urgent"])
        self.assertIn("Dans 3 jours", m_3j.deadline_info["label"])

        # 6. Completed
        m_done = Mission(title="M6", deadline=overdue_str, status="completed", progress_seconds=1200, target_seconds=1200)
        self.assertFalse(m_done.deadline_info["is_urgent"])
        self.assertIn("Terminée", m_done.deadline_info["label"])

    def test_focus_session_durations_and_overtime(self):
        s = FocusSession(
            ship_id="s1",
            ship_name="Croiseur",
            actual_seconds=1500,
            overtime_seconds=300,
            completed=True,
        )
        self.assertEqual(s.formatted_duration, "25:00 min")
        self.assertEqual(s.formatted_overtime, "+05:00")
        self.assertTrue(s.completed)


class TestStorageManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_file = Path(self.temp_dir.name) / "test_data.json"
        self.storage = StorageManager(str(self.temp_file))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_flagship_presence_and_protection(self):
        flagship = self.storage.get_flagship()
        self.assertIsNotNone(flagship)
        self.assertTrue(flagship.is_flagship)
        self.assertEqual(flagship.name, "Vaisseau Amiral")

        # Attempt to retire flagship -> must remain active
        self.storage.retire_ship(flagship.id)
        f_check = self.storage.get_flagship()
        self.assertFalse(f_check.is_retired)

        # Attempt to delete flagship -> must remain in storage
        self.storage.delete_ship(flagship.id)
        self.assertIsNotNone(self.storage.get_ship_by_id(flagship.id))

    def test_ship_crud_and_retirement(self):
        # 1. Add custom ship
        ship = self.storage.add_ship("Faucon Noir", "#FF007F", "⚡")
        self.assertIsNotNone(ship.id)
        self.assertEqual(ship.name, "Faucon Noir")
        self.assertFalse(ship.is_retired)

        # 2. Update ship
        ship.name = "Faucon Stellaire Modifié"
        self.storage.update_ship(ship)
        up_s = self.storage.get_ship_by_id(ship.id)
        self.assertEqual(up_s.name, "Faucon Stellaire Modifié")

        # 3. Retire ship (Mise au rebut)
        self.storage.retire_ship(ship.id)
        active_ships = self.storage.get_ships(include_retired=False)
        retired_ships = self.storage.get_retired_ships()

        self.assertNotIn(ship.id, [s.id for s in active_ships])
        self.assertIn(ship.id, [s.id for s in retired_ships])

        # 4. Restore ship
        self.storage.restore_ship(ship.id)
        self.assertIn(ship.id, [s.id for s in self.storage.get_ships(include_retired=False)])
        self.assertEqual(len(self.storage.get_retired_ships()), 0)

        # 5. Delete regular ship
        self.storage.delete_ship(ship.id)
        self.assertIsNone(self.storage.get_ship_by_id(ship.id))

    def test_mission_crud_operations(self):
        # 1. Add Global Mission
        m_glob = self.storage.add_mission("Deep Work Global", target_seconds=3600, is_global=True)
        self.assertTrue(m_glob.is_global)
        self.assertEqual(m_glob.ship_id, "")

        # 2. Add Specific Mission
        ship = self.storage.add_ship("Chasseur Alpha", "#00FF66", "🚀")
        m_spec = self.storage.add_mission(
            "Mission Chasseur",
            target_seconds=1800,
            is_global=False,
            ship_id=ship.id,
            ship_name=ship.name,
            ship_icon=ship.icon,
        )
        self.assertFalse(m_spec.is_global)
        self.assertEqual(m_spec.ship_id, ship.id)

        # 3. Toggle completion
        toggled = self.storage.toggle_mission_completed(m_spec.id)
        self.assertTrue(toggled.is_completed)
        self.assertIsNotNone(toggled.completed_at)

        # 4. Delete mission
        self.storage.delete_mission(m_glob.id)
        self.assertIsNone(self.storage.get_mission_by_id(m_glob.id))

    def test_automatic_resolution_of_global_and_specific_missions(self):
        flagship = self.storage.get_flagship()
        custom_ship = self.storage.add_ship("Intercepteur Beta", "#38BDF8", "🚀")

        # Create 1 Global mission (2400s) and 1 Specific mission (1200s)
        m_global = self.storage.add_mission("Mission Globale Semaine", target_seconds=2400, is_global=True)
        m_specific = self.storage.add_mission("Mission Beta", target_seconds=1200, is_global=False, ship_id=custom_ship.id, ship_name=custom_ship.name)

        # Session 1: Pilot custom ship for 1200s
        s1 = FocusSession(
            ship_id=custom_ship.id,
            ship_name=custom_ship.name,
            ship_icon=custom_ship.icon,
            target_seconds=1200,
            actual_seconds=1200,
            completed=True,
        )
        res1 = self.storage.add_session(s1)

        # Both specific AND global missions must have progressed
        self.assertIn("Mission Beta", res1["advanced_missions"])
        self.assertIn("Mission Globale Semaine", res1["advanced_missions"])
        self.assertIn("Mission Beta", res1["completed_missions"])

        m_spec_db = self.storage.get_mission_by_id(m_specific.id)
        m_glob_db = self.storage.get_mission_by_id(m_global.id)
        self.assertTrue(m_spec_db.is_completed)
        self.assertEqual(m_glob_db.progress_seconds, 1200)
        self.assertFalse(m_glob_db.is_completed)

        # Session 2: Pilot Vaisseau Amiral for 1200s
        s2 = FocusSession(
            ship_id=flagship.id,
            ship_name=flagship.name,
            ship_icon=flagship.icon,
            target_seconds=1200,
            actual_seconds=1200,
            completed=True,
        )
        res2 = self.storage.add_session(s2)

        self.assertIn("Mission Globale Semaine", res2["advanced_missions"])
        self.assertIn("Mission Globale Semaine", res2["completed_missions"])

        m_glob_db2 = self.storage.get_mission_by_id(m_global.id)
        self.assertTrue(m_glob_db2.is_completed)
        self.assertEqual(m_glob_db2.progress_seconds, 2400)

    def test_maintenance_log_csv_export(self):
        ship = self.storage.add_ship("Croiseur Gamma", "#FF9E00", "🛸")
        session = FocusSession(
            ship_id=ship.id,
            ship_name=ship.name,
            ship_icon=ship.icon,
            actual_seconds=1800,
            overtime_seconds=120,
            completed=True,
        )
        self.storage.add_session(session)

        csv_path = self.storage.export_maintenance_log_csv()
        self.assertTrue(Path(csv_path).exists())

        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader)
            self.assertIn("Vaisseau", headers)
            self.assertIn("Temps de Vol (min)", headers)
            self.assertIn("Statut de Vol", headers)

            row = next(reader)
            self.assertIn("Croiseur Gamma", row[3])

        # Cleanup test csv
        Path(csv_path).unlink(missing_ok=True)


class TestTimerEngine(unittest.TestCase):
    def test_full_timer_state_machine(self):
        engine = TimerEngine(default_target_seconds=10, ignition_duration_seconds=10)
        self.assertEqual(engine.state, TimerState.IDLE)

        # 1. Start with ignition
        engine.start(ship_id="s1", ship_name="Amiral", ship_icon="🪐", target_seconds=10, with_ignition=True)
        self.assertEqual(engine.state, TimerState.IGNITION)
        self.assertTrue(engine.is_ignition)

        # 2. Skip ignition
        engine.skip_ignition()
        self.assertEqual(engine.state, TimerState.FOCUSING)

        # 3. Simulate target completion & overtime
        engine._start_monotonic = time.monotonic() - 15
        status = engine.tick()
        self.assertEqual(engine.state, TimerState.OVERTIME)
        self.assertTrue(status["is_overtime"])

        # 4. Land & Complete
        session = engine.complete()
        self.assertEqual(engine.state, TimerState.IDLE)
        self.assertTrue(session.completed)
        self.assertEqual(session.actual_seconds, 15)
        self.assertEqual(session.overtime_seconds, 5)

    def test_ignition_cancel_grace_period(self):
        engine = TimerEngine(default_target_seconds=20, ignition_duration_seconds=10)
        engine.start(ship_id="s1", ship_name="Amiral", ship_icon="🪐", target_seconds=20, with_ignition=True)
        self.assertEqual(engine.state, TimerState.IGNITION)

        # Cancel within 10s -> returns to IDLE without recording damage
        engine.cancel_ignition()
        self.assertEqual(engine.state, TimerState.IDLE)

    def test_abort_flight(self):
        engine = TimerEngine(default_target_seconds=20, ignition_duration_seconds=0)
        engine.start(ship_id="s1", ship_name="Amiral", ship_icon="🪐", target_seconds=20, with_ignition=False)
        self.assertEqual(engine.state, TimerState.FOCUSING)

        session = engine.abort()
        self.assertEqual(engine.state, TimerState.IDLE)
        self.assertFalse(session.completed)


class TestUIViewsWorkflow(unittest.TestCase):
    class MockWindow:
        icon = None

    class MockPage:
        def __init__(self):
            self.title = ""
            self.bgcolor = ""
            self.theme_mode = None
            self.padding = 0
            self.window = TestUIViewsWorkflow.MockWindow()
            self.dialog = None

        def add(self, c):
            pass

        def update(self):
            pass

        def show_dialog(self, d):
            self.dialog = d

        def pop_dialog(self):
            self.dialog = None

        def run_task(self, h):
            pass

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = StorageManager(str(Path(self.temp_dir.name) / "ui_test.json"))
        self.page = self.MockPage()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_views_initialization_and_sync(self):
        cockpit = CockpitView(self.page, self.storage)
        missions = MissionsView(self.page, self.storage, on_launch_ship=lambda s: cockpit.load_ship(s))
        hangar = HangarView(self.page, self.storage)

        # 1. Check Cockpit controls
        self.assertIsNotNone(cockpit.get_view())
        self.assertEqual(cockpit.selected_duration_sec, 1200)

        # 2. Add ship from Hangar and verify sync in Cockpit
        new_ship = self.storage.add_ship("Chasseur Stealth", "#FF007F", "🛡️")
        cockpit.reload_fleet()
        missions.refresh()
        hangar.refresh()

        self.assertIn(new_ship.id, [opt.key for opt in cockpit.ship_dropdown.options])

        # 3. Launch mission from MissionsView loads ship in Cockpit
        m = self.storage.add_mission("Mission Infiltration", target_seconds=1200, is_global=False, ship_id=new_ship.id, ship_name=new_ship.name)
        missions._launch_mission_flight(m)
        self.assertEqual(cockpit.selected_ship.id, new_ship.id)


if __name__ == "__main__":
    unittest.main()
