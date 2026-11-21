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
- Members are real entries since 2026-11-21: Dana Alina and 8 students.
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
- [x] Real member data (photos, roles, bios) from Denis (2026-11-21)
- [ ] Dana's sign-off on research graph links and COMING SOON items
- [x] Multi-band composites for LMC, Galactic centre, Mon OB1
- [ ] IViS pilot on SB33047 (needs VPN and OPAL login)
- [ ] Domain, hosting, editors
- [ ] Performance pass on mobile for the scroll zoom

## Open items

- If the old Go site or its database still runs anywhere, rotate its
  passwords. Deleting the plaintext credential files did not rotate them.

## Design and correctness pass (started 2026-11-15)

Audience: astronomers who want to learn the group's work. Correctness first.

- [x] Fact-check every number, label and caption; apply corrections
- [x] Planck renders: remove the dipole if present, replace the log floor
      with a percentile stretch, fix field angles on the Mollweide map
      (Jacobian of the projection), new palette for all Planck images
- [x] Credit Planck PR4 (NPIPE), not PR3
- [x] Zoom-out: keep the Tarantula on screen; label the 12 deg map frame honestly
- [x] Top bar gets a solid background; the bottom readout bar shows only over
      the hero and the zoom-out; drop the "Z" readout
- [x] Type: raise the small sizes (nav, labels, tags, graph, ruler)
- [x] Hero: one line on who the group is; fewer detection labels, none overlapping
- [x] Light ruler: fits without horizontal scroll, vertical on phones,
      round-unit ticks, ends at the age of the Universe
- [x] Research graph: layout with no lines through labels; edges cite
      bibcodes checked at build time; proposals are not solid edges
- [x] Home: trim repeated sections
- [x] People: unique initials, no empty grid cell
- [x] Publications: counts on the histogram, no duplicate heading
- [x] Checks: npm run check/build, screenshots at 1440 and 390, reduced
      motion and keyboard pass, impeccable detect
- [x] Site copy free of the patterns in Wikipedia:Signs_of_AI_writing
- [x] Open questions resolved from the data and papers (2026-11-15):
      Webb weic2212a is not north-up (north 13.5 deg left of vertical,
      0.0300"/px, fit to Spitzer IRAC 3.6 um), and the 4:3 crop spans 264 ly,
      not 340 (confirmed with 294 Gaia DR3 stars from the ARI mirror); the
      zoom now rotates the image to north-up. R136 position
      agrees with the fit to 0.7". IAUS 392 used GASS (per the 2024 IAU GA
      abstract on the same work). GASS server cubes are LSR. H I cut at
      182 km/s only loses Magellanic Bridge gas (0.3% inside 6 deg of the
      LMC); nothing above 340. Filament claim rewritten from Alina et al.
      2019. ML papers: Planck, Herschel, HI4PI (2022) and Planck (2025).
- [x] Light ruler: roomier lanes, no leader behind a name, end label on its own row
- [x] Field angles drawn on the pixel grid, not against image-up: grid_angle()
      in render_lmc.py (up to 20 deg on the LMC grid); FieldDots readout
      subtracts the north tilt from sky.json to show the true PA
- [x] LMC page states the published foreground removal (Alina et al. 2023);
      H I phases reported as CNM vs the rest; graph gains Mon OB1-TRAO,
      TRAO-VGT, ML edges
- [ ] Pick from docs/design-proposals.md (16 ranked ideas; its correctness
      flags 1-4 are done; the 340 ly and orientation notes there are stale)

## Build all design proposals (started 2026-11-15)

docs/design-proposals.md, all 16. Built in parallel by file ownership; the
integrator mounts components on shared pages and deletes src/pages/_lab/.
Anything re-derived from group data or worded as a finding needs Dana's OK
before the site goes public.

- [x] A: MapFrame (scale, compass, beam, colour bar), Planck S/N fade, method
      drawer with FITS downloads (2, 13). S/N > 3 over 87% of the LMC grid.
      Re-run scripts/map_meta.py (under the Planck flock) after committing so
      the drawer shows a clean commit hash. For Dana: FITS licence wording;
      Mon OB1 distance now 745 pc (Zucker et al. 2019).
- [x] B: WebGL field from Stokes Q/U (FieldGL, fieldgl.ts), LMC foreground
      wipe (ForegroundWipe). Wipe stays behind flags.foregroundWipe = false
      until Dana approves: re-derived with uniform psi_fg (paper used a VGT
      angle map) and HI4PI minus GASS for N_H(MW). alpha, p_fg and medians
      match; integrated p inside 5 deg goes 2.9-3.6% -> 0.9-1.3% here vs the
      paper's 1.1% -> 3.3% (observed value checked from HEALPix). Ask Dana.
      Follow-up: FieldGL could replace the baked LIC in FieldDots and PullBack.
- [x] C: H I cube viewer (5, 16): CubeViewer.astro, public/sky/cube/hi.i16.gz
      (2.8 MB). Integrate on /research/lmc after A and D; remove the LayerLens
      velocity scrubber, then public/sky/channels/* and channels_kms.
- [x] D: findings on research pages (16, each with its source sentence in the
      front matter), Mon OB1 panel, Galactic centre PILOT/Planck, VGT premise
      (3, 11, 7). For Dana: approve every finding; North-Main is 16.0 +- 2.5 uG
      in Table 1 but "around 17" in the text; PILOT Q/U maps (CADE) not
      fetched, so only the published mean tilt is drawn.
- [x] E: polarization estimator bench (6): EstimatorBench.astro, npm test
      (16 tests). For Dana: panel 3 shows P not p (I zero level); Alina et al.
      2016 Sect. 3.3 quotes a 0.8 deg bias at S0 = pi/4, S/N 2, but its own
      Fig. 3 setup gives +2.4 deg; which configuration was meant?
- [x] F: relative orientation explorer (4). Built as a per-filament view
      (OrientationExplorer.astro, orientations.json). The VizieR table has no
      background field angle and its NHbkg equals NHtot in all 138 rows (same
      in the paper's Table A1), so the paper's Figs 5-8 cannot be rebuilt.
      Ask Dana for phi_bkg, corrected NHbkg and the 90-filament flag.
- [x] G: U-Net on Herschel filaments (9): FilamentNet.astro (preview flag
      until the authors approve), G202.3+2.5 in Mon OB1. Weights (372 MB) only
      in .cache/unet, never commit. Relative orientation came out near flat.
- [x] H: resolution ladder (8), mounted on /research. For Dana: Alina et al.
      2023 calls 16' = 200 pc, but at 49.59 kpc it is 234 pc (site shows 234);
      Orion map size, G286 JWST field and GASKAP footprint are derived or
      assumed and flagged in the panel.
- [x] I: publications filters/BibTeX/citation split, join page, LMC sky panel
      (14, 12, 15). For Dana: group-led rule (member first or last author,
      members = Alina + anyone ADS places at NU), join-page directions, the
      quoted one-line results.
- [x] Integrate: all components mounted on research pages (foreground wipe
      behind src/data/flags.ts), velocity scrubber and channel frames removed,
      lab pages deleted. check, 16 tests, build, 12 pages x 2 widths with no
      overflow or console errors, design detector 0, copy scan clean.
- [ ] Ask Dana (one meeting): everything marked "For Dana" above, then flip
      flags.foregroundWipe and drop FilamentNet's preview prop if approved.

## GitHub organisation avatar (2026-11-15)
- brand/ism-nu-github-avatar.png (1024 px), made by brand/make_avatar.py from
  public/sky/lmc-bfield.webp and the Doto font. Upload by hand in the ISM-NU
  organisation settings (the API cannot set an org avatar).

## Deploy (2026-11-15)
- [x] Static site served on musicroombot from a Caddy container on
      127.0.0.1:8796 (deploy/deploy.sh).
- [ ] Public hostname: DNS A record for ism.unsoundmint.com -> 46.62.161.228
      and the deploy/Caddyfile.snippet block in /etc/caddy/Caddyfile (sudo).
      Until Dana has approved the findings and join page, consider holding this.

## Tone, Dana, zoom resolution (2026-11-16)
- [x] Scrambled headings keep their final line breaks (word boxes in
      motion.ts scramble) instead of wrapping onto extra lines while resolving
- [x] Copy pass for register: plain headings and captions, no light-ruler
      asides, hero h1 "Interstellar medium group", hero log and H I barcode cut
- [x] Dana Alina: named in the hero and footer, lead block on People with her
      ADS record, email dana.alina@nu.edu.kz on Contact, Join and her card.
- [x] Scroll zoom: two insets around R136 (2.4 and 0.6 deg) on the LMC
      composite's grid and levels; 2048 px LMC base; 2880 px Tarantula
- [x] VGT.jl is private (2026-11-16): no links to it; the Join direction cites
      Alina et al. 2023 instead of a repository
- [x] Spacing and type scale (global.css head comment), enforced by
      scripts/check_scale.py inside npm run check; display headings reduced
      (hero 128, page 96, section 64 px max)
- [x] Zoom target markers: signal red with dark outline, lock-on animation
- [x] Redundant intros and head paragraphs removed across pages
- [ ] Students: real roles, photos and bios (Denis is listed as "Student")
- [ ] Dana's photo; her bio uses only her thesis and the ADS record

## Mobile motion pass (2026-11-16)
- [x] Page height no longer follows an in-app browser's header (--svh in
      Base.astro, scripts/check_viewport.py)
- [x] Scroll zoom on tall screens: Webb frame on black until it shrinks, LMC
      disc fills the width, sky stage ends on about 130 deg around the LMC and
      Galactic centre, target tags flip at the right edge, LMC tag upright
- [x] Dot field: near-square on phones; on touch the lens tours N79, N11, N44,
      30 Doradus and N159 with the scroll, a tap moves it
- [x] Light-travel time: one row per object on narrow screens
- [x] Layer lens: a tap places it
- [ ] Re-render the R136 inset (lmc-tarantula) with a stretch that does not
      clip 30 Dor's core; it reads as a pale wash around 1 000 ly on every
      screen

## Dana's feedback on the home page (2026-11-21, 4Denis.docx)
- [x] Hero sentence replaced with Dana's wording (also the home meta description)
- [x] LMC, filaments, star formation: Dana's titles and summaries; the papers
      she named show on the card (`keyPapers`), full lists stay on the pages
- [x] POL card left as it is (her item 4)
- [x] New lines: optical polarimetry (Assy-Turgen map from
      scripts/assy_map.py), hub-filament systems, machine learning
      (card image from scripts/ml_card.py; virial-parameter network as
      Coming soon)
- [x] Members: Dana Alina's photo; six new students with bios (five with
      photos) plus Temirkul Umetaliev (no photo or bio from him yet);
      placeholders deleted
- [ ] Assy photos from Dana for the optical polarimetry card and page
- [ ] FILDREAMS collaboration papers for the filaments line (Dana: "можно")
- [ ] Dana to approve the summaries and page text for hub-filament systems,
      machine learning and optical polarimetry (written by Denis from the
      members' bios and the papers)
- [x] Site copy speaks as "we" (Denis, 2026-11-21); people bios stay in the
      third person
- [x] Temirkul Umetaliev listed under Alumni (`alumni: true`); no photo or bio
      from him yet
- [x] Collaborators on every project page: co-authors on our group-led papers
      in that line, minus members and alumni (collaborators() in pubs.ts);
      ORCID link from ADS, else their ADS author search; institution from the
      ADS affiliation. Former NU students without a site entry stay listed as
      collaborators until someone says they were group members.
- [ ] Optical polarimetry has no papers, so no collaborators yet; Dana to name
      the Assy partners if they should appear
- [ ] Ali Tussupov has no photo
