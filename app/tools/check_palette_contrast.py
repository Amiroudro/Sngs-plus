#!/usr/bin/env python3
"""WCAG contrast check for the Sarangsho Plus 2.0 palette.

Every text/background pair the app renders, light + dark.
Run: python3 tools/check_palette_contrast.py  (exit 0 = all text >= 4.5:1)
Non-text pairs (hairlines, indicator bars) are reported, not gated.
"""
import sys

FOREST = "#1E3A2B"
FOREST_LIGHT = "#2F5442"
OAT = "#EEE6D6"
OAT_SOFT = "#F5EFE0"
PINK = "#FF7AB8"
PINK_TEXT = "#9E2A5C"
PINK_LIGHT = "#FF9ECB"
INK = "#111110"
INK_SEC = "#5C564E"
INK_FAINT = "#6B6357"
DARK_PAPER = "#14261C"
DARK_SURFACE = FOREST
DARK_SURFACE_SOFT = "#2A4A3A"
DARK_INK = OAT
DARK_INK_SEC = "#CFC6B2"
DARK_INK_FAINT = "#BFB69E"
SUCCESS_LIGHT = "#7FB89A"
WHITE = "#FFFFFF"


def lum(h):
    h = h.lstrip("#")
    r, g, b = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = f(r), f(g), f(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def cr(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# (name, text colour, background colour, gated?)
TEXT = [
    # Light mode — oat paper
    ("ink on oat paper", INK, OAT, True),
    ("inkSecondary on oat paper", INK_SEC, OAT, True),
    ("inkFaint on oat paper", INK_FAINT, OAT, True),
    ("ink on oatSoft surface", INK, OAT_SOFT, True),
    ("inkSecondary on oatSoft surface", INK_SEC, OAT_SOFT, True),
    ("inkFaint on oatSoft surface", INK_FAINT, OAT_SOFT, True),
    ("forest text on oat", FOREST, OAT, True),
    ("pinkText on oat", PINK_TEXT, OAT, True),
    ("pinkText on oatSoft", PINK_TEXT, OAT_SOFT, True),
    ("white on forest fill", WHITE, FOREST, True),
    ("white on forestLight fill", WHITE, FOREST_LIGHT, True),
    ("success (forest) on oat", FOREST, OAT, True),
    ("error (pinkText) on oat", PINK_TEXT, OAT, True),
    ("white on pinkText (option dot)", WHITE, PINK_TEXT, True),
    # Dark mode — forest base
    ("oat ink on dark paper", DARK_INK, DARK_PAPER, True),
    ("dark inkSecondary on dark paper", DARK_INK_SEC, DARK_PAPER, True),
    ("dark inkFaint on dark paper", DARK_INK_FAINT, DARK_PAPER, True),
    ("oat ink on dark surface", DARK_INK, DARK_SURFACE, True),
    ("dark inkSecondary on dark surface", DARK_INK_SEC, DARK_SURFACE, True),
    ("dark inkFaint on dark surface", DARK_INK_FAINT, DARK_SURFACE, True),
    ("oat ink on dark surfaceSoft", DARK_INK, DARK_SURFACE_SOFT, True),
    ("dark inkSecondary on dark surfaceSoft", DARK_INK_SEC, DARK_SURFACE_SOFT, True),
    ("dark inkFaint on dark surfaceSoft", DARK_INK_FAINT, DARK_SURFACE_SOFT, True),
    ("pinkLight on dark paper", PINK_LIGHT, DARK_PAPER, True),
    ("pinkLight on dark surface", PINK_LIGHT, DARK_SURFACE, True),
    ("pinkLight on dark surfaceSoft", PINK_LIGHT, DARK_SURFACE_SOFT, True),
    ("white on forestLight fill (dark)", WHITE, FOREST_LIGHT, True),
    ("successLight on dark paper", SUCCESS_LIGHT, DARK_PAPER, True),
    ("error (pinkLight) on dark paper", PINK_LIGHT, DARK_PAPER, True),
    ("forest on pinkLight (option dot, dark)", FOREST, PINK_LIGHT, True),
    # Must-fail guards (documented: never do these)
    ("RAW PINK on oat (never text)", PINK, OAT, False),
    ("white on RAW PINK (never)", WHITE, PINK, False),
    # Story screen — text accent split (Stage 4): forest on the warm
    # light paper/surface, lighter forest #7FB89A on the dark ones.
    ("story text accent (forest) on story paper light", FOREST, "#FBF8F3", True),
    ("story text accent (forest) on story surface light", FOREST, WHITE, True),
    ("story text accent (#7FB89A) on story paper dark", SUCCESS_LIGHT, "#1A1714", True),
    ("story text accent (#7FB89A) on story surface dark", SUCCESS_LIGHT, "#262019", True),
    # Must-fail guard: the old mapping (fill accent as text) was 2.10:1
    ("forestLight as TEXT on dark story paper (never)", FOREST_LIGHT, "#1A1714", False),
]

NON_TEXT = [
    ("hairline on oat", "#B5A67F", OAT),
    ("dark hairline on dark paper", "#33503F", DARK_PAPER),
    ("pink indicator on oat", PINK, OAT),
    ("pink indicator on dark paper", PINK, DARK_PAPER),
    ("pink switch track on oat", PINK, OAT),
]

fails = 0
for name, fg, bg, gated in TEXT:
    r = cr(fg, bg)
    mark = "PASS" if r >= 4.5 else ("FAIL" if gated else "expected-low")
    if gated and r < 4.5:
        fails += 1
    print(f"{r:5.2f}  [{mark:12}] {name}")
print()
for name, fg, bg in NON_TEXT:
    print(f"{cr(fg, bg):5.2f}  [non-text]   {name}")
print()
if fails:
    print(f"{fails} text pair(s) below 4.5:1")
    sys.exit(1)
print("All gated text pairs >= 4.5:1")
