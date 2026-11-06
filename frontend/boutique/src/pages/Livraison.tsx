import { motion } from "framer-motion";
import {
  Check,
  Landmark,
  Package,
  Phone,
  ScanLine,
  Truck,
} from "lucide-react";
import { useState } from "react";

import type { Colis, ModeRetrait } from "@commun/api/types";
import {
  Alerte,
  Bouton,
  Carte,
  Champ,
  Etiquette,
  EtatVide,
  Squelette,
  fusionner,
} from "@commun/composants/ui";
import { useSession } from "@commun/contexte/Session";
import { telephoneLisible } from "@commun/outils/formats";
import { api, useAction, useRequete } from "@commun/outils/requetes";

/**
 * L'espace du livreur partenaire — La Poste, Gozem.
 *
 * **C'est lui qui remet le colis, et lui seul.** L'OAG confie le lot en bloc
 * à l'agence et ne rencontre jamais ses acheteurs ; s'il validait lui-même
 * les retraits, celui qui doit livrer signerait sa propre livraison et le
 * code ne prouverait plus rien. Quand le livreur scanne, l'OAG apprend que
 * telle personne a reçu son colis.
 *
 * C'est le seul écran de la plateforme où l'on voit **l'adresse** d'un
 * acheteur et son numéro : on ne livre pas un pseudonyme, il faut sonner et
 * appeler.
 */

const MODES: { cle: ModeRetrait | "tous"; libelle: string }[] = [
  { cle: "tous", libelle: "Tout" },
  { cle: "poste", libelle: "Au bureau de poste" },
  { cle: "livraison", libelle: "À domicile" },
];

export default function Livraison() {
  const { utilisateur } = useSession();
  const [mode, setMode] = useState<ModeRetrait | "tous">("tous");
  const { donnees: colis, chargement, recharger } = useRequete<Colis[]>(
    mode === "tous" ? "/livraison/tournee/" : `/livraison/tournee/?mode=${mode}`,
    [mode],
  );

  if (utilisateur && utilisateur.role !== "livreur" && !utilisateur.est_equipe) {
    return (
      <div className="mx-auto max-w-md px-4 py-20">
        <EtatVide
          icone={<Truck className="size-6" />}
          titre="Réservé aux livreurs partenaires"
          texte="Cet écran sert à remettre les colis et à scanner les codes de retrait."
        />
      </div>
    );
  }

  const liste = colis ?? [];

  return (
    <div className="mx-auto w-full max-w-3xl space-y-5 px-4 py-6 pb-24 lg:py-9">
      <header className="space-y-1">
        <h1 className="text-2xl font-extrabold">Ma tournée</h1>
        <p className="texte-doux text-sm">
          Scannez le code de chaque acheteur à la remise : c'est ce qui prouve
          la livraison, et ce qui prévient l'OAG.
        </p>
      </header>

      <Scanner surRemise={recharger} />

      <div className="flex flex-wrap gap-2">
        {MODES.map((choix) => (
          <button
            key={choix.cle}
            onClick={() => setMode(choix.cle)}
            className={fusionner(
              "rounded-full px-4 py-2 text-sm font-semibold transition-colors",
              mode === choix.cle
                ? "bg-accent-doux text-[color:var(--color-accent-fort)]"
                : "surface texte-doux",
            )}
          >
            {choix.libelle}
          </button>
        ))}
      </div>

      {chargement ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }, (_, rang) => (
            <Squelette key={rang} className="h-28" />
          ))}
        </div>
      ) : !liste.length ? (
        <EtatVide
          icone={<Check className="size-6" />}
          titre="Aucun colis en attente"
          texte="Tout ce qui vous a été confié a été remis."
        />
      ) : (
        <ul className="space-y-3">
          {liste.map((paquet, rang) => (
            <motion.li
              key={paquet.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(rang, 8) * 0.04 }}
            >
              <LigneColis colis={paquet} />
            </motion.li>
          ))}
        </ul>
      )}
    </div>
  );
}

/**
 * La saisie du code.
 *
 * Le code reste lisible à l'œil dans le QR, à dessein : un téléphone dont
 * l'appareil photo ne marche pas doit pouvoir le dicter. C'est donc une
 * saisie, et le scan de l'appareil photo viendra s'y brancher.
 */
function Scanner({ surRemise }: { surRemise: () => void }) {
  const [code, setCode] = useState("");
  const [remis, setRemis] = useState<Colis | null>(null);

  const valider = useAction(async () => {
    const retour = await api.post<{ colis: Colis }>("/livraison/retrait/", {
      code: code.trim(),
    });
    setRemis(retour.colis);
    setCode("");
    surRemise();
    return retour;
  });

  return (
    <Carte className="space-y-3">
      <form
        className="flex items-end gap-2"
        onSubmit={(evenement) => {
          evenement.preventDefault();
          if (code.trim()) void valider.lancer(undefined as never);
        }}
      >
        <div className="min-w-0 flex-1">
          <Champ
            etiquette="Code QR ou Code OTP SMS de secours"
            placeholder="8 car. QR ou 6 chiffres OTP SMS"
            value={code}
            maxLength={40}
            autoCapitalize="characters"
            onChange={(evenement) => {
              setCode(evenement.target.value.toUpperCase());
              setRemis(null);
            }}
          />
        </div>
        <Bouton
          type="submit"
          taille="lg"
          chargement={valider.envoi}
          disabled={!code.trim()}
          icone={<ScanLine className="size-4" />}
        >
          Remettre
        </Bouton>
      </form>

      <Alerte>{valider.erreur?.message}</Alerte>

      {remis && (
        <motion.div
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-sm dark:border-emerald-900 dark:bg-emerald-950/40"
        >
          <span className="grid size-9 shrink-0 place-items-center rounded-full bg-emerald-500 text-white">
            <Check className="size-5" strokeWidth={3} />
          </span>
          <p className="text-emerald-900 dark:text-emerald-200">
            Colis remis à <strong>{remis.destinataire}</strong> —{" "}
            {remis.quantite} × {remis.produit}.
          </p>
        </motion.div>
      )}
    </Carte>
  );
}

function LigneColis({ colis }: { colis: Colis }) {
  return (
    <Carte className="space-y-3">
      <div className="flex items-start gap-3">
        <span className="bg-accent-doux grid size-10 shrink-0 place-items-center rounded-2xl text-[color:var(--color-accent)]">
          {colis.mode_retrait === "livraison" ? (
            <Truck className="size-5" />
          ) : (
            <Landmark className="size-5" />
          )}
        </span>
        <div className="min-w-0 flex-1">
          <p className="font-bold">{colis.destinataire}</p>
          <p className="texte-doux truncate text-sm">
            {colis.quantite} × {colis.produit}
          </p>
        </div>
        <Etiquette ton={colis.mode_retrait === "livraison" ? "accent" : "neutre"}>
          {colis.mode_retrait === "livraison" ? "À livrer" : "Au bureau"}
        </Etiquette>
      </div>

      <p className="surface-douce flex items-start gap-2 rounded-2xl p-3 text-sm">
        <Package className="texte-doux mt-0.5 size-4 shrink-0" />
        <span>
          {colis.mode_retrait === "livraison"
            ? colis.adresse_livraison
            : colis.bureau_poste}
        </span>
      </p>

      {/* Le numéro est cliquable : on prévient de son arrivée, on ne cherche
          pas une adresse à l'aveugle. */}
      <a
        href={`tel:+228${colis.telephone}`}
        className="flex items-center gap-2 text-sm font-semibold text-[color:var(--color-accent)]"
      >
        <Phone className="size-4" />
        {telephoneLisible(colis.telephone)}
      </a>
    </Carte>
  );
}
