# -*- coding: utf-8 -*-
"""Créer ou mettre à jour un compte d'administration, sans poser de question.

## ⚠️ Pourquoi cette commande existe alors que `createsuperuser` existe

**`createsuperuser` est interactif.** Il demande l'identifiant, le mot de
passe, puis sa confirmation, sur un terminal. Au déploiement il n'y a pas de
terminal : la commande attendrait une saisie qui ne viendrait jamais, et le
conteneur se figerait sans rien dire — exactement le genre de panne silencieuse
que ce dépôt documente par ailleurs pour `runserver` quand la base est
injoignable.

Django fournit bien `--noinput`, mais il refuse alors de poser un mot de passe
et crée un compte **sans mot de passe utilisable**. Pour nous, cela voudrait
dire une administration déployée dans laquelle personne ne peut entrer.

D'où cette commande : elle lit les deux valeurs dans **l'environnement**, elle
ne demande rien, et elle est **idempotente** — on peut la relancer à chaque
démarrage sans créer de doublon ni écraser un mot de passe par accident.

## Ce qu'elle lit

| Variable | Rôle |
|---|---|
| `ADMIN_IDENTIFIANT` | l'identifiant de connexion |
| `ADMIN_MOT_DE_PASSE` | le mot de passe, posé **seulement à la création** |
| `ADMIN_NOM` | facultatif — le nom qui signera les décisions KYC |

⚠️ **Le mot de passe n'est pas reposé sur un compte existant**, sauf avec
`--remplacer-le-mot-de-passe`. Sans cette règle, un `.env` oublié sur le
serveur réécrirait le mot de passe à chaque redémarrage, annulant en silence
tout changement fait depuis l'interface — et ferait du contenu de ce fichier la
clé permanente de l'administration.

## ⚠️ Et ce qu'il faut faire après

Un mot de passe passé par variable d'environnement **est lisible** : il traîne
dans le fichier de configuration de la plateforme, dans l'historique du shell,
parfois dans les journaux de démarrage. Il sert à **entrer la première fois**.
Le changer ensuite depuis l'admin Django est le geste qui le sort de là.
"""

from __future__ import annotations

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Crée ou met à jour un compte d'administration depuis "
        "ADMIN_IDENTIFIANT et ADMIN_MOT_DE_PASSE."
    )

    def add_arguments(self, parseur) -> None:
        parseur.add_argument(
            "--remplacer-le-mot-de-passe",
            action="store_true",
            help=(
                "Repose le mot de passe sur un compte qui existe déjà. "
                "Sans cette option, un compte existant n'est pas touché."
            ),
        )

    def handle(self, *args, **options) -> None:
        identifiant = (os.environ.get("ADMIN_IDENTIFIANT") or "").strip()
        mot_de_passe = os.environ.get("ADMIN_MOT_DE_PASSE") or ""
        nom = (os.environ.get("ADMIN_NOM") or "").strip()

        if not identifiant or not mot_de_passe:
            # ⚠️ **Une erreur, et non un abandon silencieux.** Appelée au
            # démarrage d'un conteneur, cette commande doit faire du bruit :
            # un démarrage qui « réussit » sans créer de compte laisserait une
            # administration dans laquelle personne ne peut entrer, et on le
            # découvrirait en essayant de se connecter.
            # ⚠️ **Les messages imprimés sont en ASCII pur**, et ce n'est pas
            # une négligence de rédaction dans un dépôt qui écrit tout en
            # français. La console Windows est en cp1252, et un conteneur peut
            # l'être selon sa locale : le « ⚠ » du message de succès a fait
            # tomber cette commande sur un `UnicodeEncodeError` **après avoir
            # créé le compte**. Le pire des deux mondes : la plateforme conclut
            # à un échec de démarrage, et le compte existe pourtant.
            raise CommandError(
                "ADMIN_IDENTIFIANT et ADMIN_MOT_DE_PASSE sont requis. "
                "Renseignez-les dans l'environnement : voir .env.exemple."
            )

        Utilisateur = get_user_model()
        compte, cree = Utilisateur.objects.get_or_create(
            **{Utilisateur.USERNAME_FIELD: identifiant}
        )

        a_poser = []

        # `is_staff` est reposé même sur un compte existant, et c'est voulu :
        # c'est lui qui ouvre l'administration, et le but de la commande est
        # précisément de garantir qu'un accès existe.
        if not compte.is_staff:
            compte.is_staff = True
            a_poser.append("is_staff")
        if not compte.is_active:
            compte.is_active = True
            a_poser.append("is_active")

        if nom and not (compte.first_name or compte.last_name):
            prenom, _, famille = nom.partition(" ")
            compte.first_name = prenom
            compte.last_name = famille
            a_poser += ["first_name", "last_name"]

        if cree or options["remplacer_le_mot_de_passe"]:
            compte.set_password(mot_de_passe)
            a_poser.append("password")

        compte.save(update_fields=a_poser or None)

        if cree:
            self.stdout.write(
                self.style.SUCCESS(
                    "Compte d'administration cree : %s" % identifiant
                )
            )
            self.stdout.write(
                "Changez ce mot de passe depuis l'admin Django : celui-ci "
                "est lisible dans la configuration du serveur."
            )
        elif options["remplacer_le_mot_de_passe"]:
            self.stdout.write(
                self.style.WARNING(
                    "Mot de passe remplace pour %s." % identifiant
                )
            )
        else:
            self.stdout.write(
                "%s existe deja : mot de passe inchange. Utilisez "
                "--remplacer-le-mot-de-passe pour le reposer." % identifiant
            )
