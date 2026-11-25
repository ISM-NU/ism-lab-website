// Shapes of the JSON files in src/data/ that the Python scripts write.
// src/lib/data.ts parses each file against its schema once, at import, so a
// generator that changes a field fails the build with the file and field named.
// Types are derived from these schemas. Keep key order the same as in the
// files: some components serialise a parsed object back into the page.
//
// This module imports only zod, so the tests can load it without the JSON.
import { z } from "astro/zod";

/** Parse `raw` (the content of `name`) or throw an error that names the file and each bad field. */
export function parseJson<S extends z.ZodType>(name: string, schema: S, raw: unknown): z.output<S> {
  const r = schema.safeParse(raw);
  if (r.success) return r.data;
  throw new Error(`src/data/${name} does not match its schema (scripts/ wrote a shape the site does not read):\n${z.prettifyError(r.error)}`);
}

const num = z.number();
const int = z.number().int();
const pair = z.tuple([num, num]);
const nums = z.array(num);
/** A square grid stored row by row. */
const grid = (n: number) => (a: unknown[]) => a.length === n * n;

// publications.json (scripts/fetch_publications.py)

export const ROLES = ["first", "led", "collab"] as const;
/** first: a group member is first author; led: a member is last author; collab: everything else. */
export const roleSchema = z.enum(ROLES);

export const paperSchema = z.object({
  bibcode: z.string(),
  title: z.string(),
  authors: z.array(z.string()),
  // Aligned with authors; "-" or "" when ADS has no affiliation or ORCID.
  aff: z.array(z.string()),
  orcid: z.array(z.string().nullable()),
  alina_index: int.nullable(),
  members: z.array(int),
  year: int,
  pub: z.string(),
  volume: z.string().nullable(),
  page: z.string().nullable(),
  doi: z.string().nullable(),
  arxiv: z.string().nullable(),
  citations: int,
  group: z.string(),
  doctype: z.string().nullable(),
  led: z.boolean(),
  role: roleSchema,
  abstract: z.string(),
  bibtex: z.string(),
});

export const publicationsSchema = z
  .object({
    query: z.string(),
    groups: z.array(z.string()),
    papers: z.array(paperSchema),
  })
  .superRefine((d, ctx) => {
    const seen = new Set<string>();
    d.papers.forEach((p, i) => {
      if (seen.has(p.bibcode)) ctx.addIssue({ code: "custom", path: ["papers", i, "bibcode"], message: `duplicate bibcode ${p.bibcode}` });
      seen.add(p.bibcode);
      if (p.aff.length !== p.authors.length) ctx.addIssue({ code: "custom", path: ["papers", i, "aff"], message: `${p.bibcode}: ${p.aff.length} affiliations for ${p.authors.length} authors` });
      if (p.orcid.length !== p.authors.length) ctx.addIssue({ code: "custom", path: ["papers", i, "orcid"], message: `${p.bibcode}: ${p.orcid.length} ORCIDs for ${p.authors.length} authors` });
      if (p.members.some((m) => m >= p.authors.length)) ctx.addIssue({ code: "custom", path: ["papers", i, "members"], message: `${p.bibcode}: member index beyond the author list` });
      if (!d.groups.includes(p.group)) ctx.addIssue({ code: "custom", path: ["papers", i, "group"], message: `${p.bibcode}: group "${p.group}" is not in groups` });
    });
  });

// maps.json (scripts/map_meta.py)

const tiltSchema = z.object({ k: int, deg: z.array(nums) }).refine((t) => t.deg.length === t.k && t.deg.every((r) => r.length === t.k), { message: "deg must be k by k" });

const frameSchema = z.object({
  frame: z.enum(["icrs", "galactic"]),
  fov_deg: num,
  centre: pair,
  dist_pc: num,
  dist_ref: z.string(),
  dist_text: z.string(),
  name: z.string(),
  tilt: tiltSchema,
});

const colourBarSchema = z.object({
  label: z.string(),
  unit: z.string(),
  lo: num,
  hi: num,
  ticks: nums,
  colors: z.array(z.string()).min(2),
  note: z.string(),
});

const mapImageSchema = z.object({
  frame: z.string(),
  title: z.string(),
  script: z.string(),
  stretch: z.string(),
  smoothing: z.string(),
  bands: z.array(z.object({ name: z.string(), fwhm_arcsec: num, ref: z.string(), note: z.string() })),
  beams: z.array(z.object({ label: z.string(), arcmin: num, layer: z.string() })),
  bar: colourBarSchema.nullable(),
  fits: z.array(z.object({ href: z.string(), bytes: num, what: z.string() })),
  snr: z.string().nullable(),
  native_px: int,
  note: z.string(),
});

export const mapsSchema = z
  .object({
    commit: z.string(),
    refs: z.record(z.string(), z.object({ label: z.string(), bib: z.string() })),
    frames: z.record(z.string(), frameSchema),
    images: z.record(z.string(), mapImageSchema),
    snr_stats: z.record(z.string(), z.object({ sigma_arcmin: num, fwhm_arcmin: num, frac_gt3: num, median: num, frac_gt3_within_4deg: num.optional() })),
    snr: z.object({ n: int, scale: int, min: num, grid: z.array(int) }).refine((s) => grid(s.n)(s.grid), { message: "grid must hold n by n values" }),
  })
  .superRefine((d, ctx) => {
    const need = (ok: boolean, path: (string | number)[], what: string, key: string) => {
      if (!ok) ctx.addIssue({ code: "custom", path, message: `${what} "${key}" is not defined in this file` });
    };
    for (const [k, f] of Object.entries(d.frames)) need(f.dist_ref in d.refs, ["frames", k, "dist_ref"], "reference", f.dist_ref);
    for (const [k, im] of Object.entries(d.images)) {
      need(im.frame in d.frames, ["images", k, "frame"], "frame", im.frame);
      if (im.snr !== null) need(im.snr in d.snr_stats, ["images", k, "snr"], "S/N entry", im.snr);
      im.bands.forEach((b, i) => need(b.ref in d.refs, ["images", k, "bands", i, "ref"], "reference", b.ref));
    }
  });

// orientations.json (scripts/fetch_catalogues.py)

const ORIENTATION_COLUMNS = "id,l,b,len,wid,pa,nh,nhfil,psi1,psi2,sig";

/** One filament of the Alina et al. 2019 catalogue, in the order of the `columns` field. psi1, psi2 and sig are null without a field angle. */
export const orientationRowSchema = z.tuple([int, num, num, num, num, num, num, num, num.nullable(), num.nullable(), num.nullable()]);

export const orientationsSchema = z.object({
  source: z.object({ paper: z.string(), bibcode: z.string(), arxiv: z.string(), vizier: z.string(), fetched_from: z.string() }),
  // The rows are positional, so a reordered column must stop the build.
  columns: z.array(z.string()).refine((c) => c.join() === ORIENTATION_COLUMNS, { message: `columns must be ${ORIENTATION_COLUMNS}` }),
  rows: z.array(orientationRowSchema),
  // paper and table are numbers or ranges such as "6 to 73".
  checks: z.array(z.object({ label: z.string(), paper: z.union([num, z.string()]), table: z.union([num, z.string()]), agree: z.boolean() })),
});

// bench_patch.json (scripts/render_bench.py)

export const benchPatchSchema = z
  .object({
    source: z.string(),
    unit: z.string(),
    fwhm_arcmin: num,
    beam_arcmin: num,
    resolution_arcmin: num,
    center: pair,
    size_deg: num,
    pix_arcmin: num,
    n: int,
    rows: z.string(),
    q: nums,
    u: nums,
    qq: nums,
    uu: nums,
    qu: nums,
  })
  .refine((p) => [p.q, p.u, p.qq, p.uu, p.qu].every(grid(p.n)), { message: "q, u, qq, uu and qu must each hold n by n values" });

// stokes.json (scripts/render_stokes.py). Only what the site reads; `validation` holds many more numbers.

const stokesPlaneSchema = z.object({ file: z.string(), n: int, lo: num, hi: num });
const starSchema = z.object({ cat: z.string(), x: num, y: num, pa: num, grid: num, p: num, spa: num, d: num, used: z.boolean() });

export const stokesSchema = z.looseObject({
  about: z.string(),
  beam_arcmin: num,
  scales_arcmin: nums,
  planes: z.record(z.string(), stokesPlaneSchema),
  i_stretch: z.object({ lo: num, hi: num, asinh: num }),
  zero_level_MJy_sr: num,
  foreground: z.looseObject({
    p_fg: num,
    psi_fg_grid_deg: num,
    b_fg_pa_deg_centre: num,
    sigma2_per_Ifg: z.record(z.string(), num),
  }),
  stars: z.array(starSchema),
  star_mean_pa_deg: num,
  star_count_used: int,
  hi_contours: z.looseObject({
    levels_K_kms: nums,
    paths: z.record(z.string(), z.array(z.string())),
    viewbox: int,
  }),
  validation: z.looseObject({ site_grid: z.looseObject({ I_med: num, I_fg_mean_in_mask: num }) }),
});

// sky.json (scripts/render_lmc.py)

export const skySchema = z
  .object({
    field_n: int,
    field: nums,
    tilt_n: int,
    north_tilt: nums,
    lmc_in_allsky: pair,
    lmc_rot_deg: num,
    hi_spectrum: nums,
    hi_range_kms: pair,
    lmc_targets: z.record(z.string(), pair),
    sources: z.object({ hi: z.string(), co: z.string(), dust_bfield: z.string() }),
  })
  .refine((s) => grid(s.field_n)(s.field) && grid(s.tilt_n)(s.north_tilt), { message: "field and north_tilt must be square grids of field_n and tilt_n" });

// The other generated files

const segmentSchema = z.object({ x: num, y: num, a: num, pa_gal: num, pa_eq: num, sig: num });

export const monOb1Schema = z.object({
  image: z.string(),
  image_small: z.string(),
  fov_deg: num,
  centre_gal: pair,
  fwhm_arcmin: num,
  beam_r: num,
  seg_len: num,
  dist_pc: num,
  compass: z.object({ N: pair, E: pair }),
  segments: z.array(segmentSchema),
  regions: z.array(
    z.object({
      id: z.string(),
      points: z.array(pair),
      name: z.string(),
      // Table 1 columns; only the regions the paper measured have them.
      ratio: z.string().optional(),
      b: z.string().optional(),
      lam: z.string().optional(),
      pa_eq_mean: num,
      n_seg: int,
    }),
  ),
  ngc2264: pair,
});

export const gcFieldSchema = z.object({
  image: z.string(),
  image_small: z.string(),
  fov_deg: num,
  fwhm_arcmin: num,
  beam_r: num,
  seg_len: num,
  dist_pc: num,
  pilot: z.object({ tilt: num, a: num, centre: pair }),
  planck_mean_tilt: num,
  segments: z.array(segmentSchema),
});

export const unetSchema = z.object({
  region: z.string(),
  centre_gal: pair,
  size_px: int,
  pixel_arcsec: num,
  width_deg: num,
  beam_arcmin: num,
  smooth_fwhm_arcmin: num,
  tophat_px: int,
  otsu: num,
  mask_fraction: num,
  n_pixels: int,
  n_regions: int,
  hist_all: z.array(int),
  bin_deg: int,
  median_rel_deg: num,
  calibration: z.array(z.tuple([int, num])),
  field: z.array(z.tuple([num, num, num])),
  segments: z.array(z.tuple([num, num, num, num, num])),
});

export const cubeSchema = z.object({
  n: int,
  nv: int,
  v0: num,
  dv: num,
  step: num,
  pix_deg: num,
  crval: pair,
  crpix: num,
  beam_arcmin: num,
  d_kpc: num,
  bytes_gz: int,
  tb_max: num,
  noise_k: num,
  peak_v_kms: num,
  mass_msun: num,
  gal_l_range: pair,
  gal_b_range: pair,
});

export const assyMapSchema = z.object({
  width: int,
  height: int,
  path: z.string(),
  points: z.object({ assy: z.object({ x: num, y: num }), astana: z.object({ x: num, y: num }), almaty: z.object({ x: num, y: num }) }),
});

export const compositesSchema = z.object({
  galactic_centre: z.array(z.string()),
  lmc: z.array(z.string()),
  monoceros_ob1: z.array(z.string()),
});

export const detectionsSchema = z.record(
  z.string(),
  z.object({ aspect: num, src: z.array(z.tuple([num, num, num, num])), core: pair, release: z.string() }),
);

export const zoomInsetsSchema = z.array(z.object({ src: z.string(), x: num, y: num, w: num }));

export type Paper = z.infer<typeof paperSchema>;
export type Role = z.infer<typeof roleSchema>;
export type Cube = z.infer<typeof cubeSchema>;
export type Maps = z.infer<typeof mapsSchema>;
export type MapImage = z.infer<typeof mapImageSchema>;
export type MapFrameMeta = z.infer<typeof frameSchema>;
export type OrientationRow = z.infer<typeof orientationRowSchema>;
export type BenchPatch = z.infer<typeof benchPatchSchema>;
