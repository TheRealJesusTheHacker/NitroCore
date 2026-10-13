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


# --- BH2-1/BH2-2 (bug hunt 2026-10-13): _stop_service_safely error paths ---
#
# The W-5 generic-exception guard covered _set_service_startup_safely but
# not _stop_service_safely: a non-win32 failure (e.g. RuntimeError from a
# torn-down RPC binding) propagated out of _optimize_services, aborting
# the remaining services and discarding every result. And _wait_for_stop
# bailed on the first SERVICE_RUNNING read, racing ControlService — a
# stop that succeeded a moment later was reported as "timed out".


def _install_full_fake_win32(
    monkeypatch,
    *,
    status_by_name=None,
    open_error=None,
    control_error=None,
):
    """Fuller fake SCM rig for the stop path and whole-step runs.

    status_by_name maps a service name to either a state constant or a
    list of states returned in sequence (final state repeats).
    """
    import types

    import source.modules.services as services_module

    closed = []
    sequences = {
        name: list(states) if isinstance(states, list) else [states]
        for name, states in (status_by_name or {}).items()
    }
    handle_names = {}

    def open_scm(*args):
        return "scm-handle"

    def open_service(scm_handle, name, access):
        if open_error is not None:
            raise open_error
        handle = f"svc-{name}"
        handle_names[handle] = name
        return handle

    def query_status(handle):
        name = handle_names.get(handle) or str(handle).removeprefix("svc-")
        seq = sequences[name]
        state = seq.pop(0) if len(seq) > 1 else seq[0]
        if isinstance(state, BaseException):
            raise state
        return (0, state, 0, 0, 0, 0, 0)

    def control_service(handle, code):
        if control_error is not None:
            raise control_error

    def change_config(*args):
        return None

    fake_win32service = types.SimpleNamespace(
        SC_MANAGER_ALL_ACCESS=0xF003F,
        SERVICE_QUERY_STATUS=0x0004,
        SERVICE_STOP=0x0020,
        SERVICE_CHANGE_CONFIG=0x0002,
        SERVICE_CONTROL_STOP=0x0001,
        SERVICE_NO_CHANGE=0xFFFFFFFF,
        SERVICE_DEMAND_START=0x0003,
        SERVICE_STOPPED=0x0001,
        SERVICE_RUNNING=0x0004,
        SERVICE_PAUSED=0x0007,
        SERVICE_STOP_PENDING=0x0003,
        OpenSCManager=open_scm,
        OpenService=open_service,
        QueryServiceStatus=query_status,
        ControlService=control_service,
        ChangeServiceConfig=change_config,
        CloseServiceHandle=closed.append,
    )
    monkeypatch.setattr(services_module, "win32service", fake_win32service)
    monkeypatch.setattr(
        services_module, "pywintypes", types.SimpleNamespace(error=_FakeWinError)
    )
    # _wait_for_stop sleeps 0.5s between polls; keep the suite fast.
    monkeypatch.setattr(services_module.time, "sleep", lambda _s: None)
    return closed


def test_stop_open_unexpected_error_is_reported_not_raised(monkeypatch):
    _install_full_fake_win32(monkeypatch, open_error=RuntimeError("RPC exploded"))
    result = ServiceManager()._stop_service_safely("scm-handle", "WSearch")
    assert result.startswith("Stop Failed")


def test_stop_query_unexpected_error_closes_handle(monkeypatch):
    closed = _install_full_fake_win32(
        monkeypatch, status_by_name={"WSearch": RuntimeError("RPC exploded")}
    )
    result = ServiceManager()._stop_service_safely("scm-handle", "WSearch")
    assert result.startswith("Stop Failed")
    assert closed == ["svc-WSearch"]


def test_stop_control_unexpected_error_closes_handle(monkeypatch):
    closed = _install_full_fake_win32(
        monkeypatch,
        status_by_name={"WSearch": 0x0004},  # SERVICE_RUNNING
        control_error=RuntimeError("boom"),
    )
    result = ServiceManager()._stop_service_safely("scm-handle", "WSearch")
    assert result.startswith("Stop Failed")
    assert closed == ["svc-WSearch"]


def test_stop_not_found_still_reported(monkeypatch):
    _install_full_fake_win32(
        monkeypatch, open_error=_FakeWinError(1060, "does not exist")
    )
    result = ServiceManager()._stop_service_safely("scm-handle", "Nope")
    assert result == "Not Found on System"


def test_wait_for_stop_tolerates_running_before_stopped(monkeypatch):
    # The BH2-2 race: ControlService returns while the service still
    # reports RUNNING (STOP_PENDING not yet posted), then it stops.
    # States: SERVICE_RUNNING=4, SERVICE_STOPPED=1.
    _install_full_fake_win32(
        monkeypatch,
        status_by_name={"WSearch": [4, 4, 1]},
    )
    assert ServiceManager._wait_for_stop("svc-WSearch", timeout_s=5.0) is True


def test_wait_for_stop_settled_state_still_fails_fast(monkeypatch):
    # SERVICE_PAUSED=7: settled in a non-stopped state — fail immediately,
    # as before (only RUNNING / STOP_PENDING keep polling now).
    _install_full_fake_win32(monkeypatch, status_by_name={"WSearch": 7})
    assert ServiceManager._wait_for_stop("svc-WSearch", timeout_s=5.0) is False


def test_optimize_services_survives_one_bad_service(monkeypatch):
    # BH2-1 end-to-end: the first service's status query explodes with a
    # non-win32 error; the step must still process the second service and
    # return both result lines instead of raising.
    closed = _install_full_fake_win32(
        monkeypatch,
        status_by_name={
            "SvcA": RuntimeError("RPC exploded"),
            "SvcB": 1,  # SERVICE_STOPPED
        },
    )
    result = ServiceManager()._optimize_services(["SvcA", "SvcB"])
    lines = result.splitlines()
    assert len(lines) == 2
    assert lines[0].startswith("SvcA: Stop Failed")
    assert "Config: Startup Set to Manual" in lines[0]
    assert lines[1].startswith("SvcB: Already Stopped")
    assert "scm-handle" in closed
