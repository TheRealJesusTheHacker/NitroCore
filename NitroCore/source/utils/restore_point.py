"""Windows System Restore point creation."""

import subprocess

from source.utils.config import Config
from source.utils.platform import IS_WINDOWS, hidden_subprocess_kwargs


def create_restore_point(description: str = "NitroCore Pre-Optimization") -> tuple[bool, str]:
    """
    Create a system restore point via PowerShell Checkpoint-Computer.
    Returns (success, message).
    """
    if Config.DRY_RUN:
        return False, "Preview mode: restore point creation skipped (nothing will change)."
    if not IS_WINDOWS:
        return False, "Restore points are only available on Windows."
    safe_desc = description.replace("'", "''")
    script = (
        f"Checkpoint-Computer -Description '{safe_desc}' "
        "-RestorePointType MODIFY_SETTINGS"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=180,
            **hidden_subprocess_kwargs(),
        )
        if result.returncode == 0:
            return True, "System restore point created successfully."
        stderr = (result.stderr or result.stdout or "").strip()
        if "disabled" in stderr.lower() or "1058" in stderr:
            return False, "System Restore is disabled on this PC. Enable it in Windows Settings first."
        return False, f"Could not create restore point: {stderr or 'Unknown error'}"
    except subprocess.TimeoutExpired:
        return False, "Restore point creation timed out."
    except Exception as exc:
        return False, f"Restore point error: {exc}"
