"""Timeout bounds for the registry module's subprocess calls (BH2-4).

W-6 (audit 2026-10-13) bounded every subprocess call in
PerformanceTuner — but _disable_hibernation (powercfg) and
_optimize_pagefile (PowerShell CIM) in registry.py were left unbounded,
the last two in the app. A hung helper would wedge the worker thread and
the GUI busy state forever. These tests pin the bounds and that a
timeout lands in the existing error strings instead of hanging.
"""

import subprocess
from types import SimpleNamespace

import pytest
import source.modules.registry as registry_module
from source.modules.registry import RegistryOptimizer
from source.utils.config import Config


@pytest.fixture()
def fake_run(monkeypatch):
    calls = []

    def run(args, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")

    monkeypatch.setattr(registry_module, "IS_WINDOWS", True)
    monkeypatch.setattr(Config, "DRY_RUN", False, raising=False)
    monkeypatch.setattr(registry_module.subprocess, "run", run)
    return calls


def test_disable_hibernation_is_time_bounded(fake_run):
    result = RegistryOptimizer()._disable_hibernation()
    assert result == "Hibernation Disabled Successfully"
    assert fake_run and fake_run[0].get("timeout") == 30


def test_optimize_pagefile_is_time_bounded(fake_run):
    result = RegistryOptimizer()._optimize_pagefile()
    assert result == "Pagefile configuration optimized to automatic management"
    assert fake_run and fake_run[0].get("timeout") == 120


def test_disable_hibernation_timeout_reports_error(monkeypatch):
    monkeypatch.setattr(registry_module, "IS_WINDOWS", True)
    monkeypatch.setattr(Config, "DRY_RUN", False, raising=False)

    def run(args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="powercfg", timeout=30)

    monkeypatch.setattr(registry_module.subprocess, "run", run)
    result = RegistryOptimizer()._disable_hibernation()
    assert result.startswith("Error disabling hibernation")


def test_optimize_pagefile_timeout_reports_error(monkeypatch):
    monkeypatch.setattr(registry_module, "IS_WINDOWS", True)
    monkeypatch.setattr(Config, "DRY_RUN", False, raising=False)

    def run(args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="powershell", timeout=120)

    monkeypatch.setattr(registry_module.subprocess, "run", run)
    result = RegistryOptimizer()._optimize_pagefile()
    assert result.startswith("Failed to optimize pagefile layout")
