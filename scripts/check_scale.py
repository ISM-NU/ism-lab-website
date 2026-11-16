#!/usr/bin/env python3
"""Keep spacing and type on the site's scale (see the top of src/styles/global.css).

Checks padding, margin, gap and font sizes in src/styles/*.css, in the <style>
blocks of src/**/*.astro and in their style="..." attributes. A px or rem
value must be a scale step. In clamp(min, preferred, max) only min and max are
checked: the fluid middle term is free. Positions (top, left, inset) and SVG or
canvas text are not checked; they are chart and decoration geometry.

    python3 scripts/check_scale.py          # report, exit 1 on any miss
    python3 scripts/check_scale.py --fix    # snap every miss to the nearest step
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPACE = [0, 1, 2, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256]  # 1 and 2: hairlines and optical nudges
TYPE = [12, 14, 16, 18, 24, 32, 48, 64, 96, 128]

PROP = re.compile(r"(?<![\w-])(padding(?:-[a-z-]+)?|margin(?:-[a-z-]+)?|gap|row-gap|column-gap|font-size|font)\s*:\s*([^;}\"`]+)")
NUM = re.compile(r"(-?\d*\.?\d+)(px|rem)\b")


def snap(v, steps, kind):
    a = abs(v)
    if kind == "space" and a in (1, 2):
        return v
    # Ties: small values round up (a little more air in tight UI), large ones
    # down (the site was too loose at the top end). Type: up to 16, then down.
    up = a < 24 if kind == "space" else a <= 16
    best = min(steps, key=lambda s: (abs(s - a), -s if up else s))
    return -best if v < 0 else best


def fmt(px, unit):
    return f"{px}px" if unit == "px" else f"{px / 16:g}rem"


def fix_value(prop, val, misses, where):
    kind = "type" if prop.startswith("font") else "space"
    steps = TYPE if kind == "type" else SPACE
    if prop == "font":
        # Shorthand: only the size before "/" or the family is a font size.
        m = re.match(r"\s*(?:[a-z]+\s+)*?(?:\d{3}\s+)?(clamp\([^)]*\)|-?\d*\.?\d+(?:px|rem))", val)
        if not m or "var(" in m.group(1)[:4]:
            return val
        head, rest = m.group(0), val[m.end():]
        return fix_value("font-size", head, misses, where) + rest

    out, i = [], 0
    # Mask the middle argument of each clamp(): it is the fluid term.
    spans = []
    for c in re.finditer(r"clamp\(", val):
        depth, j, commas = 1, c.end(), []
        while j < len(val) and depth:
            if val[j] == "(":
                depth += 1
            elif val[j] == ")":
                depth -= 1
            elif val[j] == "," and depth == 1:
                commas.append(j)
            j += 1
        if len(commas) == 2:
            spans.append((commas[0], commas[1]))
    # env(...) fallbacks and var() defaults are not spacing choices.
    for e in re.finditer(r"env\([^)]*\)", val):
        spans.append((e.start(), e.end()))

    for m in NUM.finditer(val):
        if any(a < m.start() < b for a, b in spans):
            continue
        v = float(m.group(1)) * (16 if m.group(2) == "rem" else 1)
        if v == int(v) and int(v) in [s for s in steps] + ([1, 2] if kind == "space" else []) + ([-1, -2] if kind == "space" else []) or (v < 0 and -v in steps):
            continue
        s = snap(v, steps, kind)
        misses.append(f"{where}: {prop}: {m.group(0)} -> {fmt(s, m.group(2))}")
        out.append(val[i:m.start()] + fmt(int(s), m.group(2)))
        i = m.end()
    out.append(val[i:])
    return "".join(out)


def regions(path, text):
    """(start, end) spans of CSS inside a file."""
    if path.suffix == ".css":
        return [(0, len(text))]
    r = [(m.start(1), m.end(1)) for m in re.finditer(r"<style[^>]*>(.*?)</style>", text, re.S)]
    r += [(m.start(1), m.end(1)) for m in re.finditer(r"""\bstyle=(?:"([^"]*)"|\{`([^`]*)`\})""", text) if m.group(1) is not None]
    r += [(m.start(2), m.end(2)) for m in re.finditer(r"""\bstyle=(?:"([^"]*)"|\{`([^`]*)`\})""", text) if m.group(2) is not None]
    return sorted(r)


def main():
    fix = "--fix" in sys.argv
    files = sorted((ROOT / "src").rglob("*.astro")) + sorted((ROOT / "src" / "styles").glob("*.css"))
    misses = []
    for f in files:
        text = f.read_text()
        new, last = [], 0
        for a, b in regions(f, text):
            chunk = text[a:b]

            def rep(m):
                line = text.count("\n", 0, a + m.start()) + 1
                return f"{m.group(1)}: " + fix_value(m.group(1), m.group(2), misses, f"{f.relative_to(ROOT)}:{line}")

            new.append(text[last:a] + PROP.sub(rep, chunk))
            last = b
        new.append(text[last:])
        if fix:
            f.write_text("".join(new))
    for m in misses:
        print(m)
    if misses and not fix:
        print(f"\n{len(misses)} values off the scale. Run python3 scripts/check_scale.py --fix, then look at the pages.")
        sys.exit(1)
    if fix:
        print(f"snapped {len(misses)} values")


if __name__ == "__main__":
    main()
