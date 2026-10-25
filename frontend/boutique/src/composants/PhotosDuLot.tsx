import { AnimatePresence, motion } from "framer-motion";
import { Boxes, Loader2, Trash2 } from "lucide-react";
import { useState } from "react";

import type { MediaCampagne, Page } from "@commun/api/types";
import { Carte, EtatVide, Squelette } from "@commun/composants/ui";
import { api, useRequete } from "@commun/outils/requetes";
import { EnvoiMedias, mediasPrets, type MediaEnAttente } from "@/composants/EnvoiMedias";

/**
 * Les photos de la marchandise réellement en main, sur la page du groupeur.
 *
 * Distinctes des photos du produit : celles-là montrent la référence,
 * celles-ci montrent les cartons posés par terre. C'est souvent ce qui
 * décide un acheteur hésitant, parce qu'une photo de son propre stock ne
 * s'emprunte pas à un catalogue.
 *
 * Elles se déposent **ici et pas à la création** : le groupeur lance sa
 * campagne avant d'avoir la marchandise, et ne peut donc pas la
 * photographier ce jour-là.
 */

export const MAX_PHOTOS_LOT = 5;

export function PhotosDuLot({ campagneId }: { campagneId: number }) {
  const chemin = `/groupeur/medias-campagne/?campagne=${campagneId}`;
  const { donnees, chargement, recharger } = useRequete<Page<MediaCampagne>>(chemin);
  const [enAttente, setEnAttente] = useState<MediaEnAttente[]>([]);
  const [enregistrement, setEnregistrement] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);

  const existantes = donnees?.results ?? [];
  const reste = Math.max(0, MAX_PHOTOS_LOT - existantes.length);

  // Dès qu'un envoi est monté, on l'enregistre : laisser le groupeur appuyer
  // sur un bouton « valider » en plus donnerait une photo visible à l'écran
  // mais absente de la fiche, et il n'aurait aucun moyen de s'en rendre
  // compte.
  const enregistrer = async (medias: MediaEnAttente[]) => {
    setEnAttente(medias);
    const prets = mediasPrets(medias);
    if (prets.length === 0 || prets.length !== medias.length) return;

    setEnregistrement(true);
    setErreur(null);
    try {
      for (const [rang, media] of prets.entries()) {
        await api.post("/groupeur/medias-campagne/", {
          campagne: campagneId,
          public_id: media.public_id,
          ordre: existantes.length + rang,
        });
      }
      setEnAttente([]);
      await recharger();
    } catch (souci) {
      setErreur(souci instanceof Error ? souci.message : "Enregistrement impossible.");
    } finally {
      setEnregistrement(false);
    }
  };

  const supprimer = async (id: number) => {
    await api.delete(`/groupeur/medias-campagne/${id}/`);
    await recharger();
  };

  return (
    <Carte className="space-y-3">
      <div>
        <h2 className="flex items-center gap-2 font-bold">
          <Boxes className="size-4" />
          Photos du lot
        </h2>
        <p className="texte-doux text-sm">
          Montrez la marchandise que vous avez en main : c'est ce qui rassure le
          plus.
        </p>
      </div>

      {chargement ? (
        <Squelette className="h-24" />
      ) : (
        <>
          {existantes.length > 0 && (
            <div className="flex flex-wrap gap-2">
              <AnimatePresence initial={false}>
                {existantes.map((photo) => (
                  <motion.div
                    key={photo.id}
                    layout
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    className="surface relative size-20 overflow-hidden rounded-xl"
                  >
                    {photo.vignette && (
                      <img
                        src={photo.vignette}
                        alt={photo.legende}
                        className="size-full object-cover"
                      />
                    )}
                    <button
                      type="button"
                      onClick={() => void supprimer(photo.id)}
                      className="verre-sombre absolute right-1 top-1 grid size-6 place-items-center rounded-full text-white"
                      aria-label="Supprimer cette photo"
                    >
                      <Trash2 className="size-3" />
                    </button>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}

          {existantes.length === 0 && enAttente.length === 0 && (
            <EtatVide
              icone={<Boxes className="size-6" />}
              titre="Aucune photo du lot"
              texte="Dès que la marchandise est chez vous, photographiez-la."
            />
          )}

          {reste > 0 && (
            <EnvoiMedias
              valeur={enAttente}
              surChangement={(medias) => void enregistrer(medias)}
              cible="campagne"
              imagesSeules
              plafondImages={reste}
              intitule="Ajouter des photos"
            />
          )}

          {enregistrement && (
            <p className="texte-doux flex items-center gap-2 text-sm">
              <Loader2 className="size-4 animate-spin" />
              Enregistrement…
            </p>
          )}
          {erreur && <p className="text-sm text-red-600">{erreur}</p>}
        </>
      )}
    </Carte>
  );
}
