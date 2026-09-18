"""Configuration manager and command-line argument parser for NitroCore."""
import argparse

from source.utils.profiles import GAMING


class Config:
    """Stores global application state parameters and Easter Egg switches."""
    PI_BOY_MODE = False
    CLICK_COUNTER = 0
    ACTIVE_PROFILE = GAMING
    DRY_RUN = False

    @classmethod
    def parse_arguments(cls) -> None:
        """Parses hidden runtime command-line flag profiles."""
        parser = argparse.ArgumentParser(description="NitroCore System Optimizer")
        parser.add_argument(
            '--fallout',
            action='store_true',
            help=argparse.SUPPRESS  # Hides it from standard --help lists
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview mode: print what would change without modifying the system'
        )
        args, _ = parser.parse_known_args()
        if args.fallout:
            cls.PI_BOY_MODE = True
        if args.dry_run:
            cls.DRY_RUN = True
