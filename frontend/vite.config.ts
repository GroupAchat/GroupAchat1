import { fileURLToPath, URL } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

/**
 * La **boutique** — acheteurs et groupeurs — sur le port 5173.
 *
 * La console d'administration est un dossier à part, `admin/`, avec sa
 * propre configuration et son propre port. Ce qu'elles partagent vit dans
 * `commun/` : client API, session, trousse d'interface. Le socle n'existe
 * donc qu'en un exemplaire, et une correction sur l'authentification profite
 * aux deux sans qu'on ait à y penser.
 *
 * `envDir` : il n'y a **qu'un** `.env`, à la racine du dépôt — celui que
 * lisent aussi Django et Docker Compose.
 */
export default defineConfig({
  plugins: [react(), tailwindcss()],
  envDir: "..",

  // Les logos sont servis depuis le socle : une seule marque, déposée une
  // seule fois, pour les deux applications.
  publicDir: fileURLToPath(new URL("../commun/public", import.meta.url)),

  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      "@commun": fileURLToPath(new URL("../commun/src", import.meta.url)),
    },
  },

  server: {
    port: 5173,
    // Le navigateur parle à la boutique, la boutique relaie vers Django :
    // les deux partagent alors la même origine, et le cookie de session suit
    // sans réglage CORS particulier en développement.
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/medias": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/pieces": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },

  build: { outDir: "dist" },
});
