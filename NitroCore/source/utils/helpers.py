import re
import hashlib
import os
import functools
import time
from typing import Callable, Any, Union
from pathlib import Path

# 1. Pre-compile regular expressions globally at initialization.
# This compiles the engine once in memory, making evaluation incredibly fast.
IP_PATTERN = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
SAN_PATTERN = re.compile(r'[^\w\s\-\.]')


def is_valid_ip(ip: str) -> bool:
    """High-performance IP address structure validation via pre-compiled regex."""
    if not IP_PATTERN.match(ip):
        return False
    # Quick generator check avoids creating a full extra list object in memory
    return all(0 <= int(part) <= 255 for part in ip.split('.'))


def is_valid_email(email: str) -> bool:
    """Check if string is a valid email address layout."""
    return bool(EMAIL_PATTERN.match(email))


def sanitize_input(input_str: str) -> str:
    """Sanitize input strings by sweeping away unauthorized punctuation patterns."""
    return SAN_PATTERN.sub('', input_str).strip()


def hash_password_secure(password: str, salt: bytes = None) -> tuple[str, bytes]:
    """
    Hash a password with PBKDF2-HMAC-SHA256 (600,000 iterations, random 16-byte
    salt) per OWASP recommendations. Returns (hex_digest, salt).

    NOTE: currently unused by the application. Do not use the old single-round
    SHA-256 construction for passwords anywhere — it offers no brute-force
    resistance.
    """
    if salt is None:
        salt = os.urandom(16)  # Cryptographically secure random 16-byte salt
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000)
    return digest.hex(), salt


def retry_on_failure(max_retries: int = 3, delay: float = 1.0) -> Callable:
    """
    Decorator to safely re-attempt sensitive platform executions (like I/O sweeps).
    Features exponential backoff optimization to reduce system thrashing.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(current_delay)
                    current_delay *= 2  # Exponential backoff
        return wrapper
    return decorator


def fast_memoize(func: Callable) -> Callable:
    """
    High-performance memoization decorator.
    Leverages Python's built-in optimized caching engine, which is written natively in C.
    """
    # Using lru_cache creates a highly optimized hashing lookup grid at the C layer
    @functools.lru_cache(maxsize=128)
    @functools.wraps(func)
    def cached_unhashed(*args, **kwargs):
        return func(*args, **kwargs)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Fallback to direct call if arguments are unhashable mutable objects (like lists/dicts)
        try:
            if kwargs:
                # lru_cache doesn't natively handle kwargs, so we freeze them into a tuple
                frozen_kwargs = tuple(sorted(kwargs.items()))
                return cached_inner(*args, frozen_kwargs)
            return cached_unhashed(*args)
        except TypeError:
            return func(*args, **kwargs)

    @functools.lru_cache(maxsize=128)
    def cached_inner(*args):
        # Helper to unpack frozen keyword arguments safely
        *positional, frozen_kwargs = args
        kwargs = dict(frozen_kwargs)
        return func(*positional, **kwargs)

    return wrapper


def validate_path(path: Union[str, Path]) -> bool:
    """Validate file/directory target path boundaries securely."""
    try:
        p = Path(path)
        return p.exists()
    except Exception:
        return False


def is_reparse_point(entry) -> bool:
    """
    Return True if a scandir DirEntry is a reparse point (symlink or NTFS
    junction). Cleanup code must NEVER recurse into these: a junction inside
    a temp/Downloads tree can point outside it, and deleting through it would
    destroy files the user never asked us to touch.

    Fail-closed: if we cannot determine the type, treat it as a reparse
    point (skip it).
    """
    is_junction = getattr(entry, "is_junction", None)
    if callable(is_junction):
        # Python 3.12+: explicit junction detection.
        try:
            if is_junction():
                return True
        except OSError:
            return True
    try:
        attrs = getattr(entry.stat(follow_symlinks=False), "st_file_attributes", 0)
        FILE_ATTRIBUTE_REPARSE_POINT = 0x400
        if attrs & FILE_ATTRIBUTE_REPARSE_POINT:
            return True
    except OSError:
        return True
    # Plain symlinks: is_file()/is_dir() with follow_symlinks=False already
    # return False for these, but check explicitly for clarity.
    try:
        if entry.is_symlink():
            return True
    except OSError:
        return True
    return False


def ensure_directory_exists(path: Union[str, Path]) -> None:
    """Ensure parent directory tracks exist on disk, creating them if needed."""
    Path(path).mkdir(parents=True, exist_ok=True)
