# -*- coding: utf-8 -*-
"""Envoi des codes de vérification.

Aucun opérateur SMS n'est branché pour l'instant. L'expédition passe donc par
une **passerelle simulée** qui se contente de journaliser le message et de
rendre le code à l'appelant, pour que l'interface puisse l'afficher.

Tout passe par :func:`envoyer_code`, de sorte que brancher un vrai fournisseur
revienne à écrire une seconde passerelle et à changer ``SMS_FOURNISSEUR`` —
sans toucher aux vues.
"""

from __future__ import annotations

import logging

from django.conf import settings

from groupachat.comptes.models import CodeVerification

journal = logging.getLogger(__name__)

# Les noms que peut prendre la passerelle factice. Plusieurs, parce que le
# fichier de configuration et la documentation ne l'appellent pas toujours
# pareil, et qu'un écart de vocabulaire ne doit pas faire tomber l'inscription.
PASSERELLES_SIMULEES = frozenset({"console", "demonstration", "simulation", ""})


class ResultatEnvoi:
    """Ce que l'API peut dire de l'envoi sans trahir de secret.

    ``code_affiche`` ne vaut quelque chose qu'en mode simulé : dès qu'un vrai
    fournisseur est branché, il reste à ``None`` et le code ne sort jamais du
    serveur.
    """

    def __init__(self, simule: bool, code_affiche: str | None = None):
        self.simule = simule
        self.code_affiche = code_affiche


def envoyer_code(utilisateur) -> ResultatEnvoi:
    """Émet un code neuf et le « transmet » au numéro de l'utilisateur."""
    verification = CodeVerification.emettre(utilisateur)
    message = (
        f"Group Achat : votre code de vérification est {verification.code}. "
        f"Il expire dans {settings.VALIDITE_CODE_SMS_MINUTES} minutes."
    )

    if settings.SMS_FOURNISSEUR in PASSERELLES_SIMULEES:
        journal.info("SMS simulé vers %s — %s", utilisateur.telephone, message)
        return ResultatEnvoi(simule=True, code_affiche=verification.code)

    raise NotImplementedError(
        f"Aucune passerelle SMS pour « {settings.SMS_FOURNISSEUR} »."
    )
