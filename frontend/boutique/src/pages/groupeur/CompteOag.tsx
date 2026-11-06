import { motion } from "framer-motion";
import {
  BadgeCheck,
  Eye,
  LogOut,
  ShieldCheck,
  Smartphone,
  Store,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import type { DossierKYC } from "@commun/api/types";
import { Avatar, Bouton, Carte, Etiquette } from "@commun/composants/ui";
import { useSession } from "@commun/contexte/Session";
import { dateLongue, telephoneLisible } from "@commun/outils/formats";
import { useRequete } from "@commun/outils/requetes";

import { BandeauGrade } from "@/composants/BandeauGrade";
import { CarteDroitDePublier } from "@/composants/DroitDePublier";

/**
 * Le compte de l'OAG, **dans son espace de gestion**.
 *
 * L'avatar de l'espace OAG menait auparavant au profil acheteur : on en
 * ressortait avec les onglets Accueil, Catalogue et Demandes, c'est-à-dire
 * dans la boutique, alors qu'on venait de son outil de travail. Un espace de
 * gestion qui recrache son occupant dans la vitrine à chaque réglage n'est
 * pas un espace.
 *
 * On n'y trouve donc que ce qui sert à publier et à suivre : sous quel nom
 * on est vu, le grade et la commission qu'il vaut, où les fonds arrivent, et
 * les réglages du compte. Les achats, les demandes et les messages restent du
 * côté acheteur — l'OAG y retourne par « Retour à la boutique ».
 */
export default function CompteOag() {
  const { utilisateur, deconnecter } = useSession();
  const naviguer = useNavigate();
  const { donnees: dossier } = useRequete<DossierKYC>(
    utilisateur?.statut_kyc ? "/comptes/dossier/" : null,
  );

  if (!utilisateur) return null;

  return (
    <div className="w-full space-y-4 px-3.5 py-4 pb-24">
      <motion.header
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl bg-[color:var(--color-marine-900)] p-4 text-white"
      >
        <span className="absolute -right-10 -top-16 size-56 rounded-full bg-white/10 blur-3xl" />
        <div className="relative flex items-center gap-3">
          <Avatar
            nom={utilisateur.nom_public}
            taille={56}
            className="shrink-0 ring-2 ring-white/25"
          />
          <div className="min-w-0 flex-1">
            <p className="flex items-center gap-1.5 text-xs text-white/70">
              <Eye className="size-3.5" />
              Vos acheteurs vous voient sous
            </p>
            <h1 className="truncate text-lg font-extrabold">
              {utilisateur.nom_public}
            </h1>
            <p className="text-xs text-white/80">
              {utilisateur.nom_complet} ·{" "}
              <span className="tabulaire">
                {telephoneLisible(utilisateur.telephone)}
              </span>
            </p>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {utilisateur.telephone_verifie && (
                <span className="flex items-center gap-1 rounded-full bg-white/15 px-2 py-0.5 text-[10px] font-semibold">
                  <ShieldCheck className="size-3" />
                  Numéro vérifié
                </span>
              )}
              {utilisateur.est_groupeur_valide && (
                <span className="flex items-center gap-1 rounded-full bg-white/15 px-2 py-0.5 text-[10px] font-semibold">
                  <BadgeCheck className="size-3" />
                  OAG vérifié
                </span>
              )}
            </div>
          </div>
        </div>
      </motion.header>

      <div className="space-y-4">
        <BandeauGrade />
        <CarteDroitDePublier />

          <Carte className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="grid size-10 shrink-0 place-items-center rounded-2xl bg-[color:var(--color-marine-800)] text-white">
                <Smartphone className="size-5" />
              </span>
              <div className="min-w-0">
                <p className="font-bold">Où arrivent vos fonds</p>
                <p className="texte-doux text-sm">
                  Les décaissements partent sur ce numéro.
                </p>
              </div>
            </div>

            <dl className="divide-y text-sm">
              <Ligne
                intitule="Mobile Money"
                valeur={
                  dossier?.numero_mobile_money
                    ? telephoneLisible(dossier.numero_mobile_money)
                    : "—"
                }
              />
              <Ligne
                intitule="Dossier de confiance"
                valeur={
                  dossier
                    ? dossier.statut === "valide"
                      ? `Validé le ${
                          dossier.decide_le
                            ? dateLongue(dossier.decide_le).split(" à ")[0]
                            : "—"
                        }`
                      : dossier.statut === "en_attente"
                        ? "En cours de vérification"
                        : "À corriger"
                    : "—"
                }
              />
              {dossier?.nom_commerce && (
                <Ligne
                  intitule="Commerce"
                  valeur={
                    <>
                      {dossier.nom_commerce}{" "}
                      <Etiquette>Équipe seulement</Etiquette>
                    </>
                  }
                />
              )}
            </dl>

            <p className="texte-doux text-xs">
              Pour changer ces informations, écrivez à l'équipe : elles
              engagent les versements et le contrat.
            </p>
          </Carte>

          <div className="space-y-2 pt-2">
            <Link to="/" className="block">
              <Bouton ton="contour" pleineLargeur icone={<Store className="size-4" />}>
                Retour à la boutique acheteur
              </Bouton>
            </Link>

            <Bouton
              ton="contour"
              pleineLargeur
              icone={<LogOut className="size-4" />}
              onClick={async () => {
                await deconnecter();
                naviguer("/");
              }}
              className="text-rose-600 border-rose-200 hover:bg-rose-50"
            >
              Se déconnecter
            </Bouton>
          </div>
        </div>
      </div>
  );
}

function Ligne({
  intitule,
  valeur,
}: {
  intitule: string;
  valeur: React.ReactNode;
}) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-2.5">
      <dt className="texte-doux">{intitule}</dt>
      <dd className="text-right font-semibold">{valeur}</dd>
    </div>
  );
}
