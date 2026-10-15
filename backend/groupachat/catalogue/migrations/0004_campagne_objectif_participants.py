# -*- coding: utf-8 -*-
"""Le groupeur declare combien de personnes il veut reunir.

C'est le denominateur de la barre de progression des cartes (§2.5 de la spec des
ecrans). Le champ est **obligatoire** : sans lui, la barre n'a rien a remplir.

⚠️ **Les groupages deja en base n'en avaient pas**, et il faut leur en donner un
qui ne soit pas absurde. Un chiffre fixe pour tout le monde donnerait des barres
fausses dans les deux sens : un groupage a 2 acheteurs afficherait 10 %, un
groupage a 41 afficherait un debordement. On le deduit donc de ce que chaque
groupage a reellement fait — voir ``objectif_vraisemblable``.
"""

import django.core.validators
from django.db import migrations, models


def objectif_vraisemblable(apps, schema_editor):
    """Un objectif plausible pour chaque groupage deja en base.

    La regle : **le nombre d'acheteurs deja confirmes, arrondi vers le haut a la
    dizaine**, et au moins 10. Un groupage a 32 acheteurs se voit donc attribuer
    40, ce qui donne une barre a 80 % — credible et parlante. Un groupage sans
    aucune commande part a 10.

    Ce n'est pas la verite : le groupeur n'a jamais declare ce chiffre, il
    n'existait pas. C'est une reprise de donnees, et elle vaut mieux qu'un 10
    uniforme qui ferait deborder les barres des gros groupages.
    """
    Campagne = apps.get_model("catalogue", "Campagne")
    Commande = apps.get_model("commandes", "Commande")

    #: Les statuts qui comptent comme payes. Recopies plutot qu'importes : une
    #: migration doit rester lisible dans dix ans, meme si la constante bouge.
    payants = (
        "payee",
        "cloturee",
        "chez-le-groupeur",
        "en-livraison",
        "livree",
    )

    for campagne in Campagne.objects.all():
        confirmes = Commande.objects.filter(
            campagne=campagne, statut__in=payants
        ).count()
        objectif = max(10, -(-confirmes // 10) * 10)
        Campagne.objects.filter(pk=campagne.pk).update(
            objectif_participants=objectif
        )


def oublier(apps, schema_editor):
    """Rien a defaire : le champ disparait avec la marche arriere."""


class Migration(migrations.Migration):

    dependencies = [
        ("catalogue", "0003_campagne_medias"),
        # La reprise lit les commandes pour deduire un objectif plausible.
        ("commandes", "0003_versement_devient_retrait"),
    ]

    operations = [
        migrations.AddField(
            model_name="campagne",
            name="objectif_participants",
            field=models.PositiveIntegerField(
                # ⚠️ Valeur ponctuelle, le temps d'ajouter la colonne. La
                # reprise juste apres remplace chaque ligne, et le
                # `preserve_default=False` de l'operation empeche ce 10 de
                # rester dans le modele — un objectif par defaut finirait par
                # etre publie sans que personne ne l'ait choisi.
                default=10,
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name="objectif de participants",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(objectif_vraisemblable, oublier),
    ]
