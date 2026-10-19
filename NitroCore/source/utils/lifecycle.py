"""
Application lifecycle guardrails, handling single-instance enforcement
and emergency OS handle cleanups.
"""

import ctypes
import sys
from typing import Optional

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import win32api
    import win32event
    import winerror


class LifecycleManager:
    """Manages system-level single instance constraints and process teardowns."""

    _mutex: Optional[object] = None

    @classmethod
    def enforce_single_instance(cls) -> None:
        if not IS_WINDOWS:
            return

        cls._mutex = win32event.CreateMutex(
            None, False, "Global\\NitroCore_SingleInstance_Mutex"
        )

        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            # CreateMutex returned a handle to the EXISTING mutex; we are
            # about to exit, but drop the handle explicitly instead of
            # leaking it (and keep cls._mutex from ever holding a handle
            # this branch does not own).
            try:
                cls._mutex.Close()
            except Exception:
                pass
            cls._mutex = None
            if IS_WINDOWS:
                ctypes.windll.user32.MessageBoxW(
                    0,
                    "NitroCore is already running.",
                    "NitroCore",
                    0x40,
                )
            sys.exit(1)
