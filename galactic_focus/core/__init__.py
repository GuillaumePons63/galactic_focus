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
Core package for Galactic Focus.
"""
from .models import Ship, Project, FocusSession, Mission, DailyFleetSummary, SHIP_MODELS, SHIP_TYPES, get_ship_model_for_duration, get_ship_for_duration
from .storage import StorageManager
from .timer_engine import TimerEngine, TimerState

__all__ = [
    "Ship",
    "Project",
    "FocusSession",
    "Mission",
    "DailyFleetSummary",
    "SHIP_MODELS",
    "SHIP_TYPES",
    "get_ship_model_for_duration",
    "get_ship_for_duration",
    "StorageManager",
    "TimerEngine",
    "TimerState",
]
