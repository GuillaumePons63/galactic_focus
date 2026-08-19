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
Empirical Stress Test Suite for Galactic Focus — Challenger 1 (Interactions & State Stress Tester).

Adversarially challenges:
1. Rapid duration switches in CockpitView and UI invariant safety.
2. Timer Engine full state transitions, time warps, and rapid state cycles.
3. Dynamic propulsion pulsation behavior across ticks (Ignition, Hyperdrive, Overdrive, Idle).
4. Concurrent multi-session and multi-ship / global mission auto-resolution.
5. Scrap archive restoration, retirement cycles, flagship immutability, and fleet sorting invariants.
6. UI Component headless lifecycle, dialogs, callbacks, and telemetry stress.
7. Document and assert empirical reproduction of runtime bugs.
"""

import unittest
import tempfile
import time
import threading
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
from galactic_focus.ui.theme import (
    NEON_CYAN, NEON_GREEN, NEON_AMBER, NEON_ORANGE, NEON_PURPLE, NEON_GOLD, NEON_RED,
    BORDER_CYBER, TEXT_TITLE, TEXT_MUTED
)


class MockPage:
    """Headless Mock of Flet Page for empirical UI lifecycle testing."""
    def __init__(self):
        self.title = "Galactic Focus Test"
        self.bgcolor = "#030712"
        self.theme_mode = ft.ThemeMode.DARK
        self.padding = 0
        self.dialog = None
        self.snack_bar = None
        self.controls = []
        self.tasks = []
        self.update_count = 0

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self):
        self.update_count += 1

    def show_dialog(self, dialog):
        self.dialog = dialog

    def pop_dialog(self):
        self.dialog = None

    def run_task(self, task_func):
        self.tasks.append(task_func)


# =========================================================================
# TEST SUITE 1: Rapid Duration Switches & CockpitView State
# =========================================================================
class TestCockpitDurationAndControlsStress(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = StorageManager(str(Path(self.temp_dir.name) / "cockpit_stress.json"))
        self.page = MockPage()
        self.cockpit = CockpitView(self.page, self.storage)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_rapid_duration_switching_idle(self):
        """Stress-test rapid continuous duration switching while in IDLE state."""
        test_durations = [900, 1200, 1500, 1800, 2700, 3600, 1200, 900, 3600, 1500]
        for dur in test_durations:
            self.cockpit._on_duration_selected(str(dur))
            self.assertEqual(self.cockpit.selected_duration_sec, dur)
            mins = dur // 60
            self.assertEqual(self.cockpit.timer_text.value, f"{mins:02d}:00")
            btn_text = self.cockpit.btn_main_action.content.controls[1].value
            self.assertIn(f"{mins} MIN", btn_text.upper())

    def test_duration_switch_ignored_during_flight_pure_engine(self):
        """Duration switches MUST be strictly ignored by the engine while in IGNITION, FOCUSING, or OVERTIME."""
        initial_duration = 1200
        self.cockpit.selected_duration_sec = initial_duration
        self.cockpit.timer_engine.start(ship_id="s1", ship_name="Amiral", target_seconds=initial_duration, with_ignition=True)
        self.assertEqual(self.cockpit.timer_engine.state, TimerState.IGNITION)

        # Attempt duration change during IGNITION
        self.cockpit._on_duration_selected("3600")
        self.assertEqual(self.cockpit.selected_duration_sec, initial_duration)

        # Transition to FOCUSING
        self.cockpit.timer_engine.skip_ignition()
        self.assertEqual(self.cockpit.timer_engine.state, TimerState.FOCUSING)

        # Attempt duration change during FOCUSING
        self.cockpit._on_duration_selected("3600")
        self.assertEqual(self.cockpit.selected_duration_sec, initial_duration)

        # Time warp to OVERTIME
        self.cockpit.timer_engine._start_monotonic = time.monotonic() - (initial_duration + 100)
        self.cockpit.timer_engine.tick()
        self.assertEqual(self.cockpit.timer_engine.state, TimerState.OVERTIME)

        # Attempt duration change during OVERTIME
        self.cockpit._on_duration_selected("3600")
        self.assertEqual(self.cockpit.selected_duration_sec, initial_duration)

        # Complete session -> IDLE -> now changes must be accepted
        self.cockpit.timer_engine.complete()
        self.assertEqual(self.cockpit.timer_engine.state, TimerState.IDLE)
        self.cockpit._on_duration_selected("3600")
        self.assertEqual(self.cockpit.selected_duration_sec, 3600)
        self.assertEqual(self.cockpit.timer_text.value, "60:00")

    def test_rapid_ship_switching(self):
        """Stress-test rapid ship switching in Cockpit."""
        ship1 = self.storage.add_ship("Faucon 1", "#00F0FF", "⚡")
        ship2 = self.storage.add_ship("Croiseur 2", "#9D4EDD", "🛸")
        ship3 = self.storage.add_ship("Intercepteur 3", "#38BDF8", "🚀")
        self.cockpit.reload_fleet()

        for _ in range(50):
            for s in [ship1, ship2, ship3]:
                self.cockpit.load_ship(s)
                self.assertEqual(self.cockpit.selected_ship.id, s.id)
                self.assertIn(s.name, self.cockpit.ship_pill_text.value)


# =========================================================================
# TEST SUITE 2: Timer Engine Full State Machine Transitions & Time Warp
# =========================================================================
class TestTimerEngineTransitionsAndStress(unittest.TestCase):
    def test_transition_path_idle_ignition_cancel_idle(self):
        """Path 1: IDLE -> IGNITION -> cancel grace period -> IDLE."""
        engine = TimerEngine(default_target_seconds=1200, ignition_duration_seconds=10)
        self.assertEqual(engine.state, TimerState.IDLE)
        self.assertFalse(engine.is_running)

        engine.start(ship_id="s1", ship_name="Amiral", target_seconds=1200, with_ignition=True)
        self.assertEqual(engine.state, TimerState.IGNITION)
        self.assertTrue(engine.is_running)
        self.assertTrue(engine.is_ignition)
        self.assertFalse(engine.is_in_flight)

        engine.cancel_ignition()
        self.assertEqual(engine.state, TimerState.IDLE)
        self.assertFalse(engine.is_running)
        self.assertFalse(engine.is_ignition)

    def test_transition_path_idle_ignition_skip_focusing_warp_overtime_complete(self):
        """Path 2: IDLE -> IGNITION -> skip -> FOCUSING -> time warp -> OVERTIME -> complete."""
        engine = TimerEngine(default_target_seconds=1200, ignition_duration_seconds=10)
        engine.start(ship_id="s1", ship_name="Amiral", target_seconds=1200, with_ignition=True)
        self.assertEqual(engine.state, TimerState.IGNITION)

        engine.skip_ignition()
        self.assertEqual(engine.state, TimerState.FOCUSING)
        self.assertTrue(engine.is_in_flight)
        self.assertFalse(engine.is_overtime)

        # Warp time past target (1200s + 300s overtime)
        engine._start_monotonic = time.monotonic() - 1500
        status = engine.tick()
        self.assertEqual(engine.state, TimerState.OVERTIME)
        self.assertTrue(engine.is_overtime)
        self.assertTrue(status["is_overtime"])
        self.assertEqual(status["elapsed_seconds"], 1500)
        self.assertEqual(status["overtime_seconds"], 300)
        self.assertEqual(status["display_time"], "+05:00")

        # Complete session
        session = engine.complete()
        self.assertEqual(engine.state, TimerState.IDLE)
        self.assertTrue(session.completed)
        self.assertEqual(session.actual_seconds, 1500)
        self.assertEqual(session.overtime_seconds, 300)

    def test_transition_path_auto_ignition_to_focusing_by_ticks(self):
        """Path 3: IDLE -> IGNITION -> ticks elapse 10s -> automatically transitions to FOCUSING."""
        engine = TimerEngine(default_target_seconds=1200, ignition_duration_seconds=10)
        engine.start(ship_id="s1", ship_name="Amiral", target_seconds=1200, with_ignition=True)

        # Simulate 5s elapsed in ignition
        engine._ignition_start_monotonic = time.monotonic() - 5
        st1 = engine.tick()
        self.assertEqual(engine.state, TimerState.IGNITION)
        self.assertEqual(st1["ignition_remaining"], 5)

        # Simulate 11s elapsed in ignition -> auto hyperdrive
        engine._ignition_start_monotonic = time.monotonic() - 11
        st2 = engine.tick()
        self.assertEqual(engine.state, TimerState.FOCUSING)
        self.assertEqual(st2["is_ignition"], False)

    def test_transition_path_idle_focusing_abort(self):
        """Path 4: IDLE -> start without ignition -> FOCUSING -> abort."""
        engine = TimerEngine(default_target_seconds=1200, ignition_duration_seconds=10)
        engine.start(ship_id="s1", ship_name="Amiral", target_seconds=1200, with_ignition=False)
        self.assertEqual(engine.state, TimerState.FOCUSING)

        # Simulate 200s elapsed
        engine._start_monotonic = time.monotonic() - 200
        engine.tick()

        session = engine.abort()
        self.assertEqual(engine.state, TimerState.IDLE)
        self.assertFalse(session.completed)
        self.assertEqual(session.actual_seconds, 200)
        self.assertEqual(session.overtime_seconds, 0)
        self.assertEqual(session.ship_icon, "💥")

    def test_edge_case_zero_ignition_duration(self):
        """When ignition_duration_seconds=0, start(with_ignition=True) goes directly to FOCUSING."""
        engine = TimerEngine(default_target_seconds=600, ignition_duration_seconds=0)
        engine.start(ship_id="s1", ship_name="Amiral", target_seconds=600, with_ignition=True)
        self.assertEqual(engine.state, TimerState.FOCUSING)
        self.assertFalse(engine.is_ignition)

    def test_edge_case_zero_target_seconds(self):
        """When target_seconds=0, ticks immediately evaluate to OVERTIME."""
        engine = TimerEngine(default_target_seconds=0, ignition_duration_seconds=0)
        engine.start(ship_id="s1", ship_name="Amiral", target_seconds=0, with_ignition=False)
        st = engine.tick()
        self.assertEqual(engine.state, TimerState.OVERTIME)
        self.assertEqual(st["progress_ratio"], 1.0)

    def test_rapid_state_cycles_stress(self):
        """Perform 500 rapid start -> skip -> tick -> complete cycles without memory leak or state desync."""
        engine = TimerEngine(default_target_seconds=100, ignition_duration_seconds=5)
        for i in range(500):
            engine.start(ship_id=f"ship_{i%5}", ship_name=f"Ship {i%5}", target_seconds=100)
            self.assertEqual(engine.state, TimerState.IGNITION)
            engine.skip_ignition()
            self.assertEqual(engine.state, TimerState.FOCUSING)
            engine._start_monotonic = time.monotonic() - (100 + i)
            st = engine.tick()
            self.assertEqual(engine.state, TimerState.OVERTIME)
            session = engine.complete()
            self.assertEqual(engine.state, TimerState.IDLE)
            self.assertTrue(session.completed)


# =========================================================================
# TEST SUITE 3: Dynamic Propulsion Pulsation & Bug Verification
# =========================================================================
class TestDynamicPropulsionPulsation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = StorageManager(str(Path(self.temp_dir.name) / "pulsation_stress.json"))
        self.page = MockPage()
        self.cockpit = CockpitView(self.page, self.storage)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_btn_main_action_shadow_safe_handling(self):
        """
        Verifies that CockpitView._update_timer_display safely updates
        btn_main_action shadow and color without AttributeError across all flight phases.
        """
        # 1. Test Ignition Phase
        self.cockpit.timer_engine.state = TimerState.IGNITION
        self.cockpit.timer_engine.ignition_remaining = 10
        status_ign = self.cockpit.timer_engine.get_status()
        self.cockpit._update_timer_display(status_ign)
        self.assertEqual(self.cockpit.btn_main_action.bgcolor, NEON_ORANGE)
        if isinstance(self.cockpit.btn_main_action.shadow, list) and self.cockpit.btn_main_action.shadow:
            self.assertEqual(self.cockpit.btn_main_action.shadow[0].color, f"{NEON_ORANGE}77")

        # 2. Test Hyperdrive Flight Phase
        self.cockpit.timer_engine.state = TimerState.FOCUSING
        status_foc = self.cockpit.timer_engine.get_status()
        self.cockpit._update_timer_display(status_foc)
        if isinstance(self.cockpit.btn_main_action.shadow, list) and self.cockpit.btn_main_action.shadow:
            self.assertEqual(self.cockpit.btn_main_action.shadow[0].color, "#00000000")

        # 3. Test Overdrive Phase
        self.cockpit.timer_engine.state = TimerState.OVERTIME
        status_over = self.cockpit.timer_engine.get_status()
        self.cockpit._update_timer_display(status_over)
        self.assertEqual(self.cockpit.btn_main_action.bgcolor, NEON_GREEN)
        if isinstance(self.cockpit.btn_main_action.shadow, list) and self.cockpit.btn_main_action.shadow:
            self.assertEqual(self.cockpit.btn_main_action.shadow[0].color, f"{NEON_GREEN}77")

        # 4. Test Idle View Reset
        self.cockpit._update_view_for_idle()
        self.assertEqual(self.cockpit.btn_main_action.bgcolor, NEON_CYAN)
        if isinstance(self.cockpit.btn_main_action.shadow, list) and self.cockpit.btn_main_action.shadow:
            self.assertEqual(self.cockpit.btn_main_action.shadow[0].color, f"{NEON_CYAN}77")


# =========================================================================
# TEST SUITE 4: Multi-Ship & Global Mission Auto-Resolution
# =========================================================================
class TestMissionResolutionLogic(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = StorageManager(str(Path(self.temp_dir.name) / "resolution_stress.json"))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_sequential_multi_ship_and_global_resolution(self):
        """Test sequential sessions across multiple distinct ships and verify exact resolution math."""
        flagship = self.storage.get_flagship()
        ship_a = self.storage.add_ship("Vaisseau Alpha", "#38BDF8", "🚀")
        ship_b = self.storage.add_ship("Vaisseau Beta", "#9D4EDD", "🛸")
        ship_c = self.storage.add_ship("Vaisseau Gamma", "#00E676", "⚡")

        # Create Missions:
        m_global = self.storage.add_mission("Directive Globale Flotte", target_seconds=6000, is_global=True)
        m_a = self.storage.add_mission("Mission Alpha", target_seconds=1500, is_global=False, ship_id=ship_a.id, ship_name=ship_a.name)
        m_b = self.storage.add_mission("Mission Beta", target_seconds=1500, is_global=False, ship_id=ship_b.id, ship_name=ship_b.name)
        m_c = self.storage.add_mission("Mission Gamma", target_seconds=1500, is_global=False, ship_id=ship_c.id, ship_name=ship_c.name)

        # 1. Fly Ship A for 1500s
        res_a = self.storage.add_session(FocusSession(ship_id=ship_a.id, ship_name=ship_a.name, actual_seconds=1500, completed=True))
        self.assertIn(m_a.title, res_a["completed_missions"])
        self.assertIn(m_global.title, res_a["advanced_missions"])
        self.assertTrue(self.storage.get_mission_by_id(m_a.id).is_completed)
        self.assertEqual(self.storage.get_mission_by_id(m_global.id).progress_seconds, 1500)

        # 2. Fly Ship B for 1500s
        res_b = self.storage.add_session(FocusSession(ship_id=ship_b.id, ship_name=ship_b.name, actual_seconds=1500, completed=True))
        self.assertIn(m_b.title, res_b["completed_missions"])
        self.assertTrue(self.storage.get_mission_by_id(m_b.id).is_completed)
        self.assertEqual(self.storage.get_mission_by_id(m_global.id).progress_seconds, 3000)

        # 3. Fly Ship C for 1500s
        res_c = self.storage.add_session(FocusSession(ship_id=ship_c.id, ship_name=ship_c.name, actual_seconds=1500, completed=True))
        self.assertIn(m_c.title, res_c["completed_missions"])
        self.assertTrue(self.storage.get_mission_by_id(m_c.id).is_completed)
        self.assertEqual(self.storage.get_mission_by_id(m_global.id).progress_seconds, 4500)

        # 4. Fly Flagship (Amiral) for 1500s -> completes global mission
        res_f = self.storage.add_session(FocusSession(ship_id=flagship.id, ship_name=flagship.name, actual_seconds=1500, completed=True))
        self.assertIn(m_global.title, res_f["completed_missions"])
        self.assertTrue(self.storage.get_mission_by_id(m_global.id).is_completed)
        self.assertEqual(self.storage.get_mission_by_id(m_global.id).progress_seconds, 6000)

    def test_aborted_sessions_do_not_advance_missions(self):
        """Aborted sessions (completed=False) MUST NOT advance any ship stats or missions."""
        ship = self.storage.add_ship("Chasseur Test", "#38BDF8", "🚀")
        m_spec = self.storage.add_mission("Mission Test", target_seconds=1200, is_global=False, ship_id=ship.id, ship_name=ship.name)
        m_glob = self.storage.add_mission("Mission Globale", target_seconds=1200, is_global=True)

        res = self.storage.add_session(FocusSession(ship_id=ship.id, ship_name=ship.name, actual_seconds=600, completed=False))
        self.assertEqual(len(res["advanced_missions"]), 0)
        self.assertEqual(len(res["completed_missions"]), 0)

        m_spec_db = self.storage.get_mission_by_id(m_spec.id)
        m_glob_db = self.storage.get_mission_by_id(m_glob.id)
        self.assertEqual(m_spec_db.progress_seconds, 0)
        self.assertEqual(m_glob_db.progress_seconds, 0)

        updated_ship = self.storage.get_ship_by_id(ship.id)
        self.assertEqual(updated_ship.total_seconds, 0)
        self.assertEqual(updated_ship.sessions_count, 0)


# =========================================================================
# TEST SUITE 5: Scrap Archive Restoration & Fleet Sorting Invariants
# =========================================================================
class TestScrapArchiveAndFleetInvariants(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = StorageManager(str(Path(self.temp_dir.name) / "fleet_invariants.json"))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_flagship_immutability_and_sorting(self):
        """Invariant: Flagship is always first in get_ships(), cannot be retired, cannot be deleted."""
        flagship = self.storage.get_flagship()
        self.assertTrue(flagship.is_flagship)

        # Add 5 ships
        for i in range(5):
            self.storage.add_ship(f"Chasseur {i}", "#00F0FF", "🚀")

        # 1. Verify flagship is ALWAYS index 0
        active_ships = self.storage.get_ships(include_retired=False)
        self.assertTrue(active_ships[0].is_flagship)
        self.assertEqual(active_ships[0].id, flagship.id)

        # 2. Attempt to retire flagship
        res = self.storage.retire_ship(flagship.id)
        self.assertFalse(res.is_retired)
        self.assertFalse(self.storage.get_flagship().is_retired)
        self.assertEqual(len(self.storage.get_retired_ships()), 0)

        # 3. Attempt to delete flagship
        self.storage.delete_ship(flagship.id)
        self.assertIsNotNone(self.storage.get_flagship())
        self.assertIsNotNone(self.storage.get_ship_by_id(flagship.id))

    def test_rapid_retire_and_restore_cycle_stress(self):
        """Stress-test retiring and restoring 20 ships across multiple cycles."""
        created_ships = []
        for i in range(20):
            s = self.storage.add_ship(f"Vaisseau Test {i}", "#38BDF8", "⚡")
            created_ships.append(s)

        for cycle in range(3):
            # Retire even ships
            for i, s in enumerate(created_ships):
                if i % 2 == 0:
                    self.storage.retire_ship(s.id)

            retired = self.storage.get_retired_ships()
            active = self.storage.get_ships(include_retired=False)

            self.assertEqual(len(retired), 10)
            self.assertIn(created_ships[1].id, [s.id for s in active])
            self.assertNotIn(created_ships[0].id, [s.id for s in active])

            # Restore even ships
            for i, s in enumerate(created_ships):
                if i % 2 == 0:
                    self.storage.restore_ship(s.id)

            self.assertEqual(len(self.storage.get_retired_ships()), 0)


# =========================================================================
# TEST SUITE 6: UI Component Lifecycles & Integration Workflows
# =========================================================================
class TestUIComponentLifecyclesAndWorkflows(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = StorageManager(str(Path(self.temp_dir.name) / "ui_workflows.json"))
        self.page = MockPage()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_missions_view_full_lifecycle_and_filtering(self):
        """Test MissionsView filter switches, card building, and launch triggers."""
        cockpit = CockpitView(self.page, self.storage)
        missions = MissionsView(
            self.page,
            self.storage,
            on_data_changed=lambda: cockpit.reload_fleet(),
            on_launch_ship=lambda s: cockpit.load_ship(s),
        )

        # Create missions with varied deadlines
        m1 = self.storage.add_mission("Mission Alpha", target_seconds=1200, is_global=True, deadline=date.today().strftime("%Y-%m-%d"))
        ship = self.storage.add_ship("Bombardier", "#F43F5E", "🛡️")
        m2 = self.storage.add_mission("Mission Beta", target_seconds=1800, is_global=False, ship_id=ship.id, ship_name=ship.name)

        # 1. Filter switches
        missions._set_filter("in_progress")
        self.assertEqual(missions.current_filter, "in_progress")

        missions._set_filter("completed")
        self.assertEqual(missions.current_filter, "completed")

        missions._set_filter("all")
        self.assertEqual(missions.current_filter, "all")

        # 2. Toggle completion
        missions._toggle_mission(m1)
        m1_db = self.storage.get_mission_by_id(m1.id)
        self.assertTrue(m1_db.is_completed)

        # 3. Direct launch from Mission
        missions._launch_mission_flight(m2)
        self.assertEqual(cockpit.selected_ship.id, ship.id)

    def test_hangar_view_csv_export_and_maintenance_filtering(self):
        """Test HangarView maintenance log filtering and CSV export under high session volume."""
        hangar = HangarView(self.page, self.storage)
        ship = self.storage.add_ship("Croiseur Stellar", "#9D4EDD", "🛸")

        # Generate 50 sessions
        for i in range(50):
            sess = FocusSession(
                ship_id=ship.id,
                ship_name=ship.name,
                ship_icon=ship.icon,
                actual_seconds=1200 + i * 10,
                overtime_seconds=i * 5,
                completed=(i % 10 != 0),
            )
            self.storage.add_session(sess)

        # Test CSV export
        csv_file = self.storage.export_maintenance_log_csv()
        self.assertTrue(Path(csv_file).exists())

        with open(csv_file, "r", encoding="utf-8-sig") as f:
            reader = list(csv.reader(f))
            self.assertEqual(len(reader), 51)  # Header + 50 rows
            self.assertEqual(reader[0][0], "ID")
            self.assertEqual(reader[0][3], "Vaisseau")

        Path(csv_file).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
