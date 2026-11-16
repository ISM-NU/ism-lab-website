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

/** Loads and decodes an image. Decoding up front, off the main thread, keeps
 * the first canvas drawImage of a large image from decoding it synchronously
 * mid-scroll (about 60 ms for the 2048 px zoom layers). */
export function loadImage(src: string): Promise<HTMLImageElement> {
  const i = new Image();
  i.decoding = "async";
  i.src = src;
  return i.decode().then(() => i, () => i);
}

/** An image decoded once into an ImageBitmap, for canvases that redraw it
 * every frame: a plain <img> may have its decoded pixels dropped and then be
 * decoded again inside a frame (35-40 ms for a 2048 px layer). Decoding from
 * the fetched bytes runs off the main thread; createImageBitmap(img) does not.
 * Falls back to an <img> where that path fails. */
export async function loadBitmap(src: string): Promise<ImageBitmap | HTMLImageElement> {
  try {
    const r = await fetch(src);
    if (!r.ok) throw new Error(String(r.status));
    return await createImageBitmap(await r.blob());
  } catch {
    return loadImage(src);
  }
}

export const clamp = (x: number, a: number, b: number) => Math.min(b, Math.max(a, x));
export const seg = (p: number, a: number, b: number) => clamp((p - a) / (b - a), 0, 1);
export const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
export const fmt = (n: number) => Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");

const GLYPH = "01#/\\<>[]=+*:.";
/** Resolves an element's text left to right from random glyphs.
 *
 * The glyphs are wider than the condensed capitals and allow line breaks
 * after / \ ] and :, so writing them into the text itself wrapped a one-line
 * heading onto two lines and shifted the page while it resolved. Instead each
 * word becomes an inline-block that keeps the real word (invisible) for its
 * size, with the glyphs drawn over it and clipped to it. Line breaks can then
 * fall only where the final text breaks. The original text nodes come back
 * when the animation ends. */
export function scramble(el: HTMLElement, dur = 650) {
  if (reduce || el.dataset.busy) return;
  const texts: Text[] = [];
  const walk = (n: Node) => n.childNodes.forEach((c) => (c.nodeType === 3 ? texts.push(c as Text) : walk(c)));
  walk(el);
  const words: [HTMLElement, string, number][] = [];
  const undo: [Text, Node[]][] = [];
  let total = 0;
  for (const t of texts) {
    const s = t.nodeValue ?? "";
    if (!s.trim()) continue;
    const parts: Node[] = [];
    for (const tok of s.split(/(\s+)/)) {
      if (!tok) continue;
      if (!tok.trim()) { parts.push(document.createTextNode(tok)); continue; }
      // Split after hyphens and slashes too: the final text may break there.
      for (const w of tok.match(/[^-/]+[-/]?|[-/]/g) ?? []) {
        const box = document.createElement("span");
        box.className = "scr";
        const real = document.createElement("span");
        real.className = "scr-r";
        real.textContent = w;
        const g = document.createElement("span");
        g.className = "scr-g";
        g.setAttribute("aria-hidden", "true");
        box.append(real, g);
        parts.push(box);
        words.push([g, w, total]);
        total += w.length;
      }
    }
    t.replaceWith(...parts);
    undo.push([t, parts]);
  }
  if (!words.length) return;
  el.dataset.busy = "1";
  const t0 = performance.now();
  const step = (t: number) => {
    const k = clamp((t - t0) / dur, 0, 1);
    const upto = Math.floor(total * k);
    for (const [g, w, at] of words) {
      const cut = clamp(upto - at, 0, w.length);
      let out = w.slice(0, cut);
      for (let i = cut; i < w.length; i++) out += GLYPH[(Math.random() * GLYPH.length) | 0];
      g.textContent = out;
    }
    if (k < 1) requestAnimationFrame(step);
    else {
      for (const [t, parts] of undo) { parts[0].parentNode?.insertBefore(t, parts[0]); parts.forEach((p) => (p as ChildNode).remove()); }
      delete el.dataset.busy;
    }
  };
  requestAnimationFrame(step);
}

/** The Webb Tarantula at a width that covers the screen in device pixels.
 * The hero and the scroll zoom share it, so it downloads once. */
export function tarantulaSrc() {
  const px = Math.max(innerWidth, innerHeight * (4 / 3)) * Math.min(devicePixelRatio || 1, 2);
  return `/webb/tarantula-${px > 2100 ? 2880 : px > 1100 ? 1920 : 960}.webp`;
}
