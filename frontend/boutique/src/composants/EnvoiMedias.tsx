import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, ImagePlus, Loader2, Play, X } from "lucide-react";
import { useRef, useState } from "react";

import { Bouton, fusionner } from "@commun/composants/ui";
import {
  MAX_OCTETS_IMAGE,
  MAX_OCTETS_VIDEO,
  genreDuFichier,
  refuserLeFichier,
  televerser,
  type Cible,
} from "@commun/outils/televersement";

/**
 * La galerie d'un produit, remplie depuis le téléphone du groupeur.
 *
 * **Les fichiers partent chez Cloudinary tout de suite**, sans attendre
 * l'enregistrement du formulaire : une vidéo met une minute à monter sur un
 * réseau lent, et la faire partir seulement au moment de valider donnerait
 * l'impression que le bouton ne répond plus. Ce qui remonte ensuite à l'API
 * n'est qu'une liste d'identifiants.
 *
 * Trois photos et deux vidéos : le plafond est tenu côté serveur, mais il
 * faut le dire ici aussi, sinon le groupeur envoie quatre photos avant
 * d'apprendre que la dernière est refusée.
 */

export const MAX_IMAGES = 3;
export const MAX_VIDEOS = 2;

export interface MediaEnAttente {
  /** Identifiant local, le temps de l'envoi : la liste doit se rendre. */
  cle: string;
  genre: "image" | "video";
  /** Vignette locale, affichée pendant que le fichier monte. */
  apercuLocal: string;
  public_id?: string;
  progression: number;
  erreur?: string;
}

export function EnvoiMedias({
  valeur,
  surChangement,
  cible = "produit",
  imagesSeules,
  plafondImages = MAX_IMAGES,
  intitule = "Photos et vidéos",
}: {
  valeur: MediaEnAttente[];
  surChangement: (medias: MediaEnAttente[]) => void;
  cible?: Cible;
  /** Les photos du lot ne se filment pas : il s'agit de prouver qu'on a la
      marchandise, pas de la mettre en scène. */
  imagesSeules?: boolean;
  plafondImages?: number;
  intitule?: string;
}) {
  const champ = useRef<HTMLInputElement>(null);
  const [refus, setRefus] = useState<string | null>(null);

  // La liste vit dans le parent, mais chaque envoi se termine de façon
  // asynchrone : on la relit au dernier moment plutôt que de capturer une
  // version périmée dans la fermeture.
  const liste = useRef(valeur);
  liste.current = valeur;

  const compte = (genre: "image" | "video") =>
    valeur.filter((media) => media.genre === genre).length;

  const ajouter = async (fichiers: FileList) => {
    setRefus(null);
    for (const fichier of Array.from(fichiers)) {
      const souci = refuserLeFichier(fichier);
      if (souci) {
        setRefus(souci);
        continue;
      }
      const genre = genreDuFichier(fichier)!;
      if (imagesSeules && genre === "video") {
        setRefus("Ici, seulement des photos.");
        continue;
      }
      const plafond = genre === "video" ? MAX_VIDEOS : plafondImages;
      if (compte(genre) >= plafond) {
        setRefus(
          genre === "video"
            ? `${MAX_VIDEOS} vidéos au maximum.`
            : `${plafondImages} photos au maximum.`,
        );
        continue;
      }

      const cle = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      const apercuLocal = URL.createObjectURL(fichier);
      const entree: MediaEnAttente = { cle, genre, apercuLocal, progression: 0 };
      surChangement([...liste.current, entree]);

      const remplacer = (champs: Partial<MediaEnAttente>) =>
        surChangement(
          liste.current.map((media) =>
            media.cle === cle ? { ...media, ...champs } : media,
          ),
        );

      try {
        const envoye = await televerser(fichier, cible, (pourcentage) =>
          remplacer({ progression: pourcentage }),
        );
        remplacer({ public_id: envoye.public_id, progression: 100 });
      } catch (souci) {
        remplacer({
          erreur: souci instanceof Error ? souci.message : "Envoi impossible.",
        });
      }
    }
    if (champ.current) champ.current.value = "";
  };

  const retirer = (cle: string) => {
    const media = valeur.find((un) => un.cle === cle);
    if (media) URL.revokeObjectURL(media.apercuLocal);
    surChangement(valeur.filter((un) => un.cle !== cle));
  };

  const complet = imagesSeules
    ? compte("image") >= plafondImages
    : compte("image") >= plafondImages && compte("video") >= MAX_VIDEOS;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-sm font-medium">{intitule}</p>
        <p className="texte-doux tabulaire text-xs">
          {compte("image")}/{plafondImages} photos
          {!imagesSeules && ` · ${compte("video")}/${MAX_VIDEOS} vidéos`}
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <AnimatePresence initial={false}>
          {valeur.map((media) => (
            <motion.div
              key={media.cle}
              layout
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className={fusionner(
                "surface relative size-24 overflow-hidden rounded-2xl",
                media.erreur && "border-red-500",
              )}
            >
              <img
                src={media.apercuLocal}
                alt=""
                className="size-full object-cover"
              />

              {media.genre === "video" && !media.erreur && (
                <span className="verre-sombre absolute bottom-1 left-1 grid size-6 place-items-center rounded-full text-white">
                  <Play className="size-3" fill="currentColor" />
                </span>
              )}

              {/* Pendant la montée : un voile et le pourcentage. Une barre
                  seule, sur une vignette de 96 pixels, serait illisible. */}
              {!media.public_id && !media.erreur && (
                <div className="absolute inset-0 grid place-items-center bg-black/55 text-white">
                  <Loader2 className="size-5 animate-spin" />
                  <span className="tabulaire text-xs font-bold">
                    {media.progression}%
                  </span>
                </div>
              )}

              {media.erreur && (
                <div className="absolute inset-0 grid place-items-center bg-red-900/70 p-1 text-center text-white">
                  <AlertTriangle className="size-5" />
                  <span className="text-[0.6rem] leading-tight">{media.erreur}</span>
                </div>
              )}

              <button
                type="button"
                onClick={() => retirer(media.cle)}
                className="verre-sombre absolute right-1 top-1 grid size-6 place-items-center rounded-full text-white"
                aria-label="Retirer ce média"
              >
                <X className="size-3.5" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>

        {!complet && (
          <button
            type="button"
            onClick={() => champ.current?.click()}
            className="texte-doux grid size-24 place-items-center rounded-2xl border-2 border-dashed transition-colors hover:border-[color:var(--color-accent)] hover:text-[color:var(--color-accent)]"
          >
            <ImagePlus className="size-6" />
            <span className="text-xs font-semibold">Ajouter</span>
          </button>
        )}
      </div>

      <input
        ref={champ}
        type="file"
        accept={imagesSeules ? "image/*" : "image/*,video/*"}
        multiple
        className="hidden"
        onChange={(evenement) => {
          if (evenement.target.files) void ajouter(evenement.target.files);
        }}
      />

      {refus && <p className="text-sm text-red-600">{refus}</p>}

      <p className="texte-doux text-xs">
        {imagesSeules ? (
          <>Photos jusqu'à {Math.round(MAX_OCTETS_IMAGE / 1048576)} Mo.</>
        ) : (
          <>
            Photos jusqu'à {Math.round(MAX_OCTETS_IMAGE / 1048576)} Mo, vidéos
            jusqu'à {Math.round(MAX_OCTETS_VIDEO / 1048576)} Mo. L'image figée
            d'une vidéo est extraite automatiquement.
          </>
        )}
      </p>
    </div>
  );
}

/** Les médias prêts à être rattachés : envoyés, sans erreur. */
export function mediasPrets(medias: MediaEnAttente[]) {
  return medias
    .filter((media) => media.public_id && !media.erreur)
    .map((media, rang) => ({
      genre: media.genre,
      public_id: media.public_id!,
      ordre: rang,
    }));
}

/** Un envoi est-il encore en cours ? Le formulaire attend. */
export function envoiEnCours(medias: MediaEnAttente[]) {
  return medias.some((media) => !media.public_id && !media.erreur);
}

export { Bouton };
