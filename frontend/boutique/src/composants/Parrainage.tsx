import { Check, Copy, Share2, Sparkles, UserPlus } from "lucide-react";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import type { Parrainage } from "@commun/api/types";
import { Bouton, Carte, Squelette } from "@commun/composants/ui";
import { useSession } from "@commun/contexte/Session";
import { pluriel } from "@commun/outils/formats";
import { api, useRequete } from "@commun/outils/requetes";

/**
 * Le parrainage, des deux côtés du lien.
 *
 * **Un clic ne vaut rien.** Le parrain n'est payé que lorsque la personne
 * qu'il a amenée paie sa part — le serveur ne valide rien avant. Récompenser
 * l'ouverture du lien ferait fabriquer des liens, pas des acheteurs.
 *
 * Côté invité, le code arrive dans l'adresse (`?p=ABC123`) et doit survivre
 * à la navigation : il est donc rangé dans le navigateur, puis envoyé avec
 * **la commande** — le dernier moment où l'on sait encore d'où vient la
 * personne.
 */

const CLE = "ga-parrain";

/** Le code rangé dans ce navigateur, s'il y en a un. */
export function codeParrainRecu(): string {
  // Le stockage peut lever — navigation privée, cookies bloqués. Un
  // parrainage perdu est moins grave qu'une page blanche.
  try {
    return localStorage.getItem(CLE) ?? "";
  } catch {
    return "";
  }
}

export function oublierCodeParrain() {
  try {
    localStorage.removeItem(CLE);
  } catch {
    /* rien à faire : il n'y avait rien à oublier */
  }
}

/**
 * Ramasse `?p=…` à l'arrivée, le range, et nettoie l'adresse.
 *
 * L'adresse est nettoyée parce qu'elle se partage à son tour : sans ça,
 * l'invité réexpédie le lien de son parrain et se fait voler ses propres
 * filleuls.
 */
export function RamasseurDeParrainage() {
  const { search, pathname } = useLocation();
  const naviguer = useNavigate();

  useEffect(() => {
    const parametres = new URLSearchParams(search);
    const code = parametres.get("p");
    if (!code) return;

    try {
      // Le premier parrain gagne : réécrire le code effacerait celui qui a
      // réellement fait venir la personne au profit du dernier lien cliqué.
      if (!localStorage.getItem(CLE)) {
        localStorage.setItem(CLE, code.trim().toUpperCase());
      }
    } catch {
      /* stockage indisponible : on continue sans parrainage */
    }

    parametres.delete("p");
    const reste = parametres.toString();
    naviguer(pathname + (reste ? `?${reste}` : ""), { replace: true });
  }, [search, pathname, naviguer]);

  return null;
}

/** La carte du parrain : son lien, ses filleuls, ses points. */
export function CarteParrainage() {
  const { connecte } = useSession();
  const { donnees: bilan, chargement } = useRequete<Parrainage>(
    connecte ? "/comptes/parrainage/" : null,
  );
  const [copie, setCopie] = useState(false);

  if (!connecte) return null;
  if (chargement) return <Squelette className="h-40" />;
  if (!bilan) return null;

  const lien = `${window.location.origin}/?p=${bilan.code}`;

  const copier = async () => {
    await ecrireDansLePressePapier(lien);
    setCopie(true);
    window.setTimeout(() => setCopie(false), 2200);
  };

  return (
    <Carte className="space-y-4">
      <div className="flex items-start gap-3">
        <span className="bg-accent-doux grid size-10 shrink-0 place-items-center rounded-2xl text-[color:var(--color-accent)]">
          <UserPlus className="size-5" />
        </span>
        <div className="min-w-0">
          <p className="font-bold">Invitez, et gagnez des points</p>
          <p className="texte-doux text-sm">
            <strong>{bilan.points_par_filleul} points</strong> par personne
            que vous amenez — quand elle paie sa première commande. Un clic
            ne compte pas.
          </p>
        </div>
      </div>

      <div className="surface-douce flex items-center gap-2 rounded-2xl p-2">
        <code className="tabulaire min-w-0 flex-1 truncate px-2 text-sm">
          {lien}
        </code>
        <Bouton
          taille="sm"
          ton={copie ? "doux" : "accent"}
          icone={
            copie ? <Check className="size-3.5" /> : <Copy className="size-3.5" />
          }
          onClick={() => void copier()}
        >
          {copie ? "Copié" : "Copier"}
        </Bouton>
      </div>

      <dl className="grid grid-cols-3 gap-2 text-center">
        <Chiffre valeur={bilan.filleuls_valides} libelle="validés" vedette />
        <Chiffre valeur={bilan.en_attente} libelle="en attente" />
        <Chiffre valeur={bilan.points_gagnes} libelle="points gagnés" />
      </dl>

      {bilan.en_attente > 0 && (
        <p className="texte-doux flex items-start gap-2 text-xs">
          <Sparkles className="mt-0.5 size-3.5 shrink-0" />
          {bilan.en_attente}{" "}
          {pluriel(bilan.en_attente, "personne a", "personnes ont")} commandé
          sans payer : les points arriveront à leur paiement.
        </p>
      )}
    </Carte>
  );
}

function Chiffre({
  valeur,
  libelle,
  vedette,
}: {
  valeur: number;
  libelle: string;
  vedette?: boolean;
}) {
  return (
    <div>
      <dd
        className={
          vedette
            ? "tabulaire text-xl font-extrabold text-[color:var(--color-accent)]"
            : "tabulaire text-xl font-extrabold"
        }
      >
        {valeur}
      </dd>
      <dt className="texte-doux text-xs">{libelle}</dt>
    </div>
  );
}

/**
 * Partager une campagne — avec son code de parrainage dedans.
 *
 * Le code est demandé au serveur au moment du partage, et non gardé en
 * mémoire : un acheteur qui n'a jamais partagé n'en a pas encore, et c'est
 * ce geste-ci qui le fait naître.
 */
export function BoutonPartager({
  chemin,
  titre,
}: {
  chemin: string;
  titre: string;
}) {
  const { connecte } = useSession();
  const [etat, setEtat] = useState<"repos" | "fait">("repos");

  const partager = async () => {
    let lien = `${window.location.origin}${chemin}`;
    if (connecte) {
      try {
        const bilan = await api.get<Parrainage>("/comptes/parrainage/");
        lien += `?p=${bilan.code}`;
      } catch {
        // Sans code, le lien marche quand même : il ne rapportera rien.
      }
    }

    // `navigator.share` ouvre le partage du téléphone — WhatsApp en premier,
    // là où ces liens circulent vraiment. Le presse-papier est le repli.
    if (navigator.share) {
      try {
        await navigator.share({ title: titre, url: lien });
        return;
      } catch {
        return; // partage refusé : ce n'est pas une erreur à signaler
      }
    }
    await ecrireDansLePressePapier(lien);
    setEtat("fait");
    window.setTimeout(() => setEtat("repos"), 2200);
  };

  return (
    <Bouton
      ton="contour"
      icone={
        etat === "fait" ? (
          <Check className="size-4" />
        ) : (
          <Share2 className="size-4" />
        )
      }
      onClick={() => void partager()}
    >
      {etat === "fait" ? "Lien copié" : "Partager"}
    </Bouton>
  );
}

/** Le presse-papier n'existe pas partout : il faut un repli. */
async function ecrireDansLePressePapier(texte: string) {
  try {
    await navigator.clipboard.writeText(texte);
    return;
  } catch {
    /* hors HTTPS ou permission refusée : on passe par la sélection */
  }
  const zone = document.createElement("textarea");
  zone.value = texte;
  zone.setAttribute("readonly", "");
  zone.style.position = "fixed";
  zone.style.opacity = "0";
  document.body.appendChild(zone);
  zone.select();
  try {
    document.execCommand("copy");
  } finally {
    document.body.removeChild(zone);
  }
}
