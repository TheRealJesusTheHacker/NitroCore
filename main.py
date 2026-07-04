#!/usr/bin/env python
"""NitroCore Windows System Optimizer - v1.1.0 Entry Point."""

import os
import sys
import ctypes
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from source.utils.config import Config
from source.utils.lifecycle import LifecycleManager
from source.gui.window import Window
from source.gui.fonts import FontEngine
from source.gui.frame import CustomFrame
from source.gui.button import CustomButton
from source.gui.label import CustomLabel
from source.gui.tabs import TabbedInterface

def is_admin() -> bool:
    """Check if running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

class NitroCoreApplication:
    """Main application class."""
    def __init__(self):
        self.app_window = None
        self.main_panel = None
        self.tabbed_ui = None

    def draw_dashboard(self):
        """Draw main UI."""
        if self.tabbed_ui:
            self.tabbed_ui.shutdown()
            self.tabbed_ui = None
        for widget in self.main_panel.canvas.winfo_children():
            widget.destroy()
        if Config.PI_BOY_MODE:
            self._build_pipboy_layout()
        else:
            self._build_tabbed_layout()

    def _build_tabbed_layout(self):
        """Build tabbed interface."""
        self.tabbed_ui = TabbedInterface(
            parent=self.main_panel.canvas,
            root=self.app_window.canvas,
            bg_color="#202225",
            fg_color="#F2F3F5",
            on_title_click=self._handle_secret_clicks,
        )

    def _build_pipboy_layout(self):
        """Build Pip-Boy easter egg."""
        from source.modules.registry import RegistryOptimizer
        from source.modules.temp_files import TempFileCleaner
        from source.modules.disk_cleanup import DiskCleanup
        from source.modules.services import ServiceManager
        from source.modules.performance import PerformanceTuner
        from source.modules.async_worker import AsyncWorker
        bg_color = "#030803"
        fg_color = "#33ff33"
        self.app_window.canvas.configure(bg=bg_color)
        self.main_panel.canvas.configure(bg=bg_color)
        FontEngine.initialize()
        header_text = " ___________________________________________________________________________\n|  [STAT]    > [INV] <   [DATA]    [MAP]    [RADIO]   |  KALI CORE v4.0.0   |\n|_____________________________________________________|_____________________|  "
        header_lbl = CustomLabel(self.main_panel.canvas, text=header_text, font=FontEngine.get("log"))
        header_lbl.configure(fg=fg_color, bg=bg_color, justify="left")
        header_lbl.pack(fill="x", pady=(0, 20))
        stats_box = CustomFrame(self.main_panel.canvas)
        stats_box.canvas.configure(bg=bg_color)
        stats_box.pack(fill="both", expand=True, pady=10)
        for stat, val, desc in [("S - STRENGTH", "10 [MAX]", ">> Carrying capacity optimized. Registry weight lifted."), ("P - PERCEPTION", "10 [MAX]", ">> File path scanning visibility at absolute maximum."), ("E - ENDURANCE", "10 [MAX]", ">> Process stamina verified. Handle exceptions absorbed."), ("C - CHARISMA", "10 [MAX]", ">> Network communication protocols fully persuasive."), ("I - INTELLIGENCE", "10 [MAX]", ">> Async worker thread memory allocation hyper-efficient."), ("A - AGILITY", "10 [MAX]", ">> UI update refresh latency dropped to zero ms."), ("L - LUCK", "10 [MAX]", ">> NullPointerErrors automatically avoided by fortune.")]:
            row_text = f"{stat.ljust(16)} - {val}   {desc}"
            lbl = CustomLabel(stats_box.canvas, text=row_text, font=FontEngine.get("body"))
            lbl.configure(fg=fg_color, bg=bg_color, anchor="w")
            lbl.pack(fill="x", pady=4)
        purge_btn = CustomButton(
            parent=self.main_panel.canvas,
            text=">>>  [ INITIATE SYSTEM PURGE AND OVERCLOCK ]  <<<",
            command=self._run_pipboy_purge,
            font=FontEngine.get("button"),
        )
        purge_btn.configure(bg=bg_color, fg=fg_color, activebackground=fg_color, activeforeground=bg_color, bd=2, relief="solid")
        purge_btn.pack(fill="x", ipady=12, pady=(20, 0))

    def _run_pipboy_purge(self):
        """Run all modules in Pip-Boy mode."""
        from source.modules.registry import RegistryOptimizer
        from source.modules.temp_files import TempFileCleaner
        from source.modules.disk_cleanup import DiskCleanup
        from source.modules.services import ServiceManager
        from source.modules.performance import PerformanceTuner
        from source.modules.async_worker import AsyncWorker
        print(">> [VATS] STARTING SYSTEM RAD PURGE MULTIPLIER...")
        def task():
            registry = RegistryOptimizer()
            temp = TempFileCleaner()
            disk = DiskCleanup()
            services = ServiceManager()
            perf = PerformanceTuner()
            results = [("Registry", registry.apply_all()), ("Temp", f"{temp.clean_temp_directories()}\n{temp.clean_browser_cache()}"), ("Disk", disk.clean_system_files()), ("Services", services.optimize_all_services()), ("Performance", f"{perf.optimize_power_plan()}\n{perf.set_process_priority()}")]
            for label, result in results:
                print(f">> [{label}]")
                print(result)
            print(">> [VATS] PURGE COMPLETE")
        AsyncWorker.run_task(task)

    def _handle_secret_clicks(self, event):
        """Easter egg: click 7 times on title."""
        Config.CLICK_COUNTER += 1
        if Config.CLICK_COUNTER >= 7:
            Config.PI_BOY_MODE = True
            ctypes.windll.kernel32.Beep(800, 150)
            self.app_window.canvas.title("PIP-BOY 3000 - ROB-CO INDUSTRIES")
            self.draw_dashboard()

    def run(self):
        """Main entry point."""
        Config.parse_arguments()
        if not is_admin():
            ctypes.windll.user32.MessageBoxW(0, "NitroCore requires Admin privileges.", "Access Denied", 0x10 | 0x0)
            sys.exit(0)
        LifecycleManager.enforce_single_instance()
        self.app_window = Window(title="NitroCore v1.1.0", width=980, height=780, resizable=False)
        FontEngine.initialize()
        self.main_panel = CustomFrame(self.app_window.canvas)
        self.main_panel.pack(fill="both", expand=True, padx=20, pady=16)
        self.draw_dashboard()
        self.app_window.add_close_callback(self._on_shutdown)
        self.app_window.show()

    def _on_shutdown(self):
        """Cleanup on exit."""
        if self.tabbed_ui:
            self.tabbed_ui.shutdown()

def main():
    """CLI + GUI entry point."""
    parser = argparse.ArgumentParser(description="NitroCore v1.1.0 - Windows System Optimizer", formatter_class=argparse.RawDescriptionHelpFormatter, epilog="Examples:\n  python main.py\n  python main.py --cli --module registry\n  python main.py --cli --profile cybersecurity --dry-run")
    parser.add_argument("--cli", action="store_true", help="CLI mode")
    parser.add_argument("--module", choices=["registry", "temp", "disk", "services", "performance"], help="Specific module")
    parser.add_argument("--profile", choices=["gaming", "cybersecurity"], default="gaming", help="Profile")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run mode")
    args = parser.parse_args()
    if args.cli:
        if not is_admin():
            print("[ERROR] CLI requires admin.")
            sys.exit(1)
        print(f"[INFO] NitroCore v1.1.0 CLI ({args.profile} profile)")
        if args.dry_run:
            print("[INFO] DRY-RUN MODE")
    else:
        app = NitroCoreApplication()
        app.run()

if __name__ == "__main__":
    main()
