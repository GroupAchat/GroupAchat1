# Tests — pytest + pytest-django, tels que ce dépôt les écrit

## Outils et emplacement
- `pytest` + `pytest-django` ; `backend/pytest.ini` (`DJANGO_SETTINGS_MODULE = config.settings`). Lancer depuis `backend/` : `python -m pytest`.
- `pytest.ini` collecte `tests.py`, `test_*.py` **et** `tests_*.py` — vingt-huit tests avaient dormi parce que le troisième motif manquait. Un nouveau fichier de test doit correspondre à un de ces motifs, et l'agent vérifie qu'il est bien **collecté** (`python -m pytest --collect-only -q <fichier>`).
- Un test qui ne porte que sur un sujet va dans `groupachat/<sujet>/tests.py` ; un test qui en traverse plusieurs va dans `groupachat/tests/test_<theme>.py`.
- Fixtures partagées dans `backend/conftest.py` (`client`, `categorie`, `groupeur`, comptes de test…) : les réutiliser plutôt que recréer des comptes à la main.
- `pytestmark = pytest.mark.django_db` en tête de fichier quand tout le fichier touche la base.

## Écriture
- Classes de test par thème, méthodes nommées en **phrase française** : `test_le_fil_se_lit_sans_compte`, `test_on_ne_repond_pas_a_une_reponse`.
- API testée par `rest_framework.test.APIClient`, avec les vrais parcours de connexion quand c'est eux qu'on teste.
- Vérifier le statut HTTP **et** l'effet : ligne écrite ou non, montant du séquestre, notification créée, champ privé absent.
- Horloge : `django.utils.timezone` avec des dates relatives (`timezone.now() + timedelta(...)`) ; pour un délai (7 jours, J+3, J+14), avancer la date de la donnée ou figer l'heure, jamais attendre.
- Services externes (Cloudinary, SMS) : jamais appelés ; sans variables `CLOUDINARY_*`, le dépôt retombe sur le disque local.

## Durée
La suite complète dure **environ sept minutes** (165 tests). Pendant le travail, lancer les tests du sujet touché (`python -m pytest groupachat/<sujet>/tests.py`) ; la suite entière avant de déclarer terminé.
