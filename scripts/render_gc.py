"""Galactic centre: Planck field segments and the PILOT mean orientation.

Writes src/data/gc-field.json for src/components/GalacticCentre.astro, drawn
as SVG over public/sky/comp-galactic_centre-*.webp (scripts/composites.py
REGIONS["galactic_centre"]: GLON-TAN at l=0, b=0, 2 deg wide, 2048 px).

Field: Planck PR4 353 GHz Q and U averaged over native pixels with a 1.7'
kernel (one HEALPix pixel), so the segments sit at about the 5' beam, one per
beam cell, kept where sigma_psi < 10 deg.

PILOT (Mangilli et al. 2019, 2019A&A...630A..74M): polarization angle about
+22 deg in GAL-COSMO (clockwise from Galactic north), i.e. a plane-of-sky
field "tilted clockwise to the trace of the Galactic plane by ~+22 deg"
(their sec. 7). In the IAU sense (east of Galactic north) the field PA is
90 - 22 = 68 deg: the line rises towards positive l, to the upper left.

    flock /tmp/ism-planck.lock python3 scripts/render_gc.py
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
from facts import FACTS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "data" / "gc-field.json"
KERNEL = 1.7  # arcmin
PILOT_TILT = 22.0  # deg clockwise from the Galactic plane (Mangilli et al. 2019)
DIST_PC = FACTS["galactic_centre"]["distance_pc"]


def build(m):
    r = cp.REGIONS["galactic_centre"]
    n = r["n"]
    wcs = cp.target_wcs(r)
    pix_arcmin = r["fov"] / n * 60
    fwhm = float(np.hypot(fs.PLANCK_BEAM, KERNEL))
    segs, s, gal = fs.segments(m, wcs, n, fwhm / pix_arcmin, KERNEL)

    # Planck mean over the frame from the summed Stokes parameters, for comparison.
    Q, U = s[:, 0].sum(), s[:, 1].sum()
    pa_mean = (np.degrees(0.5 * np.arctan2(U, Q)) + 90) % 180
    tilt_planck = 90 - pa_mean  # clockwise from the plane, same sense as PILOT

    # PILOT mean orientation through Sgr A* (frame centre), as a grid angle.
    c = SkyCoord(0 * u.deg, 0 * u.deg, frame="galactic")
    pa = np.radians(90 - PILOT_TILT)
    x0, y0 = wcs.world_to_pixel(c)
    x1, y1 = wcs.world_to_pixel(c.directional_offset_by(pa * u.rad, 2 * u.arcmin))
    a_line = float(np.degrees(np.arctan2(-(x1 - x0), y1 - y0)))

    data = dict(
        image="/sky/comp-galactic_centre-1920.webp",
        image_small="/sky/comp-galactic_centre-960.webp",
        fov_deg=r["fov"],
        fwhm_arcmin=round(fwhm, 2),
        beam_r=round(fwhm / 2 / (r["fov"] * 60) * 1000, 2),
        seg_len=round(fwhm / (r["fov"] * 60) * 1000 * 0.8, 2),
        dist_pc=DIST_PC,
        pilot=dict(tilt=PILOT_TILT, a=round(a_line, 2), centre=fs.to_svg(wcs, n, c)[0]),
        planck_mean_tilt=round(float(tilt_planck), 1),
        segments=segs,
    )
    OUT.write_text(json.dumps(data, separators=(",", ":")) + "\n")
    print(f"gc: {len(segs)} segments, Planck mean tilt {tilt_planck:.1f} deg clockwise from the plane, PILOT line grid angle {a_line:.1f}")


if __name__ == "__main__":
    m = fs.load()
    build(m)
    if "--mon" in sys.argv:
        import render_mon

        render_mon.build(m)
