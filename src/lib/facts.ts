// Facts the site shares with scripts/*.py. The values live in src/data/facts.json,
// which the render scripts read too; derived quantities are computed here.
import facts from "../data/facts.json";

export default facts;

/** Width of the equatorial TAN grid every LMC map is drawn on, degrees. */
export const GRID_DEG = facts.grid.naxis * facts.grid.cdelt_deg;
export const GRID_ARCMIN = GRID_DEG * 60;

/** Width and height of the all-sky Mollweide image, pixels. */
export const ALLSKY_W = facts.allsky_width_px;
export const ALLSKY_H = ALLSKY_W / 2;

export const LY_PER_PC = 3.26156;
export const pcToLy = (pc: number) => pc * LY_PER_PC;

/** The grid's width at the LMC distance, light-years. */
export const LY_PER_GRID = pcToLy(((GRID_DEG * Math.PI) / 180) * facts.lmc.distance_pc);

/** Round to `sig` significant figures. */
export const roundSig = (x: number, sig: number) => {
  const p = 10 ** (Math.floor(Math.log10(Math.abs(x))) + 1 - sig);
  return Math.round(x / p) * p;
};

/** Light-years rounded to `sig` figures, as "162 000". */
export const lyLabel = (ly: number, sig: number) => roundSig(ly, sig).toLocaleString("en-US").replace(/,/g, " ");

/** "49.6 kpc" style label for a distance in parsecs. */
export const kpcLabel = (pc: number, digits = 1) => `${(pc / 1000).toFixed(digits)} kpc`;
