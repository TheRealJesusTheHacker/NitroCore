"""
Application lifecycle guardrails, handling single-instance enforcement 
and emergency OS handle cleanups.
"""

import sys
import atexit
import ctypes
from typing import Optional

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import win32event
    import win32api
    import winerror

class LifecycleManager:
    """Manages system-level single instance constraints and process teardowns."""

    _mutex: Optional[object] = None

    @classmethod
    def enforce_single_instance(cls) -> None:
        if not IS_WINDOWS:
            return

        cls._mutex = win32event.CreateMutex(None, False, "Global\\NitroCore_SingleInstance_Mutex")

        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            cls._mutex = None
            if IS_WINDOWS:
                ctypes.windll.user32.MessageBoxW(
                    0,
                    "NitroCore is already running.",
                    "NitroCore",
                    0x40,
                )
            sys.exit(0)

    @staticmethod
    def register_emergency_cleanup(cleanup_callback: callable) -> None:
        """
        Registers an emergency handler to safely release low-level 
        system pointers if the app shuts down unexpectedly.
        """
        atexit.register(cleanup_callback)
