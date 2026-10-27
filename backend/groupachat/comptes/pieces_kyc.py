# -*- coding: utf-8 -*-
"""Pièces d'identité du dossier KYC : format, nom de stockage, nettoyage.

Ces fichiers restent sur le disque du serveur (jamais Cloudinary) et ne sont
relus que par la vue `/pieces/<id>/<côté>/`. Ce module ne touche à aucun
modèle : `models.py` y prend `chemin_piece`, le sérialiseur y prend le champ.
"""

from __future__ import annotations

import logging
import uuid
import warnings

from django.conf import settings
from rest_framework import serializers

logger = logging.getLogger(__name__)

# Le format que Pillow détecte dans les octets, pas l'extension ni le type
# MIME annoncés par le client : tous deux se falsifient en renommant un
# fichier. « MPO » est le JPEG multi-image que produisent certains
# téléphones Android : c'est une photo JPEG ordinaire pour l'utilisateur.
EXTENSION_PAR_FORMAT = {"JPEG": "jpg", "MPO": "jpg", "PNG": "png", "WEBP": "webp"}
EXTENSIONS_AUTORISEES = frozenset(EXTENSION_PAR_FORMAT.values())

# 25 Mpx couvrent les meilleurs capteurs de téléphone courants. Au-delà, la
# photo est une « bombe de décompression » en puissance : 89 octets peuvent
# annoncer 100 Mpx, que le navigateur de l'administrateur devrait décoder
# pour afficher la pièce. La dimension se lit dans l'en-tête, sans décoder.
PIXELS_MAX_PIECE = 25_000_000

MESSAGE_NON_LISIBLE = "Ce fichier n'est pas une photo lisible (JPEG, PNG ou WebP)."


def chemin_piece(instance, nom_fichier: str) -> str:
    """Nom de stockage aléatoire.

    Le nom d'origine vient du téléphone (« CNI_Komlan_Mensah.jpg ») : le
    garder mettrait une identité dans le disque et dans les journaux. Seule
    l'extension, déjà tirée du format détecté par le champ, est conservée.
    """
    extension = nom_fichier.rsplit(".", 1)[-1].lower()
    if extension not in EXTENSIONS_AUTORISEES:
        extension = "jpg"
    return f"kyc/{uuid.uuid4().hex}.{extension}"


class PieceKycField(serializers.ImageField):
    """Une photo de pièce : JPEG, PNG ou WebP, 8 Mo au plus, obligatoire."""

    def __init__(self, cote: str, **kwargs):
        absente = f"Joignez la photo du {cote} de votre pièce."
        kwargs.setdefault("write_only", True)
        kwargs["error_messages"] = {
            "required": absente,
            "null": absente,
            # Un texte ou un objet JSON au lieu d'un fichier.
            "invalid": absente,
            "empty": MESSAGE_NON_LISIBLE,
            "invalid_image": MESSAGE_NON_LISIBLE,
        }
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        # Avant Pillow : inutile de décoder un fichier qu'on va refuser, et le
        # plafond global de Django ne dit pas quel champ est en cause.
        taille = getattr(data, "size", None)
        if taille is not None and taille > settings.TAILLE_MAX_PIECE_OCTETS:
            maximum = settings.TAILLE_MAX_PIECE_OCTETS // (1024 * 1024)
            raise serializers.ValidationError(
                f"Image trop lourde : {maximum} Mo au maximum."
            )

        # Django refuse une image dont le NOM a une extension hors de sa
        # liste (« photo » sans extension, « IMG.heic ») avec un message
        # anglais. Le nom envoyé ne prouve rien : on le remplace avant, et
        # seul le contenu décide.
        if hasattr(data, "read") and hasattr(data, "name"):
            data.name = "piece.jpg"

        # Pillow signale par un avertissement (pas une erreur) les images de
        # 89 à 178 Mpx : sans ce filtre, un avertissement promu en erreur
        # deviendrait un 500. Notre plafond tranche juste après.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fichier = super().to_internal_value(data)
        extension = EXTENSION_PAR_FORMAT.get(fichier.image.format)
        largeur, hauteur = fichier.image.size
        if extension is None or largeur * hauteur > PIXELS_MAX_PIECE:
            self.fail("invalid_image")
        # Nom neutre : l'extension suit le contenu réel, jamais le nom envoyé.
        fichier.name = f"piece.{extension}"
        return fichier


def supprimer_fichiers(stockage, noms: list[str]) -> None:
    """Efface des pièces du disque ; un échec est journalisé, pas propagé.

    Appelé après coup (redépôt, annulation) : la requête principale a déjà
    réussi, un fichier qui résiste ne doit pas la défaire.
    """
    for nom in noms:
        if not nom:
            continue
        try:
            stockage.delete(nom)
        except OSError:
            logger.warning("Pièce KYC non supprimée : %s", nom, exc_info=True)
