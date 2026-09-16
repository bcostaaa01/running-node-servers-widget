"""Tray application entry point.

Three threads:
  - the scanner (background) rescans running Node processes on a timer and
    posts the result to a queue;
  - the tray icon (background) runs pystray's Win32 message loop and posts
    click events to the same queue;
  - the Tk dashboard (main thread) owns the only GUI toolkit that actually
    needs to live on one thread, and drains the queue on a timer via
    ``after()`` -- the standard way to bridge worker threads into Tkinter
    without touching widgets off-thread.
"""

from __future__ import annotations

import ctypes
import queue
import threading
from ctypes import wintypes

import pystray
from pystray import MenuItem as Item

from . import dpi
from . import icon as icon_mod
from .dashboard import Dashboard
from .scanner import scan_node_servers
from .winicon import ClickIcon

REFRESH_SECONDS = 5
QUEUE_POLL_MS = 150
APP_NAME = "Node Server Tray"

# Windows' Shell_NotifyIcon tooltip buffer is capped at 128 characters --
# pystray raises ValueError past that.
MAX_TRAY_TITLE_CHARS = 120


def _cursor_pos() -> tuple[int, int]:
    pt = wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


class TrayApp:
    def __init__(self, refresh_seconds: int = REFRESH_SECONDS):
        self._refresh_seconds = refresh_seconds
        self._stop_event = threading.Event()
        self._refresh_event = threading.Event()
        self._queue: queue.Queue = queue.Queue()

        self.dashboard = Dashboard(on_refresh=self._request_refresh, on_quit=self._request_quit)

        # ClickIcon routes both left- and right-click to this single default
        # item, so the dashboard opens on any click -- Refresh/Quit live as
        # links inside the dashboard itself (see dashboard.py) rather than
        # in a native popup menu the user would have to click through.
        menu = pystray.Menu(Item("Open dashboard", self._on_open_clicked, default=True))
        self.icon = ClickIcon("node_server_tray", icon=icon_mod.render(), title=APP_NAME, menu=menu)

    # -- pystray callbacks (fire on the tray-icon thread) --------------

    def _on_open_clicked(self, _icon=None, _item=None) -> None:
        self._queue.put(("show", _cursor_pos()))

    def _request_refresh(self) -> None:
        self._refresh_event.set()

    def _request_quit(self) -> None:
        self._stop_event.set()
        self._refresh_event.set()
        self._queue.put(("quit", None))

    # -- scanner (background thread) --------------------------------------

    def _scan_loop(self) -> None:
        while not self._stop_event.is_set():
            self._queue.put(("servers", scan_node_servers()))
            self._refresh_event.wait(timeout=self._refresh_seconds)
            self._refresh_event.clear()

    def _icon_loop(self) -> None:
        self.icon.run()

    # -- Tk main loop: the only place dashboard/icon state gets mutated --

    def _pump_queue(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "show":
                    x, y = payload
                    self.dashboard.toggle(x, y)
                elif kind == "servers":
                    self._apply_servers(payload)
                elif kind == "quit":
                    self.icon.stop()
                    self.dashboard.quit()
                    return
        except queue.Empty:
            pass
        self.dashboard.root.after(QUEUE_POLL_MS, self._pump_queue)

    def _apply_servers(self, servers) -> None:
        self.dashboard.set_servers(servers)

        if not servers:
            title = f"{APP_NAME}: no servers running"
        else:
            ports = ", ".join(str(p) for s in servers for p in s.ports)
            title = f"{APP_NAME}: {ports}"
        if len(title) > MAX_TRAY_TITLE_CHARS:
            title = title[: MAX_TRAY_TITLE_CHARS - 1] + "…"
        self.icon.title = title

    def run(self) -> None:
        threading.Thread(target=self._scan_loop, name="scanner", daemon=True).start()
        threading.Thread(target=self._icon_loop, name="tray-icon", daemon=True).start()
        self.dashboard.root.after(QUEUE_POLL_MS, self._pump_queue)
        self.dashboard.root.mainloop()


def main() -> None:
    dpi.enable()  # must run before any window (pystray's or Tk's) is created
    TrayApp().run()


if __name__ == "__main__":
    main()
