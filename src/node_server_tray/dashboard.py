"""A small always-on-top flyout listing running Node dev servers.

Native Win32 tray context menus can't be styled (plain text, no colors, no
hover states), so the tray menu stays minimal and this custom Tk popup -- a
gradient rounded card that follows the Windows light/dark theme -- carries
the actual detail, the same way OneDrive and battery/volume pop a small
panel above their tray icon.
"""

from __future__ import annotations

import time
import tkinter as tk
import webbrowser
from typing import Callable

from PIL import ImageTk

from . import colors, dpi, theme
from .gradient import render_card, tone_between
from .scanner import NodeServer, kill_process

_FONT = "Segoe UI"

MAX_ROWS = 8
ROW_H = 28
HEADER_H = 30


def _rounded_rect(canvas: tk.Canvas, x1, y1, x2, y2, radius, **kwargs):
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class Dashboard:
    """Owns the Tk root. Must only be touched from the thread running
    ``root.mainloop()`` (see app.py's queue-pump pattern).

    All layout numbers below are logical (96-DPI) pixels; :meth:`_s` scales
    them to the real display DPI so the card renders crisp at 125%/150%
    scaling. ``dpi.enable()`` must have already run (app.py's ``main()``
    does this) before this is constructed. Height grows and shrinks with
    the server count, so every render recomputes it and, if the panel is
    currently open, repositions it against the last anchor point. The
    color palette is re-read from the Windows theme on every render too,
    so a light/dark switch is picked up on the next scan tick.
    """

    WIDTH = 360

    def __init__(self, *, on_refresh: Callable[[], None], on_quit: Callable[[], None]):
        self._on_refresh = on_refresh
        self._on_quit = on_quit
        self._servers: list[NodeServer] = []
        self._updated_at: float | None = None
        self._visible = False
        self._anchor: tuple[int, int] | None = None
        self._height = 1
        self._palette = colors.for_theme(theme.is_light())
        self._bg_photo: ImageTk.PhotoImage | None = None

        display_dpi = dpi.get_dpi()
        self.scale = display_dpi / dpi.BASELINE_DPI
        self.MARGIN = self._s(10)
        self.RADIUS = self._s(16)

        magic = "#ff00fe"  # chroma-key color -> made transparent for rounded corners
        self.root = tk.Tk()
        self.root.tk.call("tk", "scaling", display_dpi / 72.0)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=magic)
        self.root.attributes("-transparentcolor", magic)
        self.root.withdraw()
        self.root.bind("<Escape>", lambda _e: self.hide())
        self.root.bind("<FocusOut>", lambda _e: self.hide())

        self.canvas = tk.Canvas(
            self.root, width=self._s(self.WIDTH), height=self._s(120),
            bg=magic, highlightthickness=0, bd=0,
        )
        self.canvas.pack()
        self._render()

    def _s(self, px: float) -> int:
        """Scale a logical (96-DPI) pixel measurement to the real display."""
        return round(px * self.scale)

    def _add_pill_hover(self, c: tk.Canvas, text_item: int, *, normal_fg: str, hover_fg: str, idle_fill: str, on_click: Callable[[], None]) -> None:
        """Gives a header/footer link a pill-shaped hover highlight and a
        hand cursor. ``idle_fill`` matches the card's own gradient at that
        spot, so the pill is invisible until hovered rather than sitting on
        top of the gradient as a flat, mismatched patch -- and it also keeps
        the pill solidly filled (not empty), which is what makes its
        interior clickable at all in Tk."""

        pad = self._s(6)
        x1, y1, x2, y2 = c.bbox(text_item)
        radius = (y2 - y1 + 2 * pad) / 2
        bg = _rounded_rect(c, x1 - pad, y1 - pad, x2 + pad, y2 + pad, radius, fill=idle_fill, outline="")
        c.tag_lower(bg, text_item)

        def _enter(_e=None):
            c.itemconfig(bg, fill=self._palette.hover_bg)
            c.itemconfig(text_item, fill=hover_fg)
            c.config(cursor="hand2")

        def _leave(_e=None):
            c.itemconfig(bg, fill=idle_fill)
            c.itemconfig(text_item, fill=normal_fg)
            c.config(cursor="")

        for item in (bg, text_item):
            c.tag_bind(item, "<Enter>", _enter)
            c.tag_bind(item, "<Leave>", _leave)
            c.tag_bind(item, "<Button-1>", lambda _e: on_click())

    def _draw_row(self, c: tk.Canvas, x1: int, y: int, x2: int, server: NodeServer, idle_fill: str) -> int:
        pal = self._palette
        ports = ", ".join(str(p) for p in server.ports)
        row_h = self._s(ROW_H)

        bg = c.create_rectangle(x1 - self._s(6), y - self._s(4), x2 + self._s(6), y + row_h - self._s(6), fill=idle_fill, outline="")

        kill_item = c.create_text(x2, y, anchor="ne", text="✕", fill=pal.fg_faint, font=(_FONT, 9))
        kx1, _ky1, _kx2, _ky2 = c.bbox(kill_item)
        pid_item = c.create_text(kx1 - self._s(10), y, anchor="ne", text=f"pid {server.pid}", fill=pal.fg_faint, font=(_FONT, 8))

        port_item = c.create_text(x1, y, anchor="nw", text=ports, fill=pal.accent, font=(_FONT, 10, "bold"))
        _px1, _py1, px2, _py2 = c.bbox(port_item)
        name_item = c.create_text(px2 + self._s(8), y, anchor="nw", text=server.name, fill=pal.fg_primary, font=(_FONT, 10))

        c.tag_lower(bg)
        port = server.ports[0]
        pid = server.pid

        def _open(_e=None):
            webbrowser.open(f"http://localhost:{port}")

        def _enter(_e=None):
            c.itemconfig(bg, fill=pal.hover_bg)
            c.itemconfig(port_item, fill=pal.accent_hover)
            c.itemconfig(name_item, font=(_FONT, 10, "underline"))
            c.config(cursor="hand2")

        def _leave(_e=None):
            c.itemconfig(bg, fill=idle_fill)
            c.itemconfig(port_item, fill=pal.accent)
            c.itemconfig(name_item, font=(_FONT, 10))
            c.config(cursor="")

        for item in (bg, port_item, name_item, pid_item):
            c.tag_bind(item, "<Enter>", _enter)
            c.tag_bind(item, "<Leave>", _leave)
            c.tag_bind(item, "<Button-1>", _open)

        # The kill button sits on top of `bg` at that one spot, so it gets
        # its own Enter/Leave/click instead of the row's -- clicking it
        # stops the server rather than opening it in a browser.
        def _kill_enter(_e=None):
            c.itemconfig(kill_item, fill=pal.link_quit_hover)
            c.config(cursor="hand2")

        def _kill_leave(_e=None):
            c.itemconfig(kill_item, fill=pal.fg_faint)
            c.config(cursor="")

        def _kill(_e=None):
            kill_process(pid)
            self._on_refresh()

        c.tag_bind(kill_item, "<Enter>", _kill_enter)
        c.tag_bind(kill_item, "<Leave>", _kill_leave)
        c.tag_bind(kill_item, "<Button-1>", _kill)

        return y + row_h

    # -- state updates (call only from the Tk thread) --------------------

    def set_servers(self, servers: list[NodeServer]) -> None:
        self._servers = servers
        self._updated_at = time.time()
        self._render()

    # -- visibility ---------------------------------------------------------

    def toggle(self, x: int, y: int) -> None:
        self.hide() if self._visible else self.show(x, y)

    def show(self, x: int, y: int) -> None:
        self._anchor = (x, y)
        self._visible = True
        self._reposition()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _reposition(self) -> None:
        if self._anchor is None:
            return
        x, y = self._anchor
        width = self._s(self.WIDTH)
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        left = min(max(x - width + self._s(40), 0), max(sw - width, 0))
        top = min(max(y - self._height - self._s(12), 0), max(sh - self._height, 0))
        self.root.geometry(f"{width}x{self._height}+{left}+{top}")

    def hide(self) -> None:
        self.root.withdraw()
        self._visible = False

    def quit(self) -> None:
        self.root.quit()

    # -- drawing ------------------------------------------------------------

    def _render(self) -> None:
        c = self.canvas
        c.delete("all")

        self._palette = colors.for_theme(theme.is_light())
        pal = self._palette

        pad = self._s(16)
        header_h = self._s(HEADER_H)
        row_h = self._s(ROW_H)
        footer_gap = self._s(14)
        footer_line_h = self._s(18)

        shown = self._servers[:MAX_ROWS]
        overflow = len(self._servers) - len(shown)
        content_rows = max(len(shown), 1) + (1 if overflow > 0 else 0)

        # Height and the footer's position are derived from the same
        # top-down sum the drawing code below walks through, so the footer
        # can never land on top of the last row regardless of row count.
        width = self._s(self.WIDTH)
        content_bottom = self.MARGIN + pad + header_h + content_rows * row_h
        footer_y = content_bottom + footer_gap + footer_line_h
        height = footer_y + pad + self.MARGIN
        c.config(width=width, height=height)
        self._height = height
        if self._visible:
            self._reposition()

        card_w, card_h = width - 2 * self.MARGIN, height - 2 * self.MARGIN
        card = render_card(card_w, card_h, self.RADIUS, top=pal.bg_top, bottom=pal.bg_bottom, border=pal.border, border_width=self._s(1))
        self._bg_photo = ImageTk.PhotoImage(card)
        c.create_image(self.MARGIN, self.MARGIN, anchor="nw", image=self._bg_photo)

        def tone(y_px: float) -> str:
            frac = (y_px - self.MARGIN) / card_h if card_h else 0
            return tone_between(pal.bg_top, pal.bg_bottom, frac)

        x1, y1 = self.MARGIN, self.MARGIN
        x2 = width - self.MARGIN

        y = y1 + pad
        c.create_text(x1 + pad, y, anchor="nw", text="Node Servers", fill=pal.fg_primary, font=(_FONT, 11, "bold"))
        close = c.create_text(x2 - pad, y, anchor="ne", text="✕", fill=pal.fg_muted, font=(_FONT, 10))
        self._add_pill_hover(c, close, normal_fg=pal.fg_muted, hover_fg=pal.fg_primary, idle_fill=tone(y), on_click=self.hide)
        y += header_h

        if not shown:
            c.create_text(x1 + pad, y, anchor="nw", text="No Node servers running", fill=pal.fg_muted, font=(_FONT, 9))
        else:
            for server in shown:
                y = self._draw_row(c, x1 + pad, y, x2 - pad, server, idle_fill=tone(y))
            if overflow > 0:
                c.create_text(x1 + pad, y, anchor="nw", text=f"+{overflow} more", fill=pal.fg_faint, font=(_FONT, 8, "italic"))

        updated = f"Updated {time.strftime('%H:%M:%S', time.localtime(self._updated_at))}" if self._updated_at else ""
        c.create_text(x1 + pad, footer_y, anchor="sw", text=updated, fill=pal.fg_faint, font=(_FONT, 8))

        refresh = c.create_text(x2 - pad - self._s(38), footer_y, anchor="se", text="Refresh", fill=pal.link_refresh, font=(_FONT, 9, "underline"))
        self._add_pill_hover(c, refresh, normal_fg=pal.link_refresh, hover_fg=pal.link_refresh_hover, idle_fill=tone(footer_y), on_click=self._on_refresh)

        quit_ = c.create_text(x2 - pad, footer_y, anchor="se", text="Quit", fill=pal.link_quit, font=(_FONT, 9, "underline"))
        self._add_pill_hover(c, quit_, normal_fg=pal.link_quit, hover_fg=pal.link_quit_hover, idle_fill=tone(footer_y), on_click=self._on_quit)
