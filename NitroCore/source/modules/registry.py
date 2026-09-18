import os
import subprocess

from source.utils.config import Config
from source.utils.platform import IS_WINDOWS, hidden_subprocess_kwargs
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
    def __init__(self):
        self.optimization_rules = {
            'disable_hibernation': self._disable_hibernation,
            'optimize_pagefile': self._optimize_pagefile,
            'optimize_performance': self._optimize_performance
        }

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
        if winreg is None:
            return None
        try:
            key = winreg.OpenKey(hive, sub_key, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, value_name)
            winreg.CloseKey(key)
            return value
        except OSError:
            return None
    
    def _set_registry_value(self, hive, sub_key, value_name, value, value_type=None):
        """
        Helper method to modify the Windows Registry safely.
        Creates the key path if it does not already exist.
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
                ["powercfg", "/hibernate", "off"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
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
        # wmic was removed from Windows 11 (24H2+); use PowerShell CIM instead,
        # with a wmic fallback for older systems where it still exists.
        commands = [
            [
                "powershell", "-NoProfile", "-NonInteractive", "-Command",
                "Get-CimInstance Win32_ComputerSystem | "
                "Set-CimInstance -Property @{AutomaticManagedPagefile=$true}",
            ],
            "wmic computersystem where name=\"%computername%\" "
            "set AutomaticManagedPagefile=True",
        ]
        last_error = None
        for cmd in commands:
            try:
                subprocess.run(
                    cmd,
                    shell=isinstance(cmd, str),
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    **hidden_subprocess_kwargs(),
                )
                return "Pagefile configuration optimized to automatic management"
            except Exception as e:
                last_error = e
        return f"Failed to optimize pagefile layout: {str(last_error)}"
    
    def _optimize_performance(self):
        """Apply native Windows registry performance adjustments for low visual latency"""
        if winreg is None:
            return "Skipped: registry tweaks are Windows-only"
        success_count = 0
        
        # Structure tweaks with explicit paths, names, values, and types
        tweaks = [
            # 1 = Adjust for best performance (disables heavy window animations, shadows, etc.)
            {
                'hive': winreg.HKEY_CURRENT_USER,
                'path': r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
                'name': "VisualFXSetting",
                'value': 1,
                'type': winreg.REG_DWORD
            },
            # Disables menu fade animations to make window opening snappier
            {
                'hive': winreg.HKEY_CURRENT_USER,
                'path': r"Control Panel\Desktop",
                'name': "UserPreferencesMask",
                'value': b'\x90\x12\x03\x80\x10\x00\x00\x00', # Hex byte sequence for disabled effects
                'type': winreg.REG_BINARY
            },
            # Lowering delay before menus hover/pop open (Default is 400ms, optimized to 10ms)
            {
                'hive': winreg.HKEY_CURRENT_USER,
                'path': r"Control Panel\Desktop",
                'name': "MenuShowDelay",
                'value': "10",
                'type': winreg.REG_SZ
            }
        ]
        
        for tweak in tweaks:
            res = self._set_registry_value(
                hive=tweak['hive'],
                sub_key=tweak['path'],
                value_name=tweak['name'],
                value=tweak['value'],
                value_type=tweak['type']
            )
            if res:
                success_count += 1

        if Config.DRY_RUN:
            return f"Would apply {success_count}/{len(tweaks)} performance registry tweaks (preview)"
        return f"Applied {success_count}/{len(tweaks)} performance registry tweaks"
    
    def apply_all(self):
        """Apply all system optimizations and aggregate responses cleanly for the UI status log"""
        summary_reports = []
        for name, func in self.optimization_rules.items():
            formatted_name = name.replace('_', ' ').title()
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
