"""Themed confirmation dialogs for NitroCore."""

import tkinter as tk
from tkinter import scrolledtext
from typing import List, Literal, Optional

from source.gui import theme
from source.gui.button import CustomButton
from source.gui.fonts import FontEngine

DialogResult = Literal["create", "skip", "cancel"]
RestoreFailedResult = Literal["retry", "continue", "abort"]


def _icon_badge(parent: tk.Widget, bg: str, glyph: str, color: str) -> tk.Canvas:
    """A small circular badge with a glyph — friendlier than a bare title."""
    canvas = tk.Canvas(parent, width=40, height=40, bg=bg, highlightthickness=0, bd=0)
    canvas.create_oval(2, 2, 38, 38, fill=color, outline="")
    # Glyph color follows the fill: white only on the danger red (the
    # fleet pair, 6.02:1); dark on the bright accent/warning/success
    # fills, where white would wash out.
    glyph_fg = theme.ON_DANGER if color == theme.DANGER else theme.ON_PRIMARY
    canvas.create_text(20, 21, text=glyph, font=FontEngine.get("header"), fill=glyph_fg)
    return canvas


class RestorePointDialog:
    """Themed modal offering restore point creation before optimizations."""

    def __init__(
        self,
        parent: tk.Tk,
        title: str = "Safety Check",
        message: str = "This will change some Windows settings. "
        "Want me to create a restore point first, just in case?",
        bg: str = theme.CARD,
        fg: str = theme.TEXT,
        muted: str = theme.MUTED,
        accent: str = theme.PRIMARY,
    ):
        self.result: Optional[DialogResult] = None

        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.configure(bg=bg)
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()

        parent.update_idletasks()
        w, h = 460, 230
        px = parent.winfo_x() + (parent.winfo_width() - w) // 2
        py = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.top.geometry(f"{w}x{h}+{px}+{py}")

        title_row = tk.Frame(self.top, bg=bg)
        title_row.pack(fill="x", padx=20, pady=(18, 6))

        _icon_badge(title_row, bg, "!", accent).pack(side="left")

        tk.Label(
            title_row,
            text=title,
            font=FontEngine.get("header"),
            bg=bg,
            fg=fg,
        ).pack(side="left", padx=(12, 0))

        tk.Label(
            self.top,
            text=message,
            font=FontEngine.get("body"),
            bg=bg,
            fg=muted,
            wraplength=410,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 18))

        btn_row = tk.Frame(self.top, bg=bg)
        btn_row.pack(fill="x", padx=20, pady=(0, 18))

        for text, result, is_primary in [
            ("Create & Continue", "create", True),
            ("Skip", "skip", False),
            ("Cancel", "cancel", False),
        ]:
            btn = CustomButton(
                btn_row,
                text=text,
                command=lambda r=result: self._close(r),
                font=FontEngine.get("button"),
                bg=accent if is_primary else theme.BTN_SECONDARY_BG,
                fg=theme.ON_PRIMARY if is_primary else fg,
                activebackground=theme.darken(accent, 0.85) if is_primary else accent,
                activeforeground=theme.ON_PRIMARY,
                corner_radius=theme.RADIUS_MD,
                border_color=None if is_primary else theme.BORDER,
            )
            btn.pack(side="left", padx=(0, 8))

        self.top.protocol("WM_DELETE_WINDOW", lambda: self._close("cancel"))
        parent.wait_window(self.top)

    def _close(self, result: DialogResult) -> None:
        self.result = result
        self.top.grab_release()
        self.top.destroy()

    @classmethod
    def ask(
        cls,
        parent: tk.Tk,
        message: str = "This will change some Windows settings. "
        "Want me to create a restore point first, just in case?",
    ) -> DialogResult:
        dialog = cls(parent, message=message)
        return dialog.result or "cancel"


class ConfirmDialog:
    """Themed modal asking the user to confirm or cancel a risky action.

    Returns True when the user confirms, False on cancel or window close.
    Pass danger=True to paint the confirm button red for destructive actions.
    """

    def __init__(
        self,
        parent: tk.Tk,
        title: str = "Are you sure?",
        message: str = "",
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        glyph: str = "?",
        danger: bool = False,
        bg: str = theme.CARD,
        fg: str = theme.TEXT,
        muted: str = theme.MUTED,
        accent: str = theme.PRIMARY,
    ):
        self.result = False
        confirm_bg = theme.DANGER if danger else accent
        confirm_fg = theme.ON_DANGER if danger else theme.ON_PRIMARY

        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.configure(bg=bg)
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()

        parent.update_idletasks()
        w, h = 460, 250
        px = parent.winfo_x() + (parent.winfo_width() - w) // 2
        py = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.top.geometry(f"{w}x{h}+{px}+{py}")

        title_row = tk.Frame(self.top, bg=bg)
        title_row.pack(fill="x", padx=20, pady=(18, 6))

        _icon_badge(title_row, bg, glyph, confirm_bg).pack(side="left")

        tk.Label(
            title_row,
            text=title,
            font=FontEngine.get("header"),
            bg=bg,
            fg=fg,
        ).pack(side="left", padx=(12, 0))

        tk.Label(
            self.top,
            text=message,
            font=FontEngine.get("body"),
            bg=bg,
            fg=muted,
            wraplength=410,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 18))

        btn_row = tk.Frame(self.top, bg=bg)
        btn_row.pack(fill="x", padx=20, pady=(0, 18))

        confirm_btn = CustomButton(
            btn_row,
            text=confirm_text,
            command=lambda: self._close(True),
            font=FontEngine.get("button"),
            bg=confirm_bg,
            fg=confirm_fg,
            activebackground=theme.darken(confirm_bg, 0.85),
            activeforeground=confirm_fg,
            corner_radius=theme.RADIUS_MD,
        )
        confirm_btn.pack(side="left", padx=(0, 8))

        cancel_btn = CustomButton(
            btn_row,
            text=cancel_text,
            command=lambda: self._close(False),
            font=FontEngine.get("button"),
            bg=theme.BTN_SECONDARY_BG,
            fg=fg,
            activebackground=accent,
            activeforeground=theme.ON_PRIMARY,
            corner_radius=theme.RADIUS_MD,
            border_color=theme.BORDER,
        )
        cancel_btn.pack(side="left")

        self.top.protocol("WM_DELETE_WINDOW", lambda: self._close(False))
        parent.wait_window(self.top)

    def _close(self, result: bool) -> None:
        self.result = result
        self.top.grab_release()
        self.top.destroy()

    @classmethod
    def ask(
        cls,
        parent: tk.Tk,
        title: str = "Are you sure?",
        message: str = "",
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        glyph: str = "?",
        danger: bool = False,
    ) -> bool:
        dialog = cls(
            parent,
            title=title,
            message=message,
            confirm_text=confirm_text,
            cancel_text=cancel_text,
            glyph=glyph,
            danger=danger,
        )
        return dialog.result


class RestoreFailedDialog:
    """Shown when a requested restore point could not be created (M-1).

    The pipeline must NOT proceed silently — the user picks: retry the
    restore point, continue without the safety net, or abort entirely.
    """

    def __init__(
        self,
        parent: tk.Tk,
        reason: str,
        bg: str = theme.CARD,
        fg: str = theme.TEXT,
        muted: str = theme.MUTED,
        accent: str = theme.PRIMARY,
    ):
        self.result: RestoreFailedResult = "abort"

        self.top = tk.Toplevel(parent)
        self.top.title("Restore Point Failed")
        self.top.configure(bg=bg)
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()

        parent.update_idletasks()
        w, h = 480, 290
        px = parent.winfo_x() + (parent.winfo_width() - w) // 2
        py = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.top.geometry(f"{w}x{h}+{px}+{py}")

        title_row = tk.Frame(self.top, bg=bg)
        title_row.pack(fill="x", padx=20, pady=(18, 6))

        _icon_badge(title_row, bg, "!", theme.WARNING).pack(side="left")

        tk.Label(
            title_row,
            text="Restore Point Failed",
            font=FontEngine.get("header"),
            bg=bg,
            fg=fg,
        ).pack(side="left", padx=(12, 0))

        tk.Label(
            self.top,
            text=(
                "I couldn't create the restore point:\n"
                f"{reason}\n\n"
                "Without it there's no safety net if something goes wrong. "
                "How do you want to proceed?"
            ),
            font=FontEngine.get("body"),
            bg=bg,
            fg=muted,
            wraplength=430,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 18))

        btn_row = tk.Frame(self.top, bg=bg)
        btn_row.pack(fill="x", padx=20, pady=(0, 18))

        for text, result, is_primary in [
            ("Try Again", "retry", True),
            ("Continue Without It", "continue", False),
            ("Abort", "abort", False),
        ]:
            btn = CustomButton(
                btn_row,
                text=text,
                command=lambda r=result: self._close(r),
                font=FontEngine.get("button"),
                bg=accent if is_primary else theme.BTN_SECONDARY_BG,
                fg=theme.ON_PRIMARY if is_primary else fg,
                activebackground=theme.darken(accent, 0.85) if is_primary else accent,
                activeforeground=theme.ON_PRIMARY,
                corner_radius=theme.RADIUS_MD,
                border_color=None if is_primary else theme.BORDER,
            )
            btn.pack(side="left", padx=(0, 8))

        self.top.protocol("WM_DELETE_WINDOW", lambda: self._close("abort"))
        parent.wait_window(self.top)

    def _close(self, result: RestoreFailedResult) -> None:
        self.result = result
        self.top.grab_release()
        self.top.destroy()

    @classmethod
    def ask(cls, parent: tk.Tk, reason: str) -> RestoreFailedResult:
        dialog = cls(parent, reason)
        return dialog.result


class PreviewReportDialog:
    """Themed scrollable modal listing everything a dry run would have changed."""

    def __init__(
        self,
        parent: tk.Tk,
        entries: List[str],
        bg: str = theme.CARD,
        fg: str = theme.TEXT,
        muted: str = theme.MUTED,
        accent: str = theme.PRIMARY,
    ):
        self.top = tk.Toplevel(parent)
        self.top.title("Preview Report — no changes made")
        self.top.configure(bg=bg)
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()

        parent.update_idletasks()
        w, h = 620, 460
        px = parent.winfo_x() + (parent.winfo_width() - w) // 2
        py = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.top.geometry(f"{w}x{h}+{px}+{py}")

        title_row = tk.Frame(self.top, bg=bg)
        title_row.pack(fill="x", padx=20, pady=(18, 4))

        _icon_badge(title_row, bg, "\u2713", theme.SUCCESS).pack(side="left")

        tk.Label(
            title_row,
            text="Preview Report",
            font=FontEngine.get("header"),
            bg=bg,
            fg=fg,
        ).pack(side="left", padx=(12, 0))

        tk.Label(
            self.top,
            text=f"{len(entries)} change(s) previewed, 0 applied.",
            font=FontEngine.get("body"),
            bg=bg,
            fg=accent,
        ).pack(anchor="w", padx=20, pady=(0, 10))

        text = scrolledtext.ScrolledText(
            self.top,
            font=FontEngine.get("log"),
            bg=theme.BG_SUNKEN,
            fg=fg,
            insertbackground=fg,
            relief="flat",
            wrap="word",
            state="disabled",
            height=14,
        )
        text.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        text.configure(state="normal")
        if entries:
            for index, entry in enumerate(entries, start=1):
                text.insert("end", f"{index}. {entry}\n")
        else:
            text.insert(
                "end",
                "All clear \u2014 your system already matches the target state, "
                "so there's nothing to change.",
            )
        text.configure(state="disabled")

        tk.Label(
            self.top,
            text="PREVIEW ONLY \u2014 no changes were made.",
            font=FontEngine.get("small"),
            bg=bg,
            fg=muted,
        ).pack(anchor="w", padx=20, pady=(0, 12))

        close_btn = CustomButton(
            self.top,
            text="Close",
            command=self._close,
            font=FontEngine.get("button"),
            bg=accent,
            fg=theme.ON_PRIMARY,
            activebackground=theme.darken(accent, 0.85),
            activeforeground=theme.ON_PRIMARY,
            corner_radius=theme.RADIUS_MD,
        )
        close_btn.pack(anchor="e", padx=20, pady=(0, 18))

        self.top.protocol("WM_DELETE_WINDOW", self._close)
        parent.wait_window(self.top)

    def _close(self) -> None:
        self.top.grab_release()
        self.top.destroy()

    @classmethod
    def show(cls, parent: tk.Tk, entries: List[str]) -> None:
        cls(parent, entries)
