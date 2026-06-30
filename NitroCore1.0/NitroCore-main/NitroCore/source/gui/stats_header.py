"""Live system stats header bar."""

import tkinter as tk
from typing import Optional

from source.gui.frame import CustomFrame
from source.gui.label import CustomLabel
from source.gui.fonts import FontEngine
from source.modules.system_stats import SystemStats


class StatsHeader:
    """Polls system metrics and renders a row of stat cards."""

    POLL_MS = 2000

    def __init__(
        self,
        parent: tk.Widget,
        root: tk.Tk,
        bg_color: str = "#202225",
        card_color: str = "#2F3136",
        fg_color: str = "#F2F3F5",
        muted_color: str = "#B9BBBE",
        accent_color: str = "#FF6B35",
    ):
        self.root = root
        self.bg_color = bg_color
        self.card_color = card_color
        self.fg_color = fg_color
        self.muted_color = muted_color
        self.accent_color = accent_color
        self._stats = SystemStats()
        self._value_labels: dict[str, CustomLabel] = {}
        self._poll_id: Optional[str] = None

        container = CustomFrame(parent, bg_color=bg_color)
        container.pack(fill="x", pady=(0, 12))
        self.container = container

        inner = tk.Frame(container.canvas, bg=bg_color)
        inner.pack(fill="x")

        for key, title in [
            ("cpu", "CPU"),
            ("ram", "RAM"),
            ("disk", "DISK"),
            ("power", "POWER"),
        ]:
            self._add_stat_card(inner, key, title)

        self.refresh()

    def _add_stat_card(self, parent: tk.Widget, key: str, title: str) -> None:
        card = tk.Frame(parent, bg=self.card_color, padx=12, pady=8)
        card.pack(side="left", fill="x", expand=True, padx=(0, 6))

        title_lbl = CustomLabel(
            parent=card,
            text=title,
            font=FontEngine.get("body"),
            bg=self.card_color,
            fg=self.muted_color,
        )
        title_lbl.pack(anchor="w")

        value_lbl = CustomLabel(
            parent=card,
            text="—",
            font=FontEngine.get("header"),
            bg=self.card_color,
            fg=self.accent_color,
        )
        value_lbl.pack(anchor="w", pady=(2, 0))
        self._value_labels[key] = value_lbl

    def refresh(self) -> None:
        try:
            data = self._stats.snapshot()
            for key, lbl in self._value_labels.items():
                lbl.configure(text=data.get(key, "—"))
        except Exception:
            pass
        self._poll_id = self.root.after(self.POLL_MS, self.refresh)

    def stop(self) -> None:
        if self._poll_id:
            self.root.after_cancel(self._poll_id)
            self._poll_id = None
