# Project: Galactic Focus Visual & Ergonomic Redesign

## Architecture
- **Framework**: Flet Desktop (Python / Flutter engine v0.86.5)
- **Application Core (`galactic_focus/core/`)**:
  - `models.py`: Domain dataclasses (`Ship`, `Mission`, `FocusSession`, `DailyFleetSummary`).
  - `storage.py`: `StorageManager` (atomic JSON persistence to `data.json` with `threading.Lock()` mutex, fleet/mission CRUD, auto-resolution, UTF-8-BOM CSV export).
  - `timer_engine.py`: `TimerEngine` (monotonic timekeeper, state machine with IDLE, IGNITION, FOCUSING, OVERTIME, COMPLETED, ABORTED).
- **Presentation Layer (`galactic_focus/ui/`)**:
  - `theme.py`: Cyberpunk Synthwave color tokens, typography, `interactive_card`, `sci_fi_button`, `floating_capsule_pill_switch`, `crt_monitor_display_card`.
  - `cockpit_view.py`: Flight command bridge, ship selector, duration capsule switcher, 210px HUD with dynamic propulsion pulsation, dual lateral CRT monitors, daily flight registry.
  - `missions_view.py`: Strategic directives deck, KPI metric row, floating filter capsule switcher, global & specific mission cards, neon progress gauges, dynamic deadline urgency badges, direct launch action.
  - `hangar_view.py`: Spacedock fleet management, armed ship cards, flagship protection, scrap archives (au rebut) with 1-click restore, maintenance log with CSV export.
- **Application Shell & Navigation**:
  - `galactic_focus/main.py`: Dark theme window setup (1260x860, min 1080x680), sidebar navigation rail, dynamic header with breadcrumbs and live status beacon, active viewport router.
  - `main.py`: Root launcher handling frozen PyInstaller `flet_client` routing.

---

## Feature Inventory
Every feature identified during survey is assigned to a milestone:

| # | Feature | Description | Milestone | Status |
|---|---------|-------------|-----------|--------|
| 1 | Cyberpunk Synthwave Color Palette | Deep cosmic base (`#030712`, `#060B1A`, `#0A1329`), Laser Cyan (`#00F0FF`), Kyber Violet (`#A855F7`), Neon Pink/Magenta (`#F43F5E`/`#EC4899`), Solar Amber (`#F59E0B`), Hyper Green (`#10B981`) | M1 | DONE |
| 2 | Futuristic Clean Typography | Modern sans-serif hierarchy (Segoe UI/Eurostile style), high-contrast numerical metrics, removal of raw console brackets and monospace clutter | M1 | DONE |
| 3 | Interactive Cards Micro-Interactions | Smooth `on_hover` border glow with dual-tone neon halo BoxShadows and slight physical elevation | M1 | DONE |
| 4 | Beveled Sci-Fi Buttons | Interactive chamfered cyber buttons with `scale: 1.02`, neon aura, and tactile click return | M1 | DONE |
| 5 | Floating Capsule Switcher | Reusable animated pill capsule switcher with dark glass background and glowing active indicator | M1 | DONE |
| 6 | CRT Telemetry Monitor Displays | Warp Oscilloscope (amber/purple) and Orbital Radar (cyan/green) CRT frame cards with scanlines and crisp telemetry alignment | M1, M2 | DONE |
| 7 | Animated Countdown & Propulsion Pulse | Central HUD ring and timer pulsation during 10s Ignition (amber alert), Hyperdrive (cyan/purple cyber breath), and Overdrive (green hyper pulse) | M2 | DONE |
| 8 | Cockpit Bridge & Ergonomics | Active ship selector, duration capsule switcher (15-60m), 210px central HUD, dual lateral monitors, daily squadron flight registry | M2 | DONE |
| 9 | Daily Squadron Flight Registry | Daily flight summary container displaying completed and aborted sorties with glowing status chips (`VOL VALIDÉ` / `AVARIE`) | M2 | DONE |
| 10 | Missions Center & Directives | Global directives (fleet-wide) and Specific ship missions, neon segmented progress gauges, floating capsule filter switcher | M3 | DONE |
| 11 | Dynamic Deadline Urgency Badges | Color-coded dynamic deadline badges (Overdue `#EF4444`, Today `#F59E0B`, Tomorrow `#FBBF24`, Future `#00F0FF`, Completed `#10B981`) | M3 | DONE |
| 12 | Direct Takeoff Action from Mission | Fast flight launch button (`DÉCOLLER AVEC [VAISSEAU]`) navigating to Cockpit with preloaded ship | M3 | DONE |
| 13 | Hangar Spacedock Fleet Cards | Armed spacecraft specification cards, sortie stats, fleet flight time progress bars, flagship protection | M4 | DONE |
| 14 | Scrap Archives (Au Rebut) | Dedicated archive for retired project ships with 1-click rearm/restore to active fleet | M4 | DONE |
| 15 | Maintenance Logbook & CSV Export | Filterable flight session logbook with 1-click Excel-compatible UTF-8-BOM CSV export | M4 | DONE |
| 16 | Window Geometry & Zero Layout Glitches | Explicit window dimensioning (1260x860, min 1080x680) and auto-scroll containment preventing clipping | M1, M2 | DONE |
| 17 | 14/14 Unit & Integration Tests Verification | Execution of `python -m unittest discover -s galactic_focus/tests` with 100% pass rate (51/51 tests total) | M5 | DONE |
| 18 | Standalone PyInstaller Binary Build | Compilation of `main.py` -> `GalacticFocus.exe` (99.45 MB) with bundled icons, assets, and Flet desktop runtime | M5 | DONE |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Theme, UI Kit & Cyberpunk Palette | `galactic_focus/ui/theme.py`, `galactic_focus/main.py` (Color constants, typography, `interactive_card`, `sci_fi_button`, `floating_capsule_pill_switch`, `crt_monitor_display_card`, window geometry) | none | DONE |
| M2 | Cockpit Command Deck & Tactical HUD | `galactic_focus/ui/cockpit_view.py` (Duration capsule switcher, 210px HUD with dynamic propulsion pulsation, CRT monitors, daily squadron flight registry) | M1 | DONE |
| M3 | Missions & Directives Command Center | `galactic_focus/ui/missions_view.py` (KPI metrics, capsule filter switcher, global/specific mission cards, neon gauges, dynamic deadline urgency badges, direct launch) | M1 | DONE |
| M4 | Hangar, Spacedock & Scrap Archives | `galactic_focus/ui/hangar_view.py` (Fleet cards, flagship protection, scrap archives with 1-click restore, maintenance logbook, CSV export) | M1 | DONE |
| M5 | Test Suite Verification & Executable Build | `galactic_focus/tests/`, `build_exe.bat`, `GalacticFocus.exe` (14/14 core tests, 51/51 total tests pass, standalone binary 99.45 MB built and verified) | M1, M2, M3, M4 | DONE |

---

## Interface Contracts

### 1. CockpitView Contract (`galactic_focus/ui/cockpit_view.py`)
- `CockpitView(page: ft.Page, storage: StorageManager, on_data_changed=None)`
- `.get_view() -> ft.Control`
- `.selected_duration_sec: int` (default `1200`)
- `.selected_ship: Optional[Ship]` (active Ship entity)
- `.ship_dropdown: ft.Dropdown` (maintains `.options` where each item has `.key == ship.id`)
- `.reload_fleet() -> None`
- `.load_ship(ship: Ship) -> None`
- `.reload_projects() -> None` (backward compatibility alias)

### 2. MissionsView Contract (`galactic_focus/ui/missions_view.py`)
- `MissionsView(page: ft.Page, storage: StorageManager, on_data_changed=None, on_launch_ship=None)`
- `.get_view() -> ft.Control`
- `.refresh() -> None`
- `._launch_mission_flight(mission: Mission) -> None` (invokes `on_launch_ship(ship)`)

### 3. HangarView Contract (`galactic_focus/ui/hangar_view.py`)
- `HangarView(page: ft.Page, storage: StorageManager, on_data_changed=None)`
- `.get_view() -> ft.Control`
- `.refresh() -> None`
- `StatsView = HangarView` (backward compatibility alias)

### 4. StorageManager API Contract (`galactic_focus/core/storage.py`)
- `get_flagship() -> Ship`
- `get_ships(include_retired: bool = False) -> List[Ship]`
- `get_retired_ships() -> List[Ship]`
- `get_ship_by_id(ship_id: str) -> Optional[Ship]`
- `add_ship(name: str, color: str = "#00F0FF", icon: str = "🚀", is_flagship: bool = False) -> Ship`
- `update_ship(ship: Ship) -> None`
- `retire_ship(ship_id: str) -> Optional[Ship]` (Flagship protected)
- `restore_ship(ship_id: str) -> Optional[Ship]`
- `delete_ship(ship_id: str) -> None` (Flagship protected)
- `get_missions(filter_status: Optional[str] = None) -> List[Mission]`
- `get_active_mission_for_ship(ship_id: str) -> Optional[Mission]`
- `get_active_global_mission() -> Optional[Mission]`
- `get_mission_by_id(mission_id: str) -> Optional[Mission]`
- `add_mission(title: str, target_seconds: int = 1200, is_global: bool = False, ship_id: str = "", ...) -> Mission`
- `update_mission(mission: Mission) -> None`
- `toggle_mission_completed(mission_id: str) -> Optional[Mission]`
- `delete_mission(mission_id: str) -> None`
- `get_sessions(limit: int = 200) -> List[FocusSession]`
- `add_session(session: FocusSession) -> dict`
- `get_daily_summary(target_date: Optional[str] = None) -> DailyFleetSummary`
- `get_global_stats() -> dict`
- `export_maintenance_log_csv(export_path: Optional[str] = None) -> str`

### 5. TimerEngine Contract (`galactic_focus/core/timer_engine.py`)
- `TimerEngine(default_target_seconds: int = 1200, ignition_duration_seconds: int = 10)`
- `.state: TimerState` (`IDLE`, `IGNITION`, `FOCUSING`, `OVERTIME`, `COMPLETED`, `ABORTED`)
- `.is_running`, `.is_in_flight`, `.is_ignition`, `.is_overtime`
- `.start(...) -> None`, `.cancel_ignition() -> None`, `.skip_ignition() -> None`, `.tick() -> dict`, `.get_status() -> dict`, `.complete() -> FocusSession`, `.abort() -> FocusSession`
