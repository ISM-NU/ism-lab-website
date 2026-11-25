"""Render web-ready sky and LMC images from public survey data.

Inputs (from the LMC workspace's shared data folder, LMC_DATA):
  - H I: any LMC cube in K (HI_CUBE). The default is the public GASS survey
    (Parkes, 16'). The GASKAP-HI + Parkes cube we hold is collaboration-internal
    and must not feed the public site until it is released.
  - CO: MAGMA CO(1-0) cube and its rms cube
  - Dust and magnetic field: Planck HFI 353 GHz I, Q, U (PR4 / NPIPE, HEALPix, Galactic)

Everything is put on one fixed equatorial TAN grid (GRID below: 12 deg, 40"
pixels), so the layers line up pixel for pixel and can be stacked or
cross-faded in the browser. Outputs go to OUT as 8-bit images plus a small JSON
with the grid. scripts/web_assets.py turns them into the site's files.

Run: LMC_DATA=/path/to/lmc-data python3 scripts/render_lmc.py
"""

import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path

import healpy as hp
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
from matplotlib import colormaps
from PIL import Image
from reproject import reproject_from_healpix, reproject_interp
from scipy.ndimage import gaussian_filter, map_coordinates

from facts import FACTS, field


def env_path(name, what):
    """Path named by an environment variable; exit with a clear message when unset."""
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"{name} is not set: point it at {what}.")
    return Path(value).expanduser()


def require_files(*paths):
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise SystemExit("missing input files:\n  " + "\n  ".join(missing))


DATA = env_path("LMC_DATA", "the LMC data folder (it holds exp_raw/ and external/)")
OUT = Path(os.environ.get("OUT", Path(__file__).resolve().parent.parent / "assets" / "lmc"))
N_CHANNEL_FRAMES = 48

# Fixed output grid, defined in src/data/facts.json. Do not change it without
# re-running web_assets.py: the site's target positions and field grid are
# computed on it.
_G = FACTS["grid"]
GRID = {"NAXIS": 2, "NAXIS1": _G["naxis"], "NAXIS2": _G["naxis"], "CTYPE1": "RA---TAN", "CTYPE2": "DEC--TAN",
        "CRVAL1": _G["crval_deg"][0], "CRVAL2": _G["crval_deg"][1], "CRPIX1": _G["crpix"], "CRPIX2": _G["crpix"],
        "CDELT1": -_G["cdelt_deg"], "CDELT2": _G["cdelt_deg"], "RADESYS": "FK5", "EQUINOX": 2000.0}
SHAPE = (GRID["NAXIS2"], GRID["NAXIS1"])
GRID_DEG = GRID["NAXIS1"] * abs(GRID["CDELT1"])  # width on the sky

HI_CUBE = Path(os.environ.get("HI_CUBE", DATA / "exp_raw/eq_subcube_182to339_gass_279_-33_1444812272.fits"))
CO_CUBE = DATA / "exp_raw/lmc_v11.co.vradlsr.base.fits"
CO_RMS = DATA / "exp_raw/lmc_v11.co.vradlsr.rms.fits"
PLANCK = DATA / "external/HFI_SkyMap_353-BPassCorrected_2048_R4.00_full.fits"


def grid_wcs():
    h = fits.Header()
    h.update(GRID)
    return WCS(h)


def tan_header(frame, centre, n, pix_deg, crpix=None, radesys="FK5"):
    """Header of an n x n gnomonic grid with north up and east to the left.

    frame is "icrs" (RA/Dec) or "galactic"; centre is the tangent point in
    degrees. crpix defaults to the middle of the image. RA/Dec grids are FK5
    J2000 like GRID; radesys=None leaves the system unset, which WCS reads as
    ICRS."""
    if frame == "icrs":
        ctype = ("RA---TAN", "DEC--TAN")
        extra = dict(RADESYS=radesys, EQUINOX=2000.0) if radesys else {}
    elif frame == "galactic":
        ctype, extra = ("GLON-TAN", "GLAT-TAN"), {}
    else:
        raise ValueError(f"unknown frame {frame!r}")
    ref = n / 2 + 0.5 if crpix is None else crpix
    h = fits.Header()
    h.update(NAXIS=2, NAXIS1=n, NAXIS2=n, CTYPE1=ctype[0], CTYPE2=ctype[1],
             CRVAL1=centre[0], CRVAL2=centre[1], CRPIX1=ref, CRPIX2=ref, CDELT1=-pix_deg, CDELT2=pix_deg, **extra)
    return h


def tan_wcs(frame, centre, n, pix_deg, crpix=None, radesys="FK5"):
    return WCS(tan_header(frame, centre, n, pix_deg, crpix, radesys))


def cosmo_to_iau(x):
    """Planck maps use the COSMO polarization convention, the field angles here
    use IAU. They differ by the sign of U, so U and every covariance with one U
    factor (IU, QU) change sign; Q, I, QQ, UU, II, IQ do not."""
    return -x


@contextmanager
def atomic(path):
    """Yield a temp path next to path (same suffix, so writers keep the format)
    and rename it over path when the block succeeds, so an interrupted run
    never leaves a half-written output."""
    path = Path(path)
    tmp = path.with_name(f"{path.stem}.tmp{path.suffix}")
    try:
        yield tmp
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def input_key(*parts):
    """Short hash of everything a cached product was computed from."""
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:16]


def stretch(a, lo_pct=1.0, hi_pct=99.7, asinh=None):
    """Percentile clip, optional asinh, to 0..1 (NaN -> 0)."""
    v = a[np.isfinite(a)]
    lo, hi = np.percentile(v, [lo_pct, hi_pct])
    x = np.clip((a - lo) / (hi - lo), 0, 1)
    if asinh:
        x = np.arcsinh(x / asinh) / np.arcsinh(1 / asinh)
    return np.nan_to_num(x)


def save_gray(x, name, quality=88):
    Image.fromarray((x * 255).astype(np.uint8)).transpose(Image.FLIP_TOP_BOTTOM).save(
        OUT / name, quality=quality
    )


def save_rgba(rgba, name, quality=88):
    img = Image.fromarray((rgba * 255).astype(np.uint8)).transpose(Image.FLIP_TOP_BOTTOM)
    img.save(OUT / name, quality=quality) if name.endswith(".png") else img.convert("RGB").save(OUT / name, quality=quality)


def hi_products(target_wcs):
    """Moment 0, moment 1, channel planes and the integrated spectrum of the
    H I cube, all reprojected onto the output grid."""
    with fits.open(HI_CUBE, memmap=True) as h:
        cube = h[0].data
        hdr = h[0].header
        nchan = cube.shape[0]
        scale = 1.0 if hdr.get("CUNIT3", "m/s").strip().lower().startswith("km") else 1e-3
        v = (hdr["CRVAL3"] + (np.arange(nchan) + 1 - hdr["CRPIX3"]) * hdr["CDELT3"]) * scale
        dv = abs(hdr["CDELT3"]) * scale
        src = WCS(hdr).celestial
        m0 = np.zeros(cube.shape[1:])
        m1 = np.zeros(cube.shape[1:])
        spectrum = np.zeros(nchan)
        chans = []
        for k in range(nchan):
            plane = np.nan_to_num(np.asarray(cube[k], dtype=np.float32))
            m0 += plane * dv
            m1 += plane * v[k] * dv
            spectrum[k] = plane.sum()
            chans.append(plane)
    with np.errstate(invalid="ignore", divide="ignore"):
        m1 = np.where(m0 > 0, m1 / m0, np.median(v))
    # Reproject before masking: NaNs would spread through the bicubic kernel.
    to_grid = lambda a: reproject_interp((a, src), target_wcs, shape_out=SHAPE, order="bicubic")[0]
    m0g, m1g = to_grid(m0), to_grid(m1)
    m1g = np.where(np.nan_to_num(m0g) > np.nanpercentile(m0g, 35), m1g, np.nan)
    return m0g, m1g, np.stack(chans), v, spectrum, to_grid


def co_moment0(target_wcs, shape):
    with fits.open(CO_CUBE, memmap=True) as h, fits.open(CO_RMS, memmap=True) as hr:
        cube, rms, hdr = h[0].data, hr[0].data, h[0].header
        dv = abs(hdr["CDELT3"]) / 1e3
        m0 = np.zeros(cube.shape[1:], dtype=np.float64)
        rms2d = np.asarray(rms[0] if rms.ndim == 3 else rms, dtype=np.float32)
        for k in range(cube.shape[0]):
            plane = np.nan_to_num(np.asarray(cube[k], dtype=np.float32))
            m0 += np.where(plane > 3 * rms2d, plane, 0) * dv
        src_wcs = WCS(hdr).celestial
    m0[m0 <= 0] = np.nan
    out, _ = reproject_interp((m0, src_wcs), target_wcs, shape_out=shape)
    return out


def read_planck():
    """I, Q, U in K_CMB, RING ordering, with the solar dipole removed from I.

    The NPIPE (PR4) frequency maps keep the solar dipole (3.3 mK towards
    l=262, b=+48). At 353 GHz it outshines the high-latitude dust and turns
    one hemisphere bright and the other black, so it is fitted away from the
    plane (|b| > 30 deg, nside 128) and subtracted. The monopole is left in;
    every stretch below is percentile based."""
    m = list(hp.read_map(PLANCK, field=(0, 1, 2), dtype=np.float32))
    nside = hp.get_nside(m[0])
    low = hp.ud_grade(m[0], 128)
    lat = hp.pix2ang(128, np.arange(low.size), lonlat=True)[1]
    low[np.abs(lat) < 30] = hp.UNSEEN
    _, dip = hp.fit_dipole(low)
    step = 1 << 22
    for s in range(0, m[0].size, step):
        x, y, z = hp.pix2vec(nside, np.arange(s, min(s + step, m[0].size)))
        m[0][s : s + step] -= (dip[0] * x + dip[1] * y + dip[2] * z).astype(np.float32)
    return m


# Dust palette for every Planck image: black through oxblood and copper to
# warm white. Lightness rises monotonically, so brightness always means more
# dust, and the hue stays clear of the site's signal red.
DUST_STOPS = [(0.0, "#000000"), (0.18, "#1c0a06"), (0.38, "#5a1e0e"), (0.58, "#a8461a"),
              (0.76, "#e08a3c"), (0.9, "#f6c98a"), (1.0, "#fff6e6")]


# Atomic gas gets a cool monochrome so it never reads as dust.
GAS_STOPS = [(0.0, "#000000"), (0.2, "#14161a"), (0.42, "#3b4048"), (0.64, "#7d848c"),
             (0.84, "#c9c7bf"), (1.0, "#fffdf6")]


def dust_cmap(stops=None):
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("dust", stops or DUST_STOPS)


def shade(dust, tex, cmap=None, amount=0.22):
    """Colour a 0..1 dust map, with the field texture worked into the value
    before the colormap (not multiplied after it), so the palette stays
    monotonic and faint regions keep visible streaks."""
    v = np.clip(dust + amount * (tex - 0.5) * (0.35 + dust), 0, 1)
    return (cmap or dust_cmap())(v)[..., :3]


def mollweide_field_angle(proj, theta, d=0.05):
    """Convert a field position angle (east of Galactic north) at every pixel
    of a healpy Mollweide image into the step direction lic() expects.

    Mollweide is not conformal and its meridians converge, so image-up is
    not north away from the central meridian. The tangent vector
    cos(theta) N + sin(theta) E is pushed through the projection by finite
    differences of ang2xy along north and east."""
    x, y = (np.ma.filled(a.astype(float), np.nan) for a in proj.ij2xy())
    out = np.full(theta.shape, np.nan)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y, th = x[ok], y[ok], theta[ok]
    lon, lat = proj.xy2ang(x, y, lonlat=True)
    lat = np.clip(lat, -89.5, 89.5)
    xy = lambda lo, la: proj.ang2xy(lo, np.clip(la, -90, 90), lonlat=True)
    xn, yn = xy(lon, lat + d)
    dlon = d / np.cos(np.radians(lat))
    xe, ye = xy(lon + dlon, lat)
    xw, yw = xy(lon - dlon, lat)
    # At the map's left and right edges one side of the east step wraps to
    # the far edge; take whichever one-sided difference stayed local.
    ex, ey = xe - x, ye - y
    wrap = np.hypot(ex, ey) > np.hypot(xw - x, yw - y) * 3
    ex, ey = np.where(wrap, x - xw, ex), np.where(wrap, y - yw, ey)
    vx = np.cos(th) * (xn - x) + np.sin(th) * ex
    vy = np.cos(th) * (yn - y) + np.sin(th) * ey
    # healpy projmap rows run upward with y and columns with x, which is the
    # (x, y-up) frame lic() steps in: (dx, dy) = (-sin a, cos a).
    out[ok] = np.arctan2(-vx, vy)
    return out


def allsky(planck, nside=512, width=FACTS["allsky_width_px"], fwhm_arcmin=30):
    """Full-sky Mollweide: dust intensity textured by the field orientation.

    I, Q, U are smoothed together on the sphere (spin-2 aware) to 30', then
    projected. The plane-of-sky field is the IAU polarization angle + 90 deg,
    converted to image directions with the projection's Jacobian.
    """
    low = [hp.ud_grade(m, nside) for m in planck]
    i_map, q_map, u_map = hp.smoothing(low, fwhm=np.radians(fwhm_arcmin / 60), pol=True)
    u_map = cosmo_to_iau(u_map)
    proj = hp.projector.MollweideProj(xsize=width)
    f = lambda m: proj.projmap(m, lambda x, y, z: hp.vec2pix(nside, x, y, z))
    I, Q, U = f(i_map), f(q_map), f(u_map)
    inside = np.isfinite(I) & (I > -1e20)
    theta = 0.5 * np.arctan2(np.where(inside, U, 0), np.where(inside, Q, 1)) + np.pi / 2
    ang = mollweide_field_angle(proj, theta)
    tex = lic(np.where(inside, ang, 0), length=26)
    lo = np.percentile(I[inside], 0.5)
    dust = stretch(np.where(inside, np.log10(np.clip(I - lo, 1e-6, None)), np.nan), 2, 99.95)
    # Drop the faintest fifth (CMB and CIB dominate there at 30') to black.
    dust = np.clip((dust - 0.2) / 0.8, 0, 1)
    rgba = np.dstack([shade(dust, tex, amount=0.45), inside.astype(float)])
    save_rgba(rgba, "allsky_bfield.png")
    save_gray(np.where(inside, tex, 0), "allsky_lic.jpg")
    np.save(OUT / "allsky_dust.npy", np.where(inside, dust, 0).astype(np.float32))


def planck_maps(planck, target_wcs, shape, smooth_px=12):
    """Dust intensity and plane-of-sky magnetic field angle from Planck 353 GHz.

    Planck maps use the COSMO convention, see cosmo_to_iau().
    The field is the polarization angle + 90 deg, measured from Galactic north;
    it is rotated to celestial north with the local angle between the frames.
    """
    i_map, q_map, u_map = planck
    proj = lambda m: reproject_from_healpix((m, "galactic"), target_wcs, shape_out=shape, nested=False)[0]
    I, Q, U = proj(i_map), proj(q_map), cosmo_to_iau(proj(u_map))
    Qs, Us = gaussian_filter(np.nan_to_num(Q), smooth_px), gaussian_filter(np.nan_to_num(U), smooth_px)
    psi_gal = 0.5 * np.arctan2(Us, Qs)
    b_gal = psi_gal + np.pi / 2

    yy, xx = np.mgrid[0 : shape[0], 0 : shape[1]]
    sky = target_wcs.pixel_to_world(xx.ravel(), yy.ravel())
    gal = sky.galactic
    north = SkyCoord(l=gal.l, b=gal.b + 1 * u.arcmin, frame="galactic").icrs
    rot = sky.icrs.position_angle(north).to_value(u.rad).reshape(shape)
    b_eq = b_gal + rot
    p = np.hypot(Qs, Us) / np.clip(gaussian_filter(np.nan_to_num(I), smooth_px), 1e-6, None)
    return I, b_eq, p


def grid_angle(wcs, shape, pa, step_arcmin=2.0):
    """Turn a position angle on the sky into an angle on the pixel grid.

    pa is measured from north towards east in the WCS's own frame (celestial
    for RA/Dec grids, Galactic for GLON/GLAT). Away from the projection centre
    local north is not the grid's vertical (on the 12 deg LMC grid at
    Dec -68.5 it tilts by up to ~20 deg), so we step along pa on the sky and
    project the step. Returns the angle lic() expects: step (-sin a, cos a)
    in array (x, y) with y up, i.e. measured from +y towards -x.
    """
    yy, xx = np.mgrid[0 : shape[0], 0 : shape[1]]
    sky = wcs.pixel_to_world(xx.ravel(), yy.ravel())
    to = sky.directional_offset_by(np.ravel(pa) * u.rad, step_arcmin * u.arcmin)
    x2, y2 = wcs.world_to_pixel(to)
    a = np.arctan2(-(x2 - xx.ravel()), y2 - yy.ravel())
    return a.reshape(shape)


def north_tilt(wcs, shape):
    """Grid angle of local north at each pixel (0 at the projection centre)."""
    return grid_angle(wcs, shape, np.zeros(shape))


def lic(angle, length=30, seed=1):
    """Line integral convolution of white noise along the field direction.

    angle is measured on the pixel grid from +y towards -x (use grid_angle()
    to convert a sky position angle), so the pixel step is (-sin, cos) in
    array (x, y) with y up.
    """
    ny, nx = angle.shape
    rng = np.random.default_rng(seed)
    noise = gaussian_filter(rng.random((ny, nx)), 0.7)
    dx, dy = -np.sin(angle), np.cos(angle)
    acc = noise.copy()
    w = np.ones_like(noise)
    for sign in (1, -1):
        x, y = np.mgrid[0:ny, 0:nx][1].astype(float), np.mgrid[0:ny, 0:nx][0].astype(float)
        for s in range(1, length):
            ix = np.clip(x, 0, nx - 1).astype(int)
            iy = np.clip(y, 0, ny - 1).astype(int)
            x += sign * dx[iy, ix]
            y += sign * dy[iy, ix]
            k = np.exp(-((s / length) ** 2) * 2)
            acc += k * map_coordinates(noise, [y, x], order=1, mode="nearest")
            w += k
    out = acc / w
    return (out - out.min()) / (out.max() - out.min())


# Clouds the group has published on, as Galactic centre and field width (deg).
REGIONS = {
    "orion": field("orion"),
    "monoceros_ob1": (202.5, 2.0, 8.0),
    "galactic_centre": (0.0, 0.0, 12.0),
    "taurus": (172.0, -14.5, 22.0),
    "mbm12": (159.4, -34.3, 8.0),
}


def regions(planck, size=900):
    """Planck dust + field-line cutouts of other regions the group studies."""
    for name, (l, b, width) in REGIONS.items():
        wcs = tan_wcs("galactic", (l, b), size, width / size)
        proj = lambda m: reproject_from_healpix((m, "galactic"), wcs, shape_out=(size, size), nested=False)[0]
        I, Q, U = proj(planck[0]), proj(planck[1]), cosmo_to_iau(proj(planck[2]))
        sm = max(2.0, 10 * (8.0 / width) ** -0.3)
        ang = 0.5 * np.arctan2(gaussian_filter(np.nan_to_num(U), sm), gaussian_filter(np.nan_to_num(Q), sm)) + np.pi / 2
        tex = lic(grid_angle(wcs, (size, size), ang), length=28)
        dust = stretch(np.log10(np.clip(I, 1e-3, None)), 1, 99.8)
        save_rgba(shade(dust, tex, amount=0.4), f"region_{name}.jpg")
        print("region", name, flush=True)


def main():
    require_files(HI_CUBE, CO_CUBE, CO_RMS, PLANCK)
    OUT.mkdir(parents=True, exist_ok=True)
    print("H I cube", HI_CUBE.name, "...", flush=True)
    wcs = grid_wcs()
    shape = SHAPE
    m0, m1, chans, v, spectrum, to_grid = hi_products(wcs)
    m0 = np.nan_to_num(m0)

    hi = stretch(m0, 2, 99.9, asinh=0.15)
    save_gray(hi, "hi_column.jpg")
    save_rgba(dust_cmap(GAS_STOPS)(hi)[..., :3], "hi_column_color.jpg")

    vel = (np.nan_to_num(m1, nan=np.nanmedian(m1)) - 200) / (320 - 200)
    rgb = colormaps["RdBu_r"](np.clip(vel, 0, 1))[..., :3] * hi[..., None] ** 0.8
    save_rgba(rgb, "hi_velocity.jpg")

    del chans

    print("CO ...", flush=True)
    co = co_moment0(wcs, shape)
    cox = stretch(np.where(np.isfinite(co), co, np.nan), 5, 99.8, asinh=0.1)
    alpha = np.where(np.isfinite(co), np.clip(cox * 1.6, 0, 1), 0)
    rgba = np.dstack([np.full(shape, 0.35), np.full(shape, 0.95), np.full(shape, 1.0), alpha])
    save_rgba(rgba, "co_clouds.png")

    print("Planck ...", flush=True)
    planck = read_planck()
    allsky(planck)
    I, b_eq, p = planck_maps(planck, wcs, shape)
    dust = stretch(I, 2, 99.8, asinh=0.2)
    save_rgba(dust_cmap()(dust)[..., :3], "dust_353.jpg")
    b_grid = grid_angle(wcs, shape, b_eq)
    tex = lic(b_grid)
    save_gray(tex, "bfield_lic.jpg")
    save_rgba(shade(dust, tex, amount=0.4), "bfield_on_dust.jpg")
    # Grid angle for drawing; north tilt so a readout can recover the sky PA.
    np.save(OUT / "bfield_angle.npy", b_grid.astype(np.float32))
    np.save(OUT / "north_tilt.npy", north_tilt(wcs, shape).astype(np.float32))

    meta = {
        "grid": {"nx": shape[1], "ny": shape[0], "wcs": dict(wcs.to_header())},
        "hi_spectrum": {"v_kms": [round(float(x), 2) for x in v], "sum_K": [float(x) for x in spectrum]},
        "sources": {
            "hi": HI_CUBE.name,
            "co": "MAGMA CO(1-0), Wong et al. 2011",
            "dust_bfield": "Planck HFI 353 GHz PR4 (NPIPE), I/Q/U, smoothed",
        },
    }
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1, default=str))
    print("done", flush=True)


if __name__ == "__main__":
    import sys

    if "--regions" in sys.argv:
        require_files(PLANCK)
        OUT.mkdir(parents=True, exist_ok=True)
        regions(read_planck())
    else:
        main()
