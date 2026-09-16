"""Tray application entry point.

pystray regenerates the menu (by calling _build_menu) every time it's about
to be shown, so right-clicking the icon always reflects the latest scan. A
background thread rescans on a timer to keep the tooltip fresh even while
the menu is closed.
"""

from __future__ import annotations

import threading
import time
import webbrowser

import pystray
from pystray import MenuItem as Item

from . import icon as icon_mod
from .scanner import NodeServer, scan_node_servers

REFRESH_SECONDS = 5
APP_NAME = "Node Server Tray"


def _open_port(port: int):
    def handler(icon, item):
        webbrowser.open(f"http://localhost:{port}")

    return handler


def _refresh(icon, item):
    icon.update_menu()


def _quit(icon, item):
    icon.stop()


def _build_menu():
    servers = scan_node_servers()

    if not servers:
        yield Item("No Node servers running", None, enabled=False)
    else:
        for server in servers:
            ports = ", ".join(str(p) for p in server.ports)
            label = f"{ports} — {server.name} (pid {server.pid})"
            yield Item(label, _open_port(server.ports[0]))

    yield pystray.Menu.SEPARATOR
    yield Item("Refresh", _refresh)
    yield Item("Quit", _quit)


def _title_for(servers: list[NodeServer]) -> str:
    if not servers:
        return f"{APP_NAME}: no servers running"
    ports = ", ".join(str(p) for s in servers for p in s.ports)
    return f"{APP_NAME}: {ports}"


def _watch(icon: pystray.Icon) -> None:
    while icon.visible:
        icon.title = _title_for(scan_node_servers())
        time.sleep(REFRESH_SECONDS)


def main() -> None:
    icon = pystray.Icon(
        "node_server_tray",
        icon=icon_mod.render(),
        title=APP_NAME,
        menu=pystray.Menu(_build_menu),
    )

    def setup(icon: pystray.Icon) -> None:
        icon.visible = True
        threading.Thread(target=_watch, args=(icon,), daemon=True, name="scanner").start()

    icon.run(setup=setup)


if __name__ == "__main__":
    main()
