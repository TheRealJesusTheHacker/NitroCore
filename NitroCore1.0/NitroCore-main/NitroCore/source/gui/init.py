"""
GUI Module - Thread-safe, modern flat-styled UI components for NitroCore.
Exposes optimized widget canvas systems and layout frameworks cleanly.
"""

__version__ = "1.0.0"
__author__ = "NitroCore Team"

# 1. Import your fully optimized, modern flat-styled components cleanly
from .window import Window
from .button import CustomButton
from .entry import CustomEntry
from .frame import CustomFrame

try:
    from .label import CustomLabel
except ImportError:
    import tkinter as tk
    class CustomLabel(tk.Label):
        pass

try:
    from .layout import LayoutManager
except ImportError:
    class LayoutManager:
        pass

try:
    from .tabs import TabbedInterface
except ImportError:
    TabbedInterface = None


__all__ = [
    "Window",
    "CustomButton",
    "CustomLabel",
    "CustomEntry",
    "CustomFrame",
    "LayoutManager",
    "TabbedInterface",
]
