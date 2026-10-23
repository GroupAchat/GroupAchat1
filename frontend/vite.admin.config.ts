import { fileURLToPath, URL } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

/**
 * La **boutique** — acheteur et groupeur — sur le port 5174.
 *
 * L'administration a sa propre configuration, `vite.admin.config.ts`, sur le
 * port 5174 : Vite n'ouvre qu'un port par serveur, deux ports demandent donc
 * deux configurations. Ce n'est pas une duplication gratuite.
 *
 * `envDir: ".."` : il n'y a **qu'un** `.env`, à la racine du dépôt, celui que
 * lisent aussi Django et Docker Compose.
 */
export default defineConfig({
  plugins: [react(), tailwindcss()],
  envDir: "..",
  cacheDir: "node_modules/.vite-admin",
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  server: {
    port: 5174,
    // Le navigateur parle à la boutique, la boutique relaie vers Django : les
    // deux partagent alors la même origine, et le cookie de session suit sans
    // réglage CORS particulier en développement.
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/medias": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
  build: { outDir: "dist-admin", rollupOptions: { input: "admin.html" } },
});
