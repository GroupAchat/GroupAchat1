import { useState } from "react";
import {
  MOTIFS_DE_REFUS,
  type MotifDeRefus,
  refuserLeColis,
} from "../../api/campagnes";
import { ErreurApi } from "../../api/client";
import Bouton from "../../ui/Bouton";
import Encart from "../../ui/Encart";
import FeuilleRemontante from "../../ui/FeuilleRemontante";

/**
 * Refuser le colis au moment de la remise. Ecran 9, feuille « Refuser le
 * colis ».
 *
 * ## C'etait le pire bouton mort du produit
 *
 * Il etait dessine, visible pendant la seule livraison, et il ne faisait
 * rien. C'est l'endroit ou « vous etes livre, ou rembourse » est mise a
 * l'epreuve pour de vrai : quelqu'un a qui on presente un produit qui n'est
 * pas le sien appuyait dessus et n'obtenait **aucune trace**. Une garantie
 * dont le seul bouton de recours ne repond pas n'est pas une garantie.
 *
 * ## ⚠️ Ce qu'on promet, et ce qu'on ne promet pas
 *
 * Le refus **ouvre un litige**. La commande passe a `litige` et un humain
 * examine. On ne rembourse pas sur declaration, et il faut l'assumer
 * franchement : le groupeur a deja retire son argent a la cloture (§10.2),
 * donc un remboursement automatique se paierait sur notre tresorerie a chaque
 * refus declare, vrai ou non.
 *
 * Le texte de confirmation est donc **celui de la spec, mot pour mot** :
 * examen sous 48 h, remboursement **si le refus est justifie**. Ecrire
 * « vous serez rembourse » serait plus rassurant et ce serait un mensonge.
 *
 * ## ⚠️ Pas de depot de photo
 *
 * La spec en prevoit, et elles aideraient a instruire le dossier. Le stockage
 * de fichiers est reporte au deploiement sur le VPS, par decision explicite :
 * un champ de depot qui perd les photos serait **pire que son absence**, parce
 * que l'acheteur croirait avoir fourni sa preuve. Le motif et la description
 * partent ; la photo suivra avec le stockage.
 */
export default function FeuilleRefusColis({
  commande,
  onFermer,
  onRefuse,
}: {
  /** L'identifiant de la commande livree. */
  commande: string;
  onFermer: () => void;
  /** Appele apres un refus accepte, pour relire la commande. */
  onRefuse: () => void;
}) {
  const [motif, setMotif] = useState<MotifDeRefus>();
  const [description, setDescription] = useState("");
  const [envoi, setEnvoi] = useState(false);
  const [erreur, setErreur] = useState<string>();
  const [envoye, setEnvoye] = useState(false);

  const envoyer = async () => {
    if (motif === undefined) {
      return;
    }
    setEnvoi(true);
    setErreur(undefined);
    try {
      await refuserLeColis(commande, motif, description.trim());
      setEnvoye(true);
      onRefuse();
    } catch (cause) {
      setErreur(
        cause instanceof ErreurApi
          ? cause.message
          : "Le signalement n'a pas pu être envoyé. Réessayez.",
      );
    } finally {
      setEnvoi(false);
    }
  };

  return (
    <FeuilleRemontante titre="Refuser le colis" onFermer={onFermer}>
      {envoye ? (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-texte">
            Votre signalement est enregistré
          </h2>
          {/* Le texte de la spec de l'ecran 9, sans l'adoucir. */}
          <p className="text-texte-secondaire">
            Group Achat examine votre dossier sous 48 h et vous rembourse si le
            refus est justifié.
          </p>
          <Bouton onClick={onFermer}>Fermer</Bouton>
        </div>
      ) : (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-texte">
            Pourquoi refusez-vous le colis ?
          </h2>

          <fieldset className="space-y-2">
            <legend className="sr-only">Motif du refus</legend>
            {MOTIFS_DE_REFUS.map((choix) => (
              <label
                key={choix.cle}
                className={`flex min-h-12 cursor-pointer items-center gap-3 rounded-[10px] border px-3 text-sm ${
                  motif === choix.cle
                    ? "border-2 border-primaire bg-primaire-fond text-primaire-texte-sur-fond"
                    : "border-bordure-champ text-texte"
                }`}
              >
                <input
                  type="radio"
                  name="motif-du-refus"
                  value={choix.cle}
                  checked={motif === choix.cle}
                  onChange={() => setMotif(choix.cle)}
                  className="size-4 accent-primaire"
                />
                {choix.libelle}
              </label>
            ))}
          </fieldset>

          {/* ⚠️ **Un champ libre, ici, et c'est voulu** — a la difference de la
              file de moderation du §15, qui l'interdit. Celle-ci n'est pas
              triee par machine : elle est lue une par une par quelqu'un qui
              doit decider s'il rembourse, et « ce n'est pas la bonne
              pointure » est exactement ce qu'il a besoin de savoir. */}
          <label className="block">
            <span className="text-sm text-texte-secondaire">
              Décrivez brièvement le problème
            </span>
            <textarea
              rows={3}
              value={description}
              onChange={(evenement) => setDescription(evenement.target.value)}
              placeholder="Ce ne sont pas les écouteurs commandés…"
              className="mt-1 w-full resize-none rounded-[10px] border border-bordure-champ px-3 py-2.5 text-sm outline-none focus:border-2 focus:border-primaire"
            />
          </label>

          <Encart variante="info">
            Le colis reste chez le livreur. Group Achat examine votre dossier
            sous 48 h et vous rembourse si le refus est justifié.
          </Encart>

          {erreur ? <Encart variante="attention">{erreur}</Encart> : null}

          {/* `primaire` et non un style « danger » : il n'en existe pas de
              plein dans le systeme (§1.2), et c'est bien l'action principale
              de cette feuille. Le bouton qui l'ouvre, lui, reste en
              `danger-texte` sur l'ecran 9. */}
          <Bouton
            onClick={envoyer}
            desactive={motif === undefined || envoi}
          >
            {envoi ? "Envoi…" : "Refuser et signaler"}
          </Bouton>
        </div>
      )}
    </FeuilleRemontante>
  );
}
