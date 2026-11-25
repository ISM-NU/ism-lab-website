// Drawing helpers shared by the Planck field-segment figures (GalacticCentre,
// MonOB1). Positions are in the 1000 x 1000 viewBox the figures draw in.

/** SVG path for a segment of half-length `h` centred on (x, y). `deg` is the angle from up, counter-clockwise on screen. */
export const segPath = (x: number, y: number, deg: number, h: number) => {
  const r = (deg * Math.PI) / 180, dx = -Math.sin(r) * h, dy = -Math.cos(r) * h;
  return `M${(x - dx).toFixed(1)},${(y - dy).toFixed(1)}L${(x + dx).toFixed(1)},${(y + dy).toFixed(1)}`;
};

/** Length of a `pc` parsec bar at `distPc`, as a fraction of a frame `fovDeg` wide. */
export const barFraction = (pc: number, distPc: number, fovDeg: number) =>
  (pc / distPc) * (180 / Math.PI) / fovDeg;
