try:
    import win32service
    import pywintypes
except ImportError:  # Non-Windows platform: service methods degrade gracefully
    win32service = None
    pywintypes = None

from source.utils.config import Config
from source.utils.preview import preview
from source.utils.profiles import GAMING

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
            scm_handle = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
        except Exception:
            return ""
        try:
            try:
                svc_handle = win32service.OpenService(
                    scm_handle,
                    service_name,
                    win32service.SERVICE_QUERY_STATUS | win32service.SERVICE_QUERY_CONFIG,
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
            return (
                f"Services: would stop and reconfigure {len(service_names)} "
                f"service(s), 0 changed (preview)"
            )

        try:
            scm_handle = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
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
        return "\n".join(results)

    def _stop_service_safely(self, scm_handle, service_name):
        try:
            svc_handle = win32service.OpenService(
                scm_handle, service_name,
                win32service.SERVICE_QUERY_STATUS | win32service.SERVICE_STOP,
            )
            status = win32service.QueryServiceStatus(svc_handle)
            if status[1] == win32service.SERVICE_STOPPED:
                win32service.CloseServiceHandle(svc_handle)
                return "Already Stopped"

            win32service.ControlService(svc_handle, win32service.SERVICE_CONTROL_STOP)
            win32service.CloseServiceHandle(svc_handle)
            return "Stopped Successfully"

        except pywintypes.error as e:
            if e.winerror == 1060:
                return "Not Found on System"
            return f"Stop Failed ({e.strerror})"

    def _set_service_startup_safely(self, scm_handle, service_name, startup_type):
        try:
            svc_handle = win32service.OpenService(
                scm_handle, service_name, win32service.SERVICE_CHANGE_CONFIG
            )
            win32service.ChangeServiceConfig(
                svc_handle,
                win32service.SERVICE_NO_CHANGE,
                startup_type,
                win32service.SERVICE_NO_CHANGE,
                None, None, 0, None, None, None, None,
            )
            win32service.CloseServiceHandle(svc_handle)
            return "Startup Set to Manual"

        except pywintypes.error as e:
            if e.winerror == 1060:
                return "Not Found"
            return f"Config Failed ({e.strerror})"
