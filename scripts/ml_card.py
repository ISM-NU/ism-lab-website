#!/usr/bin/env python3
"""Card image for the machine learning line: the Herschel 250 um cutout of
G202.3+2.5 with the pixels the U-Net classes as filament drawn in signal red.

Reads the committed outputs of scripts/unet_filaments.py (no network weights needed):
  public/sky/unet-herschel.webp, public/sky/unet-data.png (R > 0: filament)
Writes public/sky/ml-card-960.webp.
"""

from pathlib import Path

import numpy as np
from PIL import Image

SKY = Path(__file__).resolve().parent.parent / "public/sky"
SIGNAL = np.array([255, 61, 36], float)  # --signal in global.css

base = Image.open(SKY / "unet-herschel.webp").convert("L").resize((960, 960), Image.LANCZOS)
cls = np.asarray(Image.open(SKY / "unet-data.png").convert("RGB"))[..., 0] > 0
mask = np.asarray(Image.fromarray((cls * 255).astype(np.uint8)).resize((960, 960), Image.NEAREST)) > 0
g = np.asarray(base, float)[..., None] * np.array([0.78, 0.78, 0.76]) / 255
out = np.where(mask[..., None], 0.25 * g + 0.75 * SIGNAL / 255, g * 0.9)
Image.fromarray((out.clip(0, 1) * 255).astype(np.uint8)).crop((0, 120, 960, 840)).save(SKY / "ml-card-960.webp", quality=82)
print(SKY / "ml-card-960.webp", mask.mean())
