// @ts-check
import { defineConfig } from "astro/config";

export default defineConfig({
  // Set when the domain is known; used for canonical URLs and the sitemap.
  site: "http://localhost:4321",
  trailingSlash: "ignore",
  prefetch: { prefetchAll: true },
});
