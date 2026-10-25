# -*- coding: utf-8 -*-
"""L'hébergement des images et des vidéos, chez Cloudinary.

**Pourquoi un service extérieur.** Les groupeurs photographient au téléphone :
une photo pèse trois à cinq mégaoctets, et la même image repart ensuite vers
chaque acheteur qui ouvre la fiche. Servir cela depuis le conteneur Django
reviendrait à payer la bande passante deux fois et à faire attendre un
acheteur de Lomé le temps d'un aller-retour jusqu'au serveur. Cloudinary
redimensionne, recompresse en WebP ou AVIF selon le navigateur, et sert
depuis un point proche.

**Ce qui n'y va jamais : les pièces d'identité.** Elles restent sur le disque
du serveur, derrière une vue qui vérifie qui demande. Une adresse de CDN est
publique même quand elle est illisible ; un document d'identité qui fuite ne
se rattrape pas.

**Pourquoi l'envoi est direct.** Le navigateur téléverse chez Cloudinary sans
passer par l'API : Django ne fait que signer l'autorisation. Faire transiter
le fichier doublerait l'attente sur une connexion mesurée et immobiliserait un
travailleur Gunicorn pendant toute la montée.

Sans variables d'environnement, tout retombe sur le stockage local : les tests
et le jeu de démonstration n'ont pas besoin d'un compte Cloudinary.
"""

from __future__ import annotations

import time

import cloudinary
import cloudinary.uploader
import cloudinary.utils
from django.conf import settings

# Les dossiers où atterrissent les fichiers chez Cloudinary. Un dossier par
# usage : on peut purger les campagnes sans toucher au catalogue, et une
# règle de modération se pose sur un dossier, pas sur un compte entier.
DOSSIER_PRODUITS = "groupachat/produits"
DOSSIER_CAMPAGNES = "groupachat/campagnes"
DOSSIERS_AUTORISES = {DOSSIER_PRODUITS, DOSSIER_CAMPAGNES}

# Une signature vaut une heure. Assez pour une vidéo sur une connexion lente,
# assez court pour qu'un lien intercepté ne serve pas le lendemain.
VALIDITE_SIGNATURE = 3600


def actif() -> bool:
    """Cloudinary est-il configuré ?

    Les trois valeurs sont exigées ensemble : avec deux sur trois, les envois
    partiraient et échoueraient à la signature, ce qui est plus difficile à
    diagnostiquer qu'un repli franc sur le disque local.
    """
    return all(
        (
            settings.CLOUDINARY_CLOUD_NAME,
            settings.CLOUDINARY_API_KEY,
            settings.CLOUDINARY_API_SECRET,
        )
    )


def _configurer() -> None:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


def signer_envoi(dossier: str, genre: str) -> dict:
    """L'autorisation que le navigateur présente à Cloudinary.

    Le dossier et le type de ressource sont **inclus dans la signature** : un
    client qui les modifierait invaliderait l'autorisation. Sans cela,
    n'importe quel compte vérifié pourrait déposer où bon lui semble dans le
    compte Cloudinary.
    """
    if dossier not in DOSSIERS_AUTORISES:
        raise ValueError(f"Dossier non autorisé : {dossier}")
    _configurer()

    type_ressource = "video" if genre == "video" else "image"
    horodatage = int(time.time())
    parametres = {"folder": dossier, "timestamp": horodatage}
    signature = cloudinary.utils.api_sign_request(
        parametres, settings.CLOUDINARY_API_SECRET
    )
    return {
        "cloud_name": settings.CLOUDINARY_CLOUD_NAME,
        "api_key": settings.CLOUDINARY_API_KEY,
        "type_ressource": type_ressource,
        "dossier": dossier,
        "horodatage": horodatage,
        "signature": signature,
        "expire_dans": VALIDITE_SIGNATURE,
        "adresse": (
            f"https://api.cloudinary.com/v1_1/{settings.CLOUDINARY_CLOUD_NAME}"
            f"/{type_ressource}/upload"
        ),
    }


def adresse(public_id: str, genre: str = "image", **transformations) -> str:
    """L'adresse de livraison d'un média déjà hébergé.

    ``f_auto`` et ``q_auto`` sont systématiques : le navigateur reçoit du
    WebP ou de l'AVIF s'il sait les lire, au poids que Cloudinary juge
    suffisant. C'est de loin ce qui change le plus pour un acheteur sur
    forfait de données.
    """
    _configurer()
    type_ressource = "video" if genre == "video" else "image"
    url, _ = cloudinary.utils.cloudinary_url(
        public_id,
        resource_type=type_ressource,
        fetch_format="auto",
        quality="auto",
        secure=True,
        **transformations,
    )
    return url


def vignette(public_id: str, cote: int = 400) -> str:
    """Un carré recadré, pour les bandes de vignettes et les listes.

    Le recadrage se fait chez Cloudinary plutôt que dans le navigateur : une
    vignette de 400 pixels pèse quelques dizaines de kilo-octets là où
    l'original en fait quatre mille.
    """
    return adresse(
        public_id, "image", width=cote, height=cote, crop="fill", gravity="auto"
    )


def apercu_video(public_id: str, cote: int = 400) -> str:
    """L'image figée d'une vidéo, extraite par Cloudinary.

    Évite de demander au groupeur une photo d'aperçu en plus de sa vidéo :
    une étape de moins dans un formulaire rempli au téléphone.
    """
    _configurer()
    url, _ = cloudinary.utils.cloudinary_url(
        public_id,
        resource_type="video",
        format="jpg",
        width=cote,
        height=cote,
        crop="fill",
        gravity="auto",
        quality="auto",
        secure=True,
    )
    return url


def supprimer(public_id: str, genre: str = "image") -> None:
    """Retire un média de Cloudinary.

    L'échec est avalé volontairement : si le fichier a déjà disparu là-bas,
    ou si le réseau est coupé, cela ne doit pas empêcher de supprimer la
    ligne en base. Un orphelin chez Cloudinary coûte quelques octets ; une
    suppression qui échoue laisse une fiche cassée à l'écran.
    """
    if not actif():
        return
    _configurer()
    try:
        cloudinary.uploader.destroy(
            public_id, resource_type="video" if genre == "video" else "image"
        )
    except Exception:  # noqa: BLE001 — voir la note ci-dessus
        pass
