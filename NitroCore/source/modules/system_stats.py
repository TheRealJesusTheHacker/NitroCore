"""Live system telemetry for the NitroCore dashboard header."""

import os
import re
import subprocess
import time
import weakref
from typing import Dict, Optional

import psutil

from source.utils.platform import IS_WINDOWS, hidden_subprocess_kwargs

_POWER_PLAN_NAMES = {
    "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c": "High Performance",
    "e9a42b02-d5df-448d-aa00-03f14749eb61": "Ultimate Performance",
    "381b4222-f694-41f0-9685-ff5bb260df2e": "Balanced",
    "a1841308-3541-4fab-bc81-715741643351": "Power Saver",
}

# Power plan changes rarely; cache it instead of spawning powercfg on every poll.
_POWER_PLAN_TTL_SECONDS = 120.0

# Disk free space barely moves on a 2s poll cadence; cache the syscall result.
_DISK_USAGE_TTL_SECONDS = 30.0

# Live SystemStats instances. The optimization pipeline calls
# invalidate_all_power_plan_caches() when it changes the power plan so the
# header re-queries instead of showing the stale plan for up to 120s.
_INSTANCES = weakref.WeakSet()


class SystemStats:
    """Collects CPU, memory, disk, and power plan metrics."""

    def __init__(self):
        psutil.cpu_percent(interval=None)
        _INSTANCES.add(self)
        self._power_plan_cache: Optional[str] = None
        self._power_plan_cached_at: float = 0.0
        self._disk_cache: Optional[str] = None
        self._disk_cached_at: float = 0.0

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
        now = time.monotonic()
        if self._disk_cache is not None and now - self._disk_cached_at < _DISK_USAGE_TTL_SECONDS:
            return self._disk_cache
        try:
            usage = psutil.disk_usage(os.environ.get("SystemDrive", "C:") + "\\")
            self._disk_cache = (
                f"{usage.free // (1024 ** 3)} GB free on "
                f"{os.environ.get('SystemDrive', 'C:')}"
            )
        except Exception:
            self._disk_cache = "N/A"
        self._disk_cached_at = now
        return self._disk_cache

    def _active_power_plan(self) -> str:
        now = time.monotonic()
        if (
            self._power_plan_cache is not None
            and now - self._power_plan_cached_at < _POWER_PLAN_TTL_SECONDS
        ):
            return self._power_plan_cache
        plan = self._query_power_plan()
        self._power_plan_cache = plan
        self._power_plan_cached_at = now
        return plan

    def invalidate_power_plan_cache(self) -> None:
        """Force the next snapshot to re-query the active power plan."""
        self._power_plan_cache = None

    def _query_power_plan(self) -> str:
        if not IS_WINDOWS:
            return "N/A"
        try:
            result = subprocess.run(
                ["powercfg", "/getactivescheme"],
                capture_output=True,
                text=True,
                timeout=5,
                **hidden_subprocess_kwargs(),
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


def invalidate_all_power_plan_caches() -> None:
    """Force every live SystemStats instance to re-query the power plan on next poll."""
    for instance in list(_INSTANCES):
        instance.invalidate_power_plan_cache()
