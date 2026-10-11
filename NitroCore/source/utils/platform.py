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


#: Canonical locations of the Windows system helpers NitroCore shells out to.
#: S-2 (audit 2026-10-11): an elevated process must not resolve helper
#: executables via PATH, which is user-influenced — resolve to %SystemRoot%
#: instead, so a PATH-hijacked powercfg/cleanmgr/dism/powershell can never be
#: picked up with admin rights.
_SYSTEM_TOOL_LOCATIONS = {
    "powercfg": ("System32", "powercfg.exe"),
    "cleanmgr": ("System32", "cleanmgr.exe"),
    "dism": ("System32", "dism.exe"),
    "powershell": ("System32", "WindowsPowerShell", "v1.0", "powershell.exe"),
}


def system_tool_path(name: str) -> str:
    """Return the absolute path of a Windows system helper executable.

    On Windows this resolves e.g. ``"powercfg"`` to
    ``%SystemRoot%\\System32\\powercfg.exe``. Falls back to the bare name when
    the canonical file is missing (non-stock layouts) and off-Windows returns
    the name unchanged (all call sites are Windows-gated anyway).
    """
    key = os.path.splitext(name.lower())[0]
    location = _SYSTEM_TOOL_LOCATIONS.get(key)
    if not IS_WINDOWS or location is None:
        return name
    system_root = (
        os.environ.get("SystemRoot") or os.environ.get("windir") or r"C:\Windows"
    )
    candidate = os.path.join(system_root, *location)
    return candidate if os.path.isfile(candidate) else name
