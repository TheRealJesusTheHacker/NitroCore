"""Platform helpers for NitroCore.

Centralizes every Windows-only assumption so the app degrades gracefully
instead of crashing on other platforms.
"""

import os
import subprocess

IS_WINDOWS = os.name == "nt"


def hidden_subprocess_kwargs() -> dict:
    """Return subprocess kwargs that hide console windows on Windows.

    On non-Windows platforms this returns an empty dict, because
    ``subprocess.STARTUPINFO`` does not exist there.
    """
    if not IS_WINDOWS:
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return {
        "startupinfo": startupinfo,
        "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0),
    }
