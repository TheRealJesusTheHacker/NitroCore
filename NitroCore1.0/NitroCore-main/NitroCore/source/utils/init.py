"""
Utils Module - Core high-performance initialization configurations for NitroCore.
Optimized to expose stable, thread-safe system logic across execution threads.
"""

__version__ = "1.0.0"
__author__ = "JesusTheHacker"  # Updated to match your namespace

# 1. Import core loaders and managers cleanly
from .config import ConfigLoader

# NOTE: If your logger.py file isn't created yet, make sure a placeholder or module exists
try:
    from .logger import Logger
except ImportError:
    # Safe mock fallback to prevent initialization failure if Logger is a work-in-progress
    class Logger:
        @staticmethod
        def log(msg): print(f"[LOG]: {msg}")

# 2. Import the newly optimized, high-performance functions from helpers.py
from .helpers import (
    is_valid_ip, 
    is_valid_email,
    sanitize_input,
    hash_password_secure,  # Aligned with our secure SHA-256 updates
    retry_on_failure,
    fast_memoize,          # Aligned with our optimized C-layer caching logic
    validate_path,
    ensure_directory_exists
)

# 3. Explicitly define public API exports to enforce strict namespace safety
__all__ = [
    "ConfigLoader",
    "Logger",
    "is_valid_ip",
    "is_valid_email",
    "sanitize_input",
    "hash_password_secure",
    "retry_on_failure",
    "fast_memoize",
    "validate_path",
    "ensure_directory_exists"
]
