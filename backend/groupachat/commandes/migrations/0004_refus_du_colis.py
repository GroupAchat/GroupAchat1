# -*- coding: utf-8 -*-
"""Le refus du colis a la remise (ecran 9).

Trois champs seulement, tous facultatifs : le refus est l'exception, pas le
cas courant. Rien a reprendre sur les commandes existantes — une commande
jamais refusee a bien un motif vide, et c'est la verite.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commandes', '0003_versement_devient_retrait'),
    ]

    operations = [
        migrations.AddField(
            model_name='commande',
            name='description_du_refus',
            field=models.TextField(blank=True, verbose_name='description du refus'),
        ),
        migrations.AddField(
            model_name='commande',
            name='motif_de_refus',
            field=models.CharField(blank=True, choices=[('pas-le-produit', "Ce n'est pas le produit commandé"), ('abime', 'Produit visiblement abîmé'), ('autre', 'Autre')], max_length=20, verbose_name='motif du refus'),
        ),
        migrations.AddField(
            model_name='commande',
            name='refuse_le',
            field=models.DateTimeField(blank=True, null=True, verbose_name='refusé le'),
        ),
    ]
