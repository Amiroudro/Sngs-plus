#!/usr/bin/env python3
"""Regenerate the Sarangsho Plus launcher icon set (NEXUS identity).

Solid cool-crimson #B4232A square with a white "সা" mark (Noto Sans
Bengali Black), matching the in-app masthead logo block (40px crimson
block, white "সা" at 22px w900). Replaces the old emerald #0B5D3B set.

Outputs (android/app/src/main/res/):
  mipmap-{mdpi,hdpi,xhdpi,xxhdpi,xxxhdpi}/ic_launcher.png       (48..192)
  mipmap-*/ic_launcher_round.png   (crimson circle, white "সা")
  mipmap-*/ic_launcher_foreground.png (transparent, white "সা", 108dp)
The adaptive-icon background colour lives in res/values/colors.xml
(ic_launcher_background) and must be #B4232A to match.

Run: python3 tools/generate_icon.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

CRIMSON = (180, 35, 42)          # #B4232A
WHITE = (255, 255, 255)
FONT = "/usr/share/fonts/truetype/noto/NotoSansBengali-Black.ttf"
MARK = "সা"

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "android", "app", "src", "main", "res")


def render_mark(target_width, colour):
    """Render MARK in `colour` on a transparent canvas, `target_width` px
    wide (glyph bbox width), supersampled 4x for crisp downscaling."""
    ss = 4
    font = ImageFont.truetype(FONT, 400 * ss)
    tmp = Image.new("RGBA", (1200 * ss, 800 * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    d.text((0, 0), MARK, font=font, fill=colour + (255,))
    bbox = tmp.getbbox()
    glyph = tmp.crop(bbox)
    w, h = glyph.size
    new_w = target_width * ss
    new_h = round(h * new_w / w)
    glyph = glyph.resize((new_w, new_h), Image.LANCZOS)
    glyph = glyph.resize((target_width, round(h * target_width / w)),
                         Image.LANCZOS)
    return glyph


def paste_centred(base, glyph):
    x = (base.width - glyph.width) // 2
    y = (base.height - glyph.height) // 2
    base.alpha_composite(glyph, (x, y))
    return base


def legacy(size):
    img = Image.new("RGBA", (size, size), CRIMSON + (255,))
    glyph = render_mark(round(size * 0.56), WHITE)
    return paste_centred(img, glyph)


def round_icon(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, size - 1, size - 1], fill=CRIMSON + (255,))
    glyph = render_mark(round(size * 0.56), WHITE)
    return paste_centred(img, glyph)


def foreground(size):
    # White mark only, transparent background; glyph ~51% of canvas width
    # (matches the previous emerald foreground's proportions, safe zone).
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glyph = render_mark(round(size * 0.514), WHITE)
    return paste_centred(img, glyph)


DENSITIES = {
    "mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192,
}

for density, size in DENSITIES.items():
    d = os.path.join(RES, f"mipmap-{density}")
    legacy(size).save(os.path.join(d, "ic_launcher.png"))
    round_icon(size).save(os.path.join(d, "ic_launcher_round.png"))
    # Foreground is 108dp at each density.
    fg_size = size * 108 // 48
    foreground(fg_size).save(os.path.join(d, "ic_launcher_foreground.png"))
    print(f"{density}: launcher {size}x{size}, round {size}x{size}, "
          f"foreground {fg_size}x{fg_size}")

print("Done. Remember: res/values/colors.xml ic_launcher_background"
      " must be #B4232A.")
