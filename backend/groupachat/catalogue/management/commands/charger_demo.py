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

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from groupachat.catalogue.models import (
    AbonnementPublication,
    Campagne,
    Categorie,
    EtatDemonstration,
    MediaProduit,
    MediaCampagne,
    PackPublication,
    PalierPrix,
    Produit,
)
from groupachat.commandes.models import Avis, Participation
from groupachat.comptes import parrainage, points
from groupachat.comptes.parrainage import Parrainage
from groupachat.comptes.models import (
    CodeVerification,
    DossierKYC,
    MouvementPoints,
    Reputation,
    Utilisateur,
)
from groupachat.echanges.models import (
    DemandeProduit,
    InteretDemande,
    AbonnementContactPrive,
    Conversation,
    Message,
    Notification,
)
from groupachat.paiements.models import Decaissement, Sequestre, Transaction
from groupachat.paiements.services import (
    cloturer,
    demander_decaissement,
    encaisser,
    executer_decaissement,
    mettre_a_disposition,
    remettre_le_colis,
)

# ⚠️ **À incrémenter dès qu'on touche au jeu de données.** C'est ce numéro,
# et lui seul, qui décide si un redéploiement remet la démonstration à plat.
# Laissé inchangé, les nouveautés n'apparaîtraient jamais sur un serveur déjà
# démarré une fois.
VERSION_DEMO = "14"

MOT_DE_PASSE = "demo2026Groupe"

RAYONS = [
    ("Alimentation", "panier", []),
    ("Électronique", "puce", ["Téléphonie", "Électroménager"]),
    ("Maison", "maison", []),
    ("Mode", "vetement", []),
]

# Le quatrième élément est le nom d'utilisateur choisi, vide quand l'acheteur
# n'en a pas voulu : la démonstration doit montrer les deux cas, parce que le
# repli « Prénom I. » est le plus fréquent et qu'on doit le voir à l'écran.
ACHETEURS = [
    ("91002233", "Ama", "Mensah", "AmaK"),
    ("92003344", "Yao", "Dossou", ""),
    ("93004455", "Akouvi", "Adjo", "Kouvi228"),
    ("94005566", "Kodjo", "Agbeko", ""),
    ("95006677", "Afi", "Lawson", "Afi-L"),
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
        self._en_verification(concurrent, rayons)
        self._offre_concurrente(concurrent, acheteurs)
        self._demandes(acheteurs, rayons)
        self._discussions(valide, concurrent, acheteurs, admin)
        self._avis(acheteurs)
        self._notifications_lues(acheteurs)
        self._grades(valide, concurrent)
        self._droit_de_publier(valide, concurrent)
        self._parrainages(acheteurs)

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
            Parrainage,
            Avis, Transaction, Decaissement, Sequestre,
            Notification, Message, Conversation, AbonnementContactPrive,
            AbonnementPublication, PackPublication,
            InteretDemande, DemandeProduit,
            Participation, PalierPrix, MediaCampagne, Campagne,
            MediaProduit, Produit,
            DossierKYC, Reputation, CodeVerification,
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
            nom_utilisateur="Faya-02",
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
            nom_utilisateur="Doumega",
            role=Utilisateur.Role.GROUPEUR, telephone_verifie=True,
        )
        DossierKYC.objects.create(
            utilisateur=en_attente, type_piece=DossierKYC.TypePiece.PASSEPORT,
            numero_piece="TG-P-220199", numero_mobile_money="90009988",
            nom_commerce="Afi Distribution",
        )
        return valide, en_attente

    def _second_groupeur(self, admin) -> Utilisateur:
        """Un deuxième groupeur validé, avec un passé.

        Sans lui, la place de marché n'en est pas une : impossible de montrer
        deux offres sur le même produit, ni une réputation qui diffère d'un
        vendeur à l'autre.
        """
        groupeur = Utilisateur.objects.create_user(
            "96004477", MOT_DE_PASSE, nom="Amegan", prenom="Essi",
            nom_utilisateur="Zogbe",
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

    def _grades(self, bronze, argent) -> None:
        """Des groupeurs aux trois grades, pour que le barème se voie.

        Les points sont posés directement sur les compteurs plutôt que gagnés
        groupage par groupeur : atteindre Or demanderait soixante-dix
        groupages aboutis, et le jeu de démonstration en compte sept. Ce qu'on
        veut montrer, c'est la **conséquence** du grade — la commission
        affichée, la surveillance allégée —, pas le chemin pour y arriver.
        """
        cumules_du_bronze = points.compteur_de(bronze).cumules
        points.attribuer(
            argent, MouvementPoints.Motif.CORRECTION, "demonstration", 1,
            points=560 - points.compteur_de(argent).cumules,
        )

        # Un troisième groupeur, au grade Or : sans lui, la commission à
        # 1,3 % n'apparaît nulle part et le haut du barème reste abstrait.
        chevronne = Utilisateur.objects.create_user(
            "96115588", MOT_DE_PASSE, nom="Kponton", prenom="Dede",
            nom_utilisateur="Dedali", role=Utilisateur.Role.GROUPEUR,
            telephone_verifie=True,
        )
        DossierKYC.objects.create(
            utilisateur=chevronne, type_piece=DossierKYC.TypePiece.CNI,
            numero_piece="CNI-TG-770318", numero_mobile_money="96115588",
            nom_commerce="Kponton & Fils", statut=DossierKYC.Statut.VALIDE,
            decide_le=timezone.now() - timedelta(days=400),
        )
        Reputation.objects.create(
            groupeur=chevronne, campagnes_terminees=74, campagnes_annulees=2,
            avis_recus=0, participants_servis=612, note=0,
        )
        points.attribuer(
            chevronne, MouvementPoints.Motif.CORRECTION, "demonstration", 1,
            points=940,
        )
        # Du solde déjà entamé : c'est ce qui montre que dépenser ses points
        # ne fait pas perdre son grade.
        points.depenser(chevronne, 300, "demonstration", 1)

        self.stdout.write(
            f"  - Grades : Bronze ({cumules_du_bronze} pts), "
            "Argent (560 pts), Or (940 cumules, 640 de solde)"
        )

    def _dossiers_a_examiner(self) -> None:
        """De quoi remplir la file d'attente de la console d'administration."""
        candidats = [
            ("97005588", "Komlan", "Sodji", "Sodji Trading", "Kom-Lan",
             DossierKYC.TypePiece.CNI, "CNI-TG-556102"),
            ("98006699", "Nathalie", "Agbo", "NA Cosmetiques", "NathAgb",
             DossierKYC.TypePiece.PASSEPORT, "TG-P-884411"),
        ]
        for telephone, prenom, nom, commerce, pseudo, piece, numero in candidats:
            compte = Utilisateur.objects.create_user(
                telephone, MOT_DE_PASSE, nom=nom, prenom=prenom,
                nom_utilisateur=pseudo,
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
            statut=Campagne.Statut.EN_COURS, publiee_le=timezone.now(),
        )
        PalierPrix.objects.create(campagne=campagne, quantite_min=30, prix_unitaire=16000)
        for acheteur, quantite in zip(acheteurs[1:], (5, 4, 3)):
            self._payer(campagne, acheteur, quantite)
        self.stdout.write("  - Offre concurrente sur le riz (comparateur)")

    def _discussions(self, groupeur, concurrent, acheteurs, admin) -> None:
        """Des conversations privées, et un message signalé à modérer.

        Il n'y a **plus de fil public** sous les campagnes : le seul échange
        possible passe par le Contact Privé, payant. La démonstration doit
        donc montrer les deux côtés de la barrière — des acheteurs abonnés
        qui écrivent, et d'autres qui voient l'offre d'abonnement.
        """
        echanges = [
            ("Est-ce que la garantie couvre la casse a la livraison ?",
             "Oui, tout colis endommage est remplace - vous verifiez au retrait."),
            ("On peut passer recuperer en soiree apres 18 h ?",
             "Le depot reste ouvert jusqu'a 19 h 30 du lundi au samedi."),
            ("La photo correspond bien au modele exact ?",
             "Oui, photo prise sur le lot que j'ai en commande."),
        ]

        # Deux acheteurs abonnés sur cinq : assez pour montrer les fils, assez
        # peu pour que l'écran d'abonnement se voie aussi.
        abonnes = acheteurs[:2]
        for acheteur in abonnes:
            debut_abo, fin_abo = AbonnementContactPrive.prochaine_echeance(acheteur)
            abonnement = AbonnementContactPrive.objects.create(
                abonne=acheteur, debute_le=debut_abo, expire_le=fin_abo,
            )
            points.attribuer(
                acheteur, MouvementPoints.Motif.CONTACT_PRIVE,
                "abonnement_contact_prive", abonnement.id,
            )

        campagne = Campagne.objects.filter(
            statut=Campagne.Statut.EN_COURS, groupeur=groupeur
        ).order_by("id").first()

        for rang, (question, reponse) in enumerate(echanges):
            acheteur = abonnes[rang % len(abonnes)]
            destinataire = groupeur if rang % 2 == 0 else concurrent
            fil, _ = Conversation.objects.get_or_create(
                acheteur=acheteur, groupeur=destinataire,
                defaults={"campagne_initiale": campagne},
            )
            Message.objects.create(
                conversation=fil, auteur=acheteur, texte=question,
                envoye_le=timezone.now() - timedelta(hours=7 + rang),
            )
            dernier = Message.objects.create(
                conversation=fil, auteur=destinataire, texte=reponse,
                envoye_le=timezone.now() - timedelta(hours=5 + rang),
            )
            fil.dernier_message_le = dernier.envoye_le
            fil.save(update_fields=["dernier_message_le"])

        # Un message signalé, pour que la modération ait de quoi montrer.
        fil_tendu, _ = Conversation.objects.get_or_create(
            acheteur=abonnes[0], groupeur=concurrent,
            defaults={"campagne_initiale": campagne},
        )
        Message.objects.create(
            conversation=fil_tendu, auteur=abonnes[0],
            texte="Donne-moi ton numero, on fait l'affaire en direct sans la plateforme.",
            envoye_le=timezone.now() - timedelta(hours=3),
            signale_le=timezone.now() - timedelta(hours=2),
        )

        self.stdout.write(
            f"  - {Conversation.objects.count()} conversations privees "
            f"({len(abonnes)} abonnes) + 1 message signale"
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

    def _livreurs(self):
        """Les deux partenaires qui portent les colis.

        Memorises sur l'instance : ils servent a plusieurs campagnes, et deux
        appels ne doivent pas creer deux comptes pour le meme transporteur.
        """
        if getattr(self, "_les_livreurs", None) is None:
            poste = Utilisateur.objects.create_user(
                "95551122", MOT_DE_PASSE, nom="Agbeko", prenom="Komlan",
                role=Utilisateur.Role.LIVREUR, telephone_verifie=True,
                transporteur=Utilisateur.Transporteur.POSTE,
            )
            gozem = Utilisateur.objects.create_user(
                "95552233", MOT_DE_PASSE, nom="Sossou", prenom="Afi",
                role=Utilisateur.Role.LIVREUR, telephone_verifie=True,
                transporteur=Utilisateur.Transporteur.GOZEM,
            )
            self._les_livreurs = (poste, gozem)
        return self._les_livreurs

    def _acheteurs(self) -> list[Utilisateur]:
        return [
            Utilisateur.objects.create_user(
                telephone, MOT_DE_PASSE, nom=nom, prenom=prenom,
                nom_utilisateur=pseudo or None, telephone_verifie=True,
            )
            for telephone, prenom, nom, pseudo in ACHETEURS
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
            statut=Campagne.Statut.EN_COURS, publiee_le=timezone.now(),
            **extra,
        )
        return campagne

    def _payer(self, campagne, acheteur, quantite) -> Participation:
        prix = campagne.prix_pour(quantite)
        participation = Participation.objects.create(
            campagne=campagne, acheteur=acheteur, quantite=quantite,
            prix_unitaire_applique=prix, montant_total=prix * quantite,
            **self._destination(acheteur),
        )
        encaisser(participation, operateur="tmoney", numero=acheteur.telephone)
        participation.refresh_from_db()
        return participation

    # Le choix du retrait suit **l'acheteur**, pas la campagne : il habite au
    # meme endroit d'un groupage a l'autre. Deux se font livrer, les autres
    # passent a leur bureau de poste — les deux chemins sont ainsi couverts
    # partout dans le jeu, y compris dans la campagne en distribution.
    DESTINATIONS = (
        {"mode_retrait": Participation.ModeRetrait.POSTE,
         "bureau_poste": "Bureau de poste de Tokoin"},
        {"mode_retrait": Participation.ModeRetrait.LIVRAISON,
         "adresse_livraison": "Agoe-Nyive, rue des Cocotiers, maison bleue"},
        {"mode_retrait": Participation.ModeRetrait.POSTE,
         "bureau_poste": "Bureau de poste de Be-Kpota"},
        {"mode_retrait": Participation.ModeRetrait.LIVRAISON,
         "adresse_livraison": "Nyekonakpoe, derriere la pharmacie du Port"},
    )

    def _destination(self, acheteur) -> dict:
        return self.DESTINATIONS[acheteur.id % len(self.DESTINATIONS)]

    def _en_verification(self, oag, rayons):
        """Un groupage qui attend la relecture avant la vitrine.

        Sans lui, l'ecran de verification de la console est toujours vide,
        et la file ne se decouvre qu'en publiant a la main.
        """
        produit = Produit.objects.create(
            categorie=rayons["Électronique"], nom="Chargeur solaire 20 000 mAh",
            marque="Oraimo", propose_par=oag,
        )
        Campagne.objects.create(
            produit=produit, groupeur=oag,
            titre="Chargeurs solaires - en attente de relecture",
            description="Arrivage du port, batterie 20 000 mAh.",
            prix_unitaire=14000, quantite_minimale=12,
            date_limite=timezone.now() + timedelta(days=15),
            statut=Campagne.Statut.EN_VERIFICATION,
        )
        self.stdout.write(
            "  - Groupage en verification (chargeurs) - file de la console"
        )

    def _parrainages(self, acheteurs):
        """Un filleul valide, un autre encore en attente.

        Les deux etats doivent se voir : un ecran qui n'affiche que des
        parrainages aboutis laisse croire qu'un clic suffit.
        """
        marraine, filleul_paye, filleul_en_attente = acheteurs[:3]
        code = parrainage.code_de(marraine)

        # Celui-la a paye : il a deja ses parts dans le jeu de demonstration.
        paye = Parrainage.objects.create(
            parrain=marraine, filleul=filleul_paye,
            campagne=Campagne.objects.filter(
                statut=Campagne.Statut.TERMINEE
            ).first(),
            valide_le=timezone.now() - timedelta(days=3),
        )
        points.attribuer(marraine, points.Motif.PARRAINAGE, "parrainage",
                         paye.id, points=2)

        # Celui-la a commande sans payer : rien n'est credite.
        Parrainage.objects.create(
            parrain=marraine, filleul=filleul_en_attente,
            campagne=Campagne.objects.filter(
                statut=Campagne.Statut.EN_COURS
            ).first(),
        )
        self.stdout.write(
            f"  - Parrainage : code {code} ({marraine.nom_public}), "
            "1 filleul valide, 1 en attente"
        )

    def _droit_de_publier(self, valide, concurrent):
        """Les deux formules, chacune sur un OAG.

        L'abonne publie sans compter ; l'autre vit sur ses packs et en a
        deja consomme. Les deux etats doivent se voir, sinon l'ecran du
        droit de publier ne se lit que dans un sens.
        """
        AbonnementPublication.objects.create(
            oag=valide,
            debute_le=timezone.now() - timedelta(days=4),
            expire_le=timezone.now() + timedelta(days=26),
            reference_paiement="SIM-DEMO-ABO",
        )
        points.attribuer(valide, points.Motif.ABONNEMENT_PUBLICATION,
                         "abonnement_publication_demo", valide.id)

        PackPublication.objects.create(
            oag=concurrent, publications_restantes=2,
            achete_le=timezone.now() - timedelta(days=20),
            reference_paiement="SIM-DEMO-PACK",
        )
        points.attribuer(concurrent, points.Motif.PACK_PUBLICATION,
                         "premier_pack_publication", concurrent.id)
        self.stdout.write(
            "  - Droit de publier : abonnement actif (Faya-02), "
            "pack entame (2/5) pour le concurrent"
        )

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
        # Le barème des deux axes, en entier : c'est la campagne qu'on
        # montre quand on explique le produit.
        #
        # En lignes, les tranches : un acheteur qui prend six sacs paie moins
        # cher qu'un acheteur qui en prend un. En colonnes, la chute : à douze
        # participants, les deux tranches descendent encore — et la
        # différence est rendue à ceux qui avaient déjà payé.
        for quantite, participants, prix in (
            (6, 0, 16500),
            (1, 12, 17000),
            (6, 12, 15200),
        ):
            PalierPrix.objects.create(
                campagne=campagne, quantite_min=quantite,
                participants_min=participants, prix_unitaire=prix,
            )

        for acheteur, quantite in zip(acheteurs, (3, 2, 4, 2)):
            self._payer(campagne, acheteur, quantite)

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
                "paliers": [(5, 0, 12500), (1, 10, 13000), (5, 10, 11500)],
                "parts": (4, 3, 2),
            },
            {
                "categorie": "Maison", "nom": "Matelas orthopédique 160×200", "marque": "Dolidol",
                "prix": 145000, "minimum": 8, "jours": 18,
                "titre": "Matelas Dolidol 160×200 — import direct",
                "description": "Mousse haute densité, housse déhoussable, garantie 5 ans.",
                "caracteristiques": {"Dimensions": "160 × 200 cm", "Garantie": "5 ans"},
                "paliers": [(3, 0, 132000)],
                "parts": (1, 1),
            },
            {
                "categorie": "Alimentation", "nom": "Bidon d'huile végétale 20 L", "marque": "Dinor",
                "prix": 28000, "minimum": 15, "jours": 5,
                "titre": "Huile Dinor 20 L — arrivage du port",
                "description": "Huile de tournesol raffinée, bidon scellé de 20 litres.",
                "caracteristiques": {"Contenance": "20 L", "Type": "Tournesol"},
                "paliers": [(4, 0, 26000), (1, 15, 26500), (4, 15, 24500)],
                "parts": (3, 2, 2, 1),
            },
            {
                "categorie": "Mode", "nom": "Pagne wax 6 yards", "marque": "Vlisco",
                "prix": 32000, "minimum": 12, "jours": 3,
                "titre": "Pagnes wax Vlisco — collection de saison",
                "description": "Six yards, coton 100 %, motifs au choix à la commande.",
                "caracteristiques": {"Longueur": "6 yards", "Matière": "Coton"},
                "paliers": [(3, 0, 29000)],
                "parts": (2, 2, 1, 1, 1),
            },
            {
                "categorie": "Électroménager", "nom": "Congélateur coffre 200 L", "marque": "Hisense",
                "prix": 215000, "minimum": 6, "jours": 21,
                "titre": "Congélateurs Hisense 200 L — groupage de novembre",
                "description": "Classe A+, 200 litres, garantie constructeur 2 ans.",
                "caracteristiques": {"Volume": "200 L", "Classe": "A+", "Garantie": "2 ans"},
                "paliers": [(2, 0, 198000)],
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
            for quantite, participants, prix in fiche["paliers"]:
                PalierPrix.objects.create(
                    campagne=campagne, quantite_min=quantite,
                    participants_min=participants, prix_unitaire=prix,
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
        mettre_a_disposition(campagne)
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
        # C'est **le livreur** qui remet, jamais l'OAG : il a confié le lot
        # a l'agence et ne rencontre pas ses acheteurs.
        poste, gozem = self._livreurs()
        for rang, participation in enumerate(parts):
            participation.refresh_from_db()
            remettre_le_colis(
                participation.code_retrait, poste if rang % 2 == 0 else gozem
            )
        self.stdout.write(
            "  • Campagne terminée (blenders) — colis remis par La Poste et Gozem"
        )

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
                description="Si un OAG peut en importer, je suis preneur.",
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
        self.stdout.write(
            f"  OAG validé          : {valide.telephone} ({valide.nom_public})"
        )
        self.stdout.write(
            f"  OAG en attente      : {en_attente.telephone} (écran de blocage KYC)"
        )
        self.stdout.write("  Acheteurs           : " + ", ".join(a[0] for a in ACHETEURS))
        self.stdout.write("  Livreurs            : 95551122 (La Poste), 95552233 (Gozem)")
