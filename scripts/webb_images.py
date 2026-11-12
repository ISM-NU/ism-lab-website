"""Download the Webb images the site shows and find bright sources in them.

The images are ESA/Webb releases under CC BY 4.0 (credit: NASA, ESA, CSA,
STScI). The source finder is a difference-of-Gaussians blob search; its boxes
are what the site draws as "detections", so every box marks a real source.

Writes public/webb/<name>-{960,1920}.webp and src/data/detections.json.
Downloads are cached in .cache/webb/ (ignored by git).

Run: python3 scripts/webb_images.py
"""

import json
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from skimage.feature import blob_dog

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "webb"
OUT = ROOT / "public" / "webb"
DATA = ROOT / "src" / "data" / "detections.json"

# ESA/Webb release id -> site name
IMAGES = {
    "weic2212a": "tarantula",
    "weic2205a": "cliffs",
    "weic2216a": "pillars",
    "weic2209a": "deepfield",
    "weic2316a": "rhooph",
    "weic2301a": "ngc346",
}
# R136 sits off the brightest smoothed peak in the Tarantula frame, so its
# position is set by hand from the release's annotated image.
CORE_OVERRIDE = {"tarantula": [0.5967, 0.5508]}
WIDTHS = (960, 1920)
N_SOURCES = 70


def fetch(release):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{release}.jpg"
    if path.exists():
        return path
    for size in ("wallpaper5", "wallpaper4", "large"):
        url = f"https://cdn.esawebb.org/archives/images/{size}/{release}.jpg"
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                path.write_bytes(r.read())
            return path
        except OSError:
            continue
    raise RuntimeError(f"could not download {release}")


def detect(img):
    small = img.copy()
    small.thumbnail((1024, 1024))
    g = np.asarray(small.convert("L"), float) / 255
    h, w = g.shape
    scored = []
    for y, x, s in blob_dog(g, min_sigma=1.5, max_sigma=14, threshold=0.06):
        r = max(3, s * 1.8)
        patch = g[int(max(0, y - r)) : int(min(h, y + r + 1)), int(max(0, x - r)) : int(min(w, x + r + 1))]
        scored.append((float(patch.mean() * s**0.5), x / w, y / h, s * 2.4 / w))
    scored.sort(reverse=True)
    sm = gaussian_filter(g, 18)
    cy, cx = np.unravel_index(sm.argmax(), sm.shape)
    return {
        "aspect": round(w / h, 4),
        "src": [[round(a, 4), round(b, 4), round(c, 4), round(v, 3)] for v, a, b, c in scored[:N_SOURCES]],
        "core": [round(cx / w, 4), round(cy / h, 4)],
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    DATA.parent.mkdir(parents=True, exist_ok=True)
    det = {}
    for release, name in IMAGES.items():
        img = Image.open(fetch(release)).convert("RGB")
        for width in WIDTHS:
            im = img.copy()
            im.thumbnail((width, width))
            im.save(OUT / f"{name}-{width}.webp", quality=80, method=6)
        det[name] = detect(img)
        det[name]["release"] = release
        if name in CORE_OVERRIDE:
            det[name]["core"] = CORE_OVERRIDE[name]
        print(name, img.size, flush=True)
    DATA.write_text(json.dumps(det, separators=(",", ":")))


if __name__ == "__main__":
    main()
