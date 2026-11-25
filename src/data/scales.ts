// Resolution ladder: one bar per data set the group uses, from the beam to the
// map, converted to parsecs at the distance the cited paper adopted. Every
// number below was read from the paper named in its comment; a value derived
// here (not printed in the paper) says so. Bibcodes must exist in
// publications.json (ScaleLadder fails the build otherwise).
//
// Angles are in arcseconds. `dist` is in parsecs, or [near, far] when the
// paper's sample spans a range of distances (then the bar is drawn from the
// smallest beam to the largest map, with lighter end caps for the spread).

export interface Bar {
  id: string;
  /** Instrument or survey, shown as the row name. */
  name: string;
  /** Target and adopted distance, shown under the name. */
  target: string;
  /** Adopted distance in pc (one value or a range) and where it comes from. */
  dist: number | [number, number];
  distSrc: string;
  /** Beam FWHM in arcsec and what it refers to. */
  beam: number;
  beamNote: string;
  /** Map size in arcsec (largest dimension unless the note says otherwise). */
  size: number | [number, number];
  sizeNote: string;
  papers: string[];
  /** Work in progress: drawn dashed, labelled. */
  soon?: string;
  /** Extra caveat shown in the detail panel. */
  note?: string;
}

import facts, { GRID_DEG, kpcLabel } from "../lib/facts";

const AM = 60, DEG = 3600;
export const AS_PER_RAD = 206264.806;
const LMC_PC = facts.lmc.distance_pc;
const LMC_TARGET = `LMC · ${kpcLabel(LMC_PC)}`;
const MON_PC = facts.mon_ob1.cluster_distance_pc;
const PLANCK_BEAM = facts.planck.beam_arcmin * AM;

export const bars: Bar[] = [
  {
    // Saha et al. 2021 (2012.08737): ALMASOP, ALMA ACA+TM2 and TM1 at 1.3 mm.
    // Distance "~400 pc; Kounkel et al. 2018" (Sect. 2). Synthesized beams in
    // the paper run from 0.34" (TM1) to 5.5" (ACA); the substructure of
    // G205-M3 is shown at 0.8" (Fig. 2d, uv-taper), so 0.8" is the finest
    // beam the paper's results rest on. Map size is not printed: we use the
    // 7 m ACA primary beam FWHM at 1.3 mm, 1.13 lambda / D = 43", derived here.
    id: "alma-orion",
    name: "ALMA 1.3 mm",
    target: "Orion cores · 400 pc",
    dist: 400,
    distSrc: "Kounkel et al. 2018, as adopted by Saha et al. 2021",
    beam: 0.8,
    beamNote: "finest beam of the results (0.34 to 5.5 arcsec across the survey configurations)",
    size: 43,
    sizeNote: "one ACA primary beam (derived: 1.13 λ/D, D = 7 m, 1.3 mm); the paper gives no field size",
    papers: ["2021ApJ...907L..15S"],
  },
  {
    // Dewangan et al. 2026 (2605.14693): ALMAGAL 1.3 mm map, beam 0.39 x 0.34"
    // (Fig. 1d caption). Distance 2.5 kpc (Sect. 1). Analysed region: circle
    // of 30" radius that encloses the hub-filament system (Fig. 5b), so 60"
    // across. JWST NIRCam images cover the same field; the paper gives no
    // NIRCam beam, so the bar is the ALMA one.
    id: "alma-g286",
    name: "ALMA 1.3 mm + JWST",
    target: "G286.21+0.17 · 2.5 kpc",
    dist: 2500,
    distSrc: "Barnes et al. 2010, Zucker et al. 2020, Zhou et al. 2021, as adopted by Dewangan et al. 2026",
    beam: 0.39,
    beamNote: "ALMAGAL 1.3 mm beam, 0.39 × 0.34 arcsec (major axis)",
    size: 60,
    sizeNote: "diameter of the circle enclosing the hub-filament system",
    papers: ["2026MNRAS.552g1764D"],
    note: "The JWST NIRCam images of the same field are sharper than this beam; the paper does not state their resolution.",
  },
  {
    // Belfiori et al. 2025 (2503.03493), not Butterfield. D = 3.5 Mpc.
    // Band 7: beam 0.32 x 0.28" (5.4 x 4.8 pc), primary beam FWHM ~18".
    id: "alma-ngc253-b7",
    name: "ALMA Band 7 polarisation",
    target: "NGC 253 centre · 3.5 Mpc",
    dist: 3.5e6,
    distSrc: "Belfiori et al. 2025, Sect. 2",
    beam: 0.32,
    beamNote: "Band 7 (~345 GHz) beam, 0.32 × 0.28 arcsec (5.4 × 4.8 pc)",
    size: 18,
    sizeNote: "single-pointing primary beam FWHM, Band 7",
    papers: ["2025A&A...697A..24B"],
  },
  {
    // Same paper, Band 4: beam 1.54 x 1.33" (26.1 x 22.1 pc), primary beam ~42".
    id: "alma-ngc253-b4",
    name: "ALMA Band 4 polarisation",
    target: "NGC 253 centre · 3.5 Mpc",
    dist: 3.5e6,
    distSrc: "Belfiori et al. 2025, Sect. 2",
    beam: 1.54,
    beamNote: "Band 4 (~145 GHz) beam, 1.54 × 1.33 arcsec (26.1 × 22.1 pc)",
    size: 42,
    sizeNote: "single-pointing primary beam FWHM, Band 4",
    papers: ["2025A&A...697A..24B"],
  },
  {
    // Soam et al. 2019 (1908.03624): POL-2 850 um beam 14.1" (Sect. 2),
    // distance ~3.7 kpc (Sect. 1). The daisy scan gives a fully sampled
    // circle 11' across with good signal-to-noise over the central 3'.
    id: "jcmt-g34",
    name: "JCMT POL-2 850 µm",
    target: "G34.43+0.24 · 3.7 kpc",
    dist: 3700,
    distSrc: "Sanhueza et al. 2012, Foster et al. 2014, Xu et al. 2016, as adopted by Soam et al. 2019",
    beam: 14.1,
    beamNote: "JCMT 850 µm beam (14.1 arcsec)",
    size: 11 * AM,
    sizeNote: "diameter of the fully sampled daisy map (high signal-to-noise only in the central 3 arcmin)",
    papers: ["2019ApJ...883...95S"],
  },
  {
    // Vorster et al. 2026 (2605.21101, B-FROST): TRAO 12CO/13CO, beam 46-48",
    // 2.5 x 3 deg, MBM 12 at 252 +4 -6 +-12 pc (Zucker et al. 2019, Sect. 2).
    id: "trao-mbm12",
    name: "TRAO 12CO / 13CO",
    target: `MBM 12 · ${facts.mbm12.distance_pc} pc`,
    dist: facts.mbm12.distance_pc,
    distSrc: `${facts.mbm12.distance_ref}, as adopted by Vorster et al. 2026`,
    beam: 48,
    beamNote: "TRAO beam at 110 to 115 GHz (46 to 48 arcsec)",
    size: 3 * DEG,
    sizeNote: "long side of the 2.5 × 3 degree map",
    papers: ["2026A&A...711A.157V"],
  },
  {
    // Alina et al. 2022 (2007.15344): TRAO 13CO beam 47", 6 deg2 analysed in
    // the eastern part, at the distance Alina et al. adopted. Map size is
    // the side of a square of 6 deg2 (2.45 deg), derived here; the real
    // footprint is not square.
    id: "trao-mon",
    name: "TRAO 13CO",
    target: `Mon OB1 east · ${MON_PC} pc`,
    dist: MON_PC,
    distSrc: facts.mon_ob1.cluster_distance_ref,
    beam: 47,
    beamNote: "TRAO beam (47 arcsec)",
    size: Math.sqrt(6) * DEG,
    sizeNote: "side of a square of equal area to the 6 square degrees analysed (derived)",
    papers: ["2022A&A...658A..90A"],
  },
  {
    // Same paper: Planck 353 GHz smoothed from 5' to 7' ("70" in the text
    // extraction), "70 or 1.5 pc". Same 6 deg2 region.
    id: "planck-mon",
    name: "Planck 353 GHz",
    target: `Mon OB1 east · ${MON_PC} pc`,
    dist: MON_PC,
    distSrc: facts.mon_ob1.cluster_distance_ref,
    beam: 7 * AM,
    beamNote: "smoothed from the native 5 arcmin to 7 arcmin (1.5 pc in the paper)",
    size: Math.sqrt(6) * DEG,
    sizeNote: "side of a square of equal area to the 6 square degrees analysed (derived)",
    papers: ["2022A&A...658A..90A"],
  },
  {
    // Mangilli et al. 2019 (1901.06196): PILOT 240 um, 2.2'; Sun at 8.5 kpc
    // from Sgr A* (Sect. 1); polarization results for ~3.1 x 0.9 deg (Sect. 4).
    id: "pilot-gc",
    name: "PILOT 240 µm",
    target: "Galactic centre · 8.5 kpc",
    dist: 8500,
    distSrc: "adopted by Mangilli et al. 2019, Sect. 1",
    beam: 2.2 * AM,
    beamNote: "PILOT beam (2.2 arcmin)",
    size: 3.1 * DEG,
    sizeNote: "long side of the 3.1 × 0.9 degree field analysed",
    papers: ["2019A&A...630A..74M"],
  },
  {
    // Oers et al. 2026 (2606.04713): Herschel Galactic Cold Cores, 116 fields,
    // typical size 40', up to 1 deg, analysed at 36"; field distances 110 pc to
    // 3.8 kpc. Beam range 36" at 110 pc to 3.8 kpc; size range 40' at 110 pc
    // to 1 deg at 3.8 kpc.
    id: "herschel-gcc",
    name: "Herschel PACS + SPIRE",
    target: "Cold Cores fields · 110 pc to 3.8 kpc",
    dist: [110, 3800],
    distSrc: "range of the 116 fields in Oers et al. 2026",
    beam: 36,
    beamNote: "36 arcsec, the resolution of the column density maps (SPIRE 500 µm beam)",
    size: [40 * AM, 1 * DEG],
    sizeNote: "typical field 40 arcmin, up to 1 degree",
    papers: ["2026A&A...711A..97O"],
    note: "One survey, many distances: the lighter ends of the bar show the spread from the nearest to the farthest field.",
  },
  {
    // Alina et al. 2023 (2205.01275): GASS H I, 16.2' effective resolution
    // (Sect. 2.1). Region: mask built on a circle of 5 deg radius around the
    // LMC centre (Sect. 5). The site's LMC distance (the paper quotes 200 pc
    // for 16', which would need 43 kpc; the note below gives the value here).
    id: "gass-lmc",
    name: "GASS H I 21 cm",
    target: LMC_TARGET,
    dist: LMC_PC,
    distSrc: `${facts.lmc.distance_ref} (the site's adopted LMC distance)`,
    beam: 16.2 * AM,
    beamNote: "GASS effective resolution (16.2 arcmin)",
    size: 10 * DEG,
    sizeNote: "diameter of the 5 degree radius circle used for the analysis",
    papers: ["2023MNRAS.518.4466A", "2026IAUS..392..179A"],
    note: `Alina et al. 2023 state 200 pc for 16 arcmin; at ${kpcLabel(LMC_PC, 2)} it is ${Math.round((16.2 * AM / AS_PER_RAD) * LMC_PC)} pc.`,
  },
  {
    // Same paper: Planck 353 GHz at nominal ~5' ("nominal angular resolution
    // (~5 arcmin)"); the beam is the site's Planck effective beam (facts.json).
    id: "planck-lmc",
    name: "Planck 353 GHz, native",
    target: LMC_TARGET,
    dist: LMC_PC,
    distSrc: facts.lmc.distance_ref,
    beam: PLANCK_BEAM,
    beamNote: "native Planck HFI beam at 353 GHz (about 5 arcmin)",
    size: 10 * DEG,
    sizeNote: "diameter of the 5 degree radius circle used for the analysis",
    papers: ["2023MNRAS.518.4466A"],
  },
  {
    // scripts/render_lmc.py planck_maps(): Gaussian sigma = 12 pixels of the
    // sigma = 12 pixels of the output grid; combined with the native beam in
    // quadrature.
    id: "planck-lmc-site",
    name: "Planck 353 GHz, as drawn here",
    target: LMC_TARGET,
    dist: LMC_PC,
    distSrc: facts.lmc.distance_ref,
    beam: Math.hypot(2.3548 * 12 * facts.grid.cdelt_deg * DEG, PLANCK_BEAM),
    beamNote: `smoothing of the maps on this site (Gaussian σ = 12 pixels of ${Math.round(facts.grid.cdelt_deg * DEG)} arcsec) combined with the native beam, in quadrature`,
    size: GRID_DEG * DEG,
    sizeNote: "width of the image grid used on this site",
    papers: [],
    note: "Derived from the site's own render script, not from a paper.",
  },
  {
    // GASKAP-HI LMC: 30" beam, as stated in src/content/projects/lmc.md.
    // The survey footprint is not published here, so the map size is set to the
    // same 10 deg LMC field as the other LMC bars (an assumption).
    id: "gaskap-lmc",
    name: "GASKAP-HI 21 cm",
    target: LMC_TARGET,
    dist: LMC_PC,
    distSrc: facts.lmc.distance_ref,
    beam: 30,
    beamNote: "ASKAP 30 arcsec beam, as quoted on the LMC project page",
    size: 10 * DEG,
    sizeNote: "assumed to match the 10 degree LMC field of the other LMC bars",
    papers: ["2024IAUGA..32P.103A"],
    soon: "In progress: our analysis of GASKAP-HI is not published yet",
  },
];
