"""GitHub organisation avatar for ISM-NU (1024 x 1024 PNG).

The background is the site's LMC map (Planck 353 GHz dust with the field
orientation as texture, public/sky/lmc-bfield.webp), dimmed so the dot-matrix
wordmark in the site's display font (Doto) stays legible at 20 px.

    python3 brand/make_avatar.py   # needs Pillow and fonttools with brotli
"""
from pathlib import Path
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
S, INK, SIGNAL = 1024, (243, 243, 239), (255, 61, 36)  # --ink and --signal

font_path = Path("/tmp/doto-900.ttf")
f = TTFont(ROOT / "node_modules/@fontsource/doto/files/doto-latin-900-normal.woff2")
f.flavor = None
f.save(font_path)

bg = Image.open(ROOT / "public/sky/lmc-bfield.webp").convert("RGB")
w, h = bg.size
c = int(min(w, h) * 0.62)
bg = bg.crop(((w - c) // 2, (h - c) // 2, (w + c) // 2, (h + c) // 2)).resize((S, S), Image.LANCZOS)
bg = Image.eval(bg, lambda x: int(x * 0.5))

d = ImageDraw.Draw(bg)
font = ImageFont.truetype(str(font_path), 350)
lines = [("ISM", INK), ("/NU", SIGNAL)]
boxes = [d.textbbox((0, 0), t, font=font) for t, _ in lines]
gap = 40
y = (S - sum(b[3] - b[1] for b in boxes) - gap) / 2
for (t, col), b in zip(lines, boxes):
    d.text(((S - (b[2] - b[0])) / 2 - b[0], y - b[1]), t, font=font, fill=col)
    y += (b[3] - b[1]) + gap
bg.save(Path(__file__).with_name("ism-nu-github-avatar.png"))
