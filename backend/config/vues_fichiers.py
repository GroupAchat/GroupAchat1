# -*- coding: utf-8 -*-
"""Les fichiers téléversés, et qui a le droit de les lire.

Deux régimes, et la distinction n'est pas un détail :

- **Les photos de produits et de campagnes sont publiques.** Elles sont
  faites pour être vues par des visiteurs sans compte.
- **Les pièces d'identité ne le sont pas.** Une carte nationale sous une URL
  devinable, c'est une fuite de données personnelles — et la confiance de
  tous les groupeurs avec.

D'où un chemin public qui **refuse explicitement** le dossier ``kyc/``, et
une route séparée, authentifiée, pour les pièces.
"""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.views.static import serve

from groupachat.comptes.models import DossierKYC

# Le dossier réservé, tel qu'il apparaît dans `upload_to`.
DOSSIER_PRIVE = "kyc"


def media_publique(requete: HttpRequest, chemin: str) -> HttpResponse:
    """Sert un fichier téléversé public.

    ⚠️ Le refus de ``kyc/`` est répété ici **en plus** de l'expression de
    route : une route se réécrit en deux secondes, et une faute de frappe y
    exposerait des pièces d'identité sans que rien ne le signale.
    """
    premier = Path(chemin).parts[0] if chemin else ""
    if premier == DOSSIER_PRIVE:
        raise Http404("Fichier introuvable.")
    return serve(requete, chemin, document_root=settings.MEDIA_ROOT)


def piece_kyc(requete: HttpRequest, dossier_id: int, cote: str) -> HttpResponse:
    """Sert le recto ou le verso d'un dossier, à qui a le droit de le voir.

    Deux lecteurs légitimes : **le groupeur lui-même**, qui doit pouvoir
    relire ce qu'il a déposé, et **l'équipe**, qui doit le vérifier.
    """
    if cote not in {"recto", "verso"}:
        raise Http404("Côté inconnu.")

    utilisateur = requete.user
    if not utilisateur.is_authenticated:
        # 404 et non 403 : répondre « interdit » confirmerait que ce dossier
        # existe, ce qui est déjà une information de trop.
        raise Http404("Fichier introuvable.")

    dossier = DossierKYC.objects.filter(pk=dossier_id).first()
    if dossier is None:
        raise Http404("Fichier introuvable.")

    autorise = utilisateur.est_equipe or dossier.utilisateur_id == utilisateur.id
    if not autorise:
        raise Http404("Fichier introuvable.")

    fichier = dossier.piece_recto if cote == "recto" else dossier.piece_verso
    if not fichier:
        raise Http404("Aucune pièce de ce côté.")

    # `FileResponse` diffuse le fichier au lieu de le charger en mémoire.
    reponse = FileResponse(fichier.open("rb"))
    # Ces pièces ne doivent rester dans aucun cache intermédiaire.
    reponse["Cache-Control"] = "private, no-store"
    return reponse
