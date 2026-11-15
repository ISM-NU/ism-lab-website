// Polarization estimators and the angle dispersion function, transcribed from:
//   P14   Plaszczynski et al. 2014, MNRAS 439, 4048 (arXiv:1312.0437)
//   PMA1  Montier et al. 2015a, A&A 574, A135 (2015A&A...574A.135M, arXiv:1406.6536)
//   PMA2  Montier et al. 2015b, A&A 574, A136 (2015A&A...574A.136M, arXiv:1407.0178)
//   PMA3  Alina et al. 2016, A&A 595, A57 (2016A&A...595A..57A, arXiv:1608.07105)
//   PIR19 Planck Collaboration Int. XIX 2015, A&A 576, A104 (2015A&A...576A.104P, arXiv:1405.0871)
// Equation numbers below refer to these papers. Covariances are in the units of
// q and u: divide by I0^2 to work in polarization fraction (PMA2 Eq. 3), or keep
// Stokes units to work with polarized intensity P. The intensity is taken as
// perfectly known throughout, as in PMA2 Sect. 2 for every estimator but MB in 3D.
// No DOM here: the file runs under `node --test` and in the browser.

export interface Cov {
  qq: number;
  uu: number;
  qu: number;
}

/** Seeded uniform generator in [0, 1) (mulberry32). */
export function rng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Standard normal pairs from a uniform generator (Box-Muller). */
export function gauss(u: () => number): () => number {
  let spare = NaN;
  return () => {
    if (!Number.isNaN(spare)) {
      const s = spare;
      spare = NaN;
      return s;
    }
    const r = Math.sqrt(-2 * Math.log(1 - u()));
    const t = 2 * Math.PI * u();
    spare = r * Math.sin(t);
    return r * Math.cos(t);
  };
}

/** One correlated (dq, du) noise draw for covariance c (Cholesky factor). */
export function noiseDraw(c: Cov, g: () => number): [number, number] {
  const a = Math.sqrt(c.qq);
  const b = a > 0 ? c.qu / a : 0;
  const d = Math.sqrt(Math.max(c.uu - b * b, 0));
  const z1 = g(), z2 = g();
  return [a * z1, b * z1 + d * z2];
}

export interface Shape {
  theta: number; // PMA1 Eq. 5 / PMA2 Eq. 16, rotation of the noise ellipse in the (Q, U) plane
  sq2: number; // sigma'_Q^2, PMA2 Eq. 17
  su2: number; // sigma'_U^2, PMA2 Eq. 18
  epsEff: number; // PMA1 Eq. 7-8
  sigmaG: number; // Det(Sigma)^(1/4), PMA2 Eq. 5: radius of the circular Gaussian of equal area
}

export function covShape(c: Cov): Shape {
  // atan2 picks one of the two principal axes; Eq. 15 is unchanged if theta moves by
  // pi/2 because sigma'_Q and sigma'_U swap with it.
  const theta = 0.5 * Math.atan2(2 * c.qu, c.qq - c.uu);
  const cs = Math.cos(theta), sn = Math.sin(theta), s2 = Math.sin(2 * theta);
  const sq2 = c.qq * cs * cs + c.uu * sn * sn + c.qu * s2;
  const su2 = c.qq * sn * sn + c.uu * cs * cs - c.qu * s2;
  const tr = c.qq + c.uu;
  const sp2 = Math.sqrt((c.qq - c.uu) ** 2 + 4 * c.qu * c.qu); // PMA1 Eq. 8
  const epsEff = Math.sqrt((tr + sp2) / (tr - sp2)); // PMA1 Eq. 7
  const sigmaG = Math.pow(c.qq * c.uu - c.qu * c.qu, 0.25);
  return { theta, sq2, su2, epsEff, sigmaG };
}

/** Covariance with Det = sigmaG^4, axis ratio epsEff (>= 1) and major axis at theta in the (Q, U) plane. */
export function covFromShape(sigmaG: number, epsEff: number, theta: number): Cov {
  const l1 = sigmaG * sigmaG * epsEff, l2 = (sigmaG * sigmaG) / epsEff;
  const cs = Math.cos(theta), sn = Math.sin(theta);
  return { qq: l1 * cs * cs + l2 * sn * sn, uu: l1 * sn * sn + l2 * cs * cs, qu: (l1 - l2) * sn * cs };
}

/** Naive estimates: p = sqrt(q^2 + u^2), psi = atan2(u, q) / 2 (PMA3 Eq. 1-2). */
export const naiveP = (q: number, u: number) => Math.hypot(q, u);
export const naivePsi = (q: number, u: number) => 0.5 * Math.atan2(u, q);

/**
 * Noise bias b^2 (PMA2 Eq. 15, P14 Eq. 35): the variance across the direction of
 * the measured polarization vector, with the true angle replaced by the measured
 * one as PMA2 prescribes for MAS. Reduces to sigma^2 when Sigma is canonical.
 */
export function noiseBias(q: number, u: number, c: Cov, s: Shape = covShape(c)): number {
  const a = Math.atan2(u, q) - s.theta; // 2 psi - theta
  const ca = Math.cos(a), sa = Math.sin(a);
  return s.su2 * ca * ca + s.sq2 * sa * sa;
}

/** Asymptotic estimator (PMA2 Eq. 13 with sigma_p^2 replaced by b^2 as in Eq. 15). Zero below p = b. */
export function asymptotic(p: number, b2: number): number {
  return p * p > b2 ? Math.sqrt(p * p - b2) : 0;
}

/** Modified Asymptotic estimator (P14 Eq. 20; PMA2 Eq. 19 with the noise bias b^2). */
export function mas(p: number, b2: number): number {
  if (p <= 0) return 0;
  return p - (b2 * (1 - Math.exp((-p * p) / b2))) / (2 * p);
}

// Exponentially scaled modified Bessel functions I0(x) e^-x and I1(x) e^-x, x >= 0.
// Polynomial approximations of Abramowitz & Stegun 9.8.1-9.8.4 (|error| < 2.2e-7 relative).
export function i0e(x: number): number {
  const ax = Math.abs(x);
  if (ax < 3.75) {
    const t = (x / 3.75) ** 2;
    return Math.exp(-ax) * (1 + t * (3.5156229 + t * (3.0899424 + t * (1.2067492 + t * (0.2659732 + t * (0.0360768 + t * 0.0045813))))));
  }
  const t = 3.75 / ax;
  return (0.39894228 + t * (0.01328592 + t * (0.00225319 + t * (-0.00157565 + t * (0.00916281 + t * (-0.02057706 + t * (0.02635537 + t * (-0.01647633 + t * 0.00392377)))))))) / Math.sqrt(ax);
}
export function i1e(x: number): number {
  const ax = Math.abs(x);
  let r: number;
  if (ax < 3.75) {
    const t = (x / 3.75) ** 2;
    r = Math.exp(-ax) * ax * (0.5 + t * (0.87890594 + t * (0.51498869 + t * (0.15084934 + t * (0.02658733 + t * (0.00301532 + t * 0.00032411))))));
  } else {
    const t = 3.75 / ax;
    r = (0.39894228 + t * (-0.03988024 + t * (-0.00362018 + t * (0.00163801 + t * (-0.01031555 + t * (0.02282967 + t * (-0.02895312 + t * (0.01787654 + t * -0.00420059)))))))) / Math.sqrt(ax);
  }
  return x < 0 ? -r : r;
}

/** Mean of the Rice distribution, sigma sqrt(pi/2) L_1/2(-p0^2 / 2 sigma^2) (P14 Sect. 2.1). */
export function riceMean(p0: number, sigma: number): number {
  const x = (p0 * p0) / (2 * sigma * sigma);
  // L_1/2(-x) = e^(x/2) [(1 + x) I0(x/2) + x I1(x/2)]; the exponentials cancel against the scaled Bessels.
  return sigma * Math.sqrt(Math.PI / 2) * ((1 + x) * i0e(x / 2) + x * i1e(x / 2));
}

/**
 * Mean posterior Bayesian estimator in the canonical case (PMA2 Eq. 26) with the
 * flat prior on p0 in [0, pMax] of PMA2 Sect. 2.6. After integrating psi0 the
 * posterior of p0 is proportional to exp(-p0^2 / 2 sigma^2) I0(p p0 / sigma^2).
 */
export function mbCanonical(p: number, sigma: number, pMax = 1, n = 241): number {
  const lo = Math.max(0, p - 9 * sigma), hi = Math.min(pMax, p + 9 * sigma);
  if (hi <= lo) return Math.min(p, pMax);
  const h = (hi - lo) / (n - 1);
  let num = 0, den = 0;
  for (let k = 0; k < n; k++) {
    const p0 = lo + k * h;
    const z = (p * p0) / (sigma * sigma);
    // exp(-(p0 - p)^2 / 2 sigma^2) I0e(z) is the posterior up to a constant factor.
    const w = Math.exp(-((p0 - p) ** 2) / (2 * sigma * sigma)) * i0e(z) * (k === 0 || k === n - 1 ? 0.5 : 1);
    num += w * p0;
    den += w;
  }
  return num / den;
}

/**
 * Mean posterior Bayesian estimator for any covariance (PMA2 Eq. 26): the 2D
 * likelihood of (q, u) given (p0, psi0) is the bivariate Gaussian of PMA1 Eq. 2,
 * with a flat prior in (p0, psi0) over [0, pMax] x [-pi/2, pi/2]. Integrated on a
 * grid; psi0 is periodic so the trapezoid rule there converges fast.
 */
export function mbGeneral(q: number, u: number, c: Cov, pMax = 1, np = 121, nq = 144): number {
  const det = c.qq * c.uu - c.qu * c.qu;
  const iqq = c.uu / det, iuu = c.qq / det, iqu = -c.qu / det;
  const smax = Math.sqrt(Math.max(c.qq, c.uu) + Math.abs(c.qu));
  const p = Math.hypot(q, u);
  const lo = Math.max(0, p - 9 * smax), hi = Math.min(pMax, p + 9 * smax);
  if (hi <= lo) return Math.min(p, pMax);
  const h = (hi - lo) / (np - 1);
  const cs = new Float64Array(nq), sn = new Float64Array(nq);
  for (let j = 0; j < nq; j++) {
    const a = -Math.PI + (2 * Math.PI * j) / nq; // 2 psi0
    cs[j] = Math.cos(a);
    sn[j] = Math.sin(a);
  }
  // Subtract the smallest chi^2 on the grid before exponentiating (it is near the measurement).
  const chi = new Float64Array(np * nq);
  let cmin = Infinity;
  for (let k = 0; k < np; k++) {
    const p0 = lo + k * h;
    for (let j = 0; j < nq; j++) {
      const dq = q - p0 * cs[j], du = u - p0 * sn[j];
      const x = dq * dq * iqq + 2 * dq * du * iqu + du * du * iuu;
      chi[k * nq + j] = x;
      if (x < cmin) cmin = x;
    }
  }
  let num = 0, den = 0;
  for (let k = 0; k < np; k++) {
    const p0 = lo + k * h;
    let row = 0;
    for (let j = 0; j < nq; j++) row += Math.exp(-0.5 * (chi[k * nq + j] - cmin));
    const w = row * (k === 0 || k === np - 1 ? 0.5 : 1);
    num += w * p0;
    den += w;
  }
  return num / den;
}

// ---------------------------------------------------------------- dispersion function

/** Angle difference psi(x) - psi(x + l_i) from Stokes parameters (PMA3 Eq. 5, PIR19 Eq. 7). */
export function dPsi(qx: number, ux: number, qi: number, ui: number): number {
  return 0.5 * Math.atan2(ux * qi - qx * ui, qx * qi + ux * ui);
}

/** Conventional estimator S_C (PMA3 Eq. 4-5). Arrays hold the central pixel at index 0. */
export function sConventional(q: ArrayLike<number>, u: ArrayLike<number>): number {
  let s = 0;
  const n = q.length - 1;
  for (let i = 1; i <= n; i++) s += dPsi(q[0], u[0], q[i], u[i]) ** 2;
  return Math.sqrt(s / n);
}

/**
 * Conventional angle uncertainty with I known (PIR19 Eq. B.5 with Eq. B.2, C_II = C_IQ = C_IU = 0):
 * sigma_psi = (1/2) sqrt(Q^2 C_UU + U^2 C_QQ - 2 Q U C_QU) / (Q^2 + U^2) radians.
 * The 28.65 deg of Eq. B.5 is this 1/2 rad.
 */
export function sigmaPsi(q: number, u: number, c: Cov): number {
  return (0.5 * Math.sqrt(Math.max(q * q * c.uu + u * u * c.qq - 2 * q * u * c.qu, 0))) / (q * q + u * u);
}

/** Conventional uncertainty on S (PMA3 Eq. A.8 = Eq. 16-17, PIR19 Eq. 9). */
export function sigmaS(q: ArrayLike<number>, u: ArrayLike<number>, c: Cov[]): number {
  const n = q.length - 1;
  let sum = 0, sq = 0, s2 = 0;
  for (let i = 1; i <= n; i++) {
    const d = dPsi(q[0], u[0], q[i], u[i]);
    sum += d;
    s2 += d * d;
    sq += d * d * sigmaPsi(q[i], u[i], c[i]) ** 2;
  }
  const S = Math.sqrt(s2 / n);
  if (S === 0) return 0;
  return Math.sqrt(sum * sum * sigmaPsi(q[0], u[0], c[0]) ** 2 + sq) / (n * S);
}

/** Variance-subtracted estimate sqrt(S_C^2 - sigma_S^2) (PIR19 Eq. 8), set to 0 when negative. */
export function sDebiased(sc: number, sigS: number): number {
  return Math.sqrt(Math.max(sc * sc - sigS * sigS, 0));
}

/** Dichotomic estimator S_D^2 from two independent halves of the data (PMA3 Eq. 18, PIR19 Eq. 10). Can be negative. */
export function sDichotomic2(q1: ArrayLike<number>, u1: ArrayLike<number>, q2: ArrayLike<number>, u2: ArrayLike<number>): number {
  const n = q1.length - 1;
  let s = 0;
  for (let i = 1; i <= n; i++) s += dPsi(q1[0], u1[0], q1[i], u1[i]) * dPsi(q2[0], u2[0], q2[i], u2[i]);
  return s / n;
}

/** S of purely random angles: |delta psi| uniform on [0, pi/2] gives rms pi / sqrt(12) (PMA3 Sect. 2.2, PIR19 Sect. 3.3). */
export const S_RANDOM = Math.PI / Math.sqrt(12);

/**
 * True Stokes parameters of the "uniform" configuration of PMA3 Sect. 2.2: nine
 * neighbours share psi0, the central pixel sits at psi0 - S0 (Eq. 12-14), so every
 * pair differs by S0 and the true S equals S0.
 */
export function uniformConfig(p0: number, S0: number, psi0: number, n = 9): { q: number[]; u: number[] } {
  const q = [p0 * Math.cos(2 * (psi0 - S0))], u = [p0 * Math.sin(2 * (psi0 - S0))];
  for (let i = 0; i < n; i++) {
    q.push(p0 * Math.cos(2 * psi0));
    u.push(p0 * Math.sin(2 * psi0));
  }
  return { q, u };
}
