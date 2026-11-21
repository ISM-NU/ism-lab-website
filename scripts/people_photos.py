#!/usr/bin/env python3
"""Member photos: crop, colour-manage and grade every portrait the same way.

Sources live in assets/people-src/<id>.<ext> (not tracked; originals as sent).
Writes public/people/<id>.webp, 640 px square.

    python3 scripts/people_photos.py              # all photos
    python3 scripts/people_photos.py adel-umirbayeva --strength 1.2

Each photo is converted to sRGB from its embedded profile first: phone photos
are often Display P3, and reading them as sRGB makes them look washed out.
Then one recipe:
  - exposure: a gamma that moves the face box toward FACE_TARGET luminance,
  - vibrance: saturation lifted more where it is low, half as much on skin,
  - a mild S-curve for contrast,
  - a check that reports how much of the frame is clipped to white.
A new member: add the source file and a CROPS entry (left, top, side in source
pixels, chosen with the face a little above centre), then rerun.
"""

import argparse
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets/people-src"
OUT = ROOT / "public/people"
SIZE = 640

# id: (left, top, side) in source pixels; None = centred square of the short side.
CROPS = {
    "dana-alina": (0, 120, 734),
    "adel-umirbayeva": (0, 40, 760),
    "dana-makarova": (0, 450, 500),
    "baurzhan-kumarioldanov": (230, 140, 820),
    "denis-andreyev": (470, 380, 2460),
    "abusultan-meirambekuly": (663, 130, 780),
    "eldana-rustem": None,
}
# Face box as fractions of the cropped square (x0, y0, x1, y1).
FACE = (0.32, 0.22, 0.68, 0.58)
FACE_TARGET = 0.56   # mean face luminance after grading
VIBRANCE = 0.55      # extra saturation for grey pixels; vivid ones get less
SKIN_GUARD = 0.5     # share of the vibrance kept on skin hues
CONTRAST = 0.12      # S-curve strength


def to_srgb(im):
    icc = im.info.get("icc_profile")
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
        im = Image.alpha_composite(bg, im)
    im = im.convert("RGB")
    if icc:
        src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        im = ImageCms.profileToProfile(im, src, ImageCms.createProfile("sRGB"), outputMode="RGB")
    return im


def grade(rgb, strength=1.0):
    a = np.asarray(rgb, float) / 255
    h, w, _ = a.shape
    lum = lambda x: x @ np.array([0.2126, 0.7152, 0.0722])
    x0, y0, x1, y1 = FACE
    box = lum(a[int(h * y0):int(h * y1), int(w * x0):int(w * x1)])
    # Face brightness from the lit part of the box only, so hair and sunglasses
    # do not count as a dark face.
    face = float(np.median(box[box > np.percentile(box, 40)]))
    # Exposure: gamma toward the target, never darker, never more than 0.6.
    g = np.clip(np.log(FACE_TARGET) / np.log(max(face, 1e-3)), 0.6, 1.0) if face < FACE_TARGET else 1.0
    black = np.percentile(lum(a), 0.5)
    a = a ** g
    # A gamma lift greys the blacks too (a dark jacket turns charcoal); pull the
    # 0.5th percentile back to where it was.
    b2 = black ** g
    if b2 > black:
        a = np.clip((a - (b2 - black)) / (1 - (b2 - black)), 0, 1)  # unclipped negatives wrap in uint8
    # Vibrance in HSV: s' = s * (1 + v * (1 - s) * k), k lowered on skin hues.
    hsv = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).convert("HSV"), float) / 255
    hue, s = hsv[..., 0] * 360, hsv[..., 1]
    skin = np.exp(-(((hue - 25 + 180) % 360 - 180) / 25) ** 2)
    k = 1 - (1 - SKIN_GUARD) * skin
    hsv[..., 1] = np.clip(s * (1 + VIBRANCE * strength * (1 - s) * k), 0, 1)
    a = np.asarray(Image.fromarray((hsv * 255).astype(np.uint8), "HSV").convert("RGB"), float) / 255
    # S-curve around mid-grey.
    c = CONTRAST * strength
    a = a + c * (a - 0.5) * (1 - np.abs(2 * a - 1))
    a = np.clip(a, 0, 1)
    clipped = (lum(a) > 0.985).mean()
    return Image.fromarray((a * 255 + 0.5).astype(np.uint8)), face, g, clipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--strength", type=float, default=1.0, help="scales vibrance and contrast")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    ids = args.ids or list(CROPS)
    args.out.mkdir(parents=True, exist_ok=True)
    for pid in ids:
        src = next(SRC.glob(f"{pid}.*"), None)
        if src is None:
            sys.exit(f"{pid}: no source in {SRC}")
        im = to_srgb(Image.open(src))
        box = CROPS[pid]
        if box is None:
            s = min(im.size)
            box = ((im.width - s) // 2, (im.height - s) // 2, s)
        l, t, s = box
        im = im.crop((l, t, l + s, t + s)).resize((SIZE, SIZE), Image.LANCZOS)
        out, face, g, clipped = grade(im, args.strength)
        out.save(args.out / f"{pid}.webp", "WEBP", quality=84)
        flag = "  CLIPPED" if clipped > 0.08 else ""
        print(f"{pid:26s} face {face:.2f} gamma {g:.2f} white {clipped:5.1%}{flag}")


if __name__ == "__main__":
    main()
