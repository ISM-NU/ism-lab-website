# AGENTS.md

Rules for working in this repo. `README.md` has setup and the data pipeline,
`PLAN.md` has the decisions and the status.

## Before pushing

    npm run check    # check_scale.py, check_viewport.py, then astro check
    npm test         # node --test src/lib/*.test.mjs
    npm run build    # static site in dist/

`deploy/deploy.sh` runs the same three before it publishes. "Done means" in
`PLAN.md` also asks for screenshots at 1440 and 390 px, a reduced-motion pass
and a keyboard pass; no script does those.

## What the scripts already enforce

- Spacing and type sizes stay on the scale at the top of `src/styles/global.css`
  (`scripts/check_scale.py`, `--fix` snaps a miss to the nearest step).
- No `vh`, `svh`, `dvh` or `lvh` units in `src/` (`scripts/check_viewport.py`).
- Types and templates (`astro check`).
- Front matter in `src/content/` must match the schema in
  `src/content.config.ts`, and its bibcodes must exist in
  `src/data/publications.json`. The build fails otherwise.
- One-line results in `src/data/results.ts` must be verbatim parts of the ADS
  abstract (`src/lib/pubs.ts`). The build fails otherwise.
- Estimator maths follows the cited papers (`src/lib/estimators.test.mjs`).

## Generated files

`public/` images and `src/data/*.json` come from `scripts/`. Rerun the script
that writes a file instead of editing it. The README table says which script
writes what.
