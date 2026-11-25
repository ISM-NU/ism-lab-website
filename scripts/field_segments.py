"""Planck 353 GHz field orientation as beam-spaced segments for SVG overlays.

Shared by render_mon.py and render_gc.py. At each point of a regular grid
spaced by one beam, Q and U are averaged over the native HEALPix pixels with
a Gaussian kernel, and the noise is propagated from the PR4 per-pixel
covariances with the squared weights (white noise between pixels assumed, so
the sigma is a lower bound). Nothing is smoothed as an angle.

Conventions: Planck maps are COSMO, so U and the QU covariance change sign
for IAU. psi = 0.5 atan2(U, Q) is the polarization angle from Galactic north
towards increasing l; the plane-of-sky field is psi + 90 deg. The angle is
then turned into an angle on the image grid with render_lmc.grid_angle().
"""

import sys
from pathlib import Path

import healpy as hp
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
import astropy.units as u

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_lmc as rl  # noqa: E402
from facts import FACTS  # noqa: E402

# Planck 2018 results III (2020A&A...641A...3P): effective beam FWHM at 353 GHz.
PLANCK_BEAM = FACTS["planck"]["beam_arcmin"]


def load():
    """Q and U (RING, K_CMB, COSMO) via read_planck, plus QQ, QU, UU covariances."""
    _, q, u_ = rl.read_planck()
    cols = {"QQ_COV": 7, "QU_COV": 8, "UU_COV": 9}  # 0-based field index of the TTYPE
    with fits.open(rl.PLANCK, memmap=True) as h:
        names = [h[1].header[f"TTYPE{i + 1}"].strip() for i in range(h[1].header["TFIELDS"])]
    for k, i in cols.items():
        assert names[i] == k, (k, names)
    qq, qu, uu = hp.read_map(rl.PLANCK, field=tuple(cols.values()), dtype=np.float64)
    return dict(Q=q.astype(np.float64), U=u_.astype(np.float64), QQ=qq, QU=qu, UU=uu, nside=hp.get_nside(q))


def sample(m, lon, lat, kernel_fwhm_arcmin):
    """Kernel-weighted Q, U (IAU) and their covariance at each (lon, lat) in Galactic degrees."""
    sig = np.radians(kernel_fwhm_arcmin / 60) / np.sqrt(8 * np.log(2))
    out = np.zeros((len(lon), 5))
    for k, (l, b) in enumerate(zip(lon, lat)):
        v0 = hp.ang2vec(l, b, lonlat=True)
        pix = hp.query_disc(m["nside"], v0, 3 * sig + np.radians(2 / 60), inclusive=True)
        d = np.arccos(np.clip(np.array(hp.pix2vec(m["nside"], pix)).T @ np.asarray(v0), -1, 1))
        w = np.exp(-0.5 * (d / sig) ** 2)
        w /= w.sum()
        Q = w @ m["Q"][pix]
        U = rl.cosmo_to_iau(w @ m["U"][pix])
        cqq = (w * w) @ m["QQ"][pix]
        cuu = (w * w) @ m["UU"][pix]
        cqu = rl.cosmo_to_iau((w * w) @ m["QU"][pix])
        out[k] = Q, U, cqq, cuu, cqu
    return out


def field_pa(s):
    """Field position angle (rad, Galactic, east of north) and its 1-sigma uncertainty (deg)."""
    Q, U, cqq, cuu, cqu = s.T
    psi = 0.5 * np.arctan2(U, Q)
    p2 = Q * Q + U * U
    sig = 0.5 * np.sqrt(np.clip(Q * Q * cuu + U * U * cqq - 2 * Q * U * cqu, 0, None)) / p2
    return psi + np.pi / 2, np.degrees(sig)


def segments(m, wcs, n, spacing_px, kernel_fwhm_arcmin, sigma_max_deg=10.0):
    """Segments on a grid spaced by spacing_px image pixels (centred cells).

    Returns a list of dicts with SVG coordinates on a 1000 x 1000 viewBox (y down,
    matching the composites, which are saved with north up), the grid angle in
    degrees (step (-sin a, -cos a) in SVG), the Galactic and equatorial position
    angles and sigma_psi. Points with sigma_psi above sigma_max_deg are dropped.
    """
    k = int(n // spacing_px)
    off = (n - k * spacing_px) / 2
    c = off + spacing_px * (np.arange(k) + 0.5) - 0.5  # 0-based pixel centres
    xx, yy = np.meshgrid(c, c)
    sky = wcs.pixel_to_world(xx.ravel(), yy.ravel())
    gal = sky.galactic
    s = sample(m, gal.l.deg, gal.b.deg, kernel_fwhm_arcmin)
    pa, sig = field_pa(s)
    # Grid angle: the same step-and-project as render_lmc.grid_angle(), done inline because
    # the cell centres fall between pixels (spacing is not an integer number of pixels) and
    # grid_angle() evaluates every pixel of a whole grid.
    to = gal.directional_offset_by(pa * u.rad, 2 * u.arcmin)
    x2, y2 = wcs.world_to_pixel(to)
    a = np.arctan2(-(x2 - xx.ravel()), y2 - yy.ravel())
    # Equatorial PA of the same direction, for comparison with papers in RA/Dec.
    pa_eq = sky.icrs.position_angle(to.icrs).to_value(u.deg) % 180
    out = []
    for i in range(len(pa)):
        if not np.isfinite(sig[i]) or sig[i] > sigma_max_deg:
            continue
        out.append(dict(
            x=round(float((xx.ravel()[i] + 0.5) / n * 1000), 2),
            y=round(float((1 - (yy.ravel()[i] + 0.5) / n) * 1000), 2),
            a=round(float(np.degrees(a[i])), 2),
            pa_gal=round(float(np.degrees(pa[i]) % 180), 2),
            pa_eq=round(float(pa_eq[i]), 2),
            sig=round(float(sig[i]), 2),
        ))
    return out, s, gal


def to_svg(wcs, n, coords):
    """SkyCoord (any frame) to SVG points on the 1000-unit viewBox."""
    x, y = wcs.world_to_pixel(coords)
    return [[round(float((xi + 0.5) / n * 1000), 1), round(float((1 - (yi + 0.5) / n) * 1000), 1)] for xi, yi in zip(np.atleast_1d(x), np.atleast_1d(y))]


def north_east(wcs, n, lon, lat, frame="icrs"):
    """SVG step directions of celestial north and east at a Galactic point."""
    p = SkyCoord(lon * u.deg, lat * u.deg, frame="galactic").icrs
    x0, y0 = wcs.world_to_pixel(p)
    res = {}
    for name, ang in (("N", 0), ("E", 90)):
        q = p.directional_offset_by(ang * u.deg, 5 * u.arcmin)
        x1, y1 = wcs.world_to_pixel(q)
        v = np.array([x1 - x0, -(y1 - y0)], dtype=float)
        v /= np.hypot(*v)
        res[name] = [round(float(v[0]), 4), round(float(v[1]), 4)]
    return res
