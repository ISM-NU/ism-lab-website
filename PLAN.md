# ISM website rewrite: plan and status

The previous Go/PostgreSQL site is kept in history at tag `legacy-go-site`.

## Goal

A highly visual site for the ISM group (supervisor Dana Alina, Nazarbayev
University) that shows the group's work through real sky data and animation:
magnetic fields, filaments, dust polarization, the LMC, gas phases. Quality
first; hosting is decided later.

## Content the site must carry (from the legacy site)

Members, projects, publications, datasets, events (with registration link),
news/announcements, contacts.

## Decisions

- Static Astro site, no server and no login. Content lives as files in this repo.
- Direction: the "observatory console" concept (brutalist, dot-matrix readouts,
  one signal red, fast detection overlays, space-relation sections). Approved
  2026-11-13 from https://claude.ai/artifact/Mai9FCdFLTE5pQhfH4bAxk
- Everything public goes on the site: all published papers and public data.
  Work in progress shows as COMING SOON until Dana approves it.
- GASKAP-HI LMC: per-scheduling-block H I cubes are public in CASDA (project
  AS108, collection GASKAP-HI, e.g. SB79298 `MS_M000+04A_5`, quality GOOD,
  released 2026-01-22, 216 GB each, 2112 channels). Downloads need an OPAL
  login. The combined LMC mosaic the group uses is still internal. Until Dana
  and the collaboration agree to show GASKAP images, the site uses GASS
  (public Parkes survey, 16') for LMC H I. `scripts/render_lmc.py` takes
  `HI_CUBE=<path>` for a sharper cube later.
- IViS (github.com/antoinemarchal/ivis, GPU) on Irgetas, approved 2026-11-13.
  Public line visibilities exist only for pilot-era SBs (33047 GOOD; 38373,
  38758, 38791, 38814, 38845, 53093 UNCERTAIN), about 30 TB in all, about
  60 GB per beam. Pilot plan: SB33047 beams nearest 30 Dor (M000+02C beam 27,
  M000+02B beam 20, M000+02A beam 21), GASS as the short-spacing model.
  Blocked on: NU VPN for ssh, an OPAL account stored on Irgetas. Scripts go in
  LMC-cold-gas (experiment repo), not here.
- Visuals: our maps are multi-band composites (`scripts/composites.py`):
  Herschel, Spitzer, WISE and SHASSA from HiPS/SkyView for the detail, Planck
  only for the field direction (LIC texture), plus a Hessian ridge filter.
  HiPS tiles are sampled directly by HEALPix index: reproject 0.21
  `hips_as_dask_array` misplaces data near the poles (about 2 deg at the LMC).
  Planck alone (5' beam) is too soft for large images.
- Publications come from ADS through `scripts/fetch_publications.py`, which
  writes `src/data/publications.json`. The build never calls ADS.
- Members are mock placeholders (`mock: true`) until real photos and bios
  arrive. There are 9 members.
- Develop on localhost for now. Domain and hosting come later.

## Done means

- `npm run check` and `npm run build` are clean.
- Screenshots of every page at 1440 and 390 px wide, with no horizontal scroll.
- A reduced-motion pass and a keyboard pass on the interactive pieces.

## Status

- [x] Repo moved to this folder; legacy code tagged
- [x] Render script for all-sky and LMC layers
- [x] Direction chosen (v2 console)
- [x] Site scaffold (Astro), content model, all pages, publications from ADS
- [ ] Real member data (photos, roles, bios) from Denis
- [ ] Dana's sign-off on research graph links and COMING SOON items
- [x] Multi-band composites for LMC, Galactic centre, Mon OB1
- [ ] IViS pilot on SB33047 (needs VPN and OPAL login)
- [ ] Domain, hosting, editors
- [ ] Performance pass on mobile for the scroll zoom

## Open items

- If the old Go site or its database still runs anywhere, rotate its
  passwords. Deleting the plaintext credential files did not rotate them.
