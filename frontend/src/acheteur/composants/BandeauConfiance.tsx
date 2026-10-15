import { IconeBouclier } from "../../ui/Icones";

/**
 * `BandeauConfiance` — SPEC_ECRANS_FIGMA.md §2.6.
 *
 * **Le seul element bleu d'un ecran acheteur** (§1.2) : fond
 * `confiance-fond`, texte et bouclier `confiance`, coins 12, ni bordure ni
 * ombre. C'est parce que tout le reste est orange qu'il arrete l'oeil.
 *
 * Formulation contrainte par §1.7 : le groupeur etant paye a la cloture, on
 * ecrit « detenu jusqu'a la cloture », jamais « bloque jusqu'a la livraison ».
 *
 * ## ⚠️ « Groupeurs selectionnes par Group Achat » a ete retire
 *
 * La phrase ouvrait ce bandeau, et le §1.7 en faisait le signal de confiance
 * de l'application. **Elle ne doit plus apparaitre nulle part** — ni ici, ni a
 * l'accueil, ni sur l'ecran de choix de profil.
 *
 * Ce qui reste porte la promesse, et la porte mieux : « Vous etes livre, ou
 * rembourse » est un **engagement verifiable**, la ou « groupeurs
 * selectionnes » demandait de nous croire sur parole. Le bandeau garde donc
 * son bouclier, son bleu et sa place ; il a juste perdu une affirmation sur
 * nous au profit d'une garantie sur eux.
 */
export default function BandeauConfiance({
  taille = "compact",
}: {
  taille?: "compact" | "complet";
}) {
  return (
    <div className="flex items-start gap-2 rounded-xl bg-confiance-fond px-3 py-2.5 text-confiance">
      <IconeBouclier taille={20} className="mt-0.5 shrink-0" />
      <div className="text-sm">
        {/* La garantie devient le titre : c'est elle qui engage. */}
        <p className="font-semibold">Vous êtes livré, ou remboursé</p>
        {taille === "complet" ? (
          <p className="mt-0.5">
            Votre paiement est détenu par Group Achat jusqu&apos;à la clôture
            du groupage. Si le groupage n&apos;aboutit pas, vous êtes remboursé
            intégralement.
          </p>
        ) : null}
      </div>
    </div>
  );
}
