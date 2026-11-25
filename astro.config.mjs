// @ts-check
import { defineConfig } from "astro/config";

export default defineConfig({
  // Set to the public URL when the domain is live. Link previews need absolute
  // URLs, and the og:image tag in Base.astro is built from this.
  site: "http://localhost:4321",
  trailingSlash: "ignore",
  prefetch: { prefetchAll: true },
});
