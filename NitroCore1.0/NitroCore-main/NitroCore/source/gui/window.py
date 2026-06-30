"""
Core Window manager script featuring native Windows high-DPI scaling presets.
Guarantees fluid window lifecycle handling and stutter-free spatial alignment.
"""

import tkinter as tk
import ctypes
import os
from typing import Callable, Optional, Tuple

from source.utils.paths import resource_path


class Window:
    """
    High-performance root window lifecycle manager built for NitroCore.
    Enforces sharp high-DPI text scaling and smooth visual initialization pipelines.
    """
    
    def __init__(
        self,
        title: str = "NitroCore System Optimizer",
        width: int = 950,                # Optimized default canvas layout width
        height: int = 650,               # Optimized default canvas layout height
        resizable: bool = False,         # Clamp size to maintain your sleek layout ratios
        bg_color: str = "#202225"        # Dominant rich charcoal slate app backdrop
    ):
        """Initialize high-DPI window structures and register hardware interface parameters."""
        # 1. Active Windows OS high-DPI awareness targeting
        # Tells Windows not to stretch our pixel grids, keeping typography beautifully sharp
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2) # Per-monitor DPI aware mode
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware() # Fallback for older Windows systems
            except Exception:
                pass # Non-Windows runtime environment guard

        self.root = tk.Tk()
        self.root.title(title)
        self.root.config(bg=bg_color)
        self._apply_icon()
        
        # Hide the root frame instantly during geometry calculation to prevent corner flashing
        self.root.withdraw()
        
        # Configure sizing parameters
        self.width = width
        self.height = height
        self.root.resizable(resizable, resizable)
        
        # Application state tracking
        self.is_open = True
        self.on_close_callbacks = []
        
        # Bind the platform OS window dismissal event cleanly
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Center the canvas and transition to active rendering states flawlessly
        self._calculate_centered_geometry()

    def _apply_icon(self) -> None:
        icon_path = resource_path(os.path.join("assets", "icon.ico"))
        if os.path.isfile(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

    @property
    def canvas(self) -> tk.Tk:
        """Exposes the underlying root window handle for root component bindings."""
        return self.root

    def _calculate_centered_geometry(self) -> None:
        """Computes coordinate matrices silently off-screen to eliminate frame flashing."""
        self.root.update_idletasks()
        
        # Fetch actual client monitor space metrics
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Parse optimal anchor offsets
        x = (screen_width // 2) - (self.width // 2)
        y = (screen_height // 2) - (self.height // 2)
        
        # Enforce structural geometry string layout mappings
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        # Restore window tracking states now that alignment variables are safely updated
        self.root.deiconify()

    def _on_close(self) -> None:
        """Executes active cleanups before destroying C-level engine targets."""
        self.is_open = False
        for callback in self.on_close_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"[UI Lifecycle Warning] Window dismissal routine tracking failed: {e}")
        self.root.destroy()

    def add_close_callback(self, callback: Callable[[], None]) -> None:
        """Registers a background cleanup task (like saving user config profiles) to run on app exit."""
        if callback not in self.on_close_callbacks:
            self.on_close_callbacks.append(callback)

    def show(self) -> None:
        """Hands thread execution focus over to the main single-threaded Tkinter loop engine."""
        if self.is_open:
            self.root.mainloop()

    def hide(self) -> None:
        """Hides the graphical context stack without dropping internal tracking states."""
        self.root.withdraw()

    def focus(self) -> None:
        """Lifts the primary context frame straight to the absolute foreground layout tier."""
        self.root.lift()
        self.root.focus_force()
