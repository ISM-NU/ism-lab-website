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
