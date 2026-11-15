import data from "../data/publications.json";

export type Paper = (typeof data.papers)[number];
export const papers: Paper[] = data.papers;
export const groups: string[] = data.groups;
export const byBibcode = new Map(papers.map((p) => [p.bibcode, p]));

/** ADS titles carry a little HTML (<SUP>, <SUB>, entities). Keep only those. */
export function titleHtml(t: string): string {
  return t
    .replace(/&(?!(gt|lt|amp|quot|#\d+);)/g, "&amp;")
    .replace(/<(?!\/?(sup|sub)>)[^>]*>/gi, "")
    .replace(/<(\/?)(sup|sub)>/gi, (_m, s, tag) => `<${s}${tag.toLowerCase()}>`);
}

/** "Alina, D.; Smith, J. et al." with Alina kept visible when she is far down the list. */
export function authorLine(p: Paper, max = 3): string {
  const short = (a: string) => a.split(",")[0];
  const a = p.authors;
  if (a.length <= max + 1) return a.map(short).join(", ");
  const head = a.slice(0, max).map(short);
  if (p.alina_index >= max) head.push(`… ${short(a[p.alina_index])} (${p.alina_index + 1} of ${a.length})`);
  return head.join(", ") + " et al.";
}

export function link(p: Paper): string {
  if (p.doi) return `https://doi.org/${p.doi}`;
  if (p.arxiv) return `https://arxiv.org/abs/${p.arxiv}`;
  return `https://ui.adsabs.harvard.edu/abs/${encodeURIComponent(p.bibcode)}`;
}

export function venue(p: Paper): string {
  return [p.pub, p.volume, p.page].filter(Boolean).join(", ");
}

/** Large collaboration: an author list of 100 or more (the three Planck intermediate results, SCOPE, TOP-SCOPE). */
export const BIG_COLLAB = 100;
export type Role = "first" | "led" | "collab";

/**
 * Role of the group in a paper. `led` comes from scripts/fetch_publications.py:
 * a group member (the PI, or an author ADS places at Nazarbayev University)
 * is first or last author ("first": member in first position, "led": member
 * last). Everything else is a collaboration paper, wherever Alina sits in the list.
 */
export const role = (p: Paper): Role => p.role as Role;
export const isBig = (p: Paper) => !p.led && p.authors.length >= BIG_COLLAB;

/** Research lines: the four projects' `papers` lists, passed in by the page. */
export const STELLAR = "Stellar magnetism";
export const STELLAR_BIBCODES = new Set(["2011A&A...532L..13P", "2011AN....332..943P", "2012AIPC.1429...82A"]);

/**
 * Instruments and surveys matched in title or abstract. This is a text match,
 * so a paper that only uses a Planck-selected sample is tagged Planck too.
 */
const INSTRUMENTS: [string, RegExp][] = [
  ["Planck", /planck/i],
  ["PILOT", /\bPILOT\b/],
  ["Herschel", /herschel/i],
  ["JCMT", /JCMT|SCUBA-2|POL-2|SCOPE/],
  ["ALMA", /\bALMA\b/],
  ["JWST", /JWST/],
  ["TRAO", /TRAO|Taeduk/],
  ["GASS / ASKAP / Parkes", /GASS|GASKAP|ASKAP|Parkes/],
  ["Neural networks", /neural network|U-Net|Mask R-CNN|deep learning/i],
];
export const instrumentNames = INSTRUMENTS.map(([n]) => n);
export function instrumentsOf(p: Paper): string[] {
  const text = `${p.title} ${p.abstract}`;
  return INSTRUMENTS.filter(([, re]) => re.test(text)).map(([n]) => n);
}

import { results } from "../data/results";

const plain = (s: string) => s.replace(/<[^>]*>/g, "").replace(/\s+/g, " ").trim();
/**
 * One-line result for a group-led paper. Each line in data/results.ts must be a
 * verbatim piece of the paper's ADS abstract; the build fails if it is not.
 */
export function resultOf(p: Paper): string | null {
  const r = (results as Record<string, string>)[p.bibcode];
  if (!r) return null;
  const core = r.replace(/^…|…$/g, "");
  if (!plain(p.abstract).includes(core)) throw new Error(`results.ts: line for ${p.bibcode} is not in its abstract`);
  return r;
}
