"""Live system telemetry for the NitroCore dashboard header."""

import os
import re
import subprocess
from typing import Dict

import psutil

_POWER_PLAN_NAMES = {
    "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c": "High Performance",
    "e9a42b02-d5df-448d-aa00-03f14749eb61": "Ultimate Performance",
    "381b4222-f694-41f0-9685-ff5bb260df2e": "Balanced",
    "a1841308-3541-4fab-bc81-715741643351": "Power Saver",
}


class SystemStats:
    """Collects CPU, memory, disk, and power plan metrics."""

    def __init__(self):
        psutil.cpu_percent(interval=None)

    def snapshot(self) -> Dict[str, str]:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()

        primary_disk = self._primary_disk_free_gb()
        power_plan = self._active_power_plan()

        return {
            "cpu": f"{cpu:.0f}%",
            "ram": f"{mem.percent:.0f}% ({mem.used // (1024 ** 3)} / {mem.total // (1024 ** 3)} GB)",
            "disk": primary_disk,
            "power": power_plan,
        }

    def _primary_disk_free_gb(self) -> str:
        try:
            usage = psutil.disk_usage(os.environ.get("SystemDrive", "C:") + "\\")
            return f"{usage.free // (1024 ** 3)} GB free on {os.environ.get('SystemDrive', 'C:')}"
        except Exception:
            return "N/A"

    def _active_power_plan(self) -> str:
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            result = subprocess.run(
                ["powercfg", "/getactivescheme"],
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                timeout=5,
            )
            match = re.search(
                r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
                result.stdout,
                re.IGNORECASE,
            )
            if match:
                guid = match.group(1).lower()
                return _POWER_PLAN_NAMES.get(guid, "Custom Plan")
            return "Unknown"
        except Exception:
            return "Unknown"
