"""Windows System Restore point creation."""

import subprocess


def create_restore_point(description: str = "NitroCore Pre-Optimization") -> tuple[bool, str]:
    """
    Create a system restore point via PowerShell Checkpoint-Computer.
    Returns (success, message).
    """
    safe_desc = description.replace("'", "''")
    script = (
        f"Checkpoint-Computer -Description '{safe_desc}' "
        "-RestorePointType MODIFY_SETTINGS"
    )
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=180,
            startupinfo=startupinfo,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
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
