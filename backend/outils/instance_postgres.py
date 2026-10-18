# -*- coding: utf-8 -*-
"""Monte une instance PostgreSQL 17 de developpement, sur le port 5433.

**Pourquoi une seconde instance plutot que la votre.** Le serveur installe sur
cette machine exige un mot de passe (`scram-sha-256`) et tourne sous un compte
de service : sans les droits administrateur, on ne peut ni creer un role, ni
recharger sa configuration. Plutot que de modifier un serveur auquel je n'ai
pas droit, on en lance un second :

- il utilise **les memes binaires PostgreSQL 17**, donc c'est le vrai moteur de
  production qui execute les tests, pas un approximation ;
- son repertoire de donnees appartient a l'utilisateur courant, dans
  `backend/.pgdata`, ignore par git ;
- il ecoute sur **127.0.0.1:5433** : il ne touche ni au port ni aux donnees du
  serveur installe, qui continue de tourner sans rien savoir de lui ;
- son role a un **mot de passe genere**, pas `trust` : une instance de
  developpement sans authentification est une mauvaise habitude qui finit par
  se retrouver ailleurs.

Pour travailler sur votre serveur a vous, il suffira de changer `DATABASE_URL`
dans le `.env` **de la racine** — rien d'autre dans le code ne depend du port.

⚠️ **Un seul fichier de variables, a la racine**, et c'est `config/settings.py`
qui le decide : il n'en lit pas d'autre. Cet outil ecrivait `backend/.env`,
que plus personne ne lit depuis — la base repondait alors
« password authentication failed » avec un fichier qui portait pourtant le bon
mot de passe, au mauvais endroit.
"""

from __future__ import annotations

import os
import secrets
import shutil
import string
import subprocess
import sys
import time
from pathlib import Path

PG = Path(r"C:\Program Files\PostgreSQL\17\bin")
RACINE = Path(r"C:\ALLPROJECT\Professionnel\GroupAchat\backend")
#: Le `.env` lu par Django, Compose et Vite. **Le seul.**
FICHIER_ENV = RACINE.parent / ".env"
DONNEES = RACINE / ".pgdata"
JOURNAL = RACINE / ".pgdata.log"
PORT = "5433"
ROLE = "groupachat"
BASE = "groupachat"


def executer(programme: str, *args: str, **kwargs) -> subprocess.CompletedProcess:
    # ⚠️ `DEVNULL` et non `PIPE`. Sous Windows, le serveur demarre par
    # `pg_ctl` herite des descripteurs du parent : avec un tube capture,
    # `subprocess.run` attend une fin de flux qui n'arrive jamais et le script
    # se bloque pour toujours, alors meme que le serveur tourne tres bien.
    return subprocess.run(
        [str(PG / programme), *args],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **kwargs,
    )


def serveur_repond(mot_de_passe: str) -> bool:
    environnement = {**os.environ, "PGPASSWORD": mot_de_passe}
    resultat = executer(
        "psql.exe",
        "-h", "127.0.0.1", "-p", PORT, "-U", ROLE, "-d", "postgres",
        "-w", "-c", "SELECT 1",
        env=environnement,
    )
    return resultat.returncode == 0


ENTETE = (
    "# Variables de developpement. Ne pas commiter.\n"
    "# Un seul fichier pour Django, Compose et Vite — voir config/settings.py.\n"
)

GABARIT = (
    "DJANGO_SECRET_KEY=dev-seulement-a-remplacer-en-production\n"
    "DJANGO_DEBUG=1\n"
)


def poser_database_url(url: str) -> None:
    """Remplace la ligne `DATABASE_URL`, **et ne touche a rien d'autre**.

    ⚠️ Cet outil reecrivait le fichier en entier. Tant qu'il visait
    `backend/.env`, qui ne portait que trois variables, c'etait sans
    consequence. Pointe sur le `.env` de la racine, la meme ligne effacerait
    `SMS_FOURNISSEUR`, `CORS_ORIGINES` et les identifiants du
    compte administrateur — c'est-a-dire tout ce qui ne se regenere pas.

    Le mot de passe de l'instance change a chaque remise a neuf : c'est bien
    cette ligne-la, et elle seule, qui doit suivre.
    """
    lignes = (
        FICHIER_ENV.read_text(encoding="utf-8").splitlines(keepends=True)
        if FICHIER_ENV.exists()
        else [ENTETE, GABARIT]
    )

    nouvelle = f"DATABASE_URL={url}\n"
    for rang, ligne in enumerate(lignes):
        if ligne.startswith("DATABASE_URL="):
            lignes[rang] = nouvelle
            break
    else:
        lignes.append(nouvelle)

    FICHIER_ENV.write_text("".join(lignes), encoding="utf-8")


def main() -> int:
    mot_de_passe = "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(24)
    )

    # Une instance deja montee est arretee et refaite : la commande doit
    # pouvoir se relancer sans laisser un etat a moitie construit.
    if DONNEES.exists():
        print("Instance existante — arret et remise a neuf.")
        executer("pg_ctl.exe", "stop", "-D", str(DONNEES), "-m", "fast")
        time.sleep(1)
        shutil.rmtree(DONNEES, ignore_errors=True)

    fichier_mdp = DONNEES.parent / ".pgpass-initdb"
    fichier_mdp.write_text(mot_de_passe, encoding="utf-8")

    try:
        print("initdb…")
        resultat = executer(
            "initdb.exe",
            "-D", str(DONNEES),
            "-U", ROLE,
            "--auth-local=scram-sha-256",
            "--auth-host=scram-sha-256",
            f"--pwfile={fichier_mdp}",
            "-E", "UTF8",
            "--locale=C",
        )
        if resultat.returncode != 0:
            print(resultat.stdout[-2000:], file=sys.stderr)
            print(resultat.stderr[-2000:], file=sys.stderr)
            return 1
    finally:
        # Le mot de passe ne traine pas en clair sur le disque.
        fichier_mdp.unlink(missing_ok=True)

    # Port dedie, et ecoute sur la boucle locale uniquement.
    conf = DONNEES / "postgresql.conf"
    conf.write_text(
        conf.read_text(encoding="utf-8")
        + f"\n# Instance de developpement Group Achat\n"
        f"port = {PORT}\n"
        f"listen_addresses = '127.0.0.1'\n",
        encoding="utf-8",
    )

    print("Demarrage…")
    resultat = executer(
        "pg_ctl.exe", "start", "-D", str(DONNEES), "-l", str(JOURNAL), "-w"
    )
    if resultat.returncode != 0:
        print(resultat.stdout[-2000:], file=sys.stderr)
        print(resultat.stderr[-2000:], file=sys.stderr)
        return 1

    for _ in range(20):
        if serveur_repond(mot_de_passe):
            break
        time.sleep(0.5)
    else:
        print("Le serveur ne repond pas.", file=sys.stderr)
        return 1

    environnement = {**os.environ, "PGPASSWORD": mot_de_passe}
    resultat = executer(
        "createdb.exe",
        "-h", "127.0.0.1", "-p", PORT, "-U", ROLE, "-O", ROLE, "-E", "UTF8",
        BASE,
        env=environnement,
    )
    if resultat.returncode != 0 and "existe" not in resultat.stderr:
        print(resultat.stderr, file=sys.stderr)
        return 1

    url = f"postgres://{ROLE}:{mot_de_passe}@127.0.0.1:{PORT}/{BASE}"
    poser_database_url(url)

    print(f"\nInstance prete : 127.0.0.1:{PORT}, base « {BASE} »")
    print(f"Journal        : {JOURNAL}")
    print(f"{FICHIER_ENV.name:<15}: DATABASE_URL mis a jour (ignore par git)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
