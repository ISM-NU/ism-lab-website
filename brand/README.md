# Brand kit

Logo files, fonts, templates and the brand guide for the ISM group. Everything
here is generated from the website: colours are read from
`src/styles/global.css`, type comes from the site's font packages in
`node_modules`, and backgrounds are the public images in `public/`.

| Script | Writes |
|---|---|
| `build_assets.py` | `assets/logo/` (wordmark, stacked, mark; SVG outlines and 2000 px PNG), `assets/fonts/` (static cuts for Canva or desktop install) and `public/favicon.svg` |
| `build_templates.py` | `out/ism-nu-{slides,announcement-post,announcement-a4,poster-a0}-{brand,canva,stage}.pptx` |
| `build_book.py` | `out/ism-nu-brand-guide.pdf` (reads previews from `out/previews/`) |
| `build_share.py` | `public/brand/` (guide, logo, font and PowerPoint downloads for the site's `/brand` page) and `src/data/brand-files.json` |
| `make_avatar.py` | `ism-nu-github-avatar.png` |

    python3 -m venv /tmp/brand-venv && /tmp/brand-venv/bin/pip install python-pptx pillow fonttools brotli
    /tmp/brand-venv/bin/python brand/build_assets.py      # also needs magick
    /tmp/brand-venv/bin/python brand/build_templates.py
    /tmp/brand-venv/bin/python brand/build_book.py        # needs google-chrome
    /tmp/brand-venv/bin/python brand/build_share.py       # needs gs; then deploy the site

`assets/` is tracked so people can download the logos and fonts. `out/` is not.

The mark (a space telescope between two stars) is pixel art on a 16 x 16 grid,
kept as a text grid in `build_assets.py`. Edit the pixels there, never
`public/favicon.svg` by hand. `ism-nu-mark-avatar` is for services that crop to
a circle; the plain mark files lose their stars in a round crop.

## Getting templates into Canva

Canva's PowerPoint import keeps layout, colours and images, but:

- it matches fonts only against Canva's own library and ignores fonts uploaded
  to a Brand Kit;
- it drops the all-caps attribute and paragraph spacing (the builder writes
  capitals and uses line height instead);
- it imports A4 and A0 pages as A1 (2246 x 3179 px). Fix with Resize, custom
  size in mm, "Resize this design".

So the two versions go in differently:

- Canva fonts (Free plan, Russian text): import `*-canva.pptx` through the
  editor's Upload button. Done.
- Brand fonts: upload `assets/fonts/*.ttf` to the Brand Kit first, import
  `*-stage.pptx`, then in the font panel use "Change all" three times:
  Oswald to Archivo Condensed ExtraBold Regular, Inter to Archivo, IBM Plex
  Mono to Doto Black Regular. The stand-ins exist only to make that swap
  one-to-one.

`*-brand.pptx` names the real fonts and is for PowerPoint or Keynote on a
computer with `assets/fonts` installed.

After a swap, export to PDF and run `pdffonts` on it: only the brand faces
should appear, plus Noto for the few symbols Archivo lacks (≈, Greek,
superscript minus).

## Sharing

Colleagues get everything from `/brand` on the website: the page is not in the
navigation and carries `noindex`, so it is shared by link. It lists the eight
Canva template links (Share, Template link) and the downloads made by
`build_share.py`. After rebuilding a template in Canva, make a new template
link for it and replace the old one in `src/pages/brand.astro`.
