# -*- coding: utf-8 -*-
"""Questions publiques et demandes de produit.

**Il n'y a pas de messagerie privée dans ce produit.** Une question est
publique, filtrée avant publication, et son auteur n'apparaît que par un prénom
et une initiale. Le groupeur répond sous son pseudonyme. Ni l'un ni l'autre ne
peut joindre l'autre autrement — et c'est ce canal, justement parce qu'il est le
seul, qui rend l'anonymat supportable des deux côtés.
"""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models

from .. import moderation, notifications_acheteur


class Question(models.Model):
    """Une question publique posée sur une campagne."""

    class Etat(models.TextChoices):
        PUBLIEE = "publiee", "Publiée"
        #: Visible de son seul auteur, en attente du classifieur (écran 10, b).
        EN_VERIFICATION = "en-verification", "En vérification"
        REFUSEE = "refusee", "Refusée"

    campagne = models.ForeignKey(
        "catalogue.Campagne",
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="campagne",
    )
    auteur = models.ForeignKey(
        "comptes.Acheteur",
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="auteur",
    )
    texte = models.TextField("question")
    etat = models.CharField(
        "état", max_length=20, choices=Etat.choices, default=Etat.PUBLIEE
    )
    posee_le = models.DateTimeField("posée le", auto_now_add=True)

    reponse = models.TextField("réponse", blank=True)
    repondue_le = models.DateTimeField("répondue le", null=True, blank=True)

    class Meta:
        verbose_name = "question"
        verbose_name_plural = "questions"
        ordering = ("-posee_le",)

    def __str__(self) -> str:
        return self.texte[:60]

    @property
    def auteur_affiche(self) -> str:
        """« Akosua D. » — prénom et initiale, jamais un nom complet (§1.7)."""
        morceaux = (self.auteur.nom or "").split()
        if not morceaux:
            return "Acheteur vérifié"
        if len(morceaux) == 1:
            return morceaux[0]
        return f"{morceaux[0]} {morceaux[-1][0]}."

    def clean(self) -> None:
        """Repasse le message au filtre, côté serveur.

        ⚠️ **Le client a déjà fait ce contrôle, et ça ne suffit pas.** Le
        filtre côté React prévient l'utilisateur avant l'envoi ; celui-ci
        protège la base. Un client modifié ou un appel direct à l'API
        contournent le premier, aucun ne contourne le second.
        """
        super().clean()

        verdict = moderation.verifier(self.texte)
        if not verdict.publiable:
            explication = moderation.expliquer(verdict.motif or "", role="acheteur")
            raise ValidationError({"texte": explication["corps"]})

        if self.reponse:
            verdict_reponse = moderation.verifier(self.reponse)
            if not verdict_reponse.publiable:
                explication = moderation.expliquer(
                    verdict_reponse.motif or "", role="groupeur"
                )
                raise ValidationError({"reponse": explication["corps"]})

    def save(self, *args, **kwargs):
        self.full_clean(validate_unique=False)
        return super().save(*args, **kwargs)


class Notification(models.Model):
    """Ce qui s'allume dans la cloche d'un acheteur.

    ## ⚠️ Le texte est ecrit ici, pas a l'affichage

    ``titre`` et ``corps`` sont **figes au moment de l'envoi**. Une
    notification decrit un evenement date : « vos 5 000 F vous ont ete
    rembourses » doit continuer a dire 5 000 F si le prix de la part change
    ensuite. Les formulations vivent dans ``notifications_acheteur.py``, qui
    ne connait pas Django — ce modele ne fait que les ranger.

    ## ⚠️ Ce n'est pas une messagerie

    Un groupeur peut **declencher** une notification, jamais en rediger le
    texte. Il n'y a donc aucun champ libre qui traverse ce modele, et rien a
    soumettre au filtre du §15 : c'est ce qui permet a cette cloche d'exister
    sans ouvrir le canal prive que le produit refuse.

    Les trois cles etrangeres sont **toutes facultatives** et servent a
    ouvrir le bon ecran au clic. On en garde une par nature, pas plus : une
    notification qui ne sait pas ou elle mene est une notification qu'on lit
    et qu'on oublie.
    """

    class Nature(models.TextChoices):
        #: Le groupeur a recu la marchandise. Declenche par lui (ecran 15).
        PRODUIT_ARRIVE = "produit-arrive", "Le produit est arrivé"
        #: Le groupeur a repondu a une question posee par cette personne.
        REPONSE_QUESTION = "reponse-question", "Réponse à votre question"
        #: Le groupage a ete cloture. Declenche par la cloture elle-meme.
        GROUPAGE_CLOTURE = "groupage-cloture", "Groupage clôturé"
        #: Le groupage a ete annule et les acheteurs rembourses.
        GROUPAGE_ANNULE = "groupage-annule", "Groupage annulé"

    destinataire = models.ForeignKey(
        "comptes.Acheteur",
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="destinataire",
    )
    nature = models.CharField("nature", max_length=20, choices=Nature.choices)
    titre = models.CharField("titre", max_length=120)
    corps = models.TextField("corps")

    campagne = models.ForeignKey(
        "catalogue.Campagne",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
        verbose_name="campagne concernée",
    )
    commande = models.ForeignKey(
        "commandes.Commande",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
        verbose_name="commande concernée",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
        verbose_name="question concernée",
    )

    creee_le = models.DateTimeField("créée le", auto_now_add=True)
    lue_le = models.DateTimeField("lue le", null=True, blank=True)

    class Meta:
        verbose_name = "notification"
        verbose_name_plural = "notifications"
        ordering = ("-creee_le",)
        #: La cloche demande « combien de non lues » a chaque ouverture
        #: d'ecran : c'est la requete la plus frequente du modele.
        indexes = [models.Index(fields=["destinataire", "lue_le"])]

    def __str__(self) -> str:
        return f"{self.titre} → {self.destinataire_id}"


def _envoyer(destinataire, nature, redaction, **liens):
    """Enregistre une notification. Usage interne a ce module."""
    titre, corps = redaction
    return Notification.objects.create(
        destinataire=destinataire,
        nature=nature,
        titre=titre,
        corps=corps,
        **liens,
    )


def _destinataires_de(campagne):
    """Les acheteurs a prevenir, et **leur commande quand elle est unique**.

    ⚠️ **Le lien vers la commande n'est pas decoratif : c'est ce que la
    personne cherche.** « Votre commande est arrivee » doit ouvrir le suivi —
    la frise, le code de livraison, le refus du colis — et non la fiche du
    produit, qu'elle connait deja. Sans ce lien, elle lit la notification puis
    doit retrouver sa commande a la main, et cesse d'ouvrir la cloche.

    ⚠️ **Et seulement quand elle est unique.** Deux commandes de la meme
    personne sur le meme groupage ne designent aucune commande en
    particulier : la notification parle alors du groupage, et c'est la fiche
    produit qui s'ouvre. Choisir arbitrairement la premiere ouvrirait une fois
    sur deux la mauvaise.

    Renvoie une liste de ``(acheteur, commande_ou_None)``.
    """
    from ..commandes.models import Commande

    commandes = campagne.commandes.filter(
        statut__in=Commande.STATUTS_PAYANTS
    ).select_related("acheteur")

    par_acheteur: dict[int, list] = {}
    for commande in commandes:
        par_acheteur.setdefault(commande.acheteur_id, []).append(commande)

    return [
        (siennes[0].acheteur, siennes[0] if len(siennes) == 1 else None)
        for siennes in par_acheteur.values()
    ]


def prevenir_de_l_arrivee(campagne) -> int:
    """Previent les participants que le produit est arrive. Ecran 15.

    ⚠️ **Seuls les acheteurs qui ont paye**, et chacun une fois. Un groupeur
    qui appuie deux fois ne doit pas envoyer deux notifications : l'arrivee
    est un fait unique, et une cloche qui repete le meme message perd en une
    semaine le droit d'etre regardee. Le garde-fou est
    ``Campagne.arrivee_annoncee_le``, cote appelant.

    Renvoie le nombre de personnes prevenues — c'est ce que l'ecran affiche,
    et c'est **un compte, pas une liste** : le groupeur n'apprend rien sur
    qui elles sont.
    """
    redaction = notifications_acheteur.produit_arrive(campagne)

    # ⚠️ Deux commandes d'une meme personne ne font qu'une notification : elle
    # parle du produit, pas de la commande.
    destinataires = _destinataires_de(campagne)
    for acheteur, commande in destinataires:
        _envoyer(
            acheteur,
            Notification.Nature.PRODUIT_ARRIVE,
            redaction,
            campagne=campagne,
            commande=commande,
        )
    return len(destinataires)


def prevenir_d_une_reponse(question) -> None:
    """Previent l'auteur d'une question que le groupeur a repondu."""
    _envoyer(
        question.auteur,
        Notification.Nature.REPONSE_QUESTION,
        notifications_acheteur.reponse_a_une_question(question),
        campagne=question.campagne,
        question=question,
    )


def prevenir_de_la_cloture(campagne) -> int:
    """Previent les participants que le groupage est cloture."""
    redaction = notifications_acheteur.groupage_cloture(campagne)

    destinataires = _destinataires_de(campagne)
    for acheteur, commande in destinataires:
        _envoyer(
            acheteur,
            Notification.Nature.GROUPAGE_CLOTURE,
            redaction,
            campagne=campagne,
            commande=commande,
        )
    return len(destinataires)


def prevenir_de_l_annulation(commandes) -> int:
    """Previent chaque acheteur de l'annulation **et de son remboursement**.

    ⚠️ **Une notification par commande, et non par personne**, a la
    difference des trois autres : le texte porte le montant rembourse. Deux
    commandes font deux remboursements, donc deux montants, donc deux
    messages — les fondre en un seul obligerait a additionner, et un total
    qui ne correspond a aucune ligne du releve est pire que deux lignes.
    """
    compte = 0
    for commande in commandes:
        _envoyer(
            commande.acheteur,
            Notification.Nature.GROUPAGE_ANNULE,
            notifications_acheteur.groupage_annule(commande),
            campagne=commande.campagne,
            commande=commande,
        )
        compte += 1
    return compte


class SignalementQuestion(models.Model):
    """Un lecteur signale une question deja publiee. §15, niveau 3.

    ⚠️ **Un signalement ne depublie rien, et c'est le point essentiel.**

    La tentation est forte : un message signale disparait, on verifie ensuite.
    Ce serait donner a n'importe qui le pouvoir de faire taire n'importe qui —
    il suffirait de signaler la question genante (« ce produit est-il
    garanti ? ») pour l'effacer du seul canal public du produit. Le §15 est
    explicite : le niveau 3 est **humain, apres publication**. Le signalement
    remplit une file ; un administrateur tranche.

    ⚠️ **Trois motifs fermes, aucun champ libre** — c'est la regle du §15
    elle-meme. Un champ libre contiendrait au bout de six mois quarante
    formulations du meme probleme, et la file ne serait plus triable : on ne
    saurait plus **quoi** le filtre automatique laisse passer, donc plus quoi
    corriger dans ``moderation.py``.
    """

    class Motif(models.TextChoices):
        COORDONNEES = "coordonnees", "Coordonnées personnelles"
        HORS_PLATEFORME = "hors-plateforme", "Proposition de vente hors plateforme"
        INAPPROPRIE = "inapproprie", "Contenu inapproprié"

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="signalements",
        verbose_name="question",
    )
    #: Qui a signale. Une session est exigee : un signalement anonyme ne se
    #: limite pas, et la file se remplirait plus vite qu'on ne la vide.
    auteur = models.ForeignKey(
        "comptes.Acheteur",
        on_delete=models.CASCADE,
        related_name="signalements",
        verbose_name="auteur du signalement",
    )
    motif = models.CharField("motif", max_length=20, choices=Motif.choices)
    signale_le = models.DateTimeField("signalé le", auto_now_add=True)
    #: Ce qu'un administrateur en a fait. Vide = encore dans la file.
    traite_le = models.DateTimeField("traité le", null=True, blank=True)

    class Meta:
        verbose_name = "signalement de question"
        verbose_name_plural = "signalements de questions"
        ordering = ("-signale_le",)
        #: ⚠️ **Un signalement par personne et par question.** Sans cette
        #: contrainte, un seul lecteur contrarie peut gonfler le compteur
        #: autant qu'il veut et faire passer un message devant les autres dans
        #: la file — c'est-a-dire decider seul de ce qu'un humain regarde en
        #: premier.
        constraints = [
            models.UniqueConstraint(
                fields=["question", "auteur"],
                name="un_signalement_par_personne_et_par_question",
            )
        ]

    def __str__(self) -> str:
        return f"{self.get_motif_display()} — {self.question}"


class Demande(models.Model):
    """Une demande de produit — la demande crée l'offre.

    Un échec de recherche n'est jamais un cul-de-sac : il mène ici, et le fil
    des demandes du groupeur (écran 19) les lui montre **agrégées**.
    """

    class Statut(models.TextChoices):
        EN_ATTENTE = "en-attente", "En attente"
        PRISE_EN_CHARGE = "prise-en-charge", "Prise en charge"
        CAMPAGNE_LANCEE = "campagne-lancee", "Groupage lancé"
        #: Doit exister et doit être montré : une demande peut ne rien donner,
        #: et l'acheteur doit l'apprendre plutôt que d'attendre indéfiniment.
        NON_ABOUTIE = "non-aboutie", "Non aboutie"

    acheteur = models.ForeignKey(
        "comptes.Acheteur",
        on_delete=models.CASCADE,
        related_name="demandes",
        verbose_name="acheteur",
    )
    produit = models.CharField("produit", max_length=160)
    #: Texte libre et court : « 20 litres », « 2 paires ».
    quantite = models.CharField("quantité", max_length=60)
    quartier = models.CharField("quartier", max_length=40)
    budget_maximum = models.DecimalField(
        "budget maximum", max_digits=12, decimal_places=0, null=True, blank=True
    )
    precisions = models.TextField("précisions", blank=True)

    #: La photo du produit cherché, facultative.
    #:
    #: **Elle sert au groupeur, pas à l'acheteur.** « Un pagne comme celui-là »
    #: se montre en une image et ne s'écrit pas en trois lignes : c'est le fil
    #: des demandes (écran 19) qui en tire le bénéfice, puisque c'est là que
    #: quelqu'un décide d'aller sourcer le produit ou non.
    #:
    #: ⚠️ **Des octets, pas un fichier.** Le choix et son coût sont expliqués
    #: en entier à ``domaine.PHOTO_DEMANDE_MAX_OCTETS``. En deux lignes : le
    #: §18 laisse le stockage objet à définir, le §10.5 interdit
    #: ``MEDIA_ROOT``, et un plafond court rend l'attente tenable.
    #:
    #: ``editable=False`` parce qu'aucun formulaire d'administration ne doit
    #: proposer de coller des octets à la main.
    photo = models.BinaryField(
        "photo", null=True, blank=True, editable=False
    )
    #: Le type MIME **vérifié sur les octets**, jamais celui déclaré par le
    #: client — voir ``domaine.nature_de_la_photo``. Vide quand il n'y a pas
    #: de photo, ce qui en fait aussi le test de présence le moins coûteux :
    #: lire ce champ ne charge pas les octets.
    photo_type = models.CharField("type de la photo", max_length=40, blank=True)

    statut = models.CharField(
        "statut", max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE
    )
    campagne = models.ForeignKey(
        "catalogue.Campagne",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="demandes_satisfaites",
        verbose_name="campagne lancée",
    )
    deposee_le = models.DateTimeField("déposée le", auto_now_add=True)

    class Meta:
        verbose_name = "demande"
        verbose_name_plural = "demandes"
        ordering = ("-deposee_le",)

    def __str__(self) -> str:
        return f"{self.produit} — {self.quartier}"
