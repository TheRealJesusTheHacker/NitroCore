import os
import subprocess
import psutil

from source.utils.config import Config
from source.utils.platform import IS_WINDOWS, hidden_subprocess_kwargs
from source.utils.preview import preview


class PerformanceTuner:
    def __init__(self):
        self.high_perf_guid = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
        self.ultimate_perf_guid = "e9a42b02-d5df-448d-aa00-03f14749eb61"

    def set_process_priority(self):
        if not IS_WINDOWS:
            return "Skipped: process priority tuning is Windows-only"
        target_processes = ("explorer.exe", "dwm.exe")
        if Config.DRY_RUN:
            matched = []
            for proc in psutil.process_iter(["name", "pid"]):
                try:
                    if proc.info["name"] and proc.info["name"].lower() in target_processes:
                        matched.append(f"{proc.info['name']} (PID {proc.info['pid']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            for label in matched:
                preview.record(f"Would raise process priority of {label} to Above Normal")
            if not matched:
                preview.record(
                    "Would raise process priority of explorer.exe / dwm.exe to Above Normal "
                    "(neither is currently running)"
                )
            return (
                f"Process Tuning: Would adjust {len(matched)} system "
                f"component(s) (preview)"
            )
        adjusted_count = 0

        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"] and proc.info["name"].lower() in target_processes:
                    proc.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)
                    adjusted_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return f"Process Tuning: Adjusted {adjusted_count} system components to High Responsiveness"

    def _current_power_scheme(self):
        """Best-effort read of the active power scheme name (safe; used for previews)."""
        try:
            result = subprocess.run(
                ["powercfg", "/getactivescheme"],
                capture_output=True,
                text=True,
                timeout=15,
                **hidden_subprocess_kwargs(),
            )
            output = result.stdout.strip()
            # Format: "Power Scheme GUID: <guid>  (<name>)"
            if "(" in output and output.endswith(")"):
                name = output.rsplit("(", 1)[1].rstrip(")")
                return f"'{name}' "
        except Exception:
            pass
        return ""

    def optimize_power_plan(self):
        if not IS_WINDOWS:
            return "Skipped: power plans are Windows-only"
        if Config.DRY_RUN:
            current = self._current_power_scheme()
            preview.record(
                f"Would switch power plan from {current or 'the current scheme '}"
                f"to 'Ultimate Performance' via powercfg "
                f"(fallback: 'High Performance' if Ultimate is unavailable)"
            )
            return "Power Plan: Would switch to Ultimate Performance (preview)"
        run_kwargs = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            **hidden_subprocess_kwargs(),
        }

        try:
            subprocess.run(
                ["powercfg", "-duplicatescheme", self.ultimate_perf_guid],
                **run_kwargs,
            )

            subprocess.run(
                ["powercfg", "/s", self.ultimate_perf_guid],
                check=True,
                **run_kwargs,
            )
            return "Power Plan: Switched to Ultimate Performance"

        except subprocess.CalledProcessError:
            try:
                subprocess.run(
                    ["powercfg", "/s", self.high_perf_guid],
                    check=True,
                    **run_kwargs,
                )
                return "Power Plan: Switched to High Performance (Standard)"
            except Exception as e:
                return f"Power Plan Error: System rejected profile schema changes: {str(e)}"
        except Exception as e:
            return f"Power Plan Error: {str(e)}"
