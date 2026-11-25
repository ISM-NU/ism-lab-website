"""Multi-band colour composites of the regions the group studies.

Planck 353 GHz sets the field direction but has a 5' beam, too soft for a
large image. These composites take their detail from sharper public surveys
(Herschel, Spitzer, WISE, SHASSA H-alpha), read straight from HiPS tile
servers, and weave the Planck field in as a line-integral-convolution
texture. Each region gets two images: the clean composite and the same with
the field texture.

Processing per band: background removal, asinh stretch, then a starlet
(a trous wavelet) decomposition whose small scales are boosted and whose
finest scale is damped to keep noise down. Bands are coloured and combined
with a screen blend, so overlapping emission adds light the way it does on a
detector rather than mixing to grey. Point sources come from a short-wavelength
band with the extended emission subtracted.

    LMC_DATA=~/Projects/LMC/lmc-data python3 scripts/composites.py [region ...]
    python3 scripts/composites.py insets   # zoom insets around R136, after lmc

HiPS reprojections are cached in .cache/hips/; images go to public/sky/.
"""

import gzip
import io
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import warnings
from pathlib import Path

import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from astropy_healpix import HEALPix
from astropy.io import fits
from astropy.wcs import WCS
from PIL import Image
from reproject import reproject_from_healpix, reproject_interp
from scipy.ndimage import convolve1d, gaussian_filter, median_filter, zoom

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_lmc as rl  # noqa: E402  (Planck reader, LIC, LMC grid)

warnings.filterwarnings("ignore", module="astropy")
ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "hips"
OUT = ROOT / "public" / "sky"
CREDITS = ROOT / "src" / "data" / "composites.json"

# Surveys: HiPS base URL with FITS tiles and its deepest order, or a NASA
# SkyView survey name (order None). CDS's own tile servers were down when this
# was written, so CDS surveys point at the IRSA mirror.
SKYVIEW = "https://skyview.gsfc.nasa.gov/current/cgi/runquery.pl"
SURVEYS = {
    "spire250": ("https://skies.esac.esa.int/Herschel/SPIRE250", 7, "Herschel SPIRE 250 µm"),
    "pacs70": ("https://skies.esac.esa.int/Herschel/PACS70", 9, "Herschel PACS 70 µm"),
    "pacs160": ("https://skies.esac.esa.int/Herschel/PACS160", 8, "Herschel PACS 160 µm"),
    "irac1": ("https://irsa.ipac.caltech.edu/data/hips/CDS/SPITZER/IRAC1", 9, "Spitzer IRAC 3.6 µm"),
    "irac4": ("https://irsa.ipac.caltech.edu/data/hips/CDS/SPITZER/IRAC4", 9, "Spitzer IRAC 8 µm"),
    "w1": ("https://irsa.ipac.caltech.edu/data/hips/CDS/AllWISE/W1", 8, "WISE 3.4 µm"),
    "w3": ("https://irsa.ipac.caltech.edu/data/hips/CDS/AllWISE/W3", 8, "WISE 12 µm"),
    "halpha": ("SHASSA CC", None, "SHASSA H-alpha"),
}

# Colours follow wavelength, short to long: blue, teal, gold, red. This is the
# usual false-colour order, so hot ionized gas reads blue and cold dust red.
BLUE, TEAL, GOLD, RED = (0.30, 0.52, 1.00), (0.45, 0.95, 0.90), (1.00, 0.72, 0.28), (1.00, 0.26, 0.10)

# name: frame, centre, field width (deg), size (px), layers, star band.
# Layer: (survey, fallback or None, colour, black-point percentile, asinh softness, weight).
REGIONS = {
    "lmc": dict(
        frame="icrs", centre=(rl.GRID["CRVAL1"], rl.GRID["CRVAL2"]), fov=rl.GRID["NAXIS1"] * abs(rl.GRID["CDELT1"]), n=2048,
        layers=[("halpha", None, BLUE, 20, 0.08, 0.9), ("irac4", "w3", TEAL, 20, 0.06, 0.8), ("spire250", None, RED, 20, 0.08, 1.0)],
        stars=("irac1", "w1"),
    ),
    "galactic_centre": dict(
        frame="galactic", centre=(0.0, 0.0), fov=2.0, n=2048,
        layers=[("irac4", "w3", TEAL, 15, 0.10, 0.75), ("pacs70", None, GOLD, 15, 0.08, 0.85), ("spire250", None, RED, 15, 0.12, 1.0)],
        stars=("irac1", "w1"),
    ),
    "monoceros_ob1": dict(
        frame="galactic", centre=(202.9, 1.9), fov=3.0, n=2048,
        layers=[("halpha", None, BLUE, 50, 0.15, 0.55), ("w3", None, TEAL, 45, 0.08, 0.75), ("spire250", None, RED, 20, 0.08, 1.0)],
        stars=("w1", None),
    ),
}


def target_wcs(r):
    return rl.tan_wcs(r["frame"], r["centre"], r["n"], r["fov"] / r["n"])


def hips_order(pix_deg, max_order):
    """Shallowest HiPS order whose pixels are no larger than the target's."""
    for order in range(0, max_order + 1):
        if 58.6 / 2 ** (order + 9) <= pix_deg:
            return order
    return max_order


def compact(v):
    """Every second bit of v, packed: de-interleaves a nested HEALPix index."""
    v = v & 0x5555555555555555
    v = (v | (v >> 1)) & 0x3333333333333333
    v = (v | (v >> 2)) & 0x0F0F0F0F0F0F0F0F
    v = (v | (v >> 4)) & 0x00FF00FF00FF00FF
    v = (v | (v >> 8)) & 0x0000FFFF0000FFFF
    return (v | (v >> 16)) & 0x00000000FFFFFFFF


def get_url(u, tries=5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(u, timeout=120) as f:
                return f.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None  # no tile: outside the survey
            err = e
        except OSError as e:
            err = e
        time.sleep(2 * (i + 1))
    raise err


def sample_hips(url, order, wcs, n, ss=2):
    """Sample a HiPS survey on our grid straight from its FITS tiles.

    Each target pixel's nested HEALPix index at order + log2(tile width) gives
    the tile (high bits) and the pixel in it (low bits, x and y interleaved).
    In the tile array that pixel sits at row width-1-x, column y; this was
    checked against Planck on the ESA and IRSA servers (every other
    orientation is off by degrees). reproject's hips_as_dask_array put the LMC
    about 2 degrees off near the pole, so it is not used. ss x ss subsamples
    per pixel, averaged, keep stars from aliasing."""
    props = dict(l.split("=", 1) for l in get_url(url + "/properties").decode().splitlines() if "=" in l and not l.lstrip().startswith("#"))
    props = {k.strip(): v.strip() for k, v in props.items()}
    tw = int(props.get("hips_tile_width", 512))
    bits = int(np.log2(tw))
    frame = "galactic" if props.get("hips_frame", "equatorial").startswith("gal") else "icrs"
    hp = HEALPix(nside=2 ** (order + bits), order="nested", frame=frame)
    offsets = [(((k % ss) + 0.5) / ss - 0.5, ((k // ss) + 0.5) / ss - 0.5) for k in range(ss * ss)]
    block = 128  # rows per pass; keeps the peak memory to tens of MB

    def indices(i0):
        jj, ii = np.meshgrid(np.arange(n), np.arange(i0, min(i0 + block, n)))
        for dx, dy in offsets:
            yield hp.skycoord_to_healpix(wcs.pixel_to_world(jj + dx, ii + dy)).astype(np.int64)

    tiles = set()
    for i0 in range(0, n, block):
        for ip in indices(i0):
            tiles.update(np.unique(ip >> (2 * bits)).tolist())
    print(f"    {len(tiles)} tiles at order {order}", flush=True)

    def tile(t):
        u = f"{url}/Norder{order}/Dir{(t // 10000) * 10000}/Npix{t}.fits"
        for _ in range(3):
            raw = get_url(u)
            if raw is None:
                return t, None
            if raw[:2] == b"\x1f\x8b":  # some IRSA tiles are gzipped despite the .fits name
                raw = gzip.decompress(raw)
            try:
                return t, fits.getdata(io.BytesIO(raw)).astype(np.float32)
            except OSError:  # a server error page instead of a tile
                time.sleep(3)
        raise RuntimeError(f"HiPS tile {u} is unreadable after 3 tries")

    with ThreadPoolExecutor(4) as ex:  # servers reset connections under more
        data = dict(ex.map(tile, sorted(tiles)))
    out = np.zeros((n, n), np.float32)
    for i0 in range(0, n, block):
        acc = 0
        for ip in indices(i0):
            t, sub = ip >> (2 * bits), ip & (tw * tw - 1)
            row, col = tw - 1 - compact(sub), compact(sub >> 1)
            v = np.full(ip.shape, np.nan, np.float32)
            for k in np.unique(t):
                d = data.get(int(k))
                if d is not None:
                    m = t == k
                    v[m] = d[row[m], col[m]]
            acc = acc + v
        out[i0 : i0 + block] = acc / len(offsets)
    return out


def fetch(name, survey, r, wcs):
    url, max_order, _ = SURVEYS[survey]
    path = CACHE / f"{name}_{survey}.fits"
    # The grid and the survey decide the pixels; a cache from other inputs is refetched.
    key = rl.input_key(url, max_order, r["frame"], r["centre"], r["fov"], r["n"], wcs.to_header().tostring())
    if path.exists():
        try:
            data, hdr = fits.getdata(path, header=True)
            if hdr.get("INPUTKEY") == key:
                return data
        except OSError:
            pass
    if max_order is None:
        # SkyView resamples onto its own TAN grid; match centre and size, then
        # reproject to ours. Its native SHASSA pixels are 48", so 1024 px is plenty.
        q = urllib.parse.urlencode(dict(Survey=url, Position="%f,%f" % r["centre"], Projection="Tan",
                                        Coordinates="J2000" if r["frame"] == "icrs" else "Galactic",
                                        Pixels=1024, Size=r["fov"], Return="FITS"))
        with urllib.request.urlopen(f"{SKYVIEW}?{q}", timeout=600) as f:
            hdu = fits.open(io.BytesIO(f.read()))[0]
        a, _ = reproject_interp((hdu.data.astype(float), WCS(hdu.header)), wcs, shape_out=(r["n"], r["n"]))
        order = "skyview"
    else:
        order = hips_order(r["fov"] / r["n"], max_order)
        a = sample_hips(url, order, wcs, r["n"])
    a = a.astype(np.float32)
    CACHE.mkdir(parents=True, exist_ok=True)
    hdr = wcs.to_header()
    hdr["INPUTKEY"] = key
    with rl.atomic(path) as tmp:
        fits.writeto(tmp, a, hdr, overwrite=True)
    print(f"  {survey} order {order}", flush=True)
    return a


def coverage(a):
    return float(np.mean(np.isfinite(a) & (a != 0)))


def starlet(x, scales=5):
    """A trous wavelet planes (B3 spline) and the smooth residual."""
    k = np.array([1, 4, 6, 4, 1], float) / 16
    planes, c = [], x
    for j in range(scales):
        step = 2 ** j
        kj = np.zeros(4 * step + 1)
        kj[::step] = k
        s = convolve1d(convolve1d(c, kj, axis=0, mode="reflect"), kj, axis=1, mode="reflect")
        planes.append(c - s)
        c = s
    return planes, c


def enhance(x, gains=(0.6, 1.5, 1.45, 1.25, 1.1)):
    """Boost small and mid scales, damp the finest (noise) scale."""
    planes, res = starlet(x, len(gains))
    out = res + sum(g * p for g, p in zip(gains, planes))
    return np.clip(out, 0, 1)


def levels(a, lo=15, hi=99.9):
    v = a[np.isfinite(a) & (a != 0)]
    return np.percentile(v, [lo, hi])


def stretch(a, soft, lo=15, hi=99.9, lv=None):
    """asinh stretch between the lo and hi percentiles of a, or between the
    given levels lv (the insets reuse the LMC composite's levels)."""
    lo_v, hi_v = levels(a, lo, hi) if lv is None else lv
    x = np.clip((np.nan_to_num(a, nan=lo_v) - lo_v) / (hi_v - lo_v), 0, None)
    return np.clip(np.arcsinh(x / soft) / np.arcsinh(1 / soft), 0, 1)


def destar(a, native_arcsec, fov, n):
    """Remove point sources from a coarse survey (SHASSA, 48" pixels) at its own
    resolution, then upsample smoothly, so stars do not show as square blocks."""
    f = max(1, round(native_arcsec / 3600 / (fov / n)))
    small = np.nan_to_num(a[::f, ::f])
    med = median_filter(small, size=7)
    res = small - med
    mad = np.median(np.abs(res - np.median(res))) * 1.4826
    # Both signs: the continuum-corrected frame leaves over-subtracted holes.
    clean = np.where(np.abs(res) > 3 * mad, med, small)
    return gaussian_filter(zoom(clean, f, order=3)[:n, :n], f / 2)


def flatten(a, f=16, size=25):
    """Subtract a large median background. WISE atlas tiles carry different
    zero levels; a median follows their step edges, so whole tile plateaus
    subtract out while structure smaller than about f*size pixels stays."""
    small = np.nan_to_num(a[::f, ::f])
    bg = zoom(median_filter(small, size=size), f, order=1)[: a.shape[0], : a.shape[1]]
    return a - bg


def feather(a, width):
    """Coverage mask with a soft edge, so survey borders do not show as cuts."""
    m = (np.isfinite(a) & (a != 0)).astype(float)
    return np.clip(gaussian_filter(m, width) * 2 - 1, 0, 1) * m


def star_layer(a):
    """Point sources: the band minus its local median, stretched hard."""
    a = np.nan_to_num(a)
    bg = median_filter(a, size=9)
    pts = np.clip(a - bg, 0, None)
    v = pts[pts > 0]
    if v.size == 0:
        return np.zeros_like(a)
    # Ignore the faintest 90% of residuals: they are noise and unresolved stars.
    lo, hi = np.percentile(v, [90, 99.95])
    x = np.clip((pts - lo) / (hi - lo), 0, 1) ** 0.8
    return np.clip(x + 0.6 * gaussian_filter(x, 1.2), 0, 1)


def field_angle(r, wcs, planck):
    """Plane-of-sky field position angle (from north in the grid's frame). Q and U are smoothed with a
    10' sigma Gaussian (FWHM about 24') for signal to noise, much wider than the 5' beam."""
    n = r["n"]
    smooth = (10 / 60) / (r["fov"] / n)
    if r["frame"] == "icrs":
        _, ang, _ = rl.planck_maps(planck, wcs, (n, n), smooth_px=smooth)
        return ang
    proj = lambda m: reproject_from_healpix((m, "galactic"), wcs, shape_out=(n, n), nested=False)[0]
    Q, U = proj(planck[1]), rl.cosmo_to_iau(proj(planck[2]))
    return 0.5 * np.arctan2(gaussian_filter(np.nan_to_num(U), smooth), gaussian_filter(np.nan_to_num(Q), smooth)) + np.pi / 2


def tone(rgb):
    """Black point, a gentle S-curve and a small saturation lift."""
    rgb = np.clip((rgb - 0.03) / 0.97, 0, 1)
    t = rgb ** 1.15
    rgb = 0.35 * t * t * (3 - 2 * t) + 0.65 * t  # part smoothstep, part gamma
    lum = rgb.mean(axis=2, keepdims=True)
    return np.clip(lum + 1.2 * (rgb - lum), 0, 1)


def save(rgb, stem, widths=(960, 1920), vignette=False):
    img = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).transpose(Image.FLIP_TOP_BOTTOM)
    for w in widths:
        im = img.resize((w, w), Image.LANCZOS)
        name = f"{stem}-{w}.webp"
        if vignette:
            # Round fade to transparent, as the scroll zoom expects (see web_assets.save).
            yy, xx = np.mgrid[0:w, 0:w]
            rad = np.hypot(xx - w / 2, yy - w / 2) / (w / 2)
            im = im.convert("RGBA")
            im.putalpha(Image.fromarray((np.clip((1 - rad) / 0.35, 0, 1) ** 1.5 * 255).astype(np.uint8)))
            name = f"{stem}-v-{w}.webp"
        with rl.atomic(OUT / name) as tmp:
            im.save(tmp, quality=86, method=6)


def ridges(a, sigmas=(1.5, 3, 6)):
    """Filament ridges: the strongest negative Hessian eigenvalue of the log
    intensity over several scales, the usual first step of filament finders."""
    x = np.log10(np.clip(np.nan_to_num(a), np.nanpercentile(a, 5) or 1e-6, None))
    best = np.zeros_like(x)
    for s in sigmas:
        xx = gaussian_filter(x, s, order=(0, 2))
        yy = gaussian_filter(x, s, order=(2, 0))
        xy = gaussian_filter(x, s, order=(1, 1))
        lam = 0.5 * (xx + yy) - np.sqrt(0.25 * (xx - yy) ** 2 + xy ** 2)
        best = np.maximum(best, -lam * s ** 2)
    v = best[best > 0]
    return np.clip(best / np.percentile(v, 99.5), 0, 1) ** 0.8 if v.size else best


def composite(name, planck):
    r = REGIONS[name]
    wcs = target_wcs(r)
    print(name, flush=True)
    used, out = [], np.ones((r["n"], r["n"], 3))
    for survey, fallback, colour, lo, soft, weight in r["layers"]:
        a = fetch(name, survey, r, wcs)
        if coverage(a) < 0.9 and fallback:
            a = fetch(name, fallback, r, wcs)
            survey = fallback
        used.append(survey)
        edge = feather(a, r["n"] / 120)
        if SURVEYS[survey][1] is None:
            a = destar(a, 48, r["fov"], r["n"])
        if survey.startswith("w"):
            a = flatten(a)
        x = enhance(stretch(a, soft, lo=lo)) * weight * edge
        out *= 1 - np.array(colour) * x[..., None]  # screen blend
    star_band = r["stars"][0]
    s = fetch(name, star_band, r, wcs)
    if coverage(s) < 0.9 and r["stars"][1]:
        star_band = r["stars"][1]
        s = fetch(name, star_band, r, wcs)
    used.append(star_band)
    out *= 1 - 0.6 * np.array((0.9, 0.95, 1.0)) * star_layer(s)[..., None]
    rgb = tone(1 - out)
    save(rgb, f"comp-{name}")

    # LIC on a quarter-resolution grid, upsampled and softened, so the field
    # reads as broad flowing lines rather than pixel scratches.
    f = 4
    pa = field_angle(r, wcs, planck)[::f, ::f]
    ang = rl.grid_angle(wcs.slice((slice(None, None, f), slice(None, None, f))), pa.shape, pa)
    tex = gaussian_filter(zoom(rl.lic(ang, length=30), f, order=1)[: r["n"], : r["n"]], 1.6)
    tex = (tex - tex.mean()) / (tex.std() + 1e-9)
    lum = rgb.max(axis=2, keepdims=True)
    k = 0.12 * (1 - lum ** 2)  # texture in faint and mid gas, not on peaks
    # Multiplying alone leaves dark gas untouched; a faint additive glow along
    # the field lines, scaled by the smoothed emission, shows the field there too.
    halo = gaussian_filter(lum[..., 0], r["n"] / 80) ** 0.5
    glow = 0.07 * np.clip(tex, 0, None) * halo
    field = np.clip(rgb * (1 + k * tex[..., None]) + glow[..., None] * np.array((0.85, 0.9, 1.0)), 0, 1)
    save(field, f"comp-{name}-field")
    if name == "lmc":
        save(field, "comp-lmc-field", widths=(1400, 2048), vignette=True)
    # Ridge map of the cold dust, drawn in signal red on black for the lens.
    # Fill gaps before filtering so survey borders do not read as ridges, then
    # mask with the feathered coverage and weight by brightness, which drops
    # the scan stripes and noise at the map edges.
    dust = fetch(name, r["layers"][-1][0], r, wcs)
    valid = np.isfinite(dust) & (dust != 0)
    filled = np.where(valid, dust, np.percentile(dust[valid], 20))
    rd = ridges(filled) * feather(dust, r["n"] / 60) * stretch(dust, 0.08, lo=20) ** 0.5
    v = rd[rd > 0]
    rd = np.clip(rd / np.percentile(v, 99.5), 0, 1) if v.size else rd
    save(rd[..., None] * np.array((1.0, 0.24, 0.14)) + 0.25 * rd[..., None] ** 3, f"comp-{name}-ridges", widths=(960, 1920))
    return [SURVEYS[s][2] for s in dict.fromkeys(used)]


# Nested renders around R136 for the scroll zoom (PullBack.astro), which
# otherwise stretches a few hundred pixels of the LMC composite across the
# screen. Each inset is a window of the LMC composite's own TAN grid at a finer
# pixel scale, so it registers with it exactly (a TAN grid centred on 30 Dor
# would be turned about 3.5 deg against it), and it reuses that composite's
# stretch levels, so colours match across the seam.
# name, width (deg), size (px), source of the 8-12 um layer and of the stars.
R136 = (84.6766, -69.1008)  # R136a1, J2000
INSETS = [("lmc-30dor", 2.4, 2048, "w3", "w1"), ("lmc-tarantula", 0.6, 2048, "irac4", "irac1")]
INSET_JSON = ROOT / "src" / "data" / "zoom-insets.json"


def insets():
    from scipy.ndimage import map_coordinates

    r = REGIONS["lmc"]
    nb = r["n"]
    bw = target_wcs(r)
    cb = nb / 2 - 0.5  # 0-based reference pixel of the LMC grid
    xb, yb = (float(v) for v in bw.world_to_pixel_values(*R136))
    # The LMC composite's processed bands, as composite() makes them; their
    # levels, and for WISE the subtracted background, carry over to the insets.
    (_, _, BL, blo, bsoft, bwt), (_, _, TL, tlo, tsoft, twt), (_, _, RD, rlo, rsoft, rwt) = r["layers"]
    ha = destar(fetch("lmc", "halpha", r, bw), 48, r["fov"], nb)
    w3 = fetch("lmc", "w3", r, bw)
    w3_bg = w3 - flatten(w3)
    sp = fetch("lmc", "spire250", r, bw)
    lv_ha, lv_w3, lv_sp = levels(ha, blo), levels(w3 - w3_bg, tlo), levels(sp, rlo)

    boxes = []
    for stem, fov, n, warm, star in INSETS:
        s = (fov / n) / (r["fov"] / nb)  # inset pixel in LMC-grid pixels
        ci = n / 2 - 0.5 - (xb - cb) / s, n / 2 - 0.5 - (yb - cb) / s
        h = bw.to_header()
        h.update(NAXIS1=n, NAXIS2=n, CRPIX1=ci[0] + 1, CRPIX2=ci[1] + 1, CDELT1=-fov / n, CDELT2=fov / n)
        wcs = WCS(h)
        ri = dict(frame="icrs", centre=R136, fov=fov, n=n)
        jj, ii = np.meshgrid(np.arange(n), np.arange(n))
        on_base = [cb + (ii - ci[1]) * s, cb + (jj - ci[0]) * s]  # (row, col) on the LMC grid
        from_base = lambda a: map_coordinates(np.nan_to_num(a), on_base, order=3, mode="nearest")
        print(stem, flush=True)

        warm_a = fetch(stem, "w3", ri, wcs) - from_base(w3_bg)
        if warm != "w3":
            # IRAC 8 um is sharper than WISE 12 um and traces the same PAH and
            # warm dust emission. Put it in the WISE units the levels expect
            # with a robust linear fit at WISE resolution.
            ir = fetch(stem, warm, ri, wcs)
            beam = (6.5 / 3600) / (fov / n) / 2.355
            x, y = gaussian_filter(np.nan_to_num(ir), beam).ravel(), warm_a.ravel()
            m = np.isfinite(y) & (x != 0)
            x, y = x[m][::7], y[m][::7]
            for _ in range(4):
                A = np.polyfit(x, y, 1)
                res = y - np.polyval(A, x)
                keep = np.abs(res) < 3 * 1.4826 * np.median(np.abs(res))
                x, y = x[keep], y[keep]
            print(f"  {warm} -> w3: slope {A[0]:.4g}, offset {A[1]:.4g}", flush=True)
            warm_a = np.where(ir != 0, np.polyval(A, np.nan_to_num(ir)), warm_a)
        layers = [
            (from_base(ha), BL, bsoft, bwt, lv_ha),
            (warm_a, TL, tsoft, twt, lv_w3),
            # SPIRE 250 um has an 18" beam, which the LMC grid's 21" pixels
            # already hold, so it is resampled like H-alpha.
            (from_base(sp), RD, rsoft, rwt, lv_sp),
        ]
        out = np.ones((n, n, 3))
        for a, colour, soft, weight, lv in layers:
            out *= 1 - np.array(colour) * (enhance(stretch(a, soft, lv=lv)) * weight)[..., None]
        out *= 1 - 0.6 * np.array((0.9, 0.95, 1.0)) * star_layer(fetch(stem, star, ri, wcs))[..., None]
        rgb = tone(1 - out)
        img = Image.fromarray((rgb * 255).astype(np.uint8)).transpose(Image.FLIP_TOP_BOTTOM).convert("RGBA")
        # Soft square edge, so the inset fades into the image under it.
        ramp = np.clip(np.minimum(np.arange(n), np.arange(n)[::-1]) / (0.12 * n), 0, 1)
        ramp = ramp * ramp * (3 - 2 * ramp)
        img.putalpha(Image.fromarray((np.outer(ramp, ramp) * 255).astype(np.uint8)))
        for w in (1024, 2048):
            with rl.atomic(OUT / f"{stem}-{w}.webp") as tmp:
                img.resize((w, w), Image.LANCZOS).save(tmp, quality=84, method=6)
        # Position in the LMC image (fractions of its width, y down), pixel edges.
        x0 = (cb + (-0.5 - ci[0]) * s + 0.5) / nb
        y1 = (cb + (n - 0.5 - ci[1]) * s + 0.5) / nb
        boxes.append(dict(src=f"/sky/{stem}", x=round(x0, 6), y=round(1 - y1, 6), w=round(n * s / nb, 6)))
    with rl.atomic(INSET_JSON) as tmp:
        tmp.write_text(json.dumps(boxes, indent=1) + "\n")


def main():
    if sys.argv[1:] == ["insets"]:
        return insets()
    names = sys.argv[1:] or list(REGIONS)
    planck = rl.read_planck()
    credits = json.loads(CREDITS.read_text()) if CREDITS.exists() else {}
    for name in names:
        credits[name] = composite(name, planck) + ["Planck 353 GHz (field)"]
    with rl.atomic(CREDITS) as tmp:
        tmp.write_text(json.dumps(credits, indent=1, ensure_ascii=False, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
