"""Mon OB1 East: Planck field segments and the regions of Alina et al. 2022.

Writes src/data/mon-ob1.json for src/components/MonOB1.astro, which draws it
as SVG over the existing composite public/sky/comp-monoceros_ob1-*.webp
(grid from scripts/composites.py REGIONS["monoceros_ob1"]: GLON-TAN centred
at l=202.9, b=1.9, 3 deg wide, 2048 px).

Field: Planck PR4 353 GHz Q and U, kernel-averaged to an effective FWHM of
7' (the resolution Alina et al. 2022 used with PR3), one segment per 7' cell,
kept where sigma_psi < 10 deg (their selection, sec. 2.1 and Fig. 1).

    flock /tmp/ism-planck.lock python3 scripts/render_mon.py
"""

import json
import sys
from pathlib import Path

import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u

sys.path.insert(0, str(Path(__file__).resolve().parent))
import composites as cp  # noqa: E402
import field_segments as fs  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "data" / "mon-ob1.json"
FWHM = 7.0  # arcmin, effective
DIST_PC = 723  # Alina et al. 2022 sec. 1, from Cantat-Gaudin et al. 2018

# Outlines in J2000 RA, Dec (deg), digitised from the arXiv figures of Alina et
# al. 2022 (arXiv:2007.15344) against their axis ticks; good to about 1'.
#   north_main     Fig. 6 white contour, traced from the image colour.
#   north_western  Fig. 6 yellow contour, north_eastern Fig. 6 red contour: traced
#                  by hand (the circles drawn over them break a colour trace); the
#                  small unassigned pocket inside the red contour is not cut out.
#                  Fig. 6 ticks: RA 6h41m00s at x=426 px, 199 px per 60 s of RA;
#                  Dec 11d15' at y=165 px, 200.5 px per 15'.
#   shock_north    Fig. 9b (12CO smoothed to 7'), yellow pattern. Ticks: RA 6h41m00s at
#                  x=314 px, 181.5 px per 60 s; Dec 10d00' at y=1104 px, 246.5 px per 20'.
#   rect_A/B       Fig. 12 rectangles A and B, corners read by eye. Ticks: RA 6h48m at
#                  x=281.5 px, 236 px per 2 min; Dec 10d00' at y=18.5 px, 159 px per 20'.
REGIONS = {
    "north_main": [(100.220, 10.006), (100.538, 10.008), (100.543, 10.013), (100.543, 10.110), (100.520, 10.133), (100.484, 10.133), (100.470, 10.150), (100.454, 10.148), (100.442, 10.158), (100.442, 10.216), (100.469, 10.244), (100.502, 10.243), (100.540, 10.207), (100.606, 10.208), (100.611, 10.214), (100.611, 10.277), (100.572, 10.307), (100.577, 10.314), (100.577, 10.361), (100.542, 10.392), (100.543, 10.411), (100.527, 10.426), (100.527, 10.450), (100.535, 10.458), (100.552, 10.456), (100.561, 10.464), (100.561, 10.493), (100.543, 10.509), (100.543, 10.528), (100.538, 10.534), (100.523, 10.534), (100.509, 10.518), (100.467, 10.518), (100.459, 10.526), (100.459, 10.544), (100.452, 10.551), (100.417, 10.550), (100.386, 10.584), (100.366, 10.584), (100.357, 10.592), (100.357, 10.612), (100.352, 10.617), (100.337, 10.617), (100.331, 10.612), (100.331, 10.575), (100.313, 10.560), (100.313, 10.540), (100.305, 10.532), (100.231, 10.534), (100.223, 10.542), (100.223, 10.566), (100.239, 10.580), (100.239, 10.610), (100.232, 10.617), (100.212, 10.617), (100.204, 10.625), (100.205, 10.644), (100.182, 10.667), (100.163, 10.667), (100.148, 10.684), (100.102, 10.684), (100.095, 10.678), (100.095, 10.646), (100.111, 10.633), (100.114, 10.612), (100.103, 10.600), (100.084, 10.601), (100.077, 10.594), (100.077, 10.564), (100.095, 10.549), (100.095, 10.530), (100.111, 10.516), (100.111, 10.413), (100.118, 10.408), (100.137, 10.408), (100.168, 10.374), (100.188, 10.374), (100.198, 10.358), (100.190, 10.350), (100.137, 10.350), (100.129, 10.345), (100.129, 10.280), (100.136, 10.273), (100.154, 10.273), (100.163, 10.259), (100.119, 10.217), (100.102, 10.217), (100.095, 10.210), (100.095, 10.175), (100.077, 10.160), (100.077, 10.114), (100.134, 10.057), (100.154, 10.056), (100.168, 10.040), (100.204, 10.041), (100.213, 10.032), (100.220, 10.006)],
    "north_western": [(100.376, 11.114), (100.360, 11.113), (100.360, 11.102), (100.344, 11.099), (100.342, 11.069), (100.310, 11.069), (100.308, 11.082), (100.273, 11.082), (100.271, 11.068), (100.171, 11.066), (100.170, 11.050), (100.135, 11.048), (100.134, 10.996), (100.170, 10.993), (100.168, 10.967), (100.135, 10.964), (100.133, 10.932), (100.117, 10.930), (100.116, 10.915), (100.100, 10.912), (100.099, 10.845), (100.170, 10.844), (100.170, 10.815), (100.185, 10.812), (100.186, 10.795), (100.225, 10.794), (100.226, 10.826), (100.241, 10.827), (100.243, 10.842), (100.257, 10.844), (100.259, 10.860), (100.274, 10.862), (100.275, 10.896), (100.290, 10.898), (100.292, 10.927), (100.373, 10.928), (100.376, 10.944), (100.392, 10.947), (100.393, 11.044), (100.411, 11.047), (100.412, 11.060), (100.377, 11.062)],
    "north_eastern": [(100.464, 11.264), (100.443, 11.266), (100.442, 11.282), (100.377, 11.284), (100.376, 11.316), (100.342, 11.316), (100.341, 11.299), (100.289, 11.299), (100.288, 11.281), (100.272, 11.280), (100.271, 11.219), (100.223, 11.218), (100.221, 11.169), (100.204, 11.168), (100.202, 11.152), (100.185, 11.150), (100.185, 11.112), (100.204, 11.112), (100.205, 11.093), (100.254, 11.093), (100.256, 11.082), (100.273, 11.082), (100.308, 11.082), (100.310, 11.069), (100.342, 11.069), (100.344, 11.099), (100.360, 11.102), (100.360, 11.113), (100.376, 11.114), (100.377, 11.062), (100.377, 10.927), (100.409, 10.927), (100.411, 10.943), (100.427, 10.944), (100.430, 10.962), (100.455, 10.960), (100.459, 10.927), (100.491, 10.927), (100.493, 10.944), (100.514, 10.948), (100.515, 10.976), (100.531, 10.979), (100.531, 11.150), (100.515, 11.152), (100.514, 11.166), (100.498, 11.168), (100.496, 11.199), (100.481, 11.200), (100.479, 11.216), (100.464, 11.218)],
    "shock_north": [(100.210, 10.986), (100.234, 10.992), (100.284, 11.027), (100.349, 11.049), (100.358, 11.066), (100.358, 11.101), (100.346, 11.122), (100.349, 11.145), (100.382, 11.206), (100.387, 11.229), (100.404, 11.251), (100.404, 11.263), (100.391, 11.268), (100.393, 11.274), (100.345, 11.264), (100.339, 11.273), (100.345, 11.295), (100.327, 11.264), (100.301, 11.265), (100.292, 11.258), (100.292, 11.237), (100.271, 11.230), (100.254, 11.203), (100.240, 11.214), (100.231, 11.215), (100.225, 11.206), (100.221, 11.214), (100.208, 11.213), (100.221, 11.199), (100.230, 11.198), (100.259, 11.155), (100.259, 11.133), (100.243, 11.118), (100.214, 11.112), (100.206, 11.097), (100.192, 11.096), (100.179, 11.079), (100.199, 11.076), (100.204, 11.081), (100.209, 11.064), (100.217, 11.069), (100.225, 11.066), (100.209, 11.049), (100.184, 11.051), (100.185, 11.041), (100.175, 11.040), (100.172, 11.016), (100.210, 10.986)],
    "rect_A": [(101.880, 9.385), (101.406, 9.947), (100.601, 9.280), (101.077, 8.718)],
    "rect_B": [(100.931, 8.894), (100.321, 8.894), (100.321, 8.559), (100.931, 8.559)],
}

# Table 1 of Alina et al. 2022: <Bt^2>/<B0^2>, B_0,POS (uG) and lambda, for
# n = 10^2 cm^-3 (sec. 3.2). The text rounds North-Main to "around 17 uG".
TABLE = {
    "north_main": dict(name="North-Main", ratio="0.14", b="16.0 ± 2.5", lam="0.95 ± 0.41"),
    "north_western": dict(name="North-Western", ratio="0.67", b="5.1 ± 0.9", lam="2.55 ± 0.57"),
    "north_eastern": dict(name="North-Eastern", ratio="0.11", b="6.5 ± 1.1", lam="1.40 ± 0.38"),
}
OTHER = {
    "shock_north": "Candidate shock",
    "rect_A": "A",
    "rect_B": "B",
}

# SIMBAD position of the cluster (via Sesame): 06 40 52.1 +09 52 37.
NGC2264 = (100.21708333, 9.87694444)


def build(m):
    r = cp.REGIONS["monoceros_ob1"]
    n = r["n"]
    wcs = cp.target_wcs(r)
    pix_arcmin = r["fov"] / n * 60
    kernel = float(np.sqrt(FWHM**2 - fs.PLANCK_BEAM**2))
    segs, _, _ = fs.segments(m, wcs, n, FWHM / pix_arcmin, kernel)
    regions = []
    for k, pts in REGIONS.items():
        c = SkyCoord([p[0] for p in pts] * u.deg, [p[1] for p in pts] * u.deg, frame="icrs")
        svg = fs.to_svg(wcs, n, c)
        entry = dict(id=k, points=svg)
        entry.update(TABLE.get(k, {"name": OTHER.get(k, k)}))
        # Mean field PA (equatorial) inside the outline, for the report and checks.
        inside = [s for s in segs if _inside(s["x"], s["y"], svg)]
        if inside:
            a = np.radians([s["pa_eq"] for s in inside]) * 2
            entry["pa_eq_mean"] = round(float(np.degrees(np.arctan2(np.sin(a).mean(), np.cos(a).mean())) / 2), 1)
            entry["n_seg"] = len(inside)
        regions.append(entry)
    ngc = fs.to_svg(wcs, n, SkyCoord(*NGC2264, unit="deg", frame="icrs"))[0]
    data = dict(
        image="/sky/comp-monoceros_ob1-1920.webp",
        image_small="/sky/comp-monoceros_ob1-960.webp",
        fov_deg=r["fov"],
        centre_gal=list(r["centre"]),
        fwhm_arcmin=FWHM,
        beam_r=round(FWHM / 2 / (r["fov"] * 60) * 1000, 2),
        seg_len=round(FWHM / (r["fov"] * 60) * 1000 * 0.8, 2),
        dist_pc=DIST_PC,
        compass=fs.north_east(wcs, n, r["centre"][0], r["centre"][1]),
        segments=segs,
        regions=regions,
        ngc2264=ngc,
    )
    OUT.write_text(json.dumps(data, separators=(",", ":")) + "\n")
    print(f"mon: {len(segs)} segments", {e["id"]: e.get("pa_eq_mean") for e in regions})


def _inside(x, y, poly):
    """Even-odd point in polygon."""
    c = False
    for i in range(len(poly)):
        x1, y1 = poly[i - 1]
        x2, y2 = poly[i]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


if __name__ == "__main__":
    build(fs.load())
