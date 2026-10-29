# -*- coding: utf-8 -*-
"""Limitation du nombre de tentatives.

**Le piège : au Togo, beaucoup d'abonnés mobiles partagent une même adresse
IP publique** (les opérateurs font de la traduction d'adresses à grande
échelle). Une limite posée uniquement sur l'adresse IP bloquerait donc tout
un quartier parce qu'une seule personne insiste.

D'où deux lignes de défense complémentaires :

1. **Par numéro de téléphone**, pour ce qui vise un compte précis — vérifier
   un code, en redemander un. C'est la limite qui compte vraiment, et elle
   ne gêne personne d'autre que la cible.
2. **Par adresse IP**, plus large, pour ce qui n'a pas encore de numéro
   identifiable — la connexion, l'inscription. Volontairement généreuse.

⚠️ Ces limites s'appuient sur le cache de Django. Avec le cache en mémoire
par défaut, **chaque processus Gunicorn tient son propre compteur** : la
limite réelle est donc multipliée par le nombre de processus. C'est pourquoi
la protection qui compte — le nombre de codes émis — est tenue **en base**,
dans :meth:`CodeVerification.emettre`, et non ici.
"""

from __future__ import annotations

from rest_framework.throttling import (
    AnonRateThrottle,
    SimpleRateThrottle,
    UserRateThrottle,
)


class LimiteParNumero(SimpleRateThrottle):
    """Compte les tentatives visant **un numéro donné**, d'où qu'elles viennent.

    Changer d'adresse IP ne remet donc pas le compteur à zéro — c'est tout
    l'intérêt face à quelqu'un qui cherche à deviner un code à six chiffres.
    """

    def get_cache_key(self, requete, vue) -> str | None:
        numero = ""
        if isinstance(requete.data, dict):
            numero = str(requete.data.get("telephone", ""))

        # Mêmes huit chiffres que ceux stockés en base : sans normalisation,
        # « +228 90 00 11 22 » et « 90001122 » auraient deux compteurs.
        chiffres = "".join(c for c in numero if c.isdigit())[-8:]
        if len(chiffres) != 8:
            # Numéro absent ou malformé : rien à limiter ici, la validation
            # du sérialiseur s'en chargera.
            return None
        return self.cache_format % {"scope": self.scope, "ident": chiffres}


class LimiteVerification(LimiteParNumero):
    """Essais de code pour un numéro."""

    scope = "verification"


class LimiteRenvoi(LimiteParNumero):
    """Demandes d'un nouveau code pour un numéro.

    La plus serrée des trois : chaque appel enverra un vrai SMS le jour où
    une passerelle sera branchée, et c'est elle qui permettrait sinon de
    contourner la limite d'essais en redemandant un code neuf.
    """

    scope = "renvoi_code"


class LimiteConnexion(AnonRateThrottle):
    """Tentatives de connexion depuis une même adresse.

    Large à dessein : derrière une IP d'opérateur il peut y avoir des
    centaines de personnes légitimes.
    """

    scope = "connexion"


class LimiteInscription(AnonRateThrottle):
    """Créations de compte depuis une même adresse."""

    scope = "inscription"


class LimiteDepotKyc(UserRateThrottle):
    """Dépôts de dossier KYC d'un même compte.

    Par **compte** et non par adresse : l'utilisateur est déjà identifié et
    vérifié, et une IP d'opérateur est partagée par tout un quartier. Sans
    limite, un compte qui se fait rejeter pouvait renvoyer des pièces de
    plusieurs mégaoctets en boucle et remplir le disque. Ne compte que les
    dépôts qui **écrivent** (la vue l'appelle après validation) : se tromper
    de numéro ne doit pas coûter un dépôt.

    ⚠️ Le compteur vit dans le cache, donc par processus : avec plusieurs
    processus ou après un redémarrage, la limite est contournable.
    """

    scope = "depot_kyc"


class LimiteEssaisKyc(UserRateThrottle):
    """Toutes les tentatives de dépôt d'un compte, valides ou non.

    Plafond large qui protège la bande passante : un 400 n'écrit rien mais
    la requête, elle, a transporté jusqu'à plusieurs Mo. Même réserve que
    ci-dessus : le compteur est dans le cache, par processus.
    """

    scope = "essais_kyc"
