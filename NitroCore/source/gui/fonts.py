"""Hardware-accelerated typography profile manager for NitroCore graphics."""

import tkinter.font as tkfont
from typing import Dict, Optional

# UPDATED IMPORT: Pointing to 'source' instead of 'src'
from source.utils.config import Config


class FontEngine:
    _registry: Dict[str, tkfont.Font] = {}
    _family: Optional[str] = None

    @classmethod
    def initialize(cls) -> None:
        """Compiles font strings directly into the active Tkinter rendering layer."""
        family = "Consolas" if Config.PI_BOY_MODE else "Segoe UI"
        if cls._registry and cls._family == family:
            return  # already built for this family — skip the rebuild
        cls._registry.clear()
        cls._family = family

        # Type scale — one family, clear hierarchy. Roles, not sizes, at call sites.
        cls._registry["display"] = tkfont.Font(family=family, size=18, weight="bold")
        cls._registry["title"] = tkfont.Font(family=family, size=15, weight="bold")
        cls._registry["header"] = tkfont.Font(family=family, size=12, weight="bold")
        cls._registry["subheader"] = tkfont.Font(family=family, size=10, weight="bold")
        cls._registry["body"] = tkfont.Font(family=family, size=10, weight="normal")
        cls._registry["small"] = tkfont.Font(family=family, size=9, weight="normal")
        cls._registry["caption"] = tkfont.Font(family=family, size=8, weight="bold")
        cls._registry["button"] = tkfont.Font(family=family, size=11, weight="bold")
        cls._registry["log"] = tkfont.Font(family="Consolas", size=9, weight="normal")

    @classmethod
    def get(cls, style_name: str) -> tkfont.Font:
        return cls._registry.get(style_name, ("Segoe UI", 10, "normal"))
