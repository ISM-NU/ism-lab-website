// Extra sections on a research page, keyed by project id (the file name in
// src/content/projects). They render in this order after Results and before
// "In progress". To add one, append an entry here; the page needs no edit.
// The research page throws if a key here is not a project id.
import type { AstroComponentFactory } from "astro/runtime/server/index.js";
import AssyMap from "../components/AssyMap.astro";
import LayerLens from "../components/LayerLens.astro";
import CubeViewer from "../components/CubeViewer.astro";
import FieldGL from "../components/FieldGL.astro";
import ForegroundWipe from "../components/ForegroundWipe.astro";
import FilamentNet from "../components/FilamentNet.astro";
import OrientationExplorer from "../components/OrientationExplorer.astro";
import EstimatorBench from "../components/EstimatorBench.astro";
import MonOB1 from "../components/MonOB1.astro";
import GalacticCentre from "../components/GalacticCentre.astro";
import { flags } from "./flags";

export interface ResearchSection {
  /** Prefix of the heading id, so the section is labelled by `${id}-h`. */
  id: string;
  title: string;
  intro: string;
  Body: AstroComponentFactory;
  props?: Record<string, unknown>;
  /** Inline style of a div around the body. */
  bodyStyle?: string;
  /** False while the feature waits for approval (src/data/flags.ts). */
  enabled?: boolean;
}

export const researchSections: Record<string, ResearchSection[]> = {
  "optical-polarimetry": [
    { id: "assy", title: "Assy-Turgen Observatory", intro: "The observatory is about 1000 km south-east of Nazarbayev University in Astana.", Body: AssyMap },
  ],
  lmc: [
    { id: "lens", title: "Survey layers of the LMC", intro: "Every layer below is public survey data on one 12° grid.", Body: LayerLens },
    {
      id: "cube",
      title: "H I spectra across the LMC",
      intro: "Move over the map to see the 21 cm spectrum there. Drag on the spectrum to choose a velocity window. Move the red cut to see the rotation of the disc.",
      Body: CubeViewer,
    },
    {
      id: "res",
      title: "Resolution and noise",
      intro: "The field drawn live from Planck Q and U.",
      Body: FieldGL,
      props: { view: "observed", scale: 15 },
      bodyStyle: "max-width:760px;margin-top: 32px",
    },
    {
      id: "fg",
      title: "Milky Way foreground subtraction",
      intro: "Left of the handle, the Planck field as observed. Right of it, the same data after subtracting the Milky Way foreground.",
      Body: ForegroundWipe,
      enabled: flags.foregroundWipe,
    },
  ],
  filaments: [
    {
      id: "fn",
      title: "U-Net filament detection in Mon OB1",
      intro: "Our network run on Herschel 250 µm in Mon OB1, with the Planck field for comparison.",
      Body: FilamentNet,
      props: { preview: true },
    },
    {
      id: "or",
      title: "Filament orientation relative to the field",
      intro: "The public catalogue of Alina et al. 2019: 138 Planck filaments, 93 with a field angle.",
      Body: OrientationExplorer,
    },
  ],
  "dust-polarization": [
    {
      id: "bench",
      title: "Bias at low signal to noise",
      intro: "Noise biases the polarization fraction and the angle dispersion function. Compare the estimators we have studied.",
      Body: EstimatorBench,
    },
    { id: "gc", title: "The Galactic centre", intro: "Planck at 5′ against the mean orientation from PILOT at 2.2′.", Body: GalacticCentre },
  ],
  "star-formation": [
    {
      id: "mon",
      title: "Monoceros OB1 East",
      intro: "The Planck field over the cloud and the regions where Alina et al. 2022 measured its strength and traced the gas motions.",
      Body: MonOB1,
    },
  ],
};
