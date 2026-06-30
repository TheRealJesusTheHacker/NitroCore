"""
Custom UI Label Component for NitroCore.
Handles drawing stylized text strings and exposes clean dynamic property
reconfiguration parameters for color and text content swaps safely.
"""

import tkinter as tk
import tkinter.font as tkfont
from typing import Optional

class CustomLabel:
    """A clean, custom-styled flat GUI text wrapper component."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        font: tkfont.Font,
        bg: str = "#202225",
        fg: str = "#F2F3F5"
    ):
        self.normal_background = bg
        self.normal_foreground = fg

        # Create localized text label wrapper matching parents
        self.label = tk.Label(
            parent,
            text=text,
            font=font,
            bg=self.normal_background,
            fg=self.normal_foreground,
            highlightthickness=0,
            bd=0
        )

    def pack(self, **kwargs) -> None:
        """Exposes standard Tkinter layout packing parameters."""
        self.label.pack(**kwargs)

    def grid(self, **kwargs) -> None:
        """Exposes standard Tkinter grid layout parameters."""
        self.label.grid(**kwargs)

    def bind(self, sequence: str, func, add: Optional[str] = None) -> str:
        """Proxies listener events directly down to the underlying Tkinter text layer."""
        return self.label.bind(sequence, func, add)

    def configure(self, **kwargs) -> None:
        """
        UPDATED METHOD: Dynamically mutates visual characteristics.
        Prevents AttributeErrors during standard-to-PipBoy interface layout shifts.
        """
        if "bg" in kwargs:
            self.normal_background = kwargs["bg"]
            self.label.configure(bg=kwargs["bg"])
        if "fg" in kwargs:
            self.normal_foreground = kwargs["fg"]
            self.label.configure(fg=kwargs["fg"])
        if "text" in kwargs:
            self.label.configure(text=kwargs["text"])
        if "font" in kwargs:
            self.label.configure(font=kwargs["font"])
        if "justify" in kwargs:
            self.label.configure(justify=kwargs["justify"])
        if "anchor" in kwargs:
            self.label.configure(anchor=kwargs["anchor"])
