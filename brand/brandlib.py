"""Shared pieces for the brand builders: tokens from the site CSS, paths, fonts.

The colour values are read from src/styles/global.css so the brand files and
the website cannot drift apart. Anything defined only here (print-only values)
is marked as such.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "brand"
OUT = BRAND / "out"            # generated, not tracked
ASSETS = BRAND / "assets"      # generated, tracked: logos and fonts people download
CSS = ROOT / "src/styles/global.css"
NM = ROOT / "node_modules"

FONT_SRC = {
    "doto": NM / "@fontsource/doto/files/doto-latin-900-normal.woff2",
    "archivo": NM / "@fontsource-variable/archivo/files/archivo-latin-wdth-normal.woff2",
    "mono": NM / "@fontsource-variable/jetbrains-mono/files/jetbrains-mono-latin-wght-normal.woff2",
}


def tokens():
    """The :root custom properties of the site, plus the red used on paper.

    The site sets red text on paper slabs to #d42a12 inline (`.slab .label.red`)
    because #ff3d24 is too light on #f3f3ef; it is read from the same file.
    """
    css = CSS.read_text()
    root = re.search(r":root\s*\{(.*?)\n\}", css, re.S).group(1)
    t = {k: v.strip() for k, v in re.findall(r"--([\w-]+):\s*([^;]+);", root)}
    t["signal-on-paper"] = re.search(r"\.slab \.label\.red \{ color: (#[0-9a-f]{6})", css).group(1)
    return t


def hex_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def contrast(a, b):
    def lum(c):
        def ch(v):
            v /= 255
            return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        r, g, bl = (ch(v) for v in hex_rgb(c))
        return 0.2126 * r + 0.7152 * g + 0.0722 * bl
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)
