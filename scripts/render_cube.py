"""Pack the GASS H I cube of the LMC for the browser cube viewer.

Reads the 301x301 GASS III cube (Galactic CAR grid, 224 channels, 182-366 km/s
LSR), resamples it bilinearly onto the site's equatorial TAN field at
the cube's own pixel size (151x151 px of 0.08 deg, so no resolution is lost),
drops the channels above 340 km/s (noise only), quantises Tb to Int16 and writes
  public/sky/cube/hi.i16.gz   byte-shuffled Int16 (high bytes, then low bytes),
                              order [v][y][x] with y = 0 at the south edge
  src/data/cube.json          grid, velocity axis, scale, and checked numbers
Run: python3 scripts/render_cube.py
"""
import gzip
import json
import sys
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from scipy.ndimage import map_coordinates

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_lmc as rl  # noqa: E402
from facts import FACTS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = rl.DATA
CUBE = DATA / "exp_raw/gass_279_-33_LMC_range_1444812272.fits"
VMAX = 340.0          # above this the GASS channels are noise
STEP = 0.04           # K per Int16 count, about one noise sigma (0.04 K)
N = 151
GRID = FACTS["grid"]
FIELD = GRID["naxis"] * GRID["cdelt_deg"]   # deg, the site grid width
D_KPC = FACTS["lmc"]["distance_pc"] / 1000
CRVAL = tuple(GRID["crval_deg"])

pix = FIELD / N
# CRVAL sits off the field centre by the grid's own CRPIX offset
tan = rl.tan_wcs("icrs", CRVAL, N, pix, crpix=(N + 1) / 2 - ((GRID["naxis"] + 1) / 2 - GRID["crpix"]) * GRID["cdelt_deg"] / pix, radesys=None)

with fits.open(CUBE) as h:
    hdr, cube = h[0].header, np.asarray(h[0].data, dtype=np.float32)
v = hdr["CRVAL3"] + (np.arange(cube.shape[0]) + 1 - hdr["CRPIX3"]) * hdr["CDELT3"]
src = WCS(hdr).celestial
keep = v <= VMAX
cube, v = cube[keep], v[keep]
dv = float(hdr["CDELT3"])

yy, xx = np.mgrid[0:N, 0:N]
sky = tan.pixel_to_world(xx.ravel(), yy.ravel()).galactic
sx, sy = src.world_to_pixel(sky)
assert np.all((sx >= 0) & (sx <= 300) & (sy >= 0) & (sy <= 300)), "field leaves the cube"
coords = np.array([sy, sx])
out = np.stack([map_coordinates(np.nan_to_num(c), coords, order=1).reshape(N, N) for c in cube])

q = np.clip(np.round(out / STEP), -32768, 32767).astype("<i2")
raw = q.view(np.uint8).reshape(-1, 2)
packed = np.concatenate([raw[:, 1], raw[:, 0]]).tobytes()
gz = gzip.compress(packed, 9, mtime=0)  # the default stamps the current time in the header
(ROOT / "public/sky/cube").mkdir(parents=True, exist_ok=True)
(ROOT / "public/sky/cube/hi.i16.gz").write_bytes(gz)

tb = q.astype(np.float32) * STEP
nhi = 1.823e18 * tb.sum(0) * abs(dv)
area_cm2 = (D_KPC * 3.0857e21 * np.deg2rad(pix)) ** 2
m_h = 1.6735e-24 / 1.989e33
mass = float((nhi * area_cm2 * m_h)[nhi > 0].sum())
spec = tb.sum(axis=(1, 2))
gl, gb = sky.l.deg.reshape(N, N), sky.b.deg.reshape(N, N)
meta = {
    "n": N, "nv": int(len(v)), "v0": round(float(v[0]), 4), "dv": round(abs(dv), 5), "step": STEP,
    "pix_deg": round(pix, 6), "crval": CRVAL, "crpix": float(tan.wcs.crpix[0]), "beam_arcmin": 16,
    "d_kpc": D_KPC, "bytes_gz": len(gz), "tb_max": round(float(tb.max()), 1),
    "noise_k": round(float(np.std(tb[-15:])), 3),
    "peak_v_kms": round(float(v[spec.argmax()]), 1),
    "mass_msun": mass,
    "gal_l_range": [round(float(gl.min()), 2), round(float(gl.max()), 2)],
    "gal_b_range": [round(float(gb.min()), 2), round(float(gb.max()), 2)],
}
(ROOT / "src/data/cube.json").write_text(json.dumps(meta, indent=1) + "\n")
print(json.dumps(meta, indent=1))
print("raw MB", len(packed) / 1e6, "gz MB", len(gz) / 1e6)
print("Mass without He: %.2e Msun, with He x1.36: %.2e" % (mass, mass * 1.36))
