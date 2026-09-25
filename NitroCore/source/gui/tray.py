"""System tray integration wrapper for background standby execution."""
import pystray
from PIL import Image, ImageDraw, ImageFont
from typing import Callable


def _make_icon() -> Image.Image:
    """Rounded accent badge with an 'N' — matches the in-app brand mark."""
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle([4, 4, size - 4, size - 4], radius=14, fill="#FF6B35")
    try:
        font = ImageFont.load_default(size=34)
    except TypeError:
        font = ImageFont.load_default()
    text = "N"
    try:
        # Modern Pillow: anchor the text dead-center.
        draw.text((size / 2, size / 2), text, fill="white", font=font, anchor="mm")
    except Exception:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((size - tw) / 2, (size - th) / 2), text, fill="white", font=font)
    return image


class SystemTrayManager:
    """Manages the taskbar notification tray icon lifecycle."""

    def __init__(self, on_show_clicked: Callable, on_exit_clicked: Callable):
        self.menu = pystray.Menu(
            pystray.MenuItem('Open Dashboard', on_show_clicked, default=True),
            pystray.MenuItem('Exit Completely', on_exit_clicked)
        )
        self.icon = pystray.Icon("NitroCore", _make_icon(), "NitroCore Optimizer", self.menu)

    def run(self) -> None:
        """Launches the tray icon on an independent background thread loop."""
        self.icon.run_detached()

    def stop(self) -> None:
        """Removes the icon cleanly from the taskbar."""
        self.icon.stop()
