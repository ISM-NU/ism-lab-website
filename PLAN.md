# ISM website rewrite: plan and status

The previous Go/PostgreSQL site is kept in history at tag `legacy-go-site`.

## Goal

A highly visual site for the ISM group (supervisor Dana Alina, Nazarbayev
University) that shows the group's work through real sky data and animation:
magnetic fields, filaments, dust polarization, the LMC, gas phases.
Hosted on the group's own domain.

## Content the site must carry (from the legacy site)

Members, projects, publications, datasets, events (with registration link),
news/announcements, contacts.

## Decisions so far

- Static site (no server, no login). Content as files in this repo.
- Visuals come from public survey data rendered by `scripts/render_lmc.py`
  (GASKAP-HI + Parkes, MAGMA CO, Planck 353 GHz). Only published results may
  appear on the site; unpublished numbers from the LMC experiment repos stay out.

## Status

- [x] Repo moved to this folder; legacy code tagged
- [x] Render script for all-sky and LMC layers
- [ ] Direction chosen (discussion page: https://claude.ai/artifact/8jdHrZmi7vSPgNT8WwMuHG)
- [ ] Domain, hosting and editors confirmed
- [ ] Site scaffold (Astro), content model, first pages
