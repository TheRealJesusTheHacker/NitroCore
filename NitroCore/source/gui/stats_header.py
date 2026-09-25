"""Live system stats header bar — a row of stat cards."""

import tkinter as tk
from typing import Optional

from source.gui import theme
from source.gui.frame import CustomFrame
from source.gui.label import CustomLabel
from source.gui.fonts import FontEngine
from source.modules.system_stats import SystemStats


class StatsHeader:
    """Polls system metrics and renders a row of stat cards."""

    POLL_MS = 2000

    STAT_DEFS = [
        ("cpu", "CPU", "Processor load"),
        ("ram", "Memory", "RAM in use"),
        ("disk", "Disk", "Busiest drive"),
        ("power", "Power", "Active plan"),
    ]

    def __init__(
        self,
        parent: tk.Widget,
        root: tk.Tk,
        bg_color: str = theme.BG,
        card_color: str = theme.CARD,
        fg_color: str = theme.TEXT,
        muted_color: str = theme.MUTED,
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
        container.pack(fill="x", pady=(0, theme.PAD_MD))
        self.container = container

        inner = tk.Frame(container.canvas, bg=bg_color)
        inner.pack(fill="x")

        for key, title, hint in self.STAT_DEFS:
            self._add_stat_card(inner, key, title, hint)

        self.refresh()

    def _add_stat_card(self, parent: tk.Widget, key: str, title: str, hint: str) -> None:
        card = theme.Card(
            parent,
            bg=self.bg_color,
            card_bg=self.card_color,
            border_color=theme.BORDER_SOFT,
            radius=theme.RADIUS_LG,
            padx=theme.PAD_LG,
            pady=theme.PAD_MD,
        )
        card.pack(side="left", fill="x", expand=True, padx=(0, theme.PAD_SM))

        title_lbl = CustomLabel(
            parent=card.canvas,
            text=title,
            font=FontEngine.get("caption"),
            bg=self.card_color,
            fg=self.muted_color,
        )
        title_lbl.pack(anchor="w")

        value_lbl = CustomLabel(
            parent=card.canvas,
            text="—",
            font=FontEngine.get("header"),
            bg=self.card_color,
            fg=self.accent_color,
        )
        value_lbl.pack(anchor="w", pady=(2, 0))
        self._value_labels[key] = value_lbl

        hint_lbl = CustomLabel(
            parent=card.canvas,
            text=hint,
            font=FontEngine.get("small"),
            bg=self.card_color,
            fg=theme.FAINT,
        )
        hint_lbl.pack(anchor="w")

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
