"""Gaming / Cybersecurity profile selector cards."""

import tkinter as tk
from typing import Callable

from source.gui import theme
from source.gui.fonts import FontEngine
from source.gui.label import CustomLabel
from source.utils.config import Config
from source.utils.profiles import CYBERSECURITY, GAMING, PROFILE_META


class ProfileSelector:
    """Two side-by-side profile cards with accent selection state."""

    def __init__(
        self,
        parent: tk.Widget,
        on_change: Callable[[str], None],
        bg_color: str = theme.BG,
        card_color: str = theme.CARD,
        fg_color: str = theme.TEXT,
        muted_color: str = theme.MUTED,
    ):
        self.on_change = on_change
        self.bg_color = bg_color
        self.card_color = card_color
        self.fg_color = fg_color
        self.muted_color = muted_color
        self._cards: dict[str, theme.Card] = {}
        self._accents: dict[str, str] = {
            pid: meta["accent"] for pid, meta in PROFILE_META.items()
        }

        self._top_rows: dict[str, tk.Frame] = {}
        self._card_labels: dict[str, list] = {}
        header = CustomLabel(
            parent=parent,
            text="Choose your profile",
            font=FontEngine.get("subheader"),
            bg=bg_color,
            fg=fg_color,
        )
        header.pack(anchor="w", pady=(0, theme.PAD_SM))

        row = tk.Frame(parent, bg=bg_color)
        row.pack(fill="x", pady=(0, theme.PAD_MD))

        for profile_id in (GAMING, CYBERSECURITY):
            self._build_card(row, profile_id)

        self._highlight(Config.ACTIVE_PROFILE)

    def _build_card(self, parent: tk.Widget, profile_id: str) -> None:
        meta = PROFILE_META[profile_id]
        accent = meta["accent"]

        card = theme.Card(
            parent,
            bg=self.bg_color,
            card_bg=self.card_color,
            border_color=self.card_color,
            radius=theme.RADIUS_LG,
            padx=theme.PAD_LG,
            pady=theme.PAD_MD,
            cursor="hand2",
        )
        card.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, theme.PAD_SM if profile_id == GAMING else 0),
        )
        self._cards[profile_id] = card

        top_row = tk.Frame(card.canvas, bg=self.card_color)
        top_row.pack(fill="x")
        self._top_rows[profile_id] = top_row

        title = CustomLabel(
            parent=top_row,
            text=meta["label"],
            font=FontEngine.get("header"),
            bg=self.card_color,
            fg=accent,
        )
        title.pack(side="left")

        self._dot = getattr(self, "_dot", {})
        dot = tk.Canvas(
            top_row, width=18, height=18, bg=self.card_color, highlightthickness=0, bd=0
        )
        dot.pack(side="right")
        self._dot[profile_id] = (dot, accent)

        tagline = CustomLabel(
            parent=card.canvas,
            text=meta["tagline"],
            font=FontEngine.get("body"),
            bg=self.card_color,
            fg=self.fg_color,
        )
        tagline.pack(anchor="w", pady=(2, 0))

        desc = CustomLabel(
            parent=card.canvas,
            text=meta["description"],
            font=FontEngine.get("small"),
            bg=self.card_color,
            fg=self.muted_color,
        )
        desc.configure(anchor="w", justify="left", wraplength=420)
        desc.pack(anchor="w", pady=(4, 0))
        self._card_labels[profile_id] = [title, tagline, desc]

        def select(_event=None, pid=profile_id):
            self._select(pid)

        hover_targets = [
            card,
            card.inner,
            top_row,
            dot,
            title.label,
            tagline.label,
            desc.label,
        ]
        for widget in hover_targets:
            widget.bind("<Button-1>", select)
            widget.bind("<Enter>", lambda _e, pid=profile_id: self._on_hover(pid, True))
            widget.bind(
                "<Leave>", lambda _e, pid=profile_id: self._on_hover(pid, False)
            )

    def _select(self, profile_id: str) -> None:
        if Config.ACTIVE_PROFILE == profile_id:
            return
        Config.ACTIVE_PROFILE = profile_id
        self._highlight(profile_id)
        self.on_change(profile_id)

    def _on_hover(self, profile_id: str, hovering: bool) -> None:
        if Config.ACTIVE_PROFILE == profile_id:
            return
        fill = theme.CARD_HOVER if hovering else self.card_color
        card = self._cards[profile_id]
        card.set_fill(fill)
        self._top_rows[profile_id].configure(bg=fill)
        for lbl in self._card_labels[profile_id]:
            lbl.configure(bg=fill)
        self._draw_dot(profile_id, False, fill)

    def _draw_dot(self, profile_id: str, selected: bool, fill: str) -> None:
        dot, accent = self._dot[profile_id]
        dot.configure(bg=fill)
        dot.delete("all")
        if selected:
            dot.create_oval(2, 2, 16, 16, fill=accent, outline="")
            dot.create_oval(6, 6, 12, 12, fill=theme.ON_PRIMARY, outline="")
        else:
            dot.create_oval(2, 2, 16, 16, fill="", outline=theme.BORDER, width=2)

    def _highlight(self, profile_id: str) -> None:
        for pid, card in self._cards.items():
            selected = pid == profile_id
            accent = self._accents[pid]
            fill = (
                theme.tint(accent, self.card_color, 0.10)
                if selected
                else self.card_color
            )
            card.set_border(accent if selected else self.card_color)
            card.set_fill(fill)
            self._top_rows[pid].configure(bg=fill)
            for lbl in self._card_labels[pid]:
                lbl.configure(bg=fill)
            self._draw_dot(pid, selected, fill)
