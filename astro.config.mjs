// @ts-check
import { defineConfig } from "astro/config";

export default defineConfig({
  // Placeholder until the domain's DNS record exists. Set it to the public URL
  // then: Base.astro emits an absolute og:image only when this is not localhost,
  // so a build with the placeholder never publishes a localhost link.
  site: "http://localhost:4321",
  trailingSlash: "ignore",
  prefetch: { prefetchAll: true },
});
