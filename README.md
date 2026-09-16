# Node Server Tray

A Windows system tray icon that lists every Node.js process currently
listening on a port, so you can tell at a glance which dev servers are
running when you've got several frontend projects open at once.

## What you get (v0.2)

- A tray icon that scans running `node.exe` processes for open listening
  ports every few seconds.
- Click it (either button) to open a small dashboard card next to the
  cursor, the same way OneDrive/battery/volume do -- no native right-click
  menu to click through first. It lists each server's port(s), project
  (the process's working-directory name), and PID.
- The card follows your Windows light/dark app theme and fills with a
  soft green-to-sand gradient.
- Click a row to open `http://localhost:<port>` in your default browser.
- Refresh and Quit live as links in the card's footer; Escape or clicking
  elsewhere closes it.
- Hover the tray icon for a one-line tooltip summary of the active ports.

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
