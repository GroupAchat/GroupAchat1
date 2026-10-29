# -*- coding: utf-8 -*-
"""Routes de Group Achat."""

from django.contrib import admin
from django.urls import include, path, re_path

from config.service.fichiers import media_publique, piece_kyc
from config.service.application import ApplicationCompilee

urlpatterns = [
    path("administration/", admin.site.urls),
    path("api/", include("groupachat.api")),

    # ── Les fichiers téléversés ─────────────────────────────────────────────
    #
    # Servis par Django en production aussi, puisqu'il n'y a plus de serveur
    # web devant. L'expression refuse le dossier « kyc/ » ; la vue le refuse
    # une seconde fois, par sécurité.
    re_path(r"^medias/(?!kyc/)(?P<chemin>.*)$", media_publique, name="media"),

    # Les pièces d'identité, réservées à leur propriétaire et à l'équipe.
    path("pieces/<int:dossier_id>/<str:cote>/", piece_kyc, name="piece-kyc"),
]

# Pas de `static(MEDIA_URL…)` en développement : il servait `MEDIA_ROOT` tel
# quel, `kyc/` compris, sans passer par `media_publique`. La route ci-dessus
# sert déjà les médias publics, DEBUG ou non.

# ⚠️ **En dernier, toujours.** Cette route attrape tout ce qui reste : placee
# avant les autres, elle avalerait l'API et l'administration Django.
urlpatterns += [
    re_path(r"^(?!api/|administration/|medias/|statiques/|pieces/).*$",
            ApplicationCompilee.as_view(), name="application"),
]
