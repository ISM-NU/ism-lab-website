"""PowerPoint templates for import into Canva (or use as they are).

Formats: 16:9 slides, a 4:5 seminar announcement post, an A4 announcement
flyer and an A0 portrait poster. Each is written in three font versions to
brand/out/ism-nu-<format>-<version>.pptx:

- brand: the site's fonts by name. For PowerPoint or Keynote on a computer
  with brand/assets/fonts installed.
- canva: fonts from Canva's own library (Oswald, Inter, JetBrains Mono). For
  Canva Free accounts and for text in Russian, which Archivo and Doto lack.
- stage: the import file for the Canva Brand version. Canva's PowerPoint
  import ignores fonts uploaded to a Brand Kit, so each role gets a stand-in
  library font that is then swapped in Canva with "Change all":
  Oswald -> Archivo Condensed ExtraBold, Inter -> Archivo,
  IBM Plex Mono -> Doto Black. JetBrains Mono stays.

Canva ignores PowerPoint's all-caps attribute and paragraph spacing, so caps
are written as capitals and spacing is done with line height and separate
boxes.

    python3 brand/build_templates.py [format ...]   # needs python-pptx, Pillow
"""
import sys

from PIL import Image, ImageDraw
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

from brandlib import ASSETS, OUT, ROOT, hex_rgb, tokens

T = tokens()
VOID, PAPER, INK, GREY = T["void"], T["paper"], T["ink"], T["grey"]
ONP, ONPD, SIG, SIGP = T["on-paper"], T["on-paper-dim"], T["signal"], T["signal-on-paper"]

# Family name as Canva lists it and whether to press Bold. head_k scales
# headline sizes: Oswald is wider than Archivo at 62 % width.
FONTS = {
    "brand": dict(head=("Archivo Condensed ExtraBold", False), body=("Archivo", False),
                  mono=("JetBrains Mono", False), mono_b=("JetBrains Mono", True),
                  num=("Doto Black", False), head_k=1.0, head_lh=0.86),
    "canva": dict(head=("Oswald", True), body=("Inter", False),
                  mono=("JetBrains Mono", False), mono_b=("JetBrains Mono", True),
                  num=("JetBrains Mono", True), head_k=0.86, head_lh=1.0),
    "stage": dict(head=("Oswald", False), body=("Inter", False),
                  mono=("JetBrains Mono", False), mono_b=("JetBrains Mono", True),
                  num=("IBM Plex Mono", False), head_k=1.0, head_lh=0.86),
}

# Public images and their credit lines (README, "Credits").
SKY = {
    "lmc_field": (ROOT / "public/sky/lmc-bfield.webp",
                  "Large Magellanic Cloud · Planck 353 GHz dust and magnetic field"),
    "gc": (ROOT / "public/sky/comp-galactic_centre-1920.webp",
           "Galactic centre · Spitzer, Herschel, Planck 353 GHz"),
    "mon": (ROOT / "public/sky/comp-monoceros_ob1-1920.webp",
            "Monoceros OB1 · SHASSA Hα, WISE, Herschel, Planck"),
    "tarantula": (ROOT / "public/webb/tarantula-2880.webp",
                  "30 Doradus · NASA, ESA, CSA, STScI, Webb NIRCam (CC BY 4.0)"),
}


def rgb(h):
    return RGBColor(*hex_rgb(h))


def plate(key, w, h, focus=(0.5, 0.5), shade="left"):
    """Crop a sky image to w x h pixels around focus and bake in the darkening
    the text needs, so nothing depends on transparency surviving the import.
    shade: "left" (text on the left), "bottom" (text below), or None."""
    src, credit = SKY[key]
    im = Image.open(src).convert("RGB")
    scale = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    x0 = int(min(max(focus[0] * im.width - w / 2, 0), im.width - w))
    y0 = int(min(max(focus[1] * im.height - h / 2, 0), im.height - h))
    im = im.crop((x0, y0, x0 + w, y0 + h))
    if shade:
        mask = Image.new("L", (w, h))
        d = ImageDraw.Draw(mask)
        n = w if shade == "left" else h
        for i in range(n):
            t = i / n
            a = 0.88 - 0.78 * min(t / 0.75, 1) if shade == "left" else max(0.0, (t - 0.35) / 0.65) ** 1.4
            box = [(i, 0), (i, h)] if shade == "left" else [(0, i), (w, i)]
            d.line(box, fill=int(255 * a))
        im = Image.composite(Image.new("RGB", (w, h)), im, mask)
    out = OUT / "img" / f"{key}-{w}x{h}-{shade}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, quality=86, optimize=True, progressive=True)
    return out, credit


class Doc:
    """One PowerPoint file. Coordinates are in layout units; emu is the size
    of one unit (9525 = one pixel at 96 dpi)."""

    def __init__(self, fonts, w, h, emu=9525):
        self.f, self.W, self.H, self.emu = fonts, w, h, emu
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = self.u(w), self.u(h)
        self.blank = self.prs.slide_layouts[6]

    def u(self, v):
        return Emu(int(round(v * self.emu)))

    def pt(self, v):
        return Pt(v * self.emu / 12700)

    def page(self, bg, name, notes=""):
        s = self.prs.slides.add_slide(self.blank)
        s.background.fill.solid()
        s.background.fill.fore_color.rgb = rgb(bg)
        s.notes_slide.notes_text_frame.text = name + ("\n\n" + notes if notes else "")
        return s

    def rect(self, s, x, y, w, h, fill=None, line=None, dash=False, weight=2):
        r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, self.u(x), self.u(y), self.u(w), self.u(h))
        r.shadow.inherit = False
        if fill:
            r.fill.solid()
            r.fill.fore_color.rgb = rgb(fill)
        else:
            r.fill.background()
        if line:
            r.line.color.rgb = rgb(line)
            r.line.width = self.u(weight)
            if dash:
                r.line.dash_style = MSO_LINE_DASH_STYLE.DASH
        else:
            r.line.fill.background()
        return r

    def text(self, s, x, y, w, h, content, role="body", size=28, color=INK, caps=False,
             track=0.0, lh=None, align="l", anchor="t", bullets=False):
        """content: a string (paragraphs split on newlines) or a list of
        paragraphs, each a string or a list of (text, role, colour) runs."""
        tb = s.shapes.add_textbox(self.u(x), self.u(y), self.u(w), self.u(h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.auto_size = None
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
        paras = content.split("\n") if isinstance(content, str) else content
        k = self.f["head_k"] if role == "head" else 1.0
        for i, para in enumerate(paras):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
            if lh or role == "head":
                p.line_spacing = lh or self.f["head_lh"]
            if bullets:
                pPr = p._p.get_or_add_pPr()
                pPr.set("marL", str(self.u(size * 0.9)))
                pPr.set("indent", str(-self.u(size * 0.9)))
                buClr = pPr.makeelement(qn("a:buClr"), {})
                buClr.append(buClr.makeelement(qn("a:srgbClr"), {"val": (SIGP if color == ONP else SIG).lstrip("#")}))
                pPr.append(buClr)
                pPr.append(pPr.makeelement(qn("a:buFont"), {"typeface": "Arial"}))
                pPr.append(pPr.makeelement(qn("a:buChar"), {"char": "■"}))
            for txt, r_role, r_color in ([(para, role, color)] if isinstance(para, str) else para):
                r = p.add_run()
                r.text = txt.upper() if caps else txt
                fam, bold = self.f[r_role]
                r.font.name, r.font.bold = fam, bold
                r.font.size = self.pt(size * k)
                r.font.color.rgb = rgb(r_color or color)
                rPr = r._r.get_or_add_rPr()
                if track:
                    rPr.set("spc", str(int(track * size * self.emu / 12700 * 100)))
                for tag in ("a:ea", "a:cs"):  # same face for Cyrillic and symbols
                    el = rPr.find(qn(tag))
                    if el is None:
                        el = rPr.makeelement(qn(tag), {})
                        rPr.append(el)
                    el.set("typeface", fam)
        return tb

    def label(self, s, x, y, w, txt, color=GREY, align="l", size=20):
        return self.text(s, x, y, w, size * 1.5, txt, role="mono_b", size=size, color=color,
                         caps=True, track=0.12, align=align)

    def logo(self, s, x, y, h, variant="on-dark", kind="wordmark"):
        return s.shapes.add_picture(str(ASSETS / "logo" / f"ism-nu-{kind}-{variant}.png"),
                                    self.u(x), self.u(y), height=self.u(h))

    def picture(self, s, path, x, y, w, h):
        return s.shapes.add_picture(str(path), self.u(x), self.u(y), self.u(w), self.u(h))

    def corners(self, s, color=SIG, inset=40, arm=28, t=3, box=None):
        x0, y0, x1, y1 = box or (inset, inset, self.W - inset, self.H - inset)
        g = s.shapes.add_group_shape()
        for cx, cy, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            for (x, y, w, h) in ((cx if sx > 0 else cx - arm, cy if sy > 0 else cy - t, arm, t),
                                 (cx if sx > 0 else cx - t, cy if sy > 0 else cy - arm, t, arm)):
                r = g.shapes.add_shape(MSO_SHAPE.RECTANGLE, self.u(x), self.u(y), self.u(w), self.u(h))
                r.fill.solid()
                r.fill.fore_color.rgb = rgb(color)
                r.line.fill.background()
                r.shadow.inherit = False
        g.name = "Frame corners"
        return g

    def figure_box(self, s, x, y, w, h, hint="Figure", dark=False, size=20):
        c = GREY if dark else ONPD
        self.rect(s, x, y, w, h, line=c, dash=True, weight=max(2, size / 10))
        self.label(s, x, y + h / 2 - size * 0.7, w, hint, color=c, align="c", size=size)

    def table(self, s, x, y, w, rows, row_h=80, size=28, head=20):
        tbl = s.shapes.add_table(len(rows), len(rows[0]), self.u(x), self.u(y), self.u(w),
                                 self.u(row_h * len(rows))).table
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                cell = tbl.cell(r, c)
                cell.fill.solid()
                cell.fill.fore_color.rgb = rgb(ONP if r == 0 else PAPER)
                cell.margin_left = self.u(16)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                tf = cell.text_frame
                tf.text = val.upper() if r == 0 else val
                run = tf.paragraphs[0].runs[0]
                # Data reads in mono, as on the site. Body fonts in table
                # cells do not survive Canva's import anyway.
                fam, bold = self.f["mono_b" if r == 0 else "mono"]
                run.font.name, run.font.bold = fam, bold
                run.font.size = self.pt(head if r == 0 else size)
                run.font.color.rgb = rgb(INK if r == 0 else ONP)
                if r == 0:
                    run._r.get_or_add_rPr().set("spc", str(int(0.12 * head * self.emu / 12700 * 100)))

    def save(self, name):
        out = OUT / name
        self.prs.save(out)
        return out


# ---------- 16:9 slides ----------

def slides(v):
    d = Doc(FONTS[v], 1920, 1080)
    W, H, M = d.W, d.H, 96

    def head(s, title, kicker, n):
        d.text(s, M, 72, 1400, 90, title, role="head", size=72, color=ONP, caps=True, anchor="b")
        d.label(s, W - M - 400, 126, 400, kicker, color=ONPD, align="r")
        d.rect(s, M, 180, W - 2 * M, 2, fill=ONP)
        d.logo(s, M, 1004, 22, "on-light")
        d.label(s, 420, 1002, 1080, "Source · Author et al. 2025", color=ONPD, align="c")
        d.label(s, W - M - 200, 1002, 200, f"{n:02d}", color=ONPD, align="r")

    s = d.page(VOID, "Title, sky", "Swap the background for any public map; keep the left third dark for the text and update the credit line.")
    img, credit = plate("lmc_field", W, H)
    d.picture(s, img, 0, 0, W, H)
    d.corners(s)
    d.logo(s, M, 88, 34)
    d.label(s, W - M - 700, 92, 700, "Event name · 21 November 2026", align="r")
    d.label(s, M, 500, 900, "Interstellar medium group", color=SIG)
    d.text(s, M, 548, 1150, 300, "Talk title in two or three lines at most", role="head", size=128, caps=True)
    d.text(s, M, 870, 1000, 40, "Speaker name · Nazarbayev University", size=30)
    d.label(s, M, 990, 1200, credit)

    s = d.page(VOID, "Title, plain", "For talks where no sky image fits.")
    d.logo(s, M, 88, 34)
    d.rect(s, M, 560, W - 2 * M, 2, fill=INK)
    d.text(s, M, 600, 1250, 330, "Talk title in two or three lines at most", role="head", size=128, caps=True)
    d.text(s, 1440, 600, 384, 200, [[("Speaker name", "body", INK)], [("Event name", "body", GREY)],
                                    [("21 November 2026", "body", GREY)]], size=28, lh=1.4)
    d.label(s, M, 990, 1200, "Interstellar medium group · Nazarbayev University · Astana")

    for key, num, focus in (("gc", "01", (0.5, 0.45)), ("mon", "02", (0.55, 0.45))):
        s = d.page(VOID, f"Section divider {num}", "One divider per part of the talk. The number is the section, not the slide.")
        img, credit = plate(key, W, H, focus=focus)
        d.picture(s, img, 0, 0, W, H)
        d.corners(s)
        d.text(s, M, 300, 700, 220, num, role="num", size=200, color=SIG, lh=1.0)
        d.text(s, M, 560, 1100, 260, "Section title", role="head", size=112, caps=True)
        d.label(s, M, 990, 1400, credit)

    s = d.page(PAPER, "Outline")
    head(s, "Outline", "Talk · overview", 4)
    for i, it in enumerate(["Why the field matters", "Data and method", "Results", "What comes next"]):
        y = 250 + i * 170
        d.text(s, M, y, 160, 120, f"{i + 1:02d}", role="num", size=96, color=SIGP, lh=1.0)
        d.text(s, M + 200, y + 18, 1300, 90, it, role="head", size=64, color=ONP, caps=True)
        d.rect(s, M + 200, y + 140, W - 2 * M - 200, 2, fill=ONPD)

    s = d.page(PAPER, "Text and bullets", "Keep to three or four points. Put the detail in what you say.")
    head(s, "Slide title", "Section · 01", 5)
    d.text(s, M, 250, 1000, 600, ["First point, one line if possible", "Second point with a number, n ≈ 10³ cm⁻³",
                                  "Third point that ends the argument"], size=40, color=ONP, bullets=True, lh=1.6)
    d.text(s, 1240, 250, 584, 600, "A short paragraph for context can sit on the right. Set it in the body face at 28 px or more so it stays readable from the back of a lecture room.",
           size=28, color=ONPD, lh=1.45)

    s = d.page(PAPER, "Figure and text", "Paste the plot on the left. White-background matplotlib figures sit on this paper without a box.")
    head(s, "Figure with a message", "Result · 02", 6)
    d.figure_box(s, M, 230, 1060, 720, "Figure · plot or map")
    d.label(s, 1220, 236, 600, "What it shows", color=SIGP)
    d.text(s, 1220, 280, 604, 200, "The claim in one sentence, in words a student follows.", size=32, color=ONP, lh=1.35)
    d.text(s, 1220, 480, 604, 200, "The number that backs it, with its uncertainty.", size=32, color=ONPD, lh=1.35)

    s = d.page(PAPER, "Large figure")
    head(s, "One large figure", "Result · 03", 7)
    d.figure_box(s, M, 220, W - 2 * M, 690, "Figure · full width")
    d.text(s, M, 930, W - 2 * M, 50, "Caption: what the axes are, what the colour means, and the beam or resolution.", size=24, color=ONPD)

    s = d.page(PAPER, "Two figures")
    head(s, "Two figures compared", "Result · 04", 8)
    for i, cap in enumerate(("(a) Before foreground removal", "(b) After foreground removal")):
        x = M + i * 880
        d.figure_box(s, x, 230, 848, 640, "Figure")
        d.text(s, x, 890, 848, 50, cap, size=26, color=ONP)

    s = d.page(PAPER, "Key number", "One result, one number.")
    head(s, "Key result", "Result · 05", 9)
    d.text(s, M, 280, 1000, 300, "3.6%", role="num", size=240, color=SIGP, lh=1.0)
    d.label(s, M, 560, 900, "Median polarization fraction, LMC", color=ONPD)
    d.text(s, M, 620, 1000, 260, "After the Milky Way foreground is removed, the median is slightly lower than in the diffuse Milky Way.",
           size=36, color=ONP, lh=1.35)
    d.figure_box(s, 1220, 280, 604, 600, "Supporting figure")

    s = d.page(VOID, "Full-bleed image", "For outreach and openers. Always keep the credit line.")
    img, credit = plate("tarantula", W, H, shade=None)
    d.picture(s, img, 0, 0, W, H)
    d.corners(s)
    d.label(s, M, 88, 1000, "Image title or one-line message", color=INK)
    d.label(s, W - M - 1100, 990, 1100, credit, color=INK, align="r")

    s = d.page(PAPER, "Table")
    head(s, "Table of values", "Data · 06", 11)
    d.table(s, M, 240, W - 2 * M, [("Region", "Distance", "p, median", "Tracer"), ("LMC", "50 kpc", "3.6 %", "Planck 353 GHz"),
                                    ("Galactic centre", "8.2 kpc", "–", "PILOT 240 µm"), ("Mon OB1", "0.8 kpc", "–", "Planck, Herschel")])

    s = d.page(PAPER, "People", "Photos are square. Crop faces at the same height.")
    head(s, "Who did the work", "Team", 12)
    for i in range(4):
        x = M + i * 440
        d.figure_box(s, x, 230, 400, 400, "Photo")
        d.label(s, x, 650, 400, "Role", color=SIGP)
        d.text(s, x, 686, 400, 60, "Full name", role="head", size=44, color=ONP, caps=True)
        d.text(s, x, 750, 400, 120, "Topic in a few words", size=24, color=ONPD, lh=1.35)

    s = d.page(PAPER, "References")
    head(s, "References", "End", 13)
    d.text(s, M, 240, 1400, 600, ["Alina D. et al. 2023, MNRAS 518, 4466", "Alina D. et al. 2019, MNRAS 485, 2825",
                                  "Mangilli A. et al. 2019, A&A 630, A74", "Planck Collaboration Int. XIX 2015, A&A 576, A104"],
           role="mono", size=26, color=ONP, lh=1.8)

    s = d.page(VOID, "Closing")
    d.corners(s)
    d.logo(s, M, 300, 200, kind="stacked")
    d.text(s, 860, 300, 964, 160, "Questions", role="head", size=144, caps=True)
    d.text(s, 860, 500, 964, 200, [[("name.surname@nu.edu.kz", "mono", INK)], [("github.com/ISM-NU", "mono", GREY)]], size=30, lh=1.6)
    d.label(s, M, 990, 1400, "Interstellar medium group · Nazarbayev University · Astana")
    return d.save(f"ism-nu-slides-{v}.pptx")


# ---------- announcements ----------

def announcement(v, fmt):
    """Seminar announcement. post: 1080 x 1350 px (4:5 feed post).
    a4: 210 x 297 mm, laid out on a 1240 x 1754 grid (150 dpi)."""
    if fmt == "post":
        d, name = Doc(FONTS[v], 1080, 1350), "post"
    else:
        d, name = Doc(FONTS[v], 1240, 1754, emu=210 * 36000 / 1240), "a4"
    W, H = d.W, d.H
    k = W / 1080
    M = round(72 * k)
    s = d.page(VOID, "Seminar announcement", "Replace the image with any public map and keep its credit line. QR code goes in the dashed box.")
    ih = round(H * 0.5)
    img, credit = plate("gc", W, ih, focus=(0.5, 0.5), shade="bottom")
    d.picture(s, img, 0, 0, W, ih)
    d.corners(s, inset=round(32 * k), arm=round(24 * k), t=max(3, round(3 * k)))
    d.logo(s, M, M, 30 * k)
    d.label(s, W - M - 500 * k, M + 4 * k, 500 * k, "Seminar · No. 12", align="r", size=18 * k, color=INK)
    y = round(H * 0.43)
    d.label(s, M, y, W - 2 * M, "Interstellar medium group seminar", color=SIG, size=20 * k)
    d.text(s, M, y + 48 * k, W - 2 * M, 300 * k, "Seminar title on two or three lines", role="head",
           size=104 * k, caps=True)
    d.text(s, M, y + 360 * k, W - 2 * M, 50 * k, "Speaker name, affiliation", size=34 * k)
    by = H - M - 250 * k
    d.rect(s, M, by, W - 2 * M, max(2, 2 * k), fill=INK)
    span = W - 2 * M - 220 * k
    x = M
    for lab, val, share in (("Date", "Thu 27 Nov", 0.42), ("Time", "16:00", 0.22), ("Place", "Room 7.105", 0.36)):
        d.label(s, x, by + 28 * k, span * share, lab, size=18 * k)
        d.text(s, x, by + 64 * k, span * share - 16 * k, 60 * k, val, role="mono_b", size=32 * k)
        x += span * share
    d.figure_box(s, W - M - 180 * k, by + 28 * k, 180 * k, 180 * k, "QR", dark=True, size=18 * k)
    d.label(s, M, by + 150 * k, W - 2 * M - 220 * k, "Open to all · in English", size=18 * k, color=INK)
    d.label(s, M, H - M + 10 * k, W - 2 * M, credit, size=14 * k)
    return d.save(f"ism-nu-announcement-{name}-{v}.pptx")


# ---------- A0 poster ----------

def poster(v):
    """A0 portrait, 841 x 1189 mm, on a grid of 4 units per mm."""
    d = Doc(FONTS[v], 3364, 4756, emu=9000)
    W, H, M = d.W, d.H, 160
    s = d.page(PAPER, "A0 poster", "Three columns. Replace dashed boxes with figures; keep text at 32 pt or larger.")
    hh = 1100
    d.rect(s, 0, 0, W, hh, fill=VOID)
    img, credit = plate("lmc_field", W, hh, focus=(0.5, 0.5))
    d.picture(s, img, 0, 0, W, hh)
    d.corners(s, inset=64, arm=72, t=8, box=(64, 64, W - 64, hh - 64))
    d.logo(s, M, M, 72)
    d.label(s, W - M - 1600, M + 10, 1600, "Conference name · City · 2026", align="r", size=40, color=INK)
    d.label(s, M, 400, 2400, "Interstellar medium group · Nazarbayev University", color=SIG, size=44)
    d.text(s, M, 470, 2700, 380, "Poster title in two lines, the finding not the topic", role="head",
           size=180, caps=True)
    d.text(s, M, 880, 2700, 80, [[("First Author", "body", INK), (", Second Author, Third Author", "body", GREY)]], size=56)
    d.label(s, M, hh - 120, 2400, credit, size=28)

    gut, top = 96, hh + 140
    cw = (W - 2 * M - 2 * gut) / 3
    cols = [M + i * (cw + gut) for i in range(3)]

    def section(x, y, num, title, body, fig_h=0, fig="Figure"):
        d.text(s, x, y, 200, 120, num, role="num", size=110, color=SIGP, lh=1.0)
        d.text(s, x + 220, y + 10, cw - 220, 110, title, role="head", size=96, color=ONP, caps=True)
        d.rect(s, x, y + 140, cw, 4, fill=ONP)
        d.text(s, x, y + 180, cw, 420, body, size=44, color=ONP, lh=1.4)
        if fig_h:
            d.figure_box(s, x, y + 620, cw, fig_h, fig, size=36)
            d.text(s, x, y + 640 + fig_h, cw, 120, "Caption: axes, colour scale, beam.", size=34, color=ONPD, lh=1.35)

    section(cols[0], top, "01", "Motivation", "Two or three sentences on why the question matters and what was not known.", 900)
    section(cols[0], top + 1740, "02", "Data and method", "Which surveys, which resolution, and the one step that makes the method work.", 520)
    section(cols[1], top, "03", "Results", "State the result first, then the evidence for it.", 1400, "Main figure")
    d.label(s, cols[1], top + 2300, cw, "Key number", color=ONPD, size=40)
    d.text(s, cols[1], top + 2360, cw, 300, "3.6%", role="num", size=260, color=SIGP, lh=1.0)
    d.text(s, cols[1], top + 2680, cw, 300, "What the number is, with its uncertainty.", size=44, color=ONP, lh=1.4)
    section(cols[2], top, "04", "Conclusions", ["First conclusion in one line.", "Second conclusion in one line.",
                                                "What comes next."], 1000)
    d.table(s, cols[2], top + 1900, cw, [("Region", "Distance", "p"), ("LMC", "50 kpc", "3.6 %"),
                                         ("Mon OB1", "0.8 kpc", "–")], row_h=130, size=40, head=32)

    fy = H - 560
    d.rect(s, 0, fy, W, H - fy, fill=VOID)
    d.label(s, M, fy + 90, 1200, "References", size=32)
    d.text(s, M, fy + 150, 1900, 300, ["Alina D. et al. 2023, MNRAS 518, 4466", "Alina D. et al. 2019, MNRAS 485, 2825"],
           role="mono", size=34, color=INK, lh=1.6)
    d.label(s, 2150, fy + 90, 700, "Contact", size=32)
    d.text(s, 2150, fy + 150, 760, 200, [[("name.surname@nu.edu.kz", "mono", INK)], [("github.com/ISM-NU", "mono", GREY)]], size=34, lh=1.6)
    d.figure_box(s, W - M - 300, fy + 90, 300, 300, "QR", dark=True, size=32)
    return d.save(f"ism-nu-poster-a0-{v}.pptx")


BUILDERS = {"slides": slides, "post": lambda v: announcement(v, "post"),
            "a4": lambda v: announcement(v, "a4"), "poster": poster}

if __name__ == "__main__":
    for fmt in sys.argv[1:] or BUILDERS:
        for v in FONTS:
            p = BUILDERS[fmt](v)
            print(p.name, p.stat().st_size)
