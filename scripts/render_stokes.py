"""Stokes I, Q, U textures of the LMC for the in-browser field renderer, and a
re-derivation of the Milky Way foreground following Alina et al. 2023
(2023MNRAS.518.4466A, "the paper" below).

Outputs
  public/sky/stokes/*.png  16-bit greyscale PNG planes, top row = north edge
  src/data/stokes.json     plane scale/offset, foreground parameters, H I
                           contours, foreground starlight, validation numbers

Frame. Q and U are IAU (U of the COSMO maps negated) and referenced to the
grid's vertical axis, not to local north: the angle psi = 0.5 atan2(U, Q) is
measured on the pixel grid from up towards left (east). Local north tilts by up
to 20 deg on this 12 deg TAN grid (render_lmc.north_tilt); rotating Q and U into
the grid frame before smoothing removes that, so the shader draws psi directly.
The sky position angle is psi - tilt, with the tilt map in sky.json.

Inputs (LMC_DATA, required)
  external/HFI_SkyMap_353-BPassCorrected_2048_R4.00_full.fits   Planck PR4
  external/hi4pi/parts/*  rows of the HI4PI N_HI HEALPix table (LAMBDA,
      https://lambda.gsfc.nasa.gov/data/foregrounds/HI4PI/NHI_HPX.fits),
      cut to Galactic latitudes -50..-14 by HTTP range requests: the table has
      48-byte rows in RING order after a 5760-byte header, so rows
      7800832..11117060 are bytes 5760+48*7800832 .. 5760+48*11117060+47:
        curl -r <start>-<end> -o parts/part00 <url>; echo "<start> <end>" > parts/range_bytes
      (any split into several part files works; they are concatenated in order)
  exp_raw/gass_279_-33_LMC_range_1444812272.fits  GASS III, 182-366 km/s LSR
  $STARLIGHT_DIR/*_j2000.txt, the foreground starlight catalogues (required)

Run (loads the full-sky Planck map once, then caches the cut-outs):
  flock /tmp/ism-planck.lock env LMC_DATA=... STARLIGHT_DIR=... python3 scripts/render_stokes.py
"""

import json
import os
import sys
from pathlib import Path

import healpy as hp
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
from PIL import Image
from reproject import reproject_from_healpix, reproject_interp
from scipy.ndimage import gaussian_filter, map_coordinates

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_lmc as rl  # noqa: E402
from facts import FACTS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = rl.DATA
CACHE = ROOT / ".cache" / "stokes"
TEX = ROOT / "public" / "sky" / "stokes"
JSON_OUT = ROOT / "src" / "data" / "stokes.json"
STARS = rl.env_path("STARLIGHT_DIR", "the folder with the *_j2000.txt starlight catalogues")
HI4PI_PARTS = DATA / "external" / "hi4pi" / "parts"
GASS_LMC = DATA / "exp_raw" / "gass_279_-33_LMC_range_1444812272.fits"

# Planck 2018 results III (2020A&A...641A...3P), table of colour corrections
# and unit conversions: 353 GHz, 287.5 MJy/sr per K_CMB (nu I_nu = const).
K2MJY = 287.5
# Same paper, effective beam FWHM at 353 GHz (solid-angle equivalent).
BEAM = FACTS["planck"]["beam_arcmin"]
# HEALPix pixel solid angle of the nside 2048 Planck maps.
OMEGA_PIX = 4 * np.pi / (12 * 2048**2)
# Smoothing scales offered on the site (total FWHM, arcmin).
SCALES = [7, 15, 30, 60]
# The paper brings Planck to the GASS resolution, 16.2' (its section 2.1-2.2).
FG_FWHM = 16.2
# N_H = 1.823e18 * int T_B dv (paper, equation 10).
XHI = 1.823e18
# Paper section 3.3: the region around the LMC used for the foreground is the
# map minus a circle of 5 deg radius around the centre of the LMC.
R_EXCL = 5.0
# Paper section 2.3: foreground stars farther than 500 pc with sigma_PA < 20 deg.
STAR_DMIN, STAR_SPA = 500.0, 20.0
# GASS H I contour levels of the paper's figures (K km/s, its Fig. 1).
HI_LEVELS = [1000, 1400, 2400, 2800]

N_WORK = 724  # work grid, ~1.0' pixels over the site grid
N_TEX = 256  # Q, U, sigma planes
N_TEX_I = 512  # dust intensity underlay
N_TEX_FG = 128  # smooth foreground intensity planes


def site_grid(n):
    """The site's grid (render_lmc.GRID) resampled to n pixels with
    the same outer edges, so textures line up with the existing images."""
    g = dict(rl.GRID)
    k = g["NAXIS1"] / n
    g.update(NAXIS1=n, NAXIS2=n, CDELT1=g["CDELT1"] * k, CDELT2=g["CDELT2"] * k,
             CRPIX1=0.5 + (g["CRPIX1"] - 0.5) / k, CRPIX2=0.5 + (g["CRPIX2"] - 0.5) / k)
    h = fits.Header()
    h.update(g)
    return WCS(h), (n, n)


def big_grid(width_deg=20.0, px_arcmin=2.0):
    """A wider TAN grid on the same tangent point, for the annulus check."""
    n = int(round(width_deg * 60 / px_arcmin))
    h = fits.Header()
    h.update(rl.GRID)
    h.update(NAXIS1=n, NAXIS2=n, CDELT1=-px_arcmin / 60, CDELT2=px_arcmin / 60,
             CRPIX1=(n + 1) / 2, CRPIX2=(n + 1) / 2)
    return WCS(h), (n, n)


def px_arcmin(wcs):
    return abs(wcs.wcs.cdelt[1]) * 60


def galactic_north_on_grid(wcs, shape):
    """Grid angle of Galactic north (from up towards left), per pixel."""
    yy, xx = np.mgrid[0 : shape[0], 0 : shape[1]]
    sky = wcs.pixel_to_world(xx.ravel(), yy.ravel())
    gal = sky.galactic
    north = SkyCoord(l=gal.l, b=gal.b + 1 * u.arcmin, frame="galactic").icrs
    pa = sky.icrs.position_angle(north).to_value(u.rad).reshape(shape)
    return rl.grid_angle(wcs, shape, pa)


def rotate(st, chi):
    """Rotate Q, U and their covariances by angle chi (psi' = psi + chi)."""
    c, s = np.cos(2 * chi), np.sin(2 * chi)
    Q, U = st["Q"], st["U"]
    QQ, UU, QU, IQ, IU = st["QQ"], st["UU"], st["QU"], st["IQ"], st["IU"]
    st["Q"], st["U"] = c * Q - s * U, s * Q + c * U
    st["QQ"] = c * c * QQ + s * s * UU - 2 * c * s * QU
    st["UU"] = s * s * QQ + c * c * UU + 2 * c * s * QU
    st["QU"] = c * s * (QQ - UU) + (c * c - s * s) * QU
    st["IQ"], st["IU"] = c * IQ - s * IU, s * IQ + c * IU
    return st


def cut_planck(grids):
    """Cut Planck I, Q, U and covariances onto each grid, in MJy/sr and the
    grid frame. Cached: the full-sky map is read once."""
    CACHE.mkdir(parents=True, exist_ok=True)
    out = {}
    todo = []
    keys = {name: rl.input_key(wcs.to_header().tostring(), shape, K2MJY, rl.PLANCK.name, rl.PLANCK.stat().st_size)
            for name, (wcs, shape) in grids.items()}
    for name in grids:
        f = CACHE / f"planck_{name}.npz"
        cached = dict(np.load(f)) if f.exists() else {}
        if str(cached.pop("key", "")) == keys[name]:
            out[name] = cached
        else:
            todo.append(name)
    if not todo:
        return out
    print("Planck full-sky read for", todo, flush=True)
    cut = lambda m, name, nested: reproject_from_healpix(
        (m, "galactic"), grids[name][0], shape_out=grids[name][1], nested=nested)[0].astype(np.float32)
    st = {n: {} for n in todo}
    i_map, q_map, u_map = rl.read_planck()  # RING, dipole removed
    for n in todo:
        st[n]["I"] = cut(i_map, n, False) * K2MJY
        st[n]["Q"] = cut(q_map, n, False) * K2MJY
        st[n]["U"] = rl.cosmo_to_iau(cut(u_map, n, False)) * K2MJY
    del i_map, q_map, u_map
    # Covariance columns (0-based fields of the FREQ-MAP table).
    cols = {"II": 4, "IQ": 5, "IU": 6, "QQ": 7, "QU": 8, "UU": 9}
    for key, field in cols.items():
        m = hp.read_map(rl.PLANCK, field=field, nest=True, dtype=np.float32)
        for n in todo:
            c = cut(m, n, True)
            st[n][key] = (rl.cosmo_to_iau(c) if key.count("U") == 1 else c) * K2MJY**2
        del m
    for n in todo:
        wcs, shape = grids[n]
        rotate(st[n], galactic_north_on_grid(wcs, shape))
        with rl.atomic(CACHE / f"planck_{n}.npz") as tmp:
            np.savez(tmp, key=keys[n], **st[n])
        out[n] = st[n]
    return out


def kernel_sigma_px(fwhm, pxa, native=BEAM):
    return np.sqrt(max(fwhm**2 - native**2, 0)) / 2.3548 / pxa


def smooth_map(x, fwhm, pxa, native=BEAM):
    s = kernel_sigma_px(fwhm, pxa, native)
    return gaussian_filter(np.nan_to_num(x), s, mode="nearest") if s > 0 else np.nan_to_num(x)


def smooth_cov(c, fwhm, pxa):
    """Noise (co)variance after smoothing with a normalised Gaussian of
    sigma s. Planck noise is white per HEALPix pixel, so
    var = Omega_pix * integral(G^2 sigma^2) = Omega_pix / (4 pi s^2) *
    (sigma^2 convolved with a Gaussian of sigma s/sqrt 2)."""
    s_arc = np.sqrt(fwhm**2 - BEAM**2) / 2.3548
    s_rad = np.deg2rad(s_arc / 60)
    return OMEGA_PIX / (4 * np.pi * s_rad**2) * gaussian_filter(np.nan_to_num(c), s_arc / pxa / np.sqrt(2), mode="nearest")


def smoothed(st, fwhm, pxa):
    sm = {k: smooth_map(st[k], fwhm, pxa) for k in ("I", "Q", "U")}
    sm.update({k: smooth_cov(st[k], fwhm, pxa) for k in ("QQ", "UU", "QU")})
    return sm


def pol(Q, U, I, QQ, UU, QU):
    """Polarized intensity with the modified asymptotic estimator
    (Plaszczynski et al. 2014) on sigma_P, p, and SNR(p) ~ P/sigma_P (the
    I noise is negligible: SNR(I) ~ 1000 in the LMC, paper section 2.2)."""
    P = np.hypot(Q, U)
    with np.errstate(invalid="ignore", divide="ignore"):
        sP = np.sqrt(np.clip(Q * Q * QQ + U * U * UU + 2 * Q * U * QU, 0, None)) / P
        Pm = P - sP**2 * (1 - np.exp(-(P**2) / sP**2)) / (2 * P)
        p = Pm / I
    return Pm, sP, p, P / sP


def load_hi4pi():
    """Full-sky RING array of HI4PI N_HI (|v_LSR| < 600 km/s), NaN outside the
    downloaded latitude band."""
    parts = sorted(HI4PI_PARTS.glob("part*"))
    raw = b"".join(p.read_bytes() for p in parts)
    s, _ = map(int, (HI4PI_PARTS / "range_bytes").read_text().split())
    off = 5760  # primary header + one header block of the binary table
    skip = (-(s - off)) % 48
    raw = raw[skip:]
    rows = np.frombuffer(raw[: len(raw) // 48 * 48], dtype=">i8,>f8,>f8,>f8,>f8,>f8")
    m = np.full(12 * 1024**2, np.nan)
    m[rows["f0"]] = rows["f5"]
    return m


def gass_lmc_mom0():
    """GASS III integrated over 182-366 km/s (the paper's LMC range), K km/s."""
    with fits.open(GASS_LMC) as h:
        cube = h[0].data
        hdr = h[0].header
        dv = abs(hdr["CDELT3"])  # km/s (CUNIT3 = km s-1)
        m0 = np.nansum(cube, axis=0) * dv
        return m0, WCS(hdr).celestial


def sep_deg(wcs, shape):
    yy, xx = np.mgrid[0 : shape[0], 0 : shape[1]]
    sky = wcs.pixel_to_world(xx.ravel(), yy.ravel())
    c0 = SkyCoord(rl.GRID["CRVAL1"] * u.deg, rl.GRID["CRVAL2"] * u.deg)
    return sky.separation(c0).deg.reshape(shape)


def foreground(st, wcs, shape, nh_tot, gass, outer_mask=None):
    """The paper's foreground model on one grid, at 16.2'.

    I_fg = alpha * N_H(MW) (equation 9), alpha from the outer-region
    correlation with the observed I; p_fg = mean p in the outer region where
    SNR(p) > 3 (section 3.3); psi_fg uniform, from the mean outer Q and U (the
    paper used the VGT/VDA angle map, which is not public)."""
    pxa = px_arcmin(wcs)
    sm = smoothed(st, FG_FWHM, pxa)
    nh_all = reproject_from_healpix((nh_tot, "galactic"), wcs, shape_out=shape, nested=False)[0]
    m0, gw = gass
    nh_lmc = XHI * reproject_interp((m0, gw), wcs, shape_out=shape, order="bilinear")[0]
    nh_mw = nh_all - nh_lmc
    r = sep_deg(wcs, shape)
    outer = (r > R_EXCL) & np.isfinite(nh_mw) if outer_mask is None else outer_mask
    # Fit in units of 1e20 cm^-2 so the design matrix is well conditioned.
    A = np.vstack([nh_mw[outer] / 1e20, np.ones(outer.sum())]).T
    alpha, beta = np.linalg.lstsq(A, sm["I"][outer], rcond=None)[0]
    alpha /= 1e20
    # Second regressor for the LMC/Bridge gas that lies in the outer region.
    A2 = np.vstack([nh_mw[outer] / 1e20, nh_lmc[outer] / 1e20, np.ones(outer.sum())]).T
    alpha2 = np.linalg.lstsq(A2, sm["I"][outer], rcond=None)[0]
    alpha2[:2] /= 1e20
    I0 = sm["I"] - beta  # zero level from the H I correlation
    Pm, sP, p, snr = pol(sm["Q"], sm["U"], I0, sm["QQ"], sm["UU"], sm["QU"])
    good = outer & (snr > 3)
    p_fg = float(np.nanmean(p[good]))
    qm, um = float(np.mean(sm["Q"][outer])), float(np.mean(sm["U"][outer]))
    psi_fg = 0.5 * np.arctan2(um, qm)
    I_fg = alpha * nh_mw
    return dict(sm=sm, nh_mw=nh_mw, nh_lmc=nh_lmc, r=r, outer=outer, alpha=float(alpha), beta=float(beta),
                alpha2=[float(x) for x in alpha2], p_fg=p_fg, psi_fg=float(psi_fg), I_fg=I_fg, I0=I0,
                p_fg_ratio=float(np.hypot(qm, um) / np.mean(I0[outer])),
                n_outer=int(outer.sum()), n_good=int(good.sum()),
                sig2_outer={k: float(np.mean(sm[k][outer])) for k in ("QQ", "UU")},
                I_outer=float(np.mean(I0[outer])))


def subtract(fg):
    sm = fg["sm"]
    Qf = fg["p_fg"] * fg["I_fg"] * np.cos(2 * fg["psi_fg"])
    Uf = fg["p_fg"] * fg["I_fg"] * np.sin(2 * fg["psi_fg"])
    # Paper appendix B: foreground covariance scaled from the outer region.
    w = fg["I_fg"] / fg["I_outer"]
    QQ = sm["QQ"] + fg["sig2_outer"]["QQ"] * w
    UU = sm["UU"] + fg["sig2_outer"]["UU"] * w
    return dict(Q=sm["Q"] - Qf, U=sm["U"] - Uf, I=fg["I0"] - fg["I_fg"], QQ=QQ, UU=UU, QU=sm["QU"])


def stats(x):
    x = x[np.isfinite(x)]
    h, e = np.histogram(x, bins=np.linspace(0, 0.3, 121))
    return dict(peak=float(0.5 * (e[h.argmax()] + e[h.argmax() + 1])), median=float(np.median(x)),
                mean=float(np.mean(x)), p90=float(np.percentile(x, 90)), p95=float(np.percentile(x, 95)),
                p99=float(np.percentile(x, 99)), n=int(x.size))


def validate(fg, aft):
    """Numbers to compare with the paper, on the site grid at 16.2'."""
    sm, I0 = fg["sm"], fg["I0"]
    I_med = float(np.median(I0))
    _, _, p_obs, snr_obs = pol(sm["Q"], sm["U"], I0, sm["QQ"], sm["UU"], sm["QU"])
    _, _, p_aft, snr_aft = pol(aft["Q"], aft["U"], aft["I"], aft["QQ"], aft["UU"], aft["QU"])
    mask = (I0 > I_med) & (snr_obs > 3)
    mask_lmc = mask & (snr_aft > 0.5)
    psi_o = 0.5 * np.arctan2(sm["U"], sm["Q"])
    psi_a = 0.5 * np.arctan2(aft["U"], aft["Q"])
    d = np.rad2deg(0.5 * np.angle(np.exp(2j * (psi_a - psi_o))))
    inner = fg["r"] <= R_EXCL
    pint = lambda Q, U, I: float(np.hypot(Q[inner].mean(), U[inner].mean()) / I[inner].mean())
    return {
        "I_med": I_med,
        "I_fg_mean_in_mask": float(np.mean(fg["I_fg"][mask])),
        "I_lmc_mean_in_mask": float(np.mean(aft["I"][mask])),
        "p_obs_mask": stats(p_obs[mask]),
        "p_lmc_mask": stats(p_aft[mask]),
        "p_lmc_mask_snr05": stats(p_aft[mask_lmc]),
        "dpsi_abs_median_deg": float(np.median(np.abs(d[mask]))),
        "dpsi_abs_p99_deg": float(np.percentile(np.abs(d[mask]), 99)),
        "dpsi_frac_over_20": float(np.mean(np.abs(d[mask]) > 20)),
        "p_integrated_5deg_obs": pint(sm["Q"], sm["U"], I0),
        "p_integrated_5deg_lmc": pint(aft["Q"], aft["U"], aft["I"]),
        "mask_pixels": int(mask.sum()),
    }


def stars(wcs, shape):
    """Foreground starlight (Schmidt 1976; Mathewson & Ford 1970) with the
    Gaia distances compiled by the paper: J2000 position, PA east of north
    (parallel to B for extinction polarization), drawn on the grid."""
    rows = []
    for cat, f in (("S76", "lmc_foreground_stars_s76_IAU_newdist_j2000.txt"),
                   ("MF70", "lmc_foreground_stars_mf70_IAU_newdist_j2000.txt")):
        a = np.atleast_2d(np.loadtxt(STARS / f, usecols=range(9)))
        for ra, dec, P, sP, pa, spa, dist in a[:, [1, 2, 3, 4, 5, 6, 8]]:
            c = SkyCoord(ra * u.deg, dec * u.deg)
            x, y = wcs.world_to_pixel(c)
            if not (-0.5 <= x <= shape[1] - 0.5 and -0.5 <= y <= shape[0] - 0.5):
                continue
            x2, y2 = wcs.world_to_pixel(c.directional_offset_by(pa * u.deg, 6 * u.arcmin))
            ga = np.degrees(np.arctan2(-(x2 - x), y2 - y))
            rows.append({"cat": cat, "x": round(float((x + 0.5) / shape[1]), 4),
                         "y": round(float(1 - (y + 0.5) / shape[0]), 4), "pa": round(float(pa), 1),
                         "grid": round(float(ga), 1), "p": float(P), "spa": float(spa), "d": round(float(dist)),
                         "used": bool(dist > STAR_DMIN and spa < STAR_SPA)})
    return rows


def mean_axis(deg, w=None):
    a = np.deg2rad(np.asarray(deg))
    w = np.ones_like(a) if w is None else w
    return float(np.degrees(0.5 * np.arctan2((w * np.sin(2 * a)).sum(), (w * np.cos(2 * a)).sum())) % 180)


def resample(x, n):
    """Sample a smooth work-grid map at the centres of an n x n texture,
    flipped so row 0 is the top (north) edge."""
    m = x.shape[0]
    c = (np.arange(n) + 0.5) * m / n - 0.5
    yy, xx = np.meshgrid(c, c, indexing="ij")
    out = map_coordinates(np.nan_to_num(x), [yy, xx], order=1, mode="nearest")
    return np.flipud(out)


def write_plane(name, x):
    TEX.mkdir(parents=True, exist_ok=True)
    lo, hi = float(np.min(x)), float(np.max(x))
    q = np.round((x - lo) / (hi - lo) * 65535).astype(np.uint16)
    with rl.atomic(TEX / f"{name}.png") as tmp:
        Image.fromarray(q, mode="I;16").save(tmp, optimize=True)
    return {"file": f"/sky/stokes/{name}.png", "n": int(x.shape[0]), "lo": lo, "hi": hi}


def contours(m0, n):
    from skimage.measure import approximate_polygon, find_contours

    out = {}
    for lev in HI_LEVELS:
        paths = []
        for c in find_contours(np.nan_to_num(m0), lev):
            c = approximate_polygon(c, 0.6)
            if len(c) < 4:
                continue
            pts = " ".join(f"{(x + 0.5) / n * 1000:.1f},{(1 - (y + 0.5) / n) * 1000:.1f}" for y, x in c)
            paths.append("M" + pts.replace(" ", "L", 1).replace(" ", "L"))
        out[str(lev)] = paths
    return out


def main():
    wcs, shape = site_grid(N_WORK)
    bw, bshape = big_grid()
    pl = cut_planck({"site": (wcs, shape), "big": (bw, bshape)})
    nh_tot = load_hi4pi()
    gass = gass_lmc_mom0()

    print("foreground ...", flush=True)
    fg = foreground(pl["site"], wcs, shape, nh_tot, gass)
    aft = subtract(fg)
    val = validate(fg, aft)
    # Same numbers with the map offset kept in I (no zero-level correction):
    # the paper removed only the CIB monopole, so its zero level sits between.
    fk = dict(fg)
    fk["I0"] = fg["I0"] + fg["beta"]
    val_kept = validate(fk, subtract(fk))
    # Check: outer region taken as a 5-10 deg annulus on the wider grid.
    fgb = foreground(pl["big"], bw, bshape, nh_tot, gass,
                     outer_mask=None)
    rb = fgb["r"]
    ann = (rb > R_EXCL) & (rb < 10) & np.isfinite(fgb["nh_mw"])
    fga = foreground(pl["big"], bw, bshape, nh_tot, gass, outer_mask=ann)

    st = stars(wcs, shape)
    used = [s for s in st if s["used"]]
    star_mean = mean_axis([s["pa"] for s in used])
    # psi_fg is in the grid frame; at the grid centre the tilt is zero, so the
    # foreground field PA there is psi_fg + 90.
    b_fg_pa = (np.degrees(fg["psi_fg"]) + 90) % 180

    print("textures ...", flush=True)
    pxa = px_arcmin(wcs)
    planes = {}
    I_native = pl["site"]["I"] - fg["beta"]
    planes["I"] = write_plane("i", resample(I_native, N_TEX_I))
    # Display stretch of render_lmc.stretch(I, 2, 99.8, asinh=0.2), applied to
    # observed and foreground-subtracted intensity alike.
    lo, hi = np.percentile(I_native, [2, 99.8])
    i_stretch = {"lo": float(lo), "hi": float(hi), "asinh": 0.2}
    nh_mw16 = fg["nh_mw"]
    for T in SCALES:
        sm = smoothed(pl["site"], T, pxa)
        sig = np.sqrt(np.clip(0.5 * (sm["QQ"] + sm["UU"]), 0, None))
        key = f"{T:02d}"
        planes[f"q{key}"] = write_plane(f"q{key}", resample(sm["Q"], N_TEX))
        planes[f"u{key}"] = write_plane(f"u{key}", resample(sm["U"], N_TEX))
        planes[f"s{key}"] = write_plane(f"s{key}", resample(sig, N_TEX))
        # I_fg from H I at 16.2'; coarser scales smooth it further.
        if T > FG_FWHM:
            planes[f"f{key}"] = write_plane(f"f{key}", resample(fg["alpha"] * smooth_map(nh_mw16, T, pxa, native=FG_FWHM), N_TEX_FG))
        else:  # the H I resolution limits I_fg: one shared 16' plane
            planes.setdefault("f16", write_plane("f16", resample(fg["alpha"] * np.nan_to_num(nh_mw16), N_TEX_FG)))
            planes[f"f{key}"] = planes["f16"]
    planes_meta = {k: v for k, v in planes.items()}

    m0 = reproject_interp(gass, wcs, shape_out=shape, order="bilinear")[0]
    cont = contours(m0, N_WORK)

    sig2_noise = {f"{T:02d}": 0.5 * (fg["sig2_outer"]["QQ"] + fg["sig2_outer"]["UU"]) / fg["I_outer"]
                  * (FG_FWHM**2 - BEAM**2) / (T**2 - BEAM**2) for T in SCALES}

    meta = {
        "about": f"Planck PR4 (NPIPE) 353 GHz Stokes I, Q, U on the {rl.GRID_DEG:.2f} deg LMC grid, MJy/sr. "
                 "Q, U in the IAU convention, referenced to the grid vertical (psi from up towards east/left). "
                 "Planes are 16-bit greyscale PNG, value = lo + (hi - lo) * v / 65535, row 0 = north edge. "
                 "Foreground re-derived for this site following Alina et al. 2023 (2023MNRAS.518.4466A). "
                 "Written by scripts/render_stokes.py.",
        "beam_arcmin": BEAM,
        "scales_arcmin": SCALES,
        "planes": planes_meta,
        "i_stretch": i_stretch,
        "zero_level_MJy_sr": fg["beta"],
        "foreground": {
            "method": "Q_fg = p_fg I_fg cos 2psi_fg, U_fg = p_fg I_fg sin 2psi_fg (paper eqs. 6-7); "
                      "I_fg = alpha N_H(MW) (eq. 9), N_H(MW) = HI4PI N_HI (|v|<600 km/s) minus GASS 182-366 km/s; "
                      "alpha and the zero level from the outer region (r > 5 deg) at 16.2'; "
                      "p_fg = mean p in the outer region with SNR(p) > 3; "
                      "psi_fg uniform from the mean outer Q, U (the paper used a VGT/VDA angle map).",
            "alpha_MJy_sr_per_cm2": fg["alpha"],
            "p_fg": fg["p_fg"],
            "psi_fg_grid_deg": float(np.degrees(fg["psi_fg"])),
            "b_fg_pa_deg_centre": float(b_fg_pa),
            "sigma2_per_Ifg": sig2_noise,
            "fwhm_arcmin": FG_FWHM,
        },
        "stars": st,
        "star_mean_pa_deg": star_mean,
        "star_count_used": len(used),
        "hi_contours": {"levels_K_kms": HI_LEVELS, "source": "GASS III, 182-366 km/s, 16.2'", "paths": cont, "viewbox": 1000},
        "validation": {
            "site_grid": val,
            "site_grid_offset_kept": val_kept,
            "paper": {"alpha_note": "the paper quotes 1.87e21, which matches N_H/I in cm^-2 per MJy/sr, i.e. alpha = 5.35e-22",
                      "I_med": 0.276, "I_fg_mean": 0.29, "I_lmc_mean": 0.68, "p_fg": 0.072,
                      "p_obs": {"peak": 0.039, "median": 0.040, "mean": 0.042, "p90": 0.067, "p95": 0.078, "p99": 0.100},
                      "p_lmc": {"peak": 0.025, "median": 0.036, "mean": 0.049, "p90": 0.098, "p95": 0.132, "p99": 0.216},
                      "p_integrated_5deg": [0.011, 0.033], "dpsi": "at most 20 deg at 3 sigma", "stars_used": 56},
            "alpha": fg["alpha"], "alpha_with_lmc_regressor": fg["alpha2"], "beta": fg["beta"],
            "p_fg": fg["p_fg"], "p_fg_from_mean_QU": fg["p_fg_ratio"],
            "n_outer": fg["n_outer"], "n_outer_snr3": fg["n_good"],
            "annulus_5_10deg": {"alpha": fga["alpha"], "beta": fga["beta"], "p_fg": fga["p_fg"],
                                "b_fg_pa_deg_centre": float((np.degrees(fga["psi_fg"]) + 90) % 180)},
            "big_grid_r_gt_5": {"alpha": fgb["alpha"], "beta": fgb["beta"], "p_fg": fgb["p_fg"],
                                "b_fg_pa_deg_centre": float((np.degrees(fgb["psi_fg"]) + 90) % 180)},
            "nh_mw_mean_outer": float(np.nanmean(fg["nh_mw"][fg["outer"]])),
            "nh_mw_mean_inner": float(np.nanmean(fg["nh_mw"][fg["r"] <= R_EXCL])),
            "nh_mw_min": float(np.nanmin(fg["nh_mw"])),
        },
        "sources": {
            "planck": "Planck PR4 (NPIPE) HFI 353 GHz, 2020A&A...643A..42P",
            "hi4pi": "HI4PI Collaboration 2016, A&A 594, A116 (LAMBDA N_HI map)",
            "gass": "GASS III, Kalberla & Haud 2015, A&A 578, A78",
            "stars": "Schmidt 1976; Mathewson & Ford 1970; distances compiled in 2023MNRAS.518.4466A",
            "method": "2023MNRAS.518.4466A",
        },
    }
    with rl.atomic(JSON_OUT) as tmp:
        tmp.write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta["validation"], indent=1))
    print("stars used", len(used), "mean PA", star_mean, "B_fg PA", b_fg_pa)
    tot = sum((TEX / Path(f).name).stat().st_size for f in {p["file"] for p in planes.values()})
    print(f"texture bytes {tot / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
