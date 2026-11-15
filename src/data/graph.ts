// Map of the work: regions, the data behind them, and the methods. Every
// solid edge cites ADS bibcodes that must exist in publications.json (the
// build fails otherwise). An edge is only drawn when the paper itself
// supports it; proposals and work in progress are dashed.
export type Kind = "region" | "data" | "method";
export interface GNode { id: string; l: string; k: Kind; href?: string }
export interface GEdge { a: string; b: string; papers: string[]; soon?: string }

export const nodes: GNode[] = [
  { id: "lmc", l: "LMC", k: "region", href: "/research/lmc" },
  { id: "gc", l: "Galactic Centre", k: "region", href: "/research/dust-polarization" },
  { id: "orion", l: "Orion", k: "region", href: "/research/star-formation" },
  { id: "mon", l: "Mon OB1", k: "region", href: "/research/star-formation" },
  { id: "g286", l: "G286.21+0.17", k: "region", href: "/research/star-formation" },
  { id: "g34", l: "G34.43+0.24", k: "region", href: "/research/star-formation" },
  { id: "ngc253", l: "NGC 253", k: "region", href: "/research/star-formation" },
  { id: "mbm", l: "MBM 12", k: "region", href: "/research/star-formation" },
  { id: "planck", l: "Planck 353 GHz", k: "data" },
  { id: "hi", l: "H I 21 cm", k: "data" },
  { id: "pilot", l: "PILOT", k: "data" },
  { id: "alma", l: "ALMA", k: "data" },
  { id: "jwst", l: "JWST", k: "data" },
  { id: "jcmt", l: "JCMT POL-2", k: "data" },
  { id: "trao", l: "TRAO", k: "data" },
  { id: "herschel", l: "Herschel", k: "data" },
  { id: "hro", l: "Relative orientation", k: "method", href: "/research/filaments" },
  { id: "ml", l: "Filament ML", k: "method", href: "/research/filaments" },
  { id: "estim", l: "Polarization estimators", k: "method", href: "/research/dust-polarization" },
  { id: "vgt", l: "Velocity gradients", k: "method", href: "/research/lmc" },
  { id: "gauss", l: "Gaussian decomposition", k: "method", href: "/research/lmc" },
];

export const edges: GEdge[] = [
  { a: "lmc", b: "planck", papers: ["2023MNRAS.518.4466A", "2026IAUS..392..179A"] },
  { a: "lmc", b: "hi", papers: ["2026IAUS..392..179A", "2024IAUGA..32P.103A"] },
  { a: "gc", b: "pilot", papers: ["2019A&A...630A..74M"] },
  { a: "orion", b: "alma", papers: ["2021ApJ...907L..15S"] },
  { a: "orion", b: "jwst", papers: ["2025jwst.prop.7433J"], soon: "Accepted JWST Cycle 4 proposal" },
  { a: "mon", b: "planck", papers: ["2022A&A...658A..90A"] },
  { a: "mon", b: "trao", papers: ["2022A&A...658A..90A"] },
  { a: "g286", b: "jwst", papers: ["2026MNRAS.552g1764D"] },
  { a: "g286", b: "alma", papers: ["2026MNRAS.552g1764D"] },
  { a: "g34", b: "jcmt", papers: ["2019ApJ...883...95S"] },
  { a: "ngc253", b: "alma", papers: ["2025A&A...697A..24B"] },
  { a: "mbm", b: "trao", papers: ["2026A&A...711A.157V"] },
  { a: "planck", b: "hro", papers: ["2019MNRAS.485.2825A", "2026A&A...711A..97O"] },
  { a: "herschel", b: "hro", papers: ["2026A&A...711A..97O"] },
  // MaLeFiSenta trained on Planck, Herschel and HI4PI maps; the U-Net paper
  // trained on synthetic images and was tested on Planck data.
  { a: "planck", b: "ml", papers: ["2022arXiv220500683A", "2025AJ....170..207U"] },
  { a: "herschel", b: "ml", papers: ["2022arXiv220500683A"] },
  { a: "hi", b: "ml", papers: ["2022arXiv220500683A"] },
  { a: "hi", b: "vgt", papers: ["2023MNRAS.518.4466A", "2026IAUS..392..179A", "2024IAUGA..32P.103A"] },
  // Mon OB1: velocity and intensity gradients of TRAO CO compared with Planck.
  { a: "trao", b: "vgt", papers: ["2022A&A...658A..90A"] },
  { a: "hi", b: "gauss", papers: [], soon: "In progress: the cold neutral medium separated by Gaussian decomposition (ROHSA)" },
];

// Method papers that do not tie to one instrument in their title.
export const nodePapers: Record<string, string[]> = {
  ml: ["2025zndo..16647869U"],
  estim: ["2015A&A...574A.135M", "2015A&A...574A.136M", "2016A&A...595A..57A"],
};
