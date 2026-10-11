"""Guard-path and targeting tests for ServiceManager.

No test here touches the Windows Service Control Manager: the platform
guard short-circuits off Windows, and the profile-targeting logic is
verified by stubbing the private ``_optimize_services`` instead of the SCM.
"""

import sys

import pytest
from source.modules.services import _SECURITY_WARNING, ServiceManager


def test_services_to_optimize_list():
    assert ServiceManager().services_to_optimize == ["wuauserv", "BITS", "WSearch"]


@pytest.mark.skipif(sys.platform == "win32", reason="non-Windows guard")
def test_optimize_for_profile_guard_off_windows():
    manager = ServiceManager()
    assert manager.optimize_for_profile("gaming").startswith("Skipped:")
    assert manager.optimize_for_profile("cybersecurity").startswith("Skipped:")
    assert manager.optimize_all_services().startswith("Skipped:")


def test_optimize_for_profile_targets(monkeypatch):
    # pin the pure targeting decision without involving the SCM
    captured = {}

    def fake_optimize(self, service_names):
        captured["names"] = list(service_names)
        return "stubbed"

    monkeypatch.setattr(ServiceManager, "_optimize_services", fake_optimize)
    manager = ServiceManager()

    manager.optimize_for_profile("gaming")
    assert captured["names"] == ["wuauserv", "BITS", "WSearch"]

    manager.optimize_for_profile("cybersecurity")
    # cybersecurity keeps Windows Update / BITS alive for patching
    assert captured["names"] == ["WSearch"]


def test_security_warning_names_the_patch_services():
    assert "wuauserv" in _SECURITY_WARNING
    assert "BITS" in _SECURITY_WARNING
    assert "Manual" in _SECURITY_WARNING
    assert "will NOT install automatically" in _SECURITY_WARNING
