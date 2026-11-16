#!/usr/bin/env python3
"""Fail on viewport-height units (vh, svh, dvh, lvh) in src/.

In-app browsers resize the web view when their header collapses, which
changes every viewport unit mid-scroll and makes the page jump. Sizes use
var(--svh, 1svh) instead: 1svh measured once by the script in
src/layouts/Base.astro and refreshed only when the width changes.

    python3 scripts/check_viewport.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UNIT = re.compile(r"\d[sdl]?vh\b")
OK = "var(--svh, 1svh)"
DEFINES = ROOT / "src/layouts/Base.astro"  # measures 100svh to set --svh

bad = []
for path in sorted((ROOT / "src").rglob("*")):
    if path.suffix not in {".astro", ".css", ".ts"} or path == DEFINES:
        continue
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if UNIT.search(line.replace(OK, "")):
            bad.append(f"{path.relative_to(ROOT)}:{n}: {line.strip()}")

if bad:
    print("Viewport-height units; use calc(N * var(--svh, 1svh)):", *bad, sep="\n  ")
    sys.exit(1)
