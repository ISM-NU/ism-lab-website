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

G = FACTS["grid"]
SITE_TS = (ROOT / "src" / "lib" / "sky.ts").read_text()
LY_PER_PC = float(re.search(r"LY_PER_PC = ([\d.]+)", (ROOT / "src" / "lib" / "facts.ts").read_text()).group(1))
ASTANA = re.search(r'id: "astana".*?lat: ([\d.]+), lon: ([\d.]+)', SITE_TS).groups()

SEP = "[ ,.\u00a0\u2009\u202f]?"  # thousands separators seen in the site's text
NUM_BEFORE = r"(?<![\d.,])"
NUM_AFTER = r"(?!\d|\.\d)"


def int_forms(n):
    """Regex for an integer, with or without a thousands separator."""
    s = str(int(n))
    return [NUM_BEFORE + SEP.join(re.findall(r"\d{1,3}(?=(?:\d{3})*$)", s)) + NUM_AFTER]


def sig_figs(text):
    return len(text.lstrip("-0.").replace(".", ""))


def float_forms(v, bare, unit=None):
    """Regexes for v rounded or cut to each shorter length. A form with at least
    `bare` significant figures matches on its own; one figure fewer matches only
    when `unit` (a regex) follows, so '8.2 kpc' is caught and a bare '8.2' is not."""
    places = len(repr(float(v)).partition(".")[2].rstrip("0"))
    out = {}
    for d in range(1, places + 1):
        cut = f"{abs(v):.{d + 6}f}".partition(".")
        for text in (f"{abs(v):.{d}f}", cut[0] + "." + cut[2][:d]):
            n = sig_figs(text)
            if n >= bare:
                out[text] = ""
            elif n == bare - 1 and unit and text not in out:
                out[text] = unit
    return [NUM_BEFORE + re.escape(t) + (u or "") + (NUM_AFTER if not u else "") for t, u in out.items()]


KPC = r"\s*kpc\b"
ARCMIN = r"(?:\s*arcmin\b|\s*\*\s*AM\b|['\u2032])"


def distance_forms(pc, ly_sigs=(4, 5)):
    """A distance in parsecs written as pc, kpc or (derived) light-years."""
    out = int_forms(pc) + float_forms(pc / 1000, 3, KPC)
    if pc >= 1000:
        out += [int_forms(round(pc, 3 - len(str(int(pc)))))[0]]  # 3 significant figures
    ly = pc * LY_PER_PC
    for sig in ly_sigs:
        out += int_forms(float(f"{ly:.{sig - 1}e}"))
    return out


grid_deg = G["naxis"] * G["cdelt_deg"]
grid_ly = ((grid_deg * 3.141592653589793 / 180) * FACTS["lmc"]["distance_pc"]) * LY_PER_PC
# (what, regexes): a literal that has a home elsewhere and must not be retyped.
# Every pattern is built from the value in facts.json (or sky.ts), so changing a
# value moves the check with it.
LITERALS = [
    ("LMC distance (facts.json lmc.distance_pc)", distance_forms(FACTS["lmc"]["distance_pc"])),
    ("Galactic centre distance (facts.json galactic_centre.distance_pc)", distance_forms(FACTS["galactic_centre"]["distance_pc"])),
    ("Mon OB1 distances (facts.json mon_ob1)",
     distance_forms(FACTS["mon_ob1"]["cluster_distance_pc"]) + distance_forms(FACTS["mon_ob1"]["cloud_distance_pc"])),
    ("MBM 12 distance (facts.json mbm12.distance_pc)", distance_forms(FACTS["mbm12"]["distance_pc"])),
    ("grid width or size (facts.json grid)",
     int_forms(G["naxis"]) + float_forms(grid_deg, 4) + float_forms(grid_deg * 60, 4)
     + float_forms(G["cdelt_deg"], 3) + [f for sig in (3, 4, 5) for f in int_forms(float(f"{grid_ly:.{sig - 1}e}"))]),
    ("grid centre (facts.json grid.crval_deg)",
     [f for v in G["crval_deg"] for f in float_forms(v, 4)] + float_forms(G["crpix"], 4)),
    ("Planck beam (facts.json planck.beam_arcmin)", float_forms(FACTS["planck"]["beam_arcmin"], 3, ARCMIN)),
    ("Astana coordinates (src/lib/sky.ts ASTANA)", [f for v in ASTANA for f in float_forms(float(v), 5)]),
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
                for what, pats in LITERALS:
                    if any(re.search(p, line) for p in pats):
                        hits.append(f"{f.relative_to(ROOT)}:{n}: {what}: {line.strip()[:90]}")
    # sky.ts is the home of the site coordinates but must not hold the others.
    for n, line in enumerate((ROOT / "src" / "lib" / "sky.ts").read_text().splitlines(), 1):
        for what, pats in LITERALS[:-1]:
            if any(re.search(p, line) for p in pats):
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
