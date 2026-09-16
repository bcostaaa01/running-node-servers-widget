"""Reads whether Windows is currently set to its light or dark app theme,
so the dashboard can follow the system instead of forcing one look."""

from __future__ import annotations

import winreg

_KEY = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
_VALUE = "AppsUseLightTheme"


def is_light() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _KEY) as key:
            value, _ = winreg.QueryValueEx(key, _VALUE)
        return bool(value)
    except OSError:
        return False
