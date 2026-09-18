"""Premium-styled confirmation dialogs."""

import tkinter as tk
from typing import Literal, Optional

from source.gui.fonts import FontEngine

DialogResult = Literal["create", "skip", "cancel"]


class RestorePointDialog:
    """Dark-themed modal offering restore point creation before optimizations."""

    def __init__(
        self,
        parent: tk.Tk,
        title: str = "Safety Check",
        message: str = "NitroCore will modify system settings. Create a restore point first?",
        bg: str = "#2F3136",
        fg: str = "#F2F3F5",
        muted: str = "#B9BBBE",
        accent: str = "#FF6B35",
    ):
        self.result: Optional[DialogResult] = None

        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.configure(bg=bg)
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()

        parent.update_idletasks()
        w, h = 440, 200
        px = parent.winfo_x() + (parent.winfo_width() - w) // 2
        py = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.top.geometry(f"{w}x{h}+{px}+{py}")

        tk.Label(
            self.top,
            text=title,
            font=FontEngine.get("header"),
            bg=bg,
            fg=fg,
        ).pack(anchor="w", padx=20, pady=(18, 6))

        tk.Label(
            self.top,
            text=message,
            font=FontEngine.get("body"),
            bg=bg,
            fg=muted,
            wraplength=400,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 16))

        btn_row = tk.Frame(self.top, bg=bg)
        btn_row.pack(fill="x", padx=20, pady=(0, 16))

        for text, result, color in [
            ("Create & Continue", "create", accent),
            ("Skip", "skip", "#40444B"),
            ("Cancel", "cancel", "#40444B"),
        ]:
            tk.Button(
                btn_row,
                text=text,
                font=FontEngine.get("button"),
                bg=color,
                fg="#FFFFFF" if color == accent else fg,
                activebackground=color,
                activeforeground="#FFFFFF",
                relief="flat",
                padx=12,
                pady=6,
                command=lambda r=result: self._close(r),
            ).pack(side="left", padx=(0, 8))

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
        message: str = "NitroCore will modify system settings. Create a restore point first?",
    ) -> DialogResult:
        dialog = cls(parent, message=message)
        return dialog.result or "cancel"
