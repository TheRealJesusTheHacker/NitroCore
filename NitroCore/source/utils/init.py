"""
Utils Module - Core high-performance initialization configurations for NitroCore.
Optimized to expose stable, thread-safe system logic across execution threads.
"""

__version__ = "1.0.0"
__author__ = "JesusTheHacker"  # Updated to match your namespace

# 1. Import core loaders and managers cleanly
from .config import Config

# NOTE: If your logger.py file isn't created yet, make sure a placeholder or module exists
try:
    from .logger import Logger
except ImportError:
    # Safe mock fallback to prevent initialization failure if Logger is a work-in-progress
    class Logger:
        @staticmethod
        def log(msg): print(f"[LOG]: {msg}")

# 2. Explicitly define public API exports to enforce strict namespace safety
__all__ = [
    "Config",
    "Logger",
]
