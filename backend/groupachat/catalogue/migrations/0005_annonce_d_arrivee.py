# -*- coding: utf-8 -*-
# Genere par Django 5.2.18 on 2026-10-13 14:39

"""Quand le groupeur a annonce que le produit etait arrive.

Garde-fou contre le double envoi : l'arrivee est un fait unique, et une cloche
qui repete le meme message perd le droit d'etre regardee.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0004_campagne_objectif_participants'),
    ]

    operations = [
        migrations.AddField(
            model_name='campagne',
            name='arrivee_annoncee_le',
            field=models.DateTimeField(blank=True, null=True, verbose_name='arrivée annoncée le'),
        ),
    ]
