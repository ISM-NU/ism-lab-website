// Run: node --test src/lib/estimators.test.mjs   (Node >= 22.18 strips the types from estimators.ts)
// Expected values come from the papers cited in estimators.ts; each check names its source.
import { test } from "node:test";
import assert from "node:assert/strict";
import * as E from "./estimators.ts";

const close = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg}: ${a} vs ${b} (tol ${tol})`);
const DEG = Math.PI / 180;

function draws(p0, cov, n, seed, psi0 = 0.3) {
  const g = E.gauss(E.rng(seed));
  const q0 = p0 * Math.cos(2 * psi0), u0 = p0 * Math.sin(2 * psi0);
  const out = [];
  for (let k = 0; k < n; k++) {
    const [dq, du] = E.noiseDraw(cov, g);
    out.push([q0 + dq, u0 + du]);
  }
  return out;
}
const canon = (s) => ({ qq: s * s, uu: s * s, qu: 0 });
const mean = (a) => a.reduce((s, x) => s + x, 0) / a.length;

test("seeded generator is reproducible", () => {
  const a = E.rng(7), b = E.rng(7);
  for (let i = 0; i < 5; i++) assert.equal(a(), b());
});

test("E[p^2] = p0^2 + 2 sigma^2 for the naive estimator (P14 Sect. 2.1)", () => {
  const s = 0.01, p0 = 0.02;
  const d = draws(p0, canon(s), 200000, 1);
  close(mean(d.map(([q, u]) => q * q + u * u)), p0 * p0 + 2 * s * s, 0.01 * (p0 * p0 + 2 * s * s), "second moment");
});

test("Rice mean: Rayleigh limit, Monte Carlo, asymptote p0 + sigma^2/2p0 (P14 Sect. 2.1, Eq. 9)", () => {
  close(E.riceMean(0, 1), Math.sqrt(Math.PI / 2), 1e-6, "Rayleigh mean");
  for (const snr of [0.5, 1, 3]) {
    const d = draws(snr, canon(1), 200000, 2 + snr);
    close(mean(d.map(([q, u]) => Math.hypot(q, u))), E.riceMean(snr, 1), 0.006, `MC mean at p0/sigma=${snr}`);
  }
  close(E.riceMean(20, 1), 20 + 1 / 40, 1e-4, "asymptote");
});

test("MAS: p/2 slope at the origin and p - sigma^2/2p at large p (P14 Eq. 17, 19 with lambda = 1, Eq. 20)", () => {
  close(E.mas(1e-4, 1) / 1e-4, 0.5, 1e-4, "slope at 0");
  close(E.mas(8, 1), 8 - 1 / 16, 1e-12, "asymptote");
  let prev = 0;
  for (let p = 0.01; p < 6; p += 0.01) {
    const m = E.mas(p, 1);
    assert.ok(m > 0 && m > prev, `positive and increasing at p=${p}`);
    prev = m;
  }
});

test("AS gives zero for a fraction 1 - e^-1/2 of pure-noise draws (PMA2 Eq. 13, Fig. 2: about 40%)", () => {
  const d = draws(0, canon(1), 200000, 3);
  const zeros = d.filter(([q, u]) => E.asymptotic(Math.hypot(q, u), 1) === 0).length / d.length;
  close(zeros, 1 - Math.exp(-0.5), 0.004, "null fraction");
});

test("MB with a wide flat prior: 0.8 sigma at p = 0 and P14 Eq. 21 closed form", () => {
  close(E.mbCanonical(0, 0.01, 1), Math.sqrt(2 / Math.PI) * 0.01, 1e-5, "p = 0 floor (PMA2 Sect. 7: cut-off at 0.8 sigma)");
  for (const x of [0.5, 1, 2, 4, 8]) {
    const closed = (0.01 * Math.sqrt(2 / Math.PI)) / E.i0e((x * x) / 4); // sigma sqrt(2/pi) e^(x^2/4) / I0(x^2/4)
    close(E.mbCanonical(0.01 * x, 0.01, 1), closed, 2e-4 * closed, `p/sigma=${x}`);
  }
});

test("MB on the 2D grid matches the 1D canonical form and respects the prior bound", () => {
  for (const [q, u] of [[0.003, 0.004], [0.02, -0.01], [0.0, 0.001]]) {
    const a = E.mbGeneral(q, u, canon(0.01), 1), b = E.mbCanonical(Math.hypot(q, u), 0.01, 1);
    close(a, b, 2e-3 * b, `(${q}, ${u})`);
  }
  assert.ok(E.mbGeneral(0.95, 0.2, canon(0.1), 1) < 1, "posterior mean stays below pMax");
});

test("effective ellipticity matches PMA1 Fig. 1 (eps, rho) cases", () => {
  // PMA1 Eq. 4: eps = sigma_U / sigma_Q, rho = sigma_QU / (sigma_Q sigma_U).
  const mk = (eps, rho) => ({ qq: 1, uu: eps * eps, qu: rho * eps });
  close(E.covShape(mk(1, 0)).epsEff, 1, 1e-12, "eps=1 rho=0");
  close(E.covShape(mk(1, 0.5)).epsEff, 1.73, 0.005, "eps=1 rho=0.5");
  close(E.covShape(mk(2, 0)).epsEff, 2, 1e-12, "eps=2 rho=0");
  close(E.covShape(mk(2, 0.5)).epsEff, 2.48, 0.005, "eps=2 rho=0.5");
});

test("rotated variances keep trace and determinant (PMA2 Eq. 16-18); covFromShape round trip", () => {
  const c = { qq: 2.3, uu: 0.7, qu: -0.5 };
  const s = E.covShape(c);
  close(s.sq2 + s.su2, c.qq + c.uu, 1e-12, "trace");
  close(s.sq2 * s.su2, c.qq * c.uu - c.qu * c.qu, 1e-12, "det");
  const r = E.covShape(E.covFromShape(0.3, 1.6, 0.4));
  close(r.sigmaG, 0.3, 1e-12, "sigmaG");
  close(r.epsEff, 1.6, 1e-12, "epsEff");
  close(r.theta, 0.4, 1e-12, "theta");
});

test("noise bias b^2: canonical, P14 Eq. 30 at rho = 0, angle average (P14 Eq. 29, 34)", () => {
  close(E.noiseBias(0.3, -0.2, canon(0.1)), 0.01, 1e-15, "canonical");
  const sq = 0.1, su = 0.2, phi = 0.7; // phi = 2 psi
  close(E.noiseBias(Math.cos(phi), Math.sin(phi), { qq: sq * sq, uu: su * su, qu: 0 }),
    su * su * Math.cos(phi) ** 2 + sq * sq * Math.sin(phi) ** 2, 1e-15, "P14 Eq. 30");
  const c = { qq: 0.04, uu: 0.01, qu: 0.012 };
  let avg = 0;
  const n = 3600;
  for (let k = 0; k < n; k++) avg += E.noiseBias(Math.cos((2 * Math.PI * k) / n), Math.sin((2 * Math.PI * k) / n), c) / n;
  close(avg, (c.qq + c.uu) / 2, 1e-12, "angle average");
});

test("sigma_psi = sigma / 2p in the canonical case (PIR19 Eq. B.5: 28.65 deg x sigma_p / p)", () => {
  close(E.sigmaPsi(0.03, 0.04, canon(0.01)), 0.01 / (2 * 0.05), 1e-12, "sigma_psi");
});

test("dPsi equals the difference of naive angles, wrapped to (-pi/2, pi/2]", () => {
  const a = [0.3, -0.8], b = [-0.5, -0.1];
  let d = E.naivePsi(...a) - E.naivePsi(...b);
  while (d > Math.PI / 2) d -= Math.PI;
  while (d <= -Math.PI / 2) d += Math.PI;
  close(E.dPsi(a[0], a[1], b[0], b[1]), d, 1e-12, "dPsi");
});

// PMA3 Sect. 2.2 setup: 10 pixels, p0 = 0.1, uniform configuration, canonical noise sigma = p0 / (S/N).
function sRun(S0, snr, n, seed) {
  const p0 = 0.1, s = p0 / snr, cov = canon(s), covs = Array(10).fill(cov);
  const half = canon(s * Math.SQRT2);
  const g = E.gauss(E.rng(seed));
  const sc = [], sdb = [], sd2 = [];
  for (let k = 0; k < n; k++) {
    const t = E.uniformConfig(p0, S0, (k % 9) * 10 * DEG); // psi00 stepped by 10 deg as in PMA3
    const q1 = [], u1 = [], q2 = [], u2 = [], q = [], u = [];
    for (let i = 0; i < 10; i++) {
      const [a, b] = E.noiseDraw(half, g), [c, d] = E.noiseDraw(half, g);
      q1.push(t.q[i] + a); u1.push(t.u[i] + b);
      q2.push(t.q[i] + c); u2.push(t.u[i] + d);
      q.push(t.q[i] + (a + c) / 2); u.push(t.u[i] + (b + d) / 2);
    }
    const c0 = E.sConventional(q, u);
    sc.push(c0);
    sdb.push(E.sDebiased(c0, E.sigmaS(q, u, covs)));
    sd2.push(E.sDichotomic2(q1, u1, q2, u2));
  }
  return { sc: mean(sc), sc2: mean(sc.map((x) => x * x)), sdb: mean(sdb), sd2: mean(sd2) };
}

test("S_C: rms pi/sqrt(12) for noise, S0 at high S/N (PMA3 Sect. 2.2, 3.1; PIR19 Sect. 3.3)", () => {
  // pi/sqrt(12) is the rms of |delta psi| uniform on [0, pi/2], so it holds for <S_C^2>, not <S_C>.
  close(Math.sqrt(sRun(30 * DEG, 0.01, 20000, 11).sc2), E.S_RANDOM, 0.3 * DEG, "noise-dominated");
  close(sRun(30 * DEG, 200, 2000, 12).sc, 30 * DEG, 0.2 * DEG, "noise-free");
});

test("S_C bias is positive below pi/sqrt(12) and negative above (PMA3 Sect. 3.1)", () => {
  assert.ok(sRun(Math.PI / 8, 1, 20000, 13).sc > Math.PI / 8 + 1 * DEG, "S0 = pi/8");
  assert.ok(sRun((3 * Math.PI) / 8, 1, 20000, 14).sc < (3 * Math.PI) / 8 - 1 * DEG, "S0 = 3pi/8");
});

test("S_C at S0 = pi/4: small positive bias that shrinks with S/N (PMA3 Fig. 3, orange curve)", () => {
  // Read from the figure: about +7 deg (pi/sqrt(12) - pi/4) at p0/sigma = 0.1, a few degrees at 2, near 0 at 10.
  const b2 = sRun(Math.PI / 4, 2, 40000, 15).sc - Math.PI / 4, b10 = sRun(Math.PI / 4, 10, 20000, 18).sc - Math.PI / 4;
  assert.ok(b2 > 0 && b2 < 5 * DEG, `bias at S/N 2: ${b2 / DEG} deg`);
  assert.ok(Math.abs(b10) < Math.abs(b2), `bias at S/N 10: ${b10 / DEG} deg`);
});

test("dichotomic S_D^2 tends to 0 at low S/N and to S0^2 at high S/N (PMA3 Sect. 4.1)", () => {
  close(sRun(Math.PI / 8, 0.05, 20000, 16).sd2, 0, 0.03, "low S/N mean");
  close(sRun(Math.PI / 8, 200, 2000, 17).sd2, (Math.PI / 8) ** 2, 0.002, "high S/N");
});
