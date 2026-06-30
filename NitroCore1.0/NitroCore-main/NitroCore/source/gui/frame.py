"""
Custom Frame component acting as an isolated layout layout container panel.
Optimized to provide strict layout nesting boundaries without UI manager locking loops.
"""

import tkinter as tk
from typing import Optional, Tuple, Union


class CustomFrame:
    """
    High-performance flat layout container panel built for NitroCore.
    Exposes explicit parent mapping properties to allow child widgets 
    to choose their layout manager freely.
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        bg_color: str = "#2F3136",      # Discord-style deep panel background
        borderwidth: int = 0,            # Zeroed out border by default for smooth panels
        relief: str = "flat"            # Flat uniform visual layer design
    ):
        """Initialize backend canvas layout panel containers."""
        self.bg_color = bg_color
        
        # Core underlying widget initialization
        self.widget = tk.Frame(
            parent,
            bg=self.bg_color,
            borderwidth=borderwidth,
            relief=relief
        )

    @property
    def canvas(self) -> tk.Frame:
        """
        The critical structural accessor property.
        Pass this object as the 'parent' argument when creating child components.
        Example: CustomButton(my_frame.canvas, text="Run Optimizer")
        """
        return self.widget

    def pack(self, **kwargs) -> None:
        """Expose flexible container layout pack layout control."""
        self.widget.pack(**kwargs)

    def grid(self, row: int, column: int, **kwargs) -> None:
        """Expose container grid array alignment control."""
        self.widget.grid(row=row, column=column, **kwargs)

    def place(self, **kwargs) -> None:
        """Expose precise relative or pixel coordinates mapping controls."""
        self.widget.place(**kwargs)

    def set_background(self, color: str) -> None:
        """Updates the panel background theme color signature smoothly across components."""
        self.bg_color = color
        self.widget.config(bg=color)

    def clear_content(self) -> None:
        """
        Safely purges and destroys all child widgets inside this frame canvas.
        Essential for clearing out UI cards dynamically without memory resource retention.
        """
        for child in self.widget.winfo_children():
            child.destroy()
