"""Planck PR4 353 GHz Stokes Q, U and their noise covariances on a small LMC patch,
for the estimator bench (src/components/EstimatorBench.astro).

Writes src/data/bench_patch.json: Q, U (IAU convention) and C_QQ, C_UU, C_QU on a
north-up TAN grid, after smoothing with a Gaussian kernel in pixel space. The bench
applies the estimators in src/lib/estimators.ts to it in the browser, so the page and
the tests run the same code.

Smoothing and noise. Each output pixel is a normalised Gaussian-weighted sum of the
HEALPix pixels around it, x_s = sum_j w_j x_j with sum_j w_j = 1. For noise that is
independent between HEALPix pixels the covariance of the sum is sum_j w_j^2 C_j, so the
covariance maps are summed with the squared weights (not the weights, and not the
squared weights renormalised). The PR4 covariance columns are per-pixel white-noise
estimates; correlated noise between pixels (stripes, 1/f) is not in them, so the
smoothed sigma is a lower bound where that noise matters. `--check` verifies the
propagation with a Monte Carlo on one output pixel.

The kernel is narrow (FWHM 10') and the LMC sits at b = -33 deg, so the change of the
Galactic polarization reference frame across one kernel is far below a degree and
Q, U are summed without parallel transport.

Intensity is not used: its zero level (CMB, CIB monopole, Galactic offset; Alina et
al. 2023 subtract them) would set p = P/I exactly where S/N is low. The bench works
with polarized intensity P, for which the estimators are identical with sigma in K.

Run (loads the full-sky map, so take the shared lock):
  flock /tmp/ism-planck.lock python3 scripts/render_bench.py [--survey] [--check]
"""

import argparse
import json
import sys
from pathlib import Path

import healpy as hp
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
import astropy.units as u

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_lmc import GRID, PLANCK, cosmo_to_iau, read_planck, tan_wcs  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "src" / "data" / "bench_patch.json"
FWHM_ARCMIN = 10.0
BEAM_ARCMIN = 5.0  # native 353 GHz resolution, "~5 arcmin" (Alina et al. 2023, Sect. 2.2)


def tan_grid(ra, dec, size_deg, pix_arcmin):
    n = int(round(size_deg * 60 / pix_arcmin))
    return tan_wcs("icrs", (ra, dec), n, pix_arcmin / 60, radesys=None), n


def smooth_patch(maps, cov_cols, nside, wcs, n, fwhm_arcmin):
    """Gaussian-weighted Q, U and sum w^2 C at each grid pixel. maps: dict of RING arrays;
    cov_cols: dict of NESTED arrays (FITS columns, memory mapped)."""
    sig = np.radians(fwhm_arcmin / 60) / np.sqrt(8 * np.log(2))
    yy, xx = np.mgrid[0:n, 0:n]
    sky = wcs.pixel_to_world(xx.ravel(), yy.ravel()).galactic
    vec = hp.ang2vec(sky.l.deg, sky.b.deg, lonlat=True)
    out = {k: np.zeros(n * n) for k in ("q", "u", "qq", "uu", "qu")}
    for k, v in enumerate(vec):
        pix = hp.query_disc(nside, v, 3.5 * sig)
        d = np.arccos(np.clip(np.dot(np.array(hp.pix2vec(nside, pix)).T, v), -1, 1))
        w = np.exp(-0.5 * (d / sig) ** 2)
        w /= w.sum()
        nest = hp.ring2nest(nside, pix)
        out["q"][k] = w @ maps["q"][pix]
        out["u"][k] = w @ maps["u"][pix]
        w2 = w * w
        for c in ("qq", "uu", "qu"):
            out[c][k] = w2 @ cov_cols[c][nest]
    return {k: v.reshape(n, n) for k, v in out.items()}


def load():
    I, Q, U = read_planck()
    del I
    maps = {"q": Q, "u": cosmo_to_iau(U)}
    h = fits.open(PLANCK, memmap=True)
    d = h[1].data
    cov = {"qq": np.asarray(d["QQ_COV"]).ravel(), "uu": np.asarray(d["UU_COV"]).ravel(),
           "qu": cosmo_to_iau(np.asarray(d["QU_COV"]).ravel())}
    assert h[1].header["ORDERING"].strip() == "NESTED"
    return maps, cov, hp.get_nside(Q)


def check(maps, cov, nside, wcs, n, rng=np.random.default_rng(3)):
    """Monte Carlo: draw white noise from C in each HEALPix pixel, smooth it, compare
    the sample covariance with sum w^2 C at the central output pixel."""
    sig = np.radians(FWHM_ARCMIN / 60) / np.sqrt(8 * np.log(2))
    c = wcs.pixel_to_world(n // 2, n // 2).galactic
    v = hp.ang2vec(c.l.deg, c.b.deg, lonlat=True)
    pix = hp.query_disc(nside, v, 3.5 * sig)
    d = np.arccos(np.clip(np.dot(np.array(hp.pix2vec(nside, pix)).T, v), -1, 1))
    w = np.exp(-0.5 * (d / sig) ** 2)
    w /= w.sum()
    nest = hp.ring2nest(nside, pix)
    qq, uu, qu = cov["qq"][nest], cov["uu"][nest], cov["qu"][nest]
    a = np.sqrt(qq)
    b = qu / a
    dd = np.sqrt(np.maximum(uu - b * b, 0))
    z1 = rng.standard_normal((4000, pix.size))
    z2 = rng.standard_normal((4000, pix.size))
    sq = (a * z1) @ w
    su = (b * z1 + dd * z2) @ w
    pred = (w * w) @ qq, (w * w) @ uu, (w * w) @ qu
    got = np.var(sq), np.var(su), np.mean(sq * su)
    print("MC check (pred, got) QQ %.3e %.3e  UU %.3e %.3e  QU %.3e %.3e" % (pred[0], got[0], pred[1], got[1], pred[2], got[2]))
    print("raw pixel sigma_Q %.2f uK -> smoothed %.2f uK" % (1e6 * np.sqrt(np.median(qq)), 1e6 * np.sqrt(pred[0])))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--survey", action="store_true", help="print P/sigma statistics over the LMC and stop")
    ap.add_argument("--check", action="store_true", help="Monte Carlo check of the covariance propagation")
    ap.add_argument("--ra", type=float, default=round(GRID["CRVAL1"], 3))
    ap.add_argument("--dec", type=float, default=round(GRID["CRVAL2"], 3))
    ap.add_argument("--size", type=float, default=3.0)
    ap.add_argument("--pix", type=float, default=3.0)
    a = ap.parse_args()

    maps, cov, nside = load()
    if a.survey:
        wcs, n = tan_grid(a.ra, a.dec, 10.0, 6.0)
        s = smooth_patch(maps, cov, nside, wcs, n, FWHM_ARCMIN)
        P = np.hypot(s["q"], s["u"])
        snr = P / np.sqrt(0.5 * (s["qq"] + s["uu"]))
        print("10 deg LMC field, P/sigma percentiles 5/25/50/75/95:", np.percentile(snr, [5, 25, 50, 75, 95]).round(2))
        # coarse map of S/N in 1 deg blocks to choose a patch
        blk = snr.reshape(10, n // 10, 10, n // 10).transpose(0, 2, 1, 3).reshape(10, 10, -1)
        low = (blk < 3).mean(-1)
        for j in range(9, -1, -1):
            row = []
            for i in range(10):
                ra, dec = wcs.pixel_to_world_values((i + 0.5) * n / 10, (j + 0.5) * n / 10)
                row.append(f"{low[j, i]:.2f}")
            print(" ".join(row), f"  dec~{dec:.1f}")
        print("columns left to right are east to west; values are the fraction with P/sigma < 3")
        return

    wcs, n = tan_grid(a.ra, a.dec, a.size, a.pix)
    if a.check:
        check(maps, cov, nside, wcs, n)
    s = smooth_patch(maps, cov, nside, wcs, n, FWHM_ARCMIN)
    scale = 1e6  # K_CMB to uK_CMB
    rnd = lambda x, f: [float(f"{v:.4g}") for v in (x * f).ravel()]
    data = {
        "source": "Planck PR4 (NPIPE) 353 GHz, HFI_SkyMap_353-BPassCorrected_2048_R4.00_full.fits; "
                  "Q, U and QQ/UU/QU covariance columns in the Galactic frame (not rotated to the equatorial grid; "
                  "only P is used), IAU convention (U and C_QU negated from COSMO). "
                  "Made by scripts/render_bench.py.",
        "unit": "uK_CMB (Q, U); uK_CMB^2 (covariances)",
        "fwhm_arcmin": FWHM_ARCMIN,
        "beam_arcmin": BEAM_ARCMIN,
        "resolution_arcmin": round(float(np.hypot(FWHM_ARCMIN, BEAM_ARCMIN)), 1),
        "center": [a.ra, a.dec],
        "size_deg": a.size,
        "pix_arcmin": a.pix,
        "n": n,
        "rows": "row 0 is the south edge; columns run east (left) to west (right), north up",
        "q": rnd(s["q"], scale), "u": rnd(s["u"], scale),
        "qq": rnd(s["qq"], scale**2), "uu": rnd(s["uu"], scale**2), "qu": rnd(s["qu"], scale**2),
    }
    OUT.write_text(json.dumps(data, separators=(",", ":")))
    P = np.hypot(s["q"], s["u"])
    snr = P / np.sqrt(0.5 * (s["qq"] + s["uu"]))
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e3:.0f} kB), n={n}, P/sigma percentiles 5/50/95:",
          np.percentile(snr, [5, 50, 95]).round(2))


if __name__ == "__main__":
    main()
