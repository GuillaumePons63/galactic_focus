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
Data models for Galactic Focus (Ship with Flagship/Amiral support, Mission with Global/Specific support, FocusSession, DailyFleetSummary).
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import List, Optional, Dict
import uuid

# Available standard galactic ship models
SHIP_MODELS = [
    {"name": "Vaisseau Amiral", "icon": "🪐", "color": "#00F0FF"},
    {"name": "Intercepteur Stellaire", "icon": "🚀", "color": "#38BDF8"},
    {"name": "Croiseur Lourd", "icon": "🛸", "color": "#9D4EDD"},
    {"name": "Faucon Stellaire", "icon": "⚡", "color": "#00E676"},
    {"name": "Station Orbitale", "icon": "🛰️", "color": "#FFB300"},
    {"name": "Chasseur Furtif", "icon": "🛡️", "color": "#F43F5E"},
]

def get_ship_model_for_duration(duration_seconds: int) -> dict:
    """Returns ship details based on duration completed."""
    minutes = duration_seconds // 60
    if minutes >= 50:
        return SHIP_MODELS[4]
    elif minutes >= 35:
        return SHIP_MODELS[3]
    elif minutes >= 20:
        return SHIP_MODELS[2]
    return SHIP_MODELS[1]

SHIP_TYPES = SHIP_MODELS
get_ship_for_duration = get_ship_model_for_duration


@dataclass
class Ship:
    """Represents a spacecraft in the user's hangar (including Vaisseau Amiral for global focus)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Vaisseau Amiral"
    color: str = "#00F0FF"
    icon: str = "🪐"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    total_seconds: int = 0
    sessions_count: int = 0
    is_flagship: bool = False
    is_retired: bool = False
    retired_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Ship":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", "Vaisseau sans nom"),
            color=data.get("color", "#00F0FF"),
            icon=data.get("icon", "🚀"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            total_seconds=data.get("total_seconds", 0),
            sessions_count=data.get("sessions_count", 0),
            is_flagship=data.get("is_flagship", False),
            is_retired=data.get("is_retired", False),
            retired_at=data.get("retired_at", None),
        )

    @property
    def formatted_total_time(self) -> str:
        hours = self.total_seconds // 3600
        minutes = (self.total_seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes:02d}m"
        return f"{minutes} min"


# Backward compatibility alias
Project = Ship


@dataclass
class Mission:
    """Represents a mission (Specific to a ship or Global/Transversal across all ships)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    target_seconds: int = 1200  # Default 20 min
    progress_seconds: int = 0
    is_global: bool = False     # True if measures global work across any ship
    ship_id: str = ""           # Empty if is_global
    ship_name: str = "Mission Globale"
    ship_icon: str = "🌌"
    ship_color: str = "#00F0FF"
    deadline: str = ""          # YYYY-MM-DD
    status: str = "in_progress" # in_progress, completed, expired
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    # Backward compatibility properties
    @property
    def project_id(self) -> str:
        return self.ship_id

    @property
    def project_name(self) -> str:
        return self.ship_name

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Mission":
        s_id = data.get("ship_id") or data.get("project_id", "")
        raw_is_global = data.get("is_global")
        if raw_is_global is not None:
            is_glob = bool(raw_is_global)
        else:
            is_glob = (s_id == "" or data.get("ship_name") == "Mission Globale")
        s_name = data.get("ship_name") or data.get("project_name", "Mission Globale" if is_glob else "Vaisseau")
        s_icon = data.get("ship_icon") or data.get("project_icon", "🌌" if is_glob else "🚀")
        s_color = data.get("ship_color") or data.get("project_color", "#00F0FF")

        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            title=data.get("title", "Mission sans titre"),
            description=data.get("description", ""),
            target_seconds=data.get("target_seconds", 1200),
            progress_seconds=data.get("progress_seconds", 0),
            is_global=is_glob,
            ship_id=s_id,
            ship_name=s_name,
            ship_icon=s_icon,
            ship_color=s_color,
            deadline=data.get("deadline", ""),
            status=data.get("status", "in_progress"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            completed_at=data.get("completed_at", None),
        )

    @property
    def progress_ratio(self) -> float:
        if self.target_seconds <= 0:
            return 1.0
        return min(1.0, max(0.0, self.progress_seconds / self.target_seconds))

    @property
    def is_completed(self) -> bool:
        return self.status == "completed" or self.progress_seconds >= self.target_seconds

    @property
    def formatted_target_time(self) -> str:
        hours = self.target_seconds // 3600
        minutes = (self.target_seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes:02d}m"
        return f"{minutes} min"

    @property
    def formatted_progress_time(self) -> str:
        hours = self.progress_seconds // 3600
        minutes = (self.progress_seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes:02d}m"
        return f"{minutes} min"

    @property
    def deadline_info(self) -> Dict[str, any]:
        """Calculates deadline status, remaining days and color badge."""
        if not self.deadline:
            return {"label": "Sans date limite", "color": "#64748B", "is_urgent": False, "is_expired": False}

        try:
            deadline_date = datetime.strptime(self.deadline[:10], "%Y-%m-%d").date()
            today = date.today()
            diff_days = (deadline_date - today).days

            if self.is_completed:
                return {"label": f"Terminée (Échéance {self.deadline})", "color": "#00E676", "is_urgent": False, "is_expired": False}

            if diff_days < 0:
                return {"label": f"En retard ({abs(diff_days)}j)", "color": "#FF3366", "is_urgent": True, "is_expired": True}
            elif diff_days == 0:
                return {"label": "Échéance aujourd'hui !", "color": "#FF7A00", "is_urgent": True, "is_expired": False}
            elif diff_days == 1:
                return {"label": "Échéance demain", "color": "#FFB300", "is_urgent": True, "is_expired": False}
            else:
                return {"label": f"Dans {diff_days} jours", "color": "#00F0FF", "is_urgent": False, "is_expired": False}
        except Exception:
            return {"label": self.deadline, "color": "#64748B", "is_urgent": False, "is_expired": False}


@dataclass
class FocusSession:
    """Represents a completed or aborted flight session."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    ship_id: str = ""
    ship_name: str = "Vaisseau Amiral"
    ship_icon: str = "🪐"
    ship_is_flagship: bool = False
    mission_id: str = ""
    mission_title: str = ""
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ended_at: str = field(default_factory=lambda: datetime.now().isoformat())
    target_seconds: int = 1200
    actual_seconds: int = 0
    overtime_seconds: int = 0
    completed: bool = True

    # Backward compatibility properties
    @property
    def project_id(self) -> str:
        return self.ship_id

    @property
    def project_name(self) -> str:
        return self.ship_name

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FocusSession":
        s_id = data.get("ship_id") or data.get("project_id", "")
        s_name = data.get("ship_name") or data.get("project_name", "Vaisseau Amiral")
        s_icon = data.get("ship_icon", "🪐")

        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            ship_id=s_id,
            ship_name=s_name,
            ship_icon=s_icon,
            ship_is_flagship=data.get("ship_is_flagship", False),
            mission_id=data.get("mission_id", ""),
            mission_title=data.get("mission_title", ""),
            started_at=data.get("started_at", datetime.now().isoformat()),
            target_seconds=data.get("target_seconds") or data.get("target_duration_seconds", 1200),
            actual_seconds=data.get("actual_seconds") or data.get("actual_duration_seconds", 0),
            overtime_seconds=data.get("overtime_seconds", 0),
            completed=data.get("completed", True),
        )

    @property
    def formatted_duration(self) -> str:
        minutes = self.actual_seconds // 60
        seconds = self.actual_seconds % 60
        if minutes >= 60:
            h = minutes // 60
            m = minutes % 60
            return f"{h}h {m:02d}m"
        return f"{minutes:02d}:{seconds:02d} min"

    @property
    def formatted_overtime(self) -> str:
        if self.overtime_seconds <= 0:
            return "+00:00"
        m = self.overtime_seconds // 60
        s = self.overtime_seconds % 60
        return f"+{m:02d}:{s:02d}"

    @property
    def date_str(self) -> str:
        try:
            dt = datetime.fromisoformat(self.ended_at)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return "Aujourd'hui"

    @property
    def time_str(self) -> str:
        try:
            dt = datetime.fromisoformat(self.ended_at)
            return dt.strftime("%H:%M")
        except Exception:
            return "--:--"


@dataclass
class DailyFleetSummary:
    date_str: str
    total_seconds: int = 0
    completed_sessions: int = 0
    aborted_sessions: int = 0
    ships: List[str] = field(default_factory=list)

    @property
    def formatted_total_time(self) -> str:
        hours = self.total_seconds // 3600
        minutes = (self.total_seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes:02d}m"
        return f"{minutes} min"
