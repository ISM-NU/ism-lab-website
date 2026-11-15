# ISM group website

Website of the interstellar medium group at Nazarbayev University. It is a
static Astro site built around real sky data: Webb images, Planck dust
polarization, Parkes H I and the group's own maps. `PLAN.md` has the decisions
and the current status. The earlier Go and PostgreSQL site is kept at the git
tag `legacy-go-site`.

## Run it

Needs Node 22.23 or newer.

    npm install
    npm run dev        # http://localhost:4321 with live reload
    npm run check      # type and template check
    npm run build      # static site in dist/
    npm run preview    # serves dist/ in the background on localhost:4321;
                       # stop it with `npx astro preview stop`

## Content

Text lives in Markdown with typed front matter (`src/content.config.ts`):

- `src/content/people/` has one file per member. `mock: true` marks a
  placeholder, shown with a Mock tag and dot-matrix initials.
- `src/content/projects/` has the research lines. `papers` lists ADS bibcodes
  that must exist in `src/data/publications.json`, or the build fails.
  `upcoming` items are work in progress and show as Coming soon until Dana
  approves them.
- `src/content/news/` has news and events. An event dated in the future shows
  its `registration` link.

Only published or otherwise public material goes on the site.

## Data pipeline

The generated files in `public/` and `src/data/` are committed, so a normal
build needs none of this. Rerun the scripts when a source changes.

| Script | Reads | Writes |
|---|---|---|
| `scripts/fetch_publications.py` | NASA ADS API (`ADS_API_TOKEN` or `~/.ads/dev_key`) | `src/data/publications.json` |
| `scripts/webb_images.py` | ESA/Webb release images, cached in `.cache/webb/` | `public/webb/*.webp`, `src/data/detections.json` |
| `scripts/render_lmc.py` | Planck 353 GHz, GASS H I and MAGMA CO from the LMC workspace data | `assets/lmc/` (not tracked) |
| `scripts/web_assets.py` | `assets/lmc/` | `public/sky/*.webp`, `src/data/sky.json` |
| `scripts/composites.py` | Herschel, Spitzer, WISE (HiPS tiles), SHASSA H-alpha (SkyView), Planck; HiPS cutouts cached in `.cache/hips/` | `public/sky/comp-*.webp`, `src/data/composites.json` |

    python3 scripts/fetch_publications.py
    python3 scripts/webb_images.py
    LMC_DATA=/path/to/lmc-data python3 scripts/render_lmc.py
    LMC_DATA=/path/to/lmc-data python3 scripts/render_lmc.py --regions
    python3 scripts/web_assets.py
    LMC_DATA=/path/to/lmc-data python3 scripts/composites.py [lmc galactic_centre monoceros_ob1]

`render_lmc.py` reads the H I cube named by `HI_CUBE` (default: the GASS LMC
subcube). The combined GASKAP + Parkes LMC cube the group works with is
internal to the collaboration. Single GASKAP fields are public in CASDA, but
the site uses GASS until Dana and the collaboration agree to show GASKAP
images.

## Deploy

`deploy/deploy.sh` runs the checks and tests, builds `dist/`, rsyncs it with
`deploy/` to `~/ism-website` on musicroombot and (re)starts a Caddy container
on `127.0.0.1:8796` (`deploy/compose.yml`). The host Caddy serves the public
hostname from `deploy/Caddyfile.snippet`; adding that block needs sudo on the
server and a DNS A record for the hostname.

## Credits

Webb images: NASA, ESA, CSA, STScI via ESA/Webb (CC BY 4.0). Planck HFI
353 GHz: ESA Planck Legacy Archive. H I: GASS, Kalberla and Haud (2015). CO:
MAGMA, Wong et al. (2011). Herschel: ESA. Spitzer and WISE: NASA/JPL-Caltech.
SHASSA: Gaustad et al. (2001). Fonts: Doto, Archivo and JetBrains Mono (SIL OFL).
