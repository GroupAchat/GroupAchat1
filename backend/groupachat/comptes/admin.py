# -*- coding: utf-8 -*-
"""L'examen des dossiers KYC dans l'admin Django — écran A2 (§13.6).

Le §10.5 le dit sans détour : « **dans le MVP, tout se fait à la main**, dans
l'admin Django : dépôt des pièces par le groupeur, examen par un
administrateur, validation, attribution du niveau et du plafond ». À ce volume,
c'est le bon choix — et c'est aussi ce qui nous apprend à qui nous avons
affaire.

Cet écran n'est donc pas un pis-aller en attendant une belle interface. Il est
l'outil de travail, et l'écran A2 du produit lui emprunte sa logique par
``api_kyc.py``.

## Ce que la liste met en avant, et pourquoi

Un administrateur qui ouvre cette page le matin a une question unique : **quel
dossier dois-je traiter maintenant ?** Les colonnes y répondent dans cet ordre :

1. **l'ancienneté** — un dossier qui attend depuis six jours est un groupeur
   qui s'en va, et le recrutement est le goulot d'étranglement du lancement ;
2. **la concordance des noms** — le contrôle n° 2, celui qui arrête tout, et
   qu'on doit voir sans ouvrir la fiche ;
3. **l'état de l'annonce** — un dossier tranché mais non annoncé est un
   dossier dont le groupeur ne sait rien. Il n'est plus dans la file d'attente,
   donc plus personne ne le reprend : c'est la panne silencieuse de ce
   parcours, et elle a sa propre colonne.

⚠️ **Il n'y a volontairement aucune action de masse « tout valider ».** Elle
économiserait quelques minutes et détruirait le produit : « nous sélectionnons
nos groupeurs » ne vaut que si chaque dossier a été ouvert. Les deux actions
offertes traitent plusieurs dossiers à la fois, mais chacune exige un motif
unique — donc un groupe de dossiers refusés *pour la même raison*, pas un
tampon.
"""

from __future__ import annotations

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.html import format_html

from .. import domaine
from .annonces import annoncer
from .models import Acheteur, DecisionKyc, Groupeur, PieceKyc


@admin.register(Acheteur)
class AcheteurAdmin(admin.ModelAdmin):
    """L'acheteur. Peu de champs, et c'est le propos (§1.5).

    ⚠️ **Cette classe portait : « Ni mot de passe ni courriel ».** C'est faux
    depuis que le compte acheteur est un vrai compte, et la phrase est
    reproduite pour que personne ne la restaure. Son argument tient toujours
    autrement : ni l'un ni l'autre n'est **demandé** pour commander.

    ## ⚠️ Pourquoi ``exclude`` existe, et ce qui arrivait sans lui

    Un ``ModelAdmin`` sans ``fields`` ni ``exclude`` construit son formulaire
    avec **tous** les champs modifiables. ``mot_de_passe`` y apparaissait donc
    comme une simple ligne de texte, et deux choses s'ensuivaient :

    - l'empreinte était **lisible** par tout membre du personnel ouvrant la
      fiche — de quoi l'attaquer hors ligne, sans limite d'essais ni verrou ;
    - y taper un mot de passe l'enregistrait **en clair**. ``check_password``
      échouerait alors sur toute saisie, et l'acheteur se retrouverait
      incapable de se connecter **sans aucun message d'erreur nulle part** :
      l'administrateur croirait avoir rendu service.

    Le mot de passe ne se pose que par ``POST /api/comptes/moi/mot-de-passe/``,
    qui hache. Il n'y a volontairement **aucun moyen d'en définir un depuis
    l'administration** : le support n'a pas à connaître le secret de
    quelqu'un, et l'acheteur a déjà le code SMS pour reprendre la main.

    ``a_un_mot_de_passe`` le remplace dans la fiche — un booléen, qui est tout
    ce dont le support a besoin pour répondre à « je n'arrive pas à me
    connecter ».
    """

    list_display = ("telephone", "nom", "a_un_mot_de_passe", "cree_le")
    search_fields = ("telephone", "nom", "courriel")

    #: ⚠️ **Ne jamais retirer ``mot_de_passe`` d'ici** — voir la docstring.
    exclude = ("mot_de_passe",)

    #: Le verrou se **lit** mais ne se modifie pas à la main : on le lève par
    #: l'action ci-dessous, qui remet aussi le compteur à zéro. Les deux
    #: valeurs doivent rester d'accord, et deux champs libres côte à côte sont
    #: la façon sûre de les désynchroniser.
    readonly_fields = (
        "cree_le",
        "a_un_mot_de_passe",
        "echecs_connexion",
        "bloque_jusqu_a",
    )

    actions = ("lever_le_verrou",)

    @admin.display(boolean=True, description="a un mot de passe")
    def a_un_mot_de_passe(self, acheteur: Acheteur) -> bool:
        return bool(acheteur.mot_de_passe)

    @admin.action(description="Lever le verrou de connexion")
    def lever_le_verrou(self, request, queryset) -> None:
        """Rouvre la voie du mot de passe après cinq échecs.

        ⚠️ **C'est un confort de support, pas un recours indispensable.**
        L'acheteur n'a pas besoin de nous : un code SMS lève le verrou tout
        seul, et c'est précisément pour ça que le verrou peut être sévère.
        Cette action sert à quelqu'un qui appelle avant d'avoir essayé.

        Elle ne révèle ni ne change aucun mot de passe.
        """
        modifies = queryset.update(echecs_connexion=0, bloque_jusqu_a=None)
        self.message_user(
            request, f"{modifies} verrou(x) levé(s). Aucun mot de passe modifié."
        )


class PieceEnLigne(admin.TabularInline):
    """Les pièces, dans la fiche du groupeur — pas sur une autre page.

    Les contrôles 1 et 2 du §10.5 s'examinent **ensemble** : le nom sur la
    pièce, le visage sur le selfie, le titulaire du compte. Les répartir sur
    deux pages obligerait à faire des allers-retours, c'est-à-dire à comparer
    de mémoire.
    """

    model = PieceKyc
    extra = 0
    fields = ("nature", "reference", "depose_le")
    readonly_fields = ("depose_le",)


class DecisionEnLigne(admin.TabularInline):
    """L'historique des décisions. **En lecture seule.**

    Une ligne de journal ne se corrige pas : un dossier repris produit une
    nouvelle décision, qui n'effface pas la précédente. C'est cet historique
    qui montre qu'un groupeur en est à sa troisième tentative — information
    qu'un champ d'état seul perdrait.
    """

    model = DecisionKyc
    extra = 0
    can_delete = False
    fields = (
        "issue",
        "libelle_motif",
        "niveau_accorde",
        "decide_par",
        "decide_le",
        "canal",
        "notifie_le",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj) -> bool:
        # On ne fabrique pas une décision à la main : on passe par les actions,
        # qui appliquent les contrôles et envoient l'annonce.
        return False


@admin.register(Groupeur)
class GroupeurAdmin(admin.ModelAdmin):
    list_display = (
        "pseudonyme",
        "statut_kyc",
        "jours_d_attente",
        "concordance",
        "annonce",
        "niveau",
        "plafond_affiche",
        "telephone",
    )
    list_filter = ("statut_kyc", "niveau")
    search_fields = ("pseudonyme", "nom_complet", "telephone", "courriel")
    readonly_fields = ("cree_le", "concordance", "plafond_affiche")
    inlines = (PieceEnLigne, DecisionEnLigne)
    # Du plus ancien au plus récent : voir le commentaire d'en-tête.
    ordering = ("cree_le",)

    fieldsets = (
        (
            "Identité — contrôle n° 1",
            {
                "fields": ("pseudonyme", "nom_complet", "telephone", "courriel"),
                "description": (
                    "Le pseudonyme est la seule chose que les acheteurs voient "
                    "(§1.7). Le nom complet ne sort jamais vers eux."
                ),
            },
        ),
        (
            "Compte de retrait — contrôle n° 2",
            {
                "fields": (
                    "titulaire_mobile_money",
                    "numero_mobile_money",
                    "concordance",
                ),
                "description": (
                    "Si le titulaire ne porte pas le nom de la pièce "
                    "d'identité, la procédure s'arrête : il n'y a pas de bonne "
                    "raison de recevoir l'argent des acheteurs sur le compte "
                    "de quelqu'un d'autre."
                ),
            },
        ),
        (
            "Décision",
            {
                "fields": ("statut_kyc", "niveau", "plafond_affiche", "cree_le"),
                "description": (
                    "Le plafond se déduit du niveau (§10.4) et ne se saisit "
                    "pas. Au niveau Établi il n'y en a pas : il se fixe au cas "
                    "par cas avec le groupeur."
                ),
            },
        ),
    )

    actions = ("valider_les_dossiers", "renvoyer_pour_piece_illisible")

    # ── Les colonnes calculées ──────────────────────────────────────────────

    @admin.display(description="attente", ordering="cree_le")
    def jours_d_attente(self, groupeur: Groupeur) -> str:
        """Depuis combien de temps il attend. Vide si le dossier est tranché."""
        if groupeur.statut_kyc != Groupeur.StatutKyc.EN_VERIFICATION:
            return "—"
        jours = (timezone.now() - groupeur.cree_le).days
        if jours == 0:
            return "aujourd'hui"
        # Au-delà de deux jours ouvrés, on sort du délai annoncé au groupeur à
        # l'inscription. Il le voit, donc l'administrateur doit le voir aussi.
        marque = " ⚠️" if jours > 2 else ""
        return f"{jours} j{marque}"

    @admin.display(description="noms", boolean=True)
    def concordance(self, groupeur: Groupeur) -> bool:
        """Le contrôle n° 2, **recalculé à chaque affichage**.

        Pas lu depuis un champ figé au dépôt : le compte Mobile Money peut
        avoir changé depuis, et c'est le signal d'alerte numéro un du §10.5.
        """
        return domaine.noms_concordent(
            groupeur.nom_complet, groupeur.titulaire_mobile_money
        )

    @admin.display(description="annonce")
    def annonce(self, groupeur: Groupeur) -> str:
        """Le groupeur sait-il ce qui a été décidé ?"""
        decision = groupeur.derniere_decision
        if decision is None:
            return "—"
        if decision.notifie_le is not None:
            return format_html(
                "<span title='{}'>annoncée</span>", decision.get_canal_display()
            )
        return format_html(
            "<b style='color:#B42318'>à annoncer — {}</b>",
            decision.get_canal_display(),
        )

    @admin.display(description="plafond")
    def plafond_affiche(self, groupeur: Groupeur) -> str:
        plafond = groupeur.plafond
        if plafond is None:
            return "au cas par cas"
        return f"{int(plafond):,} F".replace(",", " ")

    # ── Les actions ─────────────────────────────────────────────────────────

    @admin.action(description="Valider le dossier et prévenir le groupeur")
    def valider_les_dossiers(self, request, queryset) -> None:
        """Valide, puis annonce — par courriel s'il y en a un, sinon par appel.

        Le canal n'est pas demandé parce qu'il se déduit : un dossier sans
        courriel ne peut être annoncé que de vive voix. Le script d'appel
        apparaît alors dans un message, prêt à être lu.
        """
        self._trancher(request, queryset, issue="valide", motif=None)

    @admin.action(description="Renvoyer le dossier — pièce illisible")
    def renvoyer_pour_piece_illisible(self, request, queryset) -> None:
        """Le cas de loin le plus fréquent, d'où son action dédiée.

        Il **ne refuse pas** : le dossier repasse « à compléter », le groupeur
        reprend sa photo, et le reste de son dossier est conservé. Refuser
        définitivement une photo floue ferait perdre des groupeurs
        recrutables.

        Les autres motifs se traitent dossier par dossier, par l'écran A2 ou
        par l'API : ils méritent qu'on ouvre la fiche.
        """
        self._trancher(
            request, queryset, issue="a-completer", motif="piece-illisible"
        )

    def _trancher(self, request, queryset, issue: str, motif: str | None) -> None:
        qui = request.user.get_full_name() or request.user.get_username()

        for groupeur in queryset:
            canal = (
                DecisionKyc.Canal.COURRIEL
                if groupeur.courriel
                else DecisionKyc.Canal.APPEL
            )
            try:
                decision = groupeur.trancher(
                    issue=issue, decide_par=qui, canal=canal, motif=motif
                )
            except ValidationError as erreur:
                self.message_user(
                    request,
                    f"{groupeur.pseudonyme} : {erreur.messages[0]}",
                    level=messages.ERROR,
                )
                continue

            try:
                resultat = annoncer(decision)
            except ValidationError as erreur:
                self.message_user(
                    request,
                    f"{groupeur.pseudonyme} : décision enregistrée, mais "
                    f"{erreur.messages[0]}",
                    level=messages.WARNING,
                )
                continue

            if resultat.annonce:
                self.message_user(
                    request,
                    f"{groupeur.pseudonyme} : décision enregistrée et courriel "
                    f"envoyé à {groupeur.courriel}.",
                    level=messages.SUCCESS,
                )
            else:
                # Le script est donné ici, et la décision reste « à annoncer »
                # jusqu'à ce que quelqu'un ait réellement téléphoné.
                self.message_user(
                    request,
                    format_html(
                        "<b>{} : à appeler au {}.</b> Décision enregistrée, "
                        "annonce à faire. Script :<pre style='white-space:"
                        "pre-wrap;margin:.5em 0'>{}</pre>",
                        groupeur.pseudonyme,
                        groupeur.telephone,
                        resultat.script,
                    ),
                    level=messages.WARNING,
                )


@admin.register(DecisionKyc)
class DecisionKycAdmin(admin.ModelAdmin):
    """Le journal des décisions, consultable seul.

    Il répond à deux questions qu'on ne peut pas poser depuis la fiche d'un
    groupeur : **qu'est-ce qui a été décidé cette semaine**, et **quels
    dossiers ont été tranchés sans que personne n'ait prévenu l'intéressé**.
    Le filtre sur ``notifie_le`` sert exactement à la seconde.
    """

    list_display = (
        "groupeur",
        "issue",
        "libelle_motif",
        "decide_par",
        "decide_le",
        "canal",
        "notifie_le",
    )
    list_filter = ("issue", "canal", "notifie_le", "motif")
    search_fields = ("groupeur__pseudonyme", "decide_par")
    date_hierarchy = "decide_le"

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        # Un journal se lit, il ne se corrige pas (§18.3).
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(PieceKyc)
class PieceKycAdmin(admin.ModelAdmin):
    """Les pièces déposées.

    ⚠️ **Aucune miniature, aucune prévisualisation**, et ce n'est pas une
    simplification : le §10.5 exige que les pièces d'identité et les selfies ne
    partagent pas le stockage des photos de produits, avec un accès restreint
    et une durée de conservation fixée. Ce stockage n'existe pas encore —
    ``reference`` n'est qu'une clé opaque. Afficher une image ici supposerait
    une URL servie publiquement, c'est-à-dire exactement ce qu'il ne faut pas
    construire.
    """

    list_display = ("groupeur", "nature", "depose_le")
    list_filter = ("nature",)
    search_fields = ("groupeur__pseudonyme",)
