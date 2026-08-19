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
Nova Space Mission Command Center & Cyberpunk Synthwave Theme & UI Kit for Galactic Focus.
Inspired by modern aerospace dashboards & sci-fi UI (Nova Command Center):
Cosmic Navy `#030712`, Deep Void `#060B1A`, Panel `#0A1329` / `#0A1633`, Laser Cyan `#00F0FF`, 
Kyber Violet `#A855F7`, Neon Magenta `#EC4899`, Neon Pink `#F43F5E`, Hyper Green `#10B981`, Solar Amber `#F59E0B`.
Clean futuristic typography, interactive hover animations, chamfered beveled buttons, and rich CRT monitor displays.
"""
import sys
from pathlib import Path
from typing import List, Tuple, Callable, Optional, Union
import flet as ft

# 🌌 Cosmic Command Center Color Palette
BG_DEEP_SPACE = "#030712"         # Deepest cosmic background
BG_DEEP_SPACE_ALT = "#060B1A"     # Secondary cosmic depth
BG_DEEP_SPACE_CARD = "#0A1329"    # Dark telemetry card canvas
BG_SIDEBAR = "#060E20"            # Sleek dark workspace rail
BG_PANEL = "#0A1633"              # Elevated command card
BG_PANEL_HOVER = "#0F224D"        # Interactive card hover
BG_CARD_INNER = "#060D1E"         # Inner display well
BORDER_CYBER = "#162A54"          # Hairline grid border
BORDER_CYBER_LIGHT = "#244380"    # Hover illuminated border
BORDER_GLOW_CYAN = "#00F0FF"      # Active electric cyan glow
BORDER_GLOW_AMBER = "#F59E0B"     # Active amber glow
BORDER_GLOW_MAGENTA = "#EC4899"   # Active neon magenta glow
BORDER_GLOW_PURPLE = "#A855F7"    # Active kyber violet glow

# ⚡ Electric Phosphor Accents
NEON_CYAN = "#00F0FF"             # Laser Cyan / Primary Brand Accent
NEON_ICE = "#38BDF8"              # Ice Blue / Secondary Telemetry
NEON_PURPLE = "#A855F7"           # Kyber Synthwave Violet / Archives
NEON_MAGENTA = "#EC4899"          # Neon Magenta / Glowing Accents
NEON_PINK = "#F43F5E"             # Neon Pink / Critical Pulse
NEON_GREEN = "#10B981"            # Hyper Green / Success & Overdrive
NEON_AMBER = "#F59E0B"            # Solar Amber / Ignition & Warnings
NEON_GOLD = "#FBBF24"             # Solar Gold / Target Badges
NEON_ORANGE = "#F97316"           # Core Combustion Orange
NEON_RED = "#EF4444"              # Crimson Alert / Abort

# 📝 Modern Sci-Fi Typography Fonts & Colors
FONT_HEADER = "Segoe UI, Trebuchet MS, Arial, sans-serif"
FONT_BODY = "Segoe UI, Arial, sans-serif"
FONT_NUM = "Segoe UI, Trebuchet MS, Arial, sans-serif"

TEXT_TITLE = "#F8FAFC"            # Crisp White Headers
TEXT_SUBTITLE = "#94A3B8"         # Ice Slate Subtitles
TEXT_BODY = "#CBD5E1"             # Clean Body Text
TEXT_MUTED = "#556987"            # Subtle Inactive Label
TEXT_CYAN = "#38BDF8"             # Cyan Telemetry Text
TEXT_AMBER = "#FBBF24"            # Amber Telemetry Text
TEXT_GREEN = "#34D399"            # Green Telemetry Text
TEXT_MAGENTA = "#F472B6"          # Magenta Telemetry Text
TEXT_PURPLE = "#C084FC"           # Purple Telemetry Text

# 🛸 Spacecraft Customization Palettes
SHIP_COLORS = [
    "#00F0FF", "#38BDF8", "#10B981", "#F59E0B",
    "#A855F7", "#F43F5E", "#EC4899", "#FBBF24",
]
SHIP_ICONS = ["🚀", "🛸", "⚡", "🪐", "🛰️", "🛡️", "🌌", "☄️"]

# Backward compatibility aliases
PROJECT_COLORS = SHIP_COLORS
PROJECT_ICONS = SHIP_ICONS


def get_asset_path(filename: str) -> str:
    """Resolves absolute path for packaged and development assets."""
    if getattr(sys, "frozen", False):
        base_dirs = [
            Path(getattr(sys, "_MEIPASS", sys.executable)).parent,
            Path(getattr(sys, "_MEIPASS", "")),
            Path(sys.executable).parent,
        ]
    else:
        base_dirs = [
            Path(__file__).resolve().parent.parent,
            Path(__file__).resolve().parent.parent.parent,
            Path(__file__).resolve().parent,
        ]

    for b in base_dirs:
        for sub in ["galactic_focus/assets", "assets", ""]:
            cand = (b / sub / filename) if sub else (b / filename)
            if cand.exists():
                return str(cand)

    return filename


def interactive_card(
    content: ft.Control,
    bgcolor: str = BG_PANEL,
    border_color: str = BORDER_CYBER,
    border_radius: Union[int, ft.BorderRadius] = 8,
    padding: int = 16,
    expand: bool = False,
    width: Optional[int] = None,
    height: Optional[int] = None,
    hover_border_color: str = NEON_CYAN,
    hover_bgcolor: str = BG_PANEL_HOVER,
    secondary_glow: Optional[str] = None,
    elevation_scale: float = 1.012,
    on_click=None,
) -> ft.Container:
    """Creates a high-end Cyberpunk Synthwave & Nova command card with layered neon halos and smooth hover elevation."""
    idle_shadow = [
        ft.BoxShadow(
            spread_radius=0,
            blur_radius=12,
            color="#00000088",
            offset=ft.Offset(0, 4),
        ),
    ]

    sec_glow = secondary_glow or (NEON_PURPLE if hover_border_color == NEON_CYAN else NEON_CYAN)
    hover_shadow = [
        ft.BoxShadow(
            spread_radius=1,
            blur_radius=14,
            color=f"{hover_border_color}55",
            offset=ft.Offset(0, 2),
        ),
        ft.BoxShadow(
            spread_radius=3,
            blur_radius=26,
            color=f"{sec_glow}33",
            offset=ft.Offset(0, 6),
        ),
    ]

    c = ft.Container(
        content=content,
        bgcolor=bgcolor,
        border=ft.Border.all(1, border_color),
        border_radius=border_radius,
        padding=padding,
        expand=expand,
        width=width,
        height=height,
        animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
        animate_scale=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
        on_click=on_click,
        ink=True if on_click else False,
        shadow=idle_shadow,
    )

    def on_hover(e):
        if e.data == "true":
            c.border = ft.Border.all(1, hover_border_color)
            c.bgcolor = hover_bgcolor
            c.scale = elevation_scale
            c.shadow = hover_shadow
        else:
            c.border = ft.Border.all(1, border_color)
            c.bgcolor = bgcolor
            c.scale = 1.0
            c.shadow = idle_shadow
        try:
            c.update()
        except Exception:
            pass

    c.on_hover = on_hover
    return c


def sci_fi_button(
    text: str,
    icon=None,
    color_neon: str = NEON_CYAN,
    text_color: str = "#030712",
    on_click=None,
    width: Optional[int] = None,
    height: int = 42,
    outlined: bool = False,
) -> ft.Container:
    """Creates an authentic beveled sci-fi button with scale 1.02 hover bloom and glowing neon shadow."""
    if outlined:
        bg = "transparent"
        fg = color_neon
        border = ft.Border.all(1, color_neon)
    else:
        bg = color_neon
        fg = text_color
        border = ft.Border.all(1, color_neon)

    btn_content_items = []
    if icon:
        btn_content_items.append(ft.Icon(icon, color=fg, size=15))
    btn_content_items.append(
        ft.Text(
            text.upper(),
            size=11,
            weight=ft.FontWeight.W_700,
            color=fg,
            font_family=FONT_HEADER,
            text_align=ft.TextAlign.CENTER,
        )
    )

    # Chamfered beveled geometry
    cyber_radius = ft.BorderRadius.only(
        top_left=8,
        bottom_right=8,
        top_right=3,
        bottom_left=3,
    )

    idle_shadow = [
        ft.BoxShadow(
            spread_radius=0,
            blur_radius=12,
            color=f"{color_neon}55" if not outlined else "#00000000",
            offset=ft.Offset(0, 2),
        ),
    ]

    hover_shadow = [
        ft.BoxShadow(
            spread_radius=1,
            blur_radius=20,
            color=f"{color_neon}AA",
            offset=ft.Offset(0, 3),
        ),
    ]

    btn = ft.Container(
        content=ft.Row(
            btn_content_items,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        ),
        width=width,
        height=height or 42,
        bgcolor=bg,
        border=border,
        border_radius=cyber_radius,
        padding=ft.Padding.symmetric(horizontal=14, vertical=2),
        alignment=ft.Alignment.CENTER,
        on_click=on_click,
        animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
        animate_scale=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
        ink=True,
        shadow=idle_shadow,
    )

    def on_hover(e):
        if e.data == "true":
            btn.scale = 1.02
            btn.shadow = hover_shadow
        else:
            btn.scale = 1.0
            btn.shadow = idle_shadow
        try:
            btn.update()
        except Exception:
            pass

    btn.on_hover = on_hover
    return btn


def floating_capsule_pill_switch(
    options: List[Tuple[str, str]],
    selected_key: str,
    on_change: Callable[[str], None],
    active_color: str = "#FFFFFF",
    active_text_color: str = "#030712",
) -> ft.Container:
    """Creates the signature Nova floating capsule pill switcher with dark cosmic glass and glowing active indicator."""
    pills = []
    for label, key in options:
        is_active = (key == selected_key)
        pill_shadow = [
            ft.BoxShadow(spread_radius=1, blur_radius=8, color=f"{NEON_CYAN}55", offset=ft.Offset(0, 1))
        ] if is_active and active_color != "#FFFFFF" else (
            [ft.BoxShadow(spread_radius=0, blur_radius=6, color="#FFFFFF44", offset=ft.Offset(0, 1))] if is_active else None
        )

        pill = ft.Container(
            content=ft.Text(
                label,
                size=11,
                weight=ft.FontWeight.W_700 if is_active else ft.FontWeight.NORMAL,
                color=active_text_color if is_active else TEXT_SUBTITLE,
                font_family=FONT_HEADER,
            ),
            padding=ft.Padding.symmetric(horizontal=14, vertical=6),
            bgcolor=active_color if is_active else "transparent",
            border_radius=20,
            shadow=pill_shadow,
            animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
            on_click=lambda e, k=key: on_change(k),
            ink=True,
        )
        pills.append(pill)

    return ft.Container(
        content=ft.Row(pills, spacing=2, alignment=ft.MainAxisAlignment.CENTER),
        padding=ft.Padding.all(4),
        bgcolor=f"{BG_CARD_INNER}E6",
        border=ft.Border.all(1, BORDER_CYBER),
        border_radius=24,
        shadow=[
            ft.BoxShadow(
                spread_radius=0,
                blur_radius=14,
                color="#00000099",
                offset=ft.Offset(0, 3),
            ),
        ],
    )


def crt_monitor_display_card(
    title: str,
    image_filename: str,
    telemetry_rows: List[Tuple[str, str, str]],
    color: str = NEON_CYAN,
    width: int = 240,
) -> ft.Container:
    """Creates a high-definition CRT monitor display card with retro scanline bezel & telemetry alignment."""
    img_path = get_asset_path(image_filename)

    telemetry_controls = []
    for label, val, val_col in telemetry_rows:
        telemetry_controls.append(
            ft.Row(
                [
                    ft.Text(label, size=10, color=TEXT_MUTED, font_family=FONT_BODY),
                    ft.Text(val, size=10, weight=ft.FontWeight.W_700, color=val_col, font_family=FONT_HEADER),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

    return interactive_card(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    width=6,
                                    height=6,
                                    bgcolor=color,
                                    border_radius=3,
                                    shadow=[ft.BoxShadow(spread_radius=1, blur_radius=6, color=color)],
                                ),
                                ft.Text(title, size=11, weight=ft.FontWeight.W_700, color=TEXT_TITLE, font_family=FONT_HEADER),
                            ],
                            spacing=6,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(
                            content=ft.Text("ONLINE", size=8, weight=ft.FontWeight.BOLD, color=color, font_family=FONT_HEADER),
                            padding=ft.Padding.symmetric(horizontal=5, vertical=1),
                            bgcolor=f"{color}18",
                            border=ft.Border.all(1, f"{color}44"),
                            border_radius=3,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=4),
                ft.Container(
                    content=ft.Image(
                        src=img_path,
                        width=width - 24,
                        height=140,
                        fit=ft.BoxFit.COVER,
                        border_radius=6,
                    ),
                    border=ft.Border.all(1, f"{color}44"),
                    border_radius=6,
                    bgcolor=BG_CARD_INNER,
                ),
                ft.Container(height=4),
                ft.Column(telemetry_controls, spacing=2),
            ],
            spacing=2,
            tight=True,
        ),
        width=width,
        padding=10,
        hover_border_color=color,
    )


# Backward compatibility aliases
cyber_glass_card = interactive_card
retro_console_card = interactive_card
glowing_action_button = sci_fi_button
retro_crt_monitor = interactive_card

