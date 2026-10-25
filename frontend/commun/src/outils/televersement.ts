import { api } from "@commun/api/client";

/**
 * L'envoi d'un fichier chez Cloudinary, signé par Django.
 *
 * **Le fichier ne passe pas par l'API.** Django signe une autorisation, le
 * navigateur téléverse directement. Sur une connexion togolaise, faire
 * transiter une photo de quatre mégaoctets par le serveur doublerait
 * l'attente — et immobiliserait un travailleur Gunicorn pendant toute la
 * montée, pour ne rien faire d'autre que recopier des octets.
 *
 * `fetch` ne sait pas rendre compte de la progression d'un envoi ; c'est la
 * seule raison pour laquelle `XMLHttpRequest` survit ici. Sans barre de
 * progression, un envoi de vidéo sur réseau lent ressemble à un plantage.
 */

export interface Signature {
  cloud_name: string;
  api_key: string;
  type_ressource: "image" | "video";
  dossier: string;
  horodatage: number;
  signature: string;
  expire_dans: number;
  adresse: string;
}

export interface MediaTeleverse {
  public_id: string;
  format: string;
  largeur: number;
  hauteur: number;
  octets: number;
}

export type Cible = "produit" | "campagne";

/** Plafonds côté navigateur, pour refuser avant d'avoir tout envoyé. */
export const MAX_OCTETS_IMAGE = 10 * 1024 * 1024;
export const MAX_OCTETS_VIDEO = 100 * 1024 * 1024;

export function genreDuFichier(fichier: File): "image" | "video" | null {
  if (fichier.type.startsWith("image/")) return "image";
  if (fichier.type.startsWith("video/")) return "video";
  return null;
}

/** Le message à afficher si le fichier ne convient pas, sinon `null`. */
export function refuserLeFichier(fichier: File): string | null {
  const genre = genreDuFichier(fichier);
  if (!genre) return "Seules les photos et les vidéos sont acceptées.";
  const plafond = genre === "video" ? MAX_OCTETS_VIDEO : MAX_OCTETS_IMAGE;
  if (fichier.size > plafond) {
    const mo = Math.round(plafond / (1024 * 1024));
    return `Ce fichier dépasse ${mo} Mo.`;
  }
  return null;
}

export async function televerser(
  fichier: File,
  cible: Cible,
  surProgression?: (pourcentage: number) => void,
): Promise<MediaTeleverse> {
  const genre = genreDuFichier(fichier);
  if (!genre) throw new Error("Seules les photos et les vidéos sont acceptées.");

  // La signature est demandée juste avant l'envoi, pas au chargement de la
  // page : elle expire, et un formulaire reste parfois ouvert longtemps.
  const signature = await api.post<Signature>("/groupeur/medias/signature/", {
    genre,
    cible,
  });

  const corps = new FormData();
  corps.append("file", fichier);
  corps.append("api_key", signature.api_key);
  corps.append("timestamp", String(signature.horodatage));
  corps.append("signature", signature.signature);
  corps.append("folder", signature.dossier);

  return new Promise((resoudre, rejeter) => {
    const requete = new XMLHttpRequest();
    requete.open("POST", signature.adresse);

    requete.upload.onprogress = (evenement) => {
      if (evenement.lengthComputable && surProgression) {
        surProgression(Math.round((evenement.loaded / evenement.total) * 100));
      }
    };

    requete.onload = () => {
      if (requete.status < 200 || requete.status >= 300) {
        rejeter(new Error("L'envoi a échoué. Réessayez."));
        return;
      }
      const reponse = JSON.parse(requete.responseText);
      resoudre({
        public_id: reponse.public_id,
        format: reponse.format,
        largeur: reponse.width,
        hauteur: reponse.height,
        octets: reponse.bytes,
      });
    };

    requete.onerror = () =>
      rejeter(new Error("Connexion perdue pendant l'envoi."));
    requete.onabort = () => rejeter(new Error("Envoi interrompu."));

    requete.send(corps);
  });
}
