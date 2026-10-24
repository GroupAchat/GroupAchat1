# -*- coding: utf-8 -*-
"""Les photos de produit deviennent des médias : photos **et** vidéos.

Écrite à la main plutôt que détectée. `makemigrations` aurait vu une table
supprimée et une autre créée — et jeté les photos existantes au passage.
Un renommage explicite conserve les lignes.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("catalogue", "0003_etatdemonstration"),
    ]

    operations = [
        migrations.RenameModel(old_name="ImageProduit", new_name="MediaProduit"),
        migrations.RenameField(
            model_name="mediaproduit", old_name="image", new_name="fichier"
        ),
        migrations.AlterField(
            model_name="mediaproduit",
            name="fichier",
            field=models.FileField(upload_to="produits/", verbose_name="fichier"),
        ),
        migrations.AlterField(
            model_name="mediaproduit",
            name="produit",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="medias",
                to="catalogue.produit",
                verbose_name="produit",
            ),
        ),
        migrations.AddField(
            model_name="mediaproduit",
            name="genre",
            field=models.CharField(
                choices=[("image", "Photo"), ("video", "Vidéo")],
                default="image",
                max_length=10,
                verbose_name="type",
            ),
        ),
        migrations.AddField(
            model_name="mediaproduit",
            name="apercu",
            field=models.ImageField(
                blank=True,
                upload_to="produits/apercus/",
                verbose_name="aperçu de la vidéo",
            ),
        ),
        migrations.AlterModelOptions(
            name="mediaproduit",
            options={
                "ordering": ["ordre", "id"],
                "verbose_name": "média de produit",
                "verbose_name_plural": "médias de produit",
            },
        ),
        migrations.AddIndex(
            model_name="mediaproduit",
            index=models.Index(
                fields=["produit", "genre", "ordre"],
                name="catalogue_m_produit_4797d7_idx",
            ),
        ),
    ]
