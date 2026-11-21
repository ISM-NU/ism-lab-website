#!/usr/bin/env python3
"""Outline of Kazakhstan with the Assy-Turgen Observatory and Astana, for the
optical polarimetry page.

Reads the Natural Earth 1:50m countries GeoJSON (public domain), downloaded by hand:
    curl -L -o /tmp/ne-dl/ne50.geojson https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson
    python3 scripts/assy_map.py /tmp/ne-dl/ne50.geojson
Writes src/data/assy-map.json: an SVG path in a W-wide viewBox and the projected points.

Projection: equirectangular with x scaled by cos(48 deg), the middle latitude of
the country, so shapes near the centre keep their proportions.
"""

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W, PAD = 1000, 16
LAT0 = 48.0
# Assy-Turgen: Wikipedia, "Assy-Turgen Observatory" (43 13'31"N 77 52'18"E, 2750 m).
POINTS = {
    "assy": (77.87164, 43.22524),
    "astana": (71.4491, 51.1694),
    "almaty": (76.8897, 43.2389),
}

feats = json.loads(Path(sys.argv[1]).read_text())["features"]
kaz = next(f for f in feats if f["properties"]["ADM0_A3"] == "KAZ")["geometry"]
polys = kaz["coordinates"] if kaz["type"] == "MultiPolygon" else [kaz["coordinates"]]
k = math.cos(math.radians(LAT0))
xy = lambda lon, lat: (lon * k, -lat)
rings = [[xy(*p) for p in poly[0]] for poly in polys]
xs = [x for r in rings for x, _ in r]
ys = [y for r in rings for _, y in r]
s = (W - 2 * PAD) / (max(xs) - min(xs))
H = round((max(ys) - min(ys)) * s + 2 * PAD)
tx = lambda x, y: (round((x - min(xs)) * s + PAD, 1), round((y - min(ys)) * s + PAD, 1))
path = " ".join("M" + "L".join(f"{a:g},{b:g}" for a, b in (tx(*p) for p in r)) + "Z" for r in rings)
pts = {n: dict(zip("xy", tx(*xy(*ll)))) for n, ll in POINTS.items()}
out = ROOT / "src/data/assy-map.json"
out.write_text(json.dumps({"width": W, "height": H, "path": path, "points": pts}))
print(out, W, H, len(path), pts)
