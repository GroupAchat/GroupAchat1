import { defineConfig, type Connect, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

/**
 * La configuration de **la boutique** — acheteur, groupeur, livreur, port 5173.
 *
 * L'administration a la sienne, `vite.admin.config.ts`, sur le port 5174. Vite
 * n'ouvre qu'un port par serveur de developpement, donc deux ports demandent
 * deux configurations : ce n'est pas une duplication gratuite.
 *
 * | | Boutique | Administration |
 * |---|---|---|
 * | Configuration | **ce fichier** | `vite.admin.config.ts` |
 * | Port | **5173** | 5174 |
 * | Page | `index.html` | `admin.html` |
 * | Construction | **`dist/`** | `dist-admin/` |
 */

/**
 * Refuse `/admin.html` sur le port de la boutique.
 *
 * La racine du projet contient les deux pages, et le serveur de Vite sert tout
 * ce qu'il y trouve : **sans ce garde, `http://localhost:5173/admin.html`
 * affichait l'administration.** La separation des ports n'aurait alors rien
 * separe du tout en developpement — il aurait suffi de connaitre le nom du
 * fichier.
 *
 * Ce n'est toujours **pas une mesure de securite** : l'administration reste
 * ouverte sans mot de passe sur son propre port. Ce garde sert a ce que la
 * frontiere soit vraie la ou on l'a dessinee, pour qu'on ne se fie pas a une
 * separation qui n'existe pas.
 */
/**
 * Sert `public/presentation/index.html` pour `/presentation` et
 * `/presentation/`.
 *
 * ⚠️ **Sans ce reecriveur, `/presentation/` affichait la boutique.** Vite sert
 * bien les fichiers de `publicDir` un par un — `/presentation/styles.css`
 * fonctionne — mais il **ne resout pas l'index d'un repertoire** : la demande
 * tombe alors dans le repli SPA, qui renvoie `index.html`, c'est-a-dire
 * l'application. Seul `/presentation/index.html`, ecrit en entier, marchait.
 *
 * Ce defaut n'existe qu'en developpement : en production, le
 * un serveur statique resout l'index tout seul. ⚠️ Cette phrase citait
 * `try_files $uri $uri/` de `nginx.boutique.conf` : ce fichier a ete
 * supprime avec nginx, le deploiement passant par Coolify.
 */
function servirLaPresentation(): Plugin {
  const reecriveur: Connect.NextHandleFunction = (requete, _reponse, suivant) => {
    const chemin = requete.url?.split("?")[0];
    if (chemin === "/presentation" || chemin === "/presentation/") {
      requete.url = "/presentation/index.html";
    }
    suivant();
  };

  return {
    name: "groupachat-servir-la-presentation",
    configureServer(serveur) {
      serveur.middlewares.use(reecriveur);
    },
    configurePreviewServer(serveur) {
      serveur.middlewares.use(reecriveur);
    },
  };
}

function masquerAdmin(): Plugin {
  const MESSAGE =
    "Introuvable. L'administration est servie sur le port 5174 : npm run dev:admin\n";

  /* `Connect.NextHandleFunction` est le type que Vite expose pour ses propres
     middlewares : il evite d'ajouter `@types/node` au projet pour deux
     signatures, et le meme garde sert au serveur de developpement comme a
     celui de `preview`. */
  const garde: Connect.NextHandleFunction = (requete, reponse, suivant) => {
    /* `split("?")` : `/admin.html?v=3` doit etre refuse comme `/admin.html`. */
    if (requete.url?.split("?")[0] === "/admin.html") {
      reponse.statusCode = 404;
      reponse.end(MESSAGE);
      return;
    }
    suivant();
  };

  return {
    name: "groupachat-masquer-admin",
    configureServer(serveur) {
      serveur.middlewares.use(garde);
    },
    configurePreviewServer(serveur) {
      serveur.middlewares.use(garde);
    },
  };
}

export default defineConfig({
  /**
   * Le `.env` de la racine du depot, le meme que Docker Compose et Django.
   *
   * Par defaut Vite cherche ses `.env` dans `frontend/`. Il y avait donc un
   * `frontend/.env.local` a cote de `backend/.env` et de `.env` — trois
   * fichiers pour les memes valeurs, et `VITE_API_URL` devait rester d'accord
   * avec le `CORS_ORIGINES` d'un autre fichier sans que rien ne le verifie.
   *
   * ⚠️ **Ce fichier contient des secrets, et ils ne partent pas dans le
   * paquet.** Vite n'expose a `import.meta.env` que les variables prefixees
   * `VITE_` : `POSTGRES_PASSWORD`, `DJANGO_SECRET_KEY` et `ADMIN_MOT_DE_PASSE` sont
   * lues puis ignorees. C'est verifie par une recherche de leurs valeurs dans
   * `dist/` apres construction, pas suppose.
   */
  envDir: "..",

  plugins: [react(), tailwindcss(), masquerAdmin(), servirLaPresentation()],

  build: {
    /**
     * **Explicite, et c'est le point de toute la separation.** Sans cette
     * ligne, `vite build` ramasserait aussi `admin.html` present a la racine,
     * et le code d'administration — montants detenus, files de travail,
     * libelles d'alertes — partirait dans la construction publique. Nommer
     * l'entree garantit que le paquet telecharge par un acheteur de Lome, sur
     * un forfait de donnees limite, n'en contient pas une ligne.
     */
    rollupOptions: { input: "index.html" },

    /**
     * Les quatre SVG du logo pesent environ 10 ko chacun, au-dessus de la
     * limite par defaut de 4 ko. On la releve pour qu'ils soient integres au
     * paquet sous forme de donnees plutot que servis comme fichiers : le logo
     * s'affiche alors avec la page, sans requete supplementaire.
     *
     * C'est ce qui compte pour la page de demarrage — un ecran de lancement
     * qui attend une requete reseau pour montrer le logo est un ecran vide.
     * Du SVG en base64 se compresse tres bien, donc le cout reel est faible.
     */
    assetsInlineLimit: 12 * 1024,
  },

  /**
   * ⚠️ **`qrcode-generator` doit etre pre-bundle au demarrage.**
   *
   * Vite ne pre-bundle d'emblee que les dependances qu'il trouve en partant de
   * l'entree. Celle-ci n'est importee que par l'ecran du code de livraison —
   * atteint apres un paiement — donc il la decouvre **en cours de session**,
   * re-bundle, et invalide les modules deja servis. La page en cours recoit
   * alors un `504 Outdated Optimize Dep` et reste blanche jusqu'a un
   * rechargement.
   *
   * C'est sans consequence quand on developpe a la main — on recharge sans y
   * penser — et c'est bloquant pour un test automatise, qui ne recharge pas.
   * La declarer ici la fait pre-bundler avec les autres, une fois, au
   * demarrage.
   */
  optimizeDeps: { include: ["qrcode-generator"] },

  server: {
    port: 5173,
    /**
     * ⚠️ **`ignored` REMPLACE les exclusions par defaut, il ne s'y ajoute
     * pas.**
     *
     * C'est le piege de cette option, et il a coute trois pannes. Le probleme
     * de depart etait reel : `dist/` et `dist-admin/` sont **sous la racine du
     * projet**, donc le surveillant les regarde, et un `npm run build` lance
     * pendant que le serveur tourne y reecrit des centaines de fichiers d'un
     * coup — le journal se remplit de « page reload dist/index.html ».
     *
     * Mais la premiere correction n'a mis que ces deux motifs dans `ignored`,
     * **ce qui a efface les exclusions que Vite pose par defaut** — dont
     * celle de `node_modules`. Le surveillant s'est donc mis a suivre
     * recursivement `node_modules`, soit des dizaines de milliers de fichiers,
     * chacun coutant un descripteur. Les deux serveurs mouraient ensemble,
     * code 1 et sans message, des que quelque chose touchait beaucoup de
     * fichiers a la fois. Le remede etait devenu la maladie, en pire : le
     * symptome etait le meme, donc on cherchait au mauvais endroit.
     *
     * D'ou la liste complete ci-dessous. **Les trois premieres entrees sont les
     * defauts de Vite** : les retirer casse tout, les garder ne coute rien.
     * Les deux dernieres sont le besoin reel.
     *
     * ⚠️ **Ne jamais ecrire un motif glob dans ce commentaire.** Un glob
     * recursif se termine par deux etoiles suivies d'une barre oblique, et
     * cette sequence **ferme le commentaire de bloc** : le fichier devient
     * invalide, et Vite refuse de demarrer sur un « Expected } ». C'est
     * exactement ce qui est arrive en ecrivant le motif de node_modules ici.
     * Les motifs vivent dans le tableau ci-dessous, nulle part ailleurs.
     */
    watch: {
      ignored: [
        "**/.git/**",
        "**/node_modules/**",
        "**/test-results/**",
        "**/dist/**",
        "**/dist-admin/**",
      ],
    },
    /* S'arreter plutot que de glisser silencieusement sur 5174 — ou vit
       l'administration. Sans `strictPort`, un 5173 deja occupe ferait demarrer
       la boutique sur le port de l'administration, et on passerait un moment a
       se demander pourquoi les deux se marchent dessus. */
    strictPort: true,
  },

  preview: { port: 5173, strictPort: true },
});
