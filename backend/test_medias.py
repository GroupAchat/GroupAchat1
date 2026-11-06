import os, django
os.environ["DJANGO_FORCER_SQLITE"] = "1"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from groupachat.catalogue.models import Produit, Campagne
from groupachat.catalogue.serialiseurs import CampagneResumeSerialiseur

for c in Campagne.objects.filter(id__gte=74).order_by("id"):
    p = c.produit
    s = CampagneResumeSerialiseur(c).data
    print(f"Campagne {c.id}: {c.titre}")
    print(f"  Produit {p.id}: {p.nom}")
    print(f"  Medias count: {p.medias.count()}")
    for m in p.medias.all():
        print(f"    Media {m.id}: fichier={m.fichier.name}, url={m.adresse}, vignette={m.adresse_vignette}")
    print(f"  Serialized image: {s['produit']['image']}")
