# -*- coding: utf-8 -*-
"""Django sert lui-même les deux applications compilées.

**Pourquoi pas de serveur web devant.** Coolify termine déjà le TLS et route
par domaine ; ajouter nginx n'apporterait qu'un conteneur de plus à construire,
surveiller et mettre à jour. WhiteNoise, déjà installé, sert les fichiers
compilés aussi bien ; cette vue se contente de rendre la bonne page d'entrée.

**Le choix se fait sur le domaine**, pas sur un préfixe d'URL :

    achatgr.com         → la boutique      (index.html)
    admin.achatgr.com   → l'administration (admin.html)

Les deux applications gardent ainsi leurs routes à la racine — aucune n'a
besoin d'un préfixe de base — et chacune parle à l'API depuis sa propre
origine. Ni CORS, ni cookie tiers.
"""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import View


def _racine_web() -> Path:
    return Path(settings.RACINE_WEB)


def _page_pour(hote: str) -> str:
    """La page d'entrée qui correspond à ce domaine."""
    nom = hote.split(":")[0].lower()
    prefixes = [p.strip().lower() for p in settings.HOTES_ADMINISTRATION if p.strip()]
    if any(nom == p or nom.startswith(f"{p}.") for p in prefixes):
        return "admin.html"
    return "index.html"


# ⚠️ `method_decorator`, et non `@never_cache` posé directement sur `get`.
# `never_cache` attend une **fonction de vue** dont le premier argument est la
# requête ; appliqué à une méthode, il reçoit `self` à la place et échoue en
# TypeError dès le premier affichage.
@method_decorator(never_cache, name="dispatch")
class ApplicationCompilee(View):
    """Rend la page d'entrée pour toute adresse non prise par l'API.

    C'est la reprise dont a besoin une application à navigation côté client :
    sans elle, rafraîchir la page sur « /mes-achats » renverrait un 404, alors
    que cette adresse n'existe que dans le navigateur.
    """

    # Jamais mise en cache : son contenu change à chaque déploiement, et c'est
    # elle qui désigne les fichiers compilés par leur empreinte. Une version
    # gardée en cache ferait réclamer des fichiers qui n'existent plus.
    def get(self, requete: HttpRequest, *args, **kwargs) -> HttpResponse:
        fichier = _racine_web() / _page_pour(requete.get_host())
        if not fichier.is_file():
            # En développement, le front est servi par Vite : cette vue n'a
            # rien à rendre, et le dire est plus utile qu'une page blanche.
            raise Http404(
                "Aucune application compilée. En développement, ouvrez le "
                "serveur Vite ; en production, vérifiez l'étape de "
                "construction du front."
            )
        return HttpResponse(
            fichier.read_bytes(), content_type="text/html; charset=utf-8"
        )
