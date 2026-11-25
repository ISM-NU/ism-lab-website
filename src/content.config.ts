import { defineCollection, reference } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";
import { publications } from "./lib/data";
import facts from "./data/facts.json";

const bibcodes = new Set(publications.papers.map((p) => p.bibcode));

const people = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/people" }),
  schema: z.object({
    name: z.string(),
    role: z.string(),
    focus: z.string(),
    order: z.number(),
    // Former member: listed under Alumni on the people page.
    alumni: z.boolean().default(false),
    photo: z.string().optional(),
    links: z.array(z.object({ label: z.string(), href: z.url() })).default([]),
    // Research lines this person works on; ids must exist in src/content/projects.
    // Set only from their own bio or authorship.
    lines: z.array(reference("projects")).default([]),
    // Card text when the full bio (the Markdown body, shown on the person's page) is long.
    short: z.string().optional(),
    // Code, tools and contributions outside the papers. No href for private work.
    work: z.array(z.object({ title: z.string(), note: z.string(), href: z.url().optional() })).default([]),
  }),
});

const projects = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/projects" }),
  schema: z.object({
    title: z.string(),
    code: z.string(),
    summary: z.string(),
    order: z.number(),
    // Optional: a line with no picture yet shows a dot-matrix panel on its card.
    image: z.string().optional(),
    // Says what the header image shows. Without it the header lists `instruments`,
    // which is only right when the image comes from those instruments.
    imageCaption: z.string().optional(),
    // Sky field the card image shows, by its key in `fields` of src/data/facts.json
    // (Galactic centre and width in degrees; the render scripts read the same
    // entry). Shown as a readout on the card.
    field: z.enum(Object.keys(facts.fields) as [keyof typeof facts.fields, ...(keyof typeof facts.fields)[]]).transform((k) => facts.fields[k]).optional(),
    instruments: z.array(z.string()),
    // ADS bibcodes of the published papers behind this line of work.
    papers: z.array(z.string().refine((b) => bibcodes.has(b), { message: "bibcode not in src/data/publications.json" })).default([]),
    // The papers Dana chose to name on the card ("Alina et al. 2023"). Each must
    // also be in `papers`.
    keyPapers: z.array(z.string().refine((b) => bibcodes.has(b), { message: "bibcode not in src/data/publications.json" })).default([]),
    // Published results, each stated as the paper states it. The bibcode must be in
    // publications.json; the source sentence goes in a YAML comment above each item.
    // value: the number with its uncertainty as printed, if the paper gives one.
    // figure: a site-rendered image under /sky/, never a copy of a journal figure.
    findings: z
      .array(
        z.object({
          text: z.string(),
          value: z.string().optional(),
          figure: z.string().optional(),
          bibcode: z.string().refine((b) => bibcodes.has(b), { message: "bibcode not in src/data/publications.json" }),
        }),
      )
      .default([]),
    // Work in progress, shown as COMING SOON until Dana approves it.
    upcoming: z.array(z.object({ title: z.string(), note: z.string() })).default([]),
  }).superRefine((d, ctx) => {
    d.keyPapers.forEach((b, i) => {
      if (!d.papers.includes(b)) ctx.addIssue({ code: "custom", path: ["keyPapers", i], message: "keyPapers entry is not in papers" });
    });
  }),
});

const news = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/news" }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    kind: z.enum(["news", "event"]),
    // Events only.
    where: z.string().optional(),
    registration: z.url().optional(),
    // Template item: kept in the repo, never listed.
    mock: z.boolean().default(false),
  }),
});

export const collections = { people, projects, news };
