import { motion } from "framer-motion";
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  MapPin,
  PackageCheck,
  QrCode,
  ShoppingBag,
  Undo2,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import QRCode from "qrcode";

import type { Page, Participation, StatutParticipation } from "@commun/api/types";
import { FormulaireAvis } from "@/composants/Avis";
import { Jauge } from "@/composants/Jauge";
import { Bouton, Carte, Etiquette, EtatVide, Squelette } from "@commun/composants/ui";
import { Visuel } from "@/composants/Visuel";
import { codeLisible, dateLongue, francs } from "@commun/outils/formats";
import { useRequete } from "@commun/outils/requetes";

const TONS: Record<StatutParticipation, "neutre" | "accent" | "succes" | "alerte" | "danger"> = {
  en_attente_paiement: "alerte",
  payee: "accent",
  prete: "succes",
  retiree: "neutre",
  reputee_livree: "neutre",
  remboursee: "neutre",
  annulee: "danger",
};

/** Les commandes de l'acheteur. */
export default function MesAchats() {
  const { donnees, chargement } = useRequete<Page<Participation>>("/participations/");
  const participations = donnees?.results ?? [];

  const aRetirer = participations.filter((part) => part.statut === "prete");
  const autres = participations.filter((part) => part.statut !== "prete");

  return (
    <div className="mx-auto w-full max-w-6xl space-y-6 px-4 py-6 lg:px-8 lg:py-9">
      <header>
        <h1 className="text-2xl font-extrabold">Mes achats</h1>
        <p className="texte-doux text-sm">
          Vos parts, vos codes de retrait et l'avancement de chaque campagne.
        </p>
      </header>

      {chargement ? (
        <div className="space-y-3">
          <Squelette className="h-28" />
          <Squelette className="h-28" />
        </div>
      ) : participations.length === 0 ? (
        <EtatVide
          icone={<ShoppingBag className="size-7" />}
          titre="Aucun achat pour l'instant"
          texte="Rejoignez une campagne : votre argent reste consigné jusqu'à la livraison."
          action={
            <Link to="/catalogue">
              <Bouton>Voir les campagnes</Bouton>
            </Link>
          }
        />
      ) : (
        <>
          {aRetirer.length > 0 && (
            <section className="space-y-3">
              <h2 className="flex items-center gap-2 font-bold">
                <PackageCheck className="size-5 text-emerald-600" />À retirer maintenant
              </h2>
              <div className="grid gap-3 xl:grid-cols-2">
                {aRetirer.map((part, rang) => (
                  <LigneAchat key={part.id} participation={part} index={rang} enAvant />
                ))}
              </div>
            </section>
          )}

          {autres.length > 0 && (
            <section className="space-y-3">
              {aRetirer.length > 0 && <h2 className="font-bold">Historique</h2>}
              <div className="grid gap-3 xl:grid-cols-2">
                {autres.map((part, rang) => (
                  <LigneAchat key={part.id} participation={part} index={rang} />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

function LigneAchat({
  participation,
  index,
  enAvant,
}: {
  participation: Participation;
  index: number;
  enAvant?: boolean;
}) {
  const { campagne } = participation;
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(index, 6) * 0.05 }}
    >
      <Link to={`/mes-achats/${participation.id}`}>
        <Carte
          survol
          className={enAvant ? "border-emerald-300 dark:border-emerald-800" : undefined}
        >
          <div className="flex gap-4">
            <div className="size-20 shrink-0 overflow-hidden rounded-2xl">
              <Visuel source={campagne.produit.image} nom={campagne.produit.nom} />
            </div>
            <div className="min-w-0 flex-1 space-y-1.5">
              <div className="flex items-start justify-between gap-2">
                <h3 className="line-clamp-2 font-bold leading-snug">{campagne.titre}</h3>
                <Etiquette ton={TONS[participation.statut]}>
                  {participation.statut_libelle}
                </Etiquette>
              </div>
              <p className="texte-doux tabulaire text-sm">
                {participation.quantite} × {francs(participation.prix_unitaire_applique)} ={" "}
                <strong className="text-[color:var(--texte)]">
                  {francs(participation.montant_total)}
                </strong>
              </p>

              {participation.statut === "payee" &&
                campagne.statut === "minimum_non_atteint" && (
                  <p className="text-xs font-semibold text-amber-700 dark:text-amber-400">
                    Groupage non abouti — en attente de la décision du groupeur
                  </p>
                )}

              {participation.statut === "payee" &&
                campagne.statut !== "minimum_non_atteint" && (
                <div className="space-y-1 pt-1">
                  <Jauge pourcentage={campagne.pourcentage} atteint={campagne.minimum_atteint} compact />
                  <p className="texte-doux tabulaire text-xs">
                    {campagne.quantite_reservee} / {campagne.quantite_minimale} pièces
                  </p>
                </div>
              )}

              {participation.statut === "prete" && (
                <p className="flex items-center gap-1.5 text-sm font-semibold text-emerald-700 dark:text-emerald-400">
                  <QrCode className="size-4" />
                  Code : {codeLisible(participation.code_retrait ?? "")}
                </p>
              )}
              {participation.statut === "prete" && campagne.fin_du_retrait_le && (
                <p className="texte-doux text-xs">
                  À retirer avant le {dateLongue(campagne.fin_du_retrait_le)}
                </p>
              )}
            </div>
          </div>
        </Carte>
      </Link>
    </motion.div>
  );
}

// ── Le détail d'une part, avec son QR code ─────────────────────────────────

export function DetailAchat() {
  const { id } = useParams();
  const { donnees: participation, chargement, recharger } = useRequete<Participation>(
    `/participations/${id}/`,
  );
  const [qr, setQr] = useState<string | null>(null);

  useEffect(() => {
    if (!participation?.charge_qr) return;
    // Le QR est dessiné dans le navigateur : rien à demander au serveur, et
    // le code reste affichable même sur une connexion capricieuse au point
    // de retrait.
    void QRCode.toDataURL(participation.charge_qr, {
      width: 520,
      margin: 1,
      errorCorrectionLevel: "M",
      color: { dark: "#141e42", light: "#ffffff" },
    }).then(setQr);
  }, [participation?.charge_qr]);

  if (chargement) {
    return (
      <div className="mx-auto max-w-md space-y-4 px-4 py-6">
        <Squelette className="h-8 w-40" />
        <Squelette className="aspect-square" />
      </div>
    );
  }
  if (!participation) {
    return (
      <div className="px-4 py-20 text-center">
        <p className="texte-doux">Commande introuvable.</p>
      </div>
    );
  }

  const { campagne } = participation;
  const retirable = participation.statut === "prete";
  // Passé le délai, le code reste valable : le groupeur qui a encore le colis
  // peut le remettre, et ce code est alors la seule preuve de la livraison.
  const reputeeLivree = participation.statut === "reputee_livree";

  return (
    <div className="mx-auto w-full max-w-4xl space-y-5 px-4 py-6 lg:py-9">
      <Link
        to="/mes-achats"
        className="texte-doux inline-flex items-center gap-1.5 text-sm font-semibold"
      >
        <ArrowLeft className="size-4" />
        Mes achats
      </Link>

      <header className="space-y-1">
        <h1 className="text-xl font-extrabold leading-tight">{campagne.titre}</h1>
        <Etiquette ton={TONS[participation.statut]}>
          {participation.statut_libelle}
        </Etiquette>
      </header>

      <div className="grid gap-5 lg:grid-cols-[22rem_minmax(0,1fr)] lg:items-start">
      {/* Colonne de gauche : le code et l'endroit où le présenter. */}
      <div className="space-y-5 lg:sticky lg:top-24">
      {participation.code_retrait && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ type: "spring", stiffness: 240, damping: 24 }}
        >
          <Carte className="space-y-4 text-center">
            <div>
              <p className="texte-doux text-xs font-semibold uppercase tracking-wide">
                Code de retrait
              </p>
              <p className="tabulaire mt-1 text-3xl font-extrabold tracking-[0.18em]">
                {codeLisible(participation.code_retrait)}
              </p>
            </div>

            {qr && (
              <div className="mx-auto w-fit rounded-3xl bg-white p-4 shadow-inner">
                <img src={qr} alt="QR code de retrait" className="size-52" />
              </div>
            )}

            <p className="texte-doux text-sm">
              {retirable
                ? "Présentez ce code au point de remise. Il ne sert qu'une fois."
                : reputeeLivree
                  ? "Si le groupeur a encore votre colis, présentez ce code."
                  : "Ce code deviendra actif dès que la marchandise sera à disposition."}
            </p>
          </Carte>
        </motion.div>
      )}

      {retirable && (
        <div className="flex gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900 dark:bg-emerald-950/40">
          <MapPin className="size-5 shrink-0 text-emerald-600 dark:text-emerald-400" />
          <div className="text-sm text-emerald-900 dark:text-emerald-200">
            <p className="font-semibold">Point de remise</p>
            <p>{campagne.point_remise}</p>
            {campagne.fin_du_retrait_le && (
              <p className="mt-1">
                À retirer avant le {dateLongue(campagne.fin_du_retrait_le)}
              </p>
            )}
          </div>
        </div>
      )}

      </div>

      {/* Colonne de droite : le détail de la commande. */}
      <div className="space-y-5">
      <Carte className="space-y-3 text-sm">
        <Ligne libelle="Quantité" valeur={`${participation.quantite} pièce(s)`} />
        <Ligne
          libelle="Prix unitaire"
          valeur={francs(participation.prix_unitaire_applique)}
        />
        <Ligne
          libelle="Montant payé"
          valeur={francs(participation.montant_total)}
          gras
        />
        <Ligne libelle="Commandé le" valeur={dateLongue(participation.cree_le)} />
        {participation.payee_le && (
          <Ligne libelle="Payé le" valeur={dateLongue(participation.payee_le)} />
        )}
        {participation.retiree_le && (
          <Ligne libelle="Retiré le" valeur={dateLongue(participation.retiree_le)} />
        )}
      </Carte>

      {participation.statut === "payee" && (
        <Carte className="space-y-2">
          <p className="flex items-center gap-2 text-sm font-semibold">
            <Clock className="size-4 text-[color:var(--color-accent)]" />
            Collecte en cours
          </p>
          <Jauge pourcentage={campagne.pourcentage} atteint={campagne.minimum_atteint} />
          <p className="texte-doux tabulaire text-xs">
            {campagne.quantite_reservee} / {campagne.quantite_minimale} pièces — votre
            argent reste consigné jusqu'à la livraison.
          </p>
        </Carte>
      )}

      {participation.statut === "remboursee" && (
        <div className="flex gap-3 rounded-2xl border p-4 text-sm">
          <Undo2 className="size-5 shrink-0 text-[color:var(--color-accent)]" />
          <p>
            Cette campagne n'a pas atteint son minimum.{" "}
            {francs(participation.montant_total)} vous ont été intégralement
            remboursés.
          </p>
        </div>
      )}

      {reputeeLivree && participation.reputee_livree_le && (
        <div className="flex gap-3 rounded-2xl border p-4 text-sm">
          <Clock className="size-5 shrink-0 text-[color:var(--color-accent)]" />
          <p>
            Délai de retrait écoulé le {dateLongue(participation.reputee_livree_le)} :
            la remise est réputée faite. Si le groupeur a encore votre colis,
            présentez ce code.
          </p>
        </div>
      )}

      {participation.statut === "retiree" && (
        <div className="flex gap-3 rounded-2xl border p-4 text-sm">
          <CheckCircle2 className="size-5 shrink-0 text-emerald-600" />
          <p>Colis retiré. Merci d'avoir participé à ce groupage !</p>
        </div>
      )}

      {/* La note du groupeur. Elle tient lieu de recours : la plateforme met
          en relation, elle n'arbitre pas les désaccords sur la marchandise. */}
      <FormulaireAvis participation={participation} surChangement={recharger} />

      <Link to={`/campagnes/${campagne.id}`} className="block">
        <Bouton ton="contour" pleineLargeur>
          Voir la campagne
        </Bouton>
      </Link>
      </div>
      </div>
    </div>
  );
}

function Ligne({
  libelle,
  valeur,
  gras,
}: {
  libelle: string;
  valeur: string;
  gras?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b pb-2 last:border-0 last:pb-0">
      <span className="texte-doux">{libelle}</span>
      <span className={gras ? "tabulaire font-bold" : "tabulaire"}>{valeur}</span>
    </div>
  );
}
