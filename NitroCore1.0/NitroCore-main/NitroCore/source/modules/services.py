import win32service
import pywintypes

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

    def _optimize_services(self, service_names):
        results = []

        try:
            scm_handle = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
        except pywintypes.error:
            return "Services Optimization Error: Access Denied (Requires Administrator privileges)"

        for service_name in service_names:
            stop_res = self._stop_service_safely(scm_handle, service_name)
            config_res = self._set_service_startup_safely(
                scm_handle, service_name, win32service.SERVICE_DEMAND_START
            )
            results.append(f"{service_name}: {stop_res} | Config: {config_res}")

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
