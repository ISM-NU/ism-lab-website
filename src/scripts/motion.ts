// One animation loop for the whole page. Components register a callback with
// onFrame; the loop also drives Lenis smooth scrolling.
import Lenis from "lenis";

export const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

type Frame = (t: number) => void;
const frames = new Set<Frame>();
let started = false;
let lenis: Lenis | null = null;

function loop(t: number) {
  lenis?.raf(t);
  for (const f of frames) f(t);
  requestAnimationFrame(loop);
}

export function onFrame(f: Frame): () => void {
  frames.add(f);
  if (!started) {
    started = true;
    if (!reduce) lenis = new Lenis({ lerp: 0.085 });
    requestAnimationFrame(loop);
  }
  return () => frames.delete(f);
}

/** Calls cb(true/false) as the element enters or leaves the viewport. */
export function watchVisible(el: Element, cb: (on: boolean) => void, margin = "100px") {
  const io = new IntersectionObserver((es) => cb(es[es.length - 1].isIntersecting), { rootMargin: margin });
  io.observe(el);
}

export function canvasFit(c: HTMLCanvasElement, w: number, h: number) {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  c.width = Math.round(w * dpr);
  c.height = Math.round(h * dpr);
  const x = c.getContext("2d")!;
  x.setTransform(dpr, 0, 0, dpr, 0, 0);
  return x;
}

export function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((res) => {
    const i = new Image();
    i.decoding = "async";
    i.onload = () => res(i);
    i.onerror = () => res(i);
    i.src = src;
  });
}

export const clamp = (x: number, a: number, b: number) => Math.min(b, Math.max(a, x));
export const seg = (p: number, a: number, b: number) => clamp((p - a) / (b - a), 0, 1);
export const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
export const fmt = (n: number) => Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");

const GLYPH = "01#/\\<>[]=+*:.";
/** Resolves an element's text left to right from random glyphs. */
export function scramble(el: HTMLElement, dur = 650) {
  if (reduce || el.dataset.busy) return;
  const nodes: [Text, string][] = [];
  const walk = (n: Node) => n.childNodes.forEach((c) => (c.nodeType === 3 ? nodes.push([c as Text, c.nodeValue ?? ""]) : walk(c)));
  walk(el);
  el.dataset.busy = "1";
  const t0 = performance.now();
  const step = (t: number) => {
    const k = clamp((t - t0) / dur, 0, 1);
    for (const [node, s] of nodes) {
      const cut = Math.floor(s.length * k);
      let out = s.slice(0, cut);
      for (let i = cut; i < s.length; i++) out += s[i] === " " ? " " : GLYPH[(Math.random() * GLYPH.length) | 0];
      node.nodeValue = out;
    }
    if (k < 1) requestAnimationFrame(step);
    else {
      for (const [node, s] of nodes) node.nodeValue = s;
      delete el.dataset.busy;
    }
  };
  requestAnimationFrame(step);
}
