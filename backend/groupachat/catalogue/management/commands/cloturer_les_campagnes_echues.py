# -*- coding: utf-8 -*-
"""Ferme les collectes arrivées à échéance, et rend l'argent resté sans décision.

**À faire tourner toutes les heures.** C'est la seule chose qui fait
avancer une campagne sans qu'un humain clique, et tout le produit en
dépend :

- sans elle, une campagne dépassée reste affichée au catalogue et accepte
  encore des participations ;
- sans elle, les acheteurs d'un groupage manqué ne sont jamais prévenus ;
- sans elle, un groupeur qui disparaît laisse l'argent consigné pour
  toujours ;
- sans elle, un colis non retiré bloque la campagne en distribution pour
  toujours : elle relance les acheteurs à J+3 et J+7, puis réputé livrée la
  part non retirée à J+14 et termine la campagne (F-031).

    python manage.py cloturer_les_campagnes_echues

En production, Coolify ou cron l'appelle ; en développement, on la lance à
la main pour voir le cycle se dérouler.
"""

from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand

from groupachat.paiements.retraits import (
    CLOTURE_BLOQUEE,
    CLOTURE_DUE,
    CLOTURE_PREAVIS,
    CLOTURE_RATTRAPAGE,
    etape_de_relance,
    relancer_les_retraits,
    reputer_livrees_les_echues,
    situation_a_j_plus_14,
)
from groupachat.paiements.services import cloturer_les_echus, rembourser_les_indecis


class Command(BaseCommand):
    help = (
        "Clôture les campagnes échues, rembourse celles laissées sans décision, "
        "relance les retraits et clôt à J+14."
    )

    def add_arguments(self, analyseur):
        analyseur.add_argument(
            "--a-blanc",
            action="store_true",
            help="Montre ce qui serait fait, sans rien changer.",
        )

    def handle(self, *args, **options):
        if options["a_blanc"]:
            self._annoncer()
            return

        fermees = cloturer_les_echus()
        for identifiant, statut in fermees:
            self.stdout.write(f"  campagne {identifiant} → {statut}")
        if not fermees:
            self.stdout.write("  aucune collecte arrivée à échéance.")

        rendues = rembourser_les_indecis()
        for identifiant in rendues:
            self.stdout.write(
                f"  campagne {identifiant} → remboursée, "
                f"sans décision depuis {settings.DELAI_DECISION_JOURS} jours"
            )

        relances = relancer_les_retraits()
        for identifiant, etape in relances:
            self.stdout.write(f"  campagne {identifiant} → relance {etape}")

        closes = reputer_livrees_les_echues()
        for identifiant in closes:
            self.stdout.write(
                f"  campagne {identifiant} → terminée, colis non retirés réputés livrés"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n{len(fermees)} clôture(s), {len(rendues)} remboursement(s), "
                f"{len(relances)} relance(s), "
                f"{len(closes)} campagne(s) close(s) à J+14."
            )
        )

    def _annoncer(self) -> None:
        """Ce que ferait la commande, sans le faire.

        Utile avant de la brancher sur une tâche planifiée : on vérifie
        qu'elle ne va pas fermer ce qu'on ne veut pas fermer.
        """
        from datetime import timedelta

        from django.utils import timezone

        from groupachat.catalogue.models import Campagne

        echues = Campagne.objects.filter(
            statut=Campagne.Statut.EN_COURS, date_limite__lte=timezone.now()
        )
        self.stdout.write(f"À clôturer : {echues.count()}")
        for campagne in echues:
            issue = (
                "financée" if campagne.minimum_atteint else "minimum non atteint"
            )
            self.stdout.write(
                f"  {campagne.id} · {campagne.titre[:44]} → {issue} "
                f"({campagne.quantite_reservee}/{campagne.quantite_minimale})"
            )

        if settings.DELAI_DECISION_JOURS <= 0:
            self.stdout.write("Remboursement automatique désactivé.")
            self._annoncer_retraits()
            return

        limite = timezone.now() - timedelta(days=settings.DELAI_DECISION_JOURS)
        oubliees = Campagne.objects.filter(
            statut=Campagne.Statut.MINIMUM_NON_ATTEINT, cloturee_le__lte=limite
        )
        self.stdout.write(f"À rembourser faute de décision : {oubliees.count()}")
        for campagne in oubliees:
            self.stdout.write(f"  {campagne.id} · {campagne.titre[:44]}")
        self._annoncer_retraits()

    def _annoncer_retraits(self) -> None:
        """Les relances et clôtures à J+14 que la tâche ferait, sans les faire."""
        from django.utils import timezone

        from groupachat.catalogue.models import Campagne
        from groupachat.commandes.models import Participation

        maintenant = timezone.now()
        en_distribution = Campagne.objects.filter(
            statut=Campagne.Statut.DISTRIBUTION
        ).order_by("id")
        lignes = []
        for campagne in en_distribution:
            etape = etape_de_relance(campagne, maintenant)
            if etape:
                lignes.append(f"  {campagne.id} · {campagne.titre[:44]} → relance {etape}")
            situation = situation_a_j_plus_14(campagne, maintenant)
            non_retires = campagne.participations.filter(
                statut=Participation.Statut.PRETE
            ).count()
            texte = {
                CLOTURE_DUE: f"clôture à J+14 ({non_retires} colis non retirés)",
                CLOTURE_RATTRAPAGE: "relance de rattrapage avant la clôture à J+14",
                CLOTURE_PREAVIS: "clôture à J+14 après le préavis de 72 h",
                CLOTURE_BLOQUEE: "bloquée : fonds consignés",
            }.get(situation)
            if texte:
                lignes.append(f"  {campagne.id} · {campagne.titre[:44]} → {texte}")
        self.stdout.write(f"Retraits à relancer ou à clore : {len(lignes)}")
        for ligne in lignes:
            self.stdout.write(ligne)
