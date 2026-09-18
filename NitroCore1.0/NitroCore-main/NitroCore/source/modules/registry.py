import os
import subprocess

from source.utils.platform import IS_WINDOWS, hidden_subprocess_kwargs

try:
    import winreg
except ImportError:  # Non-Windows platform: registry methods degrade gracefully
    winreg = None

from source.utils.profiles import GAMING

class RegistryOptimizer:
    def __init__(self):
        self.optimization_rules = {
            'disable_hibernation': self._disable_hibernation,
            'optimize_pagefile': self._optimize_pagefile,
            'optimize_performance': self._optimize_performance
        }
    
    def _set_registry_value(self, hive, sub_key, value_name, value, value_type=None):
        """
        Helper method to modify the Windows Registry safely.
        Creates the key path if it does not already exist.
        """
        if winreg is None:
            return False
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
        try:
            # Modifies the system memory management layout via standard WMI command line
            cmd = "wmic computersystem where name=\"%computername%\" set AutomaticManagedPagefile=True"
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
