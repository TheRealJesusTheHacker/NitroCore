"""Gaming / Cybersecurity profile selector cards."""

import tkinter as tk
from typing import Callable

from source.gui.frame import CustomFrame
from source.gui.label import CustomLabel
from source.gui.fonts import FontEngine
from source.utils.config import Config
from source.utils.profiles import PROFILE_META, GAMING, CYBERSECURITY


class ProfileSelector:
    """Two side-by-side profile cards with accent selection state."""

    def __init__(
        self,
        parent: tk.Widget,
        on_change: Callable[[str], None],
        bg_color: str = "#202225",
        card_color: str = "#2F3136",
        fg_color: str = "#F2F3F5",
        muted_color: str = "#B9BBBE",
    ):
        self.on_change = on_change
        self.bg_color = bg_color
        self.card_color = card_color
        self.fg_color = fg_color
        self.muted_color = muted_color
        self._cards: dict[str, tk.Frame] = {}
        self._accents: dict[str, str] = {
            pid: meta["accent"] for pid, meta in PROFILE_META.items()
        }

        row = tk.Frame(parent, bg=bg_color)
        row.pack(fill="x", pady=(0, 12))

        for profile_id in (GAMING, CYBERSECURITY):
            self._build_card(row, profile_id)

        self._highlight(Config.ACTIVE_PROFILE)

    def _build_card(self, parent: tk.Widget, profile_id: str) -> None:
        meta = PROFILE_META[profile_id]
        accent = meta["accent"]

        card = tk.Frame(
            parent,
            bg=self.card_color,
            highlightthickness=2,
            highlightbackground=self.card_color,
            cursor="hand2",
        )
        card.pack(side="left", fill="x", expand=True, padx=(0, 8 if profile_id == GAMING else 0))
        self._cards[profile_id] = card

        title = CustomLabel(
            parent=card,
            text=meta["label"],
            font=FontEngine.get("header"),
            bg=self.card_color,
            fg=accent,
        )
        title.pack(anchor="w", padx=14, pady=(12, 2))

        tagline = CustomLabel(
            parent=card,
            text=meta["tagline"],
            font=FontEngine.get("body"),
            bg=self.card_color,
            fg=self.fg_color,
        )
        tagline.pack(anchor="w", padx=14)

        desc = CustomLabel(
            parent=card,
            text=meta["description"],
            font=FontEngine.get("body"),
            bg=self.card_color,
            fg=self.muted_color,
        )
        desc.configure(anchor="w")
        desc.pack(anchor="w", padx=14, pady=(4, 12))

        def select(_event=None, pid=profile_id):
            self._select(pid)

        for widget in (card, title.label, tagline.label, desc.label):
            widget.bind("<Button-1>", select)

    def _select(self, profile_id: str) -> None:
        if Config.ACTIVE_PROFILE == profile_id:
            return
        Config.ACTIVE_PROFILE = profile_id
        self._highlight(profile_id)
        self.on_change(profile_id)

    def _highlight(self, profile_id: str) -> None:
        for pid, card in self._cards.items():
            if pid == profile_id:
                card.configure(highlightbackground=self._accents[pid], highlightthickness=2)
            else:
                card.configure(highlightbackground=self.card_color, highlightthickness=1)
