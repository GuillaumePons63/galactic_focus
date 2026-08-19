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

import os
import sys
import json
import csv
import uuid
import threading
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path

from .models import Ship, FocusSession, Mission, DailyFleetSummary, SHIP_MODELS

FLAGSHIP_DEFAULT = {
    "id": "flagship_main",
    "name": "Vaisseau Amiral",
    "color": "#00F0FF",
    "icon": "🪐",
    "is_flagship": True,
    "is_retired": False,
}

DEFAULT_SHIPS = [
    FLAGSHIP_DEFAULT,
    {"id": "ship_interceptor", "name": "Intercepteur Stellaire", "color": "#38BDF8", "icon": "🚀", "is_flagship": False},
    {"id": "ship_cruiser", "name": "Croiseur Lourd", "color": "#9D4EDD", "icon": "🛸", "is_flagship": False},
    {"id": "ship_falcon", "name": "Faucon Stellaire", "color": "#00E676", "icon": "⚡", "is_flagship": False},
]


class StorageManager:
    def __init__(self, storage_path: Optional[str] = None):
        self._lock = threading.Lock()
        if storage_path:
            self.file_path = Path(storage_path)
        else:
            if getattr(sys, "frozen", False):
                base_dir = Path(sys.executable).parent
            else:
                base_dir = Path(__file__).resolve().parent.parent
            self.file_path = base_dir / "data.json"
        
        self._ensure_storage()

    def _ensure_storage(self):
        """Creates or updates data.json ensuring the Vaisseau Amiral exists."""
        if not self.file_path.exists():
            default_data = {
                "ships": [],
                "missions": [],
                "sessions": [],
                "version": 3
            }
            for s in DEFAULT_SHIPS:
                ship = Ship(
                    id=s.get("id", str(uuid.uuid4())[:8]),
                    name=s["name"],
                    color=s["color"],
                    icon=s["icon"],
                    is_flagship=s.get("is_flagship", False),
                )
                default_data["ships"].append(ship.to_dict())
            
            self._save_raw(default_data)
        else:
            # Check if flagship is present in existing data
            raw = self._load_raw()
            ships = raw.get("ships", [])
            has_flagship = any(s.get("is_flagship", False) or s.get("name") == "Vaisseau Amiral" for s in ships)
            if not has_flagship:
                flagship = Ship(
                    id="flagship_main",
                    name="Vaisseau Amiral",
                    color="#00F0FF",
                    icon="🪐",
                    is_flagship=True,
                )
                raw["ships"] = [flagship.to_dict()] + ships
                self._save_raw(raw)

    def _load_raw(self) -> dict:
        with self._lock:
            try:
                with open(self.file_path, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                    if "ships" not in data:
                        data["ships"] = data.get("projects", [])
                    if "missions" not in data:
                        data["missions"] = []
                    if "sessions" not in data:
                        data["sessions"] = []
                    return data
            except Exception:
                return {"ships": [], "missions": [], "sessions": [], "version": 3}

    def _save_raw(self, data: dict):
        with self._lock:
            temp_path = self.file_path.with_name(f"{self.file_path.stem}_{uuid.uuid4().hex[:6]}.tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            temp_path.replace(self.file_path)

    # ------------------ Ships Fleet (Vaisseaux) CRUD ------------------

    def get_ships(self, include_retired: bool = False) -> List[Ship]:
        raw = self._load_raw()
        all_ships = [Ship.from_dict(s) for s in raw.get("ships", [])]
        
        # Ensure flagship is first
        all_ships.sort(key=lambda s: (0 if s.is_flagship else 1, s.created_at))

        if include_retired:
            return all_ships
        return [s for s in all_ships if not s.is_retired]

    def get_retired_ships(self) -> List[Ship]:
        raw = self._load_raw()
        all_ships = [Ship.from_dict(s) for s in raw.get("ships", [])]
        return [s for s in all_ships if s.is_retired and not s.is_flagship]

    def get_flagship(self) -> Ship:
        ships = self.get_ships(include_retired=True)
        for s in ships:
            if s.is_flagship:
                return s
        # Fallback create flagship
        flagship = self.add_ship("Vaisseau Amiral", "#00F0FF", "🪐", is_flagship=True)
        return flagship

    # Backward compatibility alias
    def get_projects(self) -> List[Ship]:
        return self.get_ships(include_retired=False)

    def get_ship_by_id(self, ship_id: str) -> Optional[Ship]:
        all_ships = self.get_ships(include_retired=True)
        for s in all_ships:
            if s.id == ship_id:
                return s
        return None

    def get_project_by_id(self, project_id: str) -> Optional[Ship]:
        return self.get_ship_by_id(project_id)

    def add_ship(self, name: str, color: str = "#00F0FF", icon: str = "🚀", is_flagship: bool = False) -> Ship:
        raw = self._load_raw()
        new_ship = Ship(name=name.strip(), color=color, icon=icon, is_flagship=is_flagship)
        raw.setdefault("ships", []).append(new_ship.to_dict())
        self._save_raw(raw)
        return new_ship

    def add_project(self, name: str, color: str = "#00F0FF", icon: str = "🚀") -> Ship:
        return self.add_ship(name, color, icon)

    def update_ship(self, updated: Ship):
        raw = self._load_raw()
        ships = []
        for s in raw.get("ships", []):
            if s.get("id") == updated.id:
                ships.append(updated.to_dict())
            else:
                ships.append(s)
        raw["ships"] = ships
        self._save_raw(raw)

    def update_project(self, updated: Ship):
        self.update_ship(updated)

    def retire_ship(self, ship_id: str) -> Optional[Ship]:
        """Marks a ship as retired/archived (Flagship cannot be retired)."""
        ship = self.get_ship_by_id(ship_id)
        if ship and not ship.is_flagship:
            ship.is_retired = True
            ship.retired_at = datetime.now().isoformat()
            self.update_ship(ship)
        return ship

    def restore_ship(self, ship_id: str) -> Optional[Ship]:
        """Restores a retired ship back to active fleet service."""
        ship = self.get_ship_by_id(ship_id)
        if ship:
            ship.is_retired = False
            ship.retired_at = None
            self.update_ship(ship)
        return ship

    def delete_ship(self, ship_id: str):
        """Deletes a ship (Flagship is protected)."""
        ship = self.get_ship_by_id(ship_id)
        if ship and ship.is_flagship:
            return  # Protect flagship
        raw = self._load_raw()
        raw["ships"] = [s for s in raw.get("ships", []) if s.get("id") != ship_id]
        self._save_raw(raw)

    def delete_project(self, project_id: str):
        self.delete_ship(project_id)

    # ------------------ Missions CRUD ------------------

    def get_missions(self, filter_status: Optional[str] = None) -> List[Mission]:
        raw = self._load_raw()
        missions = [Mission.from_dict(m) for m in raw.get("missions", [])]
        
        # Sort: in_progress first (global first, then by deadline), then completed
        missions.sort(key=lambda m: (1 if m.is_completed else 0, 0 if m.is_global else 1, m.deadline or "9999-99-99", m.created_at))

        if filter_status == "in_progress":
            return [m for m in missions if not m.is_completed]
        elif filter_status == "completed":
            return [m for m in missions if m.is_completed]
        return missions

    def get_active_mission_for_ship(self, ship_id: str) -> Optional[Mission]:
        """Returns the first active mission assigned to a specific ship."""
        missions = self.get_missions(filter_status="in_progress")
        for m in missions:
            if not m.is_global and m.ship_id == ship_id:
                return m
        return None

    def get_active_global_mission(self) -> Optional[Mission]:
        """Returns the first active global mission."""
        missions = self.get_missions(filter_status="in_progress")
        for m in missions:
            if m.is_global or m.ship_id == "":
                return m
        return None

    def get_mission_by_id(self, mission_id: str) -> Optional[Mission]:
        missions = self.get_missions()
        for m in missions:
            if m.id == mission_id:
                return m
        return None

    def add_mission(
        self,
        title: str,
        target_seconds: int = 1200,
        is_global: bool = False,
        ship_id: str = "",
        ship_name: str = "",
        ship_icon: str = "",
        ship_color: str = "#00F0FF",
        deadline: str = "",
        description: str = "",
        # Backward compatibility
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
        project_icon: Optional[str] = None,
        project_color: Optional[str] = None,
    ) -> Mission:
        s_id = ship_id or project_id or ""
        is_glob = is_global or (s_id == "")

        if is_glob:
            s_name = "Mission Globale"
            s_icon = "🌌"
            s_color = "#00F0FF"
            s_id = ""
        else:
            s_name = ship_name or project_name or "Vaisseau"
            s_icon = ship_icon or project_icon or "🚀"
            s_color = ship_color or project_color or "#00F0FF"

        raw = self._load_raw()
        new_mission = Mission(
            title=title.strip(),
            target_seconds=target_seconds,
            is_global=is_glob,
            ship_id=s_id,
            ship_name=s_name,
            ship_icon=s_icon,
            ship_color=s_color,
            deadline=deadline,
            description=description.strip(),
        )
        raw.setdefault("missions", []).append(new_mission.to_dict())
        self._save_raw(raw)
        return new_mission

    def update_mission(self, updated: Mission):
        raw = self._load_raw()
        missions = []
        for m in raw.get("missions", []):
            if m.get("id") == updated.id:
                missions.append(updated.to_dict())
            else:
                missions.append(m)
        raw["missions"] = missions
        self._save_raw(raw)

    def toggle_mission_completed(self, mission_id: str) -> Optional[Mission]:
        mission = self.get_mission_by_id(mission_id)
        if not mission:
            return None

        if mission.is_completed:
            mission.status = "in_progress"
            mission.completed_at = None
        else:
            mission.status = "completed"
            mission.completed_at = datetime.now().isoformat()
            if mission.progress_seconds < mission.target_seconds:
                mission.progress_seconds = mission.target_seconds

        self.update_mission(mission)
        return mission

    def delete_mission(self, mission_id: str):
        raw = self._load_raw()
        raw["missions"] = [m for m in raw.get("missions", []) if m.get("id") != mission_id]
        self._save_raw(raw)

    # ------------------ Sessions & Automatic Mission Resolution ------------------

    def get_sessions(self, limit: int = 200) -> List[FocusSession]:
        raw = self._load_raw()
        sessions = [FocusSession.from_dict(s) for s in raw.get("sessions", [])]
        sessions.sort(key=lambda s: s.ended_at, reverse=True)
        return sessions[:limit]

    def add_session(self, session: FocusSession) -> Dict[str, any]:
        """
        Saves a session and automatically updates ship flight hours,
        advances the ship's active mission, AND advances active global missions.
        """
        raw = self._load_raw()
        raw.setdefault("sessions", []).append(session.to_dict())
        
        advanced_missions = []
        completed_missions = []

        if session.completed:
            # 1. Update chosen ship flight stats
            s_id = session.ship_id or session.project_id
            if s_id:
                for s in raw.get("ships", []):
                    if s.get("id") == s_id:
                        s["total_seconds"] = s.get("total_seconds", 0) + session.actual_seconds
                        s["sessions_count"] = s.get("sessions_count", 0) + 1
                        break

            # 2. Automatically advance the Ship's active mission (if specific ship)
            if s_id:
                for m in raw.get("missions", []):
                    m_obj = Mission.from_dict(m)
                    if not m_obj.is_completed and not m_obj.is_global and m_obj.ship_id == s_id:
                        m["progress_seconds"] = m.get("progress_seconds", 0) + session.actual_seconds
                        advanced_missions.append(m["title"])
                        if m["progress_seconds"] >= m.get("target_seconds", 1200):
                            m["status"] = "completed"
                            m["completed_at"] = datetime.now().isoformat()
                            completed_missions.append(m["title"])
                        # Advance the first active mission of this ship
                        break

            # 3. Automatically advance ALL active Global Missions (regardless of ship flown)
            for m in raw.get("missions", []):
                m_obj = Mission.from_dict(m)
                if not m_obj.is_completed and (m_obj.is_global or m_obj.ship_id == ""):
                    m["progress_seconds"] = m.get("progress_seconds", 0) + session.actual_seconds
                    if m["title"] not in advanced_missions:
                        advanced_missions.append(m["title"])
                    if m["progress_seconds"] >= m.get("target_seconds", 1200):
                        m["status"] = "completed"
                        m["completed_at"] = datetime.now().isoformat()
                        if m["title"] not in completed_missions:
                            completed_missions.append(m["title"])

        self._save_raw(raw)
        return {
            "advanced_missions": advanced_missions,
            "completed_missions": completed_missions,
        }

    # ------------------ Aggregations & Daily Fleet ------------------

    def get_daily_summary(self, target_date: Optional[str] = None) -> DailyFleetSummary:
        if not target_date:
            target_date = datetime.now().strftime("%Y-%m-%d")

        sessions = self.get_sessions(limit=500)
        day_sessions = [s for s in sessions if s.date_str == target_date]

        total_sec = 0
        completed = 0
        aborted = 0
        ships = []

        for s in day_sessions:
            if s.completed:
                total_sec += s.actual_seconds
                completed += 1
                ships.append(s.ship_icon)
            else:
                aborted += 1
                ships.append("💥")

        return DailyFleetSummary(
            date_str=target_date,
            total_seconds=total_sec,
            completed_sessions=completed,
            aborted_sessions=aborted,
            ships=ships
        )

    def get_global_stats(self) -> dict:
        sessions = self.get_sessions(limit=1000)
        completed = [s for s in sessions if s.completed]
        total_seconds = sum(s.actual_seconds for s in completed)
        total_overtime = sum(s.overtime_seconds for s in completed)
        active_ships = self.get_ships(include_retired=False)
        retired_ships = self.get_retired_ships()
        missions = self.get_missions()
        active_missions = [m for m in missions if not m.is_completed]
        completed_missions = [m for m in missions if m.is_completed]

        return {
            "total_seconds": total_seconds,
            "total_sessions": len(completed),
            "total_overtime_seconds": total_overtime,
            "ships_count": len(active_ships),
            "retired_ships_count": len(retired_ships),
            "total_ships_count": len(active_ships) + len(retired_ships),
            "projects_count": len(active_ships),
            "total_missions": len(missions),
            "active_missions_count": len(active_missions),
            "completed_missions_count": len(completed_missions),
            "formatted_total_time": f"{total_seconds // 3600}h {(total_seconds % 3600) // 60:02d}m"
        }

    def export_maintenance_log_csv(self, export_path: Optional[str] = None) -> str:
        """Exports the ship maintenance log and flight records as CSV."""
        if not export_path:
            base_dir = Path(__file__).resolve().parent.parent
            export_path = str(base_dir / f"carnet_entretien_vaisseaux_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

        sessions = self.get_sessions(limit=1000)
        with open(export_path, "w", newline="", encoding="utf-8-sig") as csvfile:
            fieldnames = [
                "ID", "Date", "Heure", "Vaisseau", "Mission", "Temps de Vol (min)",
                "Temps (secondes)", "Overtime (sec)", "Statut de Vol"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for s in sessions:
                writer.writerow({
                    "ID": s.id,
                    "Date": s.date_str,
                    "Heure": s.time_str,
                    "Vaisseau": f"{s.ship_icon} {s.ship_name}",
                    "Mission": s.mission_title or "Vol Spécifique / Global",
                    "Temps de Vol (min)": f"{s.actual_seconds / 60:.1f}",
                    "Temps (secondes)": s.actual_seconds,
                    "Overtime (sec)": s.overtime_seconds,
                    "Statut de Vol": "Vol Réussi" if s.completed else "Vol Interrompu (Dégâts)",
                })

        return export_path

    # Backward compatibility alias
    def export_sessions_csv(self, export_path: Optional[str] = None) -> str:
        return self.export_maintenance_log_csv(export_path)
