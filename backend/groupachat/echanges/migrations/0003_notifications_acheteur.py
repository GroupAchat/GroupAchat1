# -*- coding: utf-8 -*-
# Genere par Django 5.2.18 on 2026-10-13 14:39

import django.db.models.deletion
"""La cloche de l'acheteur.

Le texte est **fige a l'envoi** : ``titre`` et ``corps`` sont ecrits une fois,
au moment du fait, et jamais recalcules a l'affichage. Les trois cles
etrangeres sont facultatives et servent a ouvrir le bon ecran au clic.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0005_annonce_d_arrivee'),
        ('commandes', '0004_refus_du_colis'),
        ('comptes', '0003_codeconnexion_acheteur_quartier_acheteur_repere_and_more'),
        ('echanges', '0002_signalement_de_question'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nature', models.CharField(choices=[('produit-arrive', 'Le produit est arrivé'), ('reponse-question', 'Réponse à votre question'), ('groupage-cloture', 'Groupage clôturé'), ('groupage-annule', 'Groupage annulé')], max_length=20, verbose_name='nature')),
                ('titre', models.CharField(max_length=120, verbose_name='titre')),
                ('corps', models.TextField(verbose_name='corps')),
                ('creee_le', models.DateTimeField(auto_now_add=True, verbose_name='créée le')),
                ('lue_le', models.DateTimeField(blank=True, null=True, verbose_name='lue le')),
                ('campagne', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='catalogue.campagne', verbose_name='campagne concernée')),
                ('commande', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='commandes.commande', verbose_name='commande concernée')),
                ('destinataire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='comptes.acheteur', verbose_name='destinataire')),
                ('question', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='echanges.question', verbose_name='question concernée')),
            ],
            options={
                'verbose_name': 'notification',
                'verbose_name_plural': 'notifications',
                'ordering': ('-creee_le',),
                'indexes': [models.Index(fields=['destinataire', 'lue_le'], name='echanges_no_destina_737106_idx')],
            },
        ),
    ]
