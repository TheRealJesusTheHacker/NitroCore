"""Rounded button component for NitroCore.

A canvas-drawn button with real hover / pressed / disabled states and
rounded corners, so the UI feels like a polished commercial utility
instead of flat rectangles. Same public API as before: pack(),
configure(), set_enabled(), and a .label proxy for text updates.
"""

import tkinter as tk
import tkinter.font as tkfont
from typing import Callable, Optional

from source.gui import theme


class _ButtonLabelProxy:
    """Lets existing code keep doing ``btn.label.configure(text=...)``."""

    def __init__(self, button: "CustomButton"):
        self._button = button

    def configure(self, **kwargs) -> None:
        if "text" in kwargs:
            self._button.set_text(kwargs["text"])
        if "fg" in kwargs:
            self._button._text_fg = kwargs["fg"]
            self._button._redraw()
        if "font" in kwargs:
            self._button._set_font(kwargs["font"])

    config = configure


class CustomButton:
    """A responsive, rounded, custom-styled canvas button."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable,
        font,
        bg: str = theme.BTN_SECONDARY_BG,
        fg: str = theme.TEXT,
        activebackground: str = theme.CARD_HOVER,
        activeforeground: str = "#FFFFFF",
        corner_radius: int = theme.RADIUS_MD,
        anchor: str = "center",
        padx: int = 14,
        pady: int = 8,
        border_color: Optional[str] = None,
    ):
        self.command = command
        self.normal_background = bg
        self.normal_foreground = fg
        self.hover_background = activebackground
        self.hover_foreground = activeforeground
        self._text = text
        self._text_fg = fg
        self._radius = corner_radius
        self._anchor = anchor
        self._padx = padx
        self._pady = pady
        self._border_color = border_color
        self._pressed = False
        self._inside = False
        self.is_disabled = False
        self._set_font(font)

        try:
            canvas_bg = parent.cget("bg")
        except Exception:
            canvas_bg = bg

        height = self._font.metrics("linespace") + pady * 2
        width = self._font.measure(text) + padx * 2

        self.canvas = tk.Canvas(
            parent,
            width=width,
            height=height,
            bg=canvas_bg,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.label = _ButtonLabelProxy(self)

        self.canvas.bind("<Configure>", self._redraw)
        self.canvas.bind("<Enter>", self._on_mouse_enter)
        self.canvas.bind("<Leave>", self._on_mouse_leave)
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_release)
        self._redraw()

    # ------------------------------------------------------------- internals
    def _set_font(self, font) -> None:
        if isinstance(font, tkfont.Font):
            self._font = font
        else:
            self._font = tkfont.Font(font=font)

    def _current_fill(self) -> str:
        if self.is_disabled:
            return theme.DISABLED_BG
        if self._pressed:
            return theme.darken(self.hover_background, 0.82)
        if self._inside:
            return self.hover_background
        return self.normal_background

    def _current_text_fg(self) -> str:
        if self.is_disabled:
            return theme.DISABLED_FG
        if self._inside or self._pressed:
            return self.hover_foreground
        return self._text_fg

    def _redraw(self, event: Optional[tk.Event] = None) -> None:
        c = self.canvas
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 4 or h < 4:
            return
        c.delete("btn")
        if self._border_color:
            theme.rounded_rect(c, 0.5, 0.5, w - 0.5, h - 0.5, self._radius,
                               fill=self._border_color, outline="", tags="btn")
            theme.rounded_rect(c, 1.5, 1.5, w - 1.5, h - 1.5,
                               max(1, self._radius - 1),
                               fill=self._current_fill(), outline="", tags="btn")
        else:
            theme.rounded_rect(c, 1, 1, w - 1, h - 1, self._radius,
                               fill=self._current_fill(), outline="", tags="btn")
        if self._anchor == "w":
            x, anchor = self._padx, "w"
        else:
            x, anchor = w / 2, "center"
        c.create_text(x, h / 2, text=self._text, font=self._font,
                      fill=self._current_text_fg(), anchor=anchor, tags="btn")

    # ------------------------------------------------------------------ API
    def pack(self, **kwargs) -> None:
        """Exposes standard Tkinter pack layout control."""
        self.canvas.pack(**kwargs)

    def grid(self, **kwargs) -> None:
        self.canvas.grid(**kwargs)

    def set_text(self, text: str) -> None:
        self._text = text
        self.canvas.configure(width=self._font.measure(text) + self._padx * 2)
        self._redraw()

    def configure(self, **kwargs) -> None:
        """Runtime palette updates (e.g. profile accent swaps)."""
        if "bg" in kwargs:
            self.normal_background = kwargs["bg"]
        if "fg" in kwargs:
            self.normal_foreground = kwargs["fg"]
            self._text_fg = kwargs["fg"]
        if "activebackground" in kwargs:
            self.hover_background = kwargs["activebackground"]
        if "activeforeground" in kwargs:
            self.hover_foreground = kwargs["activeforeground"]
        if "text" in kwargs:
            self.set_text(kwargs["text"])
            return
        # Canvas chrome (used by the Pip-Boy theme path).
        for opt in ("bd", "relief", "borderwidth"):
            if opt in kwargs:
                self.canvas.configure({opt: kwargs[opt]})
        self._redraw()

    config = configure

    def set_enabled(self, enabled: bool) -> None:
        """Toggle interactivity during background operations."""
        self.is_disabled = not enabled
        self._pressed = False
        self.canvas.configure(cursor="hand2" if enabled else "")
        self._redraw()

    # ---------------------------------------------------------------- events
    def _on_mouse_enter(self, event: Optional[tk.Event] = None) -> None:
        self._inside = True
        if not self.is_disabled:
            self._redraw()

    def _on_mouse_leave(self, event: Optional[tk.Event] = None) -> None:
        self._inside = False
        self._pressed = False
        if not self.is_disabled:
            self._redraw()

    def _on_mouse_press(self, event: Optional[tk.Event] = None) -> None:
        if self.is_disabled:
            return
        self._pressed = True
        self._redraw()

    def _on_mouse_release(self, event: Optional[tk.Event] = None) -> None:
        was_pressed = self._pressed
        self._pressed = False
        if not self.is_disabled:
            self._redraw()
        if was_pressed and self._inside and self.command:
            self.command()
