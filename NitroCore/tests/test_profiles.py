"""Tests for source.utils.profiles — profile definitions, pipeline layout,
and restore-point prompt rules.

All pure logic; safe on every platform. Nothing here touches the registry,
services, or the filesystem.
"""

from types import SimpleNamespace

from source.utils.profiles import (
    CYBERSECURITY,
    GAMING,
    PROFILE_META,
    execute_step,
    get_pipeline,
    step_requires_restore_prompt,
)


def test_profile_ids():
    assert GAMING == "gaming"
    assert CYBERSECURITY == "cybersecurity"
    assert GAMING != CYBERSECURITY


def test_profile_metadata_complete():
    for profile in (GAMING, CYBERSECURITY):
        meta = PROFILE_META[profile]
        assert meta["label"], f"{profile} missing label"
        assert meta["tagline"], f"{profile} missing tagline"
        assert meta["description"], f"{profile} missing description"
        assert meta["accent"].startswith("#"), f"{profile} accent is not a hex color"
    # the two profiles are visually distinct in the UI
    assert PROFILE_META[GAMING]["accent"] != PROFILE_META[CYBERSECURITY]["accent"]
    assert PROFILE_META[GAMING]["label"] != PROFILE_META[CYBERSECURITY]["label"]


def test_get_pipeline_step_order():
    expected = ["registry", "temp", "disk", "services", "performance"]
    for profile in (GAMING, CYBERSECURITY):
        pipeline = get_pipeline(profile)
        assert [step_id for step_id, _ in pipeline] == expected
        assert all(isinstance(label, str) and label for _, label in pipeline)


def test_get_pipeline_returns_fresh_list():
    # callers (e.g. the GUI) may mutate the list; each call must be independent
    first = get_pipeline(GAMING)
    first.append(("extra", "Extra"))
    assert [step_id for step_id, _ in get_pipeline(GAMING)] == [
        "registry",
        "temp",
        "disk",
        "services",
        "performance",
    ]


def test_step_requires_restore_prompt_high_impact_steps():
    # registry and services are high-impact on every profile
    for profile in (GAMING, CYBERSECURITY):
        assert step_requires_restore_prompt("registry", profile) is True
        assert step_requires_restore_prompt("services", profile) is True


def test_step_requires_restore_prompt_disk_only_on_gaming():
    assert step_requires_restore_prompt("disk", GAMING) is True
    assert step_requires_restore_prompt("disk", CYBERSECURITY) is False


def test_step_requires_restore_prompt_low_impact_steps():
    for step_id in ("temp", "performance", "not-a-real-step"):
        assert step_requires_restore_prompt(step_id, GAMING) is False
        assert step_requires_restore_prompt(step_id, CYBERSECURITY) is False


def _fake_modules():
    """Stand-in for the real module bundle — records dispatch, changes nothing."""
    return SimpleNamespace(
        registry=SimpleNamespace(apply_for_profile=lambda p: f"registry:{p}"),
        temp_cleaner=SimpleNamespace(
            clean_temp_directories=lambda: "temp-dirs",
            clean_browser_cache=lambda: "browser-cache",
        ),
        disk_cleanup=SimpleNamespace(clean_system_files=lambda: "disk"),
        services=SimpleNamespace(optimize_for_profile=lambda p: f"services:{p}"),
        performance=SimpleNamespace(
            optimize_power_plan=lambda: "power",
            set_process_priority=lambda: "proc",
        ),
    )


def test_execute_step_dispatches_to_correct_module():
    modules = _fake_modules()
    assert execute_step("registry", GAMING, modules) == "registry:gaming"
    assert execute_step("registry", CYBERSECURITY, modules) == "registry:cybersecurity"
    assert execute_step("temp", GAMING, modules) == "temp-dirs\nbrowser-cache"
    assert execute_step("disk", GAMING, modules) == "disk"
    assert execute_step("services", CYBERSECURITY, modules) == "services:cybersecurity"
    assert execute_step("performance", GAMING, modules) == "power\nproc"


def test_execute_step_profile_is_forwarded():
    modules = _fake_modules()
    assert "cybersecurity" in execute_step("registry", CYBERSECURITY, modules)
    assert "gaming" in execute_step("services", GAMING, modules)


def test_execute_step_unknown_step_never_touches_modules():
    result = execute_step("not-a-step", GAMING, _fake_modules())
    assert result.startswith("Unknown step:")
    assert "not-a-step" in result
