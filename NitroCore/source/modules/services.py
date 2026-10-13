try:
    import pywintypes
    import win32service
except ImportError:  # Non-Windows platform: service methods degrade gracefully
    win32service = None
    pywintypes = None

import time

from source.utils.config import Config
from source.utils.preview import preview
from source.utils.profiles import GAMING

# Services whose startup change degrades OS security patching. Users must be
# told explicitly what they're trading away (M-2).
_SECURITY_SENSITIVE_SERVICES = ("wuauserv", "BITS")
_SECURITY_WARNING = (
    "SECURITY NOTE: Windows Update (wuauserv) and BITS were set to Manual — "
    "security patches will NOT install automatically until you re-enable them "
    "(Services app -> Windows Update -> Automatic)."
)


class ServiceManager:
    def __init__(self):
        self.services_to_optimize = [
            "wuauserv",
            "BITS",
            "WSearch",
        ]

    def optimize_all_services(self):
        return self._optimize_services(self.services_to_optimize)

    def optimize_for_profile(self, profile: str) -> str:
        if profile == GAMING:
            targets = list(self.services_to_optimize)
        else:
            targets = ["WSearch"]
        return self._optimize_services(targets)

    def _describe_service_current(self, service_name):
        """Best-effort read of a service's current state/startup (safe; used for previews)."""
        if win32service is None:
            return ""
        try:
            scm_handle = win32service.OpenSCManager(
                None, None, win32service.SC_MANAGER_CONNECT
            )
        except Exception:
            return ""
        try:
            try:
                svc_handle = win32service.OpenService(
                    scm_handle,
                    service_name,
                    win32service.SERVICE_QUERY_STATUS
                    | win32service.SERVICE_QUERY_CONFIG,
                )
            except Exception:
                return " (not found on this system)"
            try:
                status = win32service.QueryServiceStatus(svc_handle)[1]
                start_type = win32service.QueryServiceConfig(svc_handle)[1]
                state_names = {
                    win32service.SERVICE_STOPPED: "stopped",
                    win32service.SERVICE_RUNNING: "running",
                    win32service.SERVICE_PAUSED: "paused",
                }
                start_names = {
                    win32service.SERVICE_AUTO_START: "Automatic",
                    win32service.SERVICE_DEMAND_START: "Manual",
                    win32service.SERVICE_DISABLED: "Disabled",
                }
                state = state_names.get(status, "unknown state")
                start = start_names.get(start_type, "unknown startup")
                return f" (currently {state}, startup: {start})"
            finally:
                win32service.CloseServiceHandle(svc_handle)
        except Exception:
            return ""
        finally:
            win32service.CloseServiceHandle(scm_handle)

    def _optimize_services(self, service_names):
        results = []

        if win32service is None:
            return "Skipped: service management is Windows-only"

        if Config.DRY_RUN:
            for service_name in service_names:
                current = self._describe_service_current(service_name)
                preview.record(
                    f"Would stop service '{service_name}'{current} "
                    f"and set its startup type to Manual"
                )
            if any(s in _SECURITY_SENSITIVE_SERVICES for s in service_names):
                preview.record(_SECURITY_WARNING)
            return (
                f"Services: would stop and reconfigure {len(service_names)} "
                f"service(s), 0 changed (preview)"
            )

        try:
            scm_handle = win32service.OpenSCManager(
                None, None, win32service.SC_MANAGER_ALL_ACCESS
            )
        except Exception:
            return "Services Optimization Error: Access Denied (Requires Administrator privileges)"

        try:
            for service_name in service_names:
                stop_res = self._stop_service_safely(scm_handle, service_name)
                config_res = self._set_service_startup_safely(
                    scm_handle, service_name, win32service.SERVICE_DEMAND_START
                )
                results.append(f"{service_name}: {stop_res} | Config: {config_res}")
        finally:
            win32service.CloseServiceHandle(scm_handle)
        if any(s in _SECURITY_SENSITIVE_SERVICES for s in service_names):
            results.append(_SECURITY_WARNING)
        return "\n".join(results)

    def _stop_service_safely(self, scm_handle, service_name):
        try:
            svc_handle = win32service.OpenService(
                scm_handle,
                service_name,
                win32service.SERVICE_QUERY_STATUS | win32service.SERVICE_STOP,
            )
        except pywintypes.error as e:
            if e.winerror == 1060:
                return "Not Found on System"
            return f"Stop Failed ({e.strerror})"
        try:
            status = win32service.QueryServiceStatus(svc_handle)
            if status[1] == win32service.SERVICE_STOPPED:
                return "Already Stopped"

            win32service.ControlService(svc_handle, win32service.SERVICE_CONTROL_STOP)
            # L-6: ControlService is fire-and-forget. Poll until the service
            # actually reaches STOPPED (or a stop-pending timeout) so the
            # reported result reflects reality.
            stopped = self._wait_for_stop(svc_handle, timeout_s=15.0)
            return (
                "Stopped Successfully"
                if stopped
                else "Stop Requested (timed out waiting for STOPPED)"
            )
        except pywintypes.error as e:
            if e.winerror == 1060:
                return "Not Found on System"
            return f"Stop Failed ({e.strerror})"
        finally:
            # W-4 (audit 2026-10-11): every OpenService success path must
            # release its handle — QueryServiceStatus/ControlService can
            # raise after the handle is open, which previously leaked it.
            win32service.CloseServiceHandle(svc_handle)

    @staticmethod
    def _wait_for_stop(svc_handle, timeout_s: float = 15.0) -> bool:
        """Poll QueryServiceStatus until SERVICE_STOPPED or timeout."""
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            try:
                state = win32service.QueryServiceStatus(svc_handle)[1]
            except Exception:
                return False
            if state == win32service.SERVICE_STOPPED:
                return True
            if state != win32service.SERVICE_STOP_PENDING:
                # Service settled in a non-stopped state (e.g. paused).
                return False
            time.sleep(0.5)
        return False

    def _set_service_startup_safely(self, scm_handle, service_name, startup_type):
        try:
            svc_handle = win32service.OpenService(
                scm_handle, service_name, win32service.SERVICE_CHANGE_CONFIG
            )
        except pywintypes.error as e:
            if e.winerror == 1060:
                return "Not Found"
            return f"Config Failed ({e.strerror})"
        except Exception as e:
            return f"Config Failed ({e})"
        try:
            win32service.ChangeServiceConfig(
                svc_handle,
                win32service.SERVICE_NO_CHANGE,
                startup_type,
                win32service.SERVICE_NO_CHANGE,
                None,
                None,
                0,
                None,
                None,
                None,
                None,
            )
            return "Startup Set to Manual"
        except pywintypes.error as e:
            if e.winerror == 1060:
                return "Not Found"
            return f"Config Failed ({e.strerror})"
        except Exception as e:
            # W-5 (audit 2026-10-13): a non-win32 failure here previously
            # propagated out of _optimize_services, aborting the remaining
            # services and failing the whole step. Report it per-service,
            # like every other failure path in this class.
            return f"Config Failed ({e})"
        finally:
            # W-5: every OpenService success path must release its handle —
            # ChangeServiceConfig raising previously leaked it (the W-4
            # pattern from _stop_service_safely, applied here too).
            win32service.CloseServiceHandle(svc_handle)
