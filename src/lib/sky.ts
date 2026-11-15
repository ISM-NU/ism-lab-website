// Sidereal time and altitude, shared by the console readout (Base.astro) and
// the LMC visibility panel (LmcSky.astro). Low-precision on purpose: GMST from
// days since J2000 and no nutation, nutation and precession corrections,
// which is good to a few seconds of time and far below a degree of altitude.

const RAD = Math.PI / 180;

/** Centre of the LMC (SIMBAD, ICRS), degrees. Used for every altitude on the site. */
export const LMC = { ra: 80.894, dec: -69.756 };

/** Days since J2000.0 (2000-01-01 12:00 UT) for a Date. */
export const daysSinceJ2000 = (t: Date) => t.getTime() / 86400000 + 2440587.5 - 2451545.0;

/** Local apparent sidereal time in hours, 0 to 24, at east longitude `lonDeg`. */
export function lstHours(t: Date, lonDeg: number): number {
  const d = daysSinceJ2000(t);
  let gmst = (18.697374558 + 24.06570982441908 * d) % 24;
  if (gmst < 0) gmst += 24;
  return (gmst + lonDeg / 15) % 24;
}

/** Altitude in degrees of a fixed point (ra, dec in degrees) from latitude `latDeg`, given the local sidereal time in hours. */
export function altitudeAtLst(lst: number, latDeg: number, raDeg: number, decDeg: number): number {
  const H = (lst * 15 - raDeg) * RAD;
  const s = Math.sin(latDeg * RAD) * Math.sin(decDeg * RAD) + Math.cos(latDeg * RAD) * Math.cos(decDeg * RAD) * Math.cos(H);
  return Math.asin(s) / RAD;
}

export const altitude = (t: Date, latDeg: number, lonDeg: number, raDeg: number, decDeg: number) =>
  altitudeAtLst(lstHours(t, lonDeg), latDeg, raDeg, decDeg);

/** Highest altitude a point ever reaches from a latitude (upper culmination), degrees. */
export const maxAltitude = (latDeg: number, decDeg: number) => 90 - Math.abs(latDeg - decDeg);

/**
 * Sites whose data the group uses, east longitudes positive. Coordinates are
 * the primary coordinates of each site's English Wikipedia article (read via
 * the MediaWiki API, 2026-11-15); Astana is the Nazarbayev University campus.
 */
export const SITES = [
  { id: "astana", name: "Astana", note: "Nazarbayev University", lat: 51.0906, lon: 71.3982 },
  { id: "askap", name: "ASKAP", note: "Murchison, Western Australia", lat: -26.696, lon: 116.637 },
  { id: "parkes", name: "Parkes", note: "New South Wales", lat: -32.99778, lon: 148.26292 },
  { id: "alma", name: "ALMA", note: "Chajnantor, Chile", lat: -23.0193, lon: -67.7532 },
  { id: "jcmt", name: "JCMT", note: "Maunakea, Hawaii", lat: 19.822861, lon: -155.477053 },
] as const;

/** Lowest altitude a point reaches (lower culmination), degrees. Positive means it never sets. */
export const minAltitude = (latDeg: number, decDeg: number) => Math.abs(latDeg + decDeg) - 90;
