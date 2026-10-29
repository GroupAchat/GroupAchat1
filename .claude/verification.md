---
# Termes propres à CE projet (nom, domaine, personnes et chiffres de démo, vocabulaire métier).
# Ils ne doivent jamais apparaître dans un agent du kit de vérification : ces agents sont
# communs à tous les projets, et kit-verification.sh refuse de remonter un agent qui en contient.
termes-propres: <Nom du projet>, <domaine-de-production.tld>, <terme métier>
---

# Profil de vérification — <Nom du projet>

Ce fichier est **propre au projet**. Les six agents du kit de vérification (`verificateur`, `testeur-fonctionnel`, `auditeur-securite`, `gardien-regles`, `correcteur`, `relecteur-correction`) le lisent en premier : tout ce qu'ils doivent savoir de ce dépôt est ici, et nulle part dans leur propre texte. Tant qu'il reste des `<…>`, `verificateur` le remplit avec l'utilisateur avant toute autre passe.

## Projet
<Ce que fait le produit, en deux phrases. Organisation du dépôt : un ou plusieurs côtés (serveur, interface), dans quels dossiers, quels frameworks. Langue du code. Branches et qui commite.>

**Les règles non négociables** sont dans `CLAUDE.md`, section « <titre de la section> ». **Hors périmètre de toute correction** : <conventions que le projet ne suit pas et qu'il ne faut pas imposer>.

## Commandes
| Rôle | Commande |
|---|---|
| Préparer l'outillage | `<installer les dépendances sans toucher aux données>` |
| Contrôles rapides | `<lint et types du côté modifié, quelques secondes à une minute>` |
| Contrôles complets | `<ce que fait la CI : suite entière, construction, contrôle de déploiement>` |
| Tests ciblés | `<lancer un module ou un test précis>` |
| Tests affaiblis | `bash .claude/skills/verify/scripts/test-diff.sh` |
| Construction de l'interface | `<commande>` |

<Moteur de base utilisé par les tests, et celui de la CI s'il diffère.>

## API jetable
| | |
|---|---|
| Démarrer | `<commande>` → `<http://127.0.0.1:PORT/>` |
| Mode production | `<commande, ou « aucun »>` |
| Arrêter / repartir de zéro | `<commandes>` |
| Base | `<où vit sa base, séparée de celle de développement>` ; <aucun message réel envoyé : comment> |
| Connexion par rôle | `<comment obtenir une session pour chaque rôle>` |

<Partagée entre agents ? Un seul à la fois ?>

## Interdits
- **Production** : `<domaines>` — aucune requête, aucun scan.
- **Bases** : `<base de développement à ne jamais toucher>`.
- **Scripts destructifs** : `<scripts qui vident une base, à lire mais pas à lancer>`.

## Sources de l'inventaire
- Routes : `<fichiers du routeur>`.
- Écrans : `<dossiers des pages>` ; intention dans `<document, section>`.
- Tâches planifiées et commandes : `<dossier>`.
- Ce que les documents annoncent : `<PRD, cahier des charges…>`.

**Lots** pour le testeur : <un lot par rôle ou par domaine>.

## Chiffres attendus
<Le jeu de démonstration : montants, totaux, identifiants à retrouver au centime dans les réponses de l'API.>

## Parcours à rejouer de bout en bout
- **<Rôle>** : <étape → étape → étape>.

## Surfaces d'attaque prioritaires
- <Ce que l'équipe sait fragile ou non résolu, avec fichier:fonction.>
- <Sessions, administration, argent, données cachées à un rôle, contenus publiés, téléversements, configuration, fichiers de dépendances.>

## Revue de logique — angles prioritaires (analyste)
<Là où la logique porte le plus de risque ou de valeur : cycles de vie et leurs états, calculs d'argent, tâches planifiées, parcours d'inscription, ce qui se passe après un échec ou une annulation. Rappeler les choix déjà justifiés dans CLAUDE.md, qu'on ne propose pas de défaire.>
- <angle> : <fichiers, questions à se poser>.

## Règles à contrôler dans le code (gardien)
| Règle | Où et quoi chercher |
|---|---|
| <règle de CLAUDE.md> | <fichiers, motifs grep, valeurs attendues> |

## Écrire un test de régression
<Framework, emplacement, aides existantes (connexion…), là où il n'y a pas d'outil de test : quelle preuve. Pièges d'édition du projet.>

## Contrat interface ↔ API
<Où sont les appels et les types côté interface ; ce qu'il faut changer ensemble quand une réponse change.>

## Avant une vraie mise en ligne
- <Points connus à confirmer ou infirmer.>
