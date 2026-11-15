"""Metadata for every sky image the site shows: scale, orientation, beams,
colour bars, distances, a polarized signal-to-noise map and FITS downloads.

Writes
  src/data/maps.json            read by MapFrame.astro, FieldDots.astro
  public/sky/snr-*.webp         small S/N masks (white: S/N >= 3) and lmc-snr.webp
  public/data/*.fits            derived LMC maps on the 12 deg grid, 2x binned

Uses the render scripts' own functions (grid, Planck reader, stretches) so the
numbers describe the images as drawn. Needs the full-sky Planck map in memory:

    flock /tmp/ism-planck.lock env LMC_DATA=~/Projects/LMC/lmc-data python3 scripts/map_meta.py

Signal to noise. P = sqrt(Qs^2 + Us^2) with Qs, Us the Gaussian-smoothed maps
the field drawings use. The noise comes from the PR4 per-pixel covariances
(QQ, QU, UU in K_CMB^2), taken as white between HEALPix pixels. For a Gaussian
of width s, the smoothed variance is
    Var = sum_i w_i^2 var_i,  w_i = G(x - x_i) * Omega_pix,
which is Omega_pix / (4 pi s^2) times the covariance map smoothed with a
Gaussian of width s / sqrt(2). Omega_pix is the HEALPix pixel area, not the
area of an image pixel: the image grids oversample nside 2048 (1.7'), so
counting image pixels as independent would underestimate the noise by the
ratio of the two areas. sigma_P is the square root of the larger eigenvalue of
the smoothed Q, U covariance, which does not depend on the (noisy) angle.
Correlated large-scale NPIPE noise is not in the covariances, so this is a
lower bound on the noise. The signal includes Milky Way foreground.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import healpy as hp
import numpy as np
from astropy import units as u
from astropy.io import fits
from astropy.wcs import WCS
from PIL import Image
from reproject import reproject_from_healpix, reproject_interp
from scipy.ndimage import binary_dilation, binary_erosion, gaussian_filter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import composites as comp  # noqa: E402
import render_lmc as rl  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "src" / "data" / "maps.json"
SKY = ROOT / "public" / "sky"
DATA_DIR = ROOT / "public" / "data"
COMPOSITES = json.loads((ROOT / "src" / "data" / "composites.json").read_text())

PLANCK_BEAM = 4.94  # arcmin, 353 GHz effective beam FWHM, Planck 2018 III table 12
FWHM = 2 * np.sqrt(2 * np.log(2))
SNR_N = 96  # same block layout as web_assets.FIELD_N
SNR_MIN = 3.0
HI_COLUMN = 1.823e18  # cm^-2 per K km/s, optically thin (Dickey & Lockman 1990)
FITS_BIN = 2

REFS = {
    "planck": ("Planck Collaboration III 2020", "2020A&A...641A...3P"),
    "npipe": ("Planck Collaboration Int. LVII 2020", "2020A&A...643A..42P"),
    "spire": ("Griffin et al. 2010", "2010A&A...518L...3G"),
    "pacs": ("Poglitsch et al. 2010", "2010A&A...518L...2P"),
    "irac": ("Fazio et al. 2004", "2004ApJS..154...10F"),
    "wise": ("Wright et al. 2010", "2010AJ....140.1868W"),
    "shassa": ("Gaustad et al. 2001", "2001PASP..113.1326G"),
    "gass": ("McClure-Griffiths et al. 2009", "2009ApJS..181..398M"),
    "magma": ("Wong et al. 2011", "2011ApJS..197...16W"),
    "lmcdist": ("Pietrzynski et al. 2019", "2019Natur.567..200P"),
    "gcdist": ("GRAVITY Collaboration 2019", "2019A&A...625L..10G"),
    "zucker": ("Zucker et al. 2019", "2019ApJ...879..125Z"),
    "dl90": ("Dickey & Lockman 1990", "1990ARA&A..28..215D"),
}

# Beam FWHM (arcsec) per band, as named in composites.json.
BANDS = {
    "SHASSA H-alpha": (0.8 * 60, "shassa", "0.8' resolution, 48'' pixels"),
    "WISE 12 µm": (6.5, "wise", ""),
    "WISE 3.4 µm": (6.1, "wise", ""),
    "Herschel SPIRE 250 µm": (18.1, "spire", ""),
    "Herschel PACS 70 µm": (5.5, "pacs", "5.2 to 5.8'' depending on scan speed"),
    "Spitzer IRAC 8 µm": (1.98, "irac", ""),
    "Spitzer IRAC 3.6 µm": (1.66, "irac", ""),
}

# Frames: sky footprint, centre, distance. Distances are the average Gaia DR2
# based values of Zucker et al. 2019 table 2 (Orion A, Taurus, Mon OB1) and
# table 3 (the MBM 12 sightline); Orion B is 423 pc in the same table.
FRAMES = {
    "lmc": dict(frame="icrs", dist=49590, ref="lmcdist", name="LMC", err="49.59 ± 0.09 (stat) ± 0.54 (sys) kpc"),
    "gc2": dict(frame="galactic", dist=8178, ref="gcdist", name="Galactic centre", err="8.178 ± 0.013 ± 0.022 kpc"),
    "gc12": dict(frame="galactic", dist=8178, ref="gcdist", name="Galactic centre", err="8.178 ± 0.013 ± 0.022 kpc"),
    "mon3": dict(frame="galactic", dist=745, ref="zucker", name="Mon OB1", err="745 ± 37 pc (Mon OB1 box l 199-204, b 0-3)"),
    "mon8": dict(frame="galactic", dist=745, ref="zucker", name="Mon OB1", err="745 ± 37 pc (Mon OB1 box l 199-204, b 0-3)"),
    "orion": dict(frame="galactic", dist=432, ref="zucker", name="Orion", err="432 ± 22 pc (Orion A; Orion B 423 pc)"),
    "taurus": dict(frame="galactic", dist=141, ref="zucker", name="Taurus", err="141 ± 7 pc"),
    "mbm12": dict(frame="galactic", dist=252, ref="zucker", name="MBM 12", err="252 (+4 -6) ± 12 pc (sightline l 159.4, b -34.3)"),
}


def frame_wcs(fid, n=None):
    """WCS of the image frame on its native render grid."""
    if fid == "lmc":
        return rl.grid_wcs(), rl.SHAPE[1], rl.GRID["NAXIS1"] * abs(rl.GRID["CDELT1"]), (rl.GRID["CRVAL1"], rl.GRID["CRVAL2"])
    if fid in ("gc2", "mon3"):
        r = dict(comp.REGIONS["galactic_centre" if fid == "gc2" else "monoceros_ob1"])
        if n:
            r["n"] = n
        return comp.target_wcs(r), r["n"], r["fov"], r["centre"]
    key = {"gc12": "galactic_centre", "mon8": "monoceros_ob1"}.get(fid, fid)
    l, b, width = rl.REGIONS[key]
    size = n or 900
    hdr = fits.Header()
    hdr.update(NAXIS=2, NAXIS1=size, NAXIS2=size, CTYPE1="GLON-TAN", CTYPE2="GLAT-TAN",
               CRVAL1=l, CRVAL2=b, CRPIX1=size / 2 + 0.5, CRPIX2=size / 2 + 0.5,
               CDELT1=-width / size, CDELT2=width / size)
    return WCS(hdr), size, width, (l, b)


def tilt_samples(wcs, n, k=9):
    """Grid angle of local north (degrees, rows top = north end) on a k x k
    lattice of fractional positions, same maths as render_lmc.grid_angle."""
    pix = np.linspace(0, n - 1, k)
    xx, yy = np.meshgrid(pix, pix)
    sky = wcs.pixel_to_world(xx.ravel(), yy.ravel())
    to = sky.directional_offset_by(0 * u.rad, 2 * u.arcmin)
    x2, y2 = wcs.world_to_pixel(to)
    a = np.degrees(np.arctan2(-(x2 - xx.ravel()), y2 - yy.ravel())).reshape(k, k)
    return np.round(a[::-1], 2)


def nice_ticks(lo, hi, n=4):
    span = hi - lo
    raw = span / n
    mag = 10 ** np.floor(np.log10(raw))
    step = min((s * mag for s in (1, 2, 2.5, 5, 10)), key=lambda s: abs(s - raw))
    first = np.ceil(lo / step) * step
    ticks = np.arange(first, hi + step * 0.01, step)
    return [round(float(t), 6) for t in ticks]


def colours(cmap, stretch_fn=None, n=16, alpha=False):
    out = []
    for t in np.linspace(0, 1, n):
        x = float(stretch_fn(t)) if stretch_fn else t
        r, g, b, a = cmap(x)
        out.append(f"rgba({int(r * 255)},{int(g * 255)},{int(b * 255)},{a:.2f})" if alpha else f"rgb({int(r * 255)},{int(g * 255)},{int(b * 255)})")
    return out


def asinh_fn(soft):
    return lambda t: np.arcsinh(t / soft) / np.arcsinh(1 / soft)


def percentiles(a, lo, hi):
    v = a[np.isfinite(a)]
    return [float(x) for x in np.percentile(v, [lo, hi])]


def hi_moment0(wcs):
    """Same as render_lmc.hi_products' moment 0, without keeping the cube planes."""
    from astropy.io import fits as F

    with F.open(rl.HI_CUBE, memmap=True) as h:
        cube, hdr = h[0].data, h[0].header
        scale = 1.0 if hdr.get("CUNIT3", "m/s").strip().lower().startswith("km") else 1e-3
        dv = abs(hdr["CDELT3"]) * scale
        m0 = np.zeros(cube.shape[1:])
        for k in range(cube.shape[0]):
            m0 += np.nan_to_num(np.asarray(cube[k], dtype=np.float32)) * dv
        src = WCS(hdr).celestial
    g = reproject_interp((m0, src), wcs, shape_out=rl.SHAPE, order="bicubic")[0]
    return np.nan_to_num(g)


def smoothed_snr(Q, U, cqq, cqu, cuu, sigma_px, pix_rad, nside=2048):
    """Polarized S/N after Gaussian smoothing, see the module docstring."""
    omega = 4 * np.pi / (12 * nside ** 2)
    k = omega / (4 * np.pi * (sigma_px * pix_rad) ** 2)
    g = lambda a: gaussian_filter(np.nan_to_num(a), sigma_px)
    Qs, Us = g(Q), g(U)
    h = lambda a: gaussian_filter(np.nan_to_num(a), sigma_px / np.sqrt(2)) * k
    a, b, c = h(cqq), h(cqu), h(cuu)
    lam = 0.5 * (a + c) + np.sqrt(0.25 * (a - c) ** 2 + b ** 2)
    return np.hypot(Qs, Us) / np.sqrt(np.clip(lam, 1e-30, None))


def snr_targets():
    """name: (wcs, shape, sigma_px, pixel size in rad, sigma in arcmin)."""
    t = {}
    wcs, n, fov, _ = frame_wcs("lmc")
    pix = np.radians(fov / n)
    t["lmc8"] = (wcs, (n, n), 12.0, pix)  # render_lmc.planck_maps smooth_px=12 on the 40'' grid
    for name, fid, key in (("lmc10", "lmc", "lmc"), ("gc2", "gc2", "galactic_centre"), ("mon3", "mon3", "monoceros_ob1")):
        nn = 1024 if fid == "lmc" else 512
        r = dict(comp.REGIONS[key])
        r["n"] = nn
        w = comp.target_wcs(r)
        px = r["fov"] / nn  # deg
        t[name] = (w, (nn, nn), (10 / 60) / px, np.radians(px))  # composites.field_angle: 10' sigma
    for fid, key in (("orion", "orion"), ("mon8", "monoceros_ob1"), ("gc12", "galactic_centre"), ("taurus", "taurus"), ("mbm12", "mbm12")):
        w, n, width, _ = frame_wcs(fid)
        # render_lmc.regions: sm = max(2, 10 (8/width)^-0.3) pixels on the 900 px grid
        sm = max(2.0, 10 * (8.0 / width) ** -0.3)
        t["reg_" + fid] = (w, (n, n), sm, np.radians(width / n))
    return t


def block_grid(a, n=SNR_N):
    """Mean over the uneven blocks web_assets.py uses for the field grid; rows top = north."""
    e0 = np.linspace(0, a.shape[0], n + 1).astype(int)[:-1]
    e1 = np.linspace(0, a.shape[1], n + 1).astype(int)[:-1]
    cnt = np.outer(np.diff(np.r_[e0, a.shape[0]]), np.diff(np.r_[e1, a.shape[1]]))
    s = np.add.reduceat(np.add.reduceat(a, e0, axis=0), e1, axis=1) / cnt
    return s[::-1]


def save_mask(snr, name):
    im = Image.fromarray(np.ascontiguousarray(snr[::-1]).astype(np.float32), mode="F").resize((256, 256), Image.BILINEAR)
    s = np.asarray(im)
    m = 0.12 + 0.88 * np.clip((s - 1.0) / (SNR_MIN - 1.0), 0, 1)
    Image.fromarray((m * 255).astype(np.uint8)).save(SKY / f"snr-{name}.webp", quality=80, method=6)


def save_snr_layer(snr):
    g = np.clip(snr / 20, 0, 1)
    m = snr >= SNR_MIN
    edge = binary_dilation(m & ~binary_erosion(m, iterations=1))
    rgb = np.dstack([g, g, g]) * 0.85
    rgb[edge] = (1.0, 0.24, 0.14)
    im = Image.fromarray((rgb * 255).astype(np.uint8)).transpose(Image.FLIP_TOP_BOTTOM)
    im.thumbnail((1000, 1000))
    im.save(SKY / "lmc-snr.webp", quality=85, method=6)


def binned(a, f=FITS_BIN, circular=False):
    n = (min(a.shape) // f) * f
    a = a[:n, :n]
    if circular:  # axial data (angle mod 180): mean of 2 theta
        s = a.reshape(n // f, f, n // f, f)
        return 0.5 * np.arctan2(np.sin(2 * s).mean((1, 3)), np.cos(2 * s).mean((1, 3)))
    return a.reshape(n // f, f, n // f, f).mean((1, 3))


def write_fits(name, data, bunit, what, extra=()):
    wcs, n, fov, _ = frame_wcs("lmc")
    d = data.astype(np.float32)
    m = d.shape[0]
    f = FITS_BIN
    h = fits.Header()
    h.update(NAXIS=2, CTYPE1="RA---TAN", CTYPE2="DEC--TAN", CRVAL1=rl.GRID["CRVAL1"], CRVAL2=rl.GRID["CRVAL2"],
             CRPIX1=(rl.GRID["CRPIX1"] - 0.5) / f + 0.5, CRPIX2=(rl.GRID["CRPIX2"] - 0.5) / f + 0.5,
             CDELT1=rl.GRID["CDELT1"] * f, CDELT2=rl.GRID["CDELT2"] * f, RADESYS="FK5", EQUINOX=2000.0)
    hdu = fits.PrimaryHDU(d, header=h)
    hh = hdu.header
    hh["BUNIT"] = bunit
    hh["OBJECT"] = "LMC"
    hh["ORIGIN"] = "ISM group, Nazarbayev University"
    hh["CREATOR"] = "scripts/map_meta.py"
    hh["DATE"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    hh["COMMENT"] = what
    for line in extra:
        hh["COMMENT"] = line
    hh["COMMENT"] = "Data: Planck HFI 353 GHz PR4 (NPIPE), Planck Collaboration Int. LVII 2020, A&A 643, A42 (2020A&A...643A..42P)."
    hh["COMMENT"] = "Planck data are public (ESA Planck Legacy Archive); please credit the Planck Collaboration and ESA."
    hh["COMMENT"] = "Please credit this derived product to the ISM group, Nazarbayev University, and cite Alina et al. 2023, MNRAS 518, 4466."
    hh["COMMENT"] = "Grid: 12.08 deg TAN, 2x2 binned from the site's 40 arcsec analysis grid. Includes Milky Way foreground."
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    hdu.writeto(DATA_DIR / name, overwrite=True)
    return f"/data/{name}", (DATA_DIR / name).stat().st_size


def main():
    SKY.mkdir(parents=True, exist_ok=True)
    wcs, n, fov, _ = frame_wcs("lmc")

    # ---- Planck I, Q, U on every target grid, then the covariances ----
    targets = snr_targets()
    planck = rl.read_planck()
    I_lmc, b_eq, _ = rl.planck_maps(planck, wcs, rl.SHAPE)
    proj = lambda m, w, s: reproject_from_healpix((m, "galactic"), w, shape_out=s, nested=False)[0]
    QU = {k: (proj(planck[1], w, s), -proj(planck[2], w, s)) for k, (w, s, _, _) in targets.items()}
    del planck
    cov = {}
    for col, key in ((7, "qq"), (8, "qu"), (9, "uu")):
        m = hp.read_map(rl.PLANCK, field=col, dtype=np.float32)
        for k, (w, s, _, _) in targets.items():
            c = proj(m, w, s)
            cov.setdefault(k, {})[key] = -c if key == "qu" else c  # U was negated
        del m
    snr = {}
    stats = {}
    for k, (w, s, sig, pix) in targets.items():
        Q, U = QU[k]
        snr[k] = smoothed_snr(Q, U, cov[k]["qq"], cov[k]["qu"], cov[k]["uu"], sig, pix)
        s_arcmin = float(sig * np.degrees(pix) * 60)
        fw = float(np.hypot(s_arcmin * FWHM, PLANCK_BEAM))
        stats[k] = dict(sigma_arcmin=round(s_arcmin, 2), fwhm_arcmin=round(fw, 1),
                        frac_gt3=round(float(np.mean(snr[k] >= SNR_MIN)), 3), median=round(float(np.median(snr[k])), 2))
        save_mask(snr[k], k)
        print(k, stats[k], flush=True)
    lm = snr["lmc8"]
    yy, xx = np.mgrid[0 : lm.shape[0], 0 : lm.shape[1]]
    disc = np.hypot(xx - lm.shape[1] / 2, yy - lm.shape[0] / 2) * abs(rl.GRID["CDELT1"]) < 4.0
    stats["lmc8"]["frac_gt3_within_4deg"] = round(float(np.mean(lm[disc] >= SNR_MIN)), 3)
    save_snr_layer(lm)
    grid = block_grid(lm)
    snr_json = dict(n=SNR_N, scale=10, min=SNR_MIN, grid=[int(round(float(v) * 10)) for v in np.clip(grid, 0, 99.9).ravel()])

    # ---- stretch limits and colour bars on the LMC grid ----
    from matplotlib import colormaps

    m0 = hi_moment0(wcs)
    hi_lo, hi_hi = percentiles(m0, 2, 99.9)
    dust_lo, dust_hi = percentiles(I_lmc, 2, 99.8)
    co = rl.co_moment0(wcs, rl.SHAPE)
    co_lo, co_hi = percentiles(co, 5, 99.8)
    c = HI_COLUMN / 1e20
    bars = {
        "hi": dict(label="N(H I)", unit="10²⁰ cm⁻²", lo=hi_lo * c, hi=hi_hi * c, ticks=nice_ticks(hi_lo * c, hi_hi * c),
                   colors=colours(rl.dust_cmap(rl.GAS_STOPS), asinh_fn(0.15)),
                   note=f"{hi_lo:.0f} to {hi_hi:.0f} K km/s, optically thin; asinh colour scale"),
        "vel": dict(label="v", unit="km/s", lo=200, hi=320, ticks=[200, 240, 280, 320],
                    colors=colours(colormaps["RdBu_r"]), note="brightness follows the H I column"),
        "dust": dict(label="I 353", unit="mK CMB", lo=dust_lo * 1e3, hi=dust_hi * 1e3, ticks=nice_ticks(dust_lo * 1e3, dust_hi * 1e3, 3),
                     colors=colours(rl.dust_cmap(), asinh_fn(0.2)), note="zero level not calibrated; asinh colour scale"),
        "co": dict(label="W(CO)", unit="K km/s", lo=co_lo, hi=co_hi, ticks=nice_ticks(co_lo, co_hi, 3),
                   colors=colours(lambda x: (0.35, 0.95, 1.0, float(np.clip(1.6 * x, 0, 1))), asinh_fn(0.1), alpha=True),
                   note="3 sigma clipped moment 0; asinh colour scale"),
        "snr": dict(label="S/N of P", unit="", lo=0, hi=20, ticks=[0, 3, 10, 20],
                    colors=colours(lambda x: (0.85 * x, 0.85 * x, 0.85 * x, 1.0)), note="red line: S/N = 3"),
    }
    for b in bars.values():
        b["lo"], b["hi"] = round(b["lo"], 4), round(b["hi"], 4)

    # ---- FITS ----
    pa = (np.degrees(b_eq) % 180.0)
    pa_b = np.degrees(binned(np.radians(pa), circular=True)) % 180.0
    fits_files = {
        "angle": write_fits("lmc_field_angle.fits", pa_b, "deg",
                            "Plane-of-sky magnetic field position angle, east of north, from Planck 353 GHz Q, U.",
                            ("PA = polarization angle + 90 deg (IAU), Q, U smoothed with a 12 pixel (8 arcmin) Gaussian before the angle.",
                             "Angle is axial (0 to 180 deg). Unit: degrees. Script: scripts/render_lmc.py planck_maps().")),
        "intensity": write_fits("lmc_planck353_I.fits", binned(I_lmc.astype(np.float32)), "K_CMB",
                                "Planck 353 GHz total intensity, solar dipole fitted at |b| > 30 deg and removed, monopole left in.",
                                ("Not smoothed: native Planck resolution (effective beam FWHM 4.94 arcmin). Script: scripts/render_lmc.py read_planck().",)),
        "snr": write_fits("lmc_field_snr.fits", binned(lm), "",
                          "Signal to noise of Planck 353 GHz polarized intensity after the 8 arcmin Gaussian smoothing used for the field angle.",
                          ("Noise from the PR4 Q, U covariances, white between HEALPix pixels; large-scale correlated noise not included.",
                           "Script: scripts/map_meta.py smoothed_snr().")),
    }

    # ---- frames and images ----
    frames = {}
    for fid, f in FRAMES.items():
        w, nn, width, centre = frame_wcs(fid)
        frames[fid] = dict(frame=f["frame"], fov_deg=round(width, 4), centre=[round(float(centre[0]), 4), round(float(centre[1]), 4)],
                           dist_pc=f["dist"], dist_ref=f["ref"], dist_text=f["err"], name=f["name"],
                           tilt=dict(k=9, deg=tilt_samples(w, nn).tolist()))

    def bands_of(key):
        out = []
        for credit in COMPOSITES[key]:
            if credit.startswith("Planck"):
                continue
            fw, ref, note = BANDS[credit]
            out.append(dict(name=credit, fwhm_arcsec=fw, ref=ref, note=note))
        return out

    def coarsest(bands):
        b = max(bands, key=lambda x: x["fwhm_arcsec"])
        return dict(label=short(b["name"]) + " " + fmt_beam(b["fwhm_arcsec"]), arcmin=b["fwhm_arcsec"] / 60, layer="band")

    def short(name):
        return name.replace("Herschel ", "").replace("Spitzer ", "").replace("SHASSA H-alpha", "SHASSA Hα")

    def fmt_beam(arcsec):
        return f"{arcsec / 60:.1f}′" if arcsec >= 60 else f"{arcsec:.0f}″" if arcsec >= 10 else f"{arcsec:.1f}″"

    planck_band = lambda note="": dict(name="Planck 353 GHz (PR4)", fwhm_arcsec=PLANCK_BEAM * 60, ref="planck", note=note or "effective beam FWHM 4.94'")

    def field_beam(sn):
        return dict(label=f"Planck field {stats[sn]['fwhm_arcmin']:.0f}′", arcmin=stats[sn]["fwhm_arcmin"], layer="field")

    comp_stretch = ("Per band: background removal, asinh stretch from a percentile black point, starlet sharpening, "
                    "colour screen blend (scripts/composites.py).")
    images = {}

    def add(key, frame, title, script, stretch, smoothing="", bands=(), beams=(), bar=None, files=(), snr_key=None, native=None, note=""):
        images[key] = dict(frame=frame, title=title, script=script, stretch=stretch, smoothing=smoothing,
                           bands=list(bands), beams=list(beams), bar=bar, fits=[fits_files[f] and dict(href=fits_files[f][0], bytes=fits_files[f][1], what=FITS_WHAT[f]) for f in files],
                           snr=snr_key, native_px=native, note=note)

    FITS_WHAT = {"angle": "Field position angle, east of north (deg)", "intensity": "Planck 353 GHz intensity (K_CMB)", "snr": "Polarized S/N at the field smoothing"}
    lmc_native = 1087
    for name, fid, key, sn in (("lmc", "lmc", "lmc", "lmc10"), ("galactic_centre", "gc2", "galactic_centre", "gc2"), ("monoceros_ob1", "mon3", "monoceros_ob1", "mon3")):
        bd = bands_of(key)
        pb = planck_band()
        sm = f"Field texture: Q and U smoothed with a 10′ sigma Gaussian (FWHM {stats[sn]['fwhm_arcmin']:.0f}′ with the Planck beam), then drawn as line integral convolution."
        files = ("angle", "snr") if name == "lmc" else ()
        add(f"comp-{name}", fid, "Multi-band composite", "scripts/composites.py composite()", comp_stretch, beams=[coarsest(bd)], bands=bd,
            native=2048)
        add(f"comp-{name}-field", fid, "Composite with the Planck field", "scripts/composites.py composite()", comp_stretch,
            sm, bands=bd + [pb], beams=[coarsest(bd), field_beam(sn)], files=files, snr_key=sn, native=2048)
    add("comp-lmc-ridges", "lmc", "Ridge filter, Herschel 250 µm", "scripts/composites.py ridges()",
        "Strongest negative Hessian eigenvalue of log intensity at sigma 1.5, 3 and 6 pixels (scale-normalised), normalised to the 99.5th percentile.",
        bands=[dict(name="Herschel SPIRE 250 µm", fwhm_arcsec=18.1, ref="spire", note="")],
        beams=[dict(label="SPIRE 250 18″", arcmin=18.1 / 60, layer="band")], native=2048)
    lmc_planck = dict(bands=[planck_band()])
    add("lmc-dust", "lmc", "Planck 353 GHz intensity", "scripts/render_lmc.py read_planck(), render main()",
        f"asinh (softening 0.2) between the 2nd and 99.8th percentile ({dust_lo * 1e3:.3f} to {dust_hi * 1e3:.3f} mK_CMB), copper palette.",
        "Unsmoothed; the solar dipole is fitted away from the plane and removed.", beams=[dict(label="Planck 4.9′", arcmin=PLANCK_BEAM, layer="band")],
        bar=bars["dust"], files=("intensity",), native=lmc_native, **lmc_planck)
    add("lmc-bfield", "lmc", "Planck dust with the field texture", "scripts/render_lmc.py planck_maps(), lic()",
        "Dust stretch as the intensity image; the line integral convolution texture is added to the value before the colour map (amount 0.4).",
        f"Q and U smoothed with a 12 pixel (8′) Gaussian, FWHM {stats['lmc8']['fwhm_arcmin']:.0f}′ with the beam. Angle drawn in grid coordinates (render_lmc.grid_angle).",
        beams=[field_beam("lmc8")], files=("angle", "snr"), snr_key="lmc8", native=lmc_native, **lmc_planck)
    for k in ("lmc-bfield-v",):
        images[k] = dict(images["lmc-bfield"])
    add("lmc-lic", "lmc", "Field texture only", "scripts/render_lmc.py lic()", "Line integral convolution of white noise along the field direction, min-max normalised.",
        f"Q and U smoothed with a 12 pixel (8′) Gaussian, FWHM {stats['lmc8']['fwhm_arcmin']:.0f}′ with the beam.",
        beams=[field_beam("lmc8")], files=("angle", "snr"), snr_key="lmc8", native=lmc_native, **lmc_planck)
    gass = dict(name="GASS H I", fwhm_arcsec=16 * 60, ref="gass", note="gridded; the Parkes beam is 14.3'")
    add("lmc-hi", "lmc", "H I column density", "scripts/render_lmc.py hi_products()",
        f"Moment 0 over 182 to 339 km/s (LSR), asinh (softening 0.15) between the 2nd and 99.9th percentile ({hi_lo:.0f} to {hi_hi:.0f} K km/s), grey palette. "
        f"Column density assumes optically thin gas, {HI_COLUMN:.3e} cm⁻² per K km/s.",
        "Cube reprojected to the 40″ grid (bicubic).", bands=[gass], beams=[dict(label="GASS 16′", arcmin=16, layer="band")], bar=bars["hi"], native=lmc_native)
    add("lmc-vel", "lmc", "H I mean velocity", "scripts/render_lmc.py hi_products()",
        "Intensity-weighted mean velocity from 200 (blue) to 320 km/s (red), RdBu_r; brightness is the H I column to the power 0.8. "
        "Pixels below the 35th percentile of the column are set to the median velocity.",
        "Cube reprojected to the 40″ grid (bicubic).", bands=[gass], beams=[dict(label="GASS 16′", arcmin=16, layer="band")], bar=bars["vel"], native=lmc_native)
    add("lmc-co", "lmc", "CO(1-0) clouds", "scripts/render_lmc.py co_moment0()",
        f"Moment 0 of channels above 3 sigma (MAGMA rms cube), asinh (softening 0.1) between the 5th and 99.8th percentile ({co_lo:.1f} to {co_hi:.1f} K km/s); drawn as cyan with opacity from the stretch.",
        "Reprojected to the 40″ grid.", bands=[dict(name="MAGMA CO(1-0), Mopra", fwhm_arcsec=45, ref="magma", note="33'' beam, gridded to about 45''")],
        beams=[dict(label="MAGMA 45″", arcmin=45 / 60, layer="band")], bar=bars["co"], native=lmc_native)
    add("lmc-snr", "lmc", "Polarized signal to noise", "scripts/map_meta.py smoothed_snr()",
        "Linear grey from 0 to 20; the red line marks S/N = 3.",
        f"Same smoothing as the field texture (8′ sigma). S/N above 3 over {stats['lmc8']['frac_gt3'] * 100:.0f}% of the grid and {stats['lmc8']['frac_gt3_within_4deg'] * 100:.0f}% within 4° of the centre.",
        bands=[planck_band()], beams=[field_beam("lmc8")], bar=bars["snr"], files=("snr",), snr_key="lmc8", native=lmc_native)
    add("dotfield", "lmc", "Field dashes", "src/components/FieldDots.astro, scripts/web_assets.py",
        "Field angle on a 96 by 96 block grid (circular mean of 2θ); dashes fade out where the polarized S/N is below 3.",
        f"Q and U smoothed with an 8′ sigma Gaussian, FWHM {stats['lmc8']['fwhm_arcmin']:.0f}′. Milky Way foreground not removed.",
        bands=[planck_band()], beams=[field_beam("lmc8")], files=("angle", "snr"), snr_key="lmc8", native=lmc_native)
    for fid, key in (("orion", "orion"), ("mon8", "monoceros_ob1"), ("gc12", "galactic_centre"), ("taurus", "taurus"), ("mbm12", "mbm12")):
        sk = "reg_" + fid
        add(f"region-{key}", fid, "Planck dust with the field texture", "scripts/render_lmc.py regions()",
            "Dust: log intensity stretched between the 1st and 99.8th percentile, copper palette; the texture is added to the value (amount 0.4).",
            f"Q and U smoothed with a {stats[sk]['sigma_arcmin']:.0f}′ sigma Gaussian, FWHM {stats[sk]['fwhm_arcmin']:.0f}′ with the beam.",
            bands=[planck_band()], beams=[field_beam(sk)], snr_key=sk, native=900)

    commit = subprocess.run(["git", "describe", "--always", "--dirty", "--exclude=*"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    out = dict(commit=commit, refs={k: dict(label=v[0], bib=v[1]) for k, v in REFS.items()}, frames=frames, images=images,
               snr_stats=stats, snr=snr_json)
    OUT_JSON.write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
    print("fits", {k: (v[0], round(v[1] / 1e6, 2)) for k, v in fits_files.items()})
    print("bars", {k: (b["lo"], b["hi"]) for k, b in bars.items()})
    print("wrote", OUT_JSON, OUT_JSON.stat().st_size)


if __name__ == "__main__":
    main()
