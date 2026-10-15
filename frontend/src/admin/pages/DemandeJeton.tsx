import { useState } from "react";
import { BASE_API } from "../../api/client";

/**
 * La porte de l'administration : saisir le jeton.
 *
 * ⚠️ **Ce n'est pas un ecran de connexion, et il ne doit pas en avoir l'air.**
 * Il ne demande ni identifiant ni mot de passe, il ne distingue pas deux
 * administrateurs, et il ne trace rien. Il ouvre une porte, il ne reconnait
 * personne. Le dessiner comme une page de connexion ferait croire a une
 * securite qui n'existe pas — et quelqu'un finirait par en deduire qu'on peut
 * se passer d'authentifier les administrateurs.
 *
 * D'ou le ton : on dit ce que c'est, ou trouver le jeton, et ce que ca ne
 * protege pas.
 */
export default function DemandeJeton({
  onJeton,
  erreur,
}: {
  onJeton: (jeton: string) => void;
  /** Rempli apres un jeton refuse par le serveur. */
  erreur?: string;
}) {
  const [saisie, setSaisie] = useState("");

  return (
    <div className="flex min-h-dvh items-center justify-center bg-surface-douce px-4">
      <form
        onSubmit={(evenement) => {
          evenement.preventDefault();
          if (saisie.trim()) {
            onJeton(saisie.trim());
          }
        }}
        className="w-full max-w-md rounded-xl border border-bordure bg-white p-8"
      >
        <h1 className="text-xl font-semibold text-texte">
          Administration Group Achat
        </h1>
        <p className="mt-2 text-sm text-texte-secondaire">
          Ces écrans affichent des noms, des numéros de téléphone et des
          références de pièces d&apos;identité. Le serveur les refuse sans
          jeton.
        </p>

        <label
          htmlFor="jeton"
          className="mt-6 block text-sm font-medium text-texte"
        >
          Jeton d&apos;administration
        </label>
        <input
          id="jeton"
          /* `password` pour ne pas l'afficher a l'ecran — un collegue derriere
             l'epaule, une capture d'ecran, un partage de session. */
          type="password"
          value={saisie}
          onChange={(evenement) => setSaisie(evenement.target.value)}
          autoComplete="off"
          autoFocus
          className="mt-1.5 h-12 w-full rounded-[10px] border border-bordure bg-white px-3 text-texte outline-none focus:border-2 focus:border-texte"
        />
        <p className="mt-2 text-xs text-texte-secondaire">
          C&apos;est la valeur de <code>JETON_ADMIN</code> dans le{" "}
          <code>.env</code> à la racine du dépôt.
        </p>

        {erreur ? (
          <p role="alert" className="mt-3 text-sm font-medium text-danger">
            {erreur}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={saisie.trim() === ""}
          className={`mt-6 h-12 w-full rounded-xl text-sm font-semibold ${
            saisie.trim() === ""
              ? "cursor-not-allowed bg-surface-douce text-texte-secondaire"
              : "bg-texte text-white hover:opacity-90"
          }`}
        >
          Ouvrir l&apos;administration
        </button>

        <p className="mt-6 border-t border-filet pt-4 text-xs text-texte-secondaire">
          {/* Dit franchement, parce que quelqu'un lira cet ecran et en
              conclura que l'administration est protegee. */}
          <strong className="font-semibold">
            Ce jeton n&apos;identifie personne.
          </strong>{" "}
          Il est partagé, il ne se révoque pas individuellement, et le nom
          inscrit sur les décisions est celui qu&apos;on veut bien saisir. Il
          sera remplacé par de vrais comptes. Il n&apos;est gardé que le temps
          de cet onglet.
        </p>
        <p className="mt-2 text-xs text-texte-secondaire">
          Serveur : <code>{BASE_API}</code>
        </p>
      </form>
    </div>
  );
}
