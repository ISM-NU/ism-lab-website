# ISM group site: critique and proposals

Reviewed 2026-11-15 against the dev server at http://127.0.0.1:4321, at 1440x900 and 390x844. Nothing in the repository was edited and no render script was run. Screenshots are in /tmp/ism-audit/fable/. The ones cited below are contact sheets I opened: `sheet-home-d-1.jpg`, `sheet-home-d-2.jpg`, `sheet-home-m.jpg`, `sheet-research-lmc-d.jpg`, `sheet-research-other-d.jpg`, `sheet-misc-d.jpg`, `sheet-inner-m.jpg`, `sheet-interactive.jpg`, and two crops, `crop-ruler-end.png` and `crop-fielddots.png`. The individual frames (`home-d-00.png` and so on) sit next to them.

Paper abstracts quoted here were read from NASA ADS today. Where I could not check something I say so.

## 1. Critique of the site as it renders

### What works

The zoom from the Webb frame out to the LMC and then to the Planck sky (`src/components/PullBack.astro`, `sheet-home-d-1.jpg`) is the best thing on the site. The frames are sized from real distances and the readout changes from light years to degrees at the right moment. The captions say what the streaks are and that the Milky Way foreground is still in them, so an astronomer can check every number on screen.

The pipeline is honest. `scripts/render_lmc.py` converts Planck U from COSMO to IAU, rotates Galactic angles to celestial north, removes the solar dipole from NPIPE, and corrects the field angle for the Mollweide projection. `scripts/composites.py` samples HiPS tiles by HEALPix index because the library route misplaced the LMC. This care is invisible to a visitor, which is a missed opportunity (proposal 13).

The build fails when a graph edge or a project cites a bibcode that is not in `src/data/publications.json`. That is the right kind of guard.

The copper palette reads as dust and is consistent across the Planck images. The type is confident. The live readouts in the frame are correct: at 12:54 UTC the page showed LST 21:18 and an LMC altitude of -57.5 degrees, and astropy gives 21:18 and -57.45 for the coordinates on the contact page. The contact page line that the LMC never rises over Astana is true and worth keeping.

### What is weak or unconvincing to an astronomer

The site shows data, and the group's results are missing. Each research page is one or two paragraphs followed by a list of papers (`src/pages/research/[id].astro`, `sheet-research-other-d.jpg`). No page states a finding or shows a measured quantity. A referee or a prospective student leaves knowing which surveys the group uses and not what it concluded. Compare the abstracts: a field tilted 22 degrees to the Galactic plane across the central molecular zone, a transition in filament orientation near n_H of 10^3 cm^-3, a foreground-subtracted LMC field that follows the H I arms. None of that is on the site.

The central LMC visual is the thing the group's main paper corrects. Every LMC field image and the dot field use the raw Planck angle with the Milky Way foreground included. The captions admit it, which is good, but Alina et al. 2023 is precisely about removing that foreground. The site leads with the "before" and lists the "after" as coming soon (see section 3).

The maps have no furniture. No image has a scale bar, a north and east compass, a beam circle or a colour bar (`sheet-home-d-2.jpg`, `sheet-interactive.jpg`). The velocity layer names its range in a text note beside the map but the map itself has no bar. For this audience these are the first things the eye looks for.

The field texture looks sharper than the data. In the Galactic centre and Mon OB1 composites the Planck orientation is smoothed to about 24 arcmin FWHM (`field_angle` in `scripts/composites.py`) and drawn as fine streaks over a 2 degree and a 3 degree field with Herschel detail underneath. That is about five and seven resolution elements across the image. The streaks read as scratches or motion blur on the cards (`sheet-home-d-2.jpg`, Mon OB1 and Galactic centre tiles) and suggest a resolution the field data do not have. A beam circle would fix the honesty problem; a coarser drawing style (short segments on a beam-spaced grid) would fix the look.

Colour in the dot field carries no data. In `src/components/FieldDots.astro` dashes turn red near the pointer and white further out, and their length grows toward the pointer (`crop-fielddots.png`). Red is the site's signal colour, so a reader expects it to mean something. Polarization fraction and signal to noise, which are available from the same maps, are not shown, and there is no mask where the Planck signal is weak around the LMC.

The hero is somebody else's image with decorative detections. The Webb Tarantula frame is credited and the log line says "brightest blobs in the press image", which is honest, but boxes snapping onto a press JPEG look like a source finder and are not one. The frame is about 7 arcmin wide, smaller than one resolution element of the field maps, so the group's own measurements cannot appear in it. The hand-off to the zoom saves it. I would keep the image (it is decided) and drop or shrink the blob boxes.

The velocity scrubber is grey fog. Stepping the H I channels in `src/components/LayerLens.astro` overlays a white haze on the composite (`sheet-interactive.jpg`, lower left). There is no spectrum, no marker on the hero's H I profile, and the GASS beam of 16 arcmin makes each frame soft. The idea is right and the execution undersells it (proposal 5).

The light ruler is outreach. It is well made, but it tells an astronomer nothing new, half its stops are Webb press images, and its end labels collide (`crop-ruler-end.png`). Proposal 8 reuses the component for something this audience would study.

People and news are placeholders, clearly labelled. The publications page counts 1501 citations without saying that 679 of them belong to three Planck Collaboration papers.

Mobile holds up (`sheet-home-m.jpg`, `sheet-inner-m.jpg`). At 390 px every page reports a scroll width equal to the viewport, and the ruler turns vertical. The hero's H I profile loses its meaning at that size because the label wraps and the bars are tiny.

## 2. Proposals, ranked by value to the audience

Ranking rule: a proposal ranks higher when it shows a result the group published, using data that can be shown publicly.

Data provenance uses four classes:

- repo: already in the repository (`public/sky`, `src/data`, `.cache/hips`)
- local: on this machine outside the repo (`~/Projects/LMC/lmc-data`: Planck PR4 353 GHz, the GASS cubes, MAGMA CO, the starlight polarization tables, an RM table)
- fetch: public, to download; the source is named
- internal: collaboration data (`Tb_combined_*`, `gaskap_casda`). No proposal below depends on these.

Effort: S is a day or two, M is about a week, L is several weeks.

### 1. The LMC field before and after foreground removal

What: a slider on /research/lmc and on the home page that wipes between the Planck field as observed and the field after the Milky Way foreground is subtracted, following Alina et al. 2023 (2023MNRAS.518.4466A). A third state overlays H I column contours so the reader can see the result the abstract states: after removal the field follows the atomic gas along the ridges south of 30 Doradus, the southern arm toward the SMC and the western outer arm. A small side panel shows the foreground itself: the mean Q and U around the LMC, the direction from H I velocity gradients, and the starlight polarization vectors of foreground stars used to test it.

Why: this is the group's headline LMC result and the site currently shows only the uncorrected map. It also teaches a general method in one interaction.

Data: best source is the paper's own foreground-subtracted I, Q, U maps from Dana (ask). Failing that, a re-derivation from local data: Planck PR4 (local), GASS at Milky Way velocities (fetch from the GASS data server, https://www.astro.uni-bonn.de/hisurvey/gass/; both local GASS cubes start at 182 km/s), starlight tables after Schmidt 1976 and Mathewson and Ford 1970 (local, published catalogues). A re-derivation must be labelled as "re-derived for this site following the method of the paper" and checked against the paper's figures before it ships.

Sketch: extend `scripts/render_lmc.py` with a `foreground()` step that writes Q and U before and after as two 16-bit textures on the existing 12 degree grid. Draw the field in the browser from those textures (see proposal 10) so the slider interpolates Stokes parameters and not images. New component `ForegroundWipe.astro`; reuse the pointer handling from `LayerLens.astro`.

Effort: M with the paper's maps, L if re-derived.

Risk: high if re-derived. The paper used PR3 or PR4 at its own resolution and a specific annulus; a different choice changes the angles. Dana should approve the result. Remove the "Milky Way foreground removed: coming soon" card once this exists.

### 2. Map furniture and a north fix on every sky image

What: every map gets a scale bar in parsecs and in angle, a north and east compass, a beam circle for each layer shown, and a colour bar for single-quantity layers (H I column, velocity, Planck intensity). Field drawings are masked or faded where polarized signal to noise is low. The LMC field drawings are corrected for the tilt of celestial north across the tangent-plane grid (section 3, item 1).

Why: these are what make an image a measurement. With them a visitor can read a filament length or compare the beam to a structure without leaving the page.

Data: repo and local. Scale and compass come from the WCS already in `assets/lmc` metadata and the region definitions in `scripts/composites.py`. Signal to noise uses the covariance columns of the local Planck PR4 file (II_COV, QQ_COV, QU_COV, UU_COV and the cross terms are present in its header).

Sketch: have the render scripts write a small JSON per image (pixel scale, distance, north angle at centre, beam FWHM per layer, stretch limits). One Astro component, `MapFrame.astro`, wraps any image and draws the furniture in SVG from that JSON. Use it in `Archive.astro`, `LayerLens.astro`, `PageHead.astro` and `FieldDots.astro`.

Effort: S for the furniture, M with the signal-to-noise mask.

Risk: low. Distances for Galactic clouds need a cited value each.

### 3. Research pages that state results

What: restructure each research page around three or four published findings. Each finding has one sentence, one number with its uncertainty where the paper gives one, one figure, and the bibcode. Examples drawn from the abstracts: the field across the central molecular zone is ordered and tilted about 22 degrees clockwise from the Galactic plane (Mangilli et al. 2019); in nearby filaments the relative orientation changes from mostly parallel to mostly perpendicular near n_H of 10^3 cm^-3 in the parts of filaments away from clumps (Alina et al. 2019); in Mon OB1 east the field runs along the northern filaments and the southern part shows at least two distinct orientations (Alina et al. 2022).

Why: this is the question the audience arrives with. It also gives students a way into the papers.

Data: the papers. Figures are either redrawn from public data by the site's scripts (preferred, and the other proposals supply several) or reproduced from the journal with permission. A&A and MNRAS allow authors to reuse their own figures with attribution; check each licence.

Sketch: add a `findings` list to the project front matter in `src/content/projects/*.md` (text, value, figure, bibcode), validated in `src/content.config.ts` against `publications.json` the same way `papers` is. Render it in `src/pages/research/[id].astro` above the paper list.

Effort: M, mostly Dana's time to choose and approve the findings.

Risk: wording. Each sentence must be checked by an author. The current filaments paragraph shows how easily a summary drifts from the abstract (section 3, item 3).

### 4. Relative orientation explorer

What: an interactive histogram of relative orientations between filaments and the field. The reader selects by environment column density and by filament contrast and watches the histogram move between parallel and perpendicular, which is the analysis of Alina et al. 2019. A sky map shows where the selected filaments lie. A second tab does the same for the Herschel fields of Oers et al. 2026, binned by column density and filament width.

Why: the relative-orientation statistics are a core output of the group, and a reader learns more from changing a cut than from a static figure. Collaborators can check their own region.

Data: fetch. VizieR J/MNRAS/485/2825 (Alina et al. 2019), already linked from `src/pages/data.astro`. I could not read its ReadMe today because the CDS servers were unavailable, so the columns are unverified. If the table does not carry relative angles and densities per filament, ask Dana for the analysis table. For Oers et al. 2026, check whether the paper has a CDS table.

Sketch: a script `scripts/fetch_catalogues.py` writes a compact JSON (a few thousand rows). Client side, a canvas histogram and a small Mollweide scatter drawn on `public/sky/allsky.webp`. No library needed; d3-array for binning if wanted.

Effort: M.

Risk: medium. Selections must reproduce the paper's figures at the paper's cuts; add a build-time test that the default view matches published bin counts if the table allows it.

### 5. H I cube under the pointer

What: replace the velocity fog in the layer lens with a proper cube viewer. Moving over the LMC shows the 21 cm spectrum at that position. Dragging on the spectrum sets a velocity window and the map shows the gas in that window. A position-velocity cut along the bar shows the rotation of the disc. With a GASS cube that extends to Milky Way velocities, the spectrum also shows the Galactic emission near 0 km/s, separated from the LMC near 270 km/s, which is the reason velocity can isolate the foreground.

Why: astronomers think in spectra. It also sets up proposal 1, and it is where a GASKAP cube would go once released.

Data: local for the LMC velocities. `eq_subcube_182to339_gass_279_-33_1444812272.fits` is 151 by 151 pixels and 193 channels; `gass_279_-33_LMC_range_1444812272.fits` is 301 by 301 pixels and 224 channels, covering 182 to 366 km/s. Neither reaches Milky Way velocities, so that part needs a new GASS cutout (fetch, public; McClure-Griffiths et al. 2009, Kalberla and Haud 2015). The same download can supply the 160 to 390 km/s range PLAN.md asks for.

Sketch: the cube is small. Pack it as one 16-bit PNG atlas or a gzipped Int16 array and load it on demand (151 by 151 by 193 samples is about 9 MB raw as Int16; measure the compressed size). WebGL2 with a 3D texture gives the windowed map in a fragment shader; the spectrum is a canvas line. Use the wider velocity range so the high-velocity wing is not clipped.

Effort: M.

Risk: low. Label the beam (16 arcmin) on the map. State the velocity frame once it is settled (section 3, item 6).

### 6. Polarization estimator bench

What: an interactive demonstration of why polarization fraction is biased at low signal to noise. The reader sets a true fraction and a noise level, the page draws many noisy Q and U samples, and histograms compare the naive estimate with the estimators studied in Montier et al. 2015 (parts I and II) and Plaszczynski et al. 2014. A second panel shows the same for the angle dispersion function (Alina et al. 2016). A final panel applies the naive and corrected estimators to a real patch of the Planck LMC map.

Why: this is method work the group is cited for, and it currently has no visual on the site at all. Students see in a minute why the papers exist.

Data: none for the simulation. The real-data panel uses Planck PR4 I, Q, U and their covariances (local).

Sketch: plain TypeScript, a seeded Gaussian generator, canvas histograms. Component `EstimatorBench.astro` on /research/dust-polarization. Transcribe the estimator formulas from the papers and unit-test them against the tabulated values there; do not write them from memory.

Effort: M.

Risk: medium. A wrong formula on a page about bias would be embarrassing, hence the tests and a review by Dana.

### 7. The Galactic centre in PILOT and in Planck

What: the central molecular zone with the field drawn twice, from Planck 353 GHz at its real resolution and from PILOT at 240 microns and 2.2 arcmin, with the 22 degree tilt marked against the Galactic plane.

Why: the site's Galactic centre image carries a Planck texture, while the group's result there is the PILOT map. A reader of the dust-polarization page should see the PILOT measurement.

Data: Planck is local. I do not know whether the PILOT Q and U maps from Mangilli et al. 2019 are public; ask Dana or J.-Ph. Bernard. If they are not, draw only the published mean orientation as a labelled line with the citation and keep the Planck segments at beam spacing.

Sketch: a `pilot` layer in `scripts/composites.py` for the `galactic_centre` region, widened from 2 degrees to the PILOT footprint (-2 to 2 degrees in longitude). Reuse `MapFrame.astro` from proposal 2.

Effort: S for the line and honest Planck segments, M with PILOT maps.

Risk: medium. Planck toward the centre integrates the whole line of sight through the disc; the caption must say so.

### 8. A resolution ladder in place of the light ruler

What: reuse the log-axis component for physical scale. The axis runs from 0.01 pc to 10 kpc. Each of the group's data sets is a bar from its beam size to its map size at the target's distance: Planck at the LMC (5 arcmin is about 72 pc at 49.6 kpc), GASS at the LMC (16 arcmin, about 230 pc), GASKAP-HI (30 arcsec, about 7 pc, drawn dashed as work in progress), PILOT at the Galactic centre (2.2 arcmin, about 5 pc), Planck at Mon OB1 (7 arcmin, about 1.5 pc at 730 pc), JCMT POL-2 at G34.43 (14 arcsec, about 0.25 pc at 3.7 kpc), ALMA in Orion and NGC 253. Selecting a bar opens the paper.

Why: it answers "at what scales does this group measure the field" in one view and shows where the gaps are, which is useful for anyone planning a proposal with the group.

Data: beam sizes and distances from the papers and instrument documentation. The figures above are my arithmetic and each needs a citation before it ships.

Sketch: generalise `src/components/LightRuler.astro` to take an axis definition and bar items; data in a new `src/data/scales.ts` with bibcodes validated at build time like `graph.ts`. Whether it replaces the light ruler on the home page is Denis's call; it could also live on /research.

Effort: S to M.

Risk: low. Distances to infrared dark clouds are uncertain; show the adopted value.

### 9. The U-Net on real filaments

What: on /research/filaments, a Herschel 250 micron cutout with three overlays the reader can switch: the ridge filter the site already computes, the position angles returned by the group's U-Net (Umetaliev, Alina and Salmenova 2025), and the Planck field. A histogram of relative orientation updates with the selection.

Why: the page says the group trains networks to find filaments and shows no network output. The current "Filaments" layer is a generic Hessian filter, labelled honestly but not the group's method.

Data: Herschel cutouts are in `.cache/hips` (repo). The code release is on Zenodo, doi 10.5281/zenodo.16647869. I have not checked whether trained weights are included or what the licence is.

Sketch: run the model offline in a script and commit the output as an angle map; that is the simple route. If the weights are small, export to ONNX and run it in the browser with onnxruntime-web so the reader can drag the cutout around a larger Herschel field.

Effort: M offline, L in the browser.

Risk: medium. The model was trained on synthetic filaments; the authors should pick the region and approve the output.

### 10. Draw the field in the browser from Q and U

What: replace the baked line-integral-convolution images with a WebGL renderer that reads Stokes textures and draws the field live. Segment or streak length follows the smoothing scale, opacity follows signal to noise, and a control changes the smoothing from 7 arcmin to 1 degree so the reader sees the trade between resolution and noise. Slow motion along the streaks is allowed if it has no arrowheads and no net drift, because dust polarization gives an orientation and not a direction.

Why: it removes the false-sharpness problem, makes proposal 1 a smooth interpolation, and shows the uncertainty that the group's estimator papers are about. It would also improve the look of the site's main motif, since the streaks would no longer be finer than the data.

Data: Planck PR4 I, Q, U and covariances (local), written as float or 16-bit textures on the existing grids.

Sketch: `scripts/render_lmc.py` writes Q, U and a signal-to-noise map per region. A shared module `src/scripts/fieldgl.ts` implements LIC over a noise texture in a fragment shader, with a canvas 2D fallback that draws beam-spaced segments. Used by `FieldDots.astro`, `Archive.astro`, `PullBack.astro`.

Effort: L.

Risk: low scientifically if smoothing is done on Q and U and not on angles (the scripts already do this). Performance on phones needs the same care as the open item for the zoom.

### 11. Mon OB1: field and gas motions together

What: a result page for Alina et al. 2022. Planck field segments over the Herschel map, TRAO CO channel maps to scrub, the regions named in the paper outlined, and the field strengths and mass-to-flux ratios from the paper's table shown per region.

Why: it is a first-author paper with a clear story (two filaments that were once one, a shock between them, inflow along the field in the south) and the site already has the composite.

Data: Planck (local), Herschel (repo cache). Position-position-velocity cubes for G202.3+2.5 are public at VizieR J/A+A/631/A3 (Montillaud et al. 2019), already linked on the data page; fetch when CDS is back and confirm which telescope and lines they hold. Region outlines and numbers come from the paper.

Sketch: a `monoceros` section in `[id].astro` or its own page under /research/star-formation; reuse the cube viewer of proposal 5 and `MapFrame.astro`.

Effort: M.

Risk: low to medium; the cubes must be regridded with care and the numbers transcribed with their uncertainties.

### 12. Projects for students and visitors

What: a page listing open questions a student could work on, each with the data it uses, the method, the code repository (VGT.jl, ROHSA-LMC, the U-Net), and what exists already. Add what a student gets: the computing available and the collaborations the group belongs to.

Why: prospective students are a named audience and the site gives them only a contact line.

Data: content from Dana.

Sketch: a `openings` content collection and a page linked from the hero's "Join or visit".

Effort: S once the content exists.

Risk: none scientific. Needs Dana's sign-off on what is advertised.

### 13. How each image was made

What: every image gets a small "method" drawer listing bands and surveys with references, the stretch, the smoothing, the script and commit that produced it, and a link to download the derived map as FITS (for example the field angle on the 12 degree grid).

Why: it turns the pipeline care into something visible and reusable. Astronomers trust an image more when they can get the array.

Data: repo. `src/data/composites.json` already records the bands; extend the scripts to write the rest.

Sketch: part of the per-image JSON in proposal 2; FITS files under `public/data/` written by the render scripts. Check the size budget.

Effort: S to M.

Risk: low. Survey licences allow derived products with credit; list the credits in the FITS header.

### 14. Publications as a map of the work

What: on /publications, add filters by research line, instrument and role (first author, group-led, collaboration), a one-line result under each group-led paper, BibTeX export, and a split of the citation total into group-led work and large collaborations. Show the earlier stellar magnetism papers (Sirius, Vega) as their own short line, since they are part of the PI's path into magnetic fields.

Why: referees and collaborators use this page most. The current list is flat and the citation figure is easy to misread.

Data: repo (`src/data/publications.json`); add an `led` flag and the abstract through `scripts/fetch_publications.py`.

Sketch: client-side filtering in `src/pages/publications.astro`; BibTeX from the ADS export endpoint at fetch time.

Effort: S to M.

Risk: none.

### 15. Where the LMC is right now

What: extend the existing altitude readout into a small panel on the contact page: the LMC's altitude now at Astana and at the telescopes whose data the group uses (ASKAP, Parkes, ALMA, JCMT), on a strip that shows the next 24 hours.

Why: it explains in one glance why a group at 51 degrees north works on a southern galaxy with archival and remote data. It is a nice detail, not a science result.

Data: none; computed from coordinates and time.

Sketch: reuse the sidereal time code behind the frame readouts in the base layout.

Effort: S.

Risk: none, if site coordinates are right.

### 16. Sonified H I spectra

What: an optional audio mode in the cube viewer that plays the spectrum under the pointer, mapping velocity to pitch and brightness temperature to loudness.

Why: it helps accessibility and is pleasant, but it tells an astronomer little the plot does not. Lowest priority.

Data: local (GASS).

Sketch: Web Audio oscillator bank, off by default, with a visible control.

Effort: S after proposal 5.

Risk: none scientific.

## 3. Things that are wrong or misleading

1. LMC field directions are drawn against image-up instead of local north. `planck_maps` in `scripts/render_lmc.py` returns the angle east of local celestial north. `lic()` in the same file and the dash drawing in `src/components/FieldDots.astro` treat it as an angle from the image's vertical axis. The LMC grid is a tangent projection centred at declination -68.5 degrees and 12 degrees wide, so north is not up away from the central meridian. I computed the tilt from the GRID WCS: 0 at the centre, 3.3 degrees at 30 Doradus, 6.5 degrees at N11, 7.6 degrees halfway from the centre to the east or west edge, 15 degrees at the edges and 20 degrees in the south-east corner. The streaks and dashes are rotated by that amount relative to the structures in the image. The readout "B PA" is still right as a position angle. The fix is to add the local angle of north on the grid (from the WCS) before drawing. The same applies to `comp-lmc-field-*`: `composite()` in `scripts/composites.py` passes the output of `field_angle` straight to `rl.lic` with no north term. The Galactic-frame regions have the analogous effect; it is negligible for the 2 and 3 degree fields and a few degrees at the edges of the 24 degree Orion cutout.

2. "Milky Way foreground removed" is listed as coming soon in `src/content/projects/lmc.md`, and the LMC card carries a COMING SOON badge. Alina et al. 2023 (2023MNRAS.518.4466A) is about exactly this: its abstract describes separating the LMC signal from the Milky Way and reports the field geometry "after foreground removal". The 2026 IAU Symposium paper covers the same ground. If the card means a new, improved subtraction, it should say so.

3. The filaments paragraph in `src/content/projects/filaments.md` says filaments hosting Planck cold clumps "tend to run perpendicular to the field when they are dense and parallel to it when they are diffuse". The abstract of Alina et al. 2019 is more specific. In low column density environments only low-contrast filaments are parallel to the background field and high-contrast ones are randomly oriented. In high column density environments there is no global preference, though low-contrast filaments alone tend toward perpendicular. The clear change from mostly parallel to mostly perpendicular near n_H of 10^3 cm^-3 holds for a subsample of nearby filaments, in their off-clump portions. PLAN.md already lists this sentence as an open question; this is the evidence. Suggested copy: "In a nearby subsample, the parts of filaments away from clumps change from mostly parallel to the field to mostly perpendicular near a density of 10^3 cm^-3. Over the full sample the trend depends on the column density of the surroundings and on the contrast of the filament."

4. The research graph understates published links. In `src/data/graph.ts` the edge from H I to velocity gradients is dashed with no papers and the note "in progress". Both LMC papers apply velocity gradients to H I to get the foreground field direction, so there is a published edge (2023MNRAS.518.4466A, 2026IAUS..392..179A); the GASKAP work can stay dashed as a second edge. Mon OB1 has no edge to TRAO although Alina et al. 2022 combines Planck with TRAO CO, and no edge to velocity gradients although the abstract compares velocity and intensity gradients with the polarization.

5. The LMC project text presents H I velocity gradients as "a second view" of the LMC field. In the published work they were used for the Milky Way foreground. The premise itself (structure in thin velocity channels follows the field because of turbulent velocities) is debated in the literature, and Hu, Lazarian, Alina et al. 2023 is the group's contribution to that debate. The page should state the premise as the method's assumption and cite that paper next to it.

6. Velocity frame label. The GASS subcube header has `CTYPE3 = VOPT` and no `SPECSYS`. `VOPT` names the velocity convention, not the rest frame. GASS is distributed in the LSR frame, so the "v_LSR" label in `Hero.astro` is very likely right; confirm against the GASS documentation. At 270 km/s the optical and radio conventions differ by about 0.25 km/s, well below the 3.3 km/s frame spacing, so nothing on screen changes.

7. The Galactic centre card and the dust-polarization page head show a Planck field texture at 24 arcmin FWHM over a 2 degree field, with no beam shown, on the page whose result is the PILOT measurement at 2.2 arcmin. The caption is accurate ("Field: Planck 353 GHz") but the pairing invites the reader to take the texture for the PILOT result. See proposal 7.

8. No signal-to-noise mask on any field drawing. Around the LMC, outside the disc, the polarized signal at 353 GHz is weak and partly Milky Way. The texture is drawn with equal confidence everywhere on the 12 degree grid. I did not measure the signal to noise, so this is a risk to check and not a demonstrated error.

9. Light ruler labels collide at the right end: the "1 Gyr" tick label is drawn over "13.8 Gyr · age of the Universe" at 1440 px (`crop-ruler-end.png`, `src/components/LightRuler.astro`).

10. The publications header shows 1501 citations for 47 entries with the line "Everything published". 679 of those citations come from the three Planck Collaboration intermediate-results papers (442, 143 and 94), and the list is the ADS record of one author back to 2011, including stellar magnetism papers that are not ISM work. Not wrong, but a referee will notice. Split the figure or add a sentence.

11. The hero's canvas label says "with detected sources marked". The boxes are the brightest blobs in a press JPEG, as the log line admits. Change the label to match the log, or remove the boxes.

12. The data page links go to vizier.cds.unistra.fr, which returned "Page unavailable" today. That is an outage, but the DOI form of each catalogue link would be more durable.

Checked by computation or by reading the code, and found correct: the 12 degree field width in light years at 49.6 kpc, the LMC's Galactic latitude (-32.9 degrees), the live LST and LMC altitude readouts, the COSMO to IAU sign handling, the rotation from Galactic to celestial north, the 20 and 25 arcmin resolutions quoted for the two LMC field products, the unit conversions on the ruler from the distances cited in its source comments, and the statement that the LMC never rises over Astana.

Consistent with what I know but not independently verified today: the 340 light year width of the Webb frame (from the ESA release), the placement of 30 Doradus, N11, N44, N159 and N79 on the LMC map (their relative positions look right for north up and east left), and the position of the LMC on the all-sky map.
