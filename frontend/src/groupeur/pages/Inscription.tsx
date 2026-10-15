import { useEffect, useState } from "react";
import { formaterFrancs } from "../../domaine/format";
import {
  LIBELLE_OPERATEUR,
  LIBELLE_PIECE,
  nomsConcordent,
  type Operateur,
  PLAFOND_PAR_NIVEAU,
  type TypePiece,
} from "../../domaine/inscription";
import { deposerUnDossier, type MonDossierApi } from "../../api/dossiers";
import { useAction } from "../../api/useRequete";
import { DELAI_ANNONCE } from "../../domaine/recrutement";
import {
  DEMONSTRATION,
  GROUPEUR_DEMO,
  valeurDemo,
} from "../../domaine/demonstration";
import { EnTeteGroupeur } from "../mise-en-page/ChromeGroupeur";
import Bouton from "../../ui/Bouton";
import Champ from "../../ui/Champ";
import Encart from "../../ui/Encart";
import FriseEtapes from "../../ui/FriseEtapes";
import { IconeCoche, IconeDepot } from "../../ui/Icones";

/**
 * L'inscription d'un groupeur — §10.5 du cahier des charges.
 *
 * **Quatre etapes, et pas sept controles.** Le formulaire ne couvre que le
 * **niveau Entree** : piece d'identite avec selfie, concordance du compte
 * Mobile Money, telephone verifie. Les references, le lieu d'activite et le
 * contrat viennent au niveau Confirme, apres trois campagnes livrees.
 *
 * Demander tout des la premiere minute ferait fuir exactement les commercants
 * que l'on cherche : **la plupart des bons groupeurs sont dans l'informel**, et
 * le recrutement est deja le goulot d'etranglement du lancement.
 *
 * ⚠️ **Le controle n° 2 arrete tout.** Si le nom du titulaire du compte Mobile
 * Money ne correspond pas a la piece d'identite, la procedure s'arrete — il
 * n'y a pas de bonne raison de recevoir l'argent des acheteurs sur le compte
 * de quelqu'un d'autre. Le formulaire le signale **a la saisie**, pas quatre
 * heures plus tard : c'est la meme logique que le filtre de moderation, un
 * garde-fou plutot qu'une punition.
 *
 * Le **pseudonyme** est demande en premier et explique : c'est la seule chose
 * que les acheteurs verront de lui (§1.7). Son nom reel ne sort jamais vers
 * eux — et le lui dire des l'inscription evite qu'il le decouvre en se
 * demandant si on l'a expose.
 *
 * **Le selfie n'est pas decoratif** : sans lui, une piece volee suffit.
 *
 * ## Ce qui se passe apres l'envoi
 *
 * **Rien d'automatique.** Le dossier part dans la file d'attente de l'ecran
 * A2, un administrateur l'ouvre, et il tranche — valide, a completer, ou
 * refuse avec un motif. La reponse arrive **par courriel si le groupeur en a
 * depose un, par telephone sinon**, et jamais seulement dans l'application :
 * quelqu'un qui attend une reponse ne reouvre pas une application tous les
 * jours pour voir si elle est arrivee.
 *
 * ⚠️ **Le tableau de bord s'ouvre, mais la creation de groupage reste
 * fermee** jusqu'a la validation. C'est le point d'equilibre : le faire
 * attendre devant une porte close lui ferait oublier le produit, mais le
 * laisser creer un groupage avant examen nous ferait garantir « vous etes
 * livre, ou rembourse » sur le compte de quelqu'un dont nous ne savons rien.
 * Voir `domaine/recrutement.ts`.
 */
type Etape = 1 | 2 | 3 | 4 | "depose";

export default function Inscription({
  onRetour,
  onTermine,
}: {
  onRetour: () => void;
  /**
   * Appelee quand il quitte l'ecran de depot.
   *
   * Elle rend **ce qu'il vient de saisir**, et les deux champs ont une raison
   * d'etre la :
   *
   * - **le courriel** — vide s'il n'en a pas depose — parce que l'ecran
   *   suivant doit pouvoir ecrire « reponse par courriel a telle adresse » ou
   *   « nous vous appellerons ». Quelqu'un qui ne sait pas s'il doit
   *   surveiller sa boite ou son telephone surveille les deux, puis ni l'un ni
   *   l'autre, et rate l'appel ;
   * - **le pseudonyme**, parce que le tableau de bord salue son titulaire.
   *   Sans lui, quelqu'un qui vient de taper « Essai Ecran » etait accueilli
   *   par « Bonjour Mama Gro » — le groupeur du jeu de demonstration. Ce
   *   genre de detail est ce qui fait douter du reste de l'ecran.
   *
   * ⚠️ Ce n'est qu'un **pansement sur une absence d'API** : les autres ecrans
   * du cote groupeur lisent toujours les constantes de demonstration et
   * continueront d'afficher les campagnes de Mama Gro. La correction de fond
   * est de brancher `GET /api/groupeurs/dossier/`.
   */
  onTermine: (depot: {
    courriel: string;
    pseudonyme: string;
    telephone: string;
    /** Ce que le serveur a enregistre : etat, plafond, identifiant. */
    dossier: MonDossierApi;
  }) => void;
}) {
  const [etape, setEtape] = useState<Etape>(1);

  /* ⚠️ **En demonstration, le dossier part rempli.** Les champs restent a
     l'ecran et restent modifiables : ce qui disparait, c'est la saisie au
     clavier devant quelqu'un qui regarde, pas les ecrans. Voir
     `domaine/demonstration.ts` pour rallumer. */
  const [pseudonyme, setPseudonyme] = useState(
    valeurDemo(GROUPEUR_DEMO.pseudonyme),
  );
  const [nomComplet, setNomComplet] = useState(
    valeurDemo(GROUPEUR_DEMO.nomComplet),
  );
  const [telephone, setTelephone] = useState(valeurDemo(GROUPEUR_DEMO.telephone));
  const [courriel, setCourriel] = useState(valeurDemo(GROUPEUR_DEMO.courriel));
  const [typePiece, setTypePiece] = useState<TypePiece>("cni");
  const [numeroPiece, setNumeroPiece] = useState(
    valeurDemo(GROUPEUR_DEMO.numeroPiece),
  );
  const [pieceDeposee, setPieceDeposee] = useState(DEMONSTRATION);
  const [selfieDepose, setSelfieDepose] = useState(DEMONSTRATION);
  const [operateur, setOperateur] = useState<Operateur>("t-money");
  const [titulaire, setTitulaire] = useState(valeurDemo(GROUPEUR_DEMO.titulaire));
  const [numeroMobileMoney, setNumeroMobileMoney] = useState(
    valeurDemo(GROUPEUR_DEMO.telephone),
  );
  const [code, setCode] = useState(valeurDemo(GROUPEUR_DEMO.code));
  const [dossierDepose, setDossierDepose] = useState<MonDossierApi>();

  /**
   * Le depot du dossier sur l'API.
   *
   * ⚠️ **Aucun fichier n'est reellement envoye**, et il ne faut pas le laisser
   * croire. Le §10.5 exige que les pieces d'identite et les selfies soient
   * conserves hors du stockage des photos de produits, avec un acces restreint
   * et une duree de conservation fixee ; ce stockage sera monte au deploiement
   * sur le VPS. D'ici la, le dossier porte **une reference de place**, et les
   * boutons « Prendre la photo » n'ouvrent pas l'appareil.
   *
   * C'est volontairement visible dans le code plutot que masque derriere un
   * faux televersement : une interface qui fait semblant d'envoyer une piece
   * d'identite est pire qu'une interface qui dit ne pas encore savoir le
   * faire.
   */
  const depot = useAction(deposerUnDossier);

  const concordance =
    titulaire.trim() === "" || nomsConcordent(nomComplet, titulaire);

  /**
   * Envoie le dossier, et **ramene a l'etape fautive** si le serveur refuse.
   *
   * Le renvoi n'est pas un detail d'ergonomie : les erreurs du serveur portent
   * sur des champs saisis deux ou trois ecrans plus tot. Afficher « ce numero
   * est deja utilise » sous le clavier du code SMS laisserait quelqu'un
   * chercher longtemps.
   */
  const envoyer = async () => {
    const resultat = await depot.executer({
      pseudonyme: pseudonyme.trim(),
      nom_complet: nomComplet.trim(),
      telephone: `+228${telephone.replace(/\D/g, "")}`,
      courriel: courriel.trim(),
      titulaire_mobile_money: titulaire.trim(),
      numero_mobile_money: `+228${numeroMobileMoney.replace(/\D/g, "")}`,
      /* ⚠️ References de place : aucun fichier n'est televerse. Voir `depot`. */
      pieces: [
        { nature: "piece-recto", reference: `depot/${Date.now()}/recto` },
        { nature: "piece-verso", reference: `depot/${Date.now()}/verso` },
        { nature: "selfie", reference: `depot/${Date.now()}/selfie` },
      ],
    });

    if (resultat) {
      setDossierDepose(resultat);

      /* ⚠️ **En demonstration, on ne passe pas par l'ecran d'attente.**
         Le serveur vient de valider le dossier (reglage `DEMONSTRATION`), donc
         « un administrateur l'examine, reponse sous 48 h » serait faux — et
         le tableau de bord derriere ne serait pas celui de l'attente. On entre
         directement dans l'espace groupeur, qui est ce qu'on venait voir. */
      if (DEMONSTRATION) {
        onTermine({
          courriel,
          pseudonyme,
          telephone: `+228${telephone.replace(/\D/g, "")}`,
          dossier: resultat,
        });
        return;
      }

      setEtape("depose");
      return;
    }
  };

  /**
   * ⚠️ **En demonstration, le bouton ne retient jamais.**
   *
   * Hors demonstration il retient comme avant : ces quatre controles
   * correspondent a ce que le serveur exigera, et le prevenir ici evite un
   * aller-retour pour rien.
   */
  const etapeComplete =
    DEMONSTRATION ||
    etape === 1
      ? pseudonyme.trim() !== "" &&
        nomComplet.trim() !== "" &&
        telephone.replace(/\D/g, "").length >= 8
      : etape === 2
        ? numeroPiece.trim() !== "" && pieceDeposee && selfieDepose
        : etape === 3
          ? titulaire.trim() !== "" &&
            numeroMobileMoney.replace(/\D/g, "").length >= 8 &&
            concordance
          : code.length === 4;

  /* Ramene a l'etape qui porte le champ refuse. Hors du rendu : changer
     d'etape pendant qu'on dessine est un effet de bord que React signale. */
  const champsRefuses = depot.erreur?.champs;
  useEffect(() => {
    if (!champsRefuses) {
      return;
    }
    const cible = ETAPE_DU_CHAMP[Object.keys(champsRefuses)[0] ?? ""];
    if (cible !== undefined) {
      setEtape(cible);
    }
  }, [champsRefuses]);

  if (etape === "depose") {
    return (
      <div className="mx-auto min-h-dvh max-w-[430px] bg-white pb-10">
        <EnTeteGroupeur titre="Dossier déposé" />
        <div className="space-y-6 px-4 pt-8">
          <div className="text-center">
            <span className="mx-auto flex size-18 items-center justify-center rounded-full bg-succes-fond text-succes">
              <IconeCoche taille={40} />
            </span>
            <h2 className="mt-4 text-2xl font-semibold text-texte">
              Votre dossier est déposé
            </h2>
            <p className="mt-2 text-texte-secondaire">
              {/* **Le mot « examine » est important.** Il dit qu'un humain
                  regarde, et c'est exactement ce qui est vendu a l'acheteur
                  sur chaque ecran. Ecrire « validation en cours » laisserait
                  croire a une formalite automatique. */}
              Un administrateur l&apos;examine, dossier par dossier. Réponse
              sous {DELAI_ANNONCE}.
            </p>
          </div>

          <FriseEtapes
            indiceEnCours={1}
            etapes={[
              { libelle: "Dossier déposé", detail: "il y a quelques instants" },
              { libelle: "Examen par un administrateur", detail: `sous ${DELAI_ANNONCE}` },
              {
                libelle: "Notre réponse",
                detail: courriel
                  ? `par courriel à ${courriel}`
                  : "par téléphone, au numéro déposé",
              },
            ]}
          />

          {/* ⚠️ **Dire par ou la reponse arrive, et le dire ici.** Quelqu'un
              qui ne sait pas s'il doit surveiller sa boite ou son telephone
              surveille les deux, puis ni l'un ni l'autre — et rate l'appel. */}
          <Encart
            variante="info"
            role="groupeur"
            titre={courriel ? "Surveillez votre courriel" : "Nous vous appellerons"}
          >
            {courriel ? (
              <>
                Nous écrirons à <strong className="font-semibold">{courriel}</strong>{" "}
                pour vous dire si votre dossier est validé, et sinon pourquoi.
                Nous pouvons aussi vous appeler au numéro déposé.
              </>
            ) : (
              <>
                Vous n&apos;avez pas déposé de courriel : un administrateur vous
                appellera au numéro indiqué pour vous dire si votre dossier est
                validé, et sinon pourquoi.
              </>
            )}
          </Encart>

          {/* ⚠️ **Le bouton n'ouvre pas les droits, il ouvre la vue.** Tant
              que le dossier n'est pas valide, le tableau de bord s'affiche en
              lecture seule et la creation de groupage est fermee — le libelle
              le dit, pour que personne ne croie avoir ete valide en appuyant.
              Le verrou reel est cote serveur, dans `Campagne.save()`. */}
          <Bouton
            role="groupeur"
            onClick={() =>
              dossierDepose &&
              onTermine({
                courriel,
                pseudonyme,
                telephone: `+228${telephone.replace(/\D/g, "")}`,
                dossier: dossierDepose,
              })
            }
          >
            Voir mon tableau de bord en attendant
          </Bouton>

          <p className="text-center text-xs text-texte-secondaire">
            Vous ne pourrez créer votre premier groupage qu&apos;après la
            validation de votre dossier. Plafond au départ :{" "}
            {formaterFrancs(PLAFOND_PAR_NIVEAU.entree ?? 0)} par groupage, puis{" "}
            {formaterFrancs(PLAFOND_PAR_NIVEAU.confirme ?? 0)} après trois
            groupages livrés sans litige.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto min-h-dvh max-w-[430px] bg-white pb-28">
      <EnTeteGroupeur
        titre="Devenir groupeur"
        sousTitre={`Étape ${etape} sur 4`}
        onRetour={etape === 1 ? onRetour : () => setEtape((etape - 1) as Etape)}
      />

      <div className="flex gap-1 px-4 pt-3">
        {[1, 2, 3, 4].map((n) => (
          <span
            key={n}
            aria-hidden="true"
            className={`h-1 flex-1 rounded-full ${n <= etape ? "bg-confiance" : "bg-bordure"}`}
          />
        ))}
      </div>

      <div className="space-y-5 px-4 pt-5">
        {etape === 1 ? (
          <>
            <h2 className="text-lg font-semibold text-texte">Qui êtes-vous ?</h2>

            <Champ
              libelle="Votre pseudonyme"
              valeur={pseudonyme}
              onChanger={setPseudonyme}
              exemple="Mama Gro"
              aide="C'est la seule chose que les acheteurs verront de vous."
            />

            <Champ
              libelle="Votre nom complet"
              valeur={nomComplet}
              onChanger={setNomComplet}
              exemple="Akossiwa Mensah"
              aide="Tel qu'il figure sur votre pièce d'identité. Jamais communiqué aux acheteurs."
            />

            <Champ
              libelle="Votre numéro de téléphone"
              valeur={telephone}
              onChanger={setTelephone}
              type="tel"
              inputMode="tel"
              prefixe="+228"
              exemple="90 12 34 56"
            />

            {/* ⚠️ **Facultatif, et il doit le rester.** Une partie des
                commercants qu'on cherche — souvent dans l'informel — n'a pas
                d'adresse de messagerie consultee, mais repond au telephone.
                Rendre ce champ obligatoire ecarterait exactement ceux-la,
                alors que le recrutement est le goulot d'etranglement du
                lancement (§10.5). Le telephone etant obligatoire, personne
                n'est injoignable : la decision se dit alors de vive voix. */}
            <Champ
              libelle="Votre courriel (facultatif)"
              valeur={courriel}
              onChanger={setCourriel}
              type="email"
              inputMode="email"
              exemple="mama.gro@exemple.tg"
              aide="Pour recevoir la décision sur votre dossier par écrit. Sans courriel, nous vous appellerons."
            />
          </>
        ) : null}

        {etape === 2 ? (
          <>
            <h2 className="text-lg font-semibold text-texte">
              Votre pièce d&apos;identité
            </h2>
            <p className="text-texte-secondaire">
              Elle reste dans un stockage à accès restreint et ne sert
              qu&apos;à la vérification.
            </p>

            <div>
              <label htmlFor="type-piece" className="block text-sm font-medium text-texte">
                Type de pièce
              </label>
              <select
                id="type-piece"
                value={typePiece}
                onChange={(e) => setTypePiece(e.target.value as TypePiece)}
                className="mt-1.5 h-13 w-full rounded-[10px] border border-bordure bg-white px-3 text-texte outline-none focus:border-2 focus:border-confiance"
              >
                {(Object.keys(LIBELLE_PIECE) as TypePiece[]).map((cle) => (
                  <option key={cle} value={cle}>
                    {LIBELLE_PIECE[cle]}
                  </option>
                ))}
              </select>
            </div>

            <Champ
              libelle="Numéro de la pièce"
              valeur={numeroPiece}
              onChanger={setNumeroPiece}
              exemple="1234567890"
            />

            <ZoneDepot
              titre="Recto et verso de la pièce"
              detail="Les quatre coins visibles, sans reflet."
              depose={pieceDeposee}
              onDeposer={() => setPieceDeposee(true)}
            />

            {/* Sans le selfie, une piece volee suffit. */}
            <ZoneDepot
              titre="Selfie en tenant la pièce"
              detail="Votre visage et la pièce sur la même photo, lisibles tous les deux."
              depose={selfieDepose}
              onDeposer={() => setSelfieDepose(true)}
            />
          </>
        ) : null}

        {etape === 3 ? (
          <>
            <h2 className="text-lg font-semibold text-texte">
              Où recevoir vos retraits
            </h2>
            <p className="text-texte-secondaire">
              C&apos;est sur ce compte que partira l&apos;argent collecté par
              vos campagnes.
            </p>

            <div>
              <p className="text-sm font-medium text-texte">Opérateur</p>
              <div className="mt-2 grid grid-cols-2 gap-3">
                {(Object.keys(LIBELLE_OPERATEUR) as Operateur[]).map((cle) => (
                  <button
                    key={cle}
                    type="button"
                    aria-pressed={operateur === cle}
                    onClick={() => setOperateur(cle)}
                    className={`flex h-16 items-center justify-center rounded-xl border font-semibold ${
                      operateur === cle
                        ? "border-2 border-confiance bg-confiance-fond text-confiance"
                        : "border-bordure text-texte"
                    }`}
                  >
                    {LIBELLE_OPERATEUR[cle]}
                  </button>
                ))}
              </div>
            </div>

            <Champ
              libelle="Nom du titulaire du compte"
              valeur={titulaire}
              onChanger={setTitulaire}
              exemple={nomComplet || "Akossiwa Mensah"}
              erreur={
                concordance
                  ? undefined
                  : "Ce nom ne correspond pas à celui de votre pièce d'identité."
              }
              aide={
                concordance
                  ? "Il doit correspondre exactement à votre pièce d'identité."
                  : undefined
              }
            />

            {/* Le controle qui arrete la procedure. On l'explique au lieu de
                le subir : la raison est simple et elle protege le groupeur
                autant que nous. */}
            {!concordance ? (
              <Encart
                variante="danger"
                role="groupeur"
                titre="Nous ne pouvons pas continuer"
              >
                L&apos;argent de vos acheteurs ne peut partir que sur un compte
                à votre nom. Si vous utilisez le compte d&apos;un proche,
                ouvrez un compte à votre nom avant de continuer.
              </Encart>
            ) : null}

            <Champ
              libelle="Numéro du compte"
              valeur={numeroMobileMoney}
              onChanger={setNumeroMobileMoney}
              type="tel"
              inputMode="tel"
              prefixe="+228"
              exemple="90 12 34 56"
            />
          </>
        ) : null}

        {etape === 4 ? (
          <>
            <h2 className="text-lg font-semibold text-texte">
              Vérifions votre numéro
            </h2>
            <p className="text-texte-secondaire">
              Code envoyé au +228 {telephone}.
            </p>

            <div className="flex justify-center gap-3">
              {[0, 1, 2, 3].map((indice) => (
                <input
                  key={indice}
                  value={code[indice] ?? ""}
                  onChange={(e) => {
                    const chiffre = e.target.value.replace(/\D/g, "").slice(-1);
                    const suivant = code.split("");
                    suivant[indice] = chiffre;
                    setCode(suivant.join("").slice(0, 4));
                  }}
                  inputMode="numeric"
                  maxLength={1}
                  aria-label={`Chiffre ${indice + 1} sur 4`}
                  className="size-14 rounded-[10px] border border-bordure text-center text-2xl font-semibold text-texte outline-none focus:border-2 focus:border-confiance"
                />
              ))}
            </div>

            <p className="text-center text-xs text-texte-secondaire">
              Démonstration — aucun SMS n&apos;est envoyé. Le code est{" "}
              <strong className="font-semibold">1234</strong>.
            </p>

            <Encart variante="info" role="groupeur" titre="Ce qui vous attend">
              Votre dossier sera examiné par un administrateur sous{" "}
              {DELAI_ANNONCE}, puis nous vous répondrons{" "}
              {courriel ? "par courriel" : "par téléphone"}. Vous pourrez
              collecter jusqu&apos;à{" "}
              {formaterFrancs(PLAFOND_PAR_NIVEAU.entree ?? 0)} par groupage au
              départ.
            </Encart>
          </>
        ) : null}
      </div>

      <div className="fixed inset-x-0 bottom-0 z-20 mx-auto max-w-[430px] bg-white px-4 py-3 shadow-[0_-2px_12px_rgba(29,25,22,0.06)]">
        {/* L'erreur se place **au-dessus du bouton**, dans le bandeau fixe :
            c'est le seul endroit toujours visible quand on vient d'appuyer.
            Plus haut dans le formulaire, elle serait hors de l'ecran. */}
        {depot.erreur ? (
          <p role="alert" className="mb-2 text-sm font-medium text-danger">
            {depot.erreur.estRefusDeSaisie
              ? premiereErreur(depot.erreur.champs)
              : depot.erreur.messageLisible}
          </p>
        ) : null}

        <Bouton
          role="groupeur"
          desactive={!etapeComplete}
          chargement={depot.enCours}
          onClick={() => {
            if (etape !== 4) {
              setEtape((etape + 1) as Etape);
              return;
            }
            void envoyer();
          }}
        >
          {etape === 4 ? "Déposer mon dossier" : "Continuer"}
        </Bouton>
      </div>
    </div>
  );
}

/** Une zone de depot de document. Elle confirme visiblement le depot. */
function ZoneDepot({
  titre,
  detail,
  depose,
  onDeposer,
}: {
  titre: string;
  detail: string;
  depose: boolean;
  onDeposer: () => void;
}) {
  return (
    <div
      className={`rounded-xl border border-dashed p-4 text-center ${
        depose ? "border-succes bg-succes-fond" : "border-bordure"
      }`}
    >
      {depose ? (
        <IconeCoche taille={28} className="mx-auto text-succes" />
      ) : (
        <IconeDepot taille={28} className="mx-auto text-texte-secondaire" />
      )}
      <p
        className={`mt-2 font-medium ${depose ? "text-succes" : "text-texte"}`}
      >
        {depose ? `${titre} — déposé` : titre}
      </p>
      {depose ? null : (
        <p className="mt-1 text-sm text-texte-secondaire">{detail}</p>
      )}
      {depose ? null : (
        <div className="mx-auto mt-3 max-w-56">
          <Bouton role="groupeur" style="secondaire" onClick={onDeposer}>
            Prendre la photo
          </Bouton>
        </div>
      )}
    </div>
  );
}

/**
 * A quelle etape se corrige chaque champ refuse par le serveur.
 *
 * Les cles sont celles de `InscriptionSerializer`. Un champ absent de cette
 * table laisse l'utilisateur ou il est, avec le message affiche : c'est le
 * comportement sur, pour un champ ajoute cote serveur et pas encore ici.
 */
const ETAPE_DU_CHAMP: Record<string, 1 | 2 | 3 | 4 | undefined> = {
  pseudonyme: 1,
  nom_complet: 1,
  telephone: 1,
  courriel: 1,
  pieces: 2,
  titulaire_mobile_money: 3,
  numero_mobile_money: 3,
};

/**
 * Le premier message a montrer, parmi ceux que le serveur a renvoyes.
 *
 * Un seul, et non la liste : corriger un champ fait souvent disparaitre les
 * autres, et un bandeau de quatre lignes sur un telephone cache le formulaire
 * qu'il faut corriger.
 */
function premiereErreur(champs: Record<string, string[]>): string {
  return Object.values(champs)[0]?.[0] ?? "Le dépôt a échoué.";
}
