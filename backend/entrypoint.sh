#!/bin/sh
#
# Ce que fait l'API au démarrage, dans l'ordre.
#
# `set -e` : si une migration échoue, le conteneur doit s'arrêter bruyamment.
# Démarrer quand même servirait une application dont le schéma ne correspond
# pas au code — la pire des pannes, parce qu'elle ne se voit qu'à l'usage.
set -e

echo "→ Attente de la base de données…"
# La dépendance Compose attend que PostgreSQL accepte les connexions, mais
# un redémarrage de la base en cours de route remettrait l'API devant une
# porte fermée. On réessaie plutôt que de supposer.
essais=0
until pg_isready --quiet --dbname "${DATABASE_URL}" 2>/dev/null; do
    essais=$((essais + 1))
    if [ "${essais}" -ge 60 ]; then
        echo "✗ La base ne répond pas après 60 tentatives. Abandon." >&2
        exit 1
    fi
    sleep 1
done
echo "  base prête."

echo "→ Migrations…"
python manage.py migrate --noinput

echo "→ Fichiers statiques…"
# Au démarrage et non à la construction : le réglage exige
# DJANGO_SECRET_KEY hors DEBUG, et ce secret n'existe qu'à l'exécution.
python manage.py collectstatic --noinput --clear >/dev/null
echo "  collectés."

# ── Compte administrateur ───────────────────────────────────────────────────
#
# Django lit `DJANGO_SUPERUSER_<CHAMP>` d'après le champ d'identification, qui
# est ici `telephone`. Le fichier Compose, lui, parle de
# `DJANGO_SUPERUSER_USERNAME` par habitude : on traduit, plutôt que de laisser
# une variable renseignée rester sans effet.
if [ -n "${DJANGO_SUPERUSER_USERNAME}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD}" ]; then
    export DJANGO_SUPERUSER_TELEPHONE="${DJANGO_SUPERUSER_USERNAME}"
    export DJANGO_SUPERUSER_NOM="${DJANGO_SUPERUSER_NOM:-Équipe}"
    export DJANGO_SUPERUSER_PRENOM="${DJANGO_SUPERUSER_PRENOM:-Group Achat}"
    echo "→ Compte administrateur ${DJANGO_SUPERUSER_TELEPHONE}…"
    # `|| true` : au second démarrage le compte existe déjà, et c'est normal.
    python manage.py createsuperuser --noinput 2>/dev/null \
        && echo "  créé." \
        || echo "  déjà présent."
fi

# ── Jeu de démonstration ────────────────────────────────────────────────────
#
# `charger_demo` s'arrête de lui-même si des campagnes existent déjà : un
# redéploiement ne duplique donc rien.
if [ "${CHARGER_DEMO}" = "1" ]; then
    echo "→ Jeu de démonstration…"
    python manage.py charger_demo
fi

echo "→ Gunicorn sur le port 8000."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_PROCESSUS:-3}" \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
