import type { CollectionEntry } from "astro:content";
import { profileLinks } from "./pubs";

type Person = CollectionEntry<"people">;

/**
 * Two-letter initials, widened with the next letter of the surname when two
 * people would share them (Dana Alina and Denis Andreyev are both "DA").
 */
export function initials(name: string, everyone: string[]): string {
  const two = (n: string) => n.split(/\s+/).map((w) => w[0]).join("").slice(0, 2).toUpperCase();
  const w = name.split(/\s+/);
  const clash = everyone.filter((n) => two(n) === two(name)).length > 1;
  return clash ? (w[0][0] + w.at(-1)!.slice(0, 2)).toUpperCase() : two(name);
}

/** NU addresses follow name.surname@nu.edu.kz. Alumni lose theirs, so they get none. */
export function email(p: Person): string | null {
  if (p.data.alumni) return null;
  return `${p.data.name.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").split(/\s+/).join(".")}@nu.edu.kz`;
}

/** Email, then ORCID and NASA ADS for anyone on our papers, then the person's own links. */
export function personLinks(p: Person): { label: string; href: string }[] {
  const e = email(p);
  return [...(e ? [{ label: e, href: `mailto:${e}` }] : []), ...profileLinks(p.data.name), ...p.data.links];
}

export const personHref = (id: string) => `/people/${id}/`;
