"""Configuration manager and command-line argument parser for NitroCore."""
import argparse

from source.utils.profiles import GAMING


class Config:
    """Stores global application state parameters and Easter Egg switches."""
    PI_BOY_MODE = False
    CLICK_COUNTER = 0
    ACTIVE_PROFILE = GAMING

    @classmethod
    def parse_arguments(cls) -> None:
        """Parses hidden runtime command-line flag profiles."""
        parser = argparse.ArgumentParser(description="NitroCore System Optimizer")
        parser.add_argument(
            '--fallout', 
            action='store_true', 
            help=argparse.SUPPRESS  # Hides it from standard --help lists
        )
        args, _ = parser.parse_known_args()
        if args.fallout:
            cls.PI_BOY_MODE = True
