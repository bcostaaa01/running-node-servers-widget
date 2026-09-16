"""Finds running Node.js processes and the ports they're listening on."""

from __future__ import annotations

from dataclasses import dataclass, field

import psutil

NODE_NAMES = {"node", "node.exe"}


@dataclass
class NodeServer:
    pid: int
    name: str
    ports: list[int] = field(default_factory=list)


def _listening_ports(proc: psutil.Process) -> list[int]:
    try:
        # Process.connections() was renamed to net_connections() in psutil 6;
        # fall back for older installs where the new name doesn't exist yet.
        conns = proc.net_connections(kind="inet")
    except AttributeError:
        conns = proc.connections(kind="inet")
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        return []
    return sorted({c.laddr.port for c in conns if c.status == psutil.CONN_LISTEN})


def _project_name(proc: psutil.Process) -> str:
    try:
        cwd = proc.cwd()
    except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
        cwd = None
    if cwd:
        return cwd.rstrip("\\/").replace("/", "\\").rsplit("\\", 1)[-1]
    try:
        cmdline = proc.cmdline()
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        cmdline = []
    return cmdline[-1] if cmdline else "node"


def scan_node_servers() -> list[NodeServer]:
    """One entry per running Node process with at least one open listening
    port, sorted by lowest port number."""

    servers = []
    for proc in psutil.process_iter(["pid", "name"]):
        if (proc.info.get("name") or "").lower() not in NODE_NAMES:
            continue
        ports = _listening_ports(proc)
        if not ports:
            continue
        servers.append(NodeServer(pid=proc.pid, name=_project_name(proc), ports=ports))

    servers.sort(key=lambda s: s.ports[0])
    return servers
