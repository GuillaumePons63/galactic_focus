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
Galactic Focus - Launcher
Run directly with: python main.py
Or as compiled executable.
"""
import sys
import os
from pathlib import Path

# Set up paths for bundled frozen executable
if getattr(sys, "frozen", False):
    base_dir = getattr(sys, "_MEIPASS", str(Path(sys.executable).parent))
    flet_client_dir = Path(base_dir) / "flet_client"
    if flet_client_dir.exists():
        os.environ["FLET_VIEW_PATH"] = str(flet_client_dir)

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import flet as ft
from galactic_focus.main import main

if __name__ == "__main__":
    ft.app(target=main)
