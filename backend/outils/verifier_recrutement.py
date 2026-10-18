# -*- coding: utf-8 -*-
"""Vérifie le parcours de recrutement d'un groupeur **sur l'API vivante**.

    .venv/Scripts/python outils/verifier_recrutement.py

Il lance son propre serveur sur un port libre, rejoue le parcours complet —
dépôt, file d'attente, examen, décision, annonce, relecture par le groupeur —
puis s'arrête. Rien à démarrer à la main.

## Pourquoi, alors qu'il y a 107 tests

Parce que les tests ne voient pas tout, et ce script l'a démontré deux fois en
étant écrit :

- le backend de messagerie **console** plantait en ``UnicodeEncodeError`` sur
  l'espace insécable fine de « 150 000 F », parce que la sortie standard de
  Windows est en cp1252. Les tests utilisent un backend en mémoire, qui
  n'encode rien : ils passaient tous ;
- cette panne remontait en **500**, laissant croire à l'administrateur que
  rien n'avait été enregistré — alors que la décision l'était.

Un test vérifie une règle ; ce script vérifie que l'assemblage tourne sur cette
machine, avec cette base, cet encodage et ces réglages.

⚠️ **Il remet la base de démonstration à zéro** (``flush`` puis
``charger_demo``), sans quoi deux exécutions ne donneraient pas le même
résultat. Ne pas le lancer sur une base qui contient autre chose que le jeu de
démonstration.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PYTHON = RACINE / ".venv" / "Scripts" / "python.exe"


def port_libre() -> int:
    """Demande un port au système plutôt que d'en choisir un.

    Un port codé en dur finirait par tomber sur un ``runserver`` oublié, et on
    interrogerait alors un serveur **plus ancien que le code qu'on teste** —
    erreur déjà commise sur ce projet, et parfaitement invisible : les réponses
    ont l'air correctes, elles viennent simplement d'ailleurs.
    """
    with socket.socket() as prise:
        prise.bind(("127.0.0.1", 0))
        return prise.getsockname()[1]


def appeler(
    methode: str, url: str, corps: dict | None = None, jeton: str | None = None
) -> tuple[int, dict]:
    donnees = json.dumps(corps).encode() if corps is not None else None
    requete = urllib.request.Request(url, data=donnees, method=methode)
    requete.add_header("Content-Type", "application/json")
    if jeton:
        requete.add_header("X-Jeton-Admin", jeton)
    try:
        with urllib.request.urlopen(requete, timeout=10) as reponse:
            return reponse.status, json.loads(reponse.read() or b"{}")
    except urllib.error.HTTPError as erreur:
        brut = erreur.read()
        try:
            return erreur.code, json.loads(brut or b"{}")
        except json.JSONDecodeError:
            return erreur.code, {"corps": brut.decode(errors="replace")[:300]}


def attendu(libelle: str, obtenu, voulu) -> None:
    marque = "ok  " if obtenu == voulu else "ÉCHEC"
    print(f"  {marque} {libelle}")
    if obtenu != voulu:
        print(f"        attendu {voulu!r}, obtenu {obtenu!r}")
        global ECHECS
        ECHECS += 1


ECHECS = 0

DOSSIER = {
    "pseudonyme": "Essai Recrutement",
    "nom_complet": "Dela Agbo",
    "telephone": "+22890777888",
    "courriel": "dela@example.tg",
    # Volontairement dans l'autre ordre et en majuscules : la concordance est
    # tolérante sur la forme, stricte sur le fond.
    "titulaire_mobile_money": "AGBO Dela",
    "numero_mobile_money": "+22890777888",
    "pieces": [
        {"nature": "piece-recto", "reference": "coffre/essai/recto"},
        {"nature": "piece-verso", "reference": "coffre/essai/verso"},
        {"nature": "selfie", "reference": "coffre/essai/selfie"},
    ],
}


#: Le compte d'administration que ce script se crée pour travailler.
#:
#: ⚠️ **Ce script lisait `JETON_ADMIN` dans le `.env` de la racine**, et sortait
#: sur « rien à vérifier » quand la variable manquait. Le jeton partagé
#: n'existe plus : l'administration se connecte contre un compte. Le script en
#: crée donc un lui-même plutôt que d'exiger qu'il en existe un — il commence
#: de toute façon par un `flush`, qui vide la table des comptes, donc aucun
#: compte préexistant ne lui survivrait.
#:
#: Le mot de passe est en clair ici, et c'est sans conséquence : il ne vaut que
#: sur une base locale que la ligne suivante vient d'effacer.
VERIFICATEUR = "verificateur-automatique"
MOT_DE_PASSE_VERIFICATEUR = "verification-locale-sans-valeur"


def main() -> int:
    print("Remise à zéro du jeu de démonstration…")
    for commande in (["flush", "--noinput"], ["charger_demo"]):
        subprocess.run(
            [str(PYTHON), "manage.py", *commande],
            cwd=RACINE,
            check=True,
            stdout=subprocess.DEVNULL,
        )

    # ⚠️ **Après le `flush`, jamais avant** : il vide `auth_user`, donc un
    # compte créé plus tôt disparaîtrait sans bruit et le script échouerait à
    # sa première requête d'administration, sur un 401 déroutant.
    subprocess.run(
        [str(PYTHON), "manage.py", "creer_administrateur"],
        cwd=RACINE,
        check=True,
        stdout=subprocess.DEVNULL,
        env={
            **os.environ,
            "ADMIN_IDENTIFIANT": VERIFICATEUR,
            "ADMIN_MOT_DE_PASSE": MOT_DE_PASSE_VERIFICATEUR,
            "ADMIN_NOM": "Verificateur Automatique",
        },
    )

    port = port_libre()
    base = f"http://127.0.0.1:{port}/api"
    print(f"Serveur sur le port {port}…")

    # ⚠️ `DEVNULL` et non `PIPE` : un `pg_ctl` ou un `runserver` lancé avec un
    # tuyau hérite de ce tuyau, et `communicate()` ne rend jamais la main.
    # C'est documenté dans backend/README.md, et ça a déjà bloqué une session.
    serveur = subprocess.Popen(
        [str(PYTHON), "manage.py", "runserver", str(port), "--noreload"],
        cwd=RACINE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        for _ in range(40):
            time.sleep(0.25)
            try:
                if appeler("GET", f"{base}/campagnes/")[0] == 200:
                    break
            except OSError:
                continue
        else:
            print("Le serveur n'a pas répondu.")
            return 1

        # La connexion ne peut avoir lieu qu'ici : c'est une requête HTTP, donc
        # elle a besoin du serveur, qui vient tout juste de répondre.
        code, session = appeler(
            "POST",
            f"{base}/session-admin/connexion/",
            {
                "identifiant": VERIFICATEUR,
                "mot_de_passe": MOT_DE_PASSE_VERIFICATEUR,
            },
        )
        attendu("l'administrateur se connecte", code, 201)
        jeton = session["jeton"]

        print("\n1. Le groupeur dépose son dossier")
        code, depot = appeler("POST", f"{base}/groupeurs/", DOSSIER)
        attendu("le dépôt est accepté", code, 201)
        attendu("il part en vérification", depot.get("etat"), "en-verification")
        attendu(
            "il ne peut rien lancer", depot.get("peut_lancer_une_campagne"), False
        )
        attendu(
            "aucun nom ne revient dans la réponse",
            "nom_complet" in depot,
            False,
        )
        identifiant = depot.get("id")

        print("\n2. Un compte au nom d'un tiers arrête la procédure")
        tiers = dict(DOSSIER, pseudonyme="Prête-nom", telephone="+22890777999")
        tiers["numero_mobile_money"] = "+22890777999"
        tiers["titulaire_mobile_money"] = "Afi Kossi"
        code, erreur = appeler("POST", f"{base}/groupeurs/", tiers)
        attendu("le dépôt est refusé", code, 400)
        attendu(
            "le message dit pourquoi, pas « champ invalide »",
            "acheteurs" in str(erreur),
            True,
        )

        print("\n3. La file d'attente de l'administrateur")
        # ⚠️ **401 et non 403.** C'est « je ne sais pas qui vous êtes », donc
        # l'écran doit rouvrir la feuille de connexion ; `client.ts` s'appuie
        # dessus avec `estNonAuthentifie()`. DRF dégradait ce 401 en 403 faute
        # de classe d'authentification — voir `sessions_admin.SchemaAdmin`.
        code, _ = appeler("GET", f"{base}/dossiers/")
        attendu("fermée sans session", code, 401)
        code, _ = appeler("GET", f"{base}/dossiers/", jeton="faux")
        attendu("fermée avec un mauvais jeton", code, 401)

        code, file = appeler(
            "GET", f"{base}/dossiers/?etat=en-verification", jeton=jeton
        )
        attendu("ouverte avec le bon jeton", code, 200)
        pseudos = [ligne["pseudonyme"] for ligne in file["results"]]
        print(f"        {file['count']} dossiers en attente : {pseudos}")
        attendu(
            "le plus ancien est en tête",
            pseudos[0],
            "Marché Hedzranawoe",
        )
        attendu("le dossier déposé y figure", "Essai Recrutement" in pseudos, True)

        print("\n4. L'administrateur étudie le dossier")
        code, fiche = appeler("GET", f"{base}/dossiers/{identifiant}/", jeton=jeton)
        attendu("la fiche est complète", code, 200)
        attendu("elle porte le nom réel", fiche.get("nom_complet"), "Dela Agbo")
        attendu("les trois pièces sont là", len(fiche.get("pieces", [])), 3)
        attendu("le contrôle n° 2 est visible", fiche.get("concordance_noms"), True)

        print("\n5. Il valide, et le groupeur est prévenu par courriel")
        code, decision = appeler(
            "POST",
            f"{base}/dossiers/{identifiant}/decision/",
            {"issue": "valide", "canal": "courriel"},
            jeton=jeton,
        )
        attendu("la décision passe", code, 200)
        attendu("le courriel est parti", decision.get("annonce"), True)
        attendu(
            "la décision est marquée annoncée",
            decision["decision"]["notifie_le"] is not None,
            True,
        )
        attendu(
            "le plafond est dit dans le message",
            "150" in decision.get("corps", ""),
            True,
        )
        attendu(
            "§1.7 : jamais « bloqué jusqu'à la livraison »",
            "bloqué" in decision.get("corps", ""),
            False,
        )

        print("\n6. Le groupeur relit son dossier")
        code, mien = appeler(
            "GET", f"{base}/groupeurs/dossier/?telephone=%2B22890777888"
        )
        attendu("il le retrouve", code, 200)
        attendu("il est validé", mien.get("etat"), "valide")
        attendu("il peut lancer un groupage", mien.get("peut_lancer_une_campagne"), True)
        attendu("son plafond est de 150 000 F", mien.get("plafond"), 150000)

        print("\n7. Un dossier sans courriel : décision annoncée par appel")
        code, file = appeler(
            "GET", f"{base}/dossiers/?etat=en-verification", jeton=jeton
        )
        sans_courriel = next(
            ligne for ligne in file["results"] if not ligne["courriel"]
        )
        print(f"        dossier retenu : {sans_courriel['pseudonyme']}")
        code, decision = appeler(
            "POST",
            f"{base}/dossiers/{sans_courriel['id']}/decision/",
            {
                "issue": "refuse",
                "motif": "doute-identite",
                "canal": "appel",
            },
            jeton=jeton,
        )
        attendu("la décision passe", code, 200)
        attendu("rien n'est annoncé tout seul", decision.get("annonce"), False)
        attendu(
            "la décision reste à annoncer",
            decision["decision"]["notifie_le"],
            None,
        )
        attendu(
            "le script d'appel est fourni",
            "[Se présenter" in decision.get("script", ""),
            True,
        )
        print("        --- script lu au téléphone ---")
        for ligne in decision["script"].splitlines():
            print(f"        {ligne}")

        print("\n8. Il téléphone, puis l'acte")
        code, actee = appeler(
            "POST",
            f"{base}/dossiers/{sans_courriel['id']}/annonce-faite/",
            {},
            jeton=jeton,
        )
        attendu("l'annonce est actée", actee.get("notifie_le") is not None, True)
        _, deuxieme = appeler(
            "POST",
            f"{base}/dossiers/{sans_courriel['id']}/annonce-faite/",
            {},
            jeton=jeton,
        )
        attendu(
            "un second appui ne réécrit pas la date",
            deuxieme.get("notifie_le"),
            actee.get("notifie_le"),
        )

        print("\n9. Un refus sans motif est refusé")
        code, file = appeler(
            "GET", f"{base}/dossiers/?etat=en-verification", jeton=jeton
        )
        restant = file["results"][0]
        code, erreur = appeler(
            "POST",
            f"{base}/dossiers/{restant['id']}/decision/",
            {"issue": "refuse", "canal": "appel"},
            jeton=jeton,
        )
        attendu("la décision est rejetée", code, 400)
        attendu("et c'est le motif qui manque", "motif" in erreur, True)

        courriels = RACINE / ".courriels"
        nombre = len(list(courriels.glob("*.log"))) if courriels.exists() else 0
        print(f"\nCourriels écrits dans backend/.courriels/ : {nombre}")

    finally:
        serveur.terminate()
        serveur.wait(timeout=10)

    print()
    if ECHECS:
        print(f"{ECHECS} vérification(s) en échec.")
        return 1
    print("Parcours de recrutement vérifié de bout en bout.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
