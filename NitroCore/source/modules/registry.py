import json
import os
import subprocess
from datetime import datetime

from source.utils.config import Config
from source.utils.platform import IS_WINDOWS, hidden_subprocess_kwargs, system_tool_path
from source.utils.preview import preview

try:
    import winreg
except ImportError:  # Non-Windows platform: registry methods degrade gracefully
    winreg = None

from source.utils.profiles import GAMING

_HIVE_NAMES = {}
if winreg is not None:
    _HIVE_NAMES = {
        winreg.HKEY_CURRENT_USER: "HKCU",
        winreg.HKEY_LOCAL_MACHINE: "HKLM",
        winreg.HKEY_CLASSES_ROOT: "HKCR",
        winreg.HKEY_USERS: "HKU",
        winreg.HKEY_CURRENT_CONFIG: "HKCC",
    }


class RegistryOptimizer:
    # M-4: every registry write snapshots the previous value here first, so a
    # tweak can always be undone. Snapshots persist to a JSON undo file under
    # %APPDATA%\NitroCore (see _write_undo_file / restore_last_undo).
    UNDO_DIRNAME = "registry_undo"

    def __init__(self):
        self.optimization_rules = {
            "disable_hibernation": self._disable_hibernation,
            "optimize_pagefile": self._optimize_pagefile,
            "optimize_performance": self._optimize_performance,
        }
        self._undo_entries = []

    @staticmethod
    def _format_value(value):
        """Render a registry value readably for preview descriptions."""
        if value is None:
            return "(not set)"
        if isinstance(value, bytes):
            return "0x" + value.hex()
        return repr(value)

    def _read_registry_value(self, hive, sub_key, value_name):
        """Best-effort read of the current value (safe; used for previews)."""
        value, _ = self._read_registry_value_full(hive, sub_key, value_name)
        return value

    def _read_registry_value_full(self, hive, sub_key, value_name):
        """Best-effort read of (value, type); (None, None) when absent."""
        if winreg is None:
            return None, None
        try:
            key = winreg.OpenKey(hive, sub_key, 0, winreg.KEY_READ)
            try:
                value, value_type = winreg.QueryValueEx(key, value_name)
                return value, value_type
            finally:
                winreg.CloseKey(key)
        except OSError:
            return None, None

    @staticmethod
    def _serialize_value(value):
        """JSON-safe encoding of a registry value (bytes -> hex)."""
        if isinstance(value, bytes):
            return {"encoding": "hex", "data": value.hex()}
        return {"encoding": "raw", "data": value}

    @staticmethod
    def _deserialize_value(payload):
        if payload.get("encoding") == "hex":
            return bytes.fromhex(payload["data"])
        return payload.get("data")

    def _undo_dir(self):
        base = os.path.realpath(os.path.expandvars("%APPDATA%\\NitroCore"))
        path = os.path.join(base, self.UNDO_DIRNAME)
        try:
            os.makedirs(path, exist_ok=True)
        except OSError:
            pass
        return path

    def _write_undo_file(self):
        """Persist this run's pre-change snapshots as a timestamped undo file."""
        if not self._undo_entries:
            return None
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        undo_file = os.path.join(self._undo_dir(), f"undo-{stamp}.json")
        payload = {
            "created": stamp,
            "entries": [
                {
                    "hive": e["hive_name"],
                    "sub_key": e["sub_key"],
                    "value_name": e["value_name"],
                    "old_value": self._serialize_value(e["old_value"]),
                    "old_type": e["old_type"],
                    "existed": e["existed"],
                }
                for e in self._undo_entries
            ],
        }
        try:
            with open(undo_file, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
        except OSError:
            # Write failed: keep the in-memory snapshots so a later run can
            # still persist them. Entries are only dropped once safely on disk.
            return None
        # The snapshots are durable now — drop the in-memory copies so the
        # next run starts fresh. Without this, repeated runs accumulate stale
        # snapshots and a later "undo" could revert to values from an earlier
        # run instead of the run being undone.
        self._undo_entries = []
        return undo_file

    def restore_last_undo(self) -> str:
        """Restore registry values from the most recent undo file (one-click undo)."""
        if winreg is None:
            return "Skipped: registry restore is Windows-only"
        undo_dir = self._undo_dir()
        try:
            files = sorted(
                f
                for f in os.listdir(undo_dir)
                if f.startswith("undo-") and f.endswith(".json")
            )
        except OSError:
            files = []
        if not files:
            return "No registry undo snapshots found — nothing to restore"
        undo_file = os.path.join(undo_dir, files[-1])
        try:
            with open(undo_file, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except (OSError, ValueError) as e:
            return f"Could not read undo file: {e}"
        # BH2-3 (bug hunt 2026-10-13): valid JSON with the wrong shape
        # (a list, a bare string, "entries" that isn't a list, non-object
        # entries) used to raise AttributeError/TypeError out of this
        # method — the undo file is user-writable, so a corrupt or
        # hand-edited file crashed the restore instead of reporting.
        if not isinstance(payload, dict) or not isinstance(
            payload.get("entries"), list
        ):
            return (
                "Could not read undo file: unexpected format "
                "(expected a JSON object with an 'entries' list)"
            )
        restored, failed = 0, 0
        hive_by_name = {v: k for k, v in _HIVE_NAMES.items()}
        for entry in payload["entries"]:
            if not isinstance(entry, dict):
                failed += 1
                continue
            # S-1 (audit 2026-10-11): undo files live under %APPDATA%, which is
            # user-writable. A planted undo-*.json must never turn this
            # elevated process into a registry writer outside HKCU. Every
            # snapshot this app writes is HKCU, so entries naming any other
            # hive are refused outright.
            if entry.get("hive") != "HKCU":
                failed += 1
                continue
            hive = hive_by_name["HKCU"]
            if hive is None:
                failed += 1
                continue
            try:
                key = winreg.CreateKeyEx(
                    hive, entry["sub_key"], 0, winreg.KEY_SET_VALUE
                )
                if entry.get("existed"):
                    winreg.SetValueEx(
                        key,
                        entry["value_name"],
                        0,
                        entry["old_type"],
                        self._deserialize_value(entry["old_value"]),
                    )
                else:
                    # Value didn't exist before we created it — remove it.
                    try:
                        winreg.DeleteValue(key, entry["value_name"])
                    except OSError:
                        pass
                winreg.CloseKey(key)
                restored += 1
            except Exception:
                failed += 1
        return (
            f"Registry undo: restored {restored} value(s)"
            + (f", {failed} failed" if failed else "")
            + f" (from {os.path.basename(undo_file)})"
        )

    def _set_registry_value(self, hive, sub_key, value_name, value, value_type=None):
        """
        Helper method to modify the Windows Registry safely.
        Creates the key path if it does not already exist.
        M-4: snapshots the previous value before every write.
        """
        if winreg is None:
            return False
        if Config.DRY_RUN:
            old_value = self._read_registry_value(hive, sub_key, value_name)
            hive_name = _HIVE_NAMES.get(hive, str(hive))
            preview.record(
                f"Would set registry value {hive_name}\\{sub_key}\\{value_name} to "
                f"{self._format_value(value)} (was {self._format_value(old_value)})"
            )
            return True
        if value_type is None:
            value_type = winreg.REG_DWORD
        # M-4: snapshot the pre-change value for the undo file.
        old_value, old_type = self._read_registry_value_full(hive, sub_key, value_name)
        self._undo_entries.append(
            {
                "hive_name": _HIVE_NAMES.get(hive, str(hive)),
                "sub_key": sub_key,
                "value_name": value_name,
                "old_value": old_value,
                "old_type": old_type,
                "existed": old_type is not None,
            }
        )
        try:
            # Open or create the key path with write permissions
            key = winreg.CreateKeyEx(hive, sub_key, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, value_name, 0, value_type, value)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"Failed registry write [{sub_key}\\{value_name}]: {e}")
            return False

    def _disable_hibernation(self):
        """Disable hibernation to free up disk space and reduce OS storage overhead"""
        if not IS_WINDOWS:
            return "Skipped: hibernation control is Windows-only"
        if Config.DRY_RUN:
            preview.record("Would run: powercfg /hibernate off (disables hibernation)")
            return "Hibernation: would be disabled (preview)"
        try:
            subprocess.run(
                [system_tool_path("powercfg"), "/hibernate", "off"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                # BH2-4 (bug hunt 2026-10-13): this and the pagefile call
                # below were the last subprocess sites in the app without
                # a timeout (W-6 bounded the rest) — a hung powercfg or
                # PowerShell would wedge the worker thread and the GUI
                # busy state forever. A timeout now lands in the existing
                # error handlers and returns a readable failure string.
                timeout=30,
                **hidden_subprocess_kwargs(),
            )
            return "Hibernation Disabled Successfully"
        except subprocess.CalledProcessError:
            return "Failed to disable hibernation (Requires Administrator privileges)"
        except Exception as e:
            return f"Error disabling hibernation: {str(e)}"

    def _optimize_pagefile(self):
        """
        Configures the system to manage the pagefile automatically, which avoids
        unnecessary disk thrashing from a fixed-size pagefile.
        """
        if not IS_WINDOWS:
            return "Skipped: pagefile control is Windows-only"
        if Config.DRY_RUN:
            preview.record(
                "Would enable automatic pagefile management "
                "(PowerShell CIM: Set AutomaticManagedPagefile=True)"
            )
            return "Pagefile: would be set to automatic management (preview)"
        # wmic was removed from Windows 11 (24H2+); only the PowerShell CIM
        # path is used now. List form only — no shell invocation anywhere.
        try:
            subprocess.run(
                [
                    # S-2 (audit 2026-10-11): resolve via System32, not PATH —
                    # this process runs elevated.
                    system_tool_path("powershell"),
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    "Get-CimInstance Win32_ComputerSystem | "
                    "Set-CimInstance -Property @{AutomaticManagedPagefile=$true}",
                ],
                shell=False,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                # BH2-4: see _disable_hibernation — PowerShell/CIM gets a
                # longer bound than powercfg (cold start + CIM on a loaded
                # machine), but it must be bounded.
                timeout=120,
                **hidden_subprocess_kwargs(),
            )
            return "Pagefile configuration optimized to automatic management"
        except Exception as e:
            return f"Failed to optimize pagefile layout: {str(e)}"

    def _optimize_performance(self):
        """Apply native Windows registry performance adjustments for low visual latency"""
        if winreg is None:
            return "Skipped: registry tweaks are Windows-only"
        success_count = 0

        # Structure tweaks with explicit paths, names, values, and types
        tweaks = [
            # 1 = Adjust for best performance (disables heavy window animations, shadows, etc.)
            {
                "hive": winreg.HKEY_CURRENT_USER,
                "path": r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
                "name": "VisualFXSetting",
                "value": 1,
                "type": winreg.REG_DWORD,
            },
            # Disables menu fade animations to make window opening snappier
            {
                "hive": winreg.HKEY_CURRENT_USER,
                "path": r"Control Panel\Desktop",
                "name": "UserPreferencesMask",
                "value": b"\x90\x12\x03\x80\x10\x00\x00\x00",  # Hex byte sequence for disabled effects
                "type": winreg.REG_BINARY,
            },
            # Lowering delay before menus hover/pop open (Default is 400ms, optimized to 10ms)
            {
                "hive": winreg.HKEY_CURRENT_USER,
                "path": r"Control Panel\Desktop",
                "name": "MenuShowDelay",
                "value": "10",
                "type": winreg.REG_SZ,
            },
        ]

        for tweak in tweaks:
            res = self._set_registry_value(
                hive=tweak["hive"],
                sub_key=tweak["path"],
                value_name=tweak["name"],
                value=tweak["value"],
                value_type=tweak["type"],
            )
            if res:
                success_count += 1

        if Config.DRY_RUN:
            return f"Would apply {success_count}/{len(tweaks)} performance registry tweaks (preview)"
        undo_file = self._write_undo_file()
        undo_note = (
            f" (previous values saved to {os.path.basename(undo_file)})"
            if undo_file
            else ""
        )
        return f"Applied {success_count}/{len(tweaks)} performance registry tweaks{undo_note}"

    def apply_all(self):
        """Apply all system optimizations and aggregate responses cleanly for the UI status log"""
        summary_reports = []
        for name, func in self.optimization_rules.items():
            formatted_name = name.replace("_", " ").title()
            execution_result = func()
            summary_reports.append(f"{formatted_name}: {execution_result}")

        # Join into a single multi-line string text payload for our safe UI display
        return "\n".join(summary_reports)

    def apply_for_profile(self, profile: str) -> str:
        """Apply registry tweaks scoped to the active optimization profile."""
        if profile == GAMING:
            return self.apply_all()
        result = self._optimize_performance()
        return f"Cybersecurity Profile: {result}"
