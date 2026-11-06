import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft,
  MessageSquareCode,
  PackageCheck,
  ShieldCheck,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import type { Utilisateur } from "@commun/api/types";
import { Marque } from "@commun/composants/Marque";
import { Alerte, Bouton, Champ, fusionner } from "@commun/composants/ui";
import { useSession } from "@commun/contexte/Session";
import { telephoneLisible } from "@commun/outils/formats";
import { api, useAction } from "@commun/outils/requetes";

interface ReponseVerification {
  sms_simule: boolean;
  code_affiche?: string;
}

function Cadre({
  titre,
  sousTitre,
  retour,
  children,
}: {
  titre: string;
  sousTitre?: string;
  retour?: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-[calc(100dvh-5rem)] flex flex-col justify-center px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
        className="w-full space-y-5"
      >
        {retour && (
          <button
            onClick={retour}
            className="texte-doux flex items-center gap-1.5 text-sm font-semibold transition active:scale-95"
          >
            <ArrowLeft className="size-4" />
            Retour
          </button>
        )}
        <div className="space-y-3">
          <div className="flex justify-center py-1">
            <Marque taille="grande" />
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-extrabold text-slate-900">{titre}</h1>
            {sousTitre && (
              <p className="texte-doux mt-1.5 text-sm max-w-xs mx-auto">
                {sousTitre}
              </p>
            )}
          </div>
        </div>

        <div className="rounded-3xl p-5 shadow-sm border border-slate-200/80 bg-white">
          {children}
        </div>

        <div className="flex items-center justify-center gap-5 text-xs text-slate-500 pt-1">
          <span className="inline-flex items-center gap-1 font-medium">
            <ShieldCheck className="size-3.5 text-emerald-600" />
            Paiements consignés
          </span>
          <span className="inline-flex items-center gap-1 font-medium">
            <PackageCheck className="size-3.5 text-orange-600" />
            Retrait sécurisé
          </span>
        </div>
      </motion.div>
    </div>
  );
}

// ── Inscription ────────────────────────────────────────────────────────────

export function Inscription() {
  const naviguer = useNavigate();
  const [params] = useSearchParams();
  const retour = params.get("retour");
  const { definir } = useSession();
  const [etape, setEtape] = useState<"formulaire" | "code">("formulaire");
  const [telephone, setTelephone] = useState("");
  const [codeSimule, setCodeSimule] = useState<string | undefined>();
  const [saisie, setSaisie] = useState({
    prenom: "",
    nom: "",
    nom_utilisateur: "",
    telephone: "",
    mot_de_passe: "",
    email: "",
  });

  const inscription = useAction(async () => {
    const reponse = await api.post<{
      utilisateur: Utilisateur;
      verification: ReponseVerification;
    }>("/comptes/inscription/", saisie);
    setTelephone(reponse.utilisateur.telephone);
    setCodeSimule(reponse.verification.code_affiche);
    setEtape("code");
    return reponse;
  });

  if (etape === "code") {
    return (
      <EtapeCode
        telephone={telephone}
        codeSimule={codeSimule}
        surRetour={() => setEtape("formulaire")}
        surSucces={(compte) => {
          definir(compte);
          const cible = retour && retour.startsWith("/") ? retour : destinationApres(compte);
          naviguer(cible, { replace: true });
        }}
      />
    );
  }

  return (
    <Cadre
      titre="Créer mon compte"
      sousTitre="Quelques informations, un code par SMS, et vous pouvez commander."
    >
      <form
        onSubmit={(evenement) => {
          evenement.preventDefault();
          void inscription.lancer(undefined as never);
        }}
        className="space-y-4"
      >
        <div className="grid grid-cols-2 gap-3">
          <Champ
            etiquette="Prénom"
            value={saisie.prenom}
            autoComplete="given-name"
            required
            onChange={(e) => setSaisie({ ...saisie, prenom: e.target.value })}
            erreur={inscription.erreur?.pourChamp("prenom")}
          />
          <Champ
            etiquette="Nom"
            value={saisie.nom}
            autoComplete="family-name"
            required
            onChange={(e) => setSaisie({ ...saisie, nom: e.target.value })}
            erreur={inscription.erreur?.pourChamp("nom")}
          />
        </div>

        {/* Sur la plateforme, l'acheteur et l'OAG ne se connaissent pas.
            Ce nom est la seule chose que l'autre partie verra — d'où le fait
            de le demander ici, et non enfoui dans le profil. */}
        <Champ
          etiquette="Nom d'utilisateur (facultatif)"
          value={saisie.nom_utilisateur}
          autoComplete="username"
          maxLength={24}
          placeholder="Ama K."
          onChange={(e) => setSaisie({ ...saisie, nom_utilisateur: e.target.value })}
          erreur={inscription.erreur?.pourChamp("nom_utilisateur")}
          aide="C'est sous ce nom que les vendeurs vous verront. Sans choix, ce sera votre prénom et l'initiale de votre nom."
        />

        <Champ
          etiquette="Numéro de téléphone"
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          placeholder="90 00 11 22"
          prefixe="+228"
          required
          value={saisie.telephone}
          onChange={(e) => setSaisie({ ...saisie, telephone: e.target.value })}
          erreur={inscription.erreur?.pourChamp("telephone")}
          aide="C'est votre identifiant : il sera vérifié par SMS."
        />

        <Champ
          etiquette="Mot de passe"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          value={saisie.mot_de_passe}
          onChange={(e) => setSaisie({ ...saisie, mot_de_passe: e.target.value })}
          erreur={inscription.erreur?.pourChamp("mot_de_passe")}
          aide="Au moins 8 caractères, pas uniquement des chiffres."
        />

        <Champ
          etiquette="Adresse e-mail (facultatif)"
          type="email"
          autoComplete="email"
          value={saisie.email}
          onChange={(e) => setSaisie({ ...saisie, email: e.target.value })}
          erreur={inscription.erreur?.pourChamp("email")}
        />

        <Alerte>
          {inscription.erreur && !inscription.erreur.pourChamp("telephone")
            ? inscription.erreur.message
            : null}
        </Alerte>

        <Bouton type="submit" pleineLargeur taille="lg" chargement={inscription.envoi}>
          Continuer
        </Bouton>

        <p className="texte-doux text-center text-sm">
          Déjà un compte ?{" "}
          <Link to="/connexion" className="font-semibold text-[color:var(--color-accent)]">
            Se connecter
          </Link>
        </p>
      </form>
    </Cadre>
  );
}

// ── Connexion ──────────────────────────────────────────────────────────────

/** Où l'on atterrit après s'être connecté, selon ce qu'on est. */
function destinationApres(utilisateur: Utilisateur): string {
  if (utilisateur.role === "livreur") return "/livraison";
  if (utilisateur.est_groupeur_valide) return "/groupeur";
  return "/";
}

export function Connexion() {
  const naviguer = useNavigate();
  const [params] = useSearchParams();
  const retour = params.get("retour");
  const { definir } = useSession();
  const [telephone, setTelephone] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [aVerifier, setAVerifier] = useState<{ numero: string; code?: string } | null>(null);

  const connexion = useAction(async () => {
    const reponse = await api.post<{
      utilisateur: Utilisateur;
      verification?: ReponseVerification;
    }>("/comptes/connexion/", { telephone, mot_de_passe: motDePasse });

    // Compte créé mais jamais vérifié : l'API renvoie un code neuf plutôt que
    // de laisser la personne devant une interface qui refusera tout.
    if (!reponse.utilisateur.telephone_verifie) {
      setAVerifier({
        numero: reponse.utilisateur.telephone,
        code: reponse.verification?.code_affiche,
      });
      return reponse;
    }
    definir(reponse.utilisateur);
    // Redirige vers le retour demandé (ex: retour sur l'offre) ou vers son espace dédié
    const cible = retour && retour.startsWith("/") ? retour : destinationApres(reponse.utilisateur);
    naviguer(cible, { replace: true });
    return reponse;
  });

  if (aVerifier) {
    return (
      <EtapeCode
        telephone={aVerifier.numero}
        codeSimule={aVerifier.code}
        surRetour={() => setAVerifier(null)}
        surSucces={(compte) => {
          definir(compte);
          const cible = retour && retour.startsWith("/") ? retour : destinationApres(compte);
          naviguer(cible, { replace: true });
        }}
      />
    );
  }

  return (
    <Cadre titre="Bon retour" sousTitre="Connectez-vous avec votre numéro de téléphone.">
      <form
        onSubmit={(evenement) => {
          evenement.preventDefault();
          void connexion.lancer(undefined as never);
        }}
        className="space-y-4"
      >
        <Champ
          etiquette="Numéro de téléphone"
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          placeholder="90 00 11 22"
          prefixe="+228"
          required
          value={telephone}
          onChange={(e) => setTelephone(e.target.value)}
        />
        <Champ
          etiquette="Mot de passe"
          type="password"
          autoComplete="current-password"
          required
          value={motDePasse}
          onChange={(e) => setMotDePasse(e.target.value)}
        />

        <Alerte>{connexion.erreur?.message}</Alerte>

        <Bouton type="submit" pleineLargeur taille="lg" chargement={connexion.envoi}>
          Se connecter
        </Bouton>

        <p className="texte-doux text-center text-sm">
          Pas encore de compte ?{" "}
          <Link to="/inscription" className="font-semibold text-[color:var(--color-accent)]">
            Créer un compte
          </Link>
        </p>
      </form>
    </Cadre>
  );
}

// ── Vérification du numéro ─────────────────────────────────────────────────

function EtapeCode({
  telephone,
  codeSimule,
  surRetour,
  surSucces,
}: {
  telephone: string;
  codeSimule?: string;
  surRetour: () => void;
  surSucces: (compte: Utilisateur) => void;
}) {
  const [chiffres, setChiffres] = useState<string[]>(Array(6).fill(""));
  const [codeAffiche, setCodeAffiche] = useState(codeSimule);
  const [attente, setAttente] = useState(30);
  const cases = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    cases.current[0]?.focus();
  }, []);

  useEffect(() => {
    if (attente <= 0) return;
    const minuteur = setTimeout(() => setAttente((reste) => reste - 1), 1000);
    return () => clearTimeout(minuteur);
  }, [attente]);

  const verification = useAction(async (code: string) => {
    const reponse = await api.post<{ utilisateur: Utilisateur }>(
      "/comptes/verification/",
      { telephone, code },
    );
    surSucces(reponse.utilisateur);
    return reponse;
  });

  const renvoi = useAction(async () => {
    const reponse = await api.post<ReponseVerification>("/comptes/renvoyer-code/", {
      telephone,
    });
    setCodeAffiche(reponse.code_affiche);
    setChiffres(Array(6).fill(""));
    setAttente(30);
    cases.current[0]?.focus();
    return reponse;
  });

  const ecrire = (rang: number, valeur: string) => {
    // Un collage de six chiffres doit remplir toutes les cases d'un coup :
    // c'est ce que fait le remplissage automatique du SMS sur téléphone.
    const propre = valeur.replace(/\D/g, "");
    if (!propre) {
      setChiffres((avant) => avant.map((c, i) => (i === rang ? "" : c)));
      return;
    }
    const suivants = [...chiffres];
    for (let decalage = 0; decalage < propre.length && rang + decalage < 6; decalage += 1) {
      suivants[rang + decalage] = propre[decalage];
    }
    setChiffres(suivants);
    const prochaine = Math.min(rang + propre.length, 5);
    cases.current[prochaine]?.focus();
    if (suivants.every(Boolean)) void verification.lancer(suivants.join(""));
  };

  return (
    <Cadre
      titre="Vérifiez votre numéro"
      sousTitre={`Nous avons envoyé un code à ${telephoneLisible(telephone)}.`}
      retour={surRetour}
    >
      {/* Le SMS n'est pas branché : plutôt que de laisser la personne attendre
          un message qui n'arrivera pas, on affiche le code. */}
      <AnimatePresence>
        {codeAffiche && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 rounded-2xl border border-dashed p-4"
            style={{ borderColor: "var(--color-accent)" }}
          >
            <MessageSquareCode className="size-5 shrink-0 text-[color:var(--color-accent)]" />
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-[color:var(--color-accent)]">
                Démonstration — SMS simulé
              </p>
              <p className="tabulaire text-xl font-extrabold tracking-[0.3em]">
                {codeAffiche}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex justify-between gap-2">
        {chiffres.map((chiffre, rang) => (
          <input
            key={rang}
            ref={(noeud) => {
              cases.current[rang] = noeud;
            }}
            value={chiffre}
            onChange={(evenement) => ecrire(rang, evenement.target.value)}
            onKeyDown={(evenement) => {
              if (evenement.key === "Backspace" && !chiffre && rang > 0) {
                cases.current[rang - 1]?.focus();
              }
            }}
            inputMode="numeric"
            autoComplete="one-time-code"
            maxLength={6}
            aria-label={`Chiffre ${rang + 1}`}
            className={fusionner(
              "surface tabulaire size-12 rounded-2xl text-center text-xl font-bold outline-none transition-all sm:size-14",
              "focus:border-[color:var(--color-accent)] focus:ring-4 focus:ring-[color:var(--color-accent)]/15",
              chiffre && "border-[color:var(--color-accent)]",
            )}
          />
        ))}
      </div>

      <Alerte>{verification.erreur?.message}</Alerte>

      <Bouton
        pleineLargeur
        taille="lg"
        chargement={verification.envoi}
        disabled={chiffres.some((chiffre) => !chiffre)}
        onClick={() => void verification.lancer(chiffres.join(""))}
      >
        Vérifier
      </Bouton>

      <button
        onClick={() => void renvoi.lancer(undefined as never)}
        disabled={attente > 0 || renvoi.envoi}
        className="texte-doux w-full text-center text-sm font-semibold disabled:opacity-60"
      >
        {attente > 0 ? `Renvoyer le code dans ${attente} s` : "Renvoyer le code"}
      </button>

      <p className="texte-doux flex items-start gap-2 text-xs">
        <ShieldCheck className="mt-0.5 size-4 shrink-0" />
        Ce numéro vérifié protège vos commandes : lui seul peut retirer vos
        colis et recevoir vos remboursements.
      </p>
    </Cadre>
  );
}
