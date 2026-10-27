"""Réécrit les liens `/participations/<n>` en `/mes-achats/<n>` (F-008).

Donnée seulement, aucun changement de schéma. Rejouable : une ligne déjà
corrigée ne correspond plus au motif. La migration est autonome (elle
n'importe aucun code applicatif) pour que l'historique ne dérive pas si
l'application change.
"""

import re

from django.db import migrations

# Motif exact et ancré : un lien qui ressemble seulement (`/participations/7/x`,
# `/api/participations/7`) ne doit surtout pas être touché.
ANCIEN_LIEN = re.compile(r"^/participations/(\d+)$")


def corriger(apps, schema_editor):
    """`/participations/<n>` (404 dans la boutique) devient `/mes-achats/<n>`."""
    Notification = apps.get_model("echanges", "Notification")
    candidats = Notification.objects.filter(lien__startswith="/participations/")
    for notification in candidats.only("id", "lien"):
        trouve = ANCIEN_LIEN.match(notification.lien)
        if trouve:
            Notification.objects.filter(pk=notification.pk).update(
                lien=f"/mes-achats/{trouve.group(1)}"
            )


class Migration(migrations.Migration):

    dependencies = [
        ("echanges", "0003_alter_notification_genre"),
    ]

    operations = [
        # Retour neutre : remettre des liens qui menaient à une 404 n'aurait
        # aucune valeur, et l'inverse écraserait les liens corrects que le
        # nouveau code écrit en `/mes-achats/<n>` après la migration.
        migrations.RunPython(corriger, migrations.RunPython.noop),
    ]
