"""System tray integration wrapper for background standby execution."""
import pystray
from PIL import Image, ImageDraw
from typing import Callable

class SystemTrayManager:
    """Manages the taskbar notification tray icon lifecycle."""
    
    def __init__(self, on_show_clicked: Callable, on_exit_clicked: Callable):
        # Generates a tiny placeholder icon dynamically (Replace with 'icon.ico' path later)
        image = Image.new('RGB', (64, 64), color='#202225')
        d = ImageDraw.Draw(image)
        d.text((24, 24), "NC", fill="#F2F3F5")

        self.menu = pystray.Menu(
            pystray.MenuItem('Open Dashboard', on_show_clicked, default=True),
            pystray.MenuItem('Exit Completely', on_exit_clicked)
        )
        self.icon = pystray.Icon("NitroCore", image, "NitroCore Optimizer", self.menu)

    def run(self) -> None:
        """Launches the tray icon on an independent background thread loop."""
        self.icon.run_detached()

    def stop(self) -> None:
        """Removes the icon cleanly from the taskbar."""
        self.icon.stop()
