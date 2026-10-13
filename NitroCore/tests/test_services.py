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


# --- W-5 (audit 2026-10-13): _set_service_startup_safely handle/error paths ---
#
# pywin32 is absent off Windows, so the module globals are replaced with
# fakes. The behavior pinned here: the service handle is released on EVERY
# path after a successful OpenService, and failures come back as result
# strings instead of raising (a raise used to abort the whole services step).


class _FakeWinError(Exception):
    """Stand-in for pywintypes.error (carries winerror/strerror)."""

    def __init__(self, winerror, strerror):
        super().__init__(strerror)
        self.winerror = winerror
        self.strerror = strerror


def _install_fake_win32(monkeypatch, *, open_error=None, config_error=None):
    import types

    import source.modules.services as services_module

    closed = []

    def open_service(scm_handle, name, access):
        if open_error is not None:
            raise open_error
        return "svc-handle"

    def change_config(*args):
        if config_error is not None:
            raise config_error

    fake_win32service = types.SimpleNamespace(
        SERVICE_CHANGE_CONFIG=0x0002,
        SERVICE_NO_CHANGE=0xFFFFFFFF,
        OpenService=open_service,
        ChangeServiceConfig=change_config,
        CloseServiceHandle=closed.append,
    )
    monkeypatch.setattr(services_module, "win32service", fake_win32service)
    monkeypatch.setattr(
        services_module, "pywintypes", types.SimpleNamespace(error=_FakeWinError)
    )
    return closed


def test_set_startup_success_closes_handle(monkeypatch):
    closed = _install_fake_win32(monkeypatch)
    result = ServiceManager()._set_service_startup_safely(None, "WSearch", 3)
    assert result == "Startup Set to Manual"
    assert closed == ["svc-handle"]


def test_set_startup_config_failure_still_closes_handle(monkeypatch):
    closed = _install_fake_win32(
        monkeypatch, config_error=_FakeWinError(5, "Access is denied")
    )
    result = ServiceManager()._set_service_startup_safely(None, "WSearch", 3)
    assert result == "Config Failed (Access is denied)"
    assert closed == ["svc-handle"]


def test_set_startup_not_found_opens_nothing(monkeypatch):
    closed = _install_fake_win32(
        monkeypatch, open_error=_FakeWinError(1060, "does not exist")
    )
    result = ServiceManager()._set_service_startup_safely(None, "Nope", 3)
    assert result == "Not Found"
    assert closed == []


def test_set_startup_unexpected_error_is_reported_not_raised(monkeypatch):
    closed = _install_fake_win32(monkeypatch, config_error=RuntimeError("boom"))
    result = ServiceManager()._set_service_startup_safely(None, "WSearch", 3)
    assert result.startswith("Config Failed")
    assert closed == ["svc-handle"]
