"""
Custom Input Entry component featuring thread-safe text monitoring and 
isolated placeholder schema control built for NitroCore.
"""

import tkinter as tk
from typing import Callable, Optional, Tuple, List


class CustomEntry:
    """
    High-performance flat-styled text input field component.
    Guarantees placeholder text isolation and instant text change callback processing.
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        placeholder: Optional[str] = None,
        width: Optional[int] = None,
        font: Tuple[str, int, str] = ("Segoe UI", 10, "normal"),
        show: Optional[str] = None,
        bg_color: str = "#1E1F22",       # Deep background dark theme matching
        fg_color: str = "#F2F3F5",       # Bright slate text output
        placeholder_color: str = "#4E5058" # Muted grey placeholder shade
    ):
        """Initialize core variable registers and bind hardware window event handlers."""
        self.parent = parent
        self.placeholder = placeholder
        self.placeholder_color = placeholder_color
        self.fg_color = fg_color
        self.show_char = show
        
        # Track placeholder state separately to keep data manipulation clean
        self.is_showing_placeholder = False
        self.on_change_callbacks: List[Callable[[str], None]] = []

        # Use native StringVar with dynamic structural tracers
        self.text_var = tk.StringVar()
        self.text_var.trace_add("write", self._on_text_modified)

        # Flat style generation configuration overrides
        self.widget = tk.Entry(
            parent,
            textvariable=self.text_var,
            width=width,
            font=font,
            show=show,
            bg=bg_color,
            fg=fg_color,
            insertbackground=fg_color,   # Colors the flashing input caret cursor white
            relief="flat",
            bd=4                         # Tiny internal boundary padding mask
        )
        
        # Initialize placeholder structure securely
        if self.placeholder:
            self._apply_placeholder_state()
            
        # Physical device interaction hook loops
        self.widget.bind("<FocusIn>", self._clear_placeholder)
        self.widget.bind("<FocusOut>", self._restore_placeholder)

    def pack(self, **kwargs) -> None:
        self.widget.pack(**kwargs)

    def grid(self, row: int, column: int, **kwargs) -> None:
        self.widget.grid(row=row, column=column, **kwargs)

    def place(self, **kwargs) -> None:
        self.widget.place(**kwargs)

    def get_value(self) -> str:
        """
        Safely captures text data. 
        Guaranteed to return an empty string if the placeholder mask is active.
        """
        if self.is_showing_placeholder:
            return ""
        return self.text_var.get()

    def set_value(self, value: str) -> None:
        """Updates text values safely across script boundaries."""
        self._remove_placeholder_state()
        self.text_var.set(value)
        if not value and self.placeholder:
            self._apply_placeholder_state()

    def add_change_callback(self, callback: Callable[[str], None]) -> None:
        """Registers a listener module to monitor and react to input changes in real time."""
        if callback not in self.on_change_callbacks:
            self.on_change_callbacks.append(callback)

    def _on_text_modified(self, *args) -> None:
        """Fires validation/UI callback updates only when authentic user mutations occur."""
        if self.is_showing_placeholder:
            return
        current_data = self.text_var.get()
        for callback in self.on_change_callbacks:
            try:
                callback(current_data)
            except Exception as e:
                print(f"[UI Callback Error] Input notification tracking failed: {e}")

    def _apply_placeholder_state(self) -> None:
        """Applies placeholder mask visual states cleanly."""
        self.is_showing_placeholder = True
        self.text_var.set(self.placeholder)
        self.widget.config(fg=self.placeholder_color)
        if self.show_char:
            self.widget.config(show="")  # Show placeholder text instead of bullets

    def _clear_placeholder(self, event=None) -> None:
        if self.is_showing_placeholder:
            self._remove_placeholder_state()

    def _restore_placeholder(self, event=None) -> None:
        if not self.text_var.get().strip() and self.placeholder:
            self._apply_placeholder_state()

    def _remove_placeholder_state(self) -> None:
        self.is_showing_placeholder = False
        self.text_var.set("")
        self.widget.config(fg=self.fg_color)
        if self.show_char:
            self.widget.config(show=self.show_char)

