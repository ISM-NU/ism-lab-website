"""Brand guide for the ISM group: brand/out/ism-nu-brand-guide.pdf.

The colours are read from src/styles/global.css and the type is set in the
files from brand/assets/fonts, so the guide shows what the site uses.
Template previews are read from brand/out/previews/ (see brand/README.md).

    python3 brand/build_book.py   # needs google-chrome for the PDF
"""
import html
import subprocess
from pathlib import Path

from brandlib import ASSETS, BRAND, NM, OUT, contrast, hex_rgb, tokens

T = tokens()
PREV = OUT / "previews"
LOGO = ASSETS / "logo"
FONTS = ASSETS / "fonts"
MONO = NM / "@fontsource-variable/jetbrains-mono/files/jetbrains-mono-latin-wght-normal.woff2"
MONO_CYR = NM / "@fontsource-variable/jetbrains-mono/files/jetbrains-mono-cyrillic-wght-normal.woff2"

COLOURS = [  # token, name, role
    ("void", "Void", "Background of dark pages, slides and the site."),
    ("paper", "Paper", "Reading surfaces: content slides, posters, print."),
    ("signal", "Signal", "One accent on dark grounds: the /NU, live readouts, selection, the key number."),
    ("signal-on-paper", "Signal on paper", "The same accent on paper. Darker, so small text stays readable."),
    ("grey", "Grey", "Labels and secondary text on dark grounds."),
    ("on-paper", "Ink on paper", "Text on paper."),
    ("on-paper-dim", "Dim on paper", "Labels and secondary text on paper."),
]


def svg(name):
    return (LOGO / f"{name}.svg").read_text()


def esc(s):
    return html.escape(s, quote=False)


def page(cls, inner, n=None, title=None, dark=False):
    head = ""
    if title:
        head = f'<header><span class="lab">{esc(title)}</span><span class="lab">{n:02d}</span></header>'
    return f'<section class="pg {cls}{" dark" if dark else ""}">{head}{inner}</section>'


def build():
    css = f"""
@font-face {{ font-family: Cond; src: url({FONTS / 'ArchivoCondensedExtraBold-Regular.ttf'}); }}
@font-face {{ font-family: Body; src: url({FONTS / 'Archivo-Regular.ttf'}); }}
@font-face {{ font-family: Body; font-weight: 700; src: url({FONTS / 'Archivo-Bold.ttf'}); }}
@font-face {{ font-family: Dot; src: url({FONTS / 'DotoBlack-Regular.ttf'}); }}
@font-face {{ font-family: Mono; font-weight: 100 800; src: url({MONO}); }}
@font-face {{ font-family: Mono; font-weight: 100 800; src: url({MONO_CYR}); unicode-range: U+0400-04FF; }}
@page {{ size: 1600px 900px; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font: 400 19px/1.5 Body, sans-serif; color: {T['on-paper']}; }}
.pg {{ width: 1600px; height: 900px; position: relative; overflow: hidden; background: {T['paper']};
      padding: 120px 96px 72px; page-break-after: always; }}
.pg.dark {{ background: {T['void']}; color: {T['ink']}; }}
header {{ position: absolute; left: 96px; right: 96px; top: 48px; display: flex; justify-content: space-between;
         border-bottom: 2px solid currentColor; padding-bottom: 12px; }}
.lab {{ font: 700 13px/1.3 Mono, monospace; letter-spacing: .12em; text-transform: uppercase; color: {T['on-paper-dim']}; }}
.dark .lab {{ color: {T['grey']}; }}
.lab.red {{ color: {T['signal-on-paper']}; }} .dark .lab.red {{ color: {T['signal']}; }}
h1 {{ font: 400 120px/.86 Cond; text-transform: uppercase; margin: 0; letter-spacing: -.01em; }}
h2 {{ font: 400 64px/.9 Cond; text-transform: uppercase; margin: 0 0 28px; letter-spacing: -.01em; }}
h3 {{ font: 400 28px/1 Cond; text-transform: uppercase; margin: 0 0 10px; }}
p {{ margin: 0 0 14px; max-width: 62ch; }}
.dim {{ color: {T['on-paper-dim']}; }} .dark .dim {{ color: {T['grey']}; }}
.grid {{ display: grid; gap: 24px; }}
.cols2 {{ grid-template-columns: 1fr 1fr; }} .cols3 {{ grid-template-columns: repeat(3, 1fr); }}
.cols4 {{ grid-template-columns: repeat(4, 1fr); }}
.cell {{ border: 2px solid rgba(10,10,11,.15); padding: 24px; }}
.dark .cell {{ border-color: rgba(243,243,239,.16); }}
.tile {{ height: 210px; display: grid; place-items: center; padding: 28px; }}
.tile svg {{ max-width: 100%; max-height: 100%; height: auto; }}
.fit svg {{ width: auto; height: 100%; display: block; }}
.corner {{ position: absolute; width: 28px; height: 28px; border: 0 solid {T['signal']}; }}
.c1 {{ top: 32px; left: 32px; border-width: 3px 0 0 3px; }} .c2 {{ top: 32px; right: 32px; border-width: 3px 3px 0 0; }}
.c3 {{ bottom: 32px; left: 32px; border-width: 0 0 3px 3px; }} .c4 {{ bottom: 32px; right: 32px; border-width: 0 3px 3px 0; }}
.mono {{ font-family: Mono, monospace; }}
.thumbs img {{ width: 100%; display: block; border: 1px solid rgba(10,10,11,.15); }}
table {{ border-collapse: collapse; width: 100%; font-size: 17px; }}
td, th {{ text-align: left; padding: 10px 12px 10px 0; border-bottom: 1px solid rgba(10,10,11,.2); vertical-align: top; }}
th {{ font: 700 13px Mono; letter-spacing: .12em; text-transform: uppercase; color: {T['on-paper-dim']}; }}
ul {{ margin: 0; padding-left: 22px; }} li {{ margin-bottom: 8px; }}
li::marker {{ color: {T['signal-on-paper']}; content: "■  "; font-size: 12px; }}
"""
    pages = []

    # 1 Cover
    bg = (BRAND.parent / "public/sky/lmc-bfield.webp").as_uri()
    pages.append(f"""<section class="pg dark" style="background: #000 url({bg}) right center / 900px no-repeat;">
<div style="position:absolute;inset:0;background:linear-gradient(90deg,#000 35%,rgba(0,0,0,.2))"></div>
<span class="corner c1"></span><span class="corner c2"></span><span class="corner c3"></span><span class="corner c4"></span>
<div style="position:relative;width:760px;margin-top:150px">
<div class="fit" style="height:150px">{svg('ism-nu-stacked-on-dark')}</div>
<p class="lab red" style="margin-top:72px">Interstellar medium group · Nazarbayev University</p>
<h1 style="margin-top:12px">Brand guide</h1>
<p class="dim" style="margin-top:24px">Logo, colour, type, images and templates for slides, announcements and posters. Version 1, November 2026.</p>
</div>
<p class="lab" style="position:absolute;left:96px;bottom:72px">Large Magellanic Cloud · Planck 353 GHz dust and magnetic field</p>
</section>""")

    # 2 Idea
    pages.append(page("", f"""<div class="grid cols2" style="gap:72px;margin-top:40px">
<div><h2>The idea</h2>
<p>The group's look comes from the website: an observatory console. A black field, thin frames, mono labels like instrument readouts, and paper surfaces for anything people read for longer than a few seconds.</p>
<p>Colour comes from the data. Maps and images bring their own colour, so the interface stays black, white and grey with a single red accent.</p>
<p>Red means "this one". It marks the /NU in the logo, a live readout, a selected item or the number a slide is about. If a page has red in three places, two of them are wrong.</p></div>
<div><h2>In short</h2>
<ul><li>Dark grounds for titles, dividers and images. Paper for text, plots and tables.</li>
<li>Headlines in condensed capitals. Body text in a plain sans. Labels, data and dates in mono capitals with wide spacing.</li>
<li>Use the group's own maps where an image is needed, and always print the credit line.</li>
<li>Numbers that matter can be set in the dot-matrix face, the same one as the logo.</li>
<li>Write titles as findings, not topics, wherever possible.</li></ul></div></div>""", 2, "01 · Principles"))

    # 3 Logo versions
    tiles = [("ism-nu-wordmark-on-dark", "#000", "Wordmark on dark"),
             ("ism-nu-wordmark-on-light", T["paper"], "Wordmark on paper"),
             ("ism-nu-stacked-on-dark", "#000", "Stacked, for square spaces"),
             ("ism-nu-mark-on-dark", "#000", "Mark, for icons and avatars"),
             ("ism-nu-wordmark-white", "#000", "One colour, light"),
             ("ism-nu-wordmark-black", T["paper"], "One colour, dark"),
             ("ism-nu-stacked-on-light", T["paper"], "Stacked on paper"),
             ("ism-nu-mark-on-light", T["paper"], "Mark on paper")]
    cells = "".join(f'<div><div class="tile cell" style="background:{bg}">{svg(n)}</div><p class="lab" style="margin-top:10px">{t}</p></div>'
                    for n, bg, t in tiles)
    pages.append(page("", f"""<h2>Logo</h2><p>ISM/NU set in Doto, the dot-matrix face from the website, with /NU in the accent colour. The files are outlines, so the logo looks the same everywhere without the font installed.</p>
<p>The mark is a small space telescope between two stars, drawn on a 16-pixel grid so it stays sharp as a browser tab icon. Where a service crops pictures to a circle, use the avatar file, which leaves room for the crop.</p>
<div class="grid cols4" style="margin-top:28px">{cells}</div>""", 3, "02 · Logo"))

    # 4 Logo use
    pages.append(page("", f"""<div class="grid cols2" style="gap:72px">
<div><h2>Using the logo</h2>
<p>Keep clear space around the logo equal to half its height. On slides, posters and announcements it sits in a corner, small, the way it sits in the website's header.</p>
<p>Smallest size: 12 px tall on screen and 4 mm in print. Below that, use the mark.</p>
<p>Use the one-colour versions where red is not available or would be too small to read, for example in the site header, on single-colour print, in footers under 20 px tall and on embroidery.</p>
<p>On a photo or map, place it on a dark part of the image or dim the image under it. Use the "on dark" files on dark grounds and the "on light" files on paper.</p></div>
<div><h2>Avoid</h2><ul>
<li>Retyping ISM/NU in another font, including Doto, instead of using the files.</li>
<li>Changing the red to another colour, or making ISM red and /NU white.</li>
<li>Stretching, outlining, adding shadows or glows.</li>
<li>Placing it over a bright part of an image without dimming.</li>
<li>Writing "ISM-NU" or "ISM NU" in running text. In text, write "the ISM group at Nazarbayev University".</li></ul>
<div class="grid cols2" style="margin-top:28px">
<div class="cell tile" style="background:#000;position:relative"><div style="outline:2px dashed {T['signal']};outline-offset:24px;width:80%">{svg('ism-nu-wordmark-on-dark')}</div></div>
<div class="cell tile" style="background:#000"><div style="width:22%">{svg('ism-nu-wordmark-on-dark')}</div></div></div>
<div class="grid cols2"><p class="lab" style="margin-top:10px">Clear space: half the height</p><p class="lab" style="margin-top:10px">Small use: 12 px tall at least</p></div></div></div>""", 4, "02 · Logo"))

    # 5 Colour
    rows = ""
    for key, name, role in COLOURS:
        hx = T[key] if len(T[key]) == 7 else "#000000"
        r, g, b = hex_rgb(hx)
        ground = "paper" if key in ("signal-on-paper", "on-paper", "on-paper-dim") else ("void" if key in ("signal", "grey") else None)
        cr = f"{contrast(hx, T[ground]):.1f}:1 on {ground}" if ground else ""
        rows += (f'<div><div style="height:150px;background:{hx};border:1px solid rgba(10,10,11,.15)"></div>'
                 f'<h3 style="margin-top:14px">{name}</h3><p class="mono" style="font-size:15px;margin:0">{hx.upper()} · {r} {g} {b}</p>'
                 f'<p class="dim" style="font-size:15px;margin:6px 0 0">{role}</p><p class="lab" style="margin-top:6px">{cr}</p></div>')
    pages.append(page("", f"""<h2>Colour</h2><p>Seven values, read from the website's stylesheet. There is no second accent and no tint scale: the colour in the group's material comes from the maps and figures.</p>
<div class="grid" style="grid-template-columns:repeat(7,1fr);gap:20px;margin-top:28px">{rows}</div>
<p class="dim" style="margin-top:28px;font-size:16px">Red text on paper uses Signal on paper. The brighter Signal reaches only 3.2:1 there, too low for small text. For plots, keep the data's own colour maps and use Signal only to mark the one curve or region the slide is about.</p>""", 5, "03 · Colour"))

    # 6 Type
    pages.append(page("", f"""<h2>Type</h2>
<div class="grid" style="grid-template-columns:1.25fr 1fr 1fr;gap:48px;margin-top:20px">
<div><p class="lab red">Headlines · Archivo at 62% width, 800</p><div style="font:400 104px/.86 Cond;text-transform:uppercase">Magnetic fields in the LMC</div>
<p class="dim" style="margin-top:16px;font-size:16px">Always capitals, tight line height. Slide titles 64 to 72 px, title slides 128 px, posters 180 pt and up.</p></div>
<div><p class="lab red">Body · Archivo</p><p style="font-size:24px;line-height:1.45">After the Milky Way foreground is removed, the field follows the atomic gas along the ridges south of 30 Doradus.</p>
<p class="dim" style="font-size:16px">Sentence case. At least 28 px on slides and 32 pt on posters.</p></div>
<div><p class="lab red">Labels and data · JetBrains Mono</p><p class="mono" style="font-weight:700;font-size:16px;letter-spacing:.12em">PLANCK 353 GHZ · 3° · 2.6 KPC</p>
<p class="mono" style="font-size:20px">n ≈ 10³ cm⁻³</p>
<p class="lab red" style="margin-top:28px">Numbers · Doto</p><div style="font:400 96px/1 Dot;color:{T['signal-on-paper']}">3.6%</div>
<p class="dim" style="font-size:16px">One number per page, large.</p></div></div>
<p class="dim" style="margin-top:28px;font-size:16px">Archivo has no Greek letters, ≈ or superscript minus. Canva fills those characters from another font, which is fine in running text. Set formulas and units in JetBrains Mono, which has them.</p>""", 6, "04 · Type"))

    # 7 Type in Canva and Russian
    pages.append(page("", f"""<div class="grid cols2" style="gap:72px"><div><h2>Fonts in Canva</h2>
<p>Canva's library has JetBrains Mono but not Archivo or Doto. There are two versions of every template.</p>
<table><tr><th>Role</th><th>Brand version</th><th>Canva version</th></tr>
<tr><td>Headlines</td><td>Archivo Condensed ExtraBold</td><td>Oswald, bold</td></tr>
<tr><td>Body</td><td>Archivo</td><td>Inter</td></tr>
<tr><td>Labels, data</td><td>JetBrains Mono</td><td>JetBrains Mono</td></tr>
<tr><td>Numbers</td><td>Doto Black</td><td>JetBrains Mono, bold</td></tr></table>
<p style="margin-top:20px">The Brand version needs the four files from brand/assets/fonts in your Canva Brand Kit (Canva Pro, Teams or Education). On a Free account, or if the fonts show up replaced, use the Canva version.</p></div>
<div><h2>Russian and Kazakh</h2>
<p>Archivo and Doto have no Cyrillic letters. For text in Russian or Kazakh, use the Canva version of a template. Oswald, Inter and JetBrains Mono cover both languages.</p>
<div class="cell" style="margin-top:20px"><p class="mono" style="font-weight:700;font-size:15px;letter-spacing:.12em;margin:0 0 12px">СЕМИНАР · АСТАНА · 27 НОЯБРЯ</p>
<p class="mono" style="font-size:19px">Магнитное поле БМО, n ≈ 10³ см⁻³</p>
<img src="{(PREV / 'slides-canva-01.png').as_uri()}" style="width:100%;display:block;margin-top:12px">
<p class="lab" style="margin-top:8px">Canva version: Oswald headline, Inter body</p></div>
<p class="dim" style="font-size:16px;margin-top:12px">The logo stays in Latin letters in every language.</p></div></div>""", 7, "04 · Type"))

    # 8 Elements
    pages.append(page("dark", f"""<h2>Graphic elements</h2>
<div class="grid cols3" style="gap:40px;margin-top:12px">
<div class="cell" style="height:250px;position:relative"><span class="corner c1" style="top:20px;left:20px"></span><span class="corner c2" style="top:20px;right:20px"></span><span class="corner c3" style="bottom:20px;left:20px"></span><span class="corner c4" style="bottom:20px;right:20px"></span>
<p class="lab" style="position:absolute;left:60px;bottom:52px">Corner brackets</p></div>
<div class="cell" style="height:250px"><p class="lab">Event · 27 November 2026</p><div style="border-bottom:2px solid {T['ink']};margin:20px 0"></div><p class="lab red">● Live</p><p class="lab">LMC alt −64.0° · below horizon</p></div>
<div class="cell" style="height:250px"><div style="font:400 110px/1 Dot;color:{T['signal']}">01</div><p class="lab" style="margin-top:20px">Section number in Doto</p></div></div>
<div class="grid cols3" style="gap:40px;margin-top:28px">
<p class="dim">Red corner brackets frame a title page, a full image or a poster header. They come from the frame around the site's maps. Use one set per page.</p>
<p class="dim">Labels are mono capitals with 0.12 em spacing, in grey on dark and dim ink on paper. Thin rules (2 px on screen, 1 pt in print) separate a title from its content.</p>
<p class="dim">Maps get the furniture a reader looks for: a scale bar, north and east, the beam or resolution and a credit line, as on the website.</p></div>""", 8, "05 · Elements", dark=True))

    # 9 Images
    imgs = [("public/sky/comp-galactic_centre-960.webp", "Galactic centre"), ("public/sky/comp-monoceros_ob1-960.webp", "Monoceros OB1"),
            ("public/sky/lmc-bfield.webp", "LMC, Planck field"), ("public/webb/tarantula-960.webp", "30 Doradus, Webb")]
    cells = "".join(f'<div><div style="height:230px;background:url({(BRAND.parent / p).as_uri()}) center/cover"></div><p class="lab" style="margin-top:10px">{t}</p></div>' for p, t in imgs)
    pages.append(page("", f"""<h2>Images</h2>
<div class="grid cols4" style="margin-top:12px">{cells}</div>
<div class="grid cols2" style="gap:72px;margin-top:32px">
<p>Use the group's own maps first, then public survey data, then press images from Webb or Hubble. Never stock "space" art. Put the credit line on the same page as the image, in a mono label: object, then instrument or survey, then licence where one applies.</p>
<p>Do not recolour or tint the data. To put text over an image, darken that part of the image toward black, as the template backgrounds do. Unpublished data and collaboration-internal maps (for example GASKAP cubes) stay out of public material until the collaboration agrees.</p></div>""", 9, "06 · Images"))

    # 10 Slides
    sl = sorted(PREV.glob("slides-*.png"))
    pick = [sl[i] for i in (0, 2, 4, 5, 6, 9, 11, 14) if i < len(sl)]
    cells = "".join(f'<img src="{p.as_uri()}">' for p in pick)
    pages.append(page("", f"""<h2>Slides</h2><p>Fifteen layouts at 1920 × 1080. Black for the title, section dividers and full images; paper for everything with text, plots or tables. White-background plots go on paper slides as they are.</p>
<div class="grid cols4 thumbs" style="margin-top:20px;gap:16px">{cells}</div>""", 10, "07 · Templates"))

    # 11 Announcements and posters
    ann = [p for p in (PREV / "post.png", PREV / "a4.png", PREV / "poster.png") if p.exists()]
    cells = "".join(f'<img src="{p.as_uri()}" style="height:420px;width:auto;border:1px solid rgba(10,10,11,.15)">' for p in ann)
    pages.append(page("", f"""<div class="grid" style="grid-template-columns:420px 1fr;gap:40px">
<div><h2>Announcements and posters</h2>
<p>A seminar announcement as a 4:5 post (1080 × 1350) and as an A4 flyer, both with a QR placeholder. An A0 portrait poster with three columns.</p>
<p>On the poster, keep body text at 32 pt or larger and the title on two lines. Make the title the finding, not the topic.</p></div>
<div style="display:flex;gap:20px;align-items:flex-start">{cells}</div></div>""", 11, "07 · Templates"))

    # 12 Files
    pages.append(page("", """<h2>Files</h2>
<table><tr><th>What</th><th>Where</th></tr>
<tr><td>Logos, SVG and PNG</td><td class="mono">brand/assets/logo/</td></tr>
<tr><td>Fonts for upload to Canva or install</td><td class="mono">brand/assets/fonts/</td></tr>
<tr><td>Canva Brand Kit</td><td>"ISM/NU": colours, logos and the four fonts</td></tr>
<tr><td>Canva templates, Brand version</td><td>ISM/NU · Slides, Announcement post, Announcement A4, Poster A0 (Brand fonts)</td></tr>
<tr><td>Canva templates, Canva version</td><td>The same four, marked "Canva fonts"</td></tr>
<tr><td>PowerPoint files</td><td class="mono">brand/out/*.pptx, built by brand/build_templates.py</td></tr>
<tr><td>Website source of the colours</td><td class="mono">src/styles/global.css</td></tr></table>
<p class="dim" style="margin-top:28px">The colours, logos, fonts and templates are generated from the website repository, so a change to the site's palette reaches every file the next time the scripts run. Fonts: Archivo, Doto and JetBrains Mono, all under the SIL Open Font License.</p>""", 12, "08 · Files"))

    doc = f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{''.join(pages)}</body></html>"
    src = OUT / "brand-guide.html"
    src.write_text(doc)
    pdf = OUT / "ism-nu-brand-guide.pdf"
    subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--allow-file-access-from-files",
                    "--no-pdf-header-footer", f"--print-to-pdf={pdf}", src.as_uri()], check=True,
                   stderr=subprocess.DEVNULL)
    return pdf


if __name__ == "__main__":
    print(build())
