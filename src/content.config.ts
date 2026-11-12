import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";

const people = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/people" }),
  schema: z.object({
    name: z.string(),
    role: z.string(),
    focus: z.string(),
    order: z.number(),
    // Placeholder entry: shown with a MOCK tag, never with a real-looking face.
    mock: z.boolean().default(false),
    photo: z.string().optional(),
    links: z.array(z.object({ label: z.string(), href: z.url() })).default([]),
  }),
});

const projects = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/projects" }),
  schema: z.object({
    title: z.string(),
    code: z.string(),
    summary: z.string(),
    order: z.number(),
    image: z.string(),
    instruments: z.array(z.string()),
    // ADS bibcodes of the published papers behind this line of work.
    papers: z.array(z.string()).default([]),
    // Work in progress, shown as COMING SOON until Dana approves it.
    upcoming: z.array(z.object({ title: z.string(), note: z.string() })).default([]),
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
    mock: z.boolean().default(false),
  }),
});

export const collections = { people, projects, news };
