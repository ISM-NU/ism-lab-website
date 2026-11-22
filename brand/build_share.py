"""Download files for the site's /brand page.

Writes public/brand/: the wordmark shown on the page, the brand guide
(recompressed from 7 MB to under 1 MB) and zips of the logos, the fonts with
their licences and the PowerPoint templates. Their sizes go to
src/data/brand-files.json for the page. Run after build_assets.py,
build_templates.py and build_book.py.

    python3 brand/build_share.py   # needs gs (Ghostscript)
"""
import json
import shutil
import subprocess
import zipfile

from brandlib import ASSETS, NM, OUT, ROOT

DEST = ROOT / "public" / "brand"

# SIL OFL asks for the licence to travel with the fonts.
LICENCES = {
    "OFL-Archivo.txt": NM / "@fontsource-variable/archivo/LICENSE",
    "OFL-Doto.txt": NM / "@fontsource/doto/LICENSE",
}
FONT_NOTE = """Fonts of the ISM group brand, from the group website.

Archivo Condensed ExtraBold: headlines (the site's Archivo at 62% width).
Archivo Regular and Bold: body text.
Doto Black: the dot-matrix face of the logo and big numbers.

Install them before using the PowerPoint templates. In Canva, upload them to a
Brand Kit (paid or education plans only) or use the "Canva fonts" templates.
Archivo and Doto have no Cyrillic: for Russian, use the "Canva fonts"
templates. Both families are under the SIL Open Font License, included here.
"""


def zipped(name, files):
    """files: (path inside the zip, source path or text)."""
    with zipfile.ZipFile(DEST / name, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, src in files:
            if isinstance(src, str):
                z.writestr(arc, src)
            else:
                z.write(src, arc)


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    # Chrome embeds the map images losslessly; JPEG at q88 keeps them clean on
    # screen and in office printing. RGB conversion drops the ICC profiles that
    # some viewers fail to read after Ghostscript.
    subprocess.run(["gs", "-q", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.6", "-dPDFSETTINGS=/printer",
                    "-sColorConversionStrategy=RGB", "-dAutoFilterColorImages=false", "-dColorImageFilter=/DCTEncode",
                    "-dJPEGQ=88", "-dNOPAUSE", "-dBATCH", f"-sOutputFile={DEST / 'ism-nu-brand-guide.pdf'}",
                    str(OUT / "ism-nu-brand-guide.pdf")], check=True)
    # The /brand page shows the wordmark itself.
    shutil.copy(ASSETS / "logo" / "ism-nu-wordmark-on-dark.svg", DEST)
    logos = sorted((ASSETS / "logo").glob("*.*"))
    zipped("ism-nu-logos.zip", [(f"ism-nu-logos/{p.name}", p) for p in logos])
    fonts = sorted((ASSETS / "fonts").glob("*.ttf"))
    zipped("ism-nu-fonts.zip", [(f"ism-nu-fonts/{p.name}", p) for p in fonts]
           + [(f"ism-nu-fonts/{n}", p) for n, p in LICENCES.items()]
           + [("ism-nu-fonts/README.txt", FONT_NOTE)])
    # The "brand" PowerPoint files name the real fonts; the stage and canva
    # versions exist only for the Canva import and stay out of the download.
    decks = sorted(OUT.glob("ism-nu-*-brand.pptx"))
    zipped("ism-nu-powerpoint.zip", [(f"ism-nu-powerpoint/{p.name.replace('-brand', '')}", p) for p in decks])
    # File sizes for the page, which has no file system access at type-check time.
    sizes = {p.name: p.stat().st_size for p in sorted(DEST.iterdir())}
    (ROOT / "src/data/brand-files.json").write_text(json.dumps(sizes, indent=2) + "\n")
    for name, n in sizes.items():
        print(f"public/brand/{name} {n / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
