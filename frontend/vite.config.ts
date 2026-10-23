import { fileURLToPath, URL } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

/**
 * La **boutique** — acheteur et groupeur — sur le port 5173.
 *
 * L'administration a sa propre configuration, `vite.admin.config.ts`, sur le
 * port 5174 : Vite n'ouvre qu'un port par serveur, deux ports demandent donc
 * deux configurations. Ce n'est pas une duplication gratuite.
 *
 * `envDir: ".."` : il n'y a **qu'un** `.env`, à la racine du dépôt, celui que
 * lisent aussi Django et Docker Compose.
 */
/**
 * Refuse `/admin.html` sur le port de la boutique.
 *
 * ⚠️ **Sans ce garde, `http://localhost:5173/admin.html` affichait la console
 * d'administration** : la racine du projet contient les deux pages, et le
 * serveur de Vite sert tout ce qu'il y trouve. La séparation des ports
 * n'aurait alors rien séparé — il aurait suffi de connaître le nom du
 * fichier.
 *
 * Ce n'est **pas une mesure de sécurité** : c'est l'API qui garde ses routes.
 * Ce garde sert à ce que la frontière soit vraie là où on l'a dessinée, pour
 * qu'on ne se fie pas à une séparation qui n'existerait qu'en production.
 */
function sansAdministration(): Plugin {
  return {
    name: "boutique-sans-administration",
    configureServer(serveur) {
      serveur.middlewares.use((requete, reponse, suite) => {
        if ((requete.url ?? "").split("?")[0].endsWith("/admin.html")) {
          reponse.statusCode = 404;
          reponse.end(
            "L'administration vit sur son propre port : http://localhost:5174/admin.html",
          );
          return;
        }
        suite();
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), tailwindcss(), sansAdministration()],
  envDir: "..",
  // Chaque application son cache de pré-bundling. Par défaut les deux
  // écriraient dans `node_modules/.vite`, et **chacune invaliderait celui de
  // l'autre** : l'onglet resté ouvert demande alors des morceaux qui
  // n'existent plus, ce que Vite signale par un 504 « Outdated Optimize Dep ».
  cacheDir: "node_modules/.vite-boutique",
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  server: {
    port: 5173,
    // Le navigateur parle à la boutique, la boutique relaie vers Django : les
    // deux partagent alors la même origine, et le cookie de session suit sans
    // réglage CORS particulier en développement.
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/medias": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
  build: { outDir: "dist" },
});
