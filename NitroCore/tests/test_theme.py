"""Namesake palette pins for the NitroCore GUI theme.

NitroCore's identity in the fleet palette program (2026-10-20) is
"nitrous": carbon-black surfaces, nitrous-azure primary, pale-nitrous
accent, cool steel text. This test pins the palette so a future edit
cannot drift it silently:

- every theme constant equals the locked value from the design spec;
- the two profile accents in source/utils/profiles.py ARE the theme's
  PRIMARY (Gaming) and ACCENT (Cybersecurity) — profiles.py holds the
  literals because utils must not import the gui layer, so equality is
  enforced here instead;
- derived tones (hover, soft border, faint, disabled surface) equal
  their documented mix() derivations from the base constants;
- every text/background pairing the interface actually renders
  measures >= 4.5:1 (WCAG), computed from the constants themselves;
- no other gui module hardcodes a color literal — theme.py is the
  single source (the Pip-Boy Easter egg in main.py is a separate,
  deliberately off-palette mode and is out of scope here);
- nothing in the palette is purple (fleet rule; Beerus is the only
  owner-granted exception, and this is not Beerus).
"""

import os
import re

import pytest
from source.gui import theme
from source.utils.profiles import PROFILE_META

# ------------------------------------------------------------- WCAG math ---


def _lum(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    channels = [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]

    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (lin(c) for c in channels)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _ratio(fg: str, bg: str) -> float:
    l1, l2 = _lum(fg), _lum(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


# ------------------------------------------------------- locked constants ---

EXPECTED = {
    "BG": "#05070A",
    "BG_SUNKEN": "#070B10",
    "CARD": "#0A0F16",
    "CARD_HOVER": "#171C23",
    "BORDER": "#1D2A3A",
    "BORDER_SOFT": "#141C28",
    "TEXT": "#E2E9F0",
    "MUTED": "#8FA3B8",
    "FAINT": "#7A8C9E",
    "DISABLED_BG": "#080B10",
    "DISABLED_FG": "#74879C",
    "PRIMARY": "#2EA3FF",
    "ACCENT": "#7CC4FF",
    "ON_PRIMARY": "#02101F",
    "DANGER": "#B03A2E",
    "ON_DANGER": "#FFFFFF",
    "SUCCESS": "#3BA55D",
    "WARNING": "#FAA61A",
    "ERROR": "#ED4245",
    "INFO": "#B9BBBE",
}


def test_palette_constants_are_the_locked_namesake_values():
    for name, expected in EXPECTED.items():
        assert getattr(theme, name) == expected, name
    assert theme.BTN_SECONDARY_BG == theme.CARD_HOVER


def test_profile_accents_come_from_the_palette():
    assert PROFILE_META["gaming"]["accent"] == theme.PRIMARY
    assert PROFILE_META["cybersecurity"]["accent"] == theme.ACCENT


def test_derived_tones_match_their_mix_derivations():
    assert theme.CARD_HOVER == theme.mix(theme.TEXT, theme.CARD, 0.06)
    assert theme.BORDER_SOFT == theme.mix(theme.BORDER, theme.CARD, 0.50)
    assert theme.FAINT == theme.mix(theme.MUTED, theme.BG, 0.85)
    assert theme.DISABLED_BG == theme.mix(theme.CARD, theme.BG, 0.50)


# ------------------------------------------------------------- pair checks ---

# The fleet standard pair set, mapped onto this repo's constant names
# (TEXT_FAINT -> MUTED, INPUT_BG -> BG_SUNKEN, RED -> DANGER,
# RED_TEXT -> ON_DANGER, PRIMARY_DARK_TEXT -> ON_PRIMARY,
# DISABLED_TEXT -> DISABLED_FG, PANEL -> CARD).
STANDARD_PAIRS = [
    ("TEXT", "BG"),
    ("TEXT", "CARD"),
    ("TEXT", "BG_SUNKEN"),
    ("MUTED", "BG"),
    ("MUTED", "CARD"),
    ("PRIMARY", "BG"),
    ("PRIMARY", "CARD"),
    ("ON_PRIMARY", "PRIMARY"),
    ("ACCENT", "BG"),
    ("ACCENT", "CARD"),
    ("ON_DANGER", "DANGER"),
    ("DISABLED_FG", "BG"),
    ("DISABLED_FG", "CARD"),
]

# Pairs this interface renders beyond the standard set: hover/pressed
# fills, dialog glyphs on bright fills, semantic log/status text, the
# risk-badge pills, and the selected profile card's tinted surface.
APP_PAIRS = (
    [
        (theme.ON_PRIMARY, theme.ACCENT),
        (theme.ON_PRIMARY, theme.darken(theme.PRIMARY, 0.85)),
        (theme.ON_PRIMARY, theme.darken(theme.ACCENT, 0.85)),
        (theme.ON_DANGER, theme.darken(theme.DANGER, 0.85)),
        (theme.TEXT, theme.CARD_HOVER),
        (theme.MUTED, theme.CARD_HOVER),
        (theme.FAINT, theme.CARD),
        (theme.FAINT, theme.BG),
        (theme.DISABLED_FG, theme.DISABLED_BG),
        (theme.ON_PRIMARY, theme.WARNING),  # dialog badge glyph
        (theme.ON_PRIMARY, theme.SUCCESS),  # dialog badge glyph
    ]
    + [
        (color, surface)
        for color in (theme.SUCCESS, theme.WARNING, theme.ERROR, theme.INFO)
        for surface in (theme.BG, theme.CARD, theme.BG_SUNKEN)
    ]
    + [
        # Risk badges: signal text on its tint pill (Badge, tint 0.10).
        (color, theme.tint(color, theme.CARD, 0.10))
        for color in (theme.SUCCESS, theme.WARNING, theme.ERROR)
    ]
    + [
        # Selected profile card: labels and title on the tinted surface.
        (theme.TEXT, theme.tint(theme.PRIMARY, theme.CARD, 0.10)),
        (theme.MUTED, theme.tint(theme.ACCENT, theme.CARD, 0.10)),
        (theme.PRIMARY, theme.tint(theme.PRIMARY, theme.CARD, 0.10)),
        (theme.ACCENT, theme.tint(theme.ACCENT, theme.CARD, 0.10)),
    ]
)


@pytest.mark.parametrize("fg_name,bg_name", STANDARD_PAIRS)
def test_standard_pairs_meet_wcag_aa(fg_name, bg_name):
    fg, bg = getattr(theme, fg_name), getattr(theme, bg_name)
    assert _ratio(fg, bg) >= 4.5, f"{fg_name} on {bg_name}"


@pytest.mark.parametrize("fg,bg", APP_PAIRS, ids=[f"{f} on {b}" for f, b in APP_PAIRS])
def test_app_pairs_meet_wcag_aa(fg, bg):
    assert _ratio(fg, bg) >= 4.5, f"{fg} on {bg}"


# ------------------------------------------------------------ guard rails ---

_HEX_LITERAL = re.compile(r"#[0-9A-Fa-f]{6}\b")


def test_no_color_literals_outside_the_theme_module():
    gui_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "source", "gui"
    )
    offenders = []
    for name in sorted(os.listdir(gui_dir)):
        if not name.endswith(".py") or name == "theme.py":
            continue
        path = os.path.join(gui_dir, name)
        with open(path, encoding="utf-8") as handle:
            for lineno, line in enumerate(handle, start=1):
                if _HEX_LITERAL.search(line):
                    offenders.append(f"{name}:{lineno}: {line.strip()}")
    assert not offenders, "color literals must live in theme.py:\n" + "\n".join(
        offenders
    )


def test_palette_has_no_purple():
    # Purple/violet reads as red AND blue both well above green. Blues
    # and blue-greys keep red at or below green; the danger red keeps
    # blue at or below green. Anything else has drifted off-palette.
    values = list(EXPECTED.values()) + [
        meta["accent"] for meta in PROFILE_META.values()
    ]
    for value in values:
        r, g, b = (int(value[i : i + 2], 16) for i in (1, 3, 5))
        assert not (r > g + 40 and b > g + 40), f"{value} reads as purple"
