// The JSON the Python scripts write into src/data/, parsed once at import.
// A file that no longer matches its schema (src/lib/schemas.ts) fails the build.
// Server side only: a client <script> that imports this pulls zod into the
// bundle. Scripts import the JSON file itself and take the type from here.
import { parseJson, publicationsSchema, mapsSchema, orientationsSchema, benchPatchSchema, stokesSchema, skySchema, monOb1Schema, gcFieldSchema, unetSchema, cubeSchema, assyMapSchema, compositesSchema, detectionsSchema, zoomInsetsSchema } from "./schemas";
import rawPublications from "../data/publications.json";
import rawMaps from "../data/maps.json";
import rawOrientations from "../data/orientations.json";
import rawBenchPatch from "../data/bench_patch.json";
import rawStokes from "../data/stokes.json";
import rawSky from "../data/sky.json";
import rawMonOb1 from "../data/mon-ob1.json";
import rawGcField from "../data/gc-field.json";
import rawUnet from "../data/unet.json";
import rawCube from "../data/cube.json";
import rawAssyMap from "../data/assy-map.json";
import rawComposites from "../data/composites.json";
import rawDetections from "../data/detections.json";
import rawZoomInsets from "../data/zoom-insets.json";

export const publications = parseJson("publications.json", publicationsSchema, rawPublications);
export const maps = parseJson("maps.json", mapsSchema, rawMaps);
export const orientations = parseJson("orientations.json", orientationsSchema, rawOrientations);
export const benchPatch = parseJson("bench_patch.json", benchPatchSchema, rawBenchPatch);
export const stokes = parseJson("stokes.json", stokesSchema, rawStokes);
export const sky = parseJson("sky.json", skySchema, rawSky);
export const monOb1 = parseJson("mon-ob1.json", monOb1Schema, rawMonOb1);
export const gcField = parseJson("gc-field.json", gcFieldSchema, rawGcField);
export const unet = parseJson("unet.json", unetSchema, rawUnet);
export const cube = parseJson("cube.json", cubeSchema, rawCube);
export const assyMap = parseJson("assy-map.json", assyMapSchema, rawAssyMap);
export const composites = parseJson("composites.json", compositesSchema, rawComposites);
// Only client scripts read these two; parsing them here keeps them under the same check.
export const detections = parseJson("detections.json", detectionsSchema, rawDetections);
export const zoomInsets = parseJson("zoom-insets.json", zoomInsetsSchema, rawZoomInsets);
