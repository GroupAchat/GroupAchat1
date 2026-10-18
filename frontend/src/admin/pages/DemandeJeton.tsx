import { useState } from "react";
import { BASE_API, ErreurApi } from "../../api/client";
import { seConnecter, type SessionAdmin } from "../../api/sessionAdmin";

/**
 * La porte de l'administration : identifiant et mot de passe.
 *
 * ## ⚠️ Cet ecran disait exactement l'inverse, et il avait raison de le dire
 *
 * Sa documentation s'ouvrait sur : *« Ce n'est pas un ecran de connexion, et
 * il ne doit pas en avoir l'air. Il ne demande ni identifiant ni mot de passe,
 * il ne distingue pas deux administrateurs, et il ne trace rien. »* Il
 * demandait un **jeton unique et partage**, recopie depuis le `.env` du
 * serveur, et il le disait franchement en bas de page — *« ce jeton n'identifie
 * personne »* — pour que personne n'en deduise une securite qui n'existait pas.
 *
 * C'en est un maintenant. Les trois reproches qu'il s'adressait sont leves :
 *
 * | | Avant | Maintenant |
 * |---|---|---|
 * | Ce qu'on saisit | un secret partage | **son propre mot de passe** |
 * | Distingue deux administrateurs | non | **oui** |
 * | Le nom sur une decision KYC | celui qu'on veut bien saisir | **le compte connecte** |
 *
 * Le dernier est le plus important : le §10.5 confie la validation d'un
 * dossier a un humain parce que, le jour d'un litige, **ce dossier est notre
 * seul recours contre le groupeur**. Un journal dont l'auteur est declaratif
 * ne prouve rien.
 *
 * ## Ce qu'il reste a dire franchement
 *
 * Le bas de page ne disparait pas, il change de contenu. Ce qui merite encore
 * d'etre su : la session dure **douze heures** et ne glisse pas, elle ne
 * survit pas a la fermeture de l'onglet, et ces ecrans affichent des pieces
 * d'identite.
 */
export default function DemandeJeton({
  onSession,
  erreur,
}: {
  /** Appele avec la session ouverte par le serveur. */
  onSession: (session: SessionAdmin) => void;
  /** Rempli quand une session gardee a ete refusee — expiration, revocation. */
  erreur?: string;
}) {
  const [identifiant, setIdentifiant] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [envoi, setEnvoi] = useState(false);
  const [refus, setRefus] = useState("");

  const incomplet = identifiant.trim() === "" || motDePasse === "";

  async function soumettre(evenement: React.FormEvent) {
    evenement.preventDefault();
    if (incomplet || envoi) return;

    setEnvoi(true);
    setRefus("");
    try {
      onSession(await seConnecter(identifiant.trim(), motDePasse));
    } catch (erreurDAppel) {
      /* ⚠️ **Le 429 doit se distinguer du 401**, et ce n'est pas du detail :
         « identifiant ou mot de passe incorrect » envoie quelqu'un chercher
         un mot de passe qu'on n'acceptera de toute facon pas avant un quart
         d'heure. Le serveur renvoie le delai restant dans son message, on le
         montre tel quel. */
      setRefus(
        erreurDAppel instanceof ErreurApi
          ? erreurDAppel.message
          : "Le serveur n'a pas repondu. Verifiez qu'il est lance.",
      );
      /* Le mot de passe est efface, pas l'identifiant : on retape rarement
         l'un pour corriger l'autre, et laisser un mot de passe refuse dans le
         champ invite a resoumettre le meme. */
      setMotDePasse("");
    } finally {
      setEnvoi(false);
    }
  }

  const message = refus || erreur;

  return (
    <div className="flex min-h-dvh items-center justify-center bg-surface-douce px-4">
      <form
        onSubmit={soumettre}
        className="w-full max-w-md rounded-xl border border-bordure bg-white p-8"
      >
        <h1 className="text-xl font-semibold text-texte">
          Administration Group Achat
        </h1>
        <p className="mt-2 text-sm text-texte-secondaire">
          Ces écrans affichent des noms, des numéros de téléphone et des
          références de pièces d&apos;identité. Connectez-vous avec votre
          compte.
        </p>

        <label
          htmlFor="identifiant"
          className="mt-6 block text-sm font-medium text-texte"
        >
          Identifiant
        </label>
        <input
          id="identifiant"
          value={identifiant}
          onChange={(evenement) => setIdentifiant(evenement.target.value)}
          autoComplete="username"
          autoFocus
          disabled={envoi}
          className="mt-1.5 h-12 w-full rounded-[10px] border border-bordure bg-white px-3 text-texte outline-none focus:border-2 focus:border-texte"
        />

        <label
          htmlFor="mot-de-passe"
          className="mt-4 block text-sm font-medium text-texte"
        >
          Mot de passe
        </label>
        <input
          id="mot-de-passe"
          type="password"
          value={motDePasse}
          onChange={(evenement) => setMotDePasse(evenement.target.value)}
          autoComplete="current-password"
          disabled={envoi}
          className="mt-1.5 h-12 w-full rounded-[10px] border border-bordure bg-white px-3 text-texte outline-none focus:border-2 focus:border-texte"
        />

        {message ? (
          <p role="alert" className="mt-3 text-sm font-medium text-danger">
            {message}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={incomplet || envoi}
          className={`mt-6 h-12 w-full rounded-xl text-sm font-semibold ${
            incomplet || envoi
              ? "cursor-not-allowed bg-surface-douce text-texte-secondaire"
              : "bg-texte text-white hover:opacity-90"
          }`}
        >
          {envoi ? "Connexion…" : "Ouvrir l’administration"}
        </button>

        <p className="mt-6 border-t border-filet pt-4 text-xs text-texte-secondaire">
          {/* Toujours dit franchement, mais ce n'est plus le meme aveu : avant,
              que le jeton n'identifiait personne ; maintenant, ce que la
              session ne couvre pas. */}
          <strong className="font-semibold">
            La session dure douze heures
          </strong>{" "}
          et ne se prolonge pas à l&apos;usage. Elle ne survit pas à la
          fermeture de l&apos;onglet. Un compte se crée avec{" "}
          <code>createsuperuser</code> et se révoque en décochant{" "}
          <code>is_staff</code>, ce qui ferme ses sessions en cours.
        </p>
        <p className="mt-2 text-xs text-texte-secondaire">
          Serveur : <code>{BASE_API}</code>
        </p>
      </form>
    </div>
  );
}
