import { useEffect, useRef, useState } from "react";

/**
 * Un message qui s'affiche, puis s'en va. §1.0.
 *
 * ## Pourquoi il a fallu l'ecrire
 *
 * Il sert d'abord au partage. Sur un ordinateur, `navigator.share` n'existe
 * pas : le bouton copie le lien dans le presse-papier, et **une copie est
 * invisible**. Sans retour a l'ecran, le bouton se comporte exactement comme
 * les boutons morts qu'on vient de brancher — on clique, rien ne bouge, on
 * reclique. Dire « Lien copie » est ce qui transforme l'action en
 * fonctionnalite.
 *
 * ## Il est neutre, et c'est voulu
 *
 * `texte` `#1D1916` avec du blanc dessus : **17,46:1**, le meme rapport que du
 * `texte` sur blanc puisqu'un contraste ne depend pas du sens. Il traverse
 * donc les deux chromes du §1.2 — l'orange acheteur et le bleu confiance —
 * sans avoir a connaitre celui dans lequel il tombe, et sans jamais risquer le
 * blanc sur `marque` (2,87:1) que le §1.2 interdit.
 *
 * ## Ce qu'il n'est pas
 *
 * Ce n'est pas un systeme de notifications. Il ne s'empile pas, il ne garde
 * pas d'historique, et **rien d'important ne doit passer par lui** : un
 * message qui disparait tout seul est un message que personne n'est oblige
 * d'avoir lu. Une erreur de paiement s'affiche sous le champ, pas ici.
 */
export default function Fugitif({ message }: { message?: string }) {
  if (message === undefined) {
    return null;
  }

  return (
    /*
     * `aria-live="polite"` plutot qu'`assertive` : on annonce la copie, on
     * n'interrompt pas la lecture en cours. Le conteneur porte
     * `role="status"`, donc le lecteur d'ecran lit le texte au moment ou il
     * apparait.
     *
     * Au-dessus du bouton flottant des questions (`z-30`) : les deux occupent
     * le bas de l'ecran, et c'est le message qui doit se voir.
     */
    <div
      role="status"
      aria-live="polite"
      className="pointer-events-none fixed inset-x-0 bottom-24 z-40 flex justify-center px-4 sm:bottom-8"
    >
      <p className="max-w-sm rounded-full bg-texte px-4 py-2.5 text-center text-sm font-medium text-white shadow-[0_4px_20px_rgba(29,25,22,0.28)]">
        {message}
      </p>
    </div>
  );
}

/**
 * Le message fugitif et de quoi l'annoncer.
 *
 * Le minuteur est **remis a zero a chaque annonce** : deux copies de suite ne
 * doivent pas faire disparaitre la seconde au bout du reste du delai de la
 * premiere. Et il est annule au demontage, sinon React avertit d'un etat pose
 * sur un composant qui n'existe plus — ce qui arrive vraiment ici, puisqu'on
 * peut partager une fiche puis la quitter aussitot.
 */
export function useFugitif(duree = 2600) {
  const [message, setMessage] = useState<string>();
  const minuteur = useRef<number>(undefined);

  useEffect(() => () => window.clearTimeout(minuteur.current), []);

  const annoncer = (texte: string) => {
    window.clearTimeout(minuteur.current);
    setMessage(texte);
    minuteur.current = window.setTimeout(() => setMessage(undefined), duree);
  };

  return { message, annoncer };
}
