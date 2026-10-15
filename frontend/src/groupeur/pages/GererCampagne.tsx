import { useMemo } from "react";
import { decrireTempsRestant, formaterFrancs } from "../../domaine/format";
import { LIBELLE_QUARTIER, type Quartier } from "../../domaine/groupage";
import type { Campagne } from "../../domaine/groupeur";
import { listerLesCommandes } from "../../api/espaceGroupeur";
import { useRequete } from "../../api/useRequete";
import { ErreurReseau, ListeEnChargement } from "../../ui/EtatReseau";
import { EnTeteGroupeur } from "../mise-en-page/ChromeGroupeur";
import Bouton from "../../ui/Bouton";

/**
 * Ecran 15 — Gerer une campagne. SPEC_ECRANS_FIGMA.md, ecran 15.
 *
 * ⚠️ **Le point de conception le plus important de l'ecran, et il est fait
 * d'absences.** Ni nom, ni numero, ni adresse : le groupeur voit **des codes
 * et des quartiers** (§1.7).
 *
 * L'ecran 4 promet a l'acheteur que ses coordonnees ne sont pas communiquees
 * au groupeur, et c'est cet ecran-ci qui tient la promesse. C'est aussi ce qui
 * empeche un groupeur de se constituer un fichier de clients et de les servir
 * hors plateforme, au meme prix, et sans nous — autrement dit c'est ce qui
 * protege le modele economique. Les identites ne sortent qu'une fois, vers le
 * livreur, le jour de la livraison (ecran 22).
 *
 * Le code suffit a emballer et a compter ; le quartier sert a organiser les
 * tournees. Rien d'autre n'est necessaire, donc rien d'autre n'est montre.
 */
export default function GererCampagne({
  campagne,
  onRetour,
  onCloturer,
  onPartager,
  onAnnoncerLArrivee,
  arriveeAnnoncee,
}: {
  campagne: Campagne;
  onRetour: () => void;
  onCloturer: () => void;
  /** Partage la **fiche acheteur** de la campagne : c'est ainsi qu'on recrute. */
  onPartager: () => void;
  /**
   * Previent les participants que le produit est arrive.
   *
   * ⚠️ **Il declenche, il ne redige pas.** Aucun champ de texte n'accompagne
   * ce geste, et c'est la condition qui le rend compatible avec le produit :
   * un champ libre vers ses acheteurs serait une messagerie privee, et un
   * texte partant a trente personnes d'un coup echapperait au filtre du §15.
   * La plateforme ecrit le message ; lui annonce un fait.
   */
  onAnnoncerLArrivee: () => void;
  /** Deja annonce : l'arrivee est un fait unique, on ne la repete pas. */
  arriveeAnnoncee: boolean;
}) {
  const temps = decrireTempsRestant(campagne.heuresRestantes);

  /**
   * On n'annonce l'arrivee qu'apres la cloture.
   *
   * « Le produit est arrive » sur un groupage encore ouvert n'a pas de sens —
   * la commande n'est pas passee — et le dire ferait croire a une livraison
   * imminente a des gens qui viennent de payer. Le serveur refuse ce cas ;
   * l'interface ne doit pas proposer un bouton qu'il refusera.
   */
  const peutAnnoncer =
    campagne.statut === "en-cours" || campagne.statut === "a-decider";

  /**
   * Les commandes de cette campagne, **telles que le groupeur a le droit de
   * les voir** : un code de livraison, une quantite, un montant, un quartier.
   *
   * ⚠️ Ni nom, ni numero, ni repere. C'est la route `commandes` de l'ecran 15
   * qui tient cette promesse, et un test verifie champ par champ qu'elle ne
   * laisse rien passer d'autre — c'est ce qui protege le modele contre la
   * desintermediation.
   */
  const requete = useRequete(
    (signal) => listerLesCommandes(campagne.id, signal),
    [campagne.id],
  );

  const commandes = (requete.donnees ?? []).map((brute) => ({
    codeLivraison: brute.code_livraison,
    quantite: brute.quantite,
    variante: brute.variante || undefined,
    montant: Number(brute.montant_parts),
    /* Le quartier revient en chaine : l'API ne connait pas le type ferme
       de l'interface. La conversion est sure parce que le serveur n'accepte
       que les quartiers desservis (`QUARTIERS_DESSERVIS` du domaine), et un
       quartier inconnu afficherait simplement sa cle brute. */
    quartier: brute.quartier as Quartier,
  }));

  /**
   * La repartition par quartier : une information qu'il n'a nulle part
   * ailleurs, et la seule carte de l'anonymat qu'il puisse lire (§1.7).
   *
   * ⚠️ **Ce bloc etait place avant `commandes`**, qu'il lit. Une `const` n'est
   * pas remontee comme une fonction : le corps du `useMemo` s'executait au
   * premier rendu et levait « Cannot access 'commandes' before
   * initialization ». L'ecran 15 ne s'ouvrait donc **jamais** — page blanche,
   * et rien dans le terminal.
   *
   * Les dependances etaient vides, en plus : meme sans l'erreur, la
   * repartition serait restee celle du premier rendu, c'est-a-dire vide,
   * puisque les commandes arrivent du reseau un instant plus tard.
   */
  const repartition = useMemo(() => {
    const parQuartier = new Map<Quartier, number>();
    for (const commande of commandes) {
      parQuartier.set(
        commande.quartier,
        (parQuartier.get(commande.quartier) ?? 0) + commande.quantite,
      );
    }
    return [...parQuartier.entries()].sort((a, b) => b[1] - a[1]);
  }, [commandes]);

  const totalParts = repartition.reduce((total, [, n]) => total + n, 0);

  if (requete.chargement) {
    return (
      <div className="pb-18">
        <EnTeteGroupeur titre={campagne.produit} onRetour={onRetour} />
        <ListeEnChargement nombre={4} className="px-4 pt-4" />
      </div>
    );
  }

  if (requete.erreur) {
    return (
      <div className="pb-18">
        <EnTeteGroupeur titre={campagne.produit} onRetour={onRetour} />
        <ErreurReseau
          erreur={requete.erreur}
          onReessayer={requete.recharger}
          role="groupeur"
        />
      </div>
    );
  }

  return (
    <div className="pb-18">
      <EnTeteGroupeur titre={campagne.produit} onRetour={onRetour} />

      {/* Bandeau de synthese. */}
      <div className="grid grid-cols-3 gap-px border-b border-filet bg-bordure">
        {[
          [String(campagne.commandes), "commandes"],
          [formaterFrancs(campagne.collecte), "collectés"],
          [
            campagne.heuresRestantes > 0 ? temps.libelleAccessible : "Clôturée",
            "",
          ],
        ].map(([valeur, libelle]) => (
          <div key={libelle || valeur} className="bg-white px-2 py-3 text-center">
            <p className="text-sm font-bold text-texte">{valeur}</p>
            {libelle ? (
              <p className="text-xs text-texte-secondaire">{libelle}</p>
            ) : null}
          </div>
        ))}
      </div>

      <div className="space-y-6 px-4 pt-5">
        <div className="space-y-3">
          <Bouton role="groupeur" style="secondaire" onClick={onPartager}>
            Partager la campagne
          </Bouton>
          {campagne.heuresRestantes > 0 ? (
            <Bouton role="groupeur" onClick={onCloturer}>
              Clôturer maintenant
            </Bouton>
          ) : (
            <Bouton role="groupeur" onClick={onCloturer}>
              Décider de la commande
            </Bouton>
          )}
          {/*
            ⚠️ **« Prévenir les participants » est devenu « Prévenir que le
            produit est arrivé », et ce n'est pas qu'une question de mots.**

            L'ancien libellé promettait un canal du groupeur vers ses
            acheteurs, c'est-à-dire une messagerie privée — ce que le produit
            refuse, et ce que son anonymat interdit. Le nouveau annonce **un
            fait précis** : la plateforme rédige le message, le groupeur ne
            fait que dire que la marchandise est là. Il n'apprend rien sur qui
            la reçoit ; la réponse ne lui renvoie qu'un compte.

            Il n'apparaît **qu'après la clôture**, et **une seule fois** :
            l'arrivée est un fait unique, et une cloche qui répète le même
            message perd le droit d'être regardée.
          */}
          {peutAnnoncer ? (
            <Bouton
              role="groupeur"
              style="secondaire"
              onClick={onAnnoncerLArrivee}
              desactive={arriveeAnnoncee}
            >
              {arriveeAnnoncee
                ? "Arrivée annoncée"
                : "Prévenir que le produit est arrivé"}
            </Bouton>
          ) : null}
        </div>

        <section>
          <h2 className="text-lg font-semibold text-texte">
            Les {campagne.commandes} commandes
          </h2>
          <p className="mt-1 text-sm text-texte-secondaire">
            Un code et un quartier par commande. Les coordonnées des acheteurs
            ne vous sont pas communiquées.
          </p>

          <ul className="mt-3">
            {commandes.map((commande) => (
              <li
                key={commande.codeLivraison}
                className="flex items-center justify-between gap-3 border-b border-filet py-3 last:border-b-0"
              >
                <div className="min-w-0">
                  {/* Le code identifie la commande, et c'est tout. */}
                  <p className="font-bold tracking-wider text-texte">
                    {commande.codeLivraison}
                  </p>
                  <p className="text-sm text-texte-secondaire">
                    {commande.quantite} part{commande.quantite > 1 ? "s" : ""}
                    {commande.variante ? ` · ${commande.variante}` : ""}
                    <span aria-hidden="true"> · </span>
                    {LIBELLE_QUARTIER[commande.quartier]}
                  </p>
                </div>
                <span className="shrink-0 font-medium text-texte">
                  {formaterFrancs(commande.montant)}
                </span>
              </li>
            ))}
          </ul>

          <p className="mt-3 text-xs text-texte-secondaire">
            {commandes.length} des {campagne.commandes} commandes affichées.
          </p>
        </section>

        {/* Utile pour organiser les tournees, et conforme a l'anonymat : un
            quartier n'identifie personne. */}
        <section>
          <h2 className="text-lg font-semibold text-texte">
            Répartition par quartier
          </h2>
          <table className="mt-3 w-full text-sm">
            <thead>
              <tr className="border-b border-filet text-left text-texte-secondaire">
                <th className="py-2 font-medium">Quartier</th>
                <th className="py-2 text-right font-medium">Parts</th>
                <th className="py-2 text-right font-medium">Part</th>
              </tr>
            </thead>
            <tbody>
              {repartition.map(([quartier, parts]) => (
                <tr key={quartier} className="border-b border-filet last:border-b-0">
                  <td className="py-2 text-texte">
                    {LIBELLE_QUARTIER[quartier]}
                  </td>
                  <td className="py-2 text-right text-texte">{parts}</td>
                  <td className="py-2 text-right text-texte-secondaire">
                    {Math.round((parts / totalParts) * 100)} %
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </div>
  );
}
