import { useEffect, useMemo, useState } from "react";
import { ErreurApi } from "../../api/client";
import {
  acterLAnnonce,
  type DossierApi,
  listerLesDossiers,
  type ResultatDecision,
  trancherUnDossier,
} from "../../api/dossiers";
import { useAction, useRequete } from "../../api/useRequete";
import {
  type Canal,
  type Issue,
  issueProposee,
  LIBELLE_CANAL,
  LIBELLE_ETAT,
  type Motif,
  MOTIFS,
} from "../../domaine/recrutement";
import { LIBELLE_PIECE_DEPOSEE } from "../../domaine/pieces";
import { ErreurReseau, Squelette } from "../../ui/EtatReseau";
import { IconeAlerte, IconeCoche, IconeRetour } from "../../ui/Icones";

/**
 * Ecran A2 — Recrutement : examiner les dossiers KYC. §10.5 et §13.6.
 *
 * **C'est le seul ecran du produit ou une decision humaine engage la promesse
 * faite a l'acheteur.** « Vous etes livre, ou rembourse » s'affiche sur
 * presque chaque ecran acheteur, et c'est cette phrase qui le decide a payer
 * d'avance quelqu'un qu'il ne connait pas.
 *
 * ⚠️ **C'est nous qui remboursons**, et c'est ce qui rend cet examen
 * obligatoire. Le groupeur retire l'argent a la cloture, donc **avant la
 * livraison** (§10.2) : si le colis n'arrive jamais, nous payons l'acheteur et
 * nous nous retournons contre le groupeur. Il faut donc, ce jour-la, un
 * **dossier constitue, examine par un humain, et opposable**. Sans lui, la
 * garantie est une phrase que personne ne peut honorer.
 *
 * ## Il lit et ecrit sur l'API
 *
 * Plus aucune donnee locale : `GET /api/dossiers/`, `POST .../decision/`,
 * `POST .../annonce-faite/`. Deux consequences qui se voient a l'ecran :
 *
 * - **la concordance des noms vient du serveur** (`concordance_noms`), qui la
 *   recalcule a chaque lecture. Elle n'est plus recalculee ici : deux
 *   implementations de la meme regle finissent toujours par diverger, et c'est
 *   celle du serveur qui decide ;
 * - **le texte envoye au groupeur est celui du serveur**, rendu par la reponse
 *   a la decision. L'administrateur voit mot pour mot ce qui est parti, et non
 *   une approximation reconstituee par le navigateur.
 *
 * ## Deux colonnes, et pourquoi pas une liste puis une page
 *
 * La file a gauche, le dossier a droite. Un administrateur en traite plusieurs
 * a la suite ; le faire revenir a la liste entre chacun lui ferait perdre sa
 * place. Les contrôles 1 et 2 du §10.5 s'examinent d'ailleurs **ensemble** —
 * le nom sur la piece, le visage sur le selfie, le titulaire du compte : les
 * repartir sur deux pages revient a comparer de memoire.
 *
 * ## Ce que la file met en avant
 *
 * Elle ne repond qu'a une question : **quel dossier traiter maintenant ?**
 *
 * 1. **l'anciennete** — du plus ancien au plus recent. Un dossier qui attend
 *    depuis six jours est un groupeur qui s'en va, et le recrutement est le
 *    goulot d'etranglement du lancement ;
 * 2. **la concordance des noms**, visible sans ouvrir la fiche ;
 * 3. **les dossiers tranches mais non annonces** — en tete, et en rouge. Un
 *    dossier decide dont le groupeur ne sait rien a quitte la file d'attente :
 *    plus personne ne le reprend, et l'interesse attend une reponse qui ne
 *    viendra jamais. **C'est la panne silencieuse de ce parcours.**
 *
 * ⚠️ **Trois absences voulues.**
 *
 * - **Aucune image de piece d'identite.** Le §10.5 exige un stockage separe de
 *   celui des photos de produits, a acces restreint et a duree de conservation
 *   fixee. Il sera monte au deploiement sur le VPS ; d'ici la, l'API ne
 *   renvoie qu'une **reference opaque**, et afficher une vignette supposerait
 *   une adresse servie publiquement.
 * - **Aucun « tout valider ».** Elle economiserait quelques minutes et
 *   detruirait le produit : la promesse ne tient que si chaque dossier a ete
 *   ouvert.
 * - **Aucun motif en texte libre.** La liste est fermee pour rester
 *   denombrable : savoir *pourquoi* les dossiers echouent est ce qui permet de
 *   corriger le formulaire d'inscription plutot que de refuser indefiniment
 *   les memes gens.
 *
 * **Chrome neutre, 1 280 x 800**, comme l'ecran A1.
 */
export default function DossiersKyc({
  jeton,
  onRetour,
  onJetonRefuse,
}: {
  jeton: string;
  onRetour: () => void;
  /** Le serveur a refuse le jeton : on redemande la porte. */
  onJetonRefuse: () => void;
}) {
  const [choisi, setChoisi] = useState<number | undefined>();
  /** La reponse du serveur a la derniere decision : courriel parti, ou script. */
  const [resultat, setResultat] = useState<ResultatDecision>();

  const file = useRequete(
    (signal) => listerLesDossiers(jeton, undefined, signal),
    [jeton],
  );

  const dossiers = useMemo(() => file.donnees?.results ?? [], [file.donnees]);

  /**
   * Un jeton refuse renvoie a la porte.
   *
   * ⚠️ **Dans un effet, et pas pendant le rendu.** Appeler `onJetonRefuse`
   * directement dans le corps du composant revient a changer l'etat du parent
   * pendant qu'on dessine l'enfant : React le signale, et en mode strict
   * l'appel part deux fois. Un jeton refuse ne se rattrape de toute facon pas
   * en reessayant — inutile de laisser un bouton « Réessayer » sur un ecran
   * vide dont on ne peut rien faire.
   */
  const refuse = file.erreur?.statut === 403;
  useEffect(() => {
    if (refuse) {
      onJetonRefuse();
    }
  }, [refuse, onJetonRefuse]);

  const aAnnoncer = useMemo(
    () =>
      dossiers.filter((dossier) => {
        const derniere = dossier.decisions_kyc[0];
        return derniere !== undefined && derniere.notifie_le === null;
      }),
    [dossiers],
  );

  const enAttente = useMemo(
    () => dossiers.filter((d) => d.statut_kyc === "en-verification"),
    [dossiers],
  );

  /* Le serveur trie deja du plus ancien au plus recent ; on ne retrie pas
     ici. Choisir le premier a examiner plutot que le premier tout court evite
     d'ouvrir un dossier deja traite a chaque chargement. */
  const dossier =
    dossiers.find((d) => d.id === choisi) ?? enAttente[0] ?? dossiers[0];

  const decision = useAction(
    async (entree: {
      id: number;
      issue: Issue;
      canal: Canal;
      motif?: Motif;
    }) => {
      const reponse = await trancherUnDossier(jeton, entree.id, {
        issue: entree.issue,
        motif: entree.motif,
        canal: entree.canal,
        /* ⚠️ Faute de comptes, ce nom est declaratif. Voir `admin/jeton.ts`. */
        decide_par: "Administration",
      });
      setResultat(reponse);
      file.recharger();
      return reponse;
    },
  );

  const annonce = useAction(async (id: number) => {
    const faite = await acterLAnnonce(jeton, id);
    file.recharger();
    return faite;
  });

  return (
    <div className="min-h-dvh bg-surface-douce">
      <header className="border-b border-filet bg-white">
        <div className="mx-auto flex max-w-[1280px] items-center gap-4 px-8 py-4">
          <button
            type="button"
            onClick={onRetour}
            className="flex items-center gap-2 rounded-[10px] px-2 py-1 text-sm text-texte-secondaire hover:bg-surface-douce"
          >
            <IconeRetour taille={18} />
            Tableau de bord
          </button>
          <div className="h-6 w-px bg-bordure" aria-hidden="true" />
          <h1 className="text-lg font-semibold text-texte">
            Recrutement — dossiers KYC
          </h1>
          <p className="ml-auto text-sm text-texte-secondaire">
            {file.chargement ? (
              <Squelette largeur="140px" hauteur={14} />
            ) : (
              <>
                {enAttente.length} à examiner
                {aAnnoncer.length > 0
                  ? ` · ${aAnnoncer.length} à annoncer`
                  : null}
              </>
            )}
          </p>
        </div>
      </header>

      {file.erreur && !refuse ? (
        <ErreurReseau erreur={file.erreur} onReessayer={file.recharger} />
      ) : (
        <div className="mx-auto flex max-w-[1280px] gap-6 px-8 py-6">
          <FileDAttente
            chargement={file.chargement}
            aAnnoncer={aAnnoncer}
            enAttente={enAttente}
            choisi={dossier?.id}
            onChoisir={(id) => {
              setChoisi(id);
              /* Le resultat appartient au dossier qu'on vient de trancher :
                 le garder en changeant de fiche le ferait lire comme celui du
                 nouveau. */
              setResultat(undefined);
              decision.oublierLErreur();
            }}
          />

          {/* ⚠️ Un `div`, pas un `main` : la coquille de l'administration
              (`mise-en-page/Sidebar`) en fournit deja un, et **un document
              n'a qu'un seul `main`**. Les imbriquer est du HTML invalide, et
              un lecteur d'ecran annonce alors deux regions principales — on ne
              sait plus laquelle porte le contenu. */}
          <div className="min-w-0 flex-1">
            {file.chargement ? (
              <FicheEnChargement />
            ) : dossier ? (
              <Fiche
                dossier={dossier}
                resultat={resultat}
                erreurDecision={decision.erreur ?? annonce.erreur}
                enCours={decision.enCours || annonce.enCours}
                onTrancher={(issue, canal, motif) =>
                  decision.executer({ id: dossier.id, issue, canal, motif })
                }
                onActerLAnnonce={() => annonce.executer(dossier.id)}
              />
            ) : (
              <p className="rounded-xl border border-bordure bg-white p-8 text-center text-texte-secondaire">
                Aucun dossier. C&apos;est l&apos;état normal : traitez les
                dossiers le jour où ils arrivent et cette page reste vide.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/** Depuis combien de jours le dossier attend. */
function joursDAttente(creeLe: string): number {
  const jours = Math.floor(
    (Date.now() - new Date(creeLe).getTime()) / 86_400_000,
  );
  return Math.max(0, jours);
}

/**
 * La colonne de gauche.
 *
 * **Les dossiers a annoncer sont au-dessus de ceux a examiner**, et ce n'est
 * pas une question de volume : un dossier non annonce est deja sorti de la
 * file d'examen. Si on le rangeait en dessous, personne ne descendrait.
 */
function FileDAttente({
  chargement,
  aAnnoncer,
  enAttente,
  choisi,
  onChoisir,
}: {
  chargement: boolean;
  aAnnoncer: DossierApi[];
  enAttente: DossierApi[];
  choisi: number | undefined;
  onChoisir: (id: number) => void;
}) {
  if (chargement) {
    return (
      <nav className="w-[340px] shrink-0 space-y-2" aria-busy="true">
        {Array.from({ length: 4 }, (_, indice) => (
          <div
            key={indice}
            className="space-y-2 rounded-xl border border-bordure bg-white p-3"
          >
            <Squelette largeur="60%" />
            <Squelette largeur="80%" hauteur={12} />
          </div>
        ))}
      </nav>
    );
  }

  return (
    <nav className="w-[340px] shrink-0 space-y-6" aria-label="File des dossiers">
      {aAnnoncer.length > 0 ? (
        <section>
          <h2 className="flex items-center gap-2 text-sm font-semibold text-danger">
            <IconeAlerte taille={16} />À annoncer ({aAnnoncer.length})
          </h2>
          <p className="mt-1 text-xs text-texte-secondaire">
            Décidés, mais le groupeur ne le sait pas encore.
          </p>
          <ul className="mt-2 space-y-2">
            {aAnnoncer.map((dossier) => (
              <li key={dossier.id}>
                <LigneDossier
                  dossier={dossier}
                  actif={dossier.id === choisi}
                  urgent
                  onChoisir={onChoisir}
                />
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section>
        <h2 className="text-sm font-semibold text-texte">
          À examiner ({enAttente.length})
        </h2>
        <p className="mt-1 text-xs text-texte-secondaire">
          Du plus ancien au plus récent.
        </p>
        {enAttente.length === 0 ? (
          /* L'etat le plus frequent, et celui qu'on oublie de dessiner. */
          <p className="mt-2 rounded-xl border border-bordure bg-white p-4 text-sm text-texte-secondaire">
            Aucun dossier en attente. C&apos;est l&apos;état normal : traitez
            les dossiers le jour où ils arrivent et cette file reste vide.
          </p>
        ) : (
          <ul className="mt-2 space-y-2">
            {enAttente.map((dossier) => (
              <li key={dossier.id}>
                <LigneDossier
                  dossier={dossier}
                  actif={dossier.id === choisi}
                  onChoisir={onChoisir}
                />
              </li>
            ))}
          </ul>
        )}
      </section>
    </nav>
  );
}

function LigneDossier({
  dossier,
  actif,
  urgent,
  onChoisir,
}: {
  dossier: DossierApi;
  actif: boolean;
  urgent?: boolean;
  onChoisir: (id: number) => void;
}) {
  const jours = joursDAttente(dossier.cree_le);
  /* Au-dela de deux jours ouvres, on sort du delai annonce au groupeur a
     l'inscription. Il le voit, donc l'administrateur doit le voir aussi. */
  const horsDelai = jours > 2;

  return (
    <button
      type="button"
      onClick={() => onChoisir(dossier.id)}
      aria-current={actif ? "true" : undefined}
      className={`w-full rounded-xl border bg-white p-3 text-left transition-colors ${
        actif
          ? "border-texte ring-1 ring-texte"
          : urgent
            ? "border-danger"
            : "border-bordure hover:border-texte-secondaire"
      }`}
    >
      <span className="flex items-baseline gap-2">
        <span className="min-w-0 flex-1 truncate font-medium text-texte">
          {dossier.pseudonyme}
        </span>
        {urgent ? (
          <span className="shrink-0 text-xs font-semibold text-danger">
            {LIBELLE_CANAL[dossier.decisions_kyc[0].canal].toLowerCase()}
          </span>
        ) : (
          <span
            className={`shrink-0 text-xs ${
              horsDelai ? "font-semibold text-danger" : "text-texte-secondaire"
            }`}
          >
            {jours === 0 ? "aujourd'hui" : `${jours} j`}
          </span>
        )}
      </span>

      <span className="mt-1 flex items-center gap-3 text-xs text-texte-secondaire">
        <span className="flex items-center gap-1">
          {dossier.concordance_noms ? (
            <IconeCoche taille={14} />
          ) : (
            <IconeAlerte taille={14} />
          )}
          <span
            className={dossier.concordance_noms ? "" : "font-semibold text-danger"}
          >
            {dossier.concordance_noms ? "noms concordent" : "noms divergents"}
          </span>
        </span>
        <span>{dossier.pieces.length}/3 pièces</span>
        {dossier.courriel === "" ? <span>à appeler</span> : null}
      </span>
    </button>
  );
}

function FicheEnChargement() {
  return (
    <div className="space-y-4" aria-busy="true">
      {[120, 160, 200].map((hauteur) => (
        <div
          key={hauteur}
          className="rounded-xl border border-bordure bg-white p-6"
          style={{ minHeight: hauteur }}
        >
          <Squelette largeur="40%" hauteur={20} />
          <div className="mt-4 space-y-2">
            <Squelette largeur="90%" />
            <Squelette largeur="70%" />
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * La fiche, a droite.
 *
 * L'ordre suit celui de l'examen reel : **l'identite, le compte de retrait,
 * les pieces, puis la decision**. Le compte de retrait est en deuxieme
 * position et non en dernier parce que c'est lui qui arrete tout : s'il ne
 * concorde pas, l'administrateur n'a pas besoin de lire la suite.
 */
function Fiche({
  dossier,
  resultat,
  erreurDecision,
  enCours,
  onTrancher,
  onActerLAnnonce,
}: {
  dossier: DossierApi;
  resultat: ResultatDecision | undefined;
  erreurDecision: ErreurApi | undefined;
  enCours: boolean;
  onTrancher: (issue: Issue, canal: Canal, motif?: Motif) => void;
  onActerLAnnonce: () => void;
}) {
  const derniere = dossier.decisions_kyc[0];
  const aAnnoncer = derniere !== undefined && derniere.notifie_le === null;

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-bordure bg-white p-6">
        <div className="flex items-start gap-4">
          <div className="min-w-0 flex-1">
            <h2 className="text-xl font-semibold text-texte">
              {dossier.pseudonyme}
            </h2>
            <p className="mt-1 text-sm text-texte-secondaire">
              {/* Le pseudonyme est au-dessus et le nom reel en dessous : c'est
                  le pseudonyme qui identifie ce groupeur partout ailleurs dans
                  le produit (§1.7). */}
              {dossier.nom_complet} · {dossier.telephone}
              {dossier.courriel ? ` · ${dossier.courriel}` : ""}
            </p>
          </div>
          <span className="shrink-0 rounded-full bg-surface-douce px-3 py-1 text-xs font-medium text-texte-secondaire">
            {LIBELLE_ETAT[dossier.statut_kyc]}
          </span>
        </div>

        {dossier.courriel === "" ? (
          <p className="mt-4 rounded-[10px] bg-surface-douce px-3 py-2 text-sm text-texte-secondaire">
            Aucun courriel au dossier : la décision ne peut lui être annoncée
            que <strong className="font-semibold">par téléphone</strong>. Ce
            n&apos;est pas un dossier incomplet — une partie des groupeurs
            n&apos;a pas de messagerie consultée, et l&apos;exiger les
            écarterait.
          </p>
        ) : null}
      </div>

      {/* ── Contrôle n° 2, en premier parce qu'il arrete tout ───────────── */}
      <section
        className={`rounded-xl border bg-white p-6 ${
          dossier.concordance_noms ? "border-bordure" : "border-danger"
        }`}
      >
        <h3 className="flex items-center gap-2 font-semibold text-texte">
          {dossier.concordance_noms ? (
            <IconeCoche taille={18} />
          ) : (
            <IconeAlerte taille={18} />
          )}
          Contrôle n° 2 — compte de retrait
        </h3>

        <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
          <div>
            <dt className="text-texte-secondaire">Nom sur la pièce</dt>
            <dd className="font-medium text-texte">{dossier.nom_complet}</dd>
          </div>
          <div>
            <dt className="text-texte-secondaire">
              Titulaire du compte Mobile Money
            </dt>
            <dd
              className={`font-medium ${
                dossier.concordance_noms ? "text-texte" : "text-danger"
              }`}
            >
              {dossier.titulaire_mobile_money}
            </dd>
          </div>
        </dl>

        {dossier.concordance_noms ? null : (
          <p className="mt-3 rounded-[10px] bg-danger-fond px-3 py-2 text-sm text-danger">
            <strong className="font-semibold">
              La procédure s&apos;arrête.
            </strong>{" "}
            Il n&apos;y a pas de bonne raison de recevoir l&apos;argent des
            acheteurs sur le compte de quelqu&apos;un d&apos;autre. Refusez avec
            le motif « titulaire différent de la pièce ».
          </p>
        )}
      </section>

      {/* ── Contrôle n° 1 ────────────────────────────────────────────────── */}
      <section className="rounded-xl border border-bordure bg-white p-6">
        <h3 className="font-semibold text-texte">
          Contrôle n° 1 — pièces déposées
        </h3>
        <ul className="mt-3 space-y-2 text-sm">
          {(["piece-recto", "piece-verso", "selfie"] as const).map((nature) => {
            const piece = dossier.pieces.find((p) => p.nature === nature);
            return (
              <li key={nature} className="flex items-center gap-2">
                {piece ? (
                  <IconeCoche taille={16} />
                ) : (
                  <IconeAlerte taille={16} />
                )}
                <span className={piece ? "text-texte" : "text-danger"}>
                  {LIBELLE_PIECE_DEPOSEE[nature]}
                </span>
                {piece ? (
                  <code className="ml-auto rounded bg-surface-douce px-2 py-0.5 text-xs text-texte-secondaire">
                    {piece.reference}
                  </code>
                ) : (
                  <span className="ml-auto text-xs font-semibold text-danger">
                    manquante
                  </span>
                )}
              </li>
            );
          })}
        </ul>

        {/* ⚠️ Le point le plus facile a « ameliorer » par erreur. */}
        <p className="mt-4 rounded-[10px] bg-surface-douce px-3 py-2 text-xs text-texte-secondaire">
          <strong className="font-semibold">
            Les images ne s&apos;affichent pas ici, et ce n&apos;est pas une
            étape manquante.
          </strong>{" "}
          Le §10.5 exige que les pièces d&apos;identité et les selfies soient
          conservés hors du stockage des photos de produits, avec un accès
          restreint et une durée de conservation fixée. Ce stockage sera monté
          au déploiement ; d&apos;ici là l&apos;API ne renvoie qu&apos;une
          référence, et afficher une vignette supposerait une adresse servie
          publiquement.
        </p>

        {dossier.pieces.length < 3 ? (
          <p className="mt-3 rounded-[10px] bg-primaire-fond px-3 py-2 text-sm text-primaire-texte-sur-fond">
            Dossier incomplet. Renvoyez-le{" "}
            <strong className="font-semibold">à compléter</strong> plutôt que de
            le refuser : le reste du dossier est conservé, et refuser une pièce
            manquante ferait perdre un groupeur recrutable.
          </p>
        ) : null}
      </section>

      {/* ── Ce que le serveur a fait de la derniere decision ─────────────── */}
      {resultat ? <ResultatEnvoi resultat={resultat} /> : null}

      {erreurDecision ? (
        <p
          role="alert"
          className="rounded-xl border border-danger bg-danger-fond p-4 text-sm text-danger"
        >
          {erreurDecision.messageLisible}
        </p>
      ) : null}

      {aAnnoncer ? (
        <AnnonceAFaire
          dossier={dossier}
          enCours={enCours}
          script={resultat?.script}
          onActerLAnnonce={onActerLAnnonce}
        />
      ) : null}

      {dossier.statut_kyc === "en-verification" ? (
        /* ⚠️ **`key` n'est pas une formalite, c'est une correction de bug.**
           Sans elle, React garde le meme composant monte en passant d'un
           dossier a l'autre, et le formulaire conserve l'issue, le motif et le
           canal du precedent — un motif retenu s'appliquait au suivant, et le
           canal « courriel » restait choisi pour un groupeur qui n'en a pas.
           Invisible sur un dossier, systematique sur dix a la suite. */
        <FormulaireDecision
          key={dossier.id}
          dossier={dossier}
          enCours={enCours}
          onTrancher={onTrancher}
        />
      ) : null}

      {dossier.decisions_kyc.length > 0 ? (
        <Historique dossier={dossier} />
      ) : null}
    </div>
  );
}

/**
 * Ce que le serveur rapporte juste apres une decision.
 *
 * **C'est le texte reellement envoye**, pas une reconstitution. Sans lui,
 * l'administrateur annonce une decision sans savoir comment elle est
 * formulee, et ne peut pas repondre quand le groupeur rappelle en citant le
 * message.
 */
function ResultatEnvoi({ resultat }: { resultat: ResultatDecision }) {
  if (resultat.probleme) {
    return (
      <section
        role="alert"
        className="rounded-xl border border-danger bg-white p-6"
      >
        <h3 className="flex items-center gap-2 font-semibold text-danger">
          <IconeAlerte taille={18} />
          Décision enregistrée, mais pas annoncée
        </h3>
        <p className="mt-2 text-sm text-texte-secondaire">
          {resultat.a_refaire ?? resultat.probleme}
        </p>
        <p className="mt-2 text-xs text-texte-secondaire">
          Détail : {resultat.probleme}
        </p>
      </section>
    );
  }

  if (!resultat.annonce) {
    /* Un appel : le bandeau « a annoncer » prend le relais, script compris. */
    return null;
  }

  return (
    <section className="rounded-xl border border-succes bg-white p-6">
      <h3 className="flex items-center gap-2 font-semibold text-succes">
        <IconeCoche taille={18} />
        Courriel envoyé
      </h3>
      <p className="mt-2 text-sm text-texte-secondaire">
        Objet : {resultat.sujet}
      </p>
      <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap rounded-[10px] bg-surface-douce px-4 py-3 text-sm text-texte">
        {resultat.corps}
      </pre>
    </section>
  );
}

/**
 * Le bandeau d'un dossier tranche mais pas encore annonce.
 *
 * Il porte le **script a lire au telephone**, celui que le serveur a compose.
 * Un script n'est pas une formalite : sans lui, deux administrateurs annoncent
 * le meme refus de deux manieres differentes, et l'un des deux le dit mal un
 * jour de fatigue.
 */
function AnnonceAFaire({
  dossier,
  script,
  enCours,
  onActerLAnnonce,
}: {
  dossier: DossierApi;
  script: string | undefined;
  enCours: boolean;
  onActerLAnnonce: () => void;
}) {
  const decision = dossier.decisions_kyc[0];

  return (
    <section className="rounded-xl border border-danger bg-white p-6">
      <h3 className="flex items-center gap-2 font-semibold text-danger">
        <IconeAlerte taille={18} />
        Décision prise, groupeur pas encore prévenu
      </h3>
      <p className="mt-2 text-sm text-texte-secondaire">
        {decision.canal === "appel"
          ? `À appeler au ${dossier.telephone}.`
          : "Le courriel n'est pas parti. Appelez-le, ou tranchez à nouveau."}
      </p>

      {script ? (
        <pre className="mt-3 whitespace-pre-wrap rounded-[10px] bg-surface-douce px-4 py-3 text-sm text-texte">
          {script}
        </pre>
      ) : decision.canal === "appel" ? (
        /* Le script vient avec la reponse a la decision. En rechargeant la
           page, il n'est plus la : on le dit, plutot que d'en reconstituer un
           qui pourrait differer de celui que le serveur compose. */
        <p className="mt-3 rounded-[10px] bg-surface-douce px-4 py-3 text-sm text-texte-secondaire">
          Le script d&apos;appel s&apos;affiche au moment de la décision. Motif
          retenu : <strong>{decision.libelle_motif || "validation"}</strong>.
        </p>
      ) : null}

      <button
        type="button"
        disabled={enCours}
        onClick={onActerLAnnonce}
        className={`mt-4 rounded-xl px-4 py-2.5 text-sm font-semibold ${
          enCours
            ? "cursor-wait bg-surface-douce text-texte-secondaire"
            : "bg-texte text-white hover:opacity-90"
        }`}
      >
        {enCours ? "…" : "J'ai appelé — acter l'annonce"}
      </button>
      {/* ⚠️ Rien ne verifie cette declaration, et c'est pour cela qu'elle est
          un geste separe plutot qu'une case pre-cochee dans le formulaire de
          decision. Le journal est opposable (§18.3). */}
      <p className="mt-2 text-xs text-texte-secondaire">
        À cocher après avoir réellement appelé. Rien ne le vérifie, et ce
        journal est celui qu&apos;on produira en cas de litige.
      </p>
    </section>
  );
}

/**
 * Le formulaire de decision.
 *
 * **Le motif se choisit avant l'issue**, et l'ordre compte : choisir un motif
 * propose aussitot l'issue qui lui correspond — « photo illisible » propose
 * « a completer », pas « refuse ». L'administrateur peut toujours changer,
 * mais le defaut le pousse vers la decision la moins destructrice.
 */
function FormulaireDecision({
  dossier,
  enCours,
  onTrancher,
}: {
  dossier: DossierApi;
  enCours: boolean;
  onTrancher: (issue: Issue, canal: Canal, motif?: Motif) => void;
}) {
  const [issue, setIssue] = useState<Issue>("valide");
  const [motif, setMotif] = useState<Motif | "">("");
  /* Sans courriel, l'appel est le seul canal : on ne propose pas un choix
     dont une branche est impossible. */
  const [canal, setCanal] = useState<Canal>(
    dossier.courriel ? "courriel" : "appel",
  );

  const motifManquant = issue !== "valide" && motif === "";

  return (
    <section className="rounded-xl border border-bordure bg-white p-6">
      <h3 className="font-semibold text-texte">Décider</h3>

      <fieldset className="mt-4">
        <legend className="text-sm font-medium text-texte-secondaire">
          Issue
        </legend>
        <div className="mt-2 flex gap-2">
          {(
            [
              ["valide", "Valider"],
              ["a-completer", "À compléter"],
              ["refuse", "Refuser"],
            ] as const
          ).map(([valeur, libelle]) => (
            <button
              key={valeur}
              type="button"
              onClick={() => {
                setIssue(valeur);
                if (valeur === "valide") {
                  setMotif("");
                }
              }}
              aria-pressed={issue === valeur}
              className={`rounded-xl border px-4 py-2 text-sm font-medium ${
                issue === valeur
                  ? "border-texte bg-texte text-white"
                  : "border-bordure text-texte hover:border-texte-secondaire"
              }`}
            >
              {libelle}
            </button>
          ))}
        </div>
      </fieldset>

      {issue === "valide" ? (
        <p className="mt-4 rounded-[10px] bg-confiance-fond px-3 py-2 text-sm text-confiance">
          Niveau <strong className="font-semibold">Entrée</strong> : il pourra
          collecter jusqu&apos;à 150 000 F par groupage. Le plafond passe à
          600 000 F après trois groupages livrés sans litige.
        </p>
      ) : (
        <fieldset className="mt-4">
          <legend className="text-sm font-medium text-texte-secondaire">
            Motif — obligatoire
          </legend>
          <select
            value={motif}
            onChange={(evenement) => {
              const choisi = evenement.target.value as Motif;
              setMotif(choisi);
              /* Le motif propose l'issue, et non l'inverse : « photo
                 illisible » doit pousser vers « a completer ». */
              setIssue(issueProposee(choisi));
            }}
            className="mt-2 w-full rounded-xl border border-bordure bg-white px-3 py-2.5 text-sm text-texte"
          >
            <option value="">Choisir un motif…</option>
            {(Object.keys(MOTIFS) as Motif[]).map((cle) => (
              <option key={cle} value={cle}>
                {MOTIFS[cle].interne}
              </option>
            ))}
          </select>
          <p className="mt-2 text-xs text-texte-secondaire">
            Sans motif, le groupeur ne peut pas savoir quoi corriger, et
            personne ne pourra relire la décision dans six mois.
          </p>
        </fieldset>
      )}

      <fieldset className="mt-4">
        <legend className="text-sm font-medium text-texte-secondaire">
          Annoncer
        </legend>
        <div className="mt-2 flex gap-2">
          {(["courriel", "appel"] as const).map((valeur) => {
            const impossible = valeur === "courriel" && dossier.courriel === "";
            return (
              <button
                key={valeur}
                type="button"
                disabled={impossible}
                onClick={() => setCanal(valeur)}
                aria-pressed={canal === valeur}
                className={`rounded-xl border px-4 py-2 text-sm font-medium ${
                  impossible
                    ? "cursor-not-allowed border-bordure text-texte-secondaire opacity-50"
                    : canal === valeur
                      ? "border-texte bg-texte text-white"
                      : "border-bordure text-texte hover:border-texte-secondaire"
                }`}
              >
                {LIBELLE_CANAL[valeur]}
                {impossible ? " — aucun courriel" : ""}
              </button>
            );
          })}
        </div>
      </fieldset>

      {/* ⚠️ **Le texte exact n'est plus affiche avant d'appuyer**, et c'est un
          recul assume. Il etait auparavant reconstitue par le navigateur ;
          c'etait un second jeu de formulations a maintenir en parallele de
          `notifications.py`, et deux textes censes etre identiques finissent
          toujours par diverger — celui qu'on relit n'etant alors plus celui
          qu'on envoie, ce qui est pire que de ne rien relire.

          Ce qui s'affiche ici est donc le **resume** de ce qui partira ; le
          texte integral arrive du serveur juste apres la decision, et c'est
          celui qui a ete envoye. */}
      {issue !== "valide" && motif ? (
        <p className="mt-4 rounded-[10px] bg-surface-douce px-4 py-3 text-sm text-texte">
          {canal === "courriel" ? "Il recevra" : "Vous lui direz"} :{" "}
          {MOTIFS[motif].public}.{" "}
          <span className="text-texte-secondaire">
            {MOTIFS[motif].suite} Le texte complet s&apos;affiche après la
            décision.
          </span>
        </p>
      ) : null}

      <button
        type="button"
        disabled={motifManquant || enCours}
        onClick={() => onTrancher(issue, canal, motif || undefined)}
        className={`mt-4 rounded-xl px-5 py-2.5 text-sm font-semibold ${
          motifManquant || enCours
            ? "cursor-not-allowed bg-surface-douce text-texte-secondaire"
            : "bg-texte text-white hover:opacity-90"
        }`}
      >
        {enCours
          ? "Enregistrement…"
          : canal === "courriel"
            ? "Enregistrer et envoyer le courriel"
            : "Enregistrer — puis appeler"}
      </button>
    </section>
  );
}

function Historique({ dossier }: { dossier: DossierApi }) {
  return (
    <section className="rounded-xl border border-bordure bg-white p-6">
      <h3 className="font-semibold text-texte">Historique du dossier</h3>
      {/* ⚠️ Rien ne s'efface : un dossier repris produit une nouvelle ligne.
          C'est cet historique qui montre qu'un groupeur en est a sa troisieme
          tentative — information qu'un champ d'etat seul perdrait, et qui est
          exactement celle qui doit faire hesiter avant de valider. */}
      <ol className="mt-3 space-y-2 text-sm">
        {dossier.decisions_kyc.map((decision) => (
          <li
            key={decision.id}
            className="flex items-baseline gap-3 border-b border-filet pb-2 last:border-b-0 last:pb-0"
          >
            <span className="w-24 shrink-0 text-texte-secondaire">
              {decision.decide_le.slice(0, 10)}
            </span>
            <span className="min-w-0 flex-1">
              <strong className="font-semibold text-texte">
                {decision.issue === "valide"
                  ? "Validé"
                  : decision.issue === "a-completer"
                    ? "Renvoyé à compléter"
                    : "Refusé"}
              </strong>
              {decision.libelle_motif ? ` — ${decision.libelle_motif}` : ""}
              <span className="block text-xs text-texte-secondaire">
                par {decision.decide_par} ·{" "}
                {LIBELLE_CANAL[decision.canal].toLowerCase()} ·{" "}
                {decision.notifie_le
                  ? `annoncé le ${decision.notifie_le.slice(0, 10)}`
                  : "annonce à faire"}
              </span>
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}
