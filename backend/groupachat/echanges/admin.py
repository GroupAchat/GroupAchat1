# -*- coding: utf-8 -*-
"""La file de moderation des questions. §15, niveau 3.

**Elle est ici, dans l'admin Django, et c'est un choix du cahier des
charges** : « Bouton Signaler + file de moderation dans l'admin Django ». Lui
dessiner un ecran dans l'application d'administration coutait un ecran de
plus a tenir, pour un volume qui se compte en unites par semaine au
lancement. Le jour ou cette file se remplit vraiment, elle rejoindra
``src/admin/``.
"""

from django.contrib import admin

from .models import Question, SignalementQuestion


@admin.register(SignalementQuestion)
class AdminSignalementQuestion(admin.ModelAdmin):
    """Ce qu'un moderateur doit voir pour trancher en dix secondes."""

    #: Le texte signale est dans la liste, pas seulement dans la fiche : la
    #: decision se prend en le lisant, et l'ouvrir un par un pour cela ferait
    #: abandonner la file au bout de vingt lignes.
    list_display = ("question_texte", "motif", "auteur", "signale_le", "traite_le")
    list_filter = ("motif", "traite_le")
    search_fields = ("question__texte",)
    #: ⚠️ **En lecture seule, sauf la date de traitement.** Un moderateur
    #: tranche sur l'etat de la question elle-meme ; corriger le motif ou
    #: l'auteur d'un signalement reviendrait a reecrire le fait signale.
    readonly_fields = ("question", "auteur", "motif", "signale_le")
    date_hierarchy = "signale_le"

    @admin.display(description="question signalée", ordering="question__texte")
    def question_texte(self, signalement):
        return signalement.question.texte[:90]


@admin.register(Question)
class AdminQuestion(admin.ModelAdmin):
    """L'etat d'une question, qui est ce sur quoi la moderation agit.

    ⚠️ **Depublier est une action humaine, jamais une consequence d'un
    signalement.** C'est la raison d'etre de cet ecran : le signalement
    remplit la file, et c'est ici qu'on passe une question a ``refusee``.
    """

    list_display = ("texte", "campagne", "auteur", "etat", "nombre_de_signalements")
    list_filter = ("etat",)
    search_fields = ("texte",)
    list_editable = ("etat",)

    @admin.display(description="signalements")
    def nombre_de_signalements(self, question):
        return question.signalements.count()
