# -*- coding: utf-8 -*-
"""Routes de Group Achat."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from config.vues_fichiers import media_publique, piece_kyc
from config.vues_spa import ApplicationCompilee

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

if settings.DEBUG:
    # Doublon inoffensif en développement, pratique quand on sert les médias
    # avec le rechargement automatique.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ⚠️ **En dernier, toujours.** Cette route attrape tout ce qui reste : placee
# avant les autres, elle avalerait l'API et l'administration Django.
urlpatterns += [
    re_path(r"^(?!api/|administration/|medias/|statiques/|pieces/).*$",
            ApplicationCompilee.as_view(), name="application"),
]
