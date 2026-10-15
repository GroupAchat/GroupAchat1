import { useState } from "react";
import { formaterFrancs } from "../../domaine/format";
import { calculerRetrait, type Campagne } from "../../domaine/groupeur";
import { FRAIS_PROVISOIRES } from "../../domaine/livraison";
import { EnTeteGroupeur } from "../mise-en-page/ChromeGroupeur";
import { cloturerUneCampagne } from "../../api/espaceGroupeur";
import { useAction } from "../../api/useRequete";
import Bouton from "../../ui/Bouton";
import Encart from "../../ui/Encart";
import FeuilleRemontante from "../../ui/FeuilleRemontante";
import { IconeHorloge } from "../../ui/Icones";

/**
 * Ecran 16 — Cloturer et decider. SPEC_ECRANS_FIGMA.md, ecran 16.
 *
 * **C'est l'ecran le plus important cote groupeur**, et il n'a pas
 * d'equivalent dans une application de vente classique : c'est le point de
 * bascule ou l'argent change de mains.
 *
 * **Pas de retour.** On ne quitte pas cet ecran sans decider ou sans le
 * refermer explicitement — d'ou la croix plutot qu'une fleche.
 *
 * ⚠️ **Chrome bleu, a une exception pres : le bandeau de decision est
 * orange.** C'est le seul ecran ou l'orange occupe autant de place cote
 * groupeur, parce que c'est le seul ou quelque chose presse vraiment. Ailleurs
 * cette proportion serait une faute ; ici elle est le propos.
 *
 * **Le compte a rebours n'est pas decoratif** : passe 48 h, la plateforme
 * annule et rembourse (§8.2 du cahier des charges). Il s'affiche donc **en
 * heures, pas en date** — « 41 h » se comprend tout de suite, « le 9 octobre a
 * 14 h » demande un calcul.
 *
 * La ligne des frais de livraison est en retrait et en `texte-secondaire` :
 * **ce n'est pas son argent**, et il doit comprendre pourquoi elle n'entre pas
 * dans son solde.
 */
export default function Decision({
  campagne,
  heuresRestantes = 41,
  telephone = "",
  onCloturee,
  onFermer,
  onCommander,
}: {
  campagne: Campagne;
  heuresRestantes?: number;
  /** Le numero du groupeur : c'est lui qui l'identifie (§1.5). */
  telephone?: string;
  /** Appele une fois la clôture enregistrée — pour recharger ses écrans. */
  onCloturee?: () => void;
  onFermer: () => void;
  onCommander: () => void;
}) {
  const [confirmation, setConfirmation] = useState<
    "commander" | "annuler" | undefined
  >();

  /**
   * La clôture : **c'est le moment où son solde cesse d'être détenu.**
   *
   * ⚠️ **Aucun argent ne change de mains ici.** La somme était déjà la sienne
   * depuis le paiement de ses acheteurs (§9) ; la clôture la rend retirable,
   * et c'est lui qui décidera de la prendre, à l'écran 18.
   *
   * Le serveur recalcule tout — collecte, 1 500 F de frais, net — et crée le
   * ``Retrait``. Les chiffres affichés ci-dessous sont un **aperçu** calculé
   * localement pour que le groupeur sache ce qu'il accepte ; ceux qui font foi
   * sont ceux que l'appel renvoie.
   *
   * ⚠️ Si l'appel échoue, **on ne ferme pas l'écran**. Fermer donnerait à
   * croire que la clôture a eu lieu, et le groupeur attendrait un solde qui ne
   * viendrait pas.
   */
  const cloture = useAction((identifiant: string) =>
    cloturerUneCampagne(telephone, identifiant),
  );

  const { collecte, frais, net } = calculerRetrait(campagne.collecte);
  const fraisCollectes = campagne.commandes * FRAIS_PROVISOIRES;

  return (
    <div className="pb-10">
      <EnTeteGroupeur
        titre="Décision"
        action={
          <button
            type="button"
            onClick={onFermer}
            className="min-h-11 px-2 text-sm font-medium text-white/85"
          >
            Plus tard
          </button>
        }
      />

      <div className="space-y-6 px-4 pt-5">
        {/* Le bandeau orange — la seule chose qui presse de ce cote-ci. */}
        <div className="rounded-xl bg-primaire-fond p-4 text-primaire-texte-sur-fond">
          <p className="flex items-center gap-2 font-semibold">
            <IconeHorloge taille={20} />
            La campagne est clôturée
          </p>
          <p className="mt-2 text-sm">
            {campagne.commandes} commandes ·{" "}
            <strong className="font-semibold">
              {formaterFrancs(collecte)} collectés
            </strong>{" "}
            · il vous reste{" "}
            <strong className="text-xl font-bold">{heuresRestantes} h</strong>{" "}
            pour décider.
          </p>
          <p className="mt-2 text-sm">
            Sans décision, les acheteurs seront remboursés automatiquement.
          </p>
        </div>

        <section>
          <h2 className="text-lg font-semibold text-texte">Votre solde</h2>
          <dl className="mt-3">
            <div className="flex justify-between gap-4 py-1.5">
              <dt className="text-texte">Collecté sur les parts</dt>
              <dd className="font-medium text-texte">
                {formaterFrancs(collecte)}
              </dd>
            </div>
            <div className="flex justify-between gap-4 py-1.5">
              <dt className="text-texte">Frais Group Achat</dt>
              <dd className="font-medium text-texte">
                − {formaterFrancs(frais)}
              </dd>
            </div>
            <div className="mt-2 flex items-baseline justify-between gap-4 border-t border-filet pt-3">
              <dt className="font-semibold text-texte">Retirable maintenant</dt>
              {/* Le chiffre qui decide. */}
              <dd className="text-prix font-bold text-confiance">
                {formaterFrancs(net)}
              </dd>
            </div>
          </dl>

          {/* En retrait : ce n'est pas son argent. */}
          <p className="mt-3 border-l-2 border-bordure pl-3 text-xs text-texte-secondaire">
            Frais de livraison collectés : {formaterFrancs(fraisCollectes)} —
            gérés par Group Achat avec son transporteur. Ils n&apos;entrent
            jamais dans votre solde.
          </p>
        </section>

        {/* Il doit savoir, a l'instant ou il decide, ce qu'on attendra de lui
            juste apres. */}
        <Encart variante="info" role="groupeur">
          Ce montant devient retirable dès maintenant, pour que vous puissiez
          acheter la marchandise. Déposez ensuite le devis de votre
          fournisseur, puis votre reçu de paiement.
        </Encart>

        <div className="space-y-3">
          <Bouton role="groupeur" onClick={() => setConfirmation("commander")}>
            Je passe la commande
          </Bouton>
          <Bouton style="danger-texte" onClick={() => setConfirmation("annuler")}>
            J&apos;annule la campagne
          </Bouton>
        </div>
      </div>

      {confirmation ? (
        <FeuilleRemontante
          titre="Confirmer la décision"
          onFermer={() => setConfirmation(undefined)}
        >
          <div className="mt-4 space-y-4">
            {confirmation === "commander" ? (
              <>
                <h2 className="text-xl font-semibold text-texte">
                  Vous pourrez retirer {formaterFrancs(net)}
                </h2>
                <p className="text-texte-secondaire">
                  Vous vous engagez à livrer les {campagne.commandes}{" "}
                  commandes. Déposez le devis de votre fournisseur.
                </p>
                <Bouton
                  role="groupeur"
                  chargement={cloture.enCours}
                  onClick={async () => {
                    const resultat = await cloture.executer(campagne.id);
                    if (resultat) {
                      onCloturee?.();
                      onCommander();
                    }
                  }}
                >
                  Je confirme
                </Bouton>
                {cloture.erreur ? (
                  <p role="alert" className="text-sm font-medium text-danger">
                    {cloture.erreur.messageLisible}
                  </p>
                ) : null}
              </>
            ) : (
              <>
                <h2 className="text-xl font-semibold text-texte">
                  Annuler la campagne
                </h2>
                <p className="text-texte-secondaire">
                  Les {campagne.commandes} acheteurs seront remboursés
                  intégralement.{" "}
                  <strong className="font-semibold text-texte">
                    Aucun frais ne vous sera prélevé.
                  </strong>
                </p>
                <Bouton style="danger-texte" onClick={onFermer}>
                  Annuler la campagne
                </Bouton>
              </>
            )}
            <Bouton
              role="groupeur"
              style="secondaire"
              onClick={() => setConfirmation(undefined)}
            >
              Revenir
            </Bouton>
          </div>
        </FeuilleRemontante>
      ) : null}
    </div>
  );
}
