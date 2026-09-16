# Node Server Tray

A Windows system tray icon that lists every Node.js process currently
listening on a port, so you can tell at a glance which dev servers are
running when you've got several frontend projects open at once.

## What you get (v0.1)

- A tray icon that scans running `node.exe` processes for open listening
  ports every few seconds.
- Right-click it to see the live list: each entry shows the port(s), the
  project (the process's working-directory name), and its PID.
- Click an entry to open `http://localhost:<port>` in your default browser.
- Hover it for a one-line tooltip summary of the active ports.

Not in yet: auto-start on login, distinguishing multiple ports on the same
process by which one is actually the dev server vs. a debugger/HMR port,
non-Windows support.

## Requirements

- Windows 10/11.
- Python 3.10+.

## Install & run

```powershell
git clone https://github.com/<you>/node-server-tray.git
cd node-server-tray
python -m venv .venv
.venv\Scripts\pip install -e .
.venv\Scripts\node-server-tray.exe
```

Or run it straight from source without installing the package:

```powershell
python -m venv .venv
.venv\Scripts\pip install pystray Pillow psutil
.venv\Scripts\python -m node_server_tray
```

## How it works

It polls `psutil` for processes named `node`/`node.exe`, checks each one's
open TCP connections for anything in `LISTEN` state, and reads the
process's working directory to label it with a project name. No network
calls, nothing leaves your machine.
