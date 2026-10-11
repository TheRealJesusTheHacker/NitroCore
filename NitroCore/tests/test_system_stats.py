"""Tests for SystemStats — read-only telemetry, safe on all platforms.

``snapshot()`` only reads CPU/RAM/disk counters via psutil; the power-plan
query degrades to ``"N/A"`` off Windows instead of shelling out.
"""

import sys

import pytest
from source.modules.system_stats import (
    SystemStats,
    invalidate_all_power_plan_caches,
)


def test_snapshot_shape():
    snapshot = SystemStats().snapshot()
    assert set(snapshot) == {"cpu", "ram", "disk", "power"}
    assert snapshot["cpu"].endswith("%")
    assert "GB" in snapshot["ram"]
    assert isinstance(snapshot["disk"], str) and snapshot["disk"]
    assert isinstance(snapshot["power"], str) and snapshot["power"]


@pytest.mark.skipif(sys.platform == "win32", reason="non-Windows behavior")
def test_power_plan_query_na_off_windows():
    assert SystemStats()._query_power_plan() == "N/A"


def test_power_plan_cache_invalidation_forces_requery():
    stats = SystemStats()
    stats._power_plan_cache = "Cached Plan"
    stats.invalidate_power_plan_cache()
    assert stats._power_plan_cache is None


def test_invalidate_all_power_plan_caches_hits_every_instance():
    first = SystemStats()
    second = SystemStats()
    first._power_plan_cache = "Cached Plan"
    second._power_plan_cache = "Cached Plan"
    invalidate_all_power_plan_caches()
    assert first._power_plan_cache is None
    assert second._power_plan_cache is None


def test_disk_cache_ttl_constant_sane():
    from source.modules import system_stats as stats_module

    assert stats_module._DISK_USAGE_TTL_SECONDS == 30.0
    assert stats_module._POWER_PLAN_TTL_SECONDS == 120.0


def test_known_power_plan_guids_mapped():
    from source.modules import system_stats as stats_module

    names = stats_module._POWER_PLAN_NAMES
    assert names["e9a42b02-d5df-448d-aa00-03f14749eb61"] == "Ultimate Performance"
    assert names["8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"] == "High Performance"
    assert names["381b4222-f694-41f0-9685-ff5bb260df2e"] == "Balanced"
