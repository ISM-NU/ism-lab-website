"""Run the group's U-Net on a Herschel SPIRE 250 um cutout and compare the
filament angles with the Planck field.

Model: Umetaliev, Alina & Salmenova 2025, AJ 170, 207 (doi 10.3847/1538-3881/adf858).
Code (MIT): github.com/Temirkul/ism-filaments-analysis, Zenodo 10.5281/zenodo.16647869.
Weights: the Google Drive file linked from that README (the checkpoint of the
paper's best run, 54 epochs). Nothing from either is committed; everything lives
in the ignored .cache/unet/.

Two stages, because torch lives in a private venv and healpy/reproject in the
system Python:

    python3 -m venv .cache/unet/.venv      # once; CPU torch, numpy, opencv-python-headless, astropy
    .cache/unet/.venv/bin/python scripts/unet_filaments.py unet
    flock /tmp/ism-planck.lock python3 scripts/unet_filaments.py field
    python3 scripts/unet_filaments.py assets

`unet` crops the cutout from .cache/hips, preprocesses it, runs the network and
writes .cache/unet/unet.npz. `field` adds the Planck field and the ridge map on
the same grid. `assets` writes public/sky/unet-*.png|webp and src/data/unet.json.
"""

import json
import sys
from pathlib import Path

import numpy as np

from facts import field

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / ".cache" / "unet"
HIPS = ROOT / ".cache" / "hips" / "monoceros_ob1_spire250.fits"
WEIGHTS = WORK / "weights.pt"
NPZ = WORK / "unet.npz"
OUT = ROOT / "public" / "sky"
JSON_OUT = ROOT / "src" / "data" / "unet.json"

# G202.3+2.5, the Mon OB1 sub-region of Alina et al. 2022 (A&A 658, A90). The
# SPIRE HiPS cache is on a Galactic TAN grid at 5.27 arcsec per pixel; a 512 px
# cutout is 0.75 deg, about 14 pc at 1.1 kpc, close to the 10 x 3 pc region plus
# its surroundings. 512 is a multiple of 16, which the network needs.
CENTRE = field("filament_net")[:2]
SIZE = 512
# Structuring element of the top-hat. The paper gives no size for Herschel; the
# example notebook uses 7x7 for Planck. See the report in docs for the choice.
TOPHAT = 15
PLANCK_BEAM_ARCMIN = 5.0
PLANCK_FWHM_SMOOTH_ARCMIN = 5.0  # FWHM of the extra Gaussian smoothing, on top of the Planck beam


def cutout():
    from astropy.io import fits
    from astropy.wcs import WCS

    h = fits.getheader(HIPS)
    d = fits.getdata(HIPS).astype(np.float32)
    w = WCS(h)
    x, y = w.world_to_pixel_values(*CENTRE)
    x0, y0 = int(round(float(x))) - SIZE // 2, int(round(float(y))) - SIZE // 2
    sub = d[y0 : y0 + SIZE, x0 : x0 + SIZE]
    wsub = w.slice((slice(y0, y0 + SIZE), slice(x0, x0 + SIZE)))
    return sub, wsub, (x0, y0)


def to_uint8(img):
    """Fill gaps with the median, asinh stretch between the 1st and 99.9th
    percentiles, 8 bit. The paper's inputs are 8 bit images; a linear stretch
    would leave only the brightest ridge, so asinh is used (not specified there)."""
    ok = np.isfinite(img) & (img != 0)
    filled = np.where(ok, img, np.median(img[ok]))
    lo, hi = np.percentile(filled[ok], [1, 99.9])
    x = np.clip((filled - lo) / (hi - lo), 0, None)
    soft = 0.1
    s = np.clip(np.arcsinh(x / soft) / np.arcsinh(1 / soft), 0, 1)
    return (s * 255).astype(np.uint8), ok


def preprocess(img8):
    """Paper section 3.2 (Herschel): top-hat, then Otsu's threshold. Result is a
    0/255 image, like the binary training images."""
    import cv2

    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (TOPHAT, TOPHAT))
    th = cv2.morphologyEx(img8, cv2.MORPH_TOPHAT, k)
    thr, binary = cv2.threshold(th, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th, binary, thr


def load_model():
    import torch

    sys.path.insert(0, str(WORK / "repo" / "src"))
    from model import UNet

    net = UNet(num_classes=181, apply_batch_norm=False)
    # The checkpoint is a pickle from outside the repo, so it is loaded with
    # weights_only. It also stores loss curves as numpy arrays (saved with numpy 1),
    # which need these globals allowed; nothing else is.
    from numpy._core import multiarray

    torch.serialization.add_safe_globals([
        (multiarray._reconstruct, "numpy.core.multiarray._reconstruct"), np.ndarray, np.dtype,
        np.dtypes.Float64DType, np.dtypes.Float32DType, np.dtypes.Int64DType])
    ck = torch.load(WEIGHTS, map_location="cpu", weights_only=True)
    net.load_state_dict(ck["model_state_dict"])
    return net.eval()


def predict(net, x):
    """x: 2D float array in the range the network was trained on (0..255 as in the
    notebook, which feeds the preprocessed image unnormalised). Returns the class
    map: 0 is background, 1..180 an angle label."""
    import torch

    with torch.no_grad():
        t = torch.from_numpy(x.astype(np.float32))[None, None]
        return torch.argmax(net(t), dim=1)[0].numpy().astype(np.uint8)


def calibrate(net):
    """Class value against the screen angle of a straight bar, measured on bars drawn
    with known direction. Screen angle is measured from up, counterclockwise (north
    through east on a sky image with north up and east left). The mask labels in
    data_generator.py read '90 - rotation angle', which does not say which way the
    image y axis runs, so the mapping is measured rather than assumed."""
    import cv2

    rows = []
    for ang in range(0, 180, 15):
        im = np.zeros((256, 256), np.uint8)
        a = np.deg2rad(ang)
        d = np.array([-np.sin(a), -np.cos(a)])  # screen (x right, y down): up is (0,-1), CCW leans left
        p0, p1 = 128 - 90 * d, 128 + 90 * d
        cv2.line(im, tuple(int(v) for v in p0), tuple(int(v) for v in p1), 255, 10)
        m = predict(net, im)
        v = m[(im > 0) & (np.hypot(*np.mgrid[0:256, 0:256] - 128) < 60)]
        rows.append((ang, float(np.median(v)), float(v.std())))
    return rows


def run_unet():
    net = load_model()
    cal = calibrate(net)
    print("screen angle (from up, CCW) -> median class, sd")
    for r in cal:
        print("  %3d -> %6.1f  %4.1f" % r)
    sub, wsub, origin = cutout()
    img8, ok = to_uint8(sub)
    th, binary, thr = preprocess(img8)
    # Array row 0 is the south edge (y up); the network sees images with row 0 at the
    # top, so flip to north-up before and after.
    flip = lambda a: np.flipud(a)
    cls = flip(predict(net, flip(binary).astype(np.float32)))
    np.savez_compressed(NPZ, img=sub, img8=img8, ok=ok, tophat=th, binary=binary, cls=cls, otsu=thr,
                        cal=np.array(cal), origin=np.array(origin))
    on = cls > 0
    print("otsu", thr, "binary fraction", (binary > 0).mean(), "classified fraction", on.mean(),
          "classified outside binary", ((cls > 0) & (binary == 0)).mean())


def circ_diff(a, b):
    """Smallest angle between two orientations (degrees, period 180), in 0..90."""
    return np.abs((a - b + 90.0) % 180.0 - 90.0)


def run_field():
    """Planck 353 GHz field and the site's ridge map on the cutout grid. Run under
    flock /tmp/ism-planck.lock (read_planck loads the full-sky map)."""
    import warnings

    from astropy.io import fits
    from astropy.wcs import WCS
    from reproject import reproject_from_healpix
    from scipy.ndimage import gaussian_filter

    warnings.filterwarnings("ignore")
    sys.path.insert(0, str(ROOT / "scripts"))
    import composites as comp
    import render_lmc as rl

    z = dict(np.load(NPZ))
    x0, y0 = (int(v) for v in z["origin"])
    wcs = WCS(fits.getheader(HIPS)).slice((slice(y0, y0 + SIZE), slice(x0, x0 + SIZE)))
    shape = z["img"].shape
    pix_arcmin = abs(wcs.wcs.cdelt[0]) * 60

    planck = rl.read_planck()
    proj = lambda m: reproject_from_healpix((m, "galactic"), wcs, shape_out=shape, nested=False)[0]
    Q, U = proj(planck[1]), rl.cosmo_to_iau(proj(planck[2]))
    del planck
    sig = PLANCK_FWHM_SMOOTH_ARCMIN / 2.3548 / pix_arcmin
    Qs, Us = gaussian_filter(np.nan_to_num(Q), sig), gaussian_filter(np.nan_to_num(U), sig)
    # Field = polarization angle + 90 deg, from Galactic north through increasing l.
    pa_gal = 0.5 * np.arctan2(Us, Qs) + np.pi / 2
    grid = rl.grid_angle(wcs, shape, pa_gal)  # angle on the image grid, from up toward -x
    field = np.rad2deg(grid) % 180.0

    # Ridge map exactly as composites.py draws it, on the whole cached map, then cropped.
    full = fits.getdata(HIPS).astype(np.float32)
    valid = np.isfinite(full) & (full != 0)
    filled = np.where(valid, full, np.percentile(full[valid], 20))
    rd = comp.ridges(filled) * comp.feather(full, full.shape[0] / 60) * comp.stretch(full, 0.08, lo=20) ** 0.5
    v = rd[rd > 0]
    rd = np.clip(rd / np.percentile(v, 99.5), 0, 1)
    ridge = rd[y0 : y0 + SIZE, x0 : x0 + SIZE]

    # Field samples at beam spacing, taken from the smoothed Q and U.
    step = PLANCK_BEAM_ARCMIN / pix_arcmin
    pts = np.arange(step / 2, shape[0], step)
    px = [(float(a), float(b)) for b in pts for a in pts]
    samples = []
    for a, b in px:
        i, j = int(round(b)), int(round(a))
        samples.append((a, b, float(field[i, j])))
    z.update(field=field.astype(np.float32), ridge=ridge.astype(np.float32), samples=np.array(samples))
    np.savez_compressed(NPZ, **z)
    print("field angle at centre", field[shape[0] // 2, shape[1] // 2], "range", field.min(), field.max())
    print("samples", len(samples), "step px", step)


def regions(cls, min_area=40):
    """Connected pieces of the U-Net mask, each with the circular mean of its pixel
    angles (orientations, so the mean is taken on doubled angles) and the length of
    its major axis. These are what the page draws as angle segments."""
    from scipy.ndimage import label

    lab, n = label(cls > 0, structure=np.ones((3, 3)))
    out = []
    for k in range(1, n + 1):
        yy, xx = np.nonzero(lab == k)
        if yy.size < min_area:
            continue
        a = np.deg2rad(2.0 * (cls[yy, xx] % 180))
        pa = (np.rad2deg(np.arctan2(np.sin(a).mean(), np.cos(a).mean())) / 2.0) % 180.0
        lam = np.linalg.eigvalsh(np.cov(np.vstack([xx, yy])))
        out.append([float(xx.mean()), float(yy.mean()), float(pa), float(np.sqrt(12 * lam[-1])), int(yy.size)])
    return out


def run_assets():
    from PIL import Image

    sys.path.insert(0, str(ROOT / "scripts"))
    import render_lmc as rl

    z = np.load(NPZ)
    img, cls, field, ridge = z["img"], z["cls"], z["field"], z["ridge"]
    ok = z["ok"]
    n = SIZE

    # Display image: asinh stretch of the 250 um map in the site's dust palette.
    fin = np.where(ok, img, np.nan)
    lo, hi = np.nanpercentile(fin, [2, 99.8])
    x = np.clip((np.nan_to_num(fin, nan=lo) - lo) / (hi - lo), 0, None)
    s = np.clip(np.arcsinh(x / 0.1) / np.arcsinh(1 / 0.1), 0, 1)
    rgba = (rl.dust_cmap()(s)[..., :3] * 255).astype(np.uint8)
    rgba[~ok] = 0
    Image.fromarray(np.flipud(rgba)).resize((1024, 1024), Image.LANCZOS).save(OUT / "unet-herschel.webp", quality=88, method=6)

    # Data for the page: R = U-Net class (0 none, 1..180 angle, 180 = 0 deg), G = Planck
    # field angle on the grid (0..179 deg), B = ridge strength. North up, opaque PNG so
    # getImageData returns the values exactly.
    data = np.dstack([cls, np.clip(np.round(field), 0, 179).astype(np.uint8) % 180, np.round(ridge * 255).astype(np.uint8)])
    Image.fromarray(np.flipud(data)).save(OUT / "unet-data.png", optimize=True)

    on = cls > 0
    rel = circ_diff(cls[on] % 180.0, np.round(field)[on])
    hist, _ = np.histogram(rel, bins=18, range=(0, 90))
    cal = z["cal"]
    regs = regions(cls)
    # Row index of the top of the image is n-1 in the arrays (y up); the page counts
    # rows from the top, so flip y of every position here.
    flip = lambda y: float(n - y)
    out = dict(
        region="G202.3+2.5 in Mon OB1",
        centre_gal=list(CENTRE), size_px=n, pixel_arcsec=round(float(abs(1.0) * 0.00146484375 * 3600), 3),
        width_deg=round(n * 0.00146484375, 3), beam_arcmin=PLANCK_BEAM_ARCMIN,
        smooth_fwhm_arcmin=PLANCK_FWHM_SMOOTH_ARCMIN, tophat_px=TOPHAT, otsu=float(z["otsu"]),
        mask_fraction=round(float(on.mean()), 4), n_pixels=int(on.sum()), n_regions=len(regs),
        hist_all=[int(h) for h in hist], bin_deg=5,
        median_rel_deg=round(float(np.median(rel)), 1),
        calibration=[[int(a), float(c)] for a, c, _ in cal],
        field=[[round(a, 1), round(flip(b), 1), round(f, 1)] for a, b, f in z["samples"]],
        segments=[[round(a, 1), round(flip(b), 1), round(p, 1), round(l, 1), m] for a, b, p, l, m in regs],
    )
    JSON_OUT.write_text(json.dumps(out, separators=(",", ":")))
    print("regions", len(regs), "mask px", int(on.sum()), "hist", hist.tolist(), "median", out["median_rel_deg"])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "unet":
        run_unet()
    elif cmd == "field":
        run_field()
    elif cmd == "assets":
        run_assets()
    else:
        sys.exit(__doc__)
