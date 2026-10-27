import { Camera, ImagePlus } from "lucide-react";
import { useEffect, useId, useState } from "react";

import { fusionner } from "@commun/composants/ui";

/** Miroir de `TAILLE_MAX_PIECE_OCTETS` côté serveur : ce contrôle évite un
 *  envoi de plusieurs Mo voué au refus, mais c'est le serveur qui décide. */
const TAILLE_MAX_OCTETS = 8 * 1024 * 1024;
const TYPES_ACCEPTES = ["image/jpeg", "image/png", "image/webp"];

/** Le message de refus avant envoi, ou `null` si la photo peut partir.
 *  Un type vide (certains navigateurs mobiles n'en annoncent pas) passe : le
 *  serveur lit les octets et tranche. */
function refuser(fichier: File): string | null {
  if (fichier.type && !TYPES_ACCEPTES.includes(fichier.type)) {
    return "Ce fichier n'est pas une photo lisible (JPEG, PNG ou WebP).";
  }
  if (fichier.size > TAILLE_MAX_OCTETS) {
    return "Image trop lourde : 8 Mo au maximum.";
  }
  return null;
}

interface Proprietes {
  etiquette: string;
  fichier: File | null;
  onChoisir: (fichier: File | null) => void;
  /** Erreur renvoyée par le serveur pour ce champ. */
  erreur?: string;
}

/** Une photo de pièce d'identité : aperçu, remplacement, refus lisible.
 *
 *  Pas d'attribut `capture` : sur Android il forcerait l'appareil photo et
 *  empêcherait de choisir une photo déjà prise ; sans lui, le téléphone
 *  propose l'appareil photo **et** la galerie. */
export default function ChampPiece({ etiquette, fichier, onChoisir, erreur }: Proprietes) {
  const identifiant = useId();
  const [refus, setRefus] = useState<string | null>(null);
  const [apercu, setApercu] = useState<string | null>(null);

  useEffect(() => {
    if (!fichier) {
      setApercu(null);
      return;
    }
    const adresse = URL.createObjectURL(fichier);
    setApercu(adresse);
    // Sans libération, chaque photo choisie resterait en mémoire du téléphone.
    return () => URL.revokeObjectURL(adresse);
  }, [fichier]);

  // Le refus local passe devant celui du serveur : il concerne le dernier
  // fichier choisi, alors que l'erreur serveur porte sur l'envoi précédent.
  const message = refus ?? erreur;

  return (
    <div className="space-y-1.5">
      <span className="block text-sm font-medium">{etiquette}</span>
      <label
        htmlFor={identifiant}
        className={fusionner(
          "flex min-h-28 cursor-pointer items-center gap-3 rounded-2xl border border-dashed p-3",
          "focus-within:border-[color:var(--color-accent)]",
          message ? "border-red-500" : "surface",
        )}
        style={{ background: "var(--fond-carte)" }}
      >
        {apercu ? (
          <img
            src={apercu}
            alt={`Aperçu : ${etiquette}`}
            className="size-20 shrink-0 rounded-xl border object-cover"
          />
        ) : (
          <span className="surface-douce grid size-20 shrink-0 place-items-center rounded-xl">
            <ImagePlus className="texte-doux size-6" />
          </span>
        )}
        <span className="min-w-0 flex-1 text-sm">
          {fichier ? (
            <>
              <span className="block truncate font-medium">{fichier.name}</span>
              <span className="texte-doux text-xs">Touchez pour remplacer</span>
            </>
          ) : (
            <>
              <span className="flex items-center gap-1.5 font-medium">
                <Camera className="size-4" /> Prendre ou choisir une photo
              </span>
              <span className="texte-doux text-xs">JPEG, PNG ou WebP, 8 Mo au maximum</span>
            </>
          )}
        </span>
        <input
          id={identifiant}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="sr-only"
          aria-label={etiquette}
          aria-invalid={Boolean(message)}
          aria-describedby={message ? `${identifiant}-erreur` : undefined}
          onChange={(evenement) => {
            const choisi = evenement.target.files?.[0] ?? null;
            // Valeur vidée : sans cela, rechoisir le même fichier après un
            // refus ne déclencherait aucun événement.
            evenement.target.value = "";
            if (!choisi) return;
            const motif = refuser(choisi);
            setRefus(motif);
            onChoisir(motif ? null : choisi);
          }}
        />
      </label>
      {message && (
        <p id={`${identifiant}-erreur`} className="text-sm text-red-600">
          {message}
        </p>
      )}
    </div>
  );
}
