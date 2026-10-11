"""Tabbed interface for NitroCore optimization modules."""

import re
import time
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext
from typing import Callable, Dict, List, Optional, Tuple

from source.gui import theme
from source.gui.button import CustomButton
from source.gui.dialogs import (
    ConfirmDialog,
    PreviewReportDialog,
    RestoreFailedDialog,
    RestorePointDialog,
)
from source.gui.fonts import FontEngine
from source.gui.frame import CustomFrame
from source.gui.label import CustomLabel
from source.gui.profile_selector import ProfileSelector
from source.gui.progress_panel import ProgressPanel
from source.gui.stats_header import StatsHeader
from source.modules.async_worker import AsyncWorker
from source.modules.disk_cleanup import DiskCleanup
from source.modules.performance import PerformanceTuner
from source.modules.registry import RegistryOptimizer
from source.modules.services import ServiceManager
from source.modules.temp_files import TempFileCleaner
from source.utils.config import Config
from source.utils.logger import Logger
from source.utils.preview import preview
from source.utils.profiles import (
    PROFILE_META,
    execute_step,
    get_pipeline,
)
from source.utils.restore_point import create_restore_point


class TabbedInterface:
    """Multi-tab dashboard wiring each optimization module to its own panel."""

    TAB_DEFS: List[Tuple[str, str]] = [
        ("registry", "Registry"),
        ("temp_files", "Temp Files"),
        ("disk", "Disk Cleanup"),
        ("services", "Services"),
        ("performance", "Performance"),
        ("status", "Status"),
    ]

    def __init__(
        self,
        parent: tk.Widget,
        root: tk.Tk,
        bg_color: str = theme.BG,
        panel_color: str = theme.CARD,
        fg_color: str = theme.TEXT,
        muted_color: str = theme.MUTED,
        accent_color: str = "#FF6B35",
        on_title_click=None,
    ):
        self.parent = parent
        self.root = root
        self.bg_color = bg_color
        self.panel_color = panel_color
        self.fg_color = fg_color
        self.muted_color = muted_color
        self.accent_color = accent_color
        self.on_title_click = on_title_click

        self.logger = Logger.get_logger("nitrocore")
        self._active_tab = "registry"
        self._tab_buttons: Dict[str, CustomButton] = {}
        self._tab_panels: Dict[str, CustomFrame] = {}
        self._action_buttons: List[CustomButton] = []
        self._busy = False
        self._run_start_time = 0.0
        self._mb_freed = 0.0
        self._steps_completed = 0

        self.registry = RegistryOptimizer()
        self.temp_cleaner = TempFileCleaner()
        self.disk_cleanup = DiskCleanup()
        self.services = ServiceManager()
        self.performance = PerformanceTuner()
        self._modules = self

        self.stats_header: Optional[StatsHeader] = None
        self.profile_selector: Optional[ProfileSelector] = None
        self.progress_panel: Optional[ProgressPanel] = None
        self.run_all_btn: Optional[CustomButton] = None

        self._apply_profile_accent(Config.ACTIVE_PROFILE)
        self._build_shell()
        self._show_tab("registry")

    def _apply_profile_accent(self, profile: str) -> None:
        self.accent_color = PROFILE_META[profile]["accent"]

    def _on_profile_changed(self, profile: str) -> None:
        self._apply_profile_accent(profile)
        if self.stats_header:
            self.stats_header.accent_color = self.accent_color
        if hasattr(self, "_logo"):
            self._draw_logo()
        if hasattr(self, "preview_check"):
            self.preview_check.set_accent(self.accent_color)
        if self.run_all_btn:
            self.run_all_btn.configure(
                bg=self.accent_color, activebackground=self._darken_accent()
            )
            self.run_all_btn.label.configure(
                text=f"Run All ({PROFILE_META[profile]['label']})"
            )
        for btn in self._tab_buttons.values():
            btn.configure(activebackground=self.accent_color)
        for btn in self._action_buttons:
            if btn is not self.run_all_btn:
                btn.configure(activebackground=self.accent_color)
        if self.progress_panel:
            self.progress_panel.set_accent(self.accent_color)
        if self.stats_header:
            for lbl in self.stats_header._value_labels.values():
                lbl.configure(fg=self.accent_color)
        self._show_tab(self._active_tab)
        self._append_log(
            f"Profile switched to {PROFILE_META[profile]['label']}.", "info"
        )

    def _darken_accent(self) -> str:
        return theme.darken(self.accent_color, 0.8)

    def _draw_logo(self) -> None:
        """Paint the accent brand mark (called again on profile accent swaps)."""
        logo = self._logo
        logo.delete("all")
        theme.rounded_rect(logo, 2, 2, 38, 38, 10, fill=self.accent_color, outline="")
        logo.create_text(
            20, 21, text="N", font=FontEngine.get("display"), fill="#FFFFFF"
        )

    def _build_brand_header(self) -> None:
        header = tk.Frame(self.parent, bg=self.bg_color)
        header.pack(fill="x", pady=(0, theme.PAD_SM))

        brand = tk.Frame(header, bg=self.bg_color)
        brand.pack(side="left")

        self._logo = tk.Canvas(
            brand, width=40, height=40, bg=self.bg_color, highlightthickness=0, bd=0
        )
        self._logo.pack(side="left")
        self._draw_logo()

        title_col = tk.Frame(brand, bg=self.bg_color)
        title_col.pack(side="left", padx=(theme.PAD_MD, 0))

        title_lbl = CustomLabel(
            parent=title_col,
            text="NitroCore",
            font=FontEngine.get("display"),
            bg=self.bg_color,
            fg=self.fg_color,
        )
        title_lbl.pack(anchor="w")

        tagline_lbl = CustomLabel(
            parent=title_col,
            text="WINDOWS SYSTEM OPTIMIZER",
            font=FontEngine.get("caption"),
            bg=self.bg_color,
            fg=self.muted_color,
        )
        tagline_lbl.pack(anchor="w")

        if self.on_title_click:
            title_lbl.bind("<Button-1>", self.on_title_click)
            self._logo.bind("<Button-1>", self.on_title_click)

        # Preview toggle, right-aligned.
        right = tk.Frame(header, bg=self.bg_color)
        right.pack(side="right")

        toggle_text = tk.Frame(right, bg=self.bg_color)
        toggle_text.pack(side="left", padx=(0, theme.PAD_MD))

        CustomLabel(
            parent=toggle_text,
            text="Preview only",
            font=FontEngine.get("body"),
            bg=self.bg_color,
            fg=self.fg_color,
        ).pack(anchor="e")
        CustomLabel(
            parent=toggle_text,
            text="See what would change \u2014 nothing gets touched",
            font=FontEngine.get("small"),
            bg=self.bg_color,
            fg=self.muted_color,
        ).pack(anchor="e")

        self.preview_var = tk.BooleanVar(value=Config.DRY_RUN)
        self.preview_check = theme.ToggleSwitch(
            right,
            self.preview_var,
            command=self._on_preview_toggled,
            bg=self.bg_color,
            accent=self.accent_color,
        )
        self.preview_check.pack(side="left")

    def _build_shell(self) -> None:
        self._build_brand_header()

        subtitle = CustomLabel(
            parent=self.parent,
            text="Tune Windows for gaming or security work \u2014 safely, step by step.",
            font=FontEngine.get("body"),
            bg=self.bg_color,
            fg=self.muted_color,
        )
        subtitle.pack(anchor="w", pady=(0, theme.PAD_MD))

        self.stats_header = StatsHeader(
            parent=self.parent,
            root=self.root,
            bg_color=self.bg_color,
            card_color=self.panel_color,
            fg_color=self.fg_color,
            muted_color=self.muted_color,
            accent_color=self.accent_color,
        )

        self.profile_selector = ProfileSelector(
            parent=self.parent,
            on_change=self._on_profile_changed,
            bg_color=self.bg_color,
            card_color=self.panel_color,
            fg_color=self.fg_color,
            muted_color=self.muted_color,
        )

        self.progress_panel = ProgressPanel(
            parent=self.parent,
            root=self.root,
            bg_color=self.bg_color,
            fg_color=self.fg_color,
            muted_color=self.muted_color,
            accent_color=self.accent_color,
        )

        tab_bar = tk.Frame(self.parent, bg=self.bg_color)
        tab_bar.pack(fill="x", pady=(0, theme.PAD_SM))

        for tab_id, tab_label in self.TAB_DEFS:
            btn = CustomButton(
                parent=tab_bar,
                text=tab_label,
                command=lambda tid=tab_id: self._show_tab(tid),
                font=FontEngine.get("body"),
                bg=self.panel_color,
                fg=self.muted_color,
                activebackground=self.accent_color,
                activeforeground="#FFFFFF",
                corner_radius=theme.RADIUS_MD,
            )
            btn.pack(side="left", padx=(0, theme.PAD_XS))
            self._tab_buttons[tab_id] = btn

        self.run_all_btn = CustomButton(
            parent=tab_bar,
            text=f"Run All ({PROFILE_META[Config.ACTIVE_PROFILE]['label']})",
            command=self._run_all_optimizations,
            font=FontEngine.get("button"),
            bg=self.accent_color,
            fg="#FFFFFF",
            activebackground=self._darken_accent(),
            activeforeground="#FFFFFF",
            corner_radius=theme.RADIUS_MD,
            padx=18,
        )
        self.run_all_btn.pack(side="right")
        self._action_buttons.append(self.run_all_btn)

        self.content_area = CustomFrame(
            self.parent,
            bg_color=self.panel_color,
            border_color=theme.BORDER_SOFT,
        )
        self.content_area.pack(fill="both", expand=True)

        self._build_registry_tab()
        self._build_temp_files_tab()
        self._build_disk_tab()
        self._build_services_tab()
        self._build_performance_tab()
        self._build_status_tab()

    def _make_tab_panel(self, tab_id: str) -> CustomFrame:
        panel = CustomFrame(self.content_area.canvas, bg_color=self.panel_color)
        self._tab_panels[tab_id] = panel
        return panel

    def _add_tab_header(
        self, panel: CustomFrame, title: str, description: str, risk: str = "Medium"
    ) -> None:
        title_row = tk.Frame(panel.canvas, bg=self.panel_color)
        title_row.pack(
            anchor="w", fill="x", padx=theme.PAD_LG, pady=(theme.PAD_LG, theme.PAD_SM)
        )

        title_lbl = CustomLabel(
            parent=title_row,
            text=title,
            font=FontEngine.get("header"),
            bg=self.panel_color,
            fg=self.fg_color,
        )
        title_lbl.pack(side="left")

        risk_color = theme.RISK_COLORS.get(risk, self.muted_color)
        risk_badge = theme.Badge(
            title_row,
            text=f"{risk} risk",
            fg=risk_color,
            bg=self.panel_color,
            font=FontEngine.get("small"),
        )
        risk_badge.pack(side="left", padx=(theme.PAD_MD, 0))

        desc_lbl = CustomLabel(
            parent=panel.canvas,
            text=description,
            font=FontEngine.get("body"),
            bg=self.panel_color,
            fg=self.muted_color,
        )
        desc_lbl.configure(justify="left", anchor="w", wraplength=880)
        desc_lbl.pack(anchor="w", padx=theme.PAD_LG, pady=(0, theme.PAD_LG))

    def _add_action_button(
        self,
        panel: CustomFrame,
        text: str,
        command: Callable[[], None],
    ) -> CustomButton:
        btn = CustomButton(
            parent=panel.canvas,
            text=text,
            command=command,
            font=FontEngine.get("button"),
            bg=theme.BTN_SECONDARY_BG,
            fg=self.fg_color,
            activebackground=self.accent_color,
            activeforeground="#FFFFFF",
            corner_radius=theme.RADIUS_MD,
            anchor="w",
            padx=theme.PAD_LG,
            pady=10,
            border_color=theme.BORDER,
        )
        btn.pack(fill="x", padx=theme.PAD_LG, pady=(0, theme.PAD_SM))
        self._action_buttons.append(btn)
        return btn

    def _build_registry_tab(self) -> None:
        panel = self._make_tab_panel("registry")
        self._add_tab_header(
            panel,
            "Registry Optimization",
            "Disables hibernation, tunes pagefile, and applies visual performance tweaks. "
            "Gaming profile applies all; Cybersecurity profile applies visual tweaks only.",
            risk="High",
        )
        self._add_action_button(
            panel, "Apply Registry Optimizations", self._run_registry
        )
        self._add_action_button(
            panel, "Restore Previous Registry Values", self._run_registry_undo
        )

    def _build_temp_files_tab(self) -> None:
        panel = self._make_tab_panel("temp_files")
        self._add_tab_header(
            panel,
            "Temporary File Cleanup",
            "Clear out system temp files and browser caches to free up disk space.",
            risk="Low",
        )
        self._add_action_button(panel, "Clean System Temp Files", self._run_temp_dirs)
        self._add_action_button(panel, "Clean Browser Cache", self._run_browser_cache)
        self._add_action_button(panel, "Clean All Temp & Cache", self._run_temp_all)

    def _build_disk_tab(self) -> None:
        panel = self._make_tab_panel("disk")
        self._add_tab_header(
            panel,
            "Disk Cleanup",
            "See what's eating your disk space, then clean it up safely.",
            risk="Medium",
        )

        self.disk_usage_lbl = CustomLabel(
            parent=panel.canvas,
            text="",
            font=FontEngine.get("log"),
            bg=self.panel_color,
            fg=self.fg_color,
        )
        self.disk_usage_lbl.configure(justify="left", anchor="w")
        self.disk_usage_lbl.pack(anchor="w", padx=16, pady=(0, 16))

        self._add_action_button(panel, "Refresh Disk Usage", self._refresh_disk_usage)
        self._add_action_button(
            panel, "Run Windows Disk Cleanup", self._run_disk_system
        )
        self._add_action_button(
            panel, "Clean Old Downloads (30+ days)", self._run_disk_downloads
        )

    def _build_services_tab(self) -> None:
        panel = self._make_tab_panel("services")
        self._add_tab_header(
            panel,
            "Service Management",
            "Gaming: stops Update, BITS, and Search. Cybersecurity: stops Search only "
            "to keep patching active.",
            risk="High",
        )
        self._add_action_button(
            panel, "Optimize Background Services", self._run_services
        )

    def _build_performance_tab(self) -> None:
        panel = self._make_tab_panel("performance")
        self._add_tab_header(
            panel,
            "Performance Tuning",
            "Switches to Ultimate/High Performance power plan and raises shell process priority.",
            risk="Low",
        )
        self._add_action_button(panel, "Apply Power Plan", self._run_power_plan)
        self._add_action_button(
            panel, "Tune Process Priority", self._run_process_priority
        )
        self._add_action_button(
            panel, "Apply All Performance Tweaks", self._run_performance_all
        )

    def _build_status_tab(self) -> None:
        panel = self._make_tab_panel("status")
        self._add_tab_header(
            panel,
            "Status & Logs",
            "Watch every step as it runs. Full logs are saved to "
            "AppData\\NitroCore\\logs.",
            risk="Low",
        )

        log_frame = tk.Frame(
            panel.canvas,
            bg=theme.BG_SUNKEN,
            highlightthickness=1,
            highlightbackground=theme.BORDER_SOFT,
            padx=2,
            pady=2,
        )
        log_frame.pack(
            fill="both", expand=True, padx=theme.PAD_LG, pady=(0, theme.PAD_SM)
        )

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=FontEngine.get("log"),
            bg=theme.BG_SUNKEN,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            relief="flat",
            wrap="word",
            state="disabled",
            height=12,
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.tag_config("success", foreground=theme.SUCCESS)
        self.log_text.tag_config("warning", foreground=theme.WARNING)
        self.log_text.tag_config("error", foreground=theme.ERROR)
        self.log_text.tag_config("info", foreground=theme.INFO)

        btn_row = tk.Frame(panel.canvas, bg=self.panel_color)
        btn_row.pack(fill="x", padx=theme.PAD_LG, pady=(0, theme.PAD_LG))

        clear_btn = CustomButton(
            parent=btn_row,
            text="Clear Log",
            command=self._clear_log,
            font=FontEngine.get("body"),
            bg=theme.BTN_SECONDARY_BG,
            fg=self.fg_color,
            activebackground=self.accent_color,
            activeforeground="#FFFFFF",
            corner_radius=theme.RADIUS_MD,
            border_color=theme.BORDER,
        )
        clear_btn.pack(side="left")

        self._append_log(
            "Welcome to NitroCore \u2014 pick a profile above, then run an "
            "optimization. Every step will show up here.",
            "info",
        )

    def _show_tab(self, tab_id: str) -> None:
        self._active_tab = tab_id
        for panel in self._tab_panels.values():
            panel.canvas.pack_forget()

        self._tab_panels[tab_id].pack(fill="both", expand=True)

        for tid, btn in self._tab_buttons.items():
            if tid == tab_id:
                btn.configure(bg=self.accent_color, fg="#FFFFFF")
            else:
                btn.configure(bg=self.panel_color, fg=self.muted_color)

        if tab_id == "disk":
            self._refresh_disk_usage()

    def _classify_log(self, message: str) -> str:
        lower = message.lower()
        if any(w in lower for w in ("error", "failed", "denied", "rejected")):
            return "error"
        if any(w in lower for w in ("warning", "skipped", "timeout", "timed out")):
            return "warning"
        if any(
            w in lower
            for w in ("success", "complete", "freed", "applied", "switched", "stopped")
        ):
            return "success"
        return "info"

    def _append_log(self, message: str, level: Optional[str] = None) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        tag = level or self._classify_log(message)
        line = f"[{timestamp}] {message}\n"
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line, tag)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.logger.info(message)

    def _parse_mb_freed(self, text: str) -> None:
        for match in re.finditer(r"(\d+\.?\d*)\s*MB freed", text, re.IGNORECASE):
            self._mb_freed += float(match.group(1))

    def _clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        for btn in self._action_buttons:
            btn.set_enabled(not busy)
        if hasattr(self, "preview_check"):
            self.preview_check.configure(state="disabled" if busy else "normal")

    def _safe_after(self, ms: int, func: Callable[[], None]) -> None:
        """Schedule func on the UI thread; silently no-op if the window is
        already gone (L-5 — worker callbacks racing teardown)."""
        try:
            if self.root.winfo_exists():
                self.root.after(ms, func)
        except tk.TclError:
            pass

    def _create_restore_then(
        self, action_label: str, continuation: Callable[[], None]
    ) -> None:
        """Create a restore point asynchronously, then run continuation."""
        self._append_log("Creating system restore point...", "info")
        self._set_busy(True)
        self.progress_panel.start("Creating restore point...", total_steps=1)

        def task() -> tuple[bool, str]:
            return create_restore_point(f"NitroCore - {action_label}")

        def on_complete(result: Optional[tuple[bool, str]]) -> None:
            def update() -> None:
                ok = bool(result) and result[0]
                reason = result[1] if result else "Restore point creation failed."
                self._append_log(reason, "success" if ok else "warning")
                self.progress_panel.reset()
                self._set_busy(False)
                if ok:
                    continuation()
                    return
                # M-1: a failed restore point BLOCKS the pipeline. Ask the
                # user whether to retry, continue without the safety net,
                # or abort — never silently proceed.
                action = RestoreFailedDialog.ask(self.root, reason)
                if action == "retry":
                    self._create_restore_then(action_label, continuation)
                elif action == "continue":
                    self._append_log(
                        "Continuing without a restore point — no safety net.",
                        "warning",
                    )
                    continuation()
                else:
                    self._append_log(
                        f"Aborted: {action_label} (no restore point)", "warning"
                    )

            self._safe_after(0, update)

        AsyncWorker.run_task(task, on_complete)

    def _on_preview_toggled(self) -> None:
        Config.DRY_RUN = bool(self.preview_var.get())
        if Config.DRY_RUN:
            self._append_log(
                "Preview mode on \u2014 runs will show what would change, nothing else.",
                "info",
            )
        else:
            self._append_log("Preview mode off \u2014 runs will apply changes.", "info")

    def _show_preview_report(self) -> None:
        entries = preview.report()
        self._append_log(
            f"Preview complete: {len(entries)} change(s) previewed, 0 applied.",
            "info",
        )
        PreviewReportDialog.show(self.root, entries)

    def _prompt_restore(
        self, action_label: str, continuation: Callable[[], None]
    ) -> None:
        if Config.DRY_RUN:
            self._append_log("Preview mode: skipping restore point prompt.", "info")
            continuation()
            return
        choice = RestorePointDialog.ask(
            self.root,
            message=(
                f"Heads up \u2014 {action_label} will change some Windows settings.\n\n"
                "Want me to create a restore point first, just in case?"
            ),
        )
        if choice == "cancel":
            self._append_log(f"Cancelled: {action_label}", "warning")
            return
        if choice == "create":
            self._create_restore_then(action_label, continuation)
        else:
            continuation()

    def _execute_async(self, label: str, task: Callable[[], str]) -> None:
        self._run_start_time = time.time()
        self._mb_freed = 0.0
        preview.start()
        self._append_log(f"Starting: {label}", "info")
        self._set_busy(True)
        self.progress_panel.start(label, total_steps=1)

        def on_complete(result: Optional[str]) -> None:
            def update_ui() -> None:
                elapsed = time.time() - self._run_start_time
                self._set_busy(False)
                if result is None:
                    self._append_log(f"Failed: {label}", "error")
                    self.progress_panel.fail(f"{label} failed.")
                else:
                    self._parse_mb_freed(result)
                    for line in result.splitlines():
                        self._append_log(line)
                    summary = f"Done in {elapsed:.1f}s"
                    if self._mb_freed > 0:
                        summary += f" · {self._mb_freed:.2f} MB freed"
                    self.progress_panel.finish(summary)
                self._mb_freed = 0.0
                if Config.DRY_RUN and result is not None:
                    self._show_preview_report()

            self._safe_after(0, update_ui)

        AsyncWorker.run_task(task, on_complete)

    def _run_async(
        self, label: str, task: Callable[[], str], require_restore: bool = False
    ) -> None:
        if self._busy:
            return
        if require_restore:
            self._prompt_restore(label, lambda: self._execute_async(label, task))
        else:
            self._execute_async(label, task)

    def _run_registry(self) -> None:
        profile = Config.ACTIVE_PROFILE
        self._run_async(
            "Registry Optimization",
            lambda: self.registry.apply_for_profile(profile),
            require_restore=True,
        )

    def _run_registry_undo(self) -> None:
        # M-4: one-click restore of the previous registry snapshot.
        self._run_async("Registry Undo", self.registry.restore_last_undo)

    def _run_temp_dirs(self) -> None:
        self._run_async("System Temp Cleanup", self.temp_cleaner.clean_temp_directories)

    def _run_browser_cache(self) -> None:
        self._run_async("Browser Cache Cleanup", self.temp_cleaner.clean_browser_cache)

    def _run_temp_all(self) -> None:
        def task() -> str:
            temp = self.temp_cleaner.clean_temp_directories()
            cache = self.temp_cleaner.clean_browser_cache()
            return f"{temp}\n{cache}"

        self._run_async("Temp & Cache Cleanup", task)

    def _refresh_disk_usage(self) -> None:
        usage = self.disk_cleanup.get_disk_usage()
        if not usage:
            self.disk_usage_lbl.configure(
                text="No fixed drives found \u2014 nothing to show here yet."
            )
            return

        lines = ["Drive Usage:"]
        for device, stats in usage.items():
            bar_len = 20
            filled = int(bar_len * stats["percent"] / 100)
            bar = "█" * filled + "░" * (bar_len - filled)
            lines.append(
                f"  {device}  [{bar}]  {stats['used_gb']}/{stats['total_gb']} GB  "
                f"({stats['free_gb']} GB free)"
            )
        self.disk_usage_lbl.configure(text="\n".join(lines))

    def _run_disk_system(self) -> None:
        self._run_async(
            "Windows Disk Cleanup",
            self.disk_cleanup.clean_system_files,
            require_restore=True,
        )

    def _run_disk_downloads(self) -> None:
        # H-2: explicit confirmation before touching user files, then the
        # normal restore-point prompt. Deleted files go to the Recycle Bin
        # (see DiskCleanup.clean_downloads), so this is recoverable.
        if self._busy:
            return
        proceed = ConfirmDialog.ask(
            self.root,
            title="Clean old Downloads?",
            message=(
                "This moves files in your Downloads folder that haven't been "
                "touched in 30+ days to the Recycle Bin.\n\n"
                "They stay recoverable from the Recycle Bin — but please make "
                "sure there's nothing in there you still need first."
            ),
            confirm_text="Move to Recycle Bin",
            cancel_text="Keep My Files",
            glyph="!",
            danger=True,
        )
        if not proceed:
            self._append_log("Cancelled: Downloads Cleanup", "warning")
            return
        self._prompt_restore(
            "Downloads Cleanup",
            lambda: self._execute_async(
                "Downloads Cleanup", self.disk_cleanup.clean_downloads
            ),
        )

    def _run_services(self) -> None:
        profile = Config.ACTIVE_PROFILE
        self._run_async(
            "Service Optimization",
            lambda: self.services.optimize_for_profile(profile),
            require_restore=True,
        )

    def _run_power_plan(self) -> None:
        self._run_async("Power Plan", self.performance.optimize_power_plan)

    def _run_process_priority(self) -> None:
        self._run_async("Process Priority", self.performance.set_process_priority)

    def _run_performance_all(self) -> None:
        def task() -> str:
            power = self.performance.optimize_power_plan()
            proc = self.performance.set_process_priority()
            return f"{power}\n{proc}"

        self._run_async("Performance Tuning", task)

    def _start_pipeline(self) -> None:
        profile = Config.ACTIVE_PROFILE
        profile_label = PROFILE_META[profile]["label"]
        pipeline = get_pipeline(profile)
        self._show_tab("status")
        self._append_log(
            f"=== Running {profile_label} optimization pipeline ===", "info"
        )
        self._set_busy(True)
        self._run_start_time = time.time()
        self._mb_freed = 0.0
        self._steps_completed = 0
        preview.start()
        self.progress_panel.start(
            f"{profile_label} pipeline", total_steps=len(pipeline)
        )

        def run_steps(index: int = 0) -> None:
            if index >= len(pipeline):

                def finish() -> None:
                    elapsed = time.time() - self._run_start_time
                    self._set_busy(False)
                    self._refresh_disk_usage()
                    summary = f"{self._steps_completed} modules · {elapsed:.1f}s" + (
                        f" · {self._mb_freed:.2f} MB freed" if self._mb_freed else ""
                    )
                    self.progress_panel.finish(summary)
                    self._append_log(
                        f"=== {profile_label} optimization complete ===", "success"
                    )
                    self._mb_freed = 0.0
                    if Config.DRY_RUN:
                        self._show_preview_report()

                self._safe_after(0, finish)
                return

            step_id, step_label = pipeline[index]
            self._safe_after(
                0,
                lambda i=index, sl=step_label: self.progress_panel.set_step(i + 1, sl),
            )

            def task() -> str:
                return execute_step(step_id, profile, self._modules)

            def on_complete(result: Optional[str]) -> None:
                def update_ui() -> None:
                    self._append_log(f"--- {step_label} ---", "info")
                    if result is None:
                        self._append_log(f"Failed: {step_label}", "error")
                    else:
                        self._steps_completed += 1
                        self._parse_mb_freed(result)
                        for line in result.splitlines():
                            self._append_log(line)
                    run_steps(index + 1)

                self._safe_after(0, update_ui)

            AsyncWorker.run_task(task, on_complete)

        run_steps(0)

    def _run_all_optimizations(self) -> None:
        if self._busy:
            return
        profile_label = PROFILE_META[Config.ACTIVE_PROFILE]["label"]
        self._prompt_restore(f"Run All ({profile_label})", self._start_pipeline)

    def shutdown(self) -> None:
        if self.stats_header:
            self.stats_header.stop()
