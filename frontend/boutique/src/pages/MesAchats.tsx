import { motion } from "framer-motion";
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  Landmark,
  PackageCheck,
  QrCode,
  ShieldAlert,
  ShoppingBag,
  Truck,
  Undo2,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import QRCode from "qrcode";

import type { Page, Participation, StatutParticipation } from "@commun/api/types";
import { FormulaireAvis } from "@/composants/Avis";
import { Jauge } from "@/composants/Jauge";
import { Bouton, Etiquette, EtatVide, Squelette, fusionner } from "@commun/composants/ui";
import { Visuel } from "@/composants/Visuel";
import { useSession } from "@commun/contexte/Session";
import { codeLisible, dateLongue, francs } from "@commun/outils/formats";
import { useRequete } from "@commun/outils/requetes";

const TONS: Record<StatutParticipation, "neutre" | "accent" | "succes" | "alerte" | "danger"> = {
  en_attente_paiement: "alerte",
  payee: "accent",
  prete: "succes",
  retiree: "neutre",
  remboursee: "neutre",
  annulee: "danger",
};

/** Les commandes de l'acheteur (100% Mobile). */
export default function MesAchats() {
  const { connecte } = useSession();
  const { donnees, chargement } = useRequete<Page<Participation>>(
    connecte ? "/participations/" : null,
  );
  const participations = donnees?.results ?? [];

  const aRetirer = participations.filter((part) => part.statut === "prete");
  const autres = participations.filter((part) => part.statut !== "prete");

  if (!connecte) {
    return (
      <div className="w-full px-4 py-16 text-center space-y-4">
        <div className="mx-auto grid size-16 place-items-center rounded-3xl bg-orange-100 text-orange-600">
          <ShoppingBag className="size-8" />
        </div>
        <div>
          <h1 className="text-xl font-extrabold text-slate-900">Suivi de vos commandes</h1>
          <p className="texte-doux text-xs max-w-xs mx-auto mt-1">
            Connectez-vous pour retrouver vos achats groupés, vos codes de retrait et suivre la livraison.
          </p>
        </div>
        <div className="pt-2">
          <Link to="/connexion">
            <Bouton taille="lg" pleineLargeur className="font-bold">
              Se connecter
            </Bouton>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full space-y-4 px-3.5 py-4 pb-24">
      <header className="space-y-1">
        <h1 className="text-2xl font-extrabold text-slate-900">Mes commandes</h1>
        <p className="texte-doux text-xs">
          Suivez vos achats groupés, vos codes de retrait et l'arrivée de vos colis.
        </p>
      </header>

      {chargement ? (
        <div className="space-y-3">
          <Squelette className="h-32 rounded-2xl" />
          <Squelette className="h-32 rounded-2xl" />
        </div>
      ) : participations.length === 0 ? (
        <div className="py-12">
          <EtatVide
            icone={<ShoppingBag className="size-8" />}
            titre="Aucune commande pour l'instant"
            texte="Rejoignez un groupage en cours : vos fonds restent consignés jusqu'à la livraison."
            action={
              <Link to="/catalogue">
                <Bouton>Voir le catalogue</Bouton>
              </Link>
            }
          />
        </div>
      ) : (
        <div className="space-y-4">
          {aRetirer.length > 0 && (
            <section className="space-y-2.5">
              <h2 className="flex items-center gap-1.5 text-xs font-bold text-emerald-800 uppercase tracking-wide">
                <PackageCheck className="size-4 text-emerald-600" />
                À retirer maintenant ({aRetirer.length})
              </h2>
              <div className="space-y-3">
                {aRetirer.map((part, rang) => (
                  <LigneAchat key={part.id} participation={part} index={rang} enAvant />
                ))}
              </div>
            </section>
          )}

          {autres.length > 0 && (
            <section className="space-y-2.5">
              {aRetirer.length > 0 && (
                <h2 className="text-xs font-bold text-slate-600 uppercase tracking-wide">
                  En cours & historique ({autres.length})
                </h2>
              )}
              <div className="space-y-3">
                {autres.map((part, rang) => (
                  <LigneAchat key={part.id} participation={part} index={rang} />
                ))}
              </div>
            </section>
          )}
        </div>
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
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(index, 6) * 0.04 }}
    >
      <Link to={`/mes-achats/${participation.id}`}>
        <div
          className={fusionner(
            "rounded-2xl border p-3.5 shadow-2xs space-y-3 transition active:scale-[0.99] bg-white",
            enAvant
              ? "border-emerald-300 ring-2 ring-emerald-500/15"
              : "border-slate-200/80 hover:border-slate-300",
          )}
        >
          {/* Ligne du haut : numéro commande et badge de statut */}
          <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-2">
            <span className="texte-doux text-[11px] font-medium">
              Commande #{participation.id} · {dateLongue(participation.cree_le).split(" à ")[0]}
            </span>
            <Etiquette ton={TONS[participation.statut]}>
              {participation.statut_libelle}
            </Etiquette>
          </div>

          {/* Ligne centrale : Visuel + Titre + Prix */}
          <div className="flex items-center gap-3">
            <div className="size-16 shrink-0 overflow-hidden rounded-xl bg-slate-50 border border-slate-100 p-1 flex items-center justify-center">
              <Visuel source={campagne.produit.image} nom={campagne.produit.nom} mode="contain" />
            </div>
            <div className="min-w-0 flex-1 space-y-0.5">
              <h3 className="line-clamp-2 text-xs font-bold leading-snug text-slate-900">
                {campagne.titre}
              </h3>
              <p className="texte-doux text-xs">
                Qté : <strong className="text-slate-800">{participation.quantite}</strong> × {francs(participation.prix_unitaire_applique)}
              </p>
              <p className="text-sm font-extrabold text-[color:var(--color-accent)]">
                Total : {francs(participation.montant_total)}
              </p>
            </div>
          </div>

          {/* Statut spécifique : progression ou code de retrait */}
          {participation.statut === "payee" && campagne.statut !== "minimum_non_atteint" && (
            <div className="space-y-1 bg-slate-50 rounded-xl p-2.5">
              <div className="flex justify-between text-[11px] font-semibold text-slate-700">
                <span>Progression de la collecte</span>
                <span className="text-[color:var(--color-accent)]">{campagne.pourcentage}%</span>
              </div>
              <Jauge pourcentage={campagne.pourcentage} atteint={campagne.minimum_atteint} compact />
            </div>
          )}

          {participation.statut === "prete" && (
            <div className="flex items-center justify-between rounded-xl bg-emerald-50 px-3 py-2 text-emerald-800">
              <span className="flex items-center gap-1.5 text-xs font-bold">
                <QrCode className="size-4 text-emerald-600" />
                Code : {codeLisible(participation.code_retrait ?? "")}
              </span>
              <span className="text-[11px] font-semibold text-emerald-700">Prêt au retrait →</span>
            </div>
          )}

          {/* Pied de carte : flèche d'accès aux détails */}
          {participation.statut !== "prete" && (
            <div className="flex items-center justify-end text-xs font-bold text-[color:var(--color-accent)] gap-0.5">
              <span>Voir les détails</span>
              <span>→</span>
            </div>
          )}
        </div>
      </Link>
    </motion.div>
  );
}

// ── Le détail d'une commande avec son code et son QR code ───────────────────

export function DetailAchat() {
  const { id } = useParams();
  const { donnees: participation, chargement, recharger } = useRequete<Participation>(
    `/participations/${id}/`,
  );
  const [qr, setQr] = useState<string | null>(null);

  useEffect(() => {
    if (!participation?.charge_qr) return;
    void QRCode.toDataURL(participation.charge_qr, {
      width: 520,
      margin: 1,
      errorCorrectionLevel: "M",
      color: { dark: "#141e42", light: "#ffffff" },
    }).then(setQr);
  }, [participation?.charge_qr]);

  if (chargement) {
    return (
      <div className="w-full space-y-4 px-3.5 py-4">
        <Squelette className="h-8 w-40" />
        <Squelette className="h-64 rounded-3xl" />
      </div>
    );
  }
  if (!participation) {
    return (
      <div className="px-4 py-20 text-center space-y-3">
        <p className="texte-doux text-sm">Commande introuvable.</p>
        <Link to="/mes-achats">
          <Bouton taille="sm">Retour aux commandes</Bouton>
        </Link>
      </div>
    );
  }

  const { campagne } = participation;
  const retirable = participation.statut === "prete";

  return (
    <div className="w-full space-y-4 px-3.5 py-4 pb-28">
      <Link
        to="/mes-achats"
        className="texte-doux inline-flex items-center gap-1.5 text-xs font-bold transition active:scale-95"
      >
        <ArrowLeft className="size-4" />
        Mes commandes
      </Link>

      <header className="space-y-1.5">
        <div className="flex items-center justify-between gap-2">
          <span className="texte-doux text-xs">Commande #{participation.id}</span>
          <Etiquette ton={TONS[participation.statut]}>
            {participation.statut_libelle}
          </Etiquette>
        </div>
        <h1 className="text-lg font-extrabold leading-snug text-slate-900">{campagne.titre}</h1>
      </header>

      {/* Code de retrait & QR */}
      {participation.code_retrait && (
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ type: "spring", stiffness: 240, damping: 24 }}
        >
          <div className="rounded-3xl border border-slate-200/80 bg-white p-5 shadow-sm space-y-4 text-center">
            <div>
              <p className="texte-doux text-[11px] font-bold uppercase tracking-wider">
                Votre Code de retrait
              </p>
              <p className="tabulaire mt-1 text-2xl font-black tracking-[0.16em] text-slate-900">
                {codeLisible(participation.code_retrait)}
              </p>
            </div>

            {qr && (
              <div className="mx-auto w-fit rounded-2xl bg-white p-3 border border-slate-100 shadow-inner">
                <img src={qr} alt="QR code de retrait" className="size-44 object-contain" />
              </div>
            )}

            {participation.code_otp_sms && (
              <div className="rounded-2xl border border-amber-300 bg-amber-50 p-3 text-center">
                <p className="text-[11px] font-bold text-amber-800">
                  Code OTP SMS de secours
                </p>
                <p className="tabulaire mt-0.5 font-mono text-lg font-black tracking-widest text-amber-900">
                  {participation.code_otp_sms}
                </p>
                <p className="texte-doux mt-0.5 text-[10px]">
                  À dicter au livreur ou à l'agent si besoin.
                </p>
              </div>
            )}

            <p className="texte-doux text-xs">
              {retirable
                ? "Présentez ce code ou faites scanner le QR lors de la remise."
                : "Ce code sera actif dès que le stock sera arrivé au point relais."}
            </p>
          </div>
        </motion.div>
      )}

      {/* Point de remise ou adresse de livraison */}
      <div className="flex gap-3 rounded-2xl border border-slate-200/80 bg-white p-3.5 text-xs shadow-2xs">
        {participation.mode_retrait === "livraison" ? (
          <Truck className="size-5 shrink-0 text-orange-600 mt-0.5" />
        ) : (
          <Landmark className="size-5 shrink-0 text-blue-600 mt-0.5" />
        )}
        <div className="space-y-0.5 text-slate-800">
          <p className="font-bold">{participation.mode_retrait_libelle}</p>
          <p className="text-slate-600">
            {participation.mode_retrait === "livraison"
              ? participation.adresse_livraison
              : participation.bureau_poste}
          </p>
          {participation.mode_retrait === "livraison" && (
            <p className="texte-doux text-[11px]">
              Frais de livraison réglés à la remise.
            </p>
          )}
        </div>
      </div>

      {/* Tableau récapitulatif */}
      <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-2xs space-y-2.5 text-xs">
        <h3 className="font-bold text-slate-900 border-b border-slate-100 pb-1.5">
          Détail du paiement
        </h3>
        <Ligne libelle="Quantité commandée" valeur={`${participation.quantite} pièce(s)`} />
        <Ligne libelle="Prix unitaire groupé" valeur={francs(participation.prix_unitaire_applique)} />
        <Ligne libelle="Total payé (Consigné)" valeur={francs(participation.montant_total)} gras />
        <Ligne libelle="Date de commande" valeur={dateLongue(participation.cree_le).split(" à ")[0]} />
        {participation.payee_le && (
          <Ligne libelle="Payé le" valeur={dateLongue(participation.payee_le).split(" à ")[0]} />
        )}
        {participation.retiree_le && (
          <Ligne libelle="Retiré le" valeur={dateLongue(participation.retiree_le).split(" à ")[0]} />
        )}
      </div>

      {/* Progression */}
      {participation.statut === "payee" && (
        <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-2xs space-y-2">
          <div className="flex justify-between items-center text-xs">
            <span className="font-bold text-slate-800 flex items-center gap-1.5">
              <Clock className="size-3.5 text-orange-600" />
              Collecte groupée en cours
            </span>
            <span className="font-extrabold text-orange-600">{campagne.pourcentage}%</span>
          </div>
          <Jauge pourcentage={campagne.pourcentage} atteint={campagne.minimum_atteint} />
          <p className="texte-doux text-[11px]">
            {campagne.quantite_reservee} / {campagne.quantite_minimale} pièces réservées — vos fonds restent sous séquestre jusqu'à la remise.
          </p>
        </div>
      )}

      {participation.statut === "remboursee" && (
        <div className="flex gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs">
          <Undo2 className="size-5 shrink-0 text-orange-600" />
          <p className="text-slate-700">
            Cette offre n'a pas atteint son quota minimal. Vos {francs(participation.montant_total)} ont été intégralement remboursés sur votre compte Mobile Money.
          </p>
        </div>
      )}

      {participation.statut === "retiree" && (
        <div className="flex gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-xs">
          <CheckCircle2 className="size-5 shrink-0 text-emerald-600" />
          <p className="text-emerald-800 font-medium">Colis retiré avec succès. Merci d'avoir participé à ce groupage !</p>
        </div>
      )}

      {/* Actions */}
      <div className="space-y-2 pt-2">
        <FormulaireAvis participation={participation} surChangement={recharger} />

        <Link to={`/reclamations?nouvelle=${participation.id}`} className="block">
          <Bouton
            ton="contour"
            pleineLargeur
            icone={<ShieldAlert className="size-4 text-amber-600" />}
          >
            Signaler un litige / Réclamation
          </Bouton>
        </Link>

        <Link to={`/campagnes/${campagne.id}`} className="block">
          <Bouton ton="fantome" pleineLargeur>
            Voir la fiche du groupage
          </Bouton>
        </Link>
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
    <div className="flex items-center justify-between gap-4 border-b border-slate-100 pb-2 last:border-0 last:pb-0">
      <span className="texte-doux">{libelle}</span>
      <span className={gras ? "tabulaire font-bold text-slate-900" : "tabulaire text-slate-800"}>{valeur}</span>
    </div>
  );
}
