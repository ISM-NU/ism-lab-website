#!/usr/bin/env python3
"""Keep each shared fact typed once, in src/data/facts.json (or src/lib/sky.ts for sites).

Fails when source files outside the facts file spell out one of its values
again, and when a card's sky field drifts from the grid it shows. Generated
JSON under src/data and prose docs are not scanned.

    python3 scripts/check_facts.py
"""

import re
import sys
from math import asin, atan2, cos, degrees, radians, sin
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from facts import FACTS  # noqa: E402

# (what, pattern): a literal that has a home elsewhere and must not be retyped.
G = FACTS["grid"]
LITERALS = [
    ("LMC distance (facts.json lmc.distance_pc)", r"(?<![\d.])49[ ,.]?59\d*(?![\d])|(?<![\d.])49\.6(?!\d)"),
    ("Galactic centre distance (facts.json galactic_centre.distance_pc)", r"(?<![\d.])8[ .]?178(?![\d])"),
    ("Mon OB1 distances (facts.json mon_ob1)", r"(?<![\d.])(?:723|745)(?![\d.])"),
    ("grid width or size (facts.json grid)", r"(?<![\d.])(?:12\.0[78]\d*|1087|0\.011111\d*)(?![\d])"),
    ("grid centre (facts.json grid.crval_deg)", r"(?<![\d.])(?:81\.189\d*|68\.526\d*|68\.5259\d*|543\.75)(?![\d])"),
    ("Planck beam (facts.json planck.beam_arcmin)", r"(?<![\d.])4\.94(?![\d])|(?<![\d.])4\.9(?=['′])"),
    ("Astana coordinates (src/lib/sky.ts ASTANA)", r"(?<![\d.])(?:71\.398\d*|51\.090\d*)(?![\d])"),
]
SCAN = [ROOT / "src", ROOT / "scripts"]
SUFFIXES = {".py", ".ts", ".astro", ".mjs", ".md"}
SKIP = {ROOT / "scripts" / "check_facts.py", ROOT / "src" / "lib" / "sky.ts"}


def literal_hits():
    hits = []
    for base in SCAN:
        for f in sorted(base.rglob("*")):
            if f.suffix not in SUFFIXES or f in SKIP or "__pycache__" in f.parts:
                continue
            for n, line in enumerate(f.read_text().splitlines(), 1):
                for what, pat in LITERALS:
                    if re.search(pat, line):
                        hits.append(f"{f.relative_to(ROOT)}:{n}: {what}: {line.strip()[:90]}")
    # sky.ts is the home of the site coordinates but must not hold the others.
    for n, line in enumerate((ROOT / "src" / "lib" / "sky.ts").read_text().splitlines(), 1):
        for what, pat in LITERALS[:-1]:
            if re.search(pat, line):
                hits.append(f"src/lib/sky.ts:{n}: {what}: {line.strip()[:90]}")
    return hits


def galactic(ra, dec):
    """ICRS to Galactic, degrees (J2000 pole at 192.85948, 27.12825; node at l = 122.93192)."""
    ag, dg, ln = radians(192.85948), radians(27.12825), radians(122.93192)
    a, d = radians(ra), radians(dec)
    b = asin(sin(d) * sin(dg) + cos(d) * cos(dg) * cos(a - ag))
    l = ln - atan2(cos(d) * sin(a - ag), sin(d) * cos(dg) - cos(d) * sin(dg) * cos(a - ag))
    return degrees(l) % 360, degrees(b)


def field_problems():
    """The LMC card field is the grid rounded; the other fields are read by scripts."""
    f = FACTS["fields"]["lmc"]
    l, b = galactic(*G["crval_deg"])
    width = G["naxis"] * G["cdelt_deg"]
    out = []
    if abs(f["l"] - l) > 0.05 or abs(f["b"] - b) > 0.05:
        out.append(f"facts.json fields.lmc is l {f['l']}, b {f['b']} but the grid centre is l {l:.2f}, b {b:.2f}")
    if abs(f["width"] - width) > 0.05:
        out.append(f"facts.json fields.lmc.width is {f['width']} but the grid is {width:.2f} deg wide")
    return out


def main():
    problems = literal_hits() + field_problems()
    for p in problems:
        print(p)
    if problems:
        print(f"\n{len(problems)} shared facts typed outside facts.json. Read the value from facts.json (scripts/facts.py, src/lib/facts.ts).")
        sys.exit(1)


if __name__ == "__main__":
    main()
