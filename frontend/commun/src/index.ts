/**
 * Le socle partagé par la boutique et la console d'administration.
 *
 * Il existe pour une raison précise : dupliquer le client API et la gestion
 * de session dans deux dossiers garantirait qu'ils divergent, et une
 * divergence sur l'authentification ne se voit qu'en production.
 *
 * Les applications importent par chemin (`@commun/api/client`) plutôt que
 * par ce fichier : l'outil de construction n'embarque alors que ce qui est
 * réellement utilisé.
 */

export * from "./api/client";
export * from "./api/types";
export * from "./composants/logos";
export * from "./composants/ui";
export * from "./contexte/Session";
export * from "./outils/formats";
export * from "./outils/requetes";
