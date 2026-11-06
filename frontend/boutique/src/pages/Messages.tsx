import { motion } from "framer-motion";
import {
  ArrowLeft,
  Flag,
  Lock,
  MessageCircle,
  Package,
  Phone,
  Send,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";

import type {
  Campagne,
  Conversation,
  EtatContactPrive,
  MessagePrive,
} from "@commun/api/types";
import {
  Alerte,
  Avatar,
  Bouton,
  EtatVide,
  Squelette,
  Tourniquet,
  fusionner,
} from "@commun/composants/ui";
import { useSession } from "@commun/contexte/Session";
import { dateLongue, depuis, francs } from "@commun/outils/formats";
import { api, useAction, useRequete } from "@commun/outils/requetes";

import {
  AvertissementHorsPlateforme,
  OffreAbonnement,
} from "@/composants/ContactPrive";

/**
 * La messagerie : **une page, pas un tiroir.**
 *
 * Deux colonnes sur grand écran — les fils à gauche, l'échange à droite,
 * comme toutes les messageries de places de marché. On passe du temps ici :
 * on relit ce qui a été promis, on revient voir la réponse. Une feuille
 * flottante au-dessus du catalogue perdait le fil à chaque fermeture.
 *
 * Sur téléphone il n'y a de place que pour l'un des deux : la liste, puis
 * l'échange en plein écran avec un retour.
 *
 * **L'historique reste lisible quand l'abonnement s'achève.** Ce sont ses
 * échanges : les lui retirer parce qu'il n'a pas renouvelé effacerait la
 * preuve de ce qui a été convenu. Ce qu'il perd, c'est le droit d'écrire et
 * de voir l'identité de l'OAG.
 */

/* La page occupe l'écran moins l'en-tête — et moins les onglets du bas, qui
   flottent au-dessus du contenu sur téléphone : sans ça la zone de saisie
   passait dessous.

   Les deux espaces n'ont pas la même en-tête : 4,5 rem dans la boutique,
   4 rem dans l'espace OAG, qui ajoute en plus sa marge verticale sur grand
   écran. Une hauteur devinée finit par recouvrir la zone de saisie. */
const HAUTEURS = {
  boutique: "h-[calc(100dvh-7.5rem)]",
  oag: "h-[calc(100dvh-7.5rem)]",
};

/**
 * `espace` dit **de quel côté du fil on se tient**.
 *
 * L'OAG répond depuis son espace de gestion : il ne lui faut ni l'état d'un
 * abonnement qu'il n'a pas à prendre, ni l'invitation à écrire depuis une
 * fiche de groupage — ce sont ses acheteurs qui lui écrivent.
 */
export default function Messages({
  espace = "boutique",
}: {
  espace?: "boutique" | "oag";
}) {
  const { id } = useParams();
  const { pathname, search } = useLocation();
  const { connecte } = useSession();

  const racine = espace === "oag" ? "/groupeur/messages" : "/messages";
  const HAUTEUR_PAGE = HAUTEURS[espace];
  const brouillon = pathname.endsWith("/nouveau");
  const campagneBrouillon = new URLSearchParams(search).get("campagne");
  const filOuvert = Boolean(id) || brouillon;

  const {
    donnees: fils,
    chargement,
    recharger: rechargerFils,
  } = useRequete<Conversation[]>(connecte ? "/conversations/" : null);
  // L'OAG n'a pas d'abonnement a prendre : il repond a ses propres
  // acheteurs. Lui demander l'etat du Contact Prive serait une requete pour
  // rien, et un prix affiche sans raison.
  const { donnees: etat, recharger: rechargerEtat } = useRequete<EtatContactPrive>(
    connecte && espace === "boutique" ? "/contact-prive/" : null,
  );

  if (!connecte) {
    return (
      <div className={fusionner(HAUTEUR_PAGE, "grid place-items-center px-4")}>
        <div className="w-full max-w-md text-center space-y-4">
          <div className="mx-auto grid size-16 place-items-center rounded-3xl bg-orange-100 text-orange-600">
            <Lock className="size-8" />
          </div>
          <div>
            <h1 className="text-xl font-extrabold text-slate-900">Vos messages sont privés</h1>
            <p className="texte-doux text-xs max-w-xs mx-auto mt-1">
              Connectez-vous pour échanger avec vos organisateurs et retrouver vos discussions.
            </p>
          </div>
          <Link to="/connexion" className="block pt-2">
            <Bouton pleineLargeur taille="lg" className="font-bold">
              Se connecter
            </Bouton>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className={fusionner(HAUTEUR_PAGE, "w-full flex flex-col overflow-hidden bg-white")}>
      {!filOuvert ? (
        <ColonneFils
          fils={fils}
          chargement={chargement}
          etat={espace === "oag" ? null : etat}
          actif={id ?? null}
          brouillon={brouillon}
          racine={racine}
          espace={espace}
        />
      ) : (
        <section className="flex flex-1 flex-col h-full w-full overflow-hidden bg-white">
          {brouillon ? (
            <PanneauBrouillon
              campagneId={campagneBrouillon}
              etat={etat}
              surAbonnement={rechargerEtat}
              surOuverture={rechargerFils}
              racine={racine}
            />
          ) : id ? (
            <PanneauFil
              filId={id}
              etat={etat}
              racine={racine}
              surAbonnement={rechargerEtat}
              surMessage={rechargerFils}
            />
          ) : (
            <div className="grid flex-1 place-items-center px-6">
              <EtatVide
                icone={<MessageCircle className="size-6" />}
                titre="Choisissez une conversation"
                texte="Vos échanges avec les OAG s'affichent ici."
              />
            </div>
          )}
        </section>
      )}
    </div>
  );
}

/** La colonne de gauche : tous les fils, le plus récent en haut. */
function ColonneFils({
  fils,
  chargement,
  etat,
  actif,
  brouillon,
  racine,
  espace,
  className,
}: {
  fils: Conversation[] | null;
  chargement: boolean;
  etat: EtatContactPrive | null;
  actif: string | null;
  brouillon: boolean;
  racine: string;
  espace: "boutique" | "oag";
  className?: string;
}) {
  return (
    <div className={fusionner("w-full flex-1 flex flex-col min-h-0 overflow-hidden bg-white", className)}>
      <header className="space-y-1 border-b border-slate-200/80 px-4 py-3 bg-white">
        <h1 className="text-xl font-extrabold text-slate-900">
          {espace === "oag" ? "Messages acheteurs" : "Mes messages"}
        </h1>
        {etat && (
          <p className="texte-doux text-xs">
            {etat.actif ? (
              <span className="text-emerald-700 font-medium inline-flex items-center gap-1">
                <ShieldCheck className="size-3.5" />
                Contact Privé actif jusqu'au {dateLongue(etat.expire_le!).split(" à ")[0]}
              </span>
            ) : (
              <span className="text-orange-700 font-medium inline-flex items-center gap-1">
                <Sparkles className="size-3.5 text-orange-500" />
                Contact Privé · {francs(etat.prix)}/mois · +{etat.points_par_mois} pts fidélité
              </span>
            )}
          </p>
        )}
      </header>

      <div className="flex-1 min-h-0 overflow-y-auto">
        {chargement ? (
          <div className="space-y-2 p-3">
            {Array.from({ length: 4 }, (_, rang) => (
              <Squelette key={rang} className="h-16 rounded-2xl" />
            ))}
          </div>
        ) : !fils?.length ? (
          <div className="px-4 py-16">
            <EtatVide
              icone={<MessageCircle className="size-7" />}
              titre="Aucun échange pour le moment"
              texte={
                espace === "oag"
                  ? "Vos acheteurs vous écriront directement depuis vos offres groupées."
                  : "Posez vos questions aux organisateurs (OAG) directement depuis la fiche d'une offre."
              }
              action={
                espace === "boutique" ? (
                  <Link to="/catalogue">
                    <Bouton>Explorer les offres</Bouton>
                  </Link>
                ) : undefined
              }
            />
          </div>
        ) : (
          <ul className="divide-y divide-slate-100">
            {brouillon && (
              <li className="bg-orange-50/70 border-b border-orange-200 px-4 py-3 text-xs font-bold text-orange-700">
                Nouveau message en cours…
              </li>
            )}
            {fils.map((fil) => (
              <li key={fil.id}>
                <Link
                  to={`${racine}/${fil.id}`}
                  className={fusionner(
                    "flex items-center gap-3 px-4 py-3 transition-colors active:bg-slate-100/80",
                    String(fil.id) === actif ? "bg-orange-50/50" : "hover:bg-slate-50",
                  )}
                >
                  <Avatar nom={fil.interlocuteur.nom_utilisateur} taille={42} />
                  <div className="min-w-0 flex-1 space-y-0.5">
                    <div className="flex items-baseline justify-between gap-2">
                      <p className="truncate text-xs font-bold text-slate-900">
                        {fil.interlocuteur.nom_utilisateur}
                      </p>
                      <span className="texte-doux shrink-0 text-[10px]">
                        {depuis(fil.dernier_message_le)}
                      </span>
                    </div>
                    <p className="texte-doux truncate text-xs">
                      {fil.dernier_message?.texte ?? "—"}
                    </p>
                  </div>
                  {fil.non_lus > 0 && (
                    <span className="grid size-5 shrink-0 place-items-center rounded-full bg-[color:var(--color-accent)] text-[10px] font-bold text-white shadow-xs">
                      {fil.non_lus}
                    </span>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

/** Un fil existant : l'en-tête, l'historique, la saisie. */
function PanneauFil({
  filId,
  etat,
  racine,
  surAbonnement,
  surMessage,
}: {
  filId: string;
  etat: EtatContactPrive | null;
  racine: string;
  surAbonnement: () => void;
  surMessage: () => void;
}) {
  const { donnees, chargement, recharger } = useRequete<{
    conversation: Conversation;
    messages: MessagePrive[];
  }>(`/conversations/${filId}/messages/`);

  // Ouvrir le fil l'a marqué lu : le compteur de la colonne doit suivre,
  // sinon il reste allumé sur une conversation déjà lue.
  useEffect(() => {
    if (donnees) surMessage();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [donnees?.conversation.id, donnees?.messages.length]);

  if (chargement && !donnees) {
    return (
      <div className="space-y-3 p-4">
        <Squelette className="h-16" />
        <Squelette className="h-40" />
      </div>
    );
  }

  if (!donnees) {
    return (
      <div className="grid flex-1 place-items-center px-6">
        <EtatVide
          icone={<Lock className="size-6" />}
          titre="Conversation introuvable"
          texte="Ce fil n'existe pas, ou il ne vous appartient pas."
        />
      </div>
    );
  }

  const { conversation, messages } = donnees;

  return (
    <>
      <EnTeteFil conversation={conversation} racine={racine} />
      <Historique
        messages={messages}
        surSignalement={async (message) => {
          await api.post(`/conversations/${conversation.id}/signaler-message/`, {
            message,
          });
          await recharger();
        }}
      />
      {/* Qui a le droit d'écrire est tranché par le serveur, et non devin
          ici : l'OAG répond sans abonnement, l'acheteur en a besoin, et une
          règle recopiée dans l'interface finit par diverger de celle qui
          décide vraiment. */}
      {conversation.je_peux_ecrire ? (
        <Composeur
          destinataire={conversation.interlocuteur.nom_utilisateur}
          surEnvoi={async (texte) => {
            await api.post(`/conversations/${conversation.id}/repondre/`, { texte });
            await recharger();
          }}
        />
      ) : (
        <BarreAbonnement
          etat={etat}
          nomOag={conversation.interlocuteur.nom_utilisateur}
          surAbonnement={surAbonnement}
        />
      )}
    </>
  );
}

/** Un fil qui n'existe pas encore : on écrit d'abord, il naît ensuite. */
function PanneauBrouillon({
  campagneId,
  etat,
  surAbonnement,
  surOuverture,
  racine,
}: {
  campagneId: string | null;
  etat: EtatContactPrive | null;
  surAbonnement: () => void;
  surOuverture: () => void;
  racine: string;
}) {
  const naviguer = useNavigate();
  const { donnees: campagne, chargement } = useRequete<Campagne>(
    campagneId ? `/catalogue/campagnes/${campagneId}/` : null,
  );

  if (chargement) {
    return (
      <div className="space-y-3 p-4">
        <Squelette className="h-16" />
        <Squelette className="h-40" />
      </div>
    );
  }

  if (!campagne) {
    return (
      <div className="grid flex-1 place-items-center px-6">
        <EtatVide
          icone={<MessageCircle className="size-6" />}
          titre="À qui écrire ?"
          texte="Ouvrez la fiche d'un groupage et écrivez à son OAG."
        />
      </div>
    );
  }

  const oag = campagne.groupeur;

  return (
    <>
      <header className="flex items-center gap-2.5 border-b border-slate-200/80 bg-white px-3 py-2.5 shadow-2xs">
        <Link
          to={racine}
          className="grid size-9 place-items-center rounded-full surface-douce transition active:scale-90 text-slate-700 shrink-0"
          aria-label="Retour aux messages"
        >
          <ArrowLeft className="size-4" />
        </Link>
        <Avatar nom={oag.nom_utilisateur} taille={38} />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-bold text-slate-900">{oag.nom_utilisateur}</p>
          <p className="texte-doux truncate text-xs">Nouveau message à l'OAG</p>
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5">
        <Link
          to={`/campagnes/${campagne.id}`}
          className="surface-douce mx-auto flex max-w-md items-center gap-3 rounded-2xl p-3 text-sm"
        >
          <Package className="texte-doux size-4 shrink-0" />
          <span className="min-w-0 flex-1 truncate font-semibold">
            {campagne.titre}
          </span>
        </Link>
        <p className="texte-doux mx-auto mt-6 max-w-md text-center text-sm">
          Posez votre question — le lot, le délai, le point de retrait. Personne
          d'autre ne lira cet échange.
        </p>
      </div>

      {etat?.actif ? (
        <Composeur
          destinataire={oag.nom_utilisateur}
          surEnvoi={async (texte) => {
            const fil = await api.post<Conversation>("/conversations/ouvrir/", {
              groupeur: oag.id,
              campagne: campagne.id,
              texte,
            });
            surOuverture();
            naviguer(`/messages/${fil.id}`, { replace: true });
          }}
        />
      ) : (
        <BarreAbonnement
          etat={etat}
          nomOag={oag.nom_utilisateur}
          surAbonnement={surAbonnement}
        />
      )}
    </>
  );
}

/**
 * L'en-tête du fil : qui, et ce que l'abonnement a dévoilé de lui.
 *
 * Le nom et le numéro ne sont là que pour un abonné en cours — c'est
 * exactement ce que l'abonnement achète.
 */
function EnTeteFil({
  conversation,
  racine,
}: {
  conversation: Conversation;
  racine: string;
}) {
  const autre = conversation.interlocuteur;
  return (
    <header className="flex items-center gap-2.5 border-b border-slate-200/80 bg-white px-3 py-2.5 shadow-2xs">
      <Link
        to={racine}
        className="grid size-9 place-items-center rounded-full surface-douce transition active:scale-90 text-slate-700 shrink-0"
        aria-label="Retour aux messages"
      >
        <ArrowLeft className="size-4" />
      </Link>
      <Avatar nom={autre.nom_utilisateur} taille={38} />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-bold text-slate-900">{autre.nom_utilisateur}</p>
        {autre.nom_complet ? (
          <p className="texte-doux truncate text-xs flex items-center gap-1">
            <span>{autre.nom_complet}</span>
            {autre.telephone && (
              <a
                href={`tel:+228${autre.telephone}`}
                className="inline-flex items-center gap-0.5 font-bold text-[color:var(--color-accent)]"
              >
                <Phone className="size-2.5" />
                {autre.telephone}
              </a>
            )}
          </p>
        ) : (
          <p className="texte-doux truncate text-[11px]">
            Organisateur certifié Group Achat
          </p>
        )}
      </div>
      {conversation.campagne_initiale && (
        <Link
          to={`/campagnes/${conversation.campagne_initiale}`}
          className="surface-douce flex shrink-0 items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-bold text-slate-700"
        >
          <Package className="size-3 text-orange-600" />
          <span>L'offre</span>
        </Link>
      )}
    </header>
  );
}

/** L'historique, qui se cale tout seul sur le dernier message. */
function Historique({
  messages,
  surSignalement,
}: {
  messages: MessagePrive[];
  surSignalement: (message: number) => Promise<void>;
}) {
  const bas = useRef<HTMLDivElement>(null);

  // Arriver en haut d'un fil de trente messages n'a aucun sens : ce qui
  // vient d'être dit est en bas.
  useEffect(() => {
    bas.current?.scrollIntoView({ block: "end" });
  }, [messages.length]);

  return (
    <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
      <ul className="mx-auto max-w-3xl space-y-2">
        {messages.map((message) => (
          <motion.li
            key={message.id}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className={fusionner(
              "group flex items-end gap-2",
              message.de_moi ? "justify-end" : "justify-start",
            )}
          >
            {!message.de_moi && !message.signale_le && (
              <button
                onClick={() => void surSignalement(message.id)}
                className="texte-doux order-2 opacity-0 transition-opacity group-hover:opacity-100"
                aria-label="Signaler ce message"
                title="Signaler ce message"
              >
                <Flag className="size-3.5" />
              </button>
            )}
            <div
              className={fusionner(
                "max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm",
                message.de_moi
                  ? "bg-[color:var(--color-accent)] text-white"
                  : "surface-douce",
              )}
            >
              <p className="whitespace-pre-wrap break-words">{message.texte}</p>
              <p
                className={fusionner(
                  "mt-1 text-[0.65rem]",
                  message.de_moi ? "text-white/70" : "texte-doux",
                )}
              >
                {heure(message.envoye_le)}
                {message.signale_le && " · signalé"}
              </p>
            </div>
          </motion.li>
        ))}
      </ul>
      <div ref={bas} />
    </div>
  );
}

/**
 * La saisie, collée en bas du panneau.
 *
 * Entrée envoie, Maj+Entrée va à la ligne : c'est ce que fait tout le monde,
 * et un message perdu parce qu'Entrée a sauté une ligne ne se récupère pas.
 */
function Composeur({
  destinataire,
  surEnvoi,
}: {
  destinataire: string;
  surEnvoi: (texte: string) => Promise<unknown>;
}) {
  const [texte, setTexte] = useState("");
  const envoyer = useAction(async () => {
    const propre = texte.trim();
    if (!propre) return null;
    const retour = await surEnvoi(propre);
    setTexte("");
    return retour;
  });

  const lancer = () => {
    if (!envoyer.envoi) void envoyer.lancer(undefined as never);
  };

  return (
    <form
      className="border-t px-4 py-3"
      onSubmit={(evenement) => {
        evenement.preventDefault();
        lancer();
      }}
    >
      <div className="mx-auto max-w-3xl space-y-2">
        <Alerte>{envoyer.erreur?.message}</Alerte>
        <div className="surface-douce flex items-end gap-2 rounded-2xl p-2">
          <textarea
            value={texte}
            rows={1}
            maxLength={2000}
            placeholder={`Votre message à ${destinataire}…`}
            onChange={(e) => setTexte(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                lancer();
              }
            }}
            className="max-h-32 min-h-10 flex-1 resize-none bg-transparent px-2 py-2 text-sm outline-none"
          />
          {/* Un bouton rond écrit à la main, et non le `Bouton` de la
              trousse : celui-ci porte un rembourrage horizontal qui ne
              s'enlève pas proprement, et une icône seule y flottait. */}
          <button
            type="submit"
            disabled={envoyer.envoi}
            aria-label="Envoyer"
            className="degrade-accent grid size-10 shrink-0 place-items-center rounded-full text-white transition-all active:scale-95 disabled:opacity-55"
          >
            {envoyer.envoi ? <Tourniquet /> : <Send className="size-4" />}
          </button>
        </div>
        <AvertissementHorsPlateforme />
      </div>
    </form>
  );
}

/** Ce qui remplace la saisie quand l'abonnement manque ou s'est achevé. */
function BarreAbonnement({
  etat,
  nomOag,
  surAbonnement,
}: {
  etat: EtatContactPrive | null;
  nomOag: string;
  surAbonnement: () => void;
}) {
  const { rafraichir } = useSession();
  const souscrire = useAction(async () => {
    const retour = await api.post("/contact-prive/souscrire/");
    surAbonnement();
    // Les points viennent de changer : le bandeau du profil doit suivre.
    await rafraichir();
    return retour;
  });

  return (
    <div className="max-h-[60%] overflow-y-auto border-t px-4 py-4">
      <div className="mx-auto max-w-md">
        <OffreAbonnement etat={etat} nomOag={nomOag} action={souscrire} />
      </div>
    </div>
  );
}

function heure(valeur: string): string {
  return new Date(valeur).toLocaleTimeString("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
  });
}
