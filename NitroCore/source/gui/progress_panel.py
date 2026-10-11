"""Progress bar and operation status panel — a slim status card."""

import tkinter as tk
import tkinter.ttk as ttk

from source.gui import theme
from source.gui.fonts import FontEngine
from source.gui.label import CustomLabel


class ProgressPanel:
    """Shows step label, progress bar, and completion summary."""

    IDLE_TEXT = "Ready when you are."
    DONE_TEXT = "All done"

    def __init__(
        self,
        parent: tk.Widget,
        root: tk.Tk,
        bg_color: str = theme.BG,
        fg_color: str = theme.TEXT,
        muted_color: str = theme.MUTED,
        accent_color: str = "#FF6B35",
    ):
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.muted_color = muted_color
        self.accent_color = accent_color
        self._total_steps = 1
        self.root = root

        self.frame = tk.Frame(
            parent,
            bg=theme.CARD,
            highlightthickness=1,
            highlightbackground=theme.BORDER_SOFT,
            padx=theme.PAD_LG,
            pady=theme.PAD_MD,
        )
        self.frame.pack(fill="x", pady=(0, theme.PAD_MD))

        self.status_lbl = CustomLabel(
            parent=self.frame,
            text=self.IDLE_TEXT,
            font=FontEngine.get("body"),
            bg=theme.CARD,
            fg=muted_color,
        )
        self.status_lbl.pack(anchor="w")

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Nitro.Horizontal.TProgressbar",
            troughcolor=theme.BG_SUNKEN,
            background=accent_color,
            darkcolor=accent_color,
            lightcolor=accent_color,
            bordercolor=theme.BG_SUNKEN,
            thickness=10,
        )

        self.bar = ttk.Progressbar(
            self.frame,
            style="Nitro.Horizontal.TProgressbar",
            mode="determinate",
            maximum=100,
        )
        self.bar.pack(fill="x", pady=(8, 4))

        self.summary_lbl = CustomLabel(
            parent=self.frame,
            text="",
            font=FontEngine.get("small"),
            bg=theme.CARD,
            fg=muted_color,
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
            self.bar.pack(fill="x", pady=(8, 4))
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
        # L-4: stop the indeterminate animation — hiding the bar is not
        # enough, it keeps spinning in the background.
        self.bar.stop()
        self.status_lbl.configure(text=self.IDLE_TEXT, fg=self.muted_color)
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
        self.status_lbl.configure(
            text=f"Step {step_index}/{self._total_steps}: {step_label}"
        )

    def finish(self, summary: str) -> None:
        self.bar.stop()
        self.bar["mode"] = "determinate"
        self.bar["value"] = 100
        self._show_bar(True)
        self.status_lbl.configure(text=self.DONE_TEXT, fg=theme.SUCCESS)
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
        self.status_lbl.configure(text=message, fg=theme.ERROR)
        self.summary_lbl.configure(text="")
        self._show_summary(False)
