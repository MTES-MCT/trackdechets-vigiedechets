import { resolve } from "path";

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

export default defineConfig({
  plugins: [react()],
  css: {},
  root: resolve("./src/static/ui_app_ts/src"),
  base: "/static/",
  build: {
    manifest: "manifest.json",
    outDir: resolve("./src/static/ui_app_ts/dist"),
    rollupOptions: {
      input: {
        main: resolve("./src/static/ui_app_ts/src/main.tsx"),
        galaxy: resolve("./src/static/ui_app_ts/src/galaxy.tsx"),
      },
    },
  },
  server: {
    watch: {
      usePolling: true,
      interval: 100, // Polling interval in ms
    },
    hmr: {
      overlay: true,
    },
  },
});
