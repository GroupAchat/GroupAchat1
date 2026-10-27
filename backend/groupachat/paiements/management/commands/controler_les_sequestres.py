# -*- coding: utf-8 -*-
"""Liste, sans rien corriger, les anomalies d'argent du séquestre.

    python manage.py controler_les_sequestres

Lecture seule : de l'argent déjà sorti ne se corrige pas automatiquement,
c'est à l'administrateur de trancher. À lancer à la main, notamment sur la
production avant un déploiement qui ajoute une contrainte sur l'argent
(voir COOLIFY.md) : sans cela, une migration qui échoue empêche le conteneur
de démarrer.

Quatre rubriques, toujours affichées. Code de sortie 0 sans anomalie, 1 sinon.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db.models import F

from groupachat.catalogue.models import Campagne
from groupachat.paiements.models import Decaissement, Sequestre


class Command(BaseCommand):
    help = "Liste les séquestres et décaissements incohérents, sans rien modifier."

    def handle(self, *args, **options):
        total = 0

        # Une fois la contrainte en base, cette rubrique ne peut plus rien
        # trouver ; on la garde pour une sauvegarde restaurée sans migration.
        depassements = list(
            Sequestre.objects.filter(
                montant_consigne__lt=F("montant_libere") + F("montant_rembourse")
            ).select_related("campagne")
        )
        total += self._rubrique(
            "Séquestres qui rendent plus que le consigné",
            [
                f"campagne {s.campagne_id} · {s.campagne.titre[:40]} — "
                f"consigné {s.montant_consigne}, libéré {s.montant_libere}, "
                f"remboursé {s.montant_rembourse}"
                for s in depassements
            ],
        )

        orphelins = Decaissement.objects.filter(
            statut=Decaissement.Statut.DEMANDE
        ).exclude(campagne__statut=Campagne.Statut.FINANCEE).select_related("campagne")
        total += self._rubrique(
            "Décaissements en attente sur une campagne non financée",
            [
                f"décaissement {d.pk} · campagne {d.campagne_id} "
                f"({d.campagne.statut}) — brut {d.montant_brut}, net {d.montant_net}"
                for d in orphelins
            ],
        )

        total += self._rubrique(
            "Campagnes au statut « decaissee »",
            [
                f"campagne {c.pk} · {c.titre[:40]}"
                for c in Campagne.objects.filter(statut=Campagne.Statut.DECAISSEE)
            ],
        )

        # Trace de l'ancien chemin financee -> distribution, qui sautait le
        # décaissement : la marchandise est distribuée, l'argent dort encore.
        non_soldes = [
            s
            for s in Sequestre.objects.filter(
                campagne__statut__in=[
                    Campagne.Statut.DISTRIBUTION,
                    Campagne.Statut.TERMINEE,
                ]
            ).select_related("campagne")
            if s.solde > 0
        ]
        total += self._rubrique(
            "Campagnes en distribution ou terminées dont le séquestre n'est pas soldé",
            [
                f"campagne {s.campagne_id} ({s.campagne.statut}) — "
                f"solde {s.solde}"
                for s in non_soldes
            ],
        )

        if total:
            raise CommandError(
                f"{total} anomalie(s) : à trancher par l'administrateur, "
                "rien n'a été corrigé."
            )
        self.stdout.write(self.style.SUCCESS("Aucune anomalie."))

    def _rubrique(self, titre: str, lignes: list[str]) -> int:
        self.stdout.write(f"{titre} : {len(lignes)}")
        for ligne in lignes:
            self.stdout.write(f"  {ligne}")
        return len(lignes)
