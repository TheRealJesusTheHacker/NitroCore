import os
import subprocess
import psutil

from source.utils.platform import IS_WINDOWS, hidden_subprocess_kwargs


class PerformanceTuner:
    def __init__(self):
        self.high_perf_guid = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
        self.ultimate_perf_guid = "e9a42b02-d5df-448d-aa00-03f14749eb61"

    def set_process_priority(self):
        if not IS_WINDOWS:
            return "Skipped: process priority tuning is Windows-only"
        target_processes = ("explorer.exe", "dwm.exe")
        adjusted_count = 0

        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"] and proc.info["name"].lower() in target_processes:
                    proc.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)
                    adjusted_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return f"Process Tuning: Adjusted {adjusted_count} system components to High Responsiveness"

    def optimize_power_plan(self):
        if not IS_WINDOWS:
            return "Skipped: power plans are Windows-only"
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
