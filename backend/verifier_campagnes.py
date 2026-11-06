import os, django
os.environ["DJANGO_FORCER_SQLITE"] = "1"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from groupachat.catalogue.models import Produit, Campagne, Categorie

print("=== PRODUITS (Total:", Produit.objects.count(), ") ===")
for p in Produit.objects.all():
    print(f"- [ID {p.id}] {p.nom} (Cat: {p.categorie.nom if p.categorie else 'Aucune'}, Medias: {p.medias.count()})")

print("\n=== CAMPAGNES (Total:", Campagne.objects.count(), ") ===")
for c in Campagne.objects.all():
    print(f"- [ID {c.id}] {c.titre} | Statut: {c.statut} | Publiée: {c.publiee_le}")

print("\n=== CATEGORIES ===")
for cat in Categorie.objects.all():
    print(f"- {cat.nom} (slug: {cat.slug})")
