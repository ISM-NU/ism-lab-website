// Run: node --test src/lib/schemas.test.mjs
// The generated JSON in src/data must match the shapes the site reads, and a file
// that does not must stop the build with an error that names the file and the field.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as S from "./schemas.ts";

const FILES = {
  "publications.json": S.publicationsSchema,
  "maps.json": S.mapsSchema,
  "orientations.json": S.orientationsSchema,
  "bench_patch.json": S.benchPatchSchema,
  "stokes.json": S.stokesSchema,
  "sky.json": S.skySchema,
  "mon-ob1.json": S.monOb1Schema,
  "gc-field.json": S.gcFieldSchema,
  "unet.json": S.unetSchema,
  "cube.json": S.cubeSchema,
  "assy-map.json": S.assyMapSchema,
  "composites.json": S.compositesSchema,
  "detections.json": S.detectionsSchema,
  "zoom-insets.json": S.zoomInsetsSchema,
};
const load = (name) => JSON.parse(readFileSync(new URL(`../data/${name}`, import.meta.url), "utf8"));
const parse = (name, raw) => S.parseJson(name, FILES[name], raw);

for (const name of Object.keys(FILES)) {
  test(`${name} as committed matches its schema`, () => {
    parse(name, load(name));
  });
}

test("a field of the wrong type fails with the file and the field path", () => {
  const cube = load("cube.json");
  cube.nv = "192";
  assert.throws(() => parse("cube.json", cube), (e) => e.message.includes("cube.json") && e.message.includes("nv"));
});

test("a missing field fails", () => {
  const sky = load("sky.json");
  delete sky.lmc_targets;
  assert.throws(() => parse("sky.json", sky), /lmc_targets/);
});

test("a paper role other than first, led or collab is rejected", () => {
  for (const role of ["first", "led", "collab"]) {
    const d = load("publications.json");
    d.papers[0].role = role;
    assert.equal(parse("publications.json", d).papers[0].role, role);
  }
  const d = load("publications.json");
  d.papers[0].role = "senior";
  assert.throws(() => parse("publications.json", d), (e) => e.message.includes("papers[0].role"));
});

test("a paper may lack a DOI, arXiv id, volume and page", () => {
  const d = load("publications.json");
  Object.assign(d.papers[0], { doi: null, arxiv: null, volume: null, page: null, alina_index: null });
  parse("publications.json", d);
});

test("two papers with one bibcode are rejected", () => {
  const d = load("publications.json");
  d.papers[1].bibcode = d.papers[0].bibcode;
  assert.throws(() => parse("publications.json", d), /duplicate bibcode/);
});

test("maps.json: an image that names a frame, S/N entry or reference that is not defined is rejected", () => {
  const frame = load("maps.json");
  frame.images["comp-lmc"].frame = "nowhere";
  assert.throws(() => parse("maps.json", frame), (e) => e.message.includes(`images["comp-lmc"].frame`) && e.message.includes("nowhere"));

  const snr = load("maps.json");
  snr.images["lmc-bfield"].snr = "nope";
  assert.throws(() => parse("maps.json", snr), /nope/);

  const ref = load("maps.json");
  ref.images["comp-lmc"].bands[0].ref = "nobody2099";
  assert.throws(() => parse("maps.json", ref), /nobody2099/);
});

test("orientations.json: rows are positional, so a reordered column is rejected", () => {
  const d = load("orientations.json");
  [d.columns[1], d.columns[2]] = [d.columns[2], d.columns[1]];
  assert.throws(() => parse("orientations.json", d), /columns/);
});

test("orientations.json: a row with a missing value is rejected", () => {
  const d = load("orientations.json");
  d.rows[0] = d.rows[0].slice(0, 10);
  assert.throws(() => parse("orientations.json", d), /rows/);
});

test("bench_patch.json: arrays must hold n by n values", () => {
  const d = load("bench_patch.json");
  d.q.pop();
  assert.throws(() => parse("bench_patch.json", d), /n by n/);
});

test("stokes.json: a plane without a file is rejected", () => {
  const d = load("stokes.json");
  delete d.planes.I.file;
  assert.throws(() => parse("stokes.json", d), /planes\.I\.file/);
});
