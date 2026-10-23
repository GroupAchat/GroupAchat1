# -*- coding: utf-8 -*-
"""Routes de Group Achat."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from config.vues_spa import ApplicationCompilee

urlpatterns = [
    path("administration/", admin.site.urls),
    path("api/", include("groupachat.api")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ⚠️ **En dernier, toujours.** Cette route attrape tout ce qui reste : placee
# avant les autres, elle avalerait l'API et l'administration Django.
urlpatterns += [
    re_path(r"^(?!api/|administration/|medias/|statiques/).*$",
            ApplicationCompilee.as_view(), name="application"),
]
