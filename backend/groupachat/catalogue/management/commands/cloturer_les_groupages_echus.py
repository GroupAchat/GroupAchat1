# -*- coding: utf-8 -*-
"""Clôture les groupages dont la date est passée.

    python manage.py cloturer_les_groupages_echus

## ⚠️ Le trou que cette commande ferme

**« Seule la date clôture »** est une règle produit non négociable. Elle ne
l'était pas dans le code : ``cloturer_campagne`` n'avait que **deux
appelants**, le bouton « Clôturer maintenant » du groupeur et les chargeurs de
démonstration. Un groupage dont la date tombait restait donc ``ouverte``
indéfiniment, et les conséquences étaient toutes silencieuses :

- il **disparaissait du catalogue** — le filtre de l'écran 2 écarte
  ``date_fin`` passée — donc plus personne ne le voyait, pas même nous ;
- **aucun ``Retrait`` n'était créé**, donc l'argent déjà encaissé auprès des
  acheteurs ne devenait jamais retirable par le groupeur. Son portefeuille
  affichait zéro sur une collecte réelle ;
- les commandes restaient ``payee`` au lieu de passer ``cloturee``, donc
  l'écran 9 de l'acheteur continuait de promettre « détenu jusqu'à la
  clôture » sur un groupage déjà échu ;
- et **la notification de clôture ne partait jamais**, puisque c'est
  ``cloturer_campagne`` qui l'envoie.

Autrement dit : un groupeur qui oubliait d'appuyer sur un bouton bloquait
l'argent de ses acheteurs sans que personne ne soit averti. C'est exactement
le genre de panne qu'on découvre par un appel téléphonique.

## Pourquoi une commande, et pas un déclencheur à l'enregistrement

Rien ne s'exécute quand une date passe : il n'y a aucun événement. Il faut
donc quelque chose qui regarde l'heure — une tâche planifiée. Une commande de
gestion est ce que ce projet sait déjà déployer, et elle est **testable sans
ordonnanceur**, ce qui n'est pas vrai d'une tâche Celery.

⚠️ **Elle doit être branchée sur le cron du VPS au déploiement.** Tant qu'elle
n'y est pas, le trou reste ouvert : écrire la commande ne suffit pas. Un
passage par quart d'heure convient — la clôture n'a pas besoin d'être à la
seconde, et l'écran acheteur n'affiche de toute façon « il reste N heures »
qu'à l'heure près (§2.4).

## Ce qu'elle ne fait pas

Elle **n'annule rien**. Un groupage sous son objectif de participants se
clôture comme les autres : l'objectif n'est ni un plafond, ni un minimum, ni
un déclencheur, et un groupage sous son objectif **peut aboutir** — c'est la
règle produit. L'annulation reste une décision, prise à l'écran 16.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from groupachat.catalogue.models import Campagne
from groupachat.commandes.models import cloturer_campagne


class Command(BaseCommand):
    help = "Clôture les groupages dont la date de fin est passée."

    def add_arguments(self, parser):
        parser.add_argument(
            "--a-blanc",
            action="store_true",
            help="Liste ce qui serait clôturé, sans rien écrire.",
        )

    def handle(self, *args, **options):
        maintenant = timezone.now()
        echus = Campagne.objects.filter(
            statut=Campagne.Statut.OUVERTE, date_fin__lte=maintenant
        ).select_related("groupeur")

        if not echus.exists():
            self.stdout.write("Aucun groupage échu.")
            return

        # argparse transforme « --a-blanc » en clef « a_blanc ».
        a_blanc = options.get("a_blanc", False)

        for campagne in echus:
            if a_blanc:
                self.stdout.write(
                    f"  [à blanc] {campagne.titre} — "
                    f"{campagne.collecte_sur_les_parts} F collectés"
                )
                continue

            # ⚠️ **Une transaction par groupage, et non une pour toutes.**
            # Si la vingtième échoue, les dix-neuf premières doivent rester
            # clôturées : ce sont des opérations indépendantes, et tout
            # annuler ferait recommencer un travail déjà bon. Surtout, une
            # clôture a déjà envoyé ses notifications — les rejouer
            # enverrait deux fois le même message.
            try:
                with transaction.atomic():
                    retrait = cloturer_campagne(campagne)
            except Exception as erreur:  # noqa: BLE001
                # On continue : un groupage en défaut ne doit pas retenir les
                # autres, et le cron n'a personne pour lire une trace perdue.
                self.stderr.write(
                    f"  ÉCHEC {campagne.titre} ({campagne.pk}) : {erreur}"
                )
                continue

            self.stdout.write(
                f"  {campagne.titre} — {retrait.collecte} F collectés, "
                f"{retrait.frais_plateforme} F de frais, "
                f"{retrait.net} F retirables"
            )

        if not a_blanc:
            self.stdout.write(self.style.SUCCESS("Groupages échus clôturés."))
