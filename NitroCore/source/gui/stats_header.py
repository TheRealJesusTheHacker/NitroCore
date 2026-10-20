"""Live system stats header bar — a row of stat cards."""

import tkinter as tk
from typing import Optional

from source.gui import theme
from source.gui.fonts import FontEngine
from source.gui.frame import CustomFrame
from source.gui.label import CustomLabel
from source.modules.async_worker import AsyncWorker
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
        accent_color: str = theme.PRIMARY,
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
        self._fetch_in_flight = False
        self._stopped = False

        container = CustomFrame(parent, bg_color=bg_color)
        container.pack(fill="x", pady=(0, theme.PAD_MD))
        self.container = container

        inner = tk.Frame(container.canvas, bg=bg_color)
        inner.pack(fill="x")

        for key, title, hint in self.STAT_DEFS:
            self._add_stat_card(inner, key, title, hint)

        self.refresh()

    def _add_stat_card(
        self, parent: tk.Widget, key: str, title: str, hint: str
    ) -> None:
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

    def _render(self, data: dict) -> None:
        for key, lbl in self._value_labels.items():
            lbl.configure(text=data.get(key, "—"))

    def refresh(self) -> None:
        """Priming refresh: synchronous snapshot + render, then start polling.

        Runs once during construction (window not yet shown), so blocking
        briefly here is harmless and the header never paints placeholders.
        """
        try:
            self._render(self._stats.snapshot())
        except Exception:
            pass
        self._poll_id = self.root.after(self.POLL_MS, self._poll)

    def _poll(self) -> None:
        """Periodic refresh — fetch off the UI thread, render back on it.

        snapshot() can spawn powercfg (up to its 5s timeout) when the
        power-plan TTL expires; doing that on the UI thread froze the
        window on every expiry. The next poll is scheduled up front so the
        cadence holds even if a fetch runs long; an in-flight guard keeps
        fetches from piling up.
        """
        self._poll_id = self.root.after(self.POLL_MS, self._poll)
        if self._fetch_in_flight:
            return
        self._fetch_in_flight = True

        def on_complete(result) -> None:
            self._fetch_in_flight = False
            if self._stopped or result is None:
                return

            def render() -> None:
                if not self._stopped:
                    self._render(result)

            try:
                self.root.after(0, render)
            except tk.TclError:
                pass

        AsyncWorker.run_task(self._stats.snapshot, on_complete)

    def stop(self) -> None:
        self._stopped = True
        if self._poll_id:
            self.root.after_cancel(self._poll_id)
            self._poll_id = None
