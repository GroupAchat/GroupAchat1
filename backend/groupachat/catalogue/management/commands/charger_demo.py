# -*- coding: utf-8 -*-
"""Peuple la base d'un jeu de données prêt à présenter.

La démonstration doit montrer la plateforme **à tous les stades à la fois** :
une campagne qui collecte, une financée en attente de décaissement, une en
distribution avec ses codes, une terminée, une annulée avec ses
remboursements. Sinon il faut attendre devant le public que quelque chose se
passe.

Elle crée aussi **deux groupeurs** : un validé, pour dérouler le parcours, et
un en attente, pour montrer la porte fermée du KYC.

    python manage.py charger_demo
"""

from __future__ import annotations

from datetime import timedelta
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw

from groupachat.catalogue.models import (
    Campagne,
    Categorie,
    EtatDemonstration,
    MediaProduit,
    MediaCampagne,
    PalierPrix,
    Produit,
)
from groupachat.commandes.models import Avis, Participation
from groupachat.comptes.models import (
    CodeVerification,
    DossierKYC,
    Reputation,
    Utilisateur,
)
from groupachat.comptes.pieces_kyc import supprimer_fichiers
from groupachat.echanges.models import (
    Commentaire,
    DemandeProduit,
    InteretDemande,
    JaimeCommentaire,
    Notification,
)
from groupachat.paiements.models import Decaissement, Sequestre, Transaction
from groupachat.paiements.services import (
    cloturer,
    demander_decaissement,
    encaisser,
    executer_decaissement,
    mettre_a_disposition,
    valider_retrait,
)

# ⚠️ **À incrémenter dès qu'on touche au jeu de données.** C'est ce numéro,
# et lui seul, qui décide si un redéploiement remet la démonstration à plat.
# Laissé inchangé, les nouveautés n'apparaîtraient jamais sur un serveur déjà
# démarré une fois.
VERSION_DEMO = "6"

MOT_DE_PASSE = "demo2026Groupe"

RAYONS = [
    ("Alimentation", "panier", []),
    ("Électronique", "puce", ["Téléphonie", "Électroménager"]),
    ("Maison", "maison", []),
    ("Mode", "vetement", []),
]

ACHETEURS = [
    ("91002233", "Ama", "Mensah"),
    ("92003344", "Yao", "Dossou"),
    ("93004455", "Akouvi", "Adjo"),
    ("94005566", "Kodjo", "Agbeko"),
    ("95006677", "Afi", "Lawson"),
]


class Command(BaseCommand):
    help = "Charge un jeu de démonstration couvrant tous les états du parcours."

    def add_arguments(self, analyseur):
        analyseur.add_argument(
            "--effacer",
            action="store_true",
            help="Vide les données existantes avant de recharger.",
        )
        analyseur.add_argument(
            "--synchroniser",
            action="store_true",
            help=(
                "Recharge seulement si la version du jeu a changé. "
                "C'est le mode utilisé au démarrage d'un conteneur."
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        etat = EtatDemonstration.objects.first()

        if options["synchroniser"]:
            if etat is not None and etat.version == VERSION_DEMO:
                self.stdout.write(
                    f"Jeu de démonstration déjà en version {VERSION_DEMO} : "
                    "rien à faire."
                )
                return
            # Version absente ou différente : on repart d'une base propre.
            # Sans cet effacement, le rechargement buterait sur les comptes
            # et les campagnes déjà présents.
            if etat is not None or Campagne.objects.exists():
                self._effacer()
        elif options["effacer"]:
            self._effacer()
        elif Campagne.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    "Des campagnes existent déjà. Relancez avec --effacer pour "
                    "repartir à zéro, ou --synchroniser pour suivre la version."
                )
            )
            return

        rayons = self._rayons()
        admin = self._administrateur()
        valide, en_attente = self._groupeurs()
        concurrent = self._second_groupeur(admin)
        self._dossiers_a_examiner()
        acheteurs = self._acheteurs()

        self._campagne_en_collecte(valide, rayons, acheteurs)
        self._autres_collectes(valide, rayons, acheteurs)
        self._campagne_financee(valide, rayons, acheteurs)
        self._campagne_en_distribution(valide, rayons, acheteurs, admin)
        self._campagne_terminee(valide, rayons, acheteurs, admin)
        self._campagne_annulee(valide, rayons, acheteurs)
        self._brouillon(valide, rayons)
        self._offre_concurrente(concurrent, acheteurs)
        self._demandes(acheteurs, rayons)
        self._discussions(valide, concurrent, acheteurs, admin)
        self._avis(acheteurs)
        self._notifications_lues(acheteurs)

        EtatDemonstration.objects.create(version=VERSION_DEMO)
        self._resumer(valide, en_attente, admin)

    # ── Mise en place ───────────────────────────────────────────────────────

    def _effacer(self):
        """Vide le jeu précédent, des feuilles vers la racine.

        ⚠️ **L'ordre n'est pas décoratif.** `Transaction` protège
        `Participation`, `Decaissement` protège `Campagne`, et `Campagne`
        protège son groupeur : supprimer dans le désordre lève une erreur
        d'intégrité et laisse la base à moitié vidée — exactement le genre
        de panne qui ne se voit qu'au déploiement suivant.
        """
        enchainement = (
            Avis, Transaction, Decaissement, Sequestre,
            Notification, JaimeCommentaire, Commentaire,
            InteretDemande, DemandeProduit,
            Participation, PalierPrix, MediaCampagne, Campagne,
            MediaProduit, Produit,
            DossierKYC, Reputation, CodeVerification,
        )
        # Les pièces vivent sur le disque : supprimer les lignes ne les efface
        # pas, et des pièces d'identité resteraient orphelines, sans dossier
        # pour les référencer. ⚠️ Cette commande vide TOUTE la base : elle ne
        # doit jamais tourner sur des données réelles (CHARGER_DEMO=0 en
        # production).
        for dossier in DossierKYC.objects.all():
            supprimer_fichiers(
                dossier.piece_recto.storage,
                [dossier.piece_recto.name, dossier.piece_verso.name],
            )
        for modele in enchainement:
            modele.objects.all().delete()

        # Les rayons se suppriment en deux temps : `Categorie.parent` est
        # protégé, et un effacement en bloc bute sur les sous-rayons qui
        # retiennent leur parent.
        Categorie.objects.filter(parent__isnull=False).delete()
        Categorie.objects.all().delete()

        # Les comptes de l'équipe survivent : ils ne viennent pas du jeu de
        # démonstration, et les effacer couperait l'accès à la console.
        Utilisateur.objects.filter(is_superuser=False).delete()
        EtatDemonstration.objects.all().delete()
        self.stdout.write("Données précédentes effacées.")

    def _rayons(self) -> dict:
        rayons = {}
        for ordre, (nom, icone, enfants) in enumerate(RAYONS):
            parent = Categorie.objects.create(nom=nom, icone=icone, ordre=ordre)
            rayons[nom] = parent
            for sous_ordre, enfant in enumerate(enfants):
                rayons[enfant] = Categorie.objects.create(
                    nom=enfant, parent=parent, ordre=sous_ordre
                )
        return rayons

    def _administrateur(self) -> Utilisateur:
        admin = Utilisateur.objects.filter(telephone="99000011").first()
        if admin is None:
            admin = Utilisateur.objects.create_superuser(
                "99000011", MOT_DE_PASSE, nom="Équipe", prenom="Group Achat"
            )
        return admin

    def _groupeurs(self) -> tuple[Utilisateur, Utilisateur]:
        valide = Utilisateur.objects.create_user(
            "90001122", MOT_DE_PASSE, nom="Abalo", prenom="Koffi",
            role=Utilisateur.Role.GROUPEUR, telephone_verifie=True,
        )
        DossierKYC.objects.create(
            utilisateur=valide, type_piece=DossierKYC.TypePiece.CNI,
            numero_piece="CNI-TG-884512", numero_mobile_money="90001122",
            nom_commerce="Abalo Import Lomé", statut=DossierKYC.Statut.VALIDE,
            decide_le=timezone.now() - timedelta(days=60),
        )
        Reputation.objects.create(groupeur=valide)

        # Celui-ci sert à montrer l'écran d'attente : sans lui, impossible de
        # présenter ce que voit un groupeur dont le dossier n'est pas tranché.
        en_attente = Utilisateur.objects.create_user(
            "90009988", MOT_DE_PASSE, nom="Doe", prenom="Afi",
            role=Utilisateur.Role.GROUPEUR, telephone_verifie=True,
        )
        dossier = DossierKYC.objects.create(
            utilisateur=en_attente, type_piece=DossierKYC.TypePiece.PASSEPORT,
            numero_piece="TG-P-220199", numero_mobile_money="90009988",
            nom_commerce="Afi Distribution",
        )
        # Sans pièce, la console d'administration n'aurait rien à montrer
        # d'un dossier à examiner.
        self._pieces_fictives(dossier)
        return valide, en_attente

    @staticmethod
    def _pieces_fictives(dossier: DossierKYC) -> None:
        """Deux images factices, passées par le stockage local normal.

        Ni photo ni donnée réelle : un aplat gris portant la mention « PIECE FICTIVE ».
        Elles vont sous `MEDIA_ROOT/kyc/`, jamais chez Cloudinary.
        """
        for champ, mention in (("piece_recto", "RECTO"), ("piece_verso", "VERSO")):
            image = Image.new("RGB", (320, 200), (200, 205, 210))
            ImageDraw.Draw(image).text(
                (20, 90), f"PIECE FICTIVE - {mention}", fill=(60, 60, 60)
            )
            tampon = BytesIO()
            image.save(tampon, format="PNG")
            getattr(dossier, champ).save(
                "piece.png", ContentFile(tampon.getvalue()), save=False
            )
        dossier.save(update_fields=["piece_recto", "piece_verso"])

    def _second_groupeur(self, admin) -> Utilisateur:
        """Un deuxième groupeur validé, avec un passé.

        Sans lui, la place de marché n'en est pas une : impossible de montrer
        deux offres sur le même produit, ni une réputation qui diffère d'un
        vendeur à l'autre.
        """
        groupeur = Utilisateur.objects.create_user(
            "96004477", MOT_DE_PASSE, nom="Amegan", prenom="Essi",
            role=Utilisateur.Role.GROUPEUR, telephone_verifie=True,
        )
        DossierKYC.objects.create(
            utilisateur=groupeur, type_piece=DossierKYC.TypePiece.CNI,
            numero_piece="CNI-TG-114027", numero_mobile_money="96004477",
            nom_commerce="Essi Negoce", statut=DossierKYC.Statut.VALIDE,
            decide_le=timezone.now() - timedelta(days=120), decide_par=admin,
        )
        Reputation.objects.create(
            groupeur=groupeur, campagnes_terminees=7, campagnes_annulees=1,
            avis_recus=0, participants_servis=43, note=0,
        )
        return groupeur

    def _dossiers_a_examiner(self) -> None:
        """De quoi remplir la file d'attente de la console d'administration."""
        candidats = [
            ("97005588", "Komlan", "Sodji", "Sodji Trading",
             DossierKYC.TypePiece.CNI, "CNI-TG-556102"),
            ("98006699", "Nathalie", "Agbo", "NA Cosmetiques",
             DossierKYC.TypePiece.PASSEPORT, "TG-P-884411"),
        ]
        for telephone, prenom, nom, commerce, piece, numero in candidats:
            compte = Utilisateur.objects.create_user(
                telephone, MOT_DE_PASSE, nom=nom, prenom=prenom,
                role=Utilisateur.Role.GROUPEUR, telephone_verifie=True,
            )
            DossierKYC.objects.create(
                utilisateur=compte, type_piece=piece, numero_piece=numero,
                numero_mobile_money=telephone, nom_commerce=commerce,
                depose_le=timezone.now() - timedelta(days=2),
            )
        self.stdout.write("  - 3 dossiers KYC en attente de decision")

    def _offre_concurrente(self, groupeur, acheteurs) -> None:
        """Deux groupeurs sur le même produit : l'acheteur compare.

        C'est le coeur de la place de marché, et ça ne se voit que si deux
        campagnes portent le **même** produit à deux prix différents.
        """
        riz = Produit.objects.filter(nom__icontains="riz").first()
        if riz is None:
            return

        campagne = Campagne.objects.create(
            produit=riz, groupeur=groupeur,
            titre="Riz Delice 25 kg - conteneur d'Essi Negoce",
            description="Meme reference, livraison une semaine plus tot.",
            prix_unitaire=17500, quantite_minimale=30,
            date_limite=timezone.now() + timedelta(days=6),
            point_remise="Depot Essi, Agoe-Nyive",
            statut=Campagne.Statut.EN_COURS, publiee_le=timezone.now(),
        )
        PalierPrix.objects.create(campagne=campagne, quantite_min=30, prix_unitaire=16000)
        for acheteur, quantite in zip(acheteurs[1:], (5, 4, 3)):
            self._payer(campagne, acheteur, quantite)
        self.stdout.write("  - Offre concurrente sur le riz (comparateur)")

    def _discussions(self, groupeur, concurrent, acheteurs, admin) -> None:
        """Des fils de discussion vivants, et un message à modérer."""
        campagnes = list(
            Campagne.objects.filter(statut=Campagne.Statut.EN_COURS).order_by("id")
        )
        if not campagnes:
            return

        echanges = [
            ("Est-ce que la garantie couvre la casse a la livraison ?",
             "Oui, tout colis endommage est remplace - vous verifiez au retrait."),
            ("On peut passer recuperer en soiree apres 18 h ?",
             "Le depot reste ouvert jusqu'a 19 h 30 du lundi au samedi."),
            ("Possible de prendre deux pieces et d'en faire livrer une a Kara ?",
             "La remise se fait a Lome ; pour Kara je peux indiquer un transporteur."),
            ("La photo correspond bien au modele exact ?",
             "Oui, photo prise sur le lot que j'ai en commande."),
        ]

        for rang, campagne in enumerate(campagnes[: len(echanges)]):
            question, reponse = echanges[rang]
            auteur = acheteurs[rang % len(acheteurs)]
            message = Commentaire.objects.create(
                campagne=campagne, auteur=auteur, texte=question,
                cree_le=timezone.now() - timedelta(hours=7 + rang),
            )
            Commentaire.objects.create(
                campagne=campagne, auteur=campagne.groupeur, reponse_a=message,
                texte=reponse, cree_le=timezone.now() - timedelta(hours=5 + rang),
            )
            # Les « j'aime » sont posés un par un plutôt qu'en compteur : le
            # fil doit savoir qui a déjà aimé, sinon le coeur de chacun est faux.
            for amateur in acheteurs[: 2 + rang % 3]:
                if amateur.id != auteur.id:
                    JaimeCommentaire.objects.create(
                        commentaire=message, utilisateur=amateur
                    )
            message.nombre_jaime = message.jaime.count()
            message.save(update_fields=["nombre_jaime"])

        avis = Commentaire.objects.create(
            campagne=campagnes[0], auteur=acheteurs[2],
            texte="Troisieme commande chez ce groupeur, toujours impeccable.",
            cree_le=timezone.now() - timedelta(days=1),
        )
        for amateur in acheteurs[:4]:
            if amateur.id != avis.auteur_id:
                JaimeCommentaire.objects.create(commentaire=avis, utilisateur=amateur)
        avis.nombre_jaime = avis.jaime.count()
        avis.save(update_fields=["nombre_jaime"])

        # Un message masqué, pour que la modération ait de quoi montrer.
        Commentaire.objects.create(
            campagne=campagnes[0], auteur=acheteurs[4],
            texte="Arnaque totale, ne commandez jamais ici !!!",
            cree_le=timezone.now() - timedelta(hours=3),
            masque_le=timezone.now() - timedelta(hours=2),
            masque_par=admin,
            motif_masquage="Accusation sans fondement, aucun litige ouvert.",
        )

        self.stdout.write(
            f"  - Discussions sur {min(len(campagnes), len(echanges))} campagnes "
            "+ 1 message masque"
        )

    def _avis(self, acheteurs) -> None:
        """Des notes laissées par les acheteurs, bonnes et moins bonnes.

        La plateforme n'arbitre pas les litiges : c'est la note qui
        sanctionne. La démonstration doit donc montrer les deux — un
        groupeur bien noté, et un avis mécontent avec la réponse du
        groupeur en dessous.
        """
        from groupachat.paiements.services import recalculer_reputation

        notees = list(
            Participation.objects.filter(
                statut__in=(
                    Participation.Statut.RETIREE,
                    Participation.Statut.PRETE,
                    Participation.Statut.REMBOURSEE,
                )
            ).select_related("campagne__groupeur")[:6]
        )
        if not notees:
            return

        contenus = [
            (5, "Riz conforme, sacs scellés, remise rapide. Rien à redire."),
            (5, "Deuxieme groupage avec Abalo, toujours impeccable."),
            (4, "Bon produit, mais j'ai attendu deux jours de plus que prevu."),
            (2, "Le coloris ne correspondait pas a la photo. Decevant."),
            (5, "Prix imbattable a plusieurs, je recommande."),
            (3, "Correct sans plus, le point de remise est loin de chez moi."),
        ]

        groupeurs = set()
        for participation, (note, commentaire) in zip(notees, contenus):
            avis = Avis.objects.create(
                participation=participation, note=note, commentaire=commentaire
            )
            groupeurs.add(participation.campagne.groupeur)

            # Le droit de réponse, sur l'avis le plus sévère.
            if note <= 2:
                avis.reponse = (
                    "Desole pour ce coloris. Contactez-moi, je vous "
                    "l'echange sur le prochain arrivage."
                )
                avis.repondu_le = timezone.now()
                avis.save(update_fields=["reponse", "repondu_le"])

        for groupeur in groupeurs:
            recalculer_reputation(groupeur)

        self.stdout.write(f"  - {len(notees)} avis laisses par les acheteurs")

    def _notifications_lues(self, acheteurs) -> None:
        """Toutes les notifications ne sont pas neuves.

        Une cloche où tout est non lu paraît fausse : on marque les plus
        anciennes comme lues pour que le compteur ait l'air d'avoir vécu.
        """
        # Tout le monde, pas seulement les acheteurs : le groupeur recoit une
        # notification par paiement, et une cloche a cinquante non lues ne
        # ressemble a rien.
        for acheteur in Utilisateur.objects.all():
            identifiants = list(
                Notification.objects.filter(destinataire=acheteur)
                .order_by("cree_le")
                .values_list("id", flat=True)
            )
            deja_lues = identifiants[: max(0, len(identifiants) - 3)]
            Notification.objects.filter(id__in=deja_lues).update(
                lue_le=timezone.now() - timedelta(hours=6)
            )
        restantes = Notification.objects.filter(lue_le__isnull=True).count()
        self.stdout.write(f"  - {restantes} notifications non lues reparties")

    def _acheteurs(self) -> list[Utilisateur]:
        return [
            Utilisateur.objects.create_user(
                telephone, MOT_DE_PASSE, nom=nom, prenom=prenom,
                telephone_verifie=True,
            )
            for telephone, prenom, nom in ACHETEURS
        ]

    def _campagne(self, groupeur, categorie, nom, marque, prix, minimum,
                  jours=14, **extra) -> Campagne:
        produit = Produit.objects.create(
            categorie=categorie, nom=nom, marque=marque,
            description=extra.pop("description", ""),
            caracteristiques=extra.pop("caracteristiques", {}),
            propose_par=groupeur,
        )
        campagne = Campagne.objects.create(
            produit=produit, groupeur=groupeur,
            titre=extra.pop("titre", ""),
            description=extra.pop("conditions", ""),
            prix_unitaire=prix, quantite_minimale=minimum,
            date_limite=timezone.now() + timedelta(days=jours),
            point_remise=extra.pop("point_remise", "Marché d'Adawlato, Lomé"),
            statut=Campagne.Statut.EN_COURS, publiee_le=timezone.now(),
            **extra,
        )
        return campagne

    def _payer(self, campagne, acheteur, quantite) -> Participation:
        prix = campagne.prix_pour_quantite(campagne.quantite_reservee + quantite)
        participation = Participation.objects.create(
            campagne=campagne, acheteur=acheteur, quantite=quantite,
            prix_unitaire_applique=prix, montant_total=prix * quantite,
        )
        encaisser(participation, operateur="tmoney", numero=acheteur.telephone)
        participation.refresh_from_db()
        return participation

    # ── Les cinq états ──────────────────────────────────────────────────────

    def _campagne_en_collecte(self, groupeur, rayons, acheteurs):
        campagne = self._campagne(
            groupeur, rayons["Alimentation"], "Sac de riz parfumé 25 kg", "Délice",
            18000, 20, jours=12,
            titre="Riz Délice 25 kg — arrivage de novembre",
            description="Riz parfumé importé de Thaïlande, sac de 25 kg.",
            caracteristiques={"Poids": "25 kg", "Origine": "Thaïlande",
                              "Variété": "Jasmin"},
            conditions="Sacs neufs, scellés. Remise au marché d'Adawlato.",
            objectif_participants=15,
        )
        PalierPrix.objects.create(campagne=campagne, quantite_min=20, prix_unitaire=16500)
        PalierPrix.objects.create(campagne=campagne, quantite_min=50, prix_unitaire=15000)

        for acheteur, quantite in zip(acheteurs, (3, 2, 4, 2)):
            self._payer(campagne, acheteur, quantite)

        question = Commentaire.objects.create(
            campagne=campagne, auteur=acheteurs[0],
            texte="Bonjour, c'est bien du riz parfumé et non du riz brisé ?",
        )
        Commentaire.objects.create(
            campagne=campagne, auteur=groupeur, reponse_a=question,
            texte="Bonjour, oui, riz jasmin parfumé, sacs scellés d'origine.",
        )
        Commentaire.objects.create(
            campagne=campagne, auteur=acheteurs[2],
            texte="J'ai déjà commandé chez Abalo le mois dernier, tout était nickel.",
            nombre_jaime=4,
        )
        self.stdout.write("  • Campagne en collecte (riz) — 11/20 pièces")

    def _autres_collectes(self, groupeur, rayons, acheteurs):
        """De quoi faire défiler le fil d'accueil.

        Une seule campagne ouverte suffirait à prouver que la mécanique
        marche, mais pas à montrer le produit : le fil vertical de l'accueil
        ne se comprend que s'il y a de quoi défiler.
        """
        catalogue = [
            {
                "categorie": "Téléphonie", "nom": "Écouteurs sans fil", "marque": "Oraimo",
                "prix": 14000, "minimum": 25, "jours": 9,
                "titre": "Écouteurs Oraimo — lot de fin d'année",
                "description": "Bluetooth 5.3, boîtier de charge, 30 h d'autonomie.",
                "caracteristiques": {"Autonomie": "30 h", "Bluetooth": "5.3"},
                "paliers": [(25, 12500), (60, 11000)],
                "parts": (4, 3, 2),
            },
            {
                "categorie": "Maison", "nom": "Matelas orthopédique 160×200", "marque": "Dolidol",
                "prix": 145000, "minimum": 8, "jours": 18,
                "titre": "Matelas Dolidol 160×200 — import direct",
                "description": "Mousse haute densité, housse déhoussable, garantie 5 ans.",
                "caracteristiques": {"Dimensions": "160 × 200 cm", "Garantie": "5 ans"},
                "paliers": [(8, 132000)],
                "parts": (1, 1),
            },
            {
                "categorie": "Alimentation", "nom": "Bidon d'huile végétale 20 L", "marque": "Dinor",
                "prix": 28000, "minimum": 15, "jours": 5,
                "titre": "Huile Dinor 20 L — arrivage du port",
                "description": "Huile de tournesol raffinée, bidon scellé de 20 litres.",
                "caracteristiques": {"Contenance": "20 L", "Type": "Tournesol"},
                "paliers": [(15, 26000), (40, 24500)],
                "parts": (3, 2, 2, 1),
            },
            {
                "categorie": "Mode", "nom": "Pagne wax 6 yards", "marque": "Vlisco",
                "prix": 32000, "minimum": 12, "jours": 3,
                "titre": "Pagnes wax Vlisco — collection de saison",
                "description": "Six yards, coton 100 %, motifs au choix à la commande.",
                "caracteristiques": {"Longueur": "6 yards", "Matière": "Coton"},
                "paliers": [(12, 29000)],
                "parts": (2, 2, 1, 1, 1),
            },
            {
                "categorie": "Électroménager", "nom": "Congélateur coffre 200 L", "marque": "Hisense",
                "prix": 215000, "minimum": 6, "jours": 21,
                "titre": "Congélateurs Hisense 200 L — groupage de novembre",
                "description": "Classe A+, 200 litres, garantie constructeur 2 ans.",
                "caracteristiques": {"Volume": "200 L", "Classe": "A+", "Garantie": "2 ans"},
                "paliers": [(6, 198000)],
                "parts": (1, 1, 1),
            },
        ]

        for fiche in catalogue:
            campagne = self._campagne(
                groupeur, rayons[fiche["categorie"]], fiche["nom"], fiche["marque"],
                fiche["prix"], fiche["minimum"], jours=fiche["jours"],
                titre=fiche["titre"], description=fiche["description"],
                caracteristiques=fiche["caracteristiques"],
            )
            for seuil, prix in fiche["paliers"]:
                PalierPrix.objects.create(
                    campagne=campagne, quantite_min=seuil, prix_unitaire=prix
                )
            for acheteur, quantite in zip(acheteurs, fiche["parts"]):
                self._payer(campagne, acheteur, quantite)

        self.stdout.write(f"  • {len(catalogue)} autres campagnes en collecte")

    def _campagne_financee(self, groupeur, rayons, acheteurs):
        campagne = self._campagne(
            groupeur, rayons["Téléphonie"], "Smartphone 128 Go double SIM", "Itel",
            95000, 5, jours=2,
            titre="Smartphone Itel 128 Go — lot de novembre",
            description="Neuf, sous blister, garantie 6 mois.",
            caracteristiques={"Stockage": "128 Go", "RAM": "6 Go",
                              "Écran": "6,6 pouces"},
        )
        for acheteur, quantite in zip(acheteurs, (2, 1, 1, 1)):
            self._payer(campagne, acheteur, quantite)
        cloturer(campagne)
        demander_decaissement(campagne)
        self.stdout.write("  • Campagne financée (smartphones) — décaissement à valider")

    def _campagne_en_distribution(self, groupeur, rayons, acheteurs, admin):
        campagne = self._campagne(
            groupeur, rayons["Maison"], "Ventilateur sur pied 3 vitesses", "Binatone",
            22000, 6, jours=1,
            titre="Ventilateurs Binatone — arrivage immédiat",
            description="Trois vitesses, oscillation, garantie 1 an.",
        )
        for acheteur, quantite in zip(acheteurs, (2, 2, 1, 2)):
            self._payer(campagne, acheteur, quantite)
        cloturer(campagne)
        decaissement = demander_decaissement(campagne)
        executer_decaissement(decaissement, admin)
        mettre_a_disposition(campagne, point_remise="Boutique Abalo, Bè-Kpota")
        self.stdout.write(
            "  • Campagne en distribution (ventilateurs) — codes de retrait actifs"
        )

    def _campagne_terminee(self, groupeur, rayons, acheteurs, admin):
        campagne = self._campagne(
            groupeur, rayons["Électroménager"], "Blender 1,5 L", "Moulinex",
            35000, 4, jours=1,
            titre="Blenders Moulinex — lot d'octobre",
        )
        parts = [
            self._payer(campagne, acheteur, quantite)
            for acheteur, quantite in zip(acheteurs, (1, 1, 2))
        ]
        cloturer(campagne)
        executer_decaissement(demander_decaissement(campagne), admin)
        mettre_a_disposition(campagne)
        for participation in parts:
            participation.refresh_from_db()
            valider_retrait(campagne, participation.code_retrait, groupeur)
        self.stdout.write("  • Campagne terminée (blenders) — tous les colis retirés")

    def _campagne_annulee(self, groupeur, rayons, acheteurs):
        campagne = self._campagne(
            groupeur, rayons["Mode"], "Paire de baskets", "Sportif",
            25000, 30, jours=1,
            titre="Baskets — minimum non atteint",
        )
        self._payer(campagne, acheteurs[0], 1)
        self._payer(campagne, acheteurs[1], 1)
        cloturer(campagne)
        self.stdout.write("  • Campagne annulée (baskets) — participants remboursés")

    def _brouillon(self, groupeur, rayons):
        produit = Produit.objects.create(
            categorie=rayons["Alimentation"], nom="Bidon d'huile 20 L",
            marque="Dinor", propose_par=groupeur,
        )
        Campagne.objects.create(
            produit=produit, groupeur=groupeur, titre="Huile Dinor 20 L — à publier",
            prix_unitaire=28000, quantite_minimale=15,
            date_limite=timezone.now() + timedelta(days=20),
            point_remise="Marché d'Adawlato, Lomé",
            statut=Campagne.Statut.BROUILLON,
        )
        self.stdout.write("  • Brouillon (huile) — prêt à publier en direct")

    def _demandes(self, acheteurs, rayons):
        demandes = [
            ("Panneau solaire 200 W avec batterie", rayons["Électronique"], 120000),
            ("Sacs de ciment CIMTOGO", rayons["Maison"], 4500),
            ("Machine à coudre industrielle", rayons["Maison"], 185000),
        ]
        for index, (titre, categorie, budget) in enumerate(demandes):
            demande = DemandeProduit.objects.create(
                auteur=acheteurs[index], titre=titre, categorie=categorie,
                budget_indicatif=budget,
                description="Si un groupeur peut en importer, je suis preneur.",
            )
            interesses = acheteurs[: len(acheteurs) - index]
            for acheteur in interesses:
                InteretDemande.objects.create(demande=demande, utilisateur=acheteur)
            demande.nombre_interets = len(interesses)
            demande.save(update_fields=["nombre_interets"])
        self.stdout.write("  • Trois demandes communautaires")

    def _resumer(self, valide, en_attente, admin):
        self.stdout.write(self.style.SUCCESS("\nJeu de démonstration chargé.\n"))
        self.stdout.write(f"  Mot de passe commun : {MOT_DE_PASSE}\n")
        self.stdout.write("  Administrateur      : 99000011")
        self.stdout.write(f"  Groupeur validé     : {valide.telephone} (Abalo Import)")
        self.stdout.write(
            f"  Groupeur en attente : {en_attente.telephone} (écran de blocage KYC)"
        )
        self.stdout.write("  Acheteurs           : " + ", ".join(a[0] for a in ACHETEURS))
