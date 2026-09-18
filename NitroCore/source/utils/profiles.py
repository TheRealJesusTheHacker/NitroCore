"""Optimization profile definitions for Gaming and Cybersecurity workloads."""

from typing import Dict, List, Tuple

GAMING = "gaming"
CYBERSECURITY = "cybersecurity"

PROFILE_META: Dict[str, Dict[str, str]] = {
    GAMING: {
        "label": "Gaming",
        "tagline": "Maximum FPS & lowest latency",
        "description": "Aggressive power plan, full registry tuning, background service reduction.",
        "accent": "#FF6B35",
    },
    CYBERSECURITY: {
        "label": "Cybersecurity",
        "tagline": "Stable tools & patch-friendly",
        "description": "Visual perf tweaks, temp cleanup, keeps Windows Update active.",
        "accent": "#00D4AA",
    },
}


def get_pipeline(profile: str) -> List[Tuple[str, str]]:
    """Return ordered (step_id, display_label) pairs for the active profile."""
    base = [
        ("registry", "Registry"),
        ("temp", "Temp Files"),
        ("disk", "Disk Cleanup"),
        ("services", "Services"),
        ("performance", "Performance"),
    ]
    return base


def execute_step(step_id: str, profile: str, modules) -> str:
    """Run a single pipeline step according to the selected profile."""
    if step_id == "registry":
        return modules.registry.apply_for_profile(profile)

    if step_id == "temp":
        temp = modules.temp_cleaner.clean_temp_directories()
        cache = modules.temp_cleaner.clean_browser_cache()
        return f"{temp}\n{cache}"

    if step_id == "disk":
        return modules.disk_cleanup.clean_system_files()

    if step_id == "services":
        return modules.services.optimize_for_profile(profile)

    if step_id == "performance":
        power = modules.performance.optimize_power_plan()
        proc = modules.performance.set_process_priority()
        return f"{power}\n{proc}"

    return f"Unknown step: {step_id}"


def step_requires_restore_prompt(step_id: str, profile: str) -> bool:
    """High-impact steps that should offer a restore point when run individually."""
    if step_id in ("registry", "services"):
        return True
    if step_id == "disk" and profile == GAMING:
        return True
    return False
