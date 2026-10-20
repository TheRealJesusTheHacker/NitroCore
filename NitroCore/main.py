"""
NitroCore Windows System Optimizer - Primary Application Entry Point.
"""

import ctypes
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from source import __version__
from source.utils.config import Config
from source.utils.lifecycle import LifecycleManager
from source.utils.platform import IS_WINDOWS
from source.utils.restore_point import create_restore_point

# GUI imports (tkinter + source.gui.*) are deliberately deferred into
# _import_gui(), which run() calls only after the headless --dry-run path
# has returned. Importing tkinter and the widget modules costs a large
# share of startup time, and a read-only preview should not pay it. The
# names are bound as module globals before any GUI method can execute —
# every method that uses them is reachable only through run().


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def _quote_cmdline_arg(arg: str) -> str:
    """Quote one argument for a Windows command line (CommandLineToArgvW rules)."""
    if arg and not any(c in arg for c in ' \t"'):
        return arg
    parts = ['"']
    backslashes = 0
    for ch in arg:
        if ch == "\\":
            backslashes += 1
            continue
        if ch == '"':
            parts.append("\\" * (2 * backslashes + 1))
            parts.append('"')
        else:
            parts.append("\\" * backslashes)
            parts.append(ch)
        backslashes = 0
    parts.append("\\" * (2 * backslashes))
    parts.append('"')
    return "".join(parts)


def elevation_command() -> tuple:
    """(executable, parameter string) to re-run this program elevated.

    Frozen (PyInstaller): the executable is the .exe itself and only the
    user's arguments carry over. From source: the interpreter re-runs
    this file, so the file path leads the parameters.
    """
    args = list(sys.argv[1:])
    if getattr(sys, "frozen", False):
        params = args
    else:
        params = [os.path.abspath(__file__), *args]
    return sys.executable, " ".join(_quote_cmdline_arg(a) for a in params)


def _shell_execute_runas(executable: str, params: str, cwd: str) -> int:
    """ShellExecuteW with the "runas" verb; returns the raw result code."""
    return ctypes.windll.shell32.ShellExecuteW(
        None, "runas", executable, params, cwd, 1
    )


def relaunch_elevated() -> bool:
    """Re-start this program with administrator rights via the UAC prompt.

    Returns True when Windows accepted the request (the elevated copy
    takes over; this process should exit). False on non-Windows, when
    the user declines the prompt, or when the request fails — the
    caller then falls back to the Access Denied exit.
    """
    if not IS_WINDOWS:
        return False
    executable, params = elevation_command()
    try:
        result = _shell_execute_runas(executable, params, os.getcwd())
    except Exception:
        return False
    # ShellExecuteW returns a value greater than 32 on success.
    return result > 32


def ensure_admin_or_exit() -> None:
    """Admin gate: elevate in place, or exit with the Access Denied message.

    NitroCore ships with an asInvoker manifest so that ANY launcher can
    start it. A requireAdministrator manifest makes CreateProcess-based
    starters (the Technician's Toolkit launcher, task schedulers, other
    tools) fail with WinError 740 — "The requested operation requires
    elevation" — before the program runs at all (field report
    2026-10-20: NitroCore would not start from the Toolkit bundle while
    double-clicking the same .exe worked, because Explorer uses
    ShellExecute and can show the prompt). The elevation request
    therefore happens here instead: exactly one UAC prompt, raised by
    the program itself, and the program runs elevated exactly as
    before once the user accepts.
    """
    if is_admin():
        return
    if relaunch_elevated():
        sys.exit(0)
    # L-1: non-Windows-safe message path — ctypes.windll crashes on
    # Linux/macOS (MessageBoxW exists only on Windows).
    show_blocking_message(
        "Access Denied",
        "NitroCore requires Administrative Privileges to modify system registries.",
    )
    sys.exit(1)


def run_self_check() -> int:
    """--self-check: prove the program starts; change nothing.

    Headless and read-only; never needs elevation and never shows the
    admin gate. Prints one line and, when the environment variable
    NITROCORE_SELF_CHECK_OUT names a file, writes the same line there —
    a windowed build has no console for a caller to read, so the file
    is the machine-checkable proof. Exit code 0 means healthy.
    """
    line = f"NitroCore {__version__} self-check OK"
    try:
        print(line)
    except Exception:
        pass
    out_path = os.environ.get("NITROCORE_SELF_CHECK_OUT")
    if out_path:
        try:
            with open(out_path, "w", encoding="utf-8") as handle:
                handle.write(line + "\n")
        except OSError:
            return 1
    return 0


def show_blocking_message(title: str, text: str, icon: int = 0x10) -> None:
    """Show a blocking message box on Windows; print to stderr elsewhere."""
    if IS_WINDOWS:
        try:
            ctypes.windll.user32.MessageBoxW(0, text, title, icon)
            return
        except Exception:
            pass
    print(f"[{title}] {text}", file=sys.stderr)


def play_beep() -> None:
    """Best-effort system beep; silently ignored on non-Windows platforms."""
    if not IS_WINDOWS:
        return
    try:
        ctypes.windll.kernel32.Beep(800, 150)
    except Exception:
        pass


def _import_gui() -> None:
    """Bind the GUI modules as globals (see the note at the top of this file)."""
    global tk, theme, CustomButton, ConfirmDialog, RestoreFailedDialog
    global RestorePointDialog, FontEngine, CustomFrame, CustomLabel
    global TabbedInterface, Window
    import tkinter as tk

    from source.gui import theme
    from source.gui.button import CustomButton
    from source.gui.dialogs import (
        ConfirmDialog,
        RestoreFailedDialog,
        RestorePointDialog,
    )
    from source.gui.fonts import FontEngine
    from source.gui.frame import CustomFrame
    from source.gui.label import CustomLabel
    from source.gui.tabs import TabbedInterface
    from source.gui.window import Window


class NitroCoreApplication:
    """Manages the lifecycle, interface layout transitions, and Easter Egg states."""

    def __init__(self):
        self.app_window = None
        self.main_panel = None
        self.tabbed_ui = None
        # H-1: busy guard for the Pip-Boy purge button.
        self._pipboy_busy = False
        self._purge_btn = None

    def draw_dashboard(self):
        """Assembles the visible components based on the active config state."""
        if self.tabbed_ui:
            self.tabbed_ui.shutdown()
            self.tabbed_ui = None

        for widget in self.main_panel.canvas.winfo_children():
            widget.destroy()

        if Config.PI_BOY_MODE:
            bg_color = "#030803"
            fg_color = "#33ff33"
            self.app_window.canvas.configure(bg=bg_color)
            self.main_panel.canvas.configure(bg=bg_color)

            FontEngine.initialize()
            self._build_pipboy_layout(bg_color, fg_color)
        else:
            bg_color = theme.BG
            fg_color = theme.TEXT
            self.app_window.canvas.configure(bg=bg_color)
            self.main_panel.canvas.configure(bg=bg_color)
            FontEngine.initialize()
            self._build_tabbed_layout(bg_color, fg_color)

    def _build_tabbed_layout(self, bg_color: str, fg_color: str):
        self.tabbed_ui = TabbedInterface(
            parent=self.main_panel.canvas,
            root=self.app_window.canvas,
            bg_color=bg_color,
            fg_color=fg_color,
            on_title_click=self._handle_secret_clicks,
        )

    def _build_pipboy_layout(self, bg_color: str, fg_color: str):
        header_text = (
            " ___________________________________________________________________________\n"
            "|  [STAT]    > [INV] <   [DATA]    [MAP]    [RADIO]   |  KALI CORE v4.0.0   |\n"
            "|_____________________________________________________|_____________________|"
        )

        header_lbl = CustomLabel(
            self.main_panel.canvas, text=header_text, font=FontEngine.get("log")
        )
        header_lbl.configure(fg=fg_color, bg=bg_color, justify="left")
        header_lbl.pack(fill="x", pady=(0, 20))
        # L-9: a way back out — click the header to leave Pip-Boy mode.
        header_lbl.bind("<Button-1>", self._exit_pipboy)

        exit_hint = CustomLabel(
            self.main_panel.canvas,
            text="(click the header above to return to the normal interface)",
            font=FontEngine.get("small"),
        )
        exit_hint.configure(fg="#1a5c1a", bg=bg_color)
        exit_hint.pack(anchor="w")
        exit_hint.bind("<Button-1>", self._exit_pipboy)

        stats_box = CustomFrame(self.main_panel.canvas)
        stats_box.canvas.configure(bg=bg_color)
        stats_box.pack(fill="both", expand=True, pady=10)

        special_data = [
            (
                "S - STRENGTH",
                "10 [MAX]",
                ">> Carrying capacity optimized. Registry weight lifted.",
            ),
            (
                "P - PERCEPTION",
                "10 [MAX]",
                ">> File path scanning visibility at absolute maximum.",
            ),
            (
                "E - ENDURANCE",
                "10 [MAX]",
                ">> Process stamina verified. Handle exceptions absorbed.",
            ),
            (
                "C - CHARISMA",
                "10 [MAX]",
                ">> Network communication protocols fully persuasive.",
            ),
            (
                "I - INTELLIGENCE",
                "10 [MAX]",
                ">> Async worker thread memory allocation hyper-efficient.",
            ),
            (
                "A - AGILITY",
                "10 [MAX]",
                ">> UI update refresh latency dropped to zero ms.",
            ),
            (
                "L - LUCK",
                "10 [MAX]",
                ">> NullPointerErrors automatically avoided by fortune.",
            ),
        ]

        for stat, val, desc in special_data:
            row_text = f"{stat.ljust(16)} - {val}   {desc}"
            lbl = CustomLabel(
                stats_box.canvas, text=row_text, font=FontEngine.get("body")
            )
            lbl.configure(fg=fg_color, bg=bg_color, anchor="w")
            lbl.pack(fill="x", pady=4)

        purge_btn = CustomButton(
            parent=self.main_panel.canvas,
            text=">>>  [ INITIATE SYSTEM PURGE AND OVERCLOCK ]  <<<",
            command=self._run_pipboy_purge,
            font=FontEngine.get("button"),
        )
        purge_btn.configure(
            bg=bg_color,
            fg=fg_color,
            activebackground=fg_color,
            activeforeground=bg_color,
            bd=2,
            relief="solid",
        )
        purge_btn.pack(fill="x", ipady=12, pady=(20, 0))
        self._purge_btn = purge_btn

    def _exit_pipboy(self, event=None):
        """L-9: leave Pip-Boy mode and return to the normal interface."""
        Config.PI_BOY_MODE = False
        Config.CLICK_COUNTER = 0
        self.app_window.canvas.title(f"NitroCore Windows Optimizer v{__version__}")
        self.draw_dashboard()

    def _run_headless_preview(self):
        """Run the optimization pipeline in dry-run mode and print the report."""
        from types import SimpleNamespace

        from source.modules.disk_cleanup import DiskCleanup
        from source.modules.performance import PerformanceTuner
        from source.modules.registry import RegistryOptimizer
        from source.modules.services import ServiceManager
        from source.modules.temp_files import TempFileCleaner
        from source.utils.preview import PREVIEW_FOOTER, preview
        from source.utils.profiles import PROFILE_META, execute_step, get_pipeline

        modules = SimpleNamespace(
            registry=RegistryOptimizer(),
            temp_cleaner=TempFileCleaner(),
            disk_cleanup=DiskCleanup(),
            services=ServiceManager(),
            performance=PerformanceTuner(),
        )
        profile = Config.ACTIVE_PROFILE
        label = PROFILE_META[profile]["label"]
        pipboy = Config.PI_BOY_MODE

        def say(line=""):
            print(f">> {line}" if pipboy and line else line)

        preview.start()
        say(f"NitroCore dry run — {label} profile")
        say("=" * 60)
        for step_id, step_label in get_pipeline(profile):
            say(f"--- {step_label} ---")
            say(execute_step(step_id, profile, modules))
        entries = preview.report()
        say()
        say(f"{len(entries)} change(s) previewed, 0 applied")
        for index, entry in enumerate(entries, start=1):
            say(f"  {index}. {entry}")
        say(PREVIEW_FOOTER)

    def _run_pipboy_purge(self):
        """H-1: the Pip-Boy purge button is no longer a fire-and-forget
        destructive pipeline. It now requires explicit confirmation, offers a
        restore point, honors preview mode, and refuses to double-fire."""

        if self._pipboy_busy:
            print(
                ">> [VATS] Purge already in progress — hold your horses, vault dweller."
            )
            return

        proceed = ConfirmDialog.ask(
            self.app_window.canvas,
            title="Whoa there, vault dweller",
            message=(
                "That big red button runs the FULL NitroCore pipeline for real — "
                "registry tweaks, temp/cache cleanup, Windows Update and BITS "
                "service changes, power plan switch, the works.\n\n"
                "This isn't a toy. Still want to do this?"
            ),
            confirm_text="Purge it",
            cancel_text="Never mind",
            glyph="!",
            danger=True,
        )
        if not proceed:
            print(">> [VATS] Purge aborted. Probably wise.")
            return

        if Config.DRY_RUN:
            print(">> [VATS] PREVIEW MODE — purge simulated, nothing touched.")
            self._pipboy_run(preview_only=True)
            return

        self._pipboy_restore_prompt()

    def _pipboy_restore_prompt(self):
        choice = RestorePointDialog.ask(
            self.app_window.canvas,
            message=(
                "Heads up — the System Purge will change some Windows settings.\n\n"
                "Want me to create a restore point first, just in case?"
            ),
        )
        if choice == "cancel":
            print(">> [VATS] Purge aborted.")
            return
        if choice == "skip":
            self._pipboy_run()
            return

        print(">> [VATS] Creating restore point...")

        def task():
            return create_restore_point("NitroCore - Pip-Boy Purge")

        def on_complete(result):
            def ui():
                ok = bool(result) and result[0]
                msg = result[1] if result else "Restore point creation failed."
                print(f">> [VATS] {msg}")
                if not ok:
                    # M-1: failed restore point blocks the purge unless the
                    # user explicitly accepts the risk.
                    action = RestoreFailedDialog.ask(self.app_window.canvas, msg)
                    if action == "retry":
                        self._pipboy_restore_prompt()
                        return
                    if action == "abort":
                        print(">> [VATS] Purge aborted.")
                        return
                    print(">> [VATS] Continuing without a restore point. Bold.")
                self._pipboy_run()

            try:
                self.app_window.canvas.after(0, ui)
            except tk.TclError:
                pass

        from source.modules.async_worker import AsyncWorker

        AsyncWorker.run_task(task, on_complete)

    def _pipboy_run(self, preview_only: bool = False):
        from source.modules.async_worker import AsyncWorker
        from source.modules.disk_cleanup import DiskCleanup
        from source.modules.performance import PerformanceTuner
        from source.modules.registry import RegistryOptimizer
        from source.modules.services import ServiceManager
        from source.modules.temp_files import TempFileCleaner

        self._pipboy_busy = True
        if self._purge_btn is not None:
            self._purge_btn.set_enabled(False)

        if preview_only:
            from source.utils.preview import preview as _preview

            _preview.start()

        print(">> [VATS] STARTING SYSTEM RAD PURGE MULTIPLIER...")

        def task():
            registry = RegistryOptimizer()
            temp = TempFileCleaner()
            disk = DiskCleanup()
            services = ServiceManager()
            perf = PerformanceTuner()
            results = [
                ("Registry", registry.apply_all()),
                (
                    "Temp",
                    f"{temp.clean_temp_directories()}\n{temp.clean_browser_cache()}",
                ),
                ("Disk", disk.clean_system_files()),
                ("Services", services.optimize_all_services()),
                (
                    "Performance",
                    f"{perf.optimize_power_plan()}\n{perf.set_process_priority()}",
                ),
            ]
            for label, result in results:
                print(f">> [{label}]")
                print(result)
            if preview_only:
                from source.utils.preview import preview

                entries = preview.report()
                print(f">> [VATS] {len(entries)} change(s) previewed, 0 applied.")
                for index, entry in enumerate(entries, start=1):
                    print(f">>   {index}. {entry}")
            print(">> [VATS] PURGE COMPLETE")

        def on_complete(_result):
            def ui():
                self._pipboy_busy = False
                # The pipeline may have switched the power plan; drop the
                # cached value so the header re-queries instead of showing
                # the stale plan for up to 120s.
                try:
                    from source.modules.system_stats import (
                        invalidate_all_power_plan_caches,
                    )
                except ImportError:
                    pass
                else:
                    invalidate_all_power_plan_caches()
                try:
                    if self._purge_btn is not None and self._purge_btn.winfo_exists():
                        self._purge_btn.set_enabled(True)
                except tk.TclError:
                    pass

            try:
                self.app_window.canvas.after(0, ui)
            except tk.TclError:
                pass

        AsyncWorker.run_task(task, on_complete)

    def _handle_secret_clicks(self, event):
        Config.CLICK_COUNTER += 1
        if Config.CLICK_COUNTER >= 7:
            Config.PI_BOY_MODE = True
            Config.CLICK_COUNTER = 0  # L-9: reset so re-entry needs 7 fresh clicks
            play_beep()
            self.app_window.canvas.title("PIP-BOY 3000 - ROB-CO INDUSTRIES")
            self.draw_dashboard()

    def run(self):
        Config.parse_arguments()

        if Config.SELF_CHECK:
            # Headless health proof: no GUI, no admin gate, no changes.
            sys.exit(run_self_check())

        if Config.DRY_RUN:
            # Headless preview: print the report to stdout, change nothing.
            # Skips the admin gate and single-instance mutex — a read-only
            # preview should never fight the user for elevation.
            self._run_headless_preview()
            return

        _import_gui()

        ensure_admin_or_exit()

        LifecycleManager.enforce_single_instance()

        self.app_window = Window(
            title=f"NitroCore Windows Optimizer v{__version__}",
            width=980,
            height=780,
            resizable=False,
        )
        FontEngine.initialize()

        self.main_panel = CustomFrame(self.app_window.canvas, bg_color=theme.BG)
        self.main_panel.pack(fill="both", expand=True, padx=20, pady=12)

        self.draw_dashboard()
        self.app_window.add_close_callback(self._on_shutdown)
        self.app_window.show()

    def _on_shutdown(self):
        if self.tabbed_ui:
            self.tabbed_ui.shutdown()


if __name__ == "__main__":
    app = NitroCoreApplication()
    app.run()
