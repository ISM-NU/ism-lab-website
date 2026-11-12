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
- GASKAP-HI LMC cube: ours comes from the collaboration's internal drive, and
  only the SMC cube is public (CSIRO DAP, doi:10.25919/www0-4p48). The site
  uses GASS (public Parkes survey, 16') for LMC H I. `scripts/render_lmc.py`
  takes `HI_CUBE=<path>`, so a sharper public cube can replace GASS later.
- Sharper H I option: image the public ASKAP visibilities (CASDA, project
  AS108) with IViS (github.com/antoinemarchal/ivis, GPU) on Irgetas. This is a
  separate task: first check which LMC measurement sets are public and their size.
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
- [ ] IViS imaging of public ASKAP LMC visibilities
- [ ] Domain, hosting, editors
- [ ] Performance pass on mobile for the scroll zoom

## Open items

- If the old Go site or its database still runs anywhere, rotate its
  passwords. Deleting the plaintext credential files did not rotate them.
