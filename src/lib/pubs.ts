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

/** Short citation as written in running text: "Alina et al. 2023", "Alina & Umirbayeva 2025", "Alina 2026". */
export function shortCite(p: Paper): string {
  const s = p.authors.map((a) => a.split(",")[0]);
  const who = s.length === 1 ? s[0] : s.length === 2 ? `${s[0]} & ${s[1]}` : `${s[0]} et al.`;
  return `${who} ${p.year}`;
}

export function link(p: Paper): string {
  if (p.doi) return `https://doi.org/${p.doi}`;
  if (p.arxiv) return `https://arxiv.org/abs/${p.arxiv}`;
  return `https://ui.adsabs.harvard.edu/abs/${encodeURIComponent(p.bibcode)}`;
}

export function venue(p: Paper): string {
  // An e-print's page is its arXiv id, which the list already links.
  const page = p.arxiv && p.page === `arXiv:${p.arxiv}` ? null : p.page;
  return [p.pub, p.volume, page].filter(Boolean).join(", ");
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

/** Research lines: the projects' `papers` lists, passed in by the page. */
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

export type Collaborator = { name: string; affiliation: string; href: string; orcid: boolean; papers: number };

/** "Bernard, J.-Ph", "Bernard, Jean-Philippe" and "Bernard, J.-P." are one person: surname plus first initial. */
const personKey = (a: string) => {
  const [last, first = ""] = a.split(",").map((s) => s.trim());
  const plain = (x: string) => x.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  return `${plain(last)} ${plain(first).replace(/[^a-z]/g, "").slice(0, 1)}`;
};

/** The institution from an ADS affiliation string: in the first affiliation, a university if
 *  there is one, else an observatory, else an institute or similar body, else the first part. */
const RANK = [/univ/i, /observ/i, /institut|max planck|CNRS|CEA\b|NAOJ|KASI|ESO\b/i, /laborat|cent(er|re)|college|academ|agency|national/i];
function institution(aff: string): string {
  // Postal codes sometimes lead a part ("00014 University of Helsinki").
  const parts = aff.split(";")[0].split(",").map((s) => s.trim().replace(/^[A-Z]{0,2}-?\d[\d -]*\s+/, "")).filter(Boolean);
  for (const re of RANK) {
    const hit = parts.find((s) => re.test(s));
    if (hit) return hit;
  }
  return parts[0] ?? "";
}

/** "Matsumura, Tomotake Matsumura" (an ADS slip) and "Lazarian, A." to display names; the fullest spelling wins. */
function displayName(spellings: string[]): string {
  const full = spellings.reduce((a, b) => (b.length > a.length ? b : a));
  const [last, first = ""] = full.split(",").map((s) => s.trim());
  const given = first.replace(new RegExp(`\\s+${last}$`), "");
  return given ? `${given} ${last}` : last;
}

/** Per person, across every paper (newest first): all spellings, the first ORCID and affiliation found. */
const directory = new Map<string, { names: string[]; aff: string; orcid: string | null }>();
for (const p of [...papers].filter((p) => p.authors.length < BIG_COLLAB).sort((a, b) => b.year - a.year)) {
  p.authors.forEach((a, i) => {
    const k = personKey(a);
    const e = directory.get(k) ?? { names: [], aff: "", orcid: null };
    e.names.push(a);
    const aff = p.aff?.[i];
    if (!e.aff && aff && aff !== "-") e.aff = institution(aff);
    e.orcid ??= p.orcid?.[i] ?? null;
    directory.set(k, e);
  });
}

/**
 * Co-authors on the group-led papers among `bibcodes`, minus current and former
 * members (`memberNames`, "First Last"). One entry per person, most shared papers
 * first. Name, affiliation and ORCID come from all our papers, newest first, so a
 * person reads the same on every project page. Without an ORCID the link is the
 * person's NASA ADS author search.
 */
export function collaborators(bibcodes: string[], memberNames: string[]): Collaborator[] {
  const members = new Set(memberNames.map((n) => { const w = n.split(/\s+/); return personKey(`${w.at(-1)}, ${w[0]}`); }));
  const count = new Map<string, number>();
  for (const p of bibcodes.map((b) => byBibcode.get(b)).filter((p): p is Paper => !!p?.led)) {
    for (const k of new Set(p.authors.map(personKey))) if (!members.has(k)) count.set(k, (count.get(k) ?? 0) + 1);
  }
  return [...count]
    .map(([k, n]) => {
      const e = directory.get(k)!;
      const name = displayName(e.names);
      const [last, first = ""] = e.names[0].split(",").map((s) => s.trim());
      const initial = first.normalize("NFD").replace(/[^A-Za-z]/g, "").slice(0, 1);
      return {
        name,
        affiliation: e.aff,
        orcid: !!e.orcid,
        href: e.orcid
          ? `https://orcid.org/${e.orcid}`
          : adsAuthor(last, initial),
        papers: n,
      };
    })
    .sort((a, b) => b.papers - a.papers || a.name.split(" ").at(-1)!.localeCompare(b.name.split(" ").at(-1)!));
}

/** NASA ADS author search for "Surname, Initial". */
const adsAuthor = (last: string, initial: string) =>
  `https://ui.adsabs.harvard.edu/search/q=${encodeURIComponent(`author:"${last}, ${initial}"`)}`;

/**
 * Profile links for a member ("First Last") who appears on any of our papers:
 * ORCID when ADS has it, and their NASA ADS author search. Empty for members
 * with no papers yet.
 */
export function profileLinks(name: string): { label: string; href: string }[] {
  const w = name.split(/\s+/);
  const e = directory.get(personKey(`${w.at(-1)}, ${w[0]}`));
  if (!e) return [];
  const [last, first = ""] = e.names[0].split(",").map((s) => s.trim());
  const initial = first.normalize("NFD").replace(/[^A-Za-z]/g, "").slice(0, 1);
  return [...(e.orcid ? [{ label: "ORCID", href: `https://orcid.org/${e.orcid}` }] : []), { label: "NASA ADS", href: adsAuthor(last, initial) }];
}
