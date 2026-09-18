"""
Custom UI Flat Button Component for NitroCore.
Handles drawing custom shapes, states, text layout positioning, 
and smooth mouse hover interaction sequences safely with perfect indentation.
"""

import tkinter as tk
import tkinter.font as tkfont
from typing import Callable, Optional
class CustomButton:
    """A highly responsive, custom-styled flat GUI canvas button."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable,
        font: tkfont.Font,
        bg: str = "#2F3136",
        fg: str = "#F2F3F5",
        activebackground: str = "#40444B",
        activeforeground: str = "#FFFFFF"
    ):
        self.command = command
        self.normal_background = bg
        self.normal_foreground = fg
        self.hover_background = activebackground
        self.hover_foreground = activeforeground
        self.is_disabled = False

        # Create localized execution base drawing canvas
        self.canvas = tk.Canvas(
            parent,
            bg=self.normal_background,
            highlightthickness=0,
            cursor="hand2"
        )
        
        # Draw explicit centered interface layout label
        self.label = tk.Label(
            self.canvas,
            text=text,
            font=font,
            bg=self.normal_background,
            fg=self.normal_foreground
        )
        self.label.pack(expand=True, fill="both", padx=10, pady=5)

        # Bind Win32 interaction listener signals properly
        self.canvas.bind("<Enter>", self._on_mouse_enter)
        self.canvas.bind("<Leave>", self._on_mouse_leave)
        self.canvas.bind("<Button-1>", self._on_mouse_click)
        self.label.bind("<Enter>", self._on_mouse_enter)
        self.label.bind("<Leave>", self._on_mouse_leave)
        self.label.bind("<Button-1>", self._on_mouse_click)

    def pack(self, **kwargs) -> None:
        """Exposes standard Tkinter layout grid packing boundaries."""
        self.canvas.pack(**kwargs)

    def configure(self, **kwargs) -> None:
        """Allows runtime palette property updates (like our Pip-Boy transformation)."""
        if "bg" in kwargs:
            self.normal_background = kwargs["bg"]
            self.canvas.configure(bg=kwargs["bg"])
            self.label.configure(bg=kwargs["bg"])
        if "fg" in kwargs:
            self.normal_foreground = kwargs["fg"]
            self.label.configure(fg=kwargs["fg"])
        if "activebackground" in kwargs:
            self.hover_background = kwargs["activebackground"]
        if "activeforeground" in kwargs:
            self.hover_foreground = kwargs["activeforeground"]
        if "bd" in kwargs:
            self.canvas.configure(highlightthickness=kwargs["bd"])

    def _on_mouse_enter(self, event: Optional[tk.Event] = None) -> None:
        """Swaps palette profiles to accent states on cursor enter."""
        if not self.is_disabled:
            self.canvas.configure(bg=self.hover_background)
            self.label.configure(bg=self.hover_background)
            self.label.configure(fg=self.hover_foreground)

    def _on_mouse_leave(self, event: Optional[tk.Event] = None) -> None:
        """Restores original background balances on cursor leave."""
        if not self.is_disabled:
            self.canvas.configure(bg=self.normal_background)
            self.label.configure(bg=self.normal_background)
            self.label.configure(fg=self.normal_foreground)

    def set_enabled(self, enabled: bool) -> None:
        """Toggle button interactivity during background operations."""
        self.is_disabled = not enabled
        cursor = "hand2" if enabled else ""
        self.canvas.configure(cursor=cursor)
        if not enabled:
            self.canvas.configure(bg="#36393F")
            self.label.configure(bg="#36393F", fg="#72767D")
        else:
            self.canvas.configure(bg=self.normal_background)
            self.label.configure(bg=self.normal_background, fg=self.normal_foreground)

    def _on_mouse_click(self, event: Optional[tk.Event] = None) -> None:
        """Interceptors button down clicks to trigger associated callbacks."""
        if not self.is_disabled and self.command:
            self.command()
