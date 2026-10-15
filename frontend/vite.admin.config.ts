import { defineConfig, type Connect, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

/**
 * La configuration de **l'administration** — ecran A1, port 5174.
 *
 * Elle est separee de `vite.config.ts` pour une raison que Vite impose : un
 * serveur de developpement, un port. Plusieurs pages dans une meme
 * configuration se partagent le meme port, et c'est precisement ce qu'on ne
 * veut pas ici — voir l'en-tete de `src/admin/main.tsx` pour les trois raisons
 * de separer l'outil interne de la boutique.
 *
 * | | Boutique | Administration |
 * |---|---|---|
 * | Configuration | `vite.config.ts` | **ce fichier** |
 * | Port | 5173 | **5174** |
 * | Page | `index.html` | `admin.html` |
 * | Construction | `dist/` | **`dist-admin/`** |
 * | Publics | Acheteur, groupeur, livreur | Administrateur |
 *
 * ⚠️ **Un port different n'authentifie personne.** Cette page s'ouvre encore
 * sans mot de passe, et elle le fera jusqu'a ce que l'authentification soit
 * branchee. La separation reduit la surface exposee et permet deux regles de
 * pare-feu distinctes ; elle ne remplace pas un controle d'acces. Le vrai
 * controle est celui de l'admin Django (§13.6), qui demande un compte.
 */

/**
 * Sert `admin.html` a la racine du port 5174.
 *
 * **Sans ce reecriveur, `http://localhost:5174/` affichait la boutique.** La
 * racine du projet reste `frontend/` — il le faut, pour que `/src/...`,
 * `src/index.css` et les logos partages se resolvent — et Vite y trouve
 * `index.html` avant `admin.html`. Le port de l'administration servait donc la
 * page du public, ce qui vidait la separation de son sens.
 *
 * Le middleware est installe **avant** ceux de Vite (c'est l'effet d'un
 * `use()` appele directement dans `configureServer`, sans renvoyer de
 * fonction) : la reecriture a lieu pendant que la requete vaut encore `/`.
 */
function servirAdminALaRacine(): Plugin {
  /* `Connect.NextHandleFunction` est le type que Vite expose pour ses propres
     middlewares : il evite d'ajouter `@types/node` au projet pour une
     signature. Le meme reecriveur sert au serveur de developpement et a celui
     de `preview`, qui sert `dist-admin/` ou le fichier s'appelle toujours
     `admin.html`. */
  const reecriveur: Connect.NextHandleFunction = (requete, _reponse, suivant) => {
    const chemin = requete.url?.split("?")[0] ?? "/";

    /*
     * ⚠️ **Toute demande de PAGE va sur `admin.html`, pas seulement `/`.**
     *
     * La premiere version ne reecrivait que `/` et `/index.html`. Le reste
     * tombait dans le repli SPA de Vite, qui sert `index.html` — et
     * `frontend/index.html` **est la boutique**. Resultat mesure :
     * `http://localhost:5174/nimportequoi` affichait l'application publique
     * depuis le port de l'administration, ce qui defait la separation que ce
     * fichier est cense etablir.
     *
     * Le test « ce chemin a-t-il une extension ? » distingue une page d'un
     * fichier : `/dossiers` est une page, `/assets/admin-x.js` un fichier.
     * C'est grossier mais suffisant ici — l'administration n'a aucune adresse
     * profonde (voir `src/admin/main.tsx`), donc la seule page legitime est
     * `admin.html` elle-meme.
     */
    /*
     * ⚠️ **Les chemins internes de Vite passent sans etre reecrits.**
     *
     * Sans cette exclusion, `/@vite/client` — dernier segment `client`, pas de
     * point — etait pris pour une page et renvoye vers `admin.html`. Vite
     * recevait alors du HTML la ou il attendait un module JavaScript, et
     * echouait a l'analyse d'import : **le serveur de developpement de
     * l'administration ne demarrait plus du tout**, avec un message parlant
     * d'« invalid JS syntax » dans un fichier `.html` — qui ne designe pas la
     * cause.
     *
     * Le meme piege guette `/@fs/`, `/@id/` et le client de rechargement a
     * chaud. Tous commencent par `/@`, sauf le repertoire des dependances
     * pre-bundlees.
     */
    const estInterneAVite =
      chemin.startsWith("/@") || chemin.startsWith("/node_modules/");

    const dernierSegment = chemin.slice(chemin.lastIndexOf("/") + 1);
    const estUnFichier = dernierSegment.includes(".");
    if (!estInterneAVite && (!estUnFichier || chemin === "/index.html")) {
      requete.url = "/admin.html";
    }
    suivant();
  };

  return {
    name: "groupachat-admin-a-la-racine",
    configureServer(serveur) {
      serveur.middlewares.use(reecriveur);
    },
    configurePreviewServer(serveur) {
      serveur.middlewares.use(reecriveur);
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
   * `VITE_` : `POSTGRES_PASSWORD`, `DJANGO_SECRET_KEY` et `JETON_ADMIN` sont
   * lues puis ignorees. C'est verifie par une recherche de leurs valeurs dans
   * `dist/` apres construction, pas suppose.
   */
  envDir: "..",

  plugins: [react(), tailwindcss(), servirAdminALaRacine()],

  /**
   * Un dossier public **a part**, et c'est necessaire depuis que le site de
   * presentation vit dans `public/presentation/`.
   *
   * Vite recopie tout `publicDir` tel quel a la racine du paquet. Avec le
   * `public/` par defaut, l'administration embarquerait donc le site de
   * presentation en entier — pres de 100 ko de pages marketing dans un outil
   * interne, et `http://localhost:5174/presentation/` servirait la vitrine
   * depuis le port de l'administration.
   *
   * `public-admin/` ne contient que ce dont `admin.html` a reellement
   * besoin : le favicon.
   */
  publicDir: "public-admin",

  /**
   * ⚠️ **Son propre cache de dependances, et c'est indispensable.**
   *
   * Par defaut, Vite pre-construit les dependances dans
   * `node_modules/.vite/deps`, **le meme dossier pour les deux
   * configurations**. Or il y ecrit aussi l'empreinte de la configuration qui
   * les a produites : quand les deux serveurs de developpement tournent
   * ensemble — et ils tournent toujours ensemble — le second constate que
   * l'empreinte a change, re-optimise, et reecrit le dossier partage.
   *
   * Le premier continue alors de reclamer des fichiers portant l'ancienne
   * empreinte (`?v=b5b293f5`), que le serveur ne connait plus : il repond
   * **504 Outdated Optimize Dep**, le module n'arrive jamais, et la page reste
   * **entierement blanche**. Rien dans le terminal ne le signale, et le
   * symptome ressemble a une panne du code.
   *
   * Un dossier par application, et les deux cessent de se marcher dessus.
   */
  cacheDir: "node_modules/.vite-admin",

  build: {
    /**
     * Le paquet de l'administration, a part. Sans cette ligne, `vite build`
     * construirait `index.html` et l'administration se retrouverait melee a la
     * boutique — ce que la separation cherche justement a eviter.
     */
    rollupOptions: { input: "admin.html" },
    outDir: "dist-admin",

    /* Meme raison que dans `vite.config.ts` : les SVG du logo pesent environ
       10 ko, au-dessus de la limite par defaut de 4 ko. */
    assetsInlineLimit: 12 * 1024,
  },

  server: {
    /**
     * 5174 — le port suivant celui de la boutique. Fixe, et non laisse au
     * hasard du premier port libre : un administrateur qui ouvre son ecran
     * chaque matin doit pouvoir mettre l'adresse dans ses favoris, et un port
     * qui glisse d'un lancement a l'autre rend ce favori faux.
     */
    port: 5174,
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
    /**
     * `strictPort` : s'arreter plutot que de glisser silencieusement sur 5175.
     * Sans lui, lancer deux fois l'administration par distraction donne deux
     * serveurs sur deux ports, et on passe un moment a se demander lequel on
     * regarde.
     */
    strictPort: true,
  },

  preview: { port: 5174, strictPort: true },
});
