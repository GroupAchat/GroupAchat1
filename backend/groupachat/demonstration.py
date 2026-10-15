# -*- coding: utf-8 -*-
"""Donner un passé au groupeur qui vient de s'inscrire.

## Le problème que ce module résout

En mode démonstration, l'inscription crée un groupeur **neuf**. Son tableau de
bord affiche alors « 0 campagne, 0 commande, 0 F », ses statistiques sont
vides, son portefeuille aussi, et il n'a reçu aucune question. Tout est exact,
et **on ne voit rien du produit** — c'est-à-dire exactement le contraire de ce
qu'on voulait en ouvrant l'application devant quelqu'un.

Ce module lui fabrique un passé : six groupages **dans six états différents**,
leurs commandes étalées sur deux semaines, les questions de ses acheteurs, et
l'argent qui va avec.

## Pourquoi six groupages et pas trois

Chaque état alimente un écran différent, et il n'y a pas de recouvrement :

| État | L'écran qu'il remplit |
|---|---|
| **Ouverte**, loin de la clôture | Tableau de bord — une barre de progression qui avance |
| **Ouverte**, clôture dans quelques heures | « À faire aujourd'hui » — l'urgence |
| **À décider** | Écran 16 — la décision de clôture, celle qui engage |
| **Commande en cours** | Écran 17 — le devis à déposer, et le virement qui attend |
| **Livrée** | Écran 18 — un retrait **effectué**, le seul argent réellement reçu |
| **Annulée** | Écran 21 — le taux d'aboutissement, qui ne vaut rien s'il fait 100 % |

⚠️ **L'annulée est la plus importante des six.** Un jeu de démonstration où
tout réussit donne une image fausse du métier et rend le taux d'aboutissement
du §10.4 illisible — à 100 %, il ne décide plus d'aucun plafond.

## Ce que ce module ne fait pas

Il **ne touche à rien d'existant** : ni aux groupeurs du jeu de démonstration,
ni à leurs campagnes, ni aux chiffres du fil rouge (§3) qu'un jury vérifie. Il
n'ajoute que des lignes rattachées au groupeur qu'on lui passe.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .catalogue.models import Campagne
from .commandes.models import (
    Commande,
    Justificatif,
    Retrait,
    annuler_campagne,
    cloturer_campagne,
    enregistrer_paiement,
    demander_le_retrait,
    executer_le_retrait,
)
from .comptes.models import Acheteur, Groupeur
from .echanges.models import Question

#: Les six quartiers du jeu de démonstration (§3), dans l'ordre de la spec.
QUARTIERS = ("Agoe", "Be", "Tokoin", "Adidogome", "Nyekonakpoe", "Hedzranawoe")

#: Une photo par groupage, **reprise du catalogue de démonstration**.
#:
#: ⚠️ **On ne choisit pas une photo sans l'avoir regardée.** La première
#: version de ce fichier piochait des identifiants Pexels au jugé : sur six
#: photos, cinq montraient autre chose que le produit annoncé — une chambre à
#: coucher pour des marmites, un plumeau pour des seaux, et une vue de ville
#: filigranée pour un ventilateur. Le texte alternatif, lui, décrivait un
#: produit que l'image ne montrait pas : un lecteur d'écran aurait énoncé une
#: description fausse.
#:
#: Les identifiants ci-dessous viennent donc de `donnees_demo/catalogue.json`,
#: où chaque photo a été choisie avec son produit, et où le texte alternatif
#: dit ce que l'image montre vraiment.
def _photo(identifiant: int) -> str:
    return (
        f"https://images.pexels.com/photos/{identifiant}/"
        f"pexels-photo-{identifiant}.jpeg?auto=compress&cs=tinysrgb&w=800"
    )


#: Les six groupages, et l'état que chacun doit atteindre.
#:
#: `heures` est le temps restant avant clôture : **négatif** pour une campagne
#: dont la date est passée, ce qui est exactement ce qui la fait apparaître
#: dans « à décider ».
GROUPAGES = (
    {
        "etat": "ouverte",
        "titre": "Riz parfumé 25 kg, sac entier",
        "autres_photos": (
            (38781904, "Sac de riz ouvert vu de dessus, grains beiges et pelle en métal"),
        ),
        "description": (
            "Sac de riz parfumé de 25 kg, importé, grain long. Acheté chez un "
            "grossiste du port de Lomé et réparti en parts de 5 kg. Le sac "
            "est ouvert devant vous au point de remise."
        ),
        "contenu_part": "5 kg de riz, en sachet refermable",
        "categorie": "alimentaire",
        "prix": 4500,
        "heures": 61,
        "commandes": 23,
        "objectif": 30,
        # C6 du catalogue — un sac de riz ouvert, vérifié.
        "photo": 5472000,
        "alt": "Sac de riz ouvert",
        "quartier": "Agoe",
        "remise": "Station Total, Agoè Assiyéyé",
    },
    {
        "etat": "ouverte",
        "titre": "Bidon d'huile végétale 5 L",
        "description": (
            "Huile végétale raffinée en bidon de 5 litres, scellé d'origine. "
            "Commande groupée chez un importateur d'Akodessewa : le prix à "
            "l'unité tombe nettement à partir de vingt bidons."
        ),
        "contenu_part": "1 bidon de 5 litres, scellé",
        "categorie": "alimentaire",
        "prix": 6200,
        # Moins de six heures : c'est ce qui remplit « À faire aujourd'hui »
        # et fait passer le compte à rebours en orange (§2.4).
        "heures": 5,
        "commandes": 17,
        "objectif": 20,
        # La même photo que « Huile de palme 20 L » du catalogue : vérifiée,
        # et elle montre bien de l'huile de cuisine.
        "photo": 6823599,
        "alt": "Huile de cuisine versée",
        "quartier": "Be",
        "remise": "Marché de Bè, entrée nord",
    },
    {
        "etat": "a-decider",
        "titre": "Eau de javel 5 L, carton de 4 bidons",
        "description": (
            "Eau de javel en bidons de 5 litres, carton de quatre. Le carton "
            "se répartit par bidon. Produit courant, qualité constante — "
            "c'est le groupage qui revient le plus souvent."
        ),
        "contenu_part": "1 bidon de 5 litres",
        "categorie": "hygiene",
        "prix": 2800,
        "heures": -3,
        "commandes": 14,
        "objectif": 20,
        # C8 du catalogue — des bidons de produits ménagers, vérifié.
        "photo": 5218019,
        "alt": "Bidons de produits ménagers",
        "quartier": "Tokoin",
        "remise": "Pharmacie du rond-point, Tokoin",
    },
    {
        "etat": "en-cours",
        "titre": "Peinture murale blanc mat, 20 L",
        "autres_photos": (
            (9222200, "Pot de peinture ouvert avec son rouleau et son bac bleus, posés au sol"),
        ),
        "description": (
            "Peinture acrylique blanc mat, seau de 20 litres, pour murs "
            "intérieurs. Commandée par palette chez un grossiste "
            "d'Adidogomé : le prix au seau tombe nettement à partir de dix."
        ),
        "contenu_part": "1 seau de 20 litres",
        "categorie": "maison",
        "prix": 7500,
        "heures": -48,
        "commandes": 19,
        "objectif": 20,
        # C11 du catalogue — un seau de peinture et des rouleaux, vérifié.
        "photo": 2293819,
        "alt": "Seau de peinture et rouleaux",
        "quartier": "Adidogome",
        "remise": "Carrefour Adidogomé, devant la quincaillerie",
        "fournisseur": "Quincaillerie Adidogomé",
        "devis": 118000,
    },
    {
        "etat": "livree",
        "titre": "Serviettes de bain éponge, lot de 6",
        "autres_photos": (
            (4210372, "Pile de serviettes éponge beiges pliées sur un tabouret blanc"),
            (30982437, "Haute pile de serviettes rayées à franges, sur fond beige"),
        ),
        "description": (
            "Serviettes de bain en coton éponge, lot de six, coloris assortis. "
            "Achetées en gros chez un importateur. Groupage déjà livré : la "
            "tournée s'est faite en une matinée."
        ),
        "contenu_part": "2 serviettes de bain",
        "categorie": "maison",
        "prix": 3200,
        "heures": -192,
        "commandes": 26,
        "objectif": 25,
        # C15 du catalogue — du textile plié tenu à la main, vérifié.
        "photo": 8346226,
        "alt": "Textile plié tenu à la main",
        "quartier": "Nyekonakpoe",
        "remise": "Boutique du coin, Nyékonakpoè",
        "fournisseur": "Textile Lomé",
        "devis": 54000,
    },
    {
        "etat": "annulee",
        "titre": "Ventilateur sur pied, 3 vitesses",
        "autres_photos": (
            (1374448, "Gros plan sur la grille d'un ventilateur aux pales dorées, sur fond noir"),
        ),
        "description": (
            "Ventilateur sur pied, 16 pouces, trois vitesses. Le fournisseur "
            "a augmenté son prix entre l'ouverture du groupage et la "
            "clôture : le groupage a été annulé et tout le monde remboursé."
        ),
        "contenu_part": "1 ventilateur sur pied",
        "categorie": "electronique",
        "prix": 12500,
        "heures": -120,
        "commandes": 8,
        "objectif": 30,
        # C9 du catalogue — un ventilateur électrique blanc, vérifié.
        "photo": 3675622,
        "alt": "Ventilateur électrique blanc",
        "quartier": "Hedzranawoe",
        "remise": "Face au marché d'Hédzranawoé",
    },
)

#: Les questions que ses acheteurs lui ont posées.
#:
#: ⚠️ **Deux sans réponse, et c'est délibéré.** L'écran 20 n'a d'intérêt que
#: s'il reste quelque chose à faire : une file vide ne montre ni le tri par
#: ancienneté, ni le bouton « Répondre ».
QUESTIONS = (
    (0, "Le sac est ouvert devant nous au point de remise ?", "Oui, systématiquement. Vous pesez votre part si vous voulez."),
    (0, "On peut prendre deux parts ?", ""),
    (1, "C'est bien de l'huile raffinée, pas de l'huile de palme ?", "Oui, huile végétale raffinée, bidon scellé d'origine."),
    (1, "Vous livrez à Agoè aussi ?", ""),
    (2, "Les barres font quel poids ?", "Environ 400 g la barre, c'est le format standard."),
    (3, "La marmite a un couvercle ?", "Oui, le couvercle est compris dans le prix."),
)


def _acheteur(groupeur: Groupeur, rang: int) -> Acheteur:
    """Un acheteur de démonstration, **propre à ce groupeur**.

    Le numéro est dérivé de son identifiant : deux démonstrations successives
    ne se partagent donc pas les mêmes comptes, et les commandes de l'une
    n'apparaissent pas dans les chiffres de l'autre.
    """
    acheteur, _ = Acheteur.objects.get_or_create(
        telephone=f"+22870{groupeur.pk % 1000:03d}{rang:03d}",
        defaults={"nom": f"Acheteur {rang + 1}"},
    )
    return acheteur


def _etaler(campagne: Campagne, decalage: int) -> None:
    """Répartit les commandes sur les quatorze derniers jours.

    ⚠️ **Sans ça, les courbes ne montrent rien.** ``passee_le`` est en
    ``auto_now_add`` : toutes les commandes porteraient l'instant du
    chargement, et la courbe resterait plate puis monterait à la verticale.

    La répartition **accélère vers la fin**, comme un vrai groupage : c'est
    tout l'effet du compte à rebours du §2.4. L'exposant est inférieur à 1, et
    le sens compte — au-dessus, la courbe descendrait.
    """
    commandes = list(campagne.commandes.order_by("id"))
    if not commandes:
        return

    maintenant = timezone.now()
    total = len(commandes)

    for rang, commande in enumerate(commandes):
        avancement = (rang / max(1, total - 1)) ** 0.55
        jours = 13 - avancement * 13
        Commande.objects.filter(pk=commande.pk).update(
            passee_le=maintenant
            - timedelta(days=jours, hours=(decalage * 3 + rang) % 24)
        )


#: Ce qui identifie un groupeur ne de la demonstration, et lui seul.
#:
#: La decision de validation porte son auteur en clair — c'est deja ce qui la
#: distingue d'un vrai examen dans la base. On s'en sert ici pour savoir quoi
#: effacer : pas le pseudonyme, qu'un vrai groupeur pourrait choisir.
AUTEUR_DEMONSTRATION = "Mode démonstration"


@transaction.atomic
def oublier_les_precedentes(sauf: Groupeur | None = None) -> int:
    """Efface les groupeurs nes d'une demonstration passee, et tout leur monde.

    ⚠️ **Sans ca, la boutique se remplit de doublons.** Chaque passage dans
    l'inscription cree six groupages, et ils sont **publics** : apres cinq
    demonstrations, un acheteur voit trente fois le meme savon de menage, et
    le catalogue ne ressemble plus a rien — c'est-a-dire exactement l'inverse
    de ce qu'on voulait montrer.

    On garde donc **une demonstration a la fois**. Les groupeurs du jeu de
    donnees (`charger_demo`) ne sont pas concernes : ils n'ont pas de decision
    signee « Mode démonstration », et leurs chiffres sont ceux que le fil
    rouge (§3) promet.

    Renvoie le nombre de groupeurs oublies.
    """
    anciens = Groupeur.objects.filter(
        decisions_kyc__decide_par=AUTEUR_DEMONSTRATION
    ).distinct()
    if sauf is not None:
        anciens = anciens.exclude(pk=sauf.pk)

    anciens = list(anciens)
    if not anciens:
        return 0

    campagnes = Campagne.objects.filter(groupeur__in=anciens)
    # L'ordre compte : les cles etrangeres sont en `PROTECT` sur la campagne et
    # sur le groupeur, donc on part des feuilles.
    Question.objects.filter(campagne__in=campagnes).delete()
    Justificatif.objects.filter(campagne__in=campagnes).delete()
    Retrait.objects.filter(campagne__in=campagnes).delete()
    Commande.objects.filter(campagne__in=campagnes).delete()
    campagnes.delete()

    for groupeur in anciens:
        groupeur.decisions_kyc.all().delete()
        groupeur.pieces.all().delete()
        groupeur.delete()

    return len(anciens)


@transaction.atomic
def peupler(groupeur: Groupeur) -> int:
    """Donne six groupages et leur histoire au groupeur passé en argument.

    Renvoie le nombre de groupages créés. **Sans effet s'il en a déjà** : on
    peut donc l'appeler deux fois sans doubler son tableau de bord.
    """
    if groupeur.campagnes.exists():
        return 0

    # ⚠️ **Un dossier non validé ne reçoit rien, et ce n'est pas un oubli.**
    #
    # `Campagne.clean` refuse une campagne dont le groupeur n'a pas passé le
    # KYC (§10.5) — c'est le verrou central du modèle, et il a raison de
    # refuser. Peupler par-dessus levait une erreur 500 à l'ouverture du
    # tableau de bord des quatre dossiers en attente du jeu de données.
    #
    # Et surtout : ces quatre-là **doivent** rester vides. Leur écran montre
    # le tableau de bord d'attente, création de groupage fermée, qui est
    # exactement ce qu'ils servent à démontrer.
    if not groupeur.peut_lancer_une_campagne:
        return 0

    maintenant = timezone.now()
    creees: list[Campagne] = []

    for rang, modele in enumerate(GROUPAGES):
        campagne = Campagne.objects.create(
            groupeur=groupeur,
            titre=modele["titre"],
            description=modele["description"],
            contenu_part=modele["contenu_part"],
            categorie=modele["categorie"],
            prix_part=Decimal(str(modele["prix"])),
            objectif_participants=modele["objectif"],
            medias=[
                {
                    "type": "image",
                    "url": _photo(modele["photo"]),
                    "alt": modele["alt"],
                },
                # ⚠️ **Les supplementaires ont ete regardees avant d'etre
                # decrites.** Elles ne sont posees que sur les groupages dont
                # le produit est litteralement le meme que celui du catalogue :
                # l'huile et l'eau de javel n'ont pas d'equivalent verifie,
                # donc elles gardent une seule photo. Une fiche a une image
                # vaut mieux qu'une fiche a deux dont la seconde montre autre
                # chose.
                *(
                    {"type": "image", "url": _photo(identifiant), "alt": alt}
                    for identifiant, alt in modele.get("autres_photos", ())
                ),
            ],
            quartier_remise=modele["quartier"],
            point_remise=modele["remise"],
            remise_le=(maintenant + timedelta(days=3)).date(),
            # ⚠️ **Toujours ouverte à la création, même pour les groupages qui
            # doivent finir dans le passé.** `enregistrer_paiement` refuse un
            # groupage dont la date est passée — et il a raison : c'est la
            # règle qui empêche de payer après la clôture. On recule donc la
            # date **après** avoir enregistré les commandes, quelques lignes
            # plus bas, plutôt que de contourner le contrôle.
            # ⚠️ **Le repli à 48 h ne vaut que pour les groupages qui
            # doivent finir dans le passé.** L'appliquer à tous écraserait le
            # groupage « clôture dans 5 heures », qui est précisément celui
            # qui remplit « À faire aujourd'hui » et fait passer le compte à
            # rebours en orange (§2.4).
            #
            # 48 h et non 1 h, parce que `heures_restantes` est un entier de
            # division : à une heure pile, les secondes passées à enregistrer
            # les commandes le font tomber à zéro, et le groupage se referme
            # au milieu de son propre peuplement.
            date_fin=maintenant
            + timedelta(
                hours=modele["heures"] if modele["heures"] > 0 else 48
            ),
        )

        for numero in range(modele["commandes"]):
            enregistrer_paiement(
                campagne=campagne,
                acheteur=_acheteur(groupeur, rang * 50 + numero),
                quantite=1,
                quartier=QUARTIERS[numero % len(QUARTIERS)],
                repere="repère de démonstration",
                telephone=_acheteur(groupeur, rang * 50 + numero).telephone,
                cle_idempotence=f"demo-{groupeur.pk}-{rang}-{numero}",
            )

        _etaler(campagne, rang)

        if modele["heures"] <= 0:
            # `update` et non `save` : la date est maintenant dans le passé, ce
            # qu'aucune saisie ne produirait, et `full_clean` n'a rien à y
            # dire. C'est ce qui fait entrer le groupage dans « à décider ».
            Campagne.objects.filter(pk=campagne.pk).update(
                date_fin=maintenant + timedelta(hours=modele["heures"])
            )
            campagne.refresh_from_db()

        creees.append(campagne)

    _poser_les_etats_de_fin(creees)
    _poser_les_questions(creees)

    return len(creees)


def _poser_les_etats_de_fin(creees: list[Campagne]) -> None:
    """Amène chaque groupage à l'état que son écran attend.

    ⚠️ **On passe par les mêmes fonctions que la vraie application** —
    ``cloturer_campagne``, ``annuler_campagne``, ``executer_le_retrait`` — et
    non par des écritures directes. Un jeu de démonstration fabriqué à la main
    finit par représenter un état que le code ne sait pas produire, et c'est
    alors la démonstration qui ment plutôt que l'application qui est en panne.
    """
    for campagne, modele in zip(creees, GROUPAGES):
        etat = modele["etat"]

        if etat == "annulee":
            annuler_campagne(campagne)
            continue

        if etat not in ("en-cours", "livree"):
            continue

        retrait = cloturer_campagne(campagne)
        Justificatif.objects.create(
            campagne=campagne,
            nature=Justificatif.Nature.DEVIS,
            fournisseur=modele["fournisseur"],
            montant=Decimal(str(modele["devis"])),
            reference=f"coffre/devis/{campagne.pk}",
        )

        if etat == "livree":
            # Le parcours entier : il demande, nous exécutons. Passer
            # directement à `effectue` produirait un retrait que personne n'a
            # demandé — un état que la vraie application ne sait pas atteindre.
            demander_le_retrait(retrait)
            executer_le_retrait(retrait, par="Administration")
            campagne.statut = Campagne.Statut.LIVREE
            campagne.save(update_fields=["statut"])
            campagne.commandes.update(statut="livree")
        else:
            # Reculé de trois jours : sinon « attend depuis 0 jour », et la
            # colonne d'ancienneté du portefeuille ne démontre rien.
            Retrait.objects.filter(pk=retrait.pk).update(
                effectue_le=timezone.now() - timedelta(days=3)
            )


def _poser_les_questions(creees: list[Campagne]) -> None:
    """Les questions publiques de ses acheteurs — écrans 10 et 20."""
    maintenant = timezone.now()

    for rang, (indice, texte, reponse) in enumerate(QUESTIONS):
        if indice >= len(creees):
            continue
        campagne = creees[indice]
        # ⚠️ **L'auteur est un acheteur de ce groupage**, et pas n'importe
        # qui : c'est la règle de l'écran 10 — on ne pose une question que sur
        # un groupage auquel on participe. Son nom ne sort jamais côté
        # groupeur, qui ne voit que « Acheteur vérifié » (§1.7).
        premiere = campagne.commandes.order_by("id").first()
        if premiere is None:
            continue

        question = Question.objects.create(
            campagne=campagne,
            auteur=premiere.acheteur,
            texte=texte,
            reponse=reponse,
            etat=Question.Etat.PUBLIEE,
            repondue_le=maintenant if reponse else None,
        )
        # Étalées elles aussi : une file dont toutes les lignes disent « il y a
        # quelques secondes » ne montre pas le tri par ancienneté, qui est
        # pourtant ce qui fait agir sur l'écran 20.
        Question.objects.filter(pk=question.pk).update(
            posee_le=maintenant - timedelta(days=rang, hours=rang * 2)
        )
