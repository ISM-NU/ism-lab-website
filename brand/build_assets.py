"""Logo files and static font files for the brand kit.

Writes brand/assets/logo/*.svg and *.png, brand/assets/fonts/*.ttf and
public/favicon.svg (the mark on a black tile).

The wordmark is the site's ISM/NU set in Doto Black, converted to outlines so
nobody needs the font to use the logo. Colours come from src/styles/global.css.
The fonts are static cuts of the site's variable fonts for Canva's Brand Kit,
which takes one file per style. All three families are SIL OFL, which allows
this.

    python3 brand/build_assets.py   # needs fonttools, brotli, Pillow; magick for PNG
"""
import re
import subprocess
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

from brandlib import ASSETS, FONT_SRC, ROOT, tokens

T = tokens()
TRACK = 0.06  # em, as .topbar .logo in src/layouts/Base.astro

# Colour sets: (main, accent). "dark" means for use on a dark ground.
SETS = {
    "on-dark": (T["ink"], T["signal"]),
    "on-light": (T["on-paper"], T["signal-on-paper"]),
    "white": (T["ink"], T["ink"]),
    "black": (T["on-paper"], T["on-paper"]),
}


def runs(font, text, x0=0.0, y0=0.0):
    """SVG path data and bounds for text, y pointing down, baseline at y0."""
    gs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font["hmtx"]
    upm = font["head"].unitsPerEm
    x, d, bounds = x0, [], None
    for i, ch in enumerate(text):
        g = cmap[ord(ch)]
        m = (1, 0, 0, -1, x, y0)
        pen = SVGPathPen(gs)
        gs[g].draw(TransformPen(pen, m))
        d.append(pen.getCommands())
        bp = BoundsPen(gs)
        gs[g].draw(TransformPen(bp, m))
        if bp.bounds:
            b = bp.bounds
            bounds = b if bounds is None else (min(bounds[0], b[0]), min(bounds[1], b[1]), max(bounds[2], b[2]), max(bounds[3], b[3]))
        x += hmtx[g][0] + (TRACK * upm if i < len(text) - 1 else 0)
    return " ".join(d), bounds, x


def svg(parts, bounds, pad):
    x0, y0, x1, y1 = bounds
    w, h = x1 - x0 + 2 * pad, y1 - y0 + 2 * pad
    body = "".join(f'<path fill="{c}" d="{d}"/>' for d, c in parts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0 - pad:.0f} {y0 - pad:.0f} {w:.0f} {h:.0f}" '
            f'width="{w:.0f}" height="{h:.0f}">{body}</svg>\n')


def union(*bs):
    return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))


# The mark: a space telescope with checkered solar panels between two stars,
# drawn pixel by pixel on a 16 x 16 grid so it is sharp as a 16 px favicon.
# "#" is the main colour, "r" the accent. Edit the pixels here; every mark
# file and public/favicon.svg are generated from this grid. Keep the stars in
# the empty corners (top right collides with a panel) and the drawing within
# x, y = 1..14, which the avatar's round-crop margin assumes.
MARK = """
................
..#........#....
.###......#.#...
..#......#.#.#..
........#.#.#.#.
...........#.#..
.......rr...#...
......rrrr.#....
....#.rrrr......
...#...rr.......
..#.#...........
.#.#.#.#........
..#.#.#......#..
...#.#......###.
....#........#..
................"""


def mark_svg(main, acc, viewbox, ground):
    rows = MARK.strip("\n").split("\n")
    assert len(rows) == 16 and all(len(r) == 16 for r in rows)
    px = {"#": [], "r": []}
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in px:
                px[ch].append(f"M{x} {y}h1v1h-1z")
    vb = [float(v) for v in viewbox.split()]
    bg = f'<rect x="{vb[0]:g}" y="{vb[1]:g}" width="{vb[2]:g}" height="{vb[3]:g}" fill="{ground}"/>' if ground else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" width="{vb[2] * 16:g}" height="{vb[3] * 16:g}" '
            f'shape-rendering="crispEdges">{bg}<path fill="{main}" d="{"".join(px["#"])}"/>'
            f'<path fill="{acc}" d="{"".join(px["r"])}"/></svg>\n')


def logos():
    doto = TTFont(FONT_SRC["doto"])
    out = ASSETS / "logo"
    out.mkdir(parents=True, exist_ok=True)
    upm = doto["head"].unitsPerEm
    for name, (main, acc) in SETS.items():
        # Horizontal: ISM/NU on one line, "/NU" in the accent.
        d1, b1, x = runs(doto, "ISM")
        d2, b2, _ = runs(doto, "/NU", x + TRACK * upm)
        pad = 0  # clear space is a rule in the brandbook, not baked into the file
        (out / f"ism-nu-wordmark-{name}.svg").write_text(svg([(d1, main), (d2, acc)], union(b1, b2), pad))
        # Stacked: ISM over /NU, right edges aligned as on the GitHub avatar.
        gap = 0.18 * upm
        d1, b1, _ = runs(doto, "ISM")
        line2_y = (b1[3] - b1[1]) + gap
        _, b2probe, _ = runs(doto, "/NU", 0, line2_y)
        shift = b1[2] - b2probe[2]
        d2, b2, _ = runs(doto, "/NU", shift, line2_y)
        (out / f"ism-nu-stacked-{name}.svg").write_text(svg([(d1, main), (d2, acc)], union(b1, b2), pad))
        # Mark: transparent, cropped to the drawing.
        (out / f"ism-nu-mark-{name}.svg").write_text(mark_svg(main, acc, "1 1 14 14", None))
    # Square black tiles: the favicon, and an avatar whose drawing fits inside
    # the inscribed circle so round crops (GitHub, Telegram, Slack) cut nothing.
    favicon = mark_svg(T["ink"], T["signal"], "0 0 16 16", T["void"])
    (out / "ism-nu-mark-tile.svg").write_text(favicon)
    (ROOT / "public" / "favicon.svg").write_text(favicon)
    (out / "ism-nu-mark-avatar.svg").write_text(mark_svg(T["ink"], T["signal"], "-2 -2 20 20", T["void"]))
    # PNG copies, 2000 px on the long side, transparent, for Canva and Office.
    # Density is set per file so the raster comes out at 2000 px directly; the
    # mark is pixel art and blurs if it is rendered small and scaled up.
    for f in sorted(out.glob("*.svg")):
        w, h = (float(v) for v in re.search(r'width="([\d.]+)" height="([\d.]+)"', f.read_text()).groups())
        subprocess.run(["magick", "-background", "none", "-density", f"{96 * 2000 / max(w, h):.1f}", str(f),
                        "-resize", "2000x2000", str(f.with_suffix(".png"))], check=True)


def rename(font, family, style, weight, bold=False):
    name = font["name"]
    for nid in (16, 17, 21, 22, 25):
        name.removeNames(nameID=nid)
    full = family if style == "Regular" else f"{family} {style}"
    ps = (family.replace(" ", "") + "-" + style.replace(" ", ""))
    for nid, val in ((1, family), (2, style), (3, f"ISM-NU;{ps}"), (4, full), (6, ps)):
        name.setName(val, nid, 3, 1, 0x409)
        name.setName(val, nid, 1, 0, 0)
    font["OS/2"].usWeightClass = weight
    sel = font["OS/2"].fsSelection & ~0b1100001  # clear italic, bold, regular
    font["OS/2"].fsSelection = sel | (0b100000 if bold else 0b1000000)
    font["head"].macStyle = 1 if bold else 0


def fonts():
    out = ASSETS / "fonts"
    out.mkdir(parents=True, exist_ok=True)
    # Each file is its own family with a Regular style, so a template can name
    # the face directly and Canva's Bold button is not needed to reach it.
    cuts = [
        ("archivo", {"wght": 800, "wdth": 62}, "Archivo Condensed ExtraBold", "Regular", 400, False),
        ("archivo", {"wght": 400, "wdth": 100}, "Archivo", "Regular", 400, False),
        ("archivo", {"wght": 600, "wdth": 100}, "Archivo", "Bold", 700, True),
    ]
    for src, axes, family, style, weight, bold in cuts:
        f = instantiateVariableFont(TTFont(FONT_SRC[src]), axes)
        f.flavor = None
        rename(f, family, style, weight, bold)
        f.save(out / f"{family.replace(' ', '')}-{style}.ttf")
    d = TTFont(FONT_SRC["doto"])
    d.flavor = None
    rename(d, "Doto Black", "Regular", 400)
    d.save(out / "DotoBlack-Regular.ttf")


if __name__ == "__main__":
    logos()
    fonts()
    for p in sorted(ASSETS.rglob("*.*")):
        print(p.relative_to(ASSETS), p.stat().st_size)
