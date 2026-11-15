// Shared by MapFrame.astro (build time) and its client script.
export type Tilt = { k: number; deg: number[][] };

/** Grid angle of local north (degrees) at fractional image position (u, v),
 *  v = 0 at the top. Bilinear on the coarse lattice written by map_meta.py. */
export function tiltAt(t: Tilt, u: number, v: number): number {
  const c = (x: number) => Math.min(Math.max(x, 0), 1) * (t.k - 1);
  const x = c(u), y = c(v);
  const x0 = Math.min(Math.floor(x), t.k - 2), y0 = Math.min(Math.floor(y), t.k - 2);
  const fx = x - x0, fy = y - y0;
  const d = t.deg;
  return d[y0][x0] * (1 - fx) * (1 - fy) + d[y0][x0 + 1] * fx * (1 - fy) + d[y0 + 1][x0] * (1 - fx) * fy + d[y0 + 1][x0 + 1] * fx * fy;
}
