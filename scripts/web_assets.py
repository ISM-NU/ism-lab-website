"""Turn the render_lmc.py outputs into the files the site loads.

Reads assets/lmc/ (from render_lmc.py) and writes:
  public/sky/*.webp      images for the canvas pieces and research pages
  src/data/sky.json      field-angle grid, target positions, LMC position and
                         orientation on the all-sky map, H I spectrum

Run after render_lmc.py: python3 scripts/web_assets.py
"""

import json
from pathlib import Path

import healpy as hp
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "lmc"
OUT = ROOT / "public" / "sky"
DATA = ROOT / "src" / "data" / "sky.json"

FIELD_N = 96  # field-angle grid the dot field samples
ALLSKY_W = 2400  # must match render_lmc.allsky width
LMC_CENTRE = SkyCoord(ra=80.894 * u.deg, dec=-69.756 * u.deg)
TARGETS = {
    "30 Doradus": "05h38m42s -69d06m03s",
    "N11": "04h56m49s -66d24m00s",
    "N44": "05h22m05s -67d56m00s",
    "N159": "05h39m50s -69d45m00s",
    "N79": "04h52m00s -69d22m00s",
}
IMAGES = {
    "allsky_bfield.png": ("allsky.webp", 2000),
    "hi_column_color.jpg": ("lmc-hi.webp", 1000),
    "hi_velocity.jpg": ("lmc-vel.webp", 1000),
    "co_clouds.png": ("lmc-co.webp", 1000),
    "dust_353.jpg": ("lmc-dust.webp", 1000),
    "bfield_on_dust.jpg": ("lmc-bfield.webp", 1000),
    "bfield_lic.jpg": ("lmc-lic.webp", 1000),
}
REGIONS = ["orion", "monoceros_ob1", "galactic_centre", "taurus", "mbm12"]


def save(src, dst, size, alpha=None):
    im = Image.open(SRC / src)
    im = im.convert("RGBA" if im.mode in ("RGBA", "LA") or alpha is not None else "RGB")
    im.thumbnail((size, size))
    if alpha is not None:
        w, h = im.size
        yy, xx = np.mgrid[0:h, 0:w]
        r = np.hypot(xx - w / 2, yy - h / 2) / (w / 2)
        a = (np.clip((1 - r) / 0.35, 0, 1) ** 1.5 * 255).astype(np.uint8)
        im.putalpha(Image.fromarray(a))
    im.save(OUT / dst, quality=80, method=6)


def grid_wcs(meta):
    h = fits.Header()
    for k, v in meta["grid"]["wcs"].items():
        h[k] = v
    return WCS(h), meta["grid"]["nx"], meta["grid"]["ny"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    meta = json.loads((SRC / "meta.json").read_text())
    for src, (dst, size) in IMAGES.items():
        save(src, dst, size)
    # Vignetted dust + field texture for the zoom: the square map edge must
    # not show. Planck (5') is sharper than the public GASS H I (16').
    save("bfield_on_dust.jpg", "lmc-bfield-v.webp", 1000, alpha=True)
    for r in REGIONS:
        save(f"region_{r}.jpg", f"region-{r}.webp", 900)
    (OUT / "channels").mkdir(exist_ok=True)
    for i, _ in enumerate(meta["channels_kms"]):
        save(f"channels/{i:02d}.jpg", f"channels/{i:02d}.webp", 640)

    # Field angle grid: circular mean in 2*theta, rows top = north.
    a = np.load(SRC / "bfield_angle.npy")
    b = a.shape[0] // FIELD_N
    blk = lambda x: x[: FIELD_N * b, : FIELD_N * b].reshape(FIELD_N, b, FIELD_N, b).mean((1, 3))
    ang = (0.5 * np.arctan2(blk(np.sin(2 * a)), blk(np.cos(2 * a))))[::-1]

    wcs, nx, ny = grid_wcs(meta)
    targets = {}
    for k, v in TARGETS.items():
        x, y = wcs.world_to_pixel(SkyCoord(v, unit=(u.hourangle, u.deg)))
        targets[k] = [round(float(x) / nx, 4), round(1 - float(y) / ny, 4)]

    # LMC position on the Mollweide all-sky map and the angle of celestial
    # north there (clockwise from up), from continuous projected coordinates.
    proj = hp.projector.MollweideProj(xsize=ALLSKY_W)

    def xy(c):
        g = c.galactic
        return proj.ang2xy(g.l.deg, g.b.deg, lonlat=True)

    # Projected x grows with image column and y grows up. Use continuous x, y:
    # xy2ij rounds to whole pixels, which snaps this angle to 90 deg.
    x0, y0 = xy(LMC_CENTRE)
    x1, y1 = xy(SkyCoord(ra=LMC_CENTRE.ra, dec=LMC_CENTRE.dec + 0.1 * u.deg))
    i, j = proj.xy2ij(x0, y0)
    rot = float(np.degrees(np.arctan2(x1 - x0, y1 - y0)))

    spec = np.asarray(meta["hi_spectrum"]["sum_K"])
    edges = np.linspace(0, len(spec), 49).astype(int)
    bars = np.array([spec[edges[k] : edges[k + 1]].mean() for k in range(48)])
    bars = (bars - bars.min()) / (bars.max() - bars.min())

    out = {
        "field_n": FIELD_N,
        "field": [round(float(v), 3) for v in ang.ravel()],
        "channels_kms": meta["channels_kms"],
        "lmc_in_allsky": [round(float(j) / ALLSKY_W, 4), round(1 - float(i) / (ALLSKY_W / 2), 4)],
        "lmc_rot_deg": round(rot, 1),
        "hi_spectrum": [round(float(v), 3) for v in bars],
        "hi_range_kms": [round(meta["hi_spectrum"]["v_kms"][0]), round(meta["hi_spectrum"]["v_kms"][-1])],
        "lmc_targets": targets,
        "sources": meta["sources"],
    }
    DATA.write_text(json.dumps(out, separators=(",", ":")))
    print({k: out[k] for k in ("lmc_in_allsky", "lmc_rot_deg", "hi_range_kms", "lmc_targets")})


if __name__ == "__main__":
    main()
