"""Hardware-accelerated typography profile manager for NitroCore graphics."""
import tkinter.font as tkfont
from typing import Dict

# UPDATED IMPORT: Pointing to 'source' instead of 'src'
from source.utils.config import Config

class FontEngine:
    _registry: Dict[str, tkfont.Font] = {}

    @classmethod
    def initialize(cls) -> None:
        """Compiles font strings directly into the active Tkinter rendering layer."""
        if cls._registry:
            cls._registry.clear()

        family = "Consolas" if Config.PI_BOY_MODE else "Segoe UI"

        cls._registry["title"] = tkfont.Font(family=family, size=15, weight="bold")
        cls._registry["header"] = tkfont.Font(family=family, size=11, weight="bold")
        cls._registry["body"] = tkfont.Font(family=family, size=10, weight="normal")
        cls._registry["button"] = tkfont.Font(family=family, size=11, weight="bold")
        cls._registry["log"] = tkfont.Font(family="Consolas", size=9, weight="normal")

    @classmethod
    def get(cls, style_name: str) -> tkfont.Font:
        return cls._registry.get(style_name, ("Segoe UI", 10, "normal"))
