import { getCollection } from "astro:content";

/** News items to show, newest first. `mock: true` items are templates and stay hidden. */
export const getNews = async () =>
  (await getCollection("news", (n) => !n.data.mock)).sort((a, b) => +b.data.date - +a.data.date);
