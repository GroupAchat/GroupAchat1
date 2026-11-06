import os, django
os.environ["DJANGO_FORCER_SQLITE"] = "1"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from groupachat.catalogue.models import Campagne, Categorie

print(f"Total Campagnes actives: {Campagne.objects.filter(statut='en_cours').count()}")
for c in Campagne.objects.filter(statut='en_cours').order_by('-publiee_le'):
    print(f"- [{c.id}] {c.titre} | Cat: {c.produit.categorie.nom if c.produit.categorie else 'N/A'} | Image: {c.produit.image_principale.adresse if c.produit.image_principale else 'SANS IMAGE'}")
