"""Render web-ready sky and LMC images from public survey data.

Inputs (from the LMC workspace's shared data folder, LMC_DATA):
  - H I: GASKAP-HI + Parkes combined cube on the GASS velocity range (K, 1 km/s)
  - CO: MAGMA CO(1-0) cube and its rms cube
  - Dust and magnetic field: Planck HFI 353 GHz I, Q, U (PR3, HEALPix, Galactic)

Everything is put on one equatorial TAN grid (the H I grid binned by BIN), so
the layers line up pixel for pixel and can be stacked or cross-faded in the
browser. Outputs go to OUT as 8-bit images plus a small JSON with the grid.

Run: LMC_DATA=~/Projects/LMC/lmc-data python3 -I scripts/render_lmc.py
"""

import json
import os
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

DATA = Path(os.environ.get("LMC_DATA", "~/Projects/LMC/lmc-data")).expanduser()
OUT = Path(os.environ.get("OUT", Path(__file__).resolve().parent.parent / "assets" / "lmc"))
BIN = 2  # 2174 px -> 1087 px, 40" pixels over the 12 deg field
N_CHANNEL_FRAMES = 48

HI_CUBE = DATA / "exp_raw/Tb_combined_LMC_182_339_res1_3pperb_reprojected_on_gass_masked.fits"
CO_CUBE = DATA / "exp_raw/lmc_v11.co.vradlsr.base.fits"
CO_RMS = DATA / "exp_raw/lmc_v11.co.vradlsr.rms.fits"
PLANCK = DATA / "external/HFI_SkyMap_353-BPassCorrected_2048_R4.00_full.fits"


def binned(a, b=BIN):
    ny, nx = (a.shape[0] // b) * b, (a.shape[1] // b) * b
    return np.nanmean(a[:ny, :nx].reshape(ny // b, b, nx // b, b), axis=(1, 3))


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


def hi_products():
    """Moment 0, moment 1 and a strip of channel maps from the H I cube."""
    with fits.open(HI_CUBE, memmap=True) as h:
        cube = h[0].data
        hdr = h[0].header
        nchan = cube.shape[0]
        v = (hdr["CRVAL3"] + (np.arange(nchan) + 1 - hdr["CRPIX3"]) * hdr["CDELT3"]) / 1e3
        dv = abs(hdr["CDELT3"]) / 1e3
        ny, nx = cube.shape[1] // BIN, cube.shape[2] // BIN
        m0 = np.zeros((ny, nx))
        m1 = np.zeros((ny, nx))
        chans = []
        for k in range(nchan):
            plane = binned(np.nan_to_num(np.asarray(cube[k], dtype=np.float32)))
            m0 += plane * dv
            m1 += plane * v[k] * dv
            chans.append(plane.astype(np.float32))
        wcs = WCS(hdr).celestial
    wcs = wcs[::BIN, ::BIN]
    with np.errstate(invalid="ignore", divide="ignore"):
        m1 = np.where(m0 > np.percentile(m0, 35), m1 / m0, np.nan)
    chans = np.stack(chans)
    return m0, m1, chans, v, wcs


def write_channels(chans, v):
    """Velocity sweep: N frames, each the mean of a block of channels."""
    edges = np.linspace(0, len(v), N_CHANNEL_FRAMES + 1).astype(int)
    hi = np.percentile(chans[chans > 0], 99.8)
    frames = []
    cmap = colormaps["magma"]
    (OUT / "channels").mkdir(exist_ok=True)
    for i in range(N_CHANNEL_FRAMES):
        a, b = edges[i], edges[i + 1]
        plane = chans[a:b].mean(axis=0)
        x = np.arcsinh(np.clip(plane / hi, 0, 1) / 0.08) / np.arcsinh(1 / 0.08)
        save_rgba(cmap(x)[..., :3], f"channels/{i:02d}.jpg", quality=80)
        frames.append(round(float(v[a:b].mean()), 1))
    return frames


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
    return hp.read_map(PLANCK, field=(0, 1, 2), dtype=np.float32)


def allsky(planck, nside=256, width=2400):
    """Full-sky Mollweide: dust intensity textured by the field direction.

    Q/U are averaged down to nside 256 (about 14') before taking angles; the
    angle is used directly in the projected plane, which is a fair visual
    approximation away from the map edge.
    """
    i_map, q_map, u_map = (hp.ud_grade(m, nside) for m in planck)
    u_map = -u_map  # COSMO -> IAU
    proj = hp.projector.MollweideProj(xsize=width)
    f = lambda m: proj.projmap(m, lambda x, y, z: hp.vec2pix(nside, x, y, z))
    I, Q, U = f(i_map), f(q_map), f(u_map)
    inside = np.isfinite(I) & (I > -1e20)
    Qs, Us = (gaussian_filter(np.where(inside, a, 0), 1.5) for a in (Q, U))
    ang = 0.5 * np.arctan2(Us, Qs) + np.pi / 2
    tex = lic(ang, length=24)
    dust = stretch(np.where(inside, np.log10(np.clip(I, 1e-3, None)), np.nan), 1, 99.9)
    rgb = colormaps["inferno"](dust)[..., :3] * (0.4 + 0.8 * tex[..., None])
    rgba = np.dstack([np.clip(rgb, 0, 1), inside.astype(float)])
    save_rgba(rgba, "allsky_bfield.png")
    save_gray(np.where(inside, tex, 0), "allsky_lic.jpg")


def planck_maps(planck, target_wcs, shape, smooth_px=12):
    """Dust intensity and plane-of-sky magnetic field angle from Planck 353 GHz.

    Planck maps use the COSMO convention, so U is negated to get IAU angles.
    The field is the polarization angle + 90 deg, measured from Galactic north;
    it is rotated to celestial north with the local angle between the frames.
    """
    i_map, q_map, u_map = planck
    proj = lambda m: reproject_from_healpix((m, "galactic"), target_wcs, shape_out=shape, nested=False)[0]
    I, Q, U = proj(i_map), proj(q_map), -proj(u_map)
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


def lic(angle, length=30, seed=1):
    """Line integral convolution of white noise along the field direction.

    angle is the position angle east of north; image x grows to the west on
    this grid (CDELT1 < 0) after the vertical flip used for saving, so the
    pixel step is (-sin, cos) in array (x, y) with y up.
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
    "orion": (209.0, -19.0, 24.0),
    "monoceros_ob1": (202.5, 2.0, 8.0),
    "galactic_centre": (0.0, 0.0, 12.0),
    "taurus": (172.0, -14.5, 22.0),
    "mbm12": (159.4, -34.3, 8.0),
}


def regions(planck, size=900):
    """Planck dust + field-line cutouts of other regions the group studies."""
    for name, (l, b, width) in REGIONS.items():
        hdr = fits.Header()
        hdr.update(NAXIS=2, NAXIS1=size, NAXIS2=size, CTYPE1="GLON-TAN", CTYPE2="GLAT-TAN",
                   CRVAL1=l, CRVAL2=b, CRPIX1=size / 2 + 0.5, CRPIX2=size / 2 + 0.5,
                   CDELT1=-width / size, CDELT2=width / size)
        wcs = WCS(hdr)
        proj = lambda m: reproject_from_healpix((m, "galactic"), wcs, shape_out=(size, size), nested=False)[0]
        I, Q, U = proj(planck[0]), proj(planck[1]), -proj(planck[2])
        sm = max(2.0, 10 * (8.0 / width) ** -0.3)
        ang = 0.5 * np.arctan2(gaussian_filter(np.nan_to_num(U), sm), gaussian_filter(np.nan_to_num(Q), sm)) + np.pi / 2
        tex = lic(ang, length=28)
        dust = stretch(np.log10(np.clip(I, 1e-3, None)), 1, 99.8)
        rgb = colormaps["inferno"](dust)[..., :3] * (0.4 + 0.8 * tex[..., None])
        save_rgba(np.clip(rgb, 0, 1), f"region_{name}.jpg")
        print("region", name, flush=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("H I cube ...", flush=True)
    m0, m1, chans, v, wcs = hi_products()
    shape = m0.shape

    hi = stretch(m0, 2, 99.9, asinh=0.15)
    save_gray(hi, "hi_column.jpg")
    save_rgba(colormaps["magma"](hi)[..., :3], "hi_column_color.jpg")

    vel = (np.nan_to_num(m1, nan=np.nanmedian(m1)) - 200) / (320 - 200)
    rgb = colormaps["RdBu_r"](np.clip(vel, 0, 1))[..., :3] * hi[..., None] ** 0.8
    save_rgba(rgb, "hi_velocity.jpg")

    frames = write_channels(chans, v)
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
    save_rgba(colormaps["inferno"](dust)[..., :3], "dust_353.jpg")
    tex = lic(b_eq)
    save_gray(tex, "bfield_lic.jpg")
    combo = colormaps["inferno"](dust)[..., :3] * (0.45 + 0.75 * tex[..., None])
    save_rgba(np.clip(combo, 0, 1), "bfield_on_dust.jpg")
    np.save(OUT / "bfield_angle.npy", b_eq.astype(np.float32))

    meta = {
        "grid": {"nx": shape[1], "ny": shape[0], "wcs": dict(wcs.to_header())},
        "channels_kms": frames,
        "sources": {
            "hi": "GASKAP-HI + Parkes (GASS) combined LMC cube",
            "co": "MAGMA CO(1-0), Wong et al. 2011",
            "dust_bfield": "Planck HFI 353 GHz PR3, I/Q/U, smoothed",
        },
    }
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1, default=str))
    print("done", flush=True)


if __name__ == "__main__":
    import sys

    if "--regions" in sys.argv:
        OUT.mkdir(parents=True, exist_ok=True)
        regions(read_planck())
    else:
        main()
