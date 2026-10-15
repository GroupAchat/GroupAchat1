import { useRef, useState } from "react";
import { IconeFermer } from "../../ui/Icones";

/**
 * Le champ photo de l'ecran 11 — prendre ou choisir une photo du produit.
 *
 * ## ⚠️ La photo est reduite **avant** de partir, et c'est tout l'interet
 *
 * Le public vise a un **forfait data limite** (§18.1 et §5 du cahier des
 * charges). Une photo d'Android d'entree de gamme pese 3 a 5 Mo : la
 * televerser telle quelle couterait a l'acheteur **plus cher que sa part**,
 * sur un ecran dont le but est de lui faire economiser de l'argent. Ce serait
 * la seule fonction du produit a travailler contre lui.
 *
 * Elle est donc redessinee dans un `<canvas>` a 1 280 px de cote maximum,
 * reencodee en JPEG a 70 %, et pese alors 100 a 250 ko. Le serveur refuse
 * au-dela de 300 ko (`domaine.PHOTO_DEMANDE_MAX_OCTETS`), donc la reduction
 * n'est pas un confort : sans elle, presque toutes les photos seraient
 * rejetees.
 *
 * ## ⚠️ Ce qui arrive quand la reduction echoue
 *
 * `canvas.toBlob` peut rendre `null`, et une image peut ne pas se decoder.
 * Dans ces deux cas **on n'envoie pas l'original** : il serait refuse par le
 * serveur, apres avoir consomme le forfait. On refuse localement avec un
 * message qui dit quoi faire.
 *
 * ## Ce que ce champ ne fait pas
 *
 * **Pas de recadrage, pas de rotation, pas de filtre.** Le §1.0 veut un
 * formulaire qu'on remplit en marchant ; un editeur d'image y ajouterait un
 * ecran. Une photo de travers reste lisible par un groupeur.
 */

/** Le cote le plus long apres reduction. */
const COTE_MAXIMUM = 1280;

/** La qualite JPEG. 70 % : au-dela le poids double sans gain visible ici. */
const QUALITE = 0.7;

/** Ce que le serveur accepte — garde-fou local, pour refuser avant d'envoyer. */
const POIDS_MAXIMUM = 300 * 1024;

export default function ChampPhoto({
  photo,
  apercu,
  onChanger,
}: {
  /** La photo reduite, prete a partir. `undefined` quand il n'y en a pas. */
  photo?: Blob;
  /** L'URL d'apercu, tenue par le parent pour pouvoir la revoquer. */
  apercu?: string;
  onChanger: (photo: Blob | undefined, apercu: string | undefined) => void;
}) {
  const entree = useRef<HTMLInputElement>(null);
  const [travail, setTravail] = useState(false);
  const [erreur, setErreur] = useState<string>();

  const choisir = async (fichier: File) => {
    setErreur(undefined);
    setTravail(true);
    try {
      const reduite = await reduire(fichier);
      if (reduite.size > POIDS_MAXIMUM) {
        /* Tres rare apres reduction, mais possible sur une image enorme et
           tres bruitee. On le dit plutot que d'essuyer un refus du serveur. */
        setErreur(
          "Cette photo reste trop lourde même réduite. Essayez-en une autre.",
        );
        return;
      }
      onChanger(reduite, URL.createObjectURL(reduite));
    } catch {
      setErreur(
        "Cette photo n'a pas pu être préparée. Choisissez une image JPEG ou PNG.",
      );
    } finally {
      setTravail(false);
      /* Remis a zero pour que rechoisir **le meme** fichier redeclenche
         `change` : sans cela, un deuxieme essai apres une erreur ne ferait
         rien, et l'acheteur croirait l'application figee. */
      if (entree.current) {
        entree.current.value = "";
      }
    }
  };

  return (
    <div>
      <p className="text-sm font-medium text-texte">
        Une photo du produit (facultatif)
      </p>
      <p className="mt-1 text-sm text-texte-secondaire">
        « Un pagne comme celui-là » se montre mieux qu'il ne s'écrit. La photo
        est réduite sur votre téléphone avant l'envoi.
      </p>

      <input
        ref={entree}
        id="photo-demande"
        type="file"
        /* `capture` absent volontairement : il forcerait l'appareil photo,
           alors que la photo cherchee est souvent deja dans la galerie — une
           capture d'ecran d'un groupe WhatsApp, par exemple. */
        accept="image/jpeg,image/png,image/webp"
        className="sr-only"
        onChange={(evenement) => {
          const fichier = evenement.target.files?.[0];
          if (fichier) {
            void choisir(fichier);
          }
        }}
      />

      {apercu ? (
        <div className="mt-3 flex items-start gap-3">
          <img
            src={apercu}
            alt="La photo que vous avez choisie"
            className="size-24 shrink-0 rounded-[10px] border border-bordure object-cover"
          />
          <div className="min-w-0">
            <p className="text-sm text-texte-secondaire">
              {photo
                ? `Prête à envoyer — ${Math.round(photo.size / 1024)} ko`
                : ""}
            </p>
            <button
              type="button"
              onClick={() => {
                /* ⚠️ La revocation appartient au parent, qui tient l'URL :
                   la faire ici laisserait le parent avec une adresse morte
                   s'il la reutilisait. */
                onChanger(undefined, undefined);
                setErreur(undefined);
              }}
              className="mt-1 inline-flex min-h-11 items-center gap-1.5 text-sm font-medium text-primaire"
            >
              <IconeFermer taille={16} />
              Retirer la photo
            </button>
          </div>
        </div>
      ) : (
        <label
          htmlFor="photo-demande"
          className="mt-3 flex min-h-13 w-full cursor-pointer items-center justify-center rounded-[10px] border border-dashed border-bordure px-4 text-sm font-medium text-primaire"
        >
          {travail ? "Préparation…" : "Ajouter une photo"}
        </label>
      )}

      {erreur ? (
        <p role="alert" className="mt-2 text-sm text-danger">
          {erreur}
        </p>
      ) : null}
    </div>
  );
}

/**
 * Redessine l'image a `COTE_MAXIMUM` et la reencode en JPEG.
 *
 * `createImageBitmap` plutot qu'une `<img>` et son `onload` : il decode hors
 * du fil principal, donc l'interface ne se fige pas sur une photo de 5 Mo.
 */
async function reduire(fichier: File): Promise<Blob> {
  const image = await createImageBitmap(fichier);
  try {
    const facteur = Math.min(
      1,
      COTE_MAXIMUM / Math.max(image.width, image.height),
    );
    /* `Math.max(1, …)` : une image de 1 px de haut donnerait un canvas de
       hauteur 0, que `toBlob` refuse. */
    const largeur = Math.max(1, Math.round(image.width * facteur));
    const hauteur = Math.max(1, Math.round(image.height * facteur));

    const toile = document.createElement("canvas");
    toile.width = largeur;
    toile.height = hauteur;

    const pinceau = toile.getContext("2d");
    if (!pinceau) {
      throw new Error("Canvas indisponible");
    }
    /* Fond blanc : un PNG transparent reencode en JPEG aurait un fond noir,
       et la photo paraitrait abimee. */
    pinceau.fillStyle = "#ffffff";
    pinceau.fillRect(0, 0, largeur, hauteur);
    pinceau.drawImage(image, 0, 0, largeur, hauteur);

    return await new Promise<Blob>((resoudre, rejeter) => {
      toile.toBlob(
        (blob) =>
          blob ? resoudre(blob) : rejeter(new Error("Réencodage impossible")),
        "image/jpeg",
        QUALITE,
      );
    });
  } finally {
    /* Libere la memoire du decodage : sur un Android d'entree de gamme, trois
       photos de 5 Mo gardees en bitmap suffisent a faire tuer l'onglet. */
    image.close();
  }
}
