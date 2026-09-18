"""Progress bar and operation status panel."""

import tkinter as tk
import tkinter.ttk as ttk

from source.gui.label import CustomLabel
from source.gui.fonts import FontEngine


class ProgressPanel:
    """Shows step label, progress bar, and completion summary."""

    def __init__(
        self,
        parent: tk.Widget,
        root: tk.Tk,
        bg_color: str = "#202225",
        fg_color: str = "#F2F3F5",
        muted_color: str = "#B9BBBE",
        accent_color: str = "#FF6B35",
    ):
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.muted_color = muted_color
        self.accent_color = accent_color
        self._total_steps = 1
        self.root = root

        self.frame = tk.Frame(parent, bg=bg_color)
        self.frame.pack(fill="x", pady=(0, 8))

        self.status_lbl = CustomLabel(
            parent=self.frame,
            text="Ready",
            font=FontEngine.get("body"),
            bg=bg_color,
            fg=muted_color,
        )
        self.status_lbl.pack(anchor="w")

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Nitro.Horizontal.TProgressbar",
            troughcolor="#1E1F22",
            background=accent_color,
            darkcolor=accent_color,
            lightcolor=accent_color,
            bordercolor="#1E1F22",
            thickness=8,
        )

        self.bar = ttk.Progressbar(
            self.frame,
            style="Nitro.Horizontal.TProgressbar",
            mode="determinate",
            maximum=100,
        )
        self.bar.pack(fill="x", pady=(6, 4))

        self.summary_lbl = CustomLabel(
            parent=self.frame,
            text="",
            font=FontEngine.get("body"),
            bg=bg_color,
            fg=fg_color,
        )
        self.summary_lbl.pack(anchor="w")

        # Hide the bar and summary line while idle so the panel stays compact.
        self._bar_visible = False
        self._summary_visible = False
        self.bar.pack_forget()
        self.summary_lbl.pack_forget()

    def _show_bar(self, visible: bool) -> None:
        self._bar_visible = visible
        if visible:
            self.bar.pack(fill="x", pady=(6, 4))
            if self._summary_visible:
                # Re-pack the summary so it stays below the bar.
                self.summary_lbl.pack_forget()
                self.summary_lbl.pack(anchor="w")
        else:
            self.bar.pack_forget()

    def _show_summary(self, visible: bool) -> None:
        self._summary_visible = visible
        if visible:
            self.summary_lbl.pack(anchor="w")
        else:
            self.summary_lbl.pack_forget()

    def reset(self) -> None:
        self.status_lbl.configure(text="Ready", fg=self.muted_color)
        self.bar["value"] = 0
        self.summary_lbl.configure(text="")
        self._show_bar(False)
        self._show_summary(False)

    def start(self, label: str, total_steps: int = 1) -> None:
        self._total_steps = max(1, total_steps)
        self.status_lbl.configure(text=label, fg=self.fg_color)
        self.summary_lbl.configure(text="")
        self._show_summary(False)
        self._show_bar(True)
        self.bar["mode"] = "indeterminate" if total_steps == 1 else "determinate"
        if total_steps == 1:
            self.bar.start(12)
        else:
            self.bar.stop()
            self.bar["value"] = 0

    def set_step(self, step_index: int, step_label: str) -> None:
        pct = (step_index / self._total_steps) * 100
        self.bar["value"] = pct
        self.status_lbl.configure(text=f"Step {step_index}/{self._total_steps}: {step_label}")

    def finish(self, summary: str) -> None:
        self.bar.stop()
        self.bar["mode"] = "determinate"
        self.bar["value"] = 100
        self._show_bar(True)
        self.status_lbl.configure(text="Complete", fg="#3BA55D")
        self.summary_lbl.configure(text=summary)
        self._show_summary(True)

    def set_accent(self, accent_color: str) -> None:
        self.accent_color = accent_color
        style = ttk.Style(self.root)
        style.configure(
            "Nitro.Horizontal.TProgressbar",
            background=accent_color,
            darkcolor=accent_color,
            lightcolor=accent_color,
        )

    def fail(self, message: str) -> None:
        self.bar.stop()
        self._show_bar(True)
        self.status_lbl.configure(text=message, fg="#ED4245")
        self.summary_lbl.configure(text="")
        self._show_summary(False)
