// Draws the plane-of-sky magnetic field from Planck Stokes Q and U in the
// browser (WebGL2), over the 353 GHz dust intensity in the copper palette.
//
// Data: src/data/stokes.json and the 16-bit PNG planes in public/sky/stokes,
// written by scripts/render_stokes.py. Q and U are IAU and referenced to the
// grid's vertical axis, so psi = 0.5 atan2(U, Q) is measured on screen from up
// towards left (east) and the field is psi + 90 deg. Stokes parameters are
// interpolated, never angles.
//
// Drawing: line integral convolution of a noise texture along the field,
// computed per fragment. Streak length is one smoothing FWHM, so streaks are
// never finer along the field than the data; streak contrast follows the
// polarized signal to noise (none below P/sigma = 2, full above 5). The noise
// twinkles in place (each texel has its own phase), which gives slow motion
// with no direction: dust polarization is an orientation, not a vector. Under
// prefers-reduced-motion the noise is still and the view is drawn once.
// Without WebGL2 a Canvas 2D fallback draws beam-spaced segments.
import { reduce, watchVisible, onFrame } from "./motion";
import { GRID_ARCMIN } from "../lib/facts";

export type Plane = { file: string; n: number; lo: number; hi: number };
export type StokesMeta = {
  beam_arcmin: number;
  scales_arcmin: number[];
  planes: Record<string, Plane>;
  foreground: { p_fg: number; psi_fg_grid_deg: number; sigma2_per_Ifg: Record<string, number> };
  i_stretch: { lo: number; hi: number; asinh: number };
  /** Observed intensity (MJy/sr) above which the subtracted field is drawn. */
  mask_I: number;
};

// Copper dust palette, render_lmc.DUST_STOPS.
const DUST_STOPS: [number, string][] = [[0, "#000000"], [0.18, "#1c0a06"], [0.38, "#5a1e0e"], [0.58, "#a8461a"], [0.76, "#e08a3c"], [0.9, "#f6c98a"], [1, "#fff6e6"]];
// Q, U, sigma and I_fg are uploaded in units of 1e-3 MJy/sr to sit well inside half-float range.
const K = 1000;
const SNR_LO = 2;
const SNR_HI = 5;

/** Decode a 16-bit greyscale, non-interlaced PNG to physical values. Browsers
 *  decode images to 8 bits per channel, so the PNG is parsed here and inflated
 *  with DecompressionStream. */
export async function loadPlane(p: Plane): Promise<Float32Array> {
  const buf = await (await fetch(p.file)).arrayBuffer();
  const dv = new DataView(buf);
  const u8 = new Uint8Array(buf);
  let o = 8, w = 0, h = 0;
  const idat: Uint8Array[] = [];
  while (o < buf.byteLength) {
    const len = dv.getUint32(o);
    const type = String.fromCharCode(u8[o + 4], u8[o + 5], u8[o + 6], u8[o + 7]);
    if (type === "IHDR") {
      w = dv.getUint32(o + 8);
      h = dv.getUint32(o + 12);
      if (u8[o + 16] !== 16 || u8[o + 17] !== 0 || u8[o + 20] !== 0) throw new Error("expected 16-bit grey PNG: " + p.file);
    } else if (type === "IDAT") idat.push(u8.subarray(o + 8, o + 8 + len));
    else if (type === "IEND") break;
    o += 12 + len;
  }
  const stream = new Blob(idat as BlobPart[]).stream().pipeThrough(new DecompressionStream("deflate"));
  const raw = new Uint8Array(await new Response(stream).arrayBuffer());
  const stride = w * 2, bpp = 2;
  const img = new Uint8Array(stride * h);
  for (let y = 0; y < h; y++) {
    const f = raw[y * (stride + 1)];
    const src = y * (stride + 1) + 1, dst = y * stride, prev = dst - stride;
    for (let x = 0; x < stride; x++) {
      const a = x >= bpp ? img[dst + x - bpp] : 0;
      const b = y > 0 ? img[prev + x] : 0;
      const c = x >= bpp && y > 0 ? img[prev + x - bpp] : 0;
      let v = raw[src + x];
      if (f === 1) v += a;
      else if (f === 2) v += b;
      else if (f === 3) v += (a + b) >> 1;
      else if (f === 4) {
        const pp = a + b - c, pa = Math.abs(pp - a), pb = Math.abs(pp - b), pc = Math.abs(pp - c);
        v += pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
      }
      img[dst + x] = v & 255;
    }
  }
  const out = new Float32Array(w * h);
  const k = (p.hi - p.lo) / 65535;
  for (let i = 0; i < w * h; i++) out[i] = p.lo + k * ((img[2 * i] << 8) | img[2 * i + 1]);
  return out;
}

/** Bilinear resample of an n x n plane to m x m (texel centres aligned). */
function resample(a: Float32Array, n: number, m: number): Float32Array {
  if (n === m) return a;
  const out = new Float32Array(m * m);
  for (let j = 0; j < m; j++) {
    const y = Math.min(Math.max(((j + 0.5) * n) / m - 0.5, 0), n - 1);
    const y0 = Math.floor(y), y1 = Math.min(y0 + 1, n - 1), fy = y - y0;
    for (let i = 0; i < m; i++) {
      const x = Math.min(Math.max(((i + 0.5) * n) / m - 0.5, 0), n - 1);
      const x0 = Math.floor(x), x1 = Math.min(x0 + 1, n - 1), fx = x - x0;
      out[j * m + i] = (a[y0 * n + x0] * (1 - fx) + a[y0 * n + x1] * fx) * (1 - fy) + (a[y1 * n + x0] * (1 - fx) + a[y1 * n + x1] * fx) * fy;
    }
  }
  return out;
}

const hex = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);

/** Dust intensity (MJy/sr) to 0..1, the stretch of render_lmc.stretch(). */
export function stretchI(v: number, s: StokesMeta["i_stretch"]) {
  const x = Math.min(Math.max((v - s.lo) / (s.hi - s.lo), 0), 1);
  return Math.asinh(x / s.asinh) / Math.asinh(1 / s.asinh);
}

export function copper(t: number): [number, number, number] {
  for (let i = 1; i < DUST_STOPS.length; i++) {
    const [p1, c1] = DUST_STOPS[i];
    if (t <= p1) {
      const [p0, c0] = DUST_STOPS[i - 1];
      const f = (t - p0) / (p1 - p0), a = hex(c0), b = hex(c1);
      return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f];
    }
  }
  return hex(DUST_STOPS[DUST_STOPS.length - 1][1]) as [number, number, number];
}

export type ScaleData = { q: Float32Array; u: Float32Array; s: Float32Array; f: Float32Array; n: number };

/** Loads and caches planes. One instance per page. */
export class StokesStore {
  private cache = new Map<string, Promise<any>>();
  constructor(public meta: StokesMeta) {}
  plane(key: string) {
    if (!this.cache.has(key)) this.cache.set(key, loadPlane(this.meta.planes[key]));
    return this.cache.get(key)! as Promise<Float32Array>;
  }
  scale(T: number): Promise<ScaleData> {
    const k = String(T).padStart(2, "0");
    const id = "scale" + k;
    if (!this.cache.has(id)) {
      this.cache.set(id, Promise.all([this.plane("q" + k), this.plane("u" + k), this.plane("s" + k), this.plane("f" + k)]).then(([q, u, s, f]) => {
        const n = this.meta.planes["q" + k].n;
        return { q, u, s, f: resample(f, this.meta.planes["f" + k].n, n), n };
      }));
    }
    return this.cache.get(id)!;
  }
  /** Dust intensity observed and after subtraction of I_fg (16' plane), both stretched 0..1. */
  dust(): Promise<{ obs: Float32Array; aft: Float32Array; n: number }> {
    if (!this.cache.has("dust")) {
      this.cache.set("dust", Promise.all([this.plane("I"), this.plane("f15")]).then(([I, f]) => {
        const n = this.meta.planes.I.n;
        const fu = resample(f, this.meta.planes.f15.n, n);
        const obs = new Float32Array(n * n), aft = new Float32Array(n * n);
        for (let i = 0; i < n * n; i++) {
          obs[i] = stretchI(I[i], this.meta.i_stretch);
          aft[i] = stretchI(I[i] - fu[i], this.meta.i_stretch);
        }
        return { obs, aft, n };
      }));
    }
    return this.cache.get("dust")!;
  }
}

const stores = new Map<string, StokesStore>();
/** One store per page, so several views share downloads. */
export function getStore(meta: StokesMeta) {
  const k = meta.planes.I.file;
  if (!stores.has(k)) stores.set(k, new StokesStore(meta));
  return stores.get(k)!;
}

export type FieldOpts = {
  scale: number;
  /** Fraction of the width, from the left, shown as observed; the rest is foreground-subtracted. 1 = all observed. */
  split: number;
};

const VS = `#version 300 es
in vec2 p; out vec2 uv;
void main() { uv = vec2(p.x * 0.5 + 0.5, 0.5 - p.y * 0.5); gl_Position = vec4(p, 0.0, 1.0); }`;

// uv: x right, y down; (0, 0) is the top-left corner (north-east of the map).
const FS = `#version 300 es
precision highp float;
in vec2 uv; out vec4 o;
uniform sampler2D tStokes;  // r=Q g=U b=sigma a=I_fg, 1e-3 MJy/sr
uniform sampler2D tDust;    // r=observed g=after, stretched 0..1
uniform sampler2D tNoise;   // r=value g=phase
uniform float uSplit, uLen, uTime, uPfg, uSig2k, uNoisePx, uRes, uMask;
uniform vec2 uFg;           // (cos 2psi_fg, sin 2psi_fg)
uniform vec3 uStops[7]; uniform float uPos[7];
const int N = 14;

vec3 copper(float t) {
  vec3 c = uStops[0];
  for (int i = 1; i < 7; i++) c = mix(c, uStops[i], clamp((t - uPos[i-1]) / (uPos[i] - uPos[i-1]), 0.0, 1.0));
  return c;
}
vec2 qu(vec2 x, float after) {
  vec4 s = texture(tStokes, x);
  return s.rg - after * uPfg * s.a * uFg;
}
// Field direction on screen (x right, y down): psi from up towards left, field = psi + 90 deg.
vec2 dir(vec2 x, float after) {
  vec2 v = qu(x, after);
  float psi = 0.5 * atan(v.y, v.x);
  float th = psi + 1.5707963;
  return vec2(-sin(th), -cos(th));
}
float noise(vec2 x) {
  vec2 n = texture(tNoise, x * uRes / uNoisePx).rg;
  return 0.5 + 0.5 * sin(6.2831853 * (n.g + uTime) ) * (0.6 + 0.4 * n.r);
}
void main() {
  float after = uv.x > uSplit ? 1.0 : 0.0;
  vec4 s = texture(tStokes, uv);
  vec2 v = s.rg - after * uPfg * s.a * uFg;
  float sig = sqrt(s.b * s.b + after * uSig2k * s.a);
  float snr = length(v) / max(sig, 1e-6);
  float a = smoothstep(${SNR_LO.toFixed(1)}, ${SNR_HI.toFixed(1)}, snr);
  vec2 dd = texture(tDust, uv).rg;
  // After subtraction, only where the observed intensity is above the map
  // median (the paper's mask): elsewhere the residual is Milky Way structure
  // the uniform foreground model does not describe, not LMC field.
  a *= mix(1.0, smoothstep(uMask - 0.02, uMask + 0.02, dd.r), after);
  float acc = noise(uv), wsum = 1.0;
  float h = uLen / float(N);
  for (int sgn = -1; sgn <= 1; sgn += 2) {
    vec2 x = uv; vec2 d0 = dir(uv, after) * float(sgn);
    for (int i = 1; i <= N; i++) {
      vec2 d = dir(x, after);
      if (dot(d, d0) < 0.0) d = -d;
      d0 = d;
      x += d * h;
      float w = 0.5 + 0.5 * cos(3.1415926 * float(i) / float(N + 1));
      acc += w * noise(x); wsum += w;
    }
  }
  float lic = clamp((acc / wsum - 0.5) * 3.2 + 0.5, 0.0, 1.0);
  float dust = after > 0.5 ? dd.g : dd.r;
  float t = clamp(dust + a * 0.42 * (lic - 0.5) * (0.35 + dust), 0.0, 1.0);
  o = vec4(copper(t), 1.0);
}`;

function sh(gl: WebGL2RenderingContext, type: number, src: string) {
  const s = gl.createShader(type)!;
  gl.shaderSource(s, src);
  gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s) || "shader");
  return s;
}

/** A live field view on a canvas. Call set() to change scale or split. */
export class FieldView {
  private gl: WebGL2RenderingContext | null = null;
  private tex: Record<string, WebGLTexture> = {};
  private u: Record<string, WebGLUniformLocation | null> = {};
  private visible = false;
  private dirty = true;
  private ready = false;
  private ctx2d: CanvasRenderingContext2D | null = null;
  private scaleData: ScaleData | null = null;
  private dust: { obs: Float32Array; aft: Float32Array; n: number } | null = null;
  private loading = 0;
  private last = 0;
  webgl: boolean;
  private started = false;

  constructor(private canvas: HTMLCanvasElement, private store: StokesStore, private opts: FieldOpts) {
    const gl = canvas.getContext("webgl2", { antialias: false, premultipliedAlpha: false, preserveDrawingBuffer: false });
    this.webgl = !!gl;
    if (gl) {
      try { this.initGL(gl); this.gl = gl; } catch (e) { console.warn(e); this.webgl = false; }
    }
    if (!this.gl) this.ctx2d = canvas.getContext("2d");
    new ResizeObserver(() => { this.resize(); this.dirty = true; }).observe(canvas);
    watchVisible(canvas, (on) => { this.visible = on; this.dirty = true; }, "200px");
    // The Stokes planes are about 600 KB of PNG: fetch them when the map is
    // a screen away, not with the page.
    watchVisible(canvas, (on) => { if (on && !this.started) { this.started = true; this.load(); } }, "100%");
    onFrame((t) => this.frame(t));
  }

  set(o: Partial<FieldOpts>) {
    const reload = o.scale !== undefined && o.scale !== this.opts.scale;
    Object.assign(this.opts, o);
    this.dirty = true;
    if (reload && this.started) this.load();
  }

  private async load() {
    const id = ++this.loading;
    const [sd, dust] = await Promise.all([this.store.scale(this.opts.scale), this.store.dust()]);
    if (id !== this.loading) return;
    this.scaleData = sd;
    this.dust = dust;
    if (this.gl) this.upload(sd, dust);
    this.ready = true;
    this.dirty = true;
  }

  /** Field at fractional position (u right, v down): grid angle of B (deg,
   *  from up towards left) and polarized S/N, on the side of the split it falls. */
  sample(u: number, v: number): { b: number; snr: number; after: boolean } | null {
    const sd = this.scaleData;
    if (!sd) return null;
    const n = sd.n, i = Math.min(n - 1, Math.max(0, Math.floor(v * n))) * n + Math.min(n - 1, Math.max(0, Math.floor(u * n)));
    const fg = this.store.meta.foreground, after = u > this.opts.split ? 1 : 0;
    const psi = (fg.psi_fg_grid_deg * Math.PI) / 180;
    const q = sd.q[i] - after * fg.p_fg * sd.f[i] * Math.cos(2 * psi);
    const w = sd.u[i] - after * fg.p_fg * sd.f[i] * Math.sin(2 * psi);
    const sig = Math.sqrt(sd.s[i] ** 2 + after * fg.sigma2_per_Ifg[String(this.opts.scale).padStart(2, "0")] * sd.f[i]);
    return { b: (0.5 * Math.atan2(w, q) * 180) / Math.PI + 90, snr: Math.hypot(q, w) / sig, after: !!after };
  }

  private resize() {
    const r = this.canvas.getBoundingClientRect();
    // Cap the backing store: the data hold ~260 beams across at 7', so more
    // pixels add cost on phone GPUs and nothing to the field.
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const px = Math.max(64, Math.min(Math.round(r.width * dpr), this.gl ? this.maxPx : 1200));
    if (this.canvas.width !== px) { this.canvas.width = px; this.canvas.height = px; }
  }

  private initGL(gl: WebGL2RenderingContext) {
    const p = gl.createProgram()!;
    gl.attachShader(p, sh(gl, gl.VERTEX_SHADER, VS));
    gl.attachShader(p, sh(gl, gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p) || "link");
    gl.useProgram(p);
    const b = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, b);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(p, "p");
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    for (const k of ["tStokes", "tDust", "tNoise", "uSplit", "uLen", "uTime", "uPfg", "uSig2k", "uFg", "uStops", "uPos", "uNoisePx", "uRes", "uMask"]) this.u[k] = gl.getUniformLocation(p, k);
    gl.uniform3fv(this.u.uStops, DUST_STOPS.flatMap(([, c]) => hex(c)));
    gl.uniform1fv(this.u.uPos, DUST_STOPS.map(([q]) => q));
    gl.uniform1i(this.u.tStokes, 0);
    gl.uniform1i(this.u.tDust, 1);
    gl.uniform1i(this.u.tNoise, 2);
    // Noise: value and phase per texel, fixed seed so every visit looks the same.
    const n = 256, data = new Uint8Array(n * n * 2);
    let s = 12345;
    for (let i = 0; i < data.length; i++) { s = (s * 1103515245 + 12345) & 0x7fffffff; data[i] = s >> 23; }
    this.tex.noise = this.texture(gl, 2, gl.RG8, gl.RG, gl.UNSIGNED_BYTE, n, data, gl.REPEAT, gl.NEAREST);
  }

  private texture(gl: WebGL2RenderingContext, unit: number, ifmt: number, fmt: number, type: number, n: number, data: ArrayBufferView, wrap: number = gl.CLAMP_TO_EDGE, filt: number = gl.LINEAR) {
    const t = gl.createTexture()!;
    gl.activeTexture(gl.TEXTURE0 + unit);
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
    gl.texImage2D(gl.TEXTURE_2D, 0, ifmt, n, n, 0, fmt, type, data);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filt);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filt);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, wrap);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, wrap);
    return t;
  }

  private upload(sd: ScaleData, dust: { obs: Float32Array; aft: Float32Array; n: number }) {
    const gl = this.gl!;
    const n = sd.n, a = new Float32Array(n * n * 4);
    for (let i = 0; i < n * n; i++) { a[4 * i] = sd.q[i] * K; a[4 * i + 1] = sd.u[i] * K; a[4 * i + 2] = sd.s[i] * K; a[4 * i + 3] = sd.f[i] * K; }
    if (this.tex.stokes) gl.deleteTexture(this.tex.stokes);
    this.tex.stokes = this.texture(gl, 0, gl.RGBA16F, gl.RGBA, gl.FLOAT, n, a);
    if (!this.tex.dust) {
      const m = dust.n, d = new Float32Array(m * m * 2);
      for (let i = 0; i < m * m; i++) { d[2 * i] = dust.obs[i]; d[2 * i + 1] = dust.aft[i]; }
      this.tex.dust = this.texture(gl, 1, gl.RG16F, gl.RG, gl.FLOAT, m, d);
    }
  }

  // Frame-time guard for slow GPUs: if animated frames keep arriving late,
  // halve the backing store once, then stop the twinkle.
  private maxPx = 900;
  private still = false;
  private slow = 0;
  private prevT = 0;

  private guard(t: number) {
    const dt = t - this.prevT;
    this.prevT = t;
    if (dt <= 0 || dt > 500) return; // first frame or a tab switch
    this.slow = dt > 50 ? this.slow + 1 : Math.max(0, this.slow - 1);
    if (this.slow < 20) return;
    this.slow = 0;
    if (this.maxPx > 450) { this.maxPx = 450; this.resize(); }
    else this.still = true;
  }

  private frame(t: number) {
    if (!this.visible || !this.ready) return;
    const animate = !!this.gl && !reduce && !this.still;
    if (animate) this.guard(t);
    // The twinkle is slow; 30 fps is enough and halves the GPU load.
    if (!this.dirty && !(animate && t - this.last > 33)) return;
    this.last = t;
    this.dirty = false;
    if (this.gl) this.drawGL(animate ? t / 1000 : 0);
    else this.draw2d();
  }

  private drawGL(time: number) {
    const gl = this.gl!, o = this.opts, fg = this.store.meta.foreground;
    gl.viewport(0, 0, this.canvas.width, this.canvas.height);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, this.tex.stokes);
    gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, this.tex.dust);
    gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, this.tex.noise);
    const psi = (fg.psi_fg_grid_deg * Math.PI) / 180;
    gl.uniform1f(this.u.uSplit, o.split);
    // Streak length 1.6 FWHM in all (0.8 each way): long enough to read the
    // orientation, and the field is coherent over at least a beam along it.
    gl.uniform1f(this.u.uLen, (0.8 * o.scale) / GRID_ARCMIN);
    gl.uniform1f(this.u.uTime, time * 0.12);
    gl.uniform1f(this.u.uPfg, fg.p_fg);
    gl.uniform1f(this.u.uSig2k, fg.sigma2_per_Ifg[String(o.scale).padStart(2, "0")] * K);
    gl.uniform2f(this.u.uFg, Math.cos(2 * psi), Math.sin(2 * psi));
    gl.uniform1f(this.u.uRes, this.canvas.width);
    // Noise texel no smaller than one integration step, so long streaks at
    // coarse smoothing do not alias into dots; coarse data get a coarse grain.
    const stepPx = (0.8 * o.scale * this.canvas.width) / GRID_ARCMIN / 14;
    gl.uniform1f(this.u.uNoisePx, 256 * Math.max(1.5, this.canvas.width / 600, stepPx));
    gl.uniform1f(this.u.uMask, stretchI(this.store.meta.mask_I, this.store.meta.i_stretch));
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }

  /** Fallback: copper dust plus segments one beam apart, one beam long. */
  private draw2d() {
    const c = this.ctx2d, sd = this.scaleData, dust = this.dust;
    if (!c || !sd || !dust) return;
    const W = this.canvas.width, o = this.opts, fg = this.store.meta.foreground;
    const m = dust.n, img = c.createImageData(m, m);
    const splitPx = o.split * m;
    for (let i = 0; i < m * m; i++) {
      const rgb = copper((i % m) < splitPx ? dust.obs[i] : dust.aft[i]);
      img.data[4 * i] = rgb[0] * 255; img.data[4 * i + 1] = rgb[1] * 255; img.data[4 * i + 2] = rgb[2] * 255; img.data[4 * i + 3] = 255;
    }
    const off = document.createElement("canvas");
    off.width = off.height = m;
    off.getContext("2d")!.putImageData(img, 0, 0);
    c.imageSmoothingEnabled = true;
    c.drawImage(off, 0, 0, W, W);
    const n = sd.n, step = (o.scale / GRID_ARCMIN) * W;
    const psi = (fg.psi_fg_grid_deg * Math.PI) / 180, k2 = fg.sigma2_per_Ifg[String(o.scale).padStart(2, "0")];
    c.lineCap = "round";
    c.lineWidth = Math.max(1, W / 500);
    for (let y = step / 2; y < W; y += step) for (let x = step / 2; x < W; x += step) {
      const i = Math.min(n - 1, Math.floor((y / W) * n)) * n + Math.min(n - 1, Math.floor((x / W) * n));
      const after = x > o.split * W ? 1 : 0;
      const q = sd.q[i] - after * fg.p_fg * sd.f[i] * Math.cos(2 * psi);
      const u = sd.u[i] - after * fg.p_fg * sd.f[i] * Math.sin(2 * psi);
      const sig = Math.sqrt(sd.s[i] ** 2 + after * k2 * sd.f[i]);
      const snr = Math.hypot(q, u) / sig;
      let a = Math.min(1, Math.max(0, (snr - SNR_LO) / (SNR_HI - SNR_LO)));
      if (after) {
        const m = dust.n, j = Math.min(m - 1, Math.floor((y / W) * m)) * m + Math.min(m - 1, Math.floor((x / W) * m));
        if (dust.obs[j] < stretchI(this.store.meta.mask_I, this.store.meta.i_stretch)) a = 0;
      }
      if (a <= 0) continue;
      const th = 0.5 * Math.atan2(u, q) + Math.PI / 2;
      const dx = -Math.sin(th) * step * 0.4, dy = -Math.cos(th) * step * 0.4;
      c.strokeStyle = `rgba(243,243,239,${0.85 * a})`;
      c.beginPath(); c.moveTo(x - dx, y - dy); c.lineTo(x + dx, y + dy); c.stroke();
    }
  }
}
