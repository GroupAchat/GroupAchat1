import { Feuille } from "@commun/composants/Feuille";
import { Alerte, Bouton } from "@commun/composants/ui";

/**
 * La demande de confirmation avant un geste qu'on ne reprend pas.
 *
 * Libérer des fonds, rembourser une campagne, prévenir des participants :
 * un toucher de pouce mal placé ne doit pas suffire. La feuille nomme la
 * conséquence, et la fermer (Annuler, Échap, fond) n'exécute rien. Elle
 * reste ouverte si le serveur refuse, pour que le message se lise là où
 * l'on a décidé ; c'est l'appelant qui la ferme après un succès.
 */
export function Confirmation({
  ouverte,
  titre,
  texte,
  libelleAction,
  ton = "accent",
  envoi = false,
  erreur,
  surConfirmation,
  surFermeture,
}: {
  ouverte: boolean;
  titre: string;
  texte: string;
  libelleAction: string;
  ton?: "accent" | "danger";
  envoi?: boolean;
  erreur?: string | null;
  surConfirmation: () => void;
  surFermeture: () => void;
}) {
  return (
    <Feuille ouverte={ouverte} surFermeture={surFermeture} titre={titre}>
      <div className="space-y-4 pt-2">
        <p className="texte-doux text-sm leading-relaxed">{texte}</p>
        <Alerte>{erreur}</Alerte>
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Bouton ton="contour" onClick={surFermeture} disabled={envoi}>
            Annuler
          </Bouton>
          {/* Désactivé pendant l'envoi : un double toucher ne doit produire
              qu'un seul versement. */}
          <Bouton ton={ton} chargement={envoi} onClick={surConfirmation}>
            {libelleAction}
          </Bouton>
        </div>
      </div>
    </Feuille>
  );
}
