"""Light and dark color palettes for the dashboard card."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    bg_top: str
    bg_bottom: str
    border: str
    fg_primary: str
    fg_muted: str
    fg_faint: str
    hover_bg: str
    accent: str
    link_refresh: str
    link_refresh_hover: str
    link_quit: str
    link_quit_hover: str


DARK = Palette(
    bg_top="#263320",
    bg_bottom="#332c1c",
    border="#4a4436",
    fg_primary="#f2f2f2",
    fg_muted="#a9a48f",
    fg_faint="#847f6c",
    hover_bg="#3d4a34",
    accent="#7fd48f",
    link_refresh="#8ab4f8",
    link_refresh_hover="#b7d3fc",
    link_quit="#d77a7a",
    link_quit_hover="#eca3a3",
)

LIGHT = Palette(
    bg_top="#e7f6e0",
    bg_bottom="#f8efd8",
    border="#ddd0ab",
    fg_primary="#1c1d1f",
    fg_muted="#6b6a5e",
    fg_faint="#8f8d7e",
    hover_bg="#d9e8ce",
    accent="#1f9d4a",
    link_refresh="#2f6fe0",
    link_refresh_hover="#4d84ea",
    link_quit="#c23b3b",
    link_quit_hover="#d95c5c",
)


def for_theme(light: bool) -> Palette:
    return LIGHT if light else DARK
