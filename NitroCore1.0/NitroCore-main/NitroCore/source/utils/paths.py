"""Resource path resolution for dev and PyInstaller builds."""

import os
import sys


def resource_path(relative: str) -> str:
    """Resolve asset paths when running from source or a frozen executable."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, relative)
