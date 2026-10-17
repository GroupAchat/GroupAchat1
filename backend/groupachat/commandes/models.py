# -*- coding: utf-8 -*-
"""Les commandes et les paiements.

**Trois champs à ne pas perdre de vue**, signalés par le §6 du PRD et tous les
trois présents ici :

- ``frais_livraison`` est **séparé** de ``montant_parts``. La part est la même
  pour tous, les frais dépendent de la position ; les fondre interdirait à
  l'acheteur de vérifier qu'on ne lui a rien glissé dans le total ;
- ``quartier`` et ``repere`` conservent la **position** sur la commande, parce
  que c'est elle qui a déterminé les frais et que le livreur en aura besoin ;
- ``cle_idempotence`` protège le paiement. Sans elle, un acheteur qui touche
  deux fois « Confirmer » sur un réseau lent paie deux fois.
"""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.db import models, transaction

from .. import domaine


class Commande(models.Model):
    """Une part achetée dans une campagne."""

    class Statut(models.TextChoices):
        PAYEE = "payee", "Payée — en attente de clôture"
        CLOTUREE = "cloturee", "Groupage clôturé"
        CHEZ_LE_GROUPEUR = "chez-le-groupeur", "Commande en cours chez le groupeur"
        EN_LIVRAISON = "en-livraison", "En cours de livraison"
        LIVREE = "livree", "Livrée"
        LITIGE = "litige", "Litige"
        REMBOURSEE = "remboursee", "Remboursée"
        ANNULEE = "annulee", "Groupage annulé"

    #: Les statuts où l'acheteur a payé. Doit rester identique à
    #: ``catalogue.models.Statut_PAYANTS`` — un test le vérifie.
    STATUTS_PAYANTS = (
        Statut.PAYEE,
        Statut.CLOTUREE,
        Statut.CHEZ_LE_GROUPEUR,
        Statut.EN_LIVRAISON,
        Statut.LIVREE,
    )

    campagne = models.ForeignKey(
        "catalogue.Campagne",
        on_delete=models.PROTECT,
        related_name="commandes",
        verbose_name="campagne",
    )
    acheteur = models.ForeignKey(
        "comptes.Acheteur",
        on_delete=models.PROTECT,
        related_name="commandes",
        verbose_name="acheteur",
    )

    quantite = models.PositiveIntegerField(
        "quantité", default=1, validators=[MinValueValidator(1)]
    )
    variante = models.CharField("variante", max_length=60, blank=True)

    montant_parts = models.DecimalField(
        "montant des parts", max_digits=12, decimal_places=0
    )
    frais_livraison = models.DecimalField(
        "frais de livraison", max_digits=12, decimal_places=0
    )
    total = models.DecimalField("total payé", max_digits=12, decimal_places=0)

    #: La position, conservée sur la commande.
    #:
    #: ⚠️ Elle **ne remonte jamais au groupeur** (§1.7) : lui ne voit que le
    #: quartier. Le repère et le téléphone ne sortent qu'une fois, vers le
    #: livreur, le jour de la tournée.
    quartier = models.CharField("quartier", max_length=40)
    repere = models.CharField("repère", max_length=200)
    telephone = models.CharField("téléphone à joindre", max_length=20)

    code_livraison = models.CharField(
        "code de livraison", max_length=10, unique=True, db_index=True
    )

    #: Générée par le client **avant** l'appel de paiement : c'est tout son
    #: intérêt. Deux appuis sur « Confirmer » portent la même clé, et le
    #: serveur n'encaisse qu'une fois.
    cle_idempotence = models.CharField(
        "clé d'idempotence", max_length=80, unique=True, db_index=True
    )

    statut = models.CharField(
        "statut", max_length=20, choices=Statut.choices, default=Statut.PAYEE
    )
    passee_le = models.DateTimeField("passée le", auto_now_add=True)

    # ── Le refus du colis à la livraison (écran 9) ──────────────────────────
    #
    # ⚠️ **Le refus ouvre un litige, il ne rembourse pas.** La spec de
    # l'écran 9 est précise sur ce qu'on promet : « Group Achat examine votre
    # dossier sous 48 h et vous rembourse **si le refus est justifié** ».
    # Rembourser sur simple déclaration serait ouvrir la porte à refuser un
    # colis conforme, et le groupeur a déjà retiré son argent à la clôture —
    # la perte serait pour nous, à chaque fois. D'où ``LITIGE`` et un humain.

    class MotifDeRefus(models.TextChoices):
        PAS_LE_PRODUIT = "pas-le-produit", "Ce n'est pas le produit commandé"
        ABIME = "abime", "Produit visiblement abîmé"
        AUTRE = "autre", "Autre"

    motif_de_refus = models.CharField(
        "motif du refus",
        max_length=20,
        choices=MotifDeRefus.choices,
        blank=True,
    )
    #: La description libre que l'acheteur a écrite. ⚠️ **Elle est utile ici,
    #: là où un champ libre est interdit dans la file de modération (§15) :**
    #: celle-ci n'est pas triée par machine, elle est lue une par une par
    #: quelqu'un qui doit décider s'il rembourse. « Ce n'est pas la bonne
    #: pointure » est exactement ce qu'il a besoin de savoir.
    description_du_refus = models.TextField("description du refus", blank=True)
    refuse_le = models.DateTimeField("refusé le", null=True, blank=True)

    class Meta:
        verbose_name = "commande"
        verbose_name_plural = "commandes"
        ordering = ("-passee_le",)
        indexes = [models.Index(fields=["campagne", "statut"])]

    def __str__(self) -> str:
        return f"{self.code_livraison} — {self.campagne.titre}"

    def refuser_le_colis(self, motif: str, description: str = "") -> None:
        """L'acheteur refuse le colis au moment de la remise (écran 9).

        ⚠️ **Refusable pendant la livraison, et à ce moment seulement.**
        Avant, il n'y a rien à refuser — le colis n'est pas parti. Après, la
        commande est marquée livrée, donc le code de livraison a été donné au
        livreur : contester alors n'est plus un refus de colis mais une
        réclamation après réception, et les deux ne s'instruisent pas de la
        même façon. Sans ce verrou, le bouton serait un moyen de rouvrir
        indéfiniment une commande close.

        ⚠️ **Elle n'appelle pas ``save()`` du modèle entier par hasard.**
        ``full_clean`` recalculerait les montants et les frais de livraison :
        si le barème du §4 a changé depuis la commande, une commande
        parfaitement valable deviendrait impossible à refuser — l'acheteur
        serait bloqué par une règle qui ne le concerne pas. On n'écrit donc
        que les quatre champs du refus.
        """
        if self.statut != self.Statut.EN_LIVRAISON:
            raise ValidationError(
                "Un colis ne se refuse que pendant la livraison."
            )
        if motif not in self.MotifDeRefus.values:
            raise ValidationError({"motif": "Motif de refus inconnu."})

        self.motif_de_refus = motif
        self.description_du_refus = description
        self.refuse_le = timezone.now()
        self.statut = self.Statut.LITIGE
        self.save(
            update_fields=[
                "motif_de_refus",
                "description_du_refus",
                "refuse_le",
                "statut",
            ]
        )

    def clean(self) -> None:
        """Vérifie que le total n'a pas été fabriqué par le client.

        Les montants arrivent du client pour qu'il puisse afficher un
        récapitulatif, mais **c'est le serveur qui fait foi** : on recalcule et
        on refuse si ça ne tombe pas juste. Sans ce contrôle, une requête forgée
        pourrait payer 5 000 F une commande à 50 000 F.
        """
        super().clean()

        if self.total != self.montant_parts + self.frais_livraison:
            raise ValidationError(
                "Le total doit être la somme des parts et des frais de livraison."
            )

        if self.campagne_id:
            # ⚠️ **Le prix applicable, pas `prix_part`.** Un groupage peut
            # porter une grille degressive : 1 part a 5 000 F, 5 parts a
            # 3 500 F. Multiplier par `prix_part` refuserait alors une
            # commande parfaitement valide — et c'est exactement le genre de
            # verrou qui se retourne contre l'acheteur.
            unitaire = self.campagne.prix_pour(self.quantite)
            attendu = domaine.arrondir(unitaire * self.quantite)
            if self.montant_parts != attendu:
                raise ValidationError(
                    "Le montant des parts ne correspond pas au prix "
                    "applicable à cette quantité."
                )

        frais = domaine.calculer_frais_livraison(self.quartier)
        if not frais.desservi:
            raise ValidationError(
                f"Nous ne livrons pas encore à {self.quartier}."
            )
        if self.frais_livraison != frais.montant:
            raise ValidationError(
                "Les frais de livraison ne correspondent pas au tarif de la zone."
            )

        if not self.repere.strip():
            # À Lomé le repère vaut plus que la coordonnée : un livreur avec un
            # point sur une carte mais sans repère tourne quand même.
            raise ValidationError({"repere": "Le repère est obligatoire."})


@transaction.atomic
def enregistrer_paiement(
    *,
    campagne,
    acheteur,
    quantite: int,
    quartier: str,
    repere: str,
    telephone: str,
    cle_idempotence: str,
    variante: str = "",
) -> tuple[Commande, bool]:
    """Encaisse une commande, une seule fois par clé d'idempotence.

    Renvoie ``(commande, creee)``. Si la clé a déjà servi, la commande
    existante est renvoyée avec ``creee=False`` et **rien n'est débité une
    seconde fois** — c'est exactement le cas d'un acheteur qui touche deux fois
    « Confirmer » sur un réseau lent, et c'est le cas le plus fréquent.

    ⚠️ Le paiement lui-même est **simulé** jusqu'à l'agrément d'un agrégateur
    (§18.2 du cahier des charges). Cette fonction enregistre la commande comme
    si l'encaissement avait réussi ; l'appel à l'agrégateur viendra ici, entre
    la vérification de la clé et la création.
    """

    # ⚠️ **Le plafond de collecte, contrôlé ici et nulle part ailleurs**
    # (§10.4).
    #
    # Il ne protège pas de la fraude, il **borne le montant maximal d'un
    # sinistre** — ce qui, pour une jeune structure, est la différence entre un
    # incident et une fermeture. Ce rôle n'a de sens qu'au moment où l'argent
    # entre : le contrôler à la création de la campagne, quand la collecte vaut
    # zéro, revenait à ne rien contrôler.
    #
    # Le message s'adresse à l'acheteur, qui n'a rien fait de mal et n'a pas à
    # comprendre nos règles internes : on lui dit que le groupage est complet,
    # pas que le groupeur a atteint son plafond.
    plafond = campagne.groupeur.plafond
    if plafond is not None:
        apres = campagne.collecte_sur_les_parts + (
            campagne.prix_pour(quantite) * quantite
        )
        if apres > plafond:
            raise PlafondAtteint(
                "Ce groupage est complet. Il se clôture bientôt — revenez "
                "voir le prochain."
            )

    existante = Commande.objects.filter(cle_idempotence=cle_idempotence).first()
    if existante is not None:
        return existante, False

    if not campagne.est_ouverte:
        raise ValidationError("Ce groupage n'est plus ouvert.")

    montant_parts, frais, total = domaine.calculer_total_commande(
        campagne.prix_pour(quantite), quantite, quartier
    )

    commande = Commande(
        campagne=campagne,
        acheteur=acheteur,
        quantite=quantite,
        variante=variante,
        montant_parts=montant_parts,
        frais_livraison=frais,
        total=total,
        quartier=quartier,
        repere=repere,
        telephone=telephone,
        cle_idempotence=cle_idempotence,
        code_livraison=domaine.generer_code_livraison(),
        statut=Commande.Statut.PAYEE,
    )
    commande.full_clean(validate_unique=False)
    commande.save()
    return commande, True


class PlafondAtteint(Exception):
    """Un paiement qui ferait dépasser le plafond de collecte du groupeur.

    Une exception à part, et non une ``ValidationError`` : ce n'est pas une
    saisie fautive. L'acheteur n'a rien fait de mal, et l'interface doit le
    traiter comme « ce groupage est complet », pas comme « votre formulaire est
    invalide ».
    """


class Retrait(models.Model):
    """Le retrait d'un groupage par son groupeur, ouvert à la clôture.

    ## ⚠️ Ce n'est plus un versement, et le mot a disparu exprès

    L'argent de l'acheteur est inscrit au **portefeuille du groupeur** dès son
    paiement (§9 du cahier des charges). La plateforme ne détient plus les
    fonds pour son compte et ne « verse » donc plus rien : elle tient le
    compte, et elle **exécute des retraits**. Écrire « nous vous versons »
    laisserait croire que nous pourrions ne pas le faire.

    **Le solde est détenu jusqu'à la clôture**, puis retirable intégralement,
    avant la livraison. Aucun écran ne doit écrire « votre argent est bloqué
    jusqu'à la livraison » : la formulation exacte est « détenu jusqu'à la
    clôture ».

    ## Trois états, et un seul nous appelle à agir

    | État | Ce que ça veut dire | Qui agit |
    |---|---|---|
    | ``retirable`` | Groupage clôturé et maintenu, le solde est à lui | Lui |
    | ``demande`` | Il a appuyé sur « Retirer mes fonds » | **Nous** |
    | ``effectue`` | L'argent est parti, 1 500 F retenus | Personne |

    ⚠️ **Le devis fournisseur ne conditionne plus rien.** Il est demandé, lu et
    archivé, mais son absence ne bloque aucun retrait : un portefeuille dont le
    titulaire ne peut pas retirer son propre argent sans l'accord d'un tiers
    n'est pas un portefeuille. Le §9.1 du cahier des charges dit ce que cette
    perte nous coûte, et le §10.2 ce qui la remplace partiellement.

    ## Pourquoi le montant est calculé dès la clôture

    Les frais sont un montant fixe (§9.2), donc connus d'avance : rien
    n'oblige à attendre le retrait pour les calculer. Le groupeur voit donc à
    la clôture **le chiffre exact** qu'il touchera, et c'est ce chiffre qui le
    fait décider à l'écran 16. « Retenus au retrait » dit *quand l'argent sort
    de son solde*, pas *quand on sait combien*.
    """

    class Etat(models.TextChoices):
        #: Clôturé et maintenu : le solde est à lui, il retire quand il veut.
        RETIRABLE = "retirable", "Retirable"
        #: Il a demandé son retrait ; c'est à nous d'exécuter le transfert.
        DEMANDE = "demande", "Retrait demandé"
        EFFECTUE = "effectue", "Effectué"
        #: Le groupage a échoué après la clôture : rien ne part.
        ANNULE = "annule", "Annulé"

    campagne = models.OneToOneField(
        "catalogue.Campagne",
        on_delete=models.PROTECT,
        related_name="retrait",
        verbose_name="campagne",
    )
    collecte = models.DecimalField("collecté sur les parts", max_digits=12, decimal_places=0)
    frais_plateforme = models.DecimalField(
        "frais de plateforme", max_digits=12, decimal_places=0
    )
    net = models.DecimalField("net pour le groupeur", max_digits=12, decimal_places=0)
    #: Collectés auprès des acheteurs, reversés au transporteur.
    #: ⚠️ **Jamais touchés par les frais** : ce n'est pas l'argent du groupeur.
    frais_livraison_collectes = models.DecimalField(
        "frais de livraison collectés", max_digits=12, decimal_places=0
    )
    etat = models.CharField(
        "état", max_length=20, choices=Etat.choices, default=Etat.RETIRABLE
    )

    #: Quand le groupeur a demandé son retrait. ``None`` s'il ne l'a pas fait.
    demande_le = models.DateTimeField("demandé le", null=True, blank=True)

    #: Quand l'argent est réellement parti. ``None`` tant qu'il est là.
    libere_le = models.DateTimeField("exécuté le", null=True, blank=True)
    #: Qui a exécuté le transfert. ⚠️ Un nom en clair faute d'authentification
    #: côté administration — voir ``api_kyc.JetonAdmin``. Le jour où les
    #: comptes existent, ce champ devient une clé étrangère.
    libere_par = models.CharField("exécuté par", max_length=120, blank=True)

    effectue_le = models.DateTimeField("ouvert le", auto_now_add=True)

    class Meta:
        verbose_name = "retrait"
        verbose_name_plural = "retraits"
        ordering = ("-effectue_le",)

    def __str__(self) -> str:
        return f"{self.campagne.titre} — {self.net} F"

    @property
    def devis(self):
        """Le devis fournisseur déposé pour cette campagne, s'il y en a un.

        C'est ce que l'administrateur lit : chez qui le groupeur achète, et
        pour combien.

        ⚠️ **Il ne commande plus le retrait.** Rien ici ne l'empêche d'être
        ``None`` au moment où l'argent part — voir ``Retrait.retirable``.
        """
        return self.campagne.justificatifs.filter(
            nature=Justificatif.Nature.DEVIS
        ).first()

    @property
    def retirable(self) -> bool:
        """Le groupeur peut-il demander son retrait ?

        ⚠️ **La clôture suffit, et le devis n'entre pas dans ce calcul.** C'est
        la décision du §10.1 : son solde est à lui dès que le groupage est
        clôturé et maintenu. Le contrôle qui s'exerçait ici — refuser tant que
        le devis manquait — a disparu avec le portefeuille, et le §9.1 dit
        franchement ce que ça coûte.
        """
        return self.etat == self.Etat.RETIRABLE

    @property
    def executable(self) -> bool:
        """Y a-t-il un transfert à faire partir, de notre côté ?

        **Seulement s'il l'a demandé.** Nous n'exécutons jamais un retrait que
        le groupeur n'a pas déclenché : ce serait décider à sa place de sortir
        son argent de la plateforme.
        """
        return self.etat == self.Etat.DEMANDE


@transaction.atomic
def cloturer_campagne(campagne) -> Retrait:
    """Clôture un groupage et ouvre le retrait de son groupeur.

    Les frais portent sur les parts seules ; les frais de livraison sont
    comptés à part et ne sont **jamais** amputés.

    ⚠️ **Rien ne part ici.** La fonction ouvre un retrait à l'état
    ``retirable`` : c'est le groupeur qui décidera de retirer, et nous qui
    exécuterons. Elle ne fait donc bouger aucun argent, elle rend un solde
    disponible.
    """
    collecte = campagne.collecte_sur_les_parts
    resultat = domaine.calculer_retrait(collecte)

    frais_collectes = campagne.commandes.filter(
        statut__in=Commande.STATUTS_PAYANTS
    ).aggregate(total=models.Sum("frais_livraison"))["total"] or Decimal("0")

    campagne.statut = campagne.Statut.EN_COURS
    campagne.save(update_fields=["statut"])
    campagne.commandes.filter(statut=Commande.Statut.PAYEE).update(
        statut=Commande.Statut.CLOTUREE
    )

    # ⚠️ **Les participants sont prévenus ici, et non dans la vue.** La
    # clôture a deux points d'entrée — le bouton du groupeur et la date qui
    # tombe — et brancher la notification sur l'un des deux aurait fait une
    # clôture silencieuse sur l'autre. C'est pourtant l'événement que
    # l'acheteur attend le plus : à partir de là, le groupeur a été payé et
    # c'est notre garantie qui porte.
    #
    # Import tardif : ``echanges`` connaît ``commandes``, et l'inverse ferait
    # un cycle au chargement des modèles.
    from ..echanges.models import prevenir_de_la_cloture

    prevenir_de_la_cloture(campagne)

    return Retrait.objects.create(
        campagne=campagne,
        collecte=resultat.collecte,
        frais_plateforme=resultat.frais,
        net=resultat.net,
        frais_livraison_collectes=domaine.arrondir(frais_collectes),
    )


class Justificatif(models.Model):
    """Le devis fournisseur, puis le reçu de paiement — §10.3.

    Deux pièces, deux moments, et elles ne jouent pas le même rôle :

    | | Quand | Ce qu'elle sert à faire |
    |---|---|---|
    | **Devis** | Après la clôture, avant le retrait | Savoir **chez qui** il achète, et pour combien. ⚠️ Il **constate**, il ne débloque plus rien |
    | **Reçu** | Après l'achat | Vérifier qu'il a bien acheté. Son absence entraîne l'annulation du groupage |

    ⚠️ **Le devis a perdu son levier** en passant au portefeuille du groupeur : son solde est retirable dès la clôture, sans qu'on puisse l'exiger. Ce qui le remplace partiellement est le **délai de dépôt du reçu** du point 4 du §10.2 — une sanction différée au lieu d'un contrôle préventif.

    ⚠️ **Aucun fichier n'est stocké ici**, pour la même raison que les pièces
    d'identité : ``reference`` est une clé dans un stockage à accès restreint,
    qui reste à monter au déploiement. Ce qui est en base, c'est le
    **fournisseur et le montant** — c'est-à-dire ce que l'administrateur lit
    pour décider, et ce qu'on peut recouper plus tard avec le relevé bancaire.
    """

    class Nature(models.TextChoices):
        DEVIS = "devis", "Devis fournisseur"
        RECU = "recu", "Reçu de paiement"

    class Etat(models.TextChoices):
        EN_ATTENTE = "en-attente", "À contrôler"
        VALIDE = "valide", "Validé"
        REFUSE = "refuse", "Refusé"

    campagne = models.ForeignKey(
        "catalogue.Campagne",
        on_delete=models.CASCADE,
        related_name="justificatifs",
        verbose_name="campagne",
    )
    nature = models.CharField("nature", max_length=10, choices=Nature.choices)

    fournisseur = models.CharField("fournisseur", max_length=160)
    montant = models.DecimalField("montant", max_digits=12, decimal_places=0)

    #: La clé dans le stockage à accès restreint. Jamais une URL publique.
    reference = models.CharField("référence de stockage", max_length=200, blank=True)

    etat = models.CharField(
        "état", max_length=20, choices=Etat.choices, default=Etat.EN_ATTENTE
    )
    motif_refus = models.CharField("motif du refus", max_length=240, blank=True)

    depose_le = models.DateTimeField("déposé le", auto_now_add=True)

    class Meta:
        verbose_name = "justificatif"
        verbose_name_plural = "justificatifs"
        ordering = ("-depose_le",)
        constraints = [
            # Un devis et un reçu par campagne. En redéposer un remplace le
            # précédent : sinon l'administrateur examine une pile et ne sait
            # plus lequel fait foi.
            models.UniqueConstraint(
                fields=["campagne", "nature"], name="un_justificatif_par_nature"
            )
        ]

    def __str__(self) -> str:
        return f"{self.get_nature_display()} — {self.campagne.titre}"


@transaction.atomic
def demander_le_retrait(retrait: Retrait) -> Retrait:
    """Le groupeur demande son argent.

    ⚠️ **Nous ne pouvons pas le lui refuser.** Ce solde est le sien depuis le
    paiement de ses acheteurs (§9) ; la seule condition est que le groupage soit
    clôturé et maintenu, c'est-à-dire que le retrait soit à l'état
    ``retirable``. L'absence de devis fournisseur **ne bloque rien** — voir le
    §9.1, qui assume cette perte de levier plutôt que de la masquer.
    """
    if retrait.etat != Retrait.Etat.RETIRABLE:
        raise ValidationError("Ce retrait a déjà été demandé ou traité.")

    retrait.etat = Retrait.Etat.DEMANDE
    retrait.demande_le = timezone.now()
    retrait.save(update_fields=["etat", "demande_le"])
    return retrait


@transaction.atomic
def executer_le_retrait(retrait: Retrait, par: str) -> Retrait:
    """Fait partir l'argent vers le groupeur, les 1 500 F retenus.

    ⚠️ **Seulement s'il l'a demandé.** Exécuter un retrait qu'il n'a pas
    déclenché reviendrait à sortir son argent de la plateforme à sa place.
    """
    if retrait.etat != Retrait.Etat.DEMANDE:
        raise ValidationError(
            "Ce retrait n'a pas été demandé par le groupeur, ou il est déjà "
            "parti."
        )

    retrait.etat = Retrait.Etat.EFFECTUE
    retrait.libere_le = timezone.now()
    retrait.libere_par = par
    retrait.save(update_fields=["etat", "libere_le", "libere_par"])

    # ⚠️ **Aucun virement réel n'est émis.** Le paiement est simulé jusqu'à
    # l'agrément d'un agrégateur (§18.2) : cette ligne note que l'argent *doit*
    # partir, elle ne le fait pas partir. C'est ici que l'appel au prestataire
    # viendra.
    return retrait


@transaction.atomic
def annuler_campagne(campagne) -> None:
    """Annule un groupage et rembourse les acheteurs.

    **Aucun frais n'est prélevé sur un groupage annulé** (§7 du cahier des
    charges) : la fonction ne crée donc aucun ``Retrait``, et c'est volontaire
    — pas de ligne à zéro à expliquer plus tard.
    """
    campagne.statut = campagne.Statut.ANNULEE
    campagne.save(update_fields=["statut"])

    # ⚠️ **On lit les commandes à rembourser avant de les mettre à jour.**
    # Après l'``update``, plus aucune ne répond au filtre ``STATUTS_PAYANTS``
    # et la notification ne partirait à personne — un remboursement annoncé
    # nulle part, qui est exactement le cas où l'acheteur appelle.
    #
    # ``list()`` force la requête tout de suite, pour la même raison : un
    # queryset paresseux serait évalué après l'``update``.
    a_rembourser = list(
        campagne.commandes.filter(
            statut__in=Commande.STATUTS_PAYANTS
        ).select_related("acheteur", "campagne", "campagne__groupeur")
    )

    campagne.commandes.filter(statut__in=Commande.STATUTS_PAYANTS).update(
        statut=Commande.Statut.REMBOURSEE
    )

    from ..echanges.models import prevenir_de_l_annulation

    prevenir_de_l_annulation(a_rembourser)

    # Si le groupage avait déjà été clôturé, son retrait est annulé avec lui —
    # mais **seulement s'il n'est pas déjà parti**. De l'argent retiré ne se
    # reprend pas d'un `update` : ce serait un remboursement à réclamer, et il
    # doit se voir dans le journal plutôt que de disparaître.
    #
    # ⚠️ Un retrait **demandé** s'annule encore : l'argent n'a pas bougé, c'est
    # un ordre en attente d'exécution. Seul `effectue` est irréversible.
    Retrait.objects.filter(
        campagne=campagne,
        etat__in=(Retrait.Etat.RETIRABLE, Retrait.Etat.DEMANDE),
    ).update(etat=Retrait.Etat.ANNULE)
