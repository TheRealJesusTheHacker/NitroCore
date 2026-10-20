"""NitroCore design system — one palette, one spacing scale, shared primitives.

Everything visual in the GUI should come from here so the whole app feels
like it was designed by one person. The palette is NitroCore's own
"namesake" identity (fleet palette program, 2026-10-20): nitrous — a
carbon-black base, nitrous-azure primary, pale-nitrous accent, cool steel
text. The accent stays profile-driven, and both profile accents now come
from this palette: Gaming wears PRIMARY azure, Cybersecurity wears the
pale ACCENT (see source/utils/profiles.py; tests/test_theme.py pins the
two in sync so they cannot drift apart).

Every text/background pairing in this palette measures at least 4.5:1
(WCAG) — the pairs are pinned by tests/test_theme.py. Text painted on a
PRIMARY/ACCENT fill is ON_PRIMARY (dark), never white: white on azure
measures only ~2.7:1. Destructive fills are the fleet danger red
(DANGER) with white text (6.02:1), the same red as every Sentinel tool;
ERROR below is a different job — error *text* on dark surfaces, where
the darker fleet red would measure ~3.4:1 and fail, so the brighter
signal red is kept for text only.

Roles with no palette constant of their own (hover, soft border, faint,
disabled surface) are derived from the base constants with mix() —
their literals below are those derivations, recomputed and pinned by
tests/test_theme.py.
"""

import tkinter as tk
import tkinter.font as tkfont
from typing import Optional

# ---------------------------------------------------------------- palette ---
BG = "#05070A"  # app backdrop (carbon black)
BG_SUNKEN = "#070B10"  # sunken areas: log view, progress trough, inputs
CARD = "#0A0F16"  # card surfaces (panel)
CARD_HOVER = "#171C23"  # card/button hover surface — mix(TEXT, CARD, 0.06)
BTN_SECONDARY_BG = CARD_HOVER
BORDER = "#1D2A3A"  # card borders (panel border)
BORDER_SOFT = "#141C28"  # barely-there borders — mix(BORDER, CARD, 0.50)
TEXT = "#E2E9F0"  # primary text (cool steel)
MUTED = "#8FA3B8"  # secondary text
FAINT = "#7A8C9E"  # captions, placeholders — mix(MUTED, BG, 0.85)
DISABLED_BG = "#080B10"  # disabled surfaces — mix(CARD, BG, 0.50)
DISABLED_FG = "#74879C"  # disabled text

# Brand accents (nitrous). PRIMARY is the Gaming profile accent; ACCENT
# is the Cybersecurity profile accent.
PRIMARY = "#2EA3FF"  # nitrous azure
ACCENT = "#7CC4FF"  # pale nitrous
ON_PRIMARY = "#02101F"  # text/glyphs painted on PRIMARY or ACCENT fills

# Destructive-action fills (fleet danger red) and the text on them.
DANGER = "#B03A2E"
ON_DANGER = "#FFFFFF"

# Semantic colors (status, logs, badges) — text roles on dark surfaces,
# not the brand accent. ERROR is text-only; destructive *fills* use
# DANGER above (see the module docstring).
SUCCESS = "#3BA55D"
WARNING = "#FAA61A"
ERROR = "#ED4245"
INFO = "#B9BBBE"

RISK_COLORS = {
    "Low": SUCCESS,
    "Medium": WARNING,
    "High": ERROR,
}

# ------------------------------------------------------------ spacing scale ---
PAD_XS = 4
PAD_SM = 8
PAD_MD = 12
PAD_LG = 16
PAD_XL = 24
PAD_XXL = 32

RADIUS_SM = 6
RADIUS_MD = 8
RADIUS_LG = 12


# ------------------------------------------------------------------ color ----
def _clamp(v: float) -> int:
    return max(0, min(255, int(round(v))))


def hex_to_rgb(color: str) -> tuple:
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: tuple) -> str:
    return "#{:02X}{:02X}{:02X}".format(*[_clamp(c) for c in rgb])


def mix(color_a: str, color_b: str, t: float) -> str:
    """Blend two hex colors. t=1 -> color_a, t=0 -> color_b."""
    ra, ga, ba = hex_to_rgb(color_a)
    rb, gb, bb = hex_to_rgb(color_b)
    return rgb_to_hex(
        (ra * t + rb * (1 - t), ga * t + gb * (1 - t), ba * t + bb * (1 - t))
    )


def darken(color: str, factor: float = 0.8) -> str:
    """Darken a hex color toward black. factor < 1 darkens."""
    r, g, b = hex_to_rgb(color)
    return rgb_to_hex((r * factor, g * factor, b * factor))


def tint(accent: str, surface: str = CARD, amount: float = 0.14) -> str:
    """A whisper of the accent over a surface — for selected states, badges."""
    return mix(accent, surface, amount)


# ------------------------------------------------------------------ drawing ---
def rounded_rect(canvas: tk.Canvas, x1, y1, x2, y2, radius, **kwargs):
    """Draw a rounded rectangle on a canvas via a smoothed polygon.

    Works on every Tk version — no exotic APIs. Returns the item id.
    """
    radius = max(0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    points = [
        x1 + radius,
        y1,
        x2 - radius,
        y1,
        x2,
        y1,
        x2,
        y1 + radius,
        x2,
        y2 - radius,
        x2,
        y2,
        x2 - radius,
        y2,
        x1 + radius,
        y2,
        x1,
        y2,
        x1,
        y2 - radius,
        x1,
        y1 + radius,
        x1,
        y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def as_font(font) -> tkfont.Font:
    """Normalize a Font instance / tuple / name into a tkfont.Font for measuring."""
    if isinstance(font, tkfont.Font):
        return font
    return tkfont.Font(font=font)


# ------------------------------------------------------------------- Card ----
class Card(tk.Canvas):
    """A rounded-corner card surface with a subtle border.

    Children go in ``card.canvas`` (an inner Frame), so it can replace
    CustomFrame anywhere a bordered card look is wanted::

        card = Card(parent, bg=theme.BG)
        card.pack(fill="x")
        tk.Label(card.canvas, ...).pack()
    """

    def __init__(
        self,
        parent: tk.Widget,
        bg: str = BG,
        card_bg: str = CARD,
        border_color: str = BORDER_SOFT,
        radius: int = RADIUS_LG,
        padx: int = PAD_MD,
        pady: int = PAD_MD,
        cursor: Optional[str] = None,
    ):
        super().__init__(
            parent,
            bg=bg,
            highlightthickness=0,
            bd=0,
            cursor=cursor or "",
        )
        self._card_bg = card_bg
        self._border_color = border_color
        self._radius = radius
        self._padx = padx
        self._pady = pady

        self.inner = tk.Frame(self, bg=card_bg)
        self._win = self.create_window(padx, pady, anchor="nw", window=self.inner)
        self.bind("<Configure>", self._redraw)
        self.inner.bind("<Configure>", self._fit)
        self._fit()

    @property
    def canvas(self) -> tk.Frame:
        """Inner content frame — pass this as the parent for child widgets."""
        return self.inner

    def set_border(self, color: str) -> None:
        self._border_color = color
        self._redraw()

    def set_fill(self, color: str) -> None:
        self._card_bg = color
        self.inner.configure(bg=color)
        self._redraw()

    def _fit(self, event=None) -> None:
        needed = self.inner.winfo_reqheight() + 2 * self._pady
        if needed > 1 and self.winfo_height() != needed:
            self.configure(height=needed)

    def _redraw(self, event=None) -> None:
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 4 or h < 4:
            return
        self.delete("card")
        rounded_rect(
            self,
            1,
            1,
            w - 1,
            h - 1,
            self._radius,
            fill=self._border_color,
            outline="",
            tags="card",
        )
        inner_r = max(1, self._radius - 1)
        rounded_rect(
            self,
            2,
            2,
            w - 2,
            h - 2,
            inner_r,
            fill=self._card_bg,
            outline="",
            tags="card",
        )
        self.itemconfigure(self._win, width=max(1, w - 2 * self._padx))
        self.coords(self._win, self._padx, self._pady)
        self.tag_lower("card", self._win)


# ------------------------------------------------------------------ Badge ----
class Badge(tk.Canvas):
    """A small pill label — risk levels, status chips, version tags."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        fg: str,
        bg: str = BG,
        pill_bg: Optional[str] = None,
        font=None,
        radius: int = 9,
        padx: int = 10,
        pady: int = 4,
    ):
        self._font = as_font(font or ("Segoe UI", 9, "bold"))
        self._fg = fg
        # Pill stays close to the card so badge text keeps >= 4.5:1
        # (at 0.16 the High-risk red measured 4.35:1 — pinned by
        # tests/test_theme.py).
        self._pill_bg = pill_bg or tint(fg, CARD, 0.10)
        self._radius = radius
        self._padx = padx
        self._pady = pady
        height = self._font.metrics("linespace") + pady * 2
        width = self._font.measure(text) + padx * 2
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=bg,
            highlightthickness=0,
            bd=0,
        )
        self._text = text
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        w = int(self.cget("width"))
        h = int(self.cget("height"))
        rounded_rect(
            self, 1, 1, w - 1, h - 1, self._radius, fill=self._pill_bg, outline=""
        )
        self.create_text(w / 2, h / 2, text=self._text, font=self._font, fill=self._fg)

    def set_text(self, text: str) -> None:
        self._text = text
        self.configure(width=self._font.measure(text) + self._padx * 2)
        self._draw()


# ------------------------------------------------------------ ToggleSwitch ----
class ToggleSwitch(tk.Canvas):
    """A friendly on/off switch bound to a BooleanVar. Replaces checkboxes."""

    def __init__(
        self,
        parent: tk.Widget,
        variable: tk.BooleanVar,
        command=None,
        bg: str = BG,
        accent: str = PRIMARY,
        width: int = 46,
        height: int = 26,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=bg,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.variable = variable
        self.command = command
        self.accent = accent
        self._tw = width
        self._th = height
        self._enabled = True
        self.bind("<Button-1>", self._on_click)
        self._draw()

    def _on_click(self, event=None) -> None:
        if not self._enabled:
            return
        self.variable.set(not self.variable.get())
        self._draw()
        if self.command:
            self.command()

    def _draw(self) -> None:
        self.delete("all")
        is_on = bool(self.variable.get())
        radius = self._th // 2
        if not self._enabled:
            track = DISABLED_BG
            knob_fill = FAINT
        else:
            track = self.accent if is_on else BORDER
            knob_fill = "#FFFFFF"
        rounded_rect(
            self, 1, 1, self._tw - 1, self._th - 1, radius - 1, fill=track, outline=""
        )
        knob_r = radius - 5
        cy = self._th / 2
        cx = (self._tw - radius - 1) if is_on else (radius + 1)
        self.create_oval(
            cx - knob_r,
            cy - knob_r,
            cx + knob_r,
            cy + knob_r,
            fill=knob_fill,
            outline="",
        )

    def set_accent(self, accent: str) -> None:
        self.accent = accent
        self._draw()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self.configure(cursor="hand2" if enabled else "")
        self._draw()

    def configure(self, *args, **kwargs):
        if "state" in kwargs:
            state = kwargs.pop("state")
            self.set_enabled(state != "disabled")
        if args or kwargs:
            super().configure(*args, **kwargs)
