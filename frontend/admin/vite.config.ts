import { fileURLToPath, URL } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

/**
 * La **console d'administration**, sur le port 5174.
 *
 * Un dossier à part, et non une page de plus dans la boutique : la frontière
 * entre les deux est réelle. Ce n'est pas pour autant une mesure de
 * sécurité — c'est l'API qui garde ses routes derrière
 * `EstAdministrateur`. La séparation sert à ce que personne ne se fie à une
 * frontière qui n'existerait que dans le routage du navigateur.
 *
 * Le socle partagé vit dans `commun/` : client API, session, trousse
 * d'interface. La console n'en a donc aucune copie.
 */
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Le `.env` est à la racine du dépôt, deux dossiers plus haut :
  // c'est le même fichier que lisent Django et Docker Compose.
  envDir: "../..",

  publicDir: fileURLToPath(new URL("../commun/public", import.meta.url)),

  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      "@commun": fileURLToPath(new URL("../commun/src", import.meta.url)),
    },
  },

  server: {
    port: 5174,
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/medias": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/pieces": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },

  // Les fichiers compilés des deux applications se rejoignent dans un seul
  // dossier côté image Docker. Le préfixe « admin- » garantit qu'aucun ne
  // vient écraser celui de la boutique.
  build: {
    outDir: "dist",
    rollupOptions: {
      output: {
        entryFileNames: "assets/admin-[hash].js",
        chunkFileNames: "assets/admin-[hash].js",
        assetFileNames: "assets/admin-[hash][extname]",
      },
    },
  },
});
