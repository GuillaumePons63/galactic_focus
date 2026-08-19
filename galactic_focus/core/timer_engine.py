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
Timer engine for Galactic Focus with 10s ignition countdown, precision tracking, overtime flow, and ship/mission binding.
"""
import time
from enum import Enum
from datetime import datetime
from typing import Optional

from .models import FocusSession, get_ship_model_for_duration


class TimerState(str, Enum):
    IDLE = "IDLE"
    IGNITION = "IGNITION"      # 10-second countdown grace period
    FOCUSING = "FOCUSING"      # Main countdown (e.g. 20 min down to 0)
    OVERTIME = "OVERTIME"      # Post-target overtime count-up (+MM:SS)
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


class TimerEngine:
    def __init__(self, default_target_seconds: int = 1200, ignition_duration_seconds: int = 10):
        self.default_target_seconds = default_target_seconds
        self.ignition_duration_seconds = ignition_duration_seconds
        self.target_seconds = default_target_seconds
        self.state: TimerState = TimerState.IDLE
        
        self.ship_id: str = ""
        self.ship_name: str = ""
        self.ship_icon: str = "🚀"
        self.mission_id: str = ""
        self.mission_title: str = ""
        
        self._ignition_start_monotonic: Optional[float] = None
        self._start_monotonic: Optional[float] = None
        self._started_at_iso: str = ""
        self._ended_at_iso: str = ""
        
        self.ignition_remaining: int = 10
        self.elapsed_seconds: int = 0
        self.overtime_seconds: int = 0

    @property
    def is_running(self) -> bool:
        return self.state in (TimerState.IGNITION, TimerState.FOCUSING, TimerState.OVERTIME)

    @property
    def is_in_flight(self) -> bool:
        return self.state in (TimerState.FOCUSING, TimerState.OVERTIME)

    @property
    def is_ignition(self) -> bool:
        return self.state == TimerState.IGNITION

    @property
    def is_overtime(self) -> bool:
        return self.state == TimerState.OVERTIME

    def start(
        self,
        ship_id: str = "",
        ship_name: str = "",
        ship_icon: str = "🚀",
        target_seconds: Optional[int] = None,
        with_ignition: bool = True,
        mission_id: str = "",
        mission_title: str = "",
        # Backward compatibility args
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
    ):
        """Starts a flight session with ignition countdown or directly in hyperdrive."""
        self.target_seconds = target_seconds or self.default_target_seconds
        self.ship_id = ship_id or project_id or ""
        self.ship_name = ship_name or project_name or "Vaisseau"
        self.ship_icon = ship_icon
        self.mission_id = mission_id
        self.mission_title = mission_title
        self.elapsed_seconds = 0
        self.overtime_seconds = 0
        self._started_at_iso = datetime.now().isoformat()

        if with_ignition and self.ignition_duration_seconds > 0:
            self.state = TimerState.IGNITION
            self._ignition_start_monotonic = time.monotonic()
            self.ignition_remaining = self.ignition_duration_seconds
            self._start_monotonic = None
        else:
            self._engage_hyperdrive()

    def _engage_hyperdrive(self):
        """Transitions into active hyperdrive focus mode."""
        self.state = TimerState.FOCUSING
        self._start_monotonic = time.monotonic()
        self._ignition_start_monotonic = None
        self.ignition_remaining = 0

    def cancel_ignition(self):
        """Cancels during 10s countdown grace period without registering any flight."""
        self.reset()

    def skip_ignition(self):
        """Immediately starts hyperdrive without waiting for 10s countdown to finish."""
        if self.state == TimerState.IGNITION:
            self._engage_hyperdrive()

    def tick(self) -> dict:
        """Updates internal flight timing metrics."""
        if self.state == TimerState.IGNITION and self._ignition_start_monotonic is not None:
            elapsed_ign = int(time.monotonic() - self._ignition_start_monotonic)
            self.ignition_remaining = max(0, self.ignition_duration_seconds - elapsed_ign)
            
            if self.ignition_remaining <= 0:
                self._engage_hyperdrive()
            return self.get_status()

        if self.is_in_flight and self._start_monotonic is not None:
            real_elapsed = int(time.monotonic() - self._start_monotonic)
            self.elapsed_seconds = max(0, real_elapsed)

            if self.elapsed_seconds >= self.target_seconds:
                self.state = TimerState.OVERTIME
                self.overtime_seconds = self.elapsed_seconds - self.target_seconds
            else:
                self.state = TimerState.FOCUSING
                self.overtime_seconds = 0

        return self.get_status()

    def get_status(self) -> dict:
        """Returns the current presentation metrics."""
        target_name = self.mission_title if self.mission_title else self.ship_name

        if self.state == TimerState.IDLE:
            minutes = self.target_seconds // 60
            seconds = self.target_seconds % 60
            return {
                "state": self.state.value,
                "display_time": f"{minutes:02d}:{seconds:02d}",
                "progress_ratio": 0.0,
                "is_ignition": False,
                "ignition_remaining": 0,
                "is_overtime": False,
                "elapsed_seconds": 0,
                "overtime_seconds": 0,
                "status_title": "PRÊT AU DÉCOLLAGE",
                "status_subtitle": f"Session de {self.target_seconds // 60} min",
            }

        if self.state == TimerState.IGNITION:
            ign_ratio = max(0.0, min(1.0, 1.0 - (self.ignition_remaining / max(1, self.ignition_duration_seconds))))
            return {
                "state": self.state.value,
                "display_time": f"00:{self.ignition_remaining:02d}",
                "progress_ratio": ign_ratio,
                "is_ignition": True,
                "ignition_remaining": self.ignition_remaining,
                "is_overtime": False,
                "elapsed_seconds": 0,
                "overtime_seconds": 0,
                "status_title": "🔥 IGNITION EN COURS",
                "status_subtitle": f"Allumage de {self.ship_name} dans {self.ignition_remaining}s",
            }

        if self.state == TimerState.FOCUSING:
            remaining = max(0, self.target_seconds - self.elapsed_seconds)
            rem_min = remaining // 60
            rem_sec = remaining % 60
            ratio = min(1.0, self.elapsed_seconds / max(1, self.target_seconds))
            return {
                "state": self.state.value,
                "display_time": f"{rem_min:02d}:{rem_sec:02d}",
                "progress_ratio": ratio,
                "is_ignition": False,
                "ignition_remaining": 0,
                "is_overtime": False,
                "elapsed_seconds": self.elapsed_seconds,
                "overtime_seconds": 0,
                "status_title": "🚀 HYPERDRIVE ACTIF",
                "status_subtitle": f"Mission : {target_name} ({self.ship_icon} {self.ship_name})",
            }

        # Overtime State
        ot_min = self.overtime_seconds // 60
        ot_sec = self.overtime_seconds % 60
        return {
            "state": self.state.value,
            "display_time": f"+{ot_min:02d}:{ot_sec:02d}",
            "progress_ratio": 1.0,
            "is_ignition": False,
            "ignition_remaining": 0,
            "is_overtime": True,
            "elapsed_seconds": self.elapsed_seconds,
            "overtime_seconds": self.overtime_seconds,
            "status_title": "⚡ OVERDRIVE ACTIF",
            "status_subtitle": f"Vol validé • Propulsion continue sur {target_name}",
        }

    def complete(self) -> FocusSession:
        """Ends the flight session with success."""
        self.tick()
        self._ended_at_iso = datetime.now().isoformat()
        self.state = TimerState.COMPLETED

        session = FocusSession(
            ship_id=self.ship_id,
            ship_name=self.ship_name,
            ship_icon=self.ship_icon,
            mission_id=self.mission_id,
            mission_title=self.mission_title,
            started_at=self._started_at_iso,
            ended_at=self._ended_at_iso,
            target_seconds=self.target_seconds,
            actual_seconds=self.elapsed_seconds,
            overtime_seconds=self.overtime_seconds,
            completed=True,
        )
        self.reset()
        return session

    def abort(self) -> FocusSession:
        """Aborts the flight session before completing target duration."""
        self.tick()
        self._ended_at_iso = datetime.now().isoformat()
        self.state = TimerState.ABORTED

        session = FocusSession(
            ship_id=self.ship_id,
            ship_name=self.ship_name,
            ship_icon="💥",
            mission_id=self.mission_id,
            mission_title=self.mission_title,
            started_at=self._started_at_iso,
            ended_at=self._ended_at_iso,
            target_seconds=self.target_seconds,
            actual_seconds=self.elapsed_seconds,
            overtime_seconds=0,
            completed=False,
        )
        self.reset()
        return session

    def reset(self):
        """Resets to idle state."""
        self.state = TimerState.IDLE
        self._ignition_start_monotonic = None
        self._start_monotonic = None
        self.ignition_remaining = 10
        self.elapsed_seconds = 0
        self.overtime_seconds = 0
        self.mission_id = ""
        self.mission_title = ""
