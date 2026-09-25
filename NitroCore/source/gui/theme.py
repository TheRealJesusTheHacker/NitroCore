"""NitroCore design system — one palette, one spacing scale, shared primitives.

Everything visual in the GUI should come from here so the whole app feels
like it was designed by one person. Tasteful dark theme, single accent color
(the accent itself is profile-driven: orange for Gaming, teal for
Cybersecurity), consistent type roles from FontEngine, and card-based
surfaces with subtle borders.
"""

import tkinter as tk
import tkinter.font as tkfont
from typing import Optional

# ---------------------------------------------------------------- palette ---
BG = "#1B1D21"            # app backdrop
BG_SUNKEN = "#141619"     # sunken areas: log view, progress trough
CARD = "#26282E"          # card surfaces
CARD_HOVER = "#2E3138"    # card/button hover surface
BTN_SECONDARY_BG = "#2E3138"
BORDER = "#3B3E46"        # subtle card borders
BORDER_SOFT = "#32353C"   # barely-there borders
TEXT = "#F2F3F5"          # primary text
MUTED = "#A9ADB3"         # secondary text
FAINT = "#6E7279"         # captions, placeholders
DISABLED_BG = "#2A2D33"
DISABLED_FG = "#6E7279"

# Semantic colors (status, logs, badges) — not the brand accent.
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
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: tuple) -> str:
    return "#{:02X}{:02X}{:02X}".format(*[_clamp(c) for c in rgb])


def mix(color_a: str, color_b: str, t: float) -> str:
    """Blend two hex colors. t=1 -> color_a, t=0 -> color_b."""
    ra, ga, ba = hex_to_rgb(color_a)
    rb, gb, bb = hex_to_rgb(color_b)
    return rgb_to_hex((ra * t + rb * (1 - t), ga * t + gb * (1 - t), ba * t + bb * (1 - t)))


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
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
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
        rounded_rect(self, 1, 1, w - 1, h - 1, self._radius,
                     fill=self._border_color, outline="", tags="card")
        inner_r = max(1, self._radius - 1)
        rounded_rect(self, 2, 2, w - 2, h - 2, inner_r,
                     fill=self._card_bg, outline="", tags="card")
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
        self._pill_bg = pill_bg or tint(fg, CARD, 0.16)
        self._radius = radius
        self._padx = padx
        self._pady = pady
        height = self._font.metrics("linespace") + pady * 2
        width = self._font.measure(text) + padx * 2
        super().__init__(
            parent, width=width, height=height, bg=bg,
            highlightthickness=0, bd=0,
        )
        self._text = text
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        w = int(self.cget("width"))
        h = int(self.cget("height"))
        rounded_rect(self, 1, 1, w - 1, h - 1, self._radius,
                     fill=self._pill_bg, outline="")
        self.create_text(w / 2, h / 2, text=self._text,
                         font=self._font, fill=self._fg)

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
        accent: str = "#FF6B35",
        width: int = 46,
        height: int = 26,
    ):
        super().__init__(
            parent, width=width, height=height, bg=bg,
            highlightthickness=0, bd=0, cursor="hand2",
        )
        self.variable = variable
        self.command = command
        self.accent = accent
        self._w = width
        self._h = height
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
        radius = self._h // 2
        if not self._enabled:
            track = DISABLED_BG
            knob_fill = FAINT
        else:
            track = self.accent if is_on else BORDER
            knob_fill = "#FFFFFF"
        rounded_rect(self, 1, 1, self._w - 1, self._h - 1, radius - 1,
                     fill=track, outline="")
        knob_r = radius - 5
        cy = self._h / 2
        cx = (self._w - radius - 1) if is_on else (radius + 1)
        self.create_oval(cx - knob_r, cy - knob_r, cx + knob_r, cy + knob_r,
                         fill=knob_fill, outline="")

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
