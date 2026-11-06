# Group Achat — Spécification fonctionnelle v2

> **Version** 0.1 — 6 novembre 2026
> **Statut** Proposition de travail, à valider avant développement.
> **Source** `Cahier_de_Charge.docx` (novembre 2026), complété par les décisions du fondateur et par l'état du dépôt au 6 novembre 2026.
> **Remplace à terme** `CAHIER_DES_CHARGES.md` (v1). Le v1 reste la référence historique jusqu'à validation de ce document.
> **Périmètre** Règles métier, fonctionnalités, modèle de données, écrans, matrice des écarts et plan de mise en œuvre. Ce document ne modifie aucun fichier de code.

---

## 0. Comment lire ce document

### 0.1 Statut de réalité

Le nouveau cahier des charges décrit une cible ambitieuse. Plusieurs de ses briques ne peuvent pas être présentées comme opérationnelles tant que les partenaires ne sont pas signés. La règle est simple : **on modélise, on affiche un statut, on ne promet pas.**

| Élément | État réel aujourd'hui | Ce que l'interface peut dire | Ce qu'elle ne doit pas dire |
|---|---|---|---|
| Paiement Mobile Money | Simulé (`Transaction.simulee=True`, `_executer_paiement`) | « Paiement simulé — mode démonstration » | « Paiement sécurisé », « argent encaissé » |
| SMS / OTP | Simulé (passerelle qui journalise, code affiché en prototype) | « Code de démonstration » | « SMS envoyé » sans réserve |
| Assurance Tout Risques | Modèle, aucune police active | « Assurance prévue — partenariat en cours » | « Vos achats sont assurés » |
| Contrat OAG certifié | Modèle, certification non effectuée | « Contrat en cours de certification » | « Contrat notarié signé » |
| Partenaires logistiques | Pistes (La Poste, Gozem), pas de convention | « Partenaire prévu » | « Livraison garantie par La Poste » |
| Prestataire de paiement | Non intégré | « Prestataire en cours de sélection » | « Fonds détenus par un établissement agréé » |
| IPDCP | Démarche à engager | « Conformité en cours » | « Déclaré à l'IPDCP » |
| Données de démonstration | Fictives | « Données de démonstration » | « Clients réels » |

**Règle de communication.** Aucun écran ne peut afficher « assuré », « certifié par notaire », « paiement sécurisé » ou « SMS envoyé » si le partenaire correspondant n'est pas signé et si le statut en base ne le confirme pas. Le mot **« garantie »** peut désigner un engagement commercial de la plateforme ; le mot **« assurance »** est réservé à une police réellement souscrite auprès d'un assureur habilité.

### 0.2 Priorités

| Priorité | Signification |
|---|---|
| **P0** | Bloquant pour le pilote ou pour la crédibilité de la promesse. |
| **P1** | Nécessaire avant l'ouverture publique. |
| **P2** | Après le pilote, quand le volume le justifie. |

### 0.3 Ce que ce document ne fait pas

- Il ne remplace pas un avis juridique, un contrat notarié, une police d'assurance ou une autorisation réglementaire.
- Il ne tranche pas les points marqués **« À trancher »**. Il propose une recommandation et indique ce qui bloque.
- Il ne renomme pas les modèles techniques `Campagne` et `groupeur` : le changement serait vaste et risqué pour un gain surtout cosmétique. L'interface, elle, parle d'**Offre d'achat** et d'**OAG**.

---

## 1. Décisions

### 1.1 Décisions validées

| ID | Sujet | Décision | Conséquence |
|---|---|---|---|
| **D-01** | Barème des points | Achat payé 5 pts, parrainage 2 pts, Contact Privé 10 pts. Les points de groupage abouti sont supprimés. | Le barème de `comptes/points.py` change ; les tests de points et de clôture changent. |
| **D-02** | Droit de publier | On conserve l'abonnement 2 000 FCFA/mois illimité et le pack 500 FCFA/5 publications. Le ticket 100 FCFA/10 créations n'est pas retenu. | `catalogue/publication.py` reste la référence ; les points de publication restent 10/mois et 2/pack. |
| **D-03** | Identité des OAG | Profil vérifié avec **coordonnées masquées** : nom public ou enseigne, badge « Identité vérifiée », jamais de téléphone ni d'adresse publics. Le Contact Privé ouvre la **messagerie interne**, pas les coordonnées. | Le code qui révèle `nom_complet` et `telephone` à l'abonné doit être retiré. |
| **D-04** | Réclamations | Module complet : dossier, preuves, contradictoire, délais, escalade, remboursement, décision motivée. La règle « la plateforme n'arbitre pas » est supprimée. | Nouveau domaine `reclamations` ; l'avis ne remplace plus la procédure. |
| **D-05** | Prochaine étape | Spécification et plan d'abord, code ensuite. | Ce document. |

### 1.2 Décisions dérivées, à confirmer

| ID | Sujet | Recommandation | Pourquoi |
|---|---|---|---|
| **D-06** | Seuils de grade | Quatre paliers : **Nouveau 0–249** (4 %), **Bronze 250–399** (4 %), **Argent 400–599** (3 %), **Or 600+** (2 %). | Le document fixe Bronze à 250 ; il faut un état avant Bronze, sinon un OAG qui débute n'a aucun grade. La commission de Nouveau et de Bronze est identique, donc personne n'est pénalisé. |
| **D-07** | Contact Privé | 2 000 FCFA/mois ; **50 points cumulés minimum** pour souscrire ; 10 points après paiement. Le seuil est une **condition d'accès**, pas une dépense. | Le document parle de « 50 points minimum » ; les points cumulés ne descendent jamais, donc l'accès reste stable. |
| **D-08** | Réduction livraison | 100 points cumulés, **50 % sur une livraison éligible, une fois par compte**. Mécanisme à trancher. | Le document fixe le seuil ; il ne dit pas qui porte les 50 %. La plateforme n'encaisse pas les frais de livraison. |
| **D-09** | OTP | **Deux codes distincts** : un OTP de validation d'achat (consommé au paiement) et un OTP de secours à la remise (généré à la demande). | Un code consommé à l'achat ne peut pas servir à la remise ; un code envoyé à l'achat peut expirer avant la livraison. |
| **D-10** | Commission | Assiette : montant total collecté. Taux figé au calcul. Exigible au décaissement. Remboursement avant décaissement : pas de commission. Après décaissement : commission acquise, remboursement sur fonds de garantie ou recouvrement, décision journalisée. | Le document demande de préciser le moment d'exigibilité et le traitement des remboursements. |
| **D-11** | Assurance et contrat | Modèles et statuts, aucune couverture active par défaut. Le contrat n'est « certifié » qu'au statut `CERTIFIE`. L'acceptation en ligne est enregistrée, mais présentée comme « signature électronique en cours de validation juridique » tant que le juriste n'a pas confirmé. | On ne peut pas promettre une couverture ou une certification qui n'existe pas. |
| **D-12** | Administration | Rôles internes séparés, double validation des opérations sensibles, journal d'audit append-only. | Le code actuel n'a qu'un drapeau `est_equipe` et aucune trace d'audit. |
| **D-13** | Données personnelles | Droits d'accès, rectification, opposition, suppression ; durées de conservation par catégorie ; démarche IPDCP. | Le code protège le KYC mais n'a ni consentement, ni export, ni effacement, ni durées. |
| **D-14** | Médias | Article : **3 images + 1 vidéo maximum**. Photos du lot réel : **3 photos maximum**, sans vidéo. | Le code autorise 2 vidéos et 5 photos de campagne. |
| **D-15** | Terminologie | Interface : **Offre d'achat** côté OAG, **Club d'achat** côté acheteur, **OAG** partout. Technique : `Campagne` et `groupeur` conservés. | Un renommage complet des modèles coûterait des migrations et des tests pour un gain nul côté utilisateur. |
| **D-16** | Réalité des promesses | Paiement, SMS, assurance, contrat notarié et partenaires restent simulés ou au statut « modèle » tant qu'ils ne sont pas signés. | Voir le tableau 0.1. |

### 1.3 Les trois contradictions à garder en tête

**1. Le grade ne mesure plus la fiabilité si le groupage abouti ne rapporte rien.**
Avec le barème strict, un OAG gagne 10 points par mois d'abonnement et 2 points par pack, une seule fois. Pour atteindre Bronze (250), il faudrait 25 mois d'abonnement ou 125 packs. Pour atteindre Or (600), 60 mois. Ce n'est pas un grade de fiabilité, c'est un compteur d'ancienneté. Deux corrections possibles, à trancher :

- **Option A (recommandée)** : le grade est atteint par les points **ou** par un nombre d'Offres d'achat terminées — par exemple 5 pour Bronze, 15 pour Argent, 30 pour Or. Le barème des points reste strict, mais la fiabilité opérationnelle compte.
- **Option B** : rétablir des points par groupage abouti, par exemple 10 points, comme dans la v1. Cela contredit la décision D-01 mais rend le grade atteignable.

Tant que ce point n'est pas tranché, **la Phase 1 ne doit pas être considérée comme terminée**.

**2. Le Contact Privé à 50 points ferme la porte au nouvel acheteur.**
C'est voulu par le document : le Contact Privé devient un avantage de fidélité, pas un droit d'entrée. Il faut l'assumer dans l'interface : « Disponible à partir de 50 points — vous en avez X ». Un acheteur qui n'a encore rien acheté ne peut pas écrire à un OAG ; il peut consulter, acheter et laisser un avis.

**3. La réduction de livraison coûte de l'argent réel.**
La plateforme n'encaisse pas les frais de livraison. Accorder 50 % sur une livraison, c'est soit rembourser l'agence, soit lui demander de renoncer à sa marge. Le mécanisme doit être négocié avant d'être codé. En attendant, l'avantage peut être affiché comme « en préparation », jamais comme disponible.

---

## 2. Glossaire et terminologie

| Terme | Définition | Usage interface | Usage code |
|---|---|---|---|
| **OAG** | Organisateur d'achat groupé. Remplace « OA » et « groupeur ». | Partout. | `groupeur` conservé dans les modèles et les routes existantes. |
| **Offre d'achat** | Ce que lance l'OAG : un produit, un prix, un minimum, une date limite. | Espace OAG, fiche côté OAG. | `Campagne`. |
| **Club d'achat** | La même réalité vue par l'acheteur. | Boutique, fiche côté acheteur. | `Campagne`. |
| **Participation** | La part d'un acheteur dans une Offre d'achat. | « Ma participation ». | `Participation`. |
| **Séquestre** | Comptabilité des fonds d'une Offre d'achat, par campagne. Ce n'est **pas** un compte bancaire. | « Fonds consignés ». | `Sequestre`. |
| **Grade** | Niveau de l'OAG : Nouveau, Bronze, Argent, Or. Il détermine la commission et l'autonomie de publication. | Badge et espace OAG. | `Grade`, `SEUILS`, `COMMISSIONS_CENTIEMES`. |
| **Badge** | Mention publique liée à des critères publiés : « Identité vérifiée », « OAG expérimenté », « OAG recommandé ». | Fiche OAG. | Nouveau `Badge`, `BadgeOAG`. |
| **KYC** | Vérification de l'identité et de l'activité de l'OAG. | « Dossier OAG ». | `DossierKYC`, à étendre. |
| **Réclamation** | Dossier d'incident ouvert par un acheteur ou un OAG. | « Réclamation ». | Nouveau `DossierReclamation`. |
| **Remboursement** | Restitution d'un montant à un acheteur, avec preuve et statut. | « Remboursement ». | Nouveau `Remboursement`. |
| **Police** | Assurance Tout Risques unique par Offre d'achat. | « Assurance prévue / active ». | Nouveau `PoliceAssurance`. |
| **Contrat OAG** | Contrat-cadre, à certifier par notaire. | « Contrat OAG ». | Nouveau `ContratOAG`. |
| **Jeton QR** | Jeton unique et révocable contenu dans le QR code de remise. | « QR de retrait ». | À durcir à partir de `code_retrait`. |
| **OTP** | Code à usage unique envoyé par SMS. | « Code de secours ». | Nouveau `CodeOTP`. |
| **Points cumulés** | Total de la vie du compte, qui ne descend jamais. Il décide du grade et de l'éligibilité au Contact Privé. | « Points cumulés ». | `CompteurPoints.cumules`. |
| **Solde de points** | Points disponibles pour une dépense. | « Solde ». | `CompteurPoints.solde`. |
| **Contact Privé** | Abonnement mensuel qui ouvre la messagerie interne avec les OAG. | « Contact Privé ». | `AbonnementContactPrive`. |

**Règle de rédaction.** Dans l'interface et les messages, on écrit « OAG », jamais « groupeur » ni « OA ». Dans le code, on garde les noms existants pour ne pas casser les migrations, les routes et les tests. Les `verbose_name` et les libellés peuvent être changés sans migration.

---

## 3. Promesse, limites et responsabilités

### 3.1 Promesse aux acheteurs

- Consulter les Offres d'achat et leurs conditions avant de s'engager.
- Identifier les OAG dont le profil a été vérifié, avec un badge et des critères publiés.
- Disposer d'une trace de paiement et d'un historique de commande.
- Suivre les étapes du Club d'achat et de la livraison.
- Présenter un QR code unique comme preuve de remise, complété par un code OTP de secours.
- Bénéficier de l'Assurance Tout Risques **lorsqu'une police est active** ; sinon, voir clairement que le partenariat est en cours.
- Déposer une réclamation selon une procédure connue, avec des délais affichés.
- Comprendre quelles données sont collectées, qui peut y accéder, et comment exercer ses droits.

### 3.2 Promesse aux OAG

- Lancer des Offres d'achat auprès d'une clientèle élargie.
- Suivre les participations, paiements et livraisons.
- Connaître les règles à l'avance : commission, grade, publication, réclamation.
- Développer une réputation fondée sur des indicateurs vérifiables.
- Accéder à des avantages selon le grade et la fiabilité.
- Disposer d'un support en cas de difficulté opérationnelle.
- Voir chaque Offre d'achat couverte par l'Assurance Tout Risques **lorsqu'elle est active**.
- Disposer d'un historique d'activité exportable, utilisable comme justificatif auprès d'une banque, avec son consentement.
- Exercer dans un cadre contractuel sécurisé, dont le contrat OAG certifié par notaire est la cible.

### 3.3 Limites à annoncer

La plateforme garantit **l'enregistrement des opérations qu'elle contrôle, l'application de ses procédures et la traçabilité des événements**. Elle ne garantit pas :

- la qualité de tout produit ;
- la conformité de tout produit à l'attente de l'acheteur ;
- la disponibilité d'un fournisseur ;
- l'absence absolue de fraude ;
- une couverture d'assurance qui n'est pas souscrite.

### 3.4 Répartition des responsabilités

| Acteur | Ce dont il répond | Ce qu'il ne porte pas |
|---|---|---|
| **OAG** | Exactitude de l'Offre d'achat, existence de la marchandise ou du fournisseur, délais annoncés, remise contre preuve. | La qualité du transport, la solvabilité de l'acheteur, les pannes de la plateforme. |
| **Transporteur / agence** | Livraison, point relais, preuve de remise, respect du niveau de service. | Le prix de l'article, la conformité du produit. |
| **Prestataire de paiement** | Encaissement, confirmation, remboursement, rapprochement. | La qualité du produit, la relation commerciale. |
| **Innov'elles / Group Achat** | Plateforme, procédures, traçabilité, séquestre selon le statut juridique retenu, réclamation, données. | La qualité du produit, la disponibilité du fournisseur, les engagements pris hors plateforme. |

**Conséquence.** Une transaction conclue hors de la plateforme n'ouvre ni le séquestre, ni l'assurance, ni la procédure de réclamation. L'interface doit le dire à l'endroit où l'acheteur serait tenté de contourner le paiement.

---

## 4. Règles métier cibles

### 4.1 Comptes, rôles et identité

**Un compte unique, plusieurs rôles.** Un compte peut être acheteur, OAG, livreur partenaire ou administrateur. Le téléphone reste l'identifiant, normalisé à huit chiffres. La vérification du numéro est obligatoire avant de commander, de publier ou de souscrire au Contact Privé.

**Identité publique de l'OAG.**
- Nom public : nom d'utilisateur ou enseigne déclarée.
- Badge « Identité vérifiée » si le KYC est validé, le contrat accepté et le téléphone vérifié.
- Jamais de téléphone, d'adresse e-mail ou d'adresse postale dans une réponse publique.
- Le nom civil et les pièces justificatives restent réservés à l'intéressé, à l'équipe habilitée et aux autorités compétentes.
- Le Contact Privé ouvre une messagerie interne ; il ne transmet pas le numéro de téléphone. Si l'acheteur et l'OAG veulent échanger hors plateforme, c'est à leurs risques et hors garantie.

**Ce que voit l'acheteur avant paiement.** Le nom public de l'OAG, son badge, son grade éventuel, ses indicateurs publics (note, offres terminées, taux de livraison), la description de l'Offre d'achat, les photos, le prix, les frais, le minimum, la date limite, les conséquences si le minimum n'est pas atteint, le délai, les options de livraison, les conditions de remboursement et de réclamation, et le statut de l'assurance.

**Ce que voit l'OAG.** Les participations, les quantités, les montants, les modes de retrait et les références internes. Il ne voit **jamais** l'adresse de livraison ni le téléphone de l'acheteur. Le partenaire logistique reçoit le strict nécessaire à la remise.

### 4.2 Parcours OAG et contrats

#### 4.2.1 Trois profils

| Profil | Description | Vérifications |
|---|---|---|
| **OAG commerçant** | Boutique ou vendeur professionnel. | Existence de l'activité, adresse professionnelle, justificatifs, références. |
| **OAG individuel** | Particulier qui organise des Offres d'achat. | Identité, coordonnées, expérience, références disponibles. |
| **OAG partenaire** | Organisation ou entreprise. | Existence juridique, représentant habilité, capacité opérationnelle. |

Le profil et le grade sont deux axes distincts. Le profil est fixé à l'entrée et commande la surveillance ; le grade se gagne et commande la commission et l'autonomie de publication.

#### 4.2.2 Parcours de validation en six étapes

| # | Étape | Ce qui se passe | Trace dans la plateforme |
|---|---|---|---|
| 1 | **Candidature** | Formulaire : identité, téléphone, localisation, type d'activité, catégories, expérience, références. | `DossierKYC` au statut `CANDIDATURE`. |
| 2 | **Vérification** | Contrôle des documents et de leur cohérence. On ne conserve que le nécessaire. | Pièces, statut `VERIFICATION`, commentaire. |
| 3 | **Entretien** | Compréhension du modèle, capacité à gérer les commandes, acceptation des règles. | Compte rendu, date, acteur, verdict. |
| 4 | **Formation** | Publications, paiements, délais, remboursements, livraison, confidentialité, réclamations. | `formation_validee_le`, support de formation, version. |
| 5 | **Signature** | Acceptation des conditions, qui vaut signature du contrat OAG, et de la charte de conduite. | `ContratOAG`, `CharteOAG`, version et date. |
| 6 | **Observation** | Accompagnement des premières Offres d'achat, revue après les premières opérations. | `observation_fin_le`, nombre d'offres suivies, décision. |

**Statuts du dossier.** `CANDIDATURE`, `VERIFICATION`, `ENTRETIEN`, `FORMATION`, `SIGNATURE`, `OBSERVATION`, `VALIDE`, `REJETE`, `SUSPENDU`. Le statut `VALIDE` déclenche l'accès à l'espace OAG. Un refus est motivé et peut être retenté si le motif est corrigeable.

**Pièces demandées.** CNI, passeport ou carte consulaire ; numéro Mobile Money ; pour un commerçant, RCCM ou NIF et adresse du local ; pour un partenaire, existence juridique et représentant habilité. Les pièces ne sont **jamais** servies publiquement et ne partent pas chez Cloudinary.

#### 4.2.3 Contrat OAG et charte

- **Contrat OAG** : version, date, signataire, référence notaire, statut (`MODELE`, `ACCEPTE_EN_LIGNE`, `SIGNE`, `CERTIFIE`, `RESILIE`), document.
- **Charte OAG** : transparence, exactitude, respect, pratiques commerciales interdites, version et date d'acceptation.
- L'acceptation en ligne est enregistrée avec la version du texte et l'horodatage. Elle n'est présentée comme « signature du contrat certifié » que si le statut est `CERTIFIE`.
- Le contrat couvre : objet, exactitude, prix et frais, commandes et délais, fonds et prestataire, données, réclamations, suspension, responsabilité, fin de la relation.

#### 4.2.4 Suspension et refus

- **Documents à corriger** : le dossier revient au candidat avec la liste de ce qui manque.
- **Refus** : motif enregistré, evenement conservé.
- **Suspension** : mesures conservatoires, traitement des Offres d'achat en cours, droit de réponse, recours.
- Toute suspension est journalisée et validée par une personne différente de celle qui a validé le dossier, si possible.

### 4.3 Offre d'achat, Club d'achat et catalogue

#### 4.3.1 Structure

- Une **Offre d'achat** porte sur **un seul article**.
- Le **produit** décrit la référence ; l'**Offre d'achat** décrit les conditions : prix, minimum, date limite, paliers, photos du lot.
- Deux OAG peuvent proposer le même produit à deux prix : l'acheteur compare.
- Le catalogue est consultable sans authentification. L'authentification est obligatoire au moment de payer, et n'est pas redemandée à un acheteur déjà connecté.

#### 4.3.2 Médias

| Média | Plafond cible | Règle |
|---|---:|---|
| Photos de l'article | **3** | Images de la référence produit. |
| Vidéo de l'article | **1** | Facultative. Une seule. |
| Photos du lot réel | **3** | Preuves de l'existence de la marchandise, sans vidéo, dans un bloc distinct. |

Le plafond de 3 images + 1 vidéo est celui de l'article. Les photos du lot réel ne le remplacent pas : elles prouvent que la marchandise existe. Le code actuel autorise 3 images + 2 vidéos et 5 photos de campagne ; les deux plafonds doivent être corrigés.

#### 4.3.3 Informations visibles avant paiement

La fiche doit afficher, sans dépliage excessif :

- le profil public de l'OAG et son badge ;
- la description, les photos, les caractéristiques connues ;
- le prix de participation, la quantité, les frais additionnels ;
- le minimum requis, la date limite, ce qui se passe si le minimum n'est pas atteint ;
- le délai estimé et les options de livraison ;
- les conditions de remboursement, de réclamation et de traitement des produits non conformes ;
- le rôle de la plateforme et les limites de ses garanties ;
- le statut de l'assurance : « prévue », « active » ou « non disponible ».

#### 4.3.4 Mise en avant

La mise en avant est un service distinct du droit de publier. Elle est **signalée comme telle** sur la fiche : l'acheteur ne doit pas lire « premier du catalogue » comme « le plus fiable ». Son tarif et son mode d'obtention restent à définir : achat, points, ou inclusion dans l'abonnement. Tant que ce n'est pas tranché, elle n'est pas développée.

### 4.4 Participation, paiement, séquestre et commission

#### 4.4.1 Participation

- L'acheteur choisit la quantité et le mode de retrait : bureau de poste ou livraison à domicile.
- Le prix unitaire est **figé à la commande** ; un palier franchi plus tard ne change pas ce qui a été payé.
- Le montant total, les frais et la destination sont récapitulés avant paiement.
- Une participation payée ne s'annule pas à la seule demande de l'acheteur, sous réserve des droits impératifs des consommateurs et des cas de remboursement prévus.
- L'adresse de livraison n'est jamais servie à l'OAG.

#### 4.4.2 Paiement

- Le paiement est simulé tant que le prestataire n'est pas intégré. La comptabilité du séquestre est tenue pour de vrai.
- La transaction porte : montant, opérateur, référence, statut, horodatage, `simulee`.
- Une notification de paiement n'est acceptée que si elle est signée par le prestataire, idempotente et vérifiée côté serveur. En mode prototype, l'action de l'interface fait avancer l'état.
- Après confirmation : la participation passe à `PAYEE`, le QR est généré, l'OTP d'achat est envoyé, les points d'achat sont attribués.

#### 4.4.3 Séquestre et commission

- Un séquestre par Offre d'achat. Il ne libère jamais plus qu'il n'a consigné.
- La commission est prélevée sur le **montant total collecté**, au moment du décaissement.
- Taux : **4 % Nouveau/Bronze, 3 % Argent, 2 % Or**.
- Le taux et le grade sont **figés** dans le décaissement.
- Un remboursement avant décaissement réduit le séquestre et annule la commission correspondante.
- Un remboursement après décaissement ne rembourse pas automatiquement la commission : il est traité par le fonds de garantie ou par recouvrement, avec décision de la direction et journal d'audit.
- Le vocabulaire de l'interface doit être prudent : « solde d'opération », « solde bloqué », « solde retirable », « bénéfice estimé », « commissions ». Jamais « compte bancaire ».

#### 4.4.4 Double validation

| Opération | Seuil recommandé | Règle |
|---|---:|---|
| Décaissement vers un OAG | 500 000 FCFA | Deux validateurs distincts, dont aucun n'est le demandeur. |
| Remboursement | 100 000 FCFA | Deux validateurs distincts, dont aucun n'est le demandeur. |
| Correction de points | Tout montant | Motif obligatoire, journal d'audit, validation par un rôle finance ou conformité. |

Les seuils sont des paramètres, pas des constantes codées en dur. Ils doivent être validés par la direction et le juriste.

### 4.5 Remise et livraison

#### 4.5.1 Preuve de remise

- Le QR code est généré après confirmation du paiement. Il contient un **jeton imprévisible**, lié à la participation et à l'Offre d'achat, avec un statut (`ACTIF`, `UTILISE`, `REVOQUE`, `EXPIRE`).
- Le scan est fait par le **livreur partenaire**, jamais par l'OAG. L'OAG remet le lot en bloc à l'agence et ne rencontre pas les acheteurs.
- Le scan vérifie côté serveur : la campagne, la participation, le statut, l'unicité et l'absence de révocation. Il journalise l'acteur, le lieu, l'heure et le résultat.
- Le scan confirme la remise et clôture opérationnellement la participation. Il **ne déclenche pas automatiquement** le retrait de l'OAG.

#### 4.5.2 OTP de secours

- Si le QR ne fonctionne pas, l'acheteur demande un **OTP de remise** : 6 chiffres, durée de vie courte (10 minutes recommandées), 3 tentatives, usage unique, renvoi limité.
- L'OTP est haché en base, jamais affiché publiquement, jamais journalisé en clair.
- L'OTP d'achat est distinct : il est envoyé au moment du paiement, valable 10 minutes, 3 tentatives, consommé à la confirmation. Il prouve que l'acheteur possède le numéro.
- Un OTP utilisé, expiré ou révoqué ne peut plus servir. Toute tentative échouée est journalisée.

#### 4.5.3 Livraison

- L'acheteur choisit le bureau de poste ou la livraison à domicile, part par part.
- Les frais de livraison sont fixés par l'agence et réglés à la remise ; la plateforme ne les encaisse pas.
- Le partenaire logistique reçoit l'adresse et le téléphone strictement nécessaires à la remise.
- Un colis non retiré dans un délai défini (14 jours recommandés) est traité selon la procédure : relance, retour, remboursement ou décision de l'OAG. Le délai et le sort du colis doivent être écrits dans les CGV.
- Les indicateurs « livraison à temps » et « taux de livraison » sont calculés à partir des dates de mise à disposition, de remise et des incidents.

#### 4.5.4 Réduction de livraison

- Seuil : **100 points cumulés**.
- Avantage : **50 % sur une livraison éligible, une fois par compte**.
- L'avantage ne réduit pas le prix de l'article.
- Mécanisme à trancher :
  - **Option A (recommandée)** : bon nominatif à usage unique, présenté à l'agence partenaire ; la plateforme rembourse l'agence sur justificatif, dans une limite plafonnée.
  - **Option B** : remise accordée par l'agence dans le cadre du partenariat, sans remboursement de la plateforme.
  - **Option C** : avoir crédité sur le compte de l'acheteur, utilisable sur une prochaine livraison, si le partenaire l'accepte.
- Tant que le partenaire n'est pas signé, l'avantage est affiché comme « en préparation » et n'est pas consommable.

### 4.6 Contact Privé

- Prix : **2 000 FCFA par mois**, 30 jours.
- Condition : **50 points cumulés minimum**. C'est un seuil d'éligibilité, pas une dépense. Les points cumulés ne descendent jamais ; l'acheteur qui a atteint 50 points reste éligible.
- Récompense : **10 points** après paiement, une fois par mois payé.
- Renouveler avant l'échéance ajoute 30 jours à ceux qui restent.
- Ouvre la **messagerie interne avec tous les OAG**. L'OAG répond sans abonnement.
- **Ne révèle ni le téléphone ni l'adresse** de l'OAG. Le nom public et le badge suffisent.
- Aucune discussion publique sous une Offre d'achat. Les échanges hors plateforme échappent au séquestre, à l'assurance et à la réclamation.
- Un abonné dont le mois s'achève garde l'historique de ses messages ; il perd le droit d'écrire et l'accès au Contact Privé.
- Les messages signalés sont masqués, jamais supprimés sans trace. La modération journalise le motif.

### 4.7 Points, grades et droit de publier

#### 4.7.1 Barème

| Action | Bénéficiaire | Points | Condition |
|---|---|---:|---|
| Achat payé | Acheteur | **5** | Paiement confirmé, une attribution par participation. |
| Parrainage validé | Parrain | **2** | Le filleul rejoint un Club d'achat et paie ; clic ou inscription seuls exclus. |
| Contact Privé payé | Acheteur | **10** | Abonnement payé et activé, une fois par mois. |
| Groupage abouti | OAG | **0** | Décision D-01 ; conséquence à rouvrir (P-02). |
| Abonnement publication | OAG | **10** | Un mois payé, une fois par mois. Conservé par D-02. |
| Pack publication | OAG | **2** | Une seule fois par compte, conservé par D-02. |
| Ticket publication | OAG | **Non retenu** | Le ticket 100 FCFA/10 n'est pas appliqué. |

**Deux compteurs.** `cumules` ne descend jamais et décide du grade et de l'éligibilité au Contact Privé. `solde` monte aux mêmes occasions et baisse à chaque dépense. Dépenser ne fait pas perdre son grade.

**Idempotence.** Une même opération ne peut pas attribuer deux fois les mêmes points. L'attribution porte l'événement d'origine et une contrainte d'unicité en base.

**Anti-fraude.** Détecter l'auto-parrainage, les comptes artificiels, les transactions annulées, les participations entre comptes liés. Publier les règles de suspension ou de retrait des points.

#### 4.7.2 Grades

| Palier | Points cumulés | Commission | Badge affiché |
|---|---:|---:|---|
| **Nouveau** | 0–249 | 4 % | « Nouveau » (pas de badge Bronze) |
| **Bronze** | 250–399 | 4 % | Bronze |
| **Argent** | 400–599 | 3 % | Argent |
| **Or** | 600+ | 2 % | Or |

Le niveau Nouveau est l'état d'observation avant Bronze. La commission est la même que Bronze, donc aucun OAG n'est financièrement pénalisé. Si l'option A de la section 1.3 est retenue, le grade peut aussi être atteint par un nombre d'Offres d'achat terminées.

**Rétrogradation.** Les règles de perte de grade ne sont pas définies. Tant qu'elles ne le sont pas, un grade obtenu est conservé. À trancher avant l'ouverture publique.

#### 4.7.3 Droit de publier

| Formule | Prix | Publications | Points |
|---|---:|---|---:|
| **Abonnement publication** | 2 000 FCFA/mois | illimitées | 10 points par mois payé |
| **Pack** | 500 FCFA | 5 | 2 points, une seule fois |

- Les deux compteurs sont indépendants. Un abonnement qui s'achève ne prend pas les publications déjà payées.
- Une publication se consomme **à la mise en ligne**, jamais à la création du brouillon.
- Une publication n'est pas rendue si l'Offre d'achat échoue : elle paie la mise en ligne, pas la réussite.
- Un refus de l'équipe rend la publication : la mise en ligne n'a pas eu lieu.
- Le ticket 100 FCFA/10 du nouveau document n'est pas retenu. Le modèle économique de la section 12 du document source est donc partiellement appliqué : commission 4/3/2 et Contact Privé 2 000 sont retenus, ticket non.

#### 4.7.4 Mise en avant

La mise en avant reste à définir. Elle doit être signalée sur la fiche et ne peut pas être confondue avec un classement de fiabilité. Elle peut être achetée, payée en points ou incluse dans l'abonnement ; le choix doit être tranché avant développement.

### 4.8 Réclamations, conflits et remboursements

#### 4.8.1 Principe

**La plateforme n'arbitre plus au sens de « elle ne fait rien ».** Elle instruit les réclamations, examine les preuves, organise le contradictoire et rend une décision motivée. Elle ne garantit pas la qualité du produit, mais elle peut ordonner une correction, un remplacement ou un remboursement dans les cas prévus.

La phrase de l'ancien cahier des charges — « Group Achat met en relation, elle n'arbitre pas » — est **supprimée**. Elle est remplacée par : « Group Achat instruit les réclamations selon une procédure connue ; elle ne garantit pas la qualité du produit, mais elle examine la conformité de l'opération et peut ordonner un remboursement dans les cas prévus. »

#### 4.8.2 Typologie des incidents

| Incident | Exemple | Première mesure |
|---|---|---|
| **Non-livraison** | Commande payée mais non remise. | Ouvrir un dossier, vérifier le statut et la preuve. |
| **Retard** | Délai dépassé. | Notifier l'OAG, informer l'acheteur. |
| **Produit non conforme** | Article différent de la description. | Collecter la fiche initiale, les photos et les réponses. |
| **Commande incomplète** | Quantité manquante. | Comparer quantité commandée, préparée et remise. |
| **Minimum non atteint** | Seuil de participants non atteint. | Appliquer le cycle du Club d'achat et les règles de remboursement. |
| **Paiement contesté** | Débit annoncé sans confirmation. | Vérifier auprès du prestataire. |
| **Suspicion de fraude** | OAG injoignable ou documents falsifiés. | Mesures conservatoires proportionnées et enquête. |
| **Contestation de badge** | L'OAG conteste une notation ou un badge. | Ouvrir un dossier de contestation, revoir les critères. |

#### 4.8.3 Procédure en cinq étapes

1. **Ouverture** : l'utilisateur choisit la participation, le motif, décrit le problème et joint les preuves. Un numéro de dossier est attribué.
2. **Accusé de réception** : sous 24 heures ouvrées, avec les prochaines étapes et le délai cible.
3. **Contradictoire** : l'autre partie est informée et peut répondre sous 2 jours ouvrés. Seules les données nécessaires sont partagées ; l'OAG ne voit jamais l'adresse ou le téléphone de l'acheteur.
4. **Analyse** : le gestionnaire examine paiements, historique, description, échanges utiles et preuve de remise. Il peut demander des pièces complémentaires.
5. **Décision et recours** : décision motivée, actions exécutées, voies de recours communiquées. La décision est notifiée aux deux parties.

#### 4.8.4 Délais cibles

| Action | Cible |
|---|---|
| Accusé de réception | 24 heures ouvrées |
| Première analyse | 2 jours ouvrés |
| Réponse initiale de l'OAG | 2 jours ouvrés |
| Cas simple | 3 à 5 jours ouvrés |
| Cas complexe | jusqu'à 10 jours ouvrés, avec information régulière |

Ces délais sont des objectifs internes, pas des délais légaux. Ils doivent être configurables et affichés dans le dossier. Le calcul en jours ouvrés suppose une table de jours fériés ; à défaut, utiliser des jours calendaires avec une marge, et le dire.

#### 4.8.5 Escalade

| Niveau | Qui | Cas |
|---|---|---|
| **1** | Support client ou gestionnaire OAG | Incidents simples, retard, incompréhension. |
| **2** | Responsable litiges / opérations | Désaccord nécessitant une analyse, montant significatif. |
| **3** | Direction et conseil juridique | Fraude présumée, montant important, risque réglementaire. |

Les parties conservent le droit de saisir les autorités ou juridictions compétentes. La procédure interne ne prive personne de ses droits.

#### 4.8.6 Remboursements

**Cas de remboursement.** La liste doit être fermée et écrite dans les CGV :

1. L'Offre d'achat n'a pas abouti et l'OAG renonce, ou ne répond pas dans le délai prévu.
2. L'OAG disparaît avant la mise à disposition.
3. Le colis a été remis sans scan et l'acheteur conteste la remise.
4. Le délai annoncé est dépassé d'une marge fixée au contrat, sans explication.
5. Le produit livré est non conforme à la description, après examen des preuves.
6. La commande est incomplète, après comparaison des quantités.
7. Le paiement est contesté et l'encaissement n'est pas confirmé.

**Ce qui n'ouvre pas droit à remboursement.** Le produit ne plaît pas, la couleur n'est pas celle imaginée, la taille ne convient pas, l'acheteur a changé d'avis. Une participation payée ne s'annule pas à sa demande, sous réserve des droits impératifs des consommateurs.

**Ordre de financement.** D'abord le séquestre de l'Offre d'achat, ensuite le fonds de garantie interne, puis la procédure de recouvrement auprès de l'OAG. Chaque remboursement porte : motif, décideur, approbateur, référence de transaction, statut, preuve d'exécution, date.

**Double validation.** Au-delà du seuil défini (recommandation : 100 000 FCFA), deux validateurs distincts. En mode prototype, le remboursement est simulé et porte `simule=True`.

#### 4.8.7 Lien avec les avis

L'avis reste public et ne peut pas être supprimé par l'OAG. Il ne remplace pas la réclamation. Un acheteur peut laisser un avis **et** ouvrir une réclamation. Une réclamation confirmée peut être affichée comme indicateur de réputation, mais le détail du dossier reste confidentiel.

### 4.9 Assurance Tout Risques et partenaires

#### 4.9.1 Police unique par Offre d'achat

| Champ | Contenu |
|---|---|
| Offre d'achat | Une police par Offre d'achat. |
| Assureur | Nom, agrément, contact. |
| Référence | Numéro de police ou de certificat. |
| Couverture | Événements couverts, de la collecte à la livraison. |
| Exclusions | Ce qui n'est pas couvert. |
| Plafond | Montant maximal. |
| Franchise | Montant à la charge de l'assuré. |
| Prime | Montant et payeur. |
| Statut | `A_SOUSCRIRE`, `ACTIVE`, `EXPIREE`, `ANNULEE`. |
| Document | Conditions générales et particulières. |

**Règle d'affichage.** Tant que le statut n'est pas `ACTIVE`, l'écran affiche « Assurance prévue — partenariat en cours » et jamais « couvert » ou « assuré ». Une police `ACTIVE` doit afficher les exclusions et le plafond, pas seulement le mot « assurance ».

#### 4.9.2 Sinistres

Un dossier de sinistre porte : police, participation, nature, date, preuves, déclaration, statut, décision de l'assureur, montant indemnisé. Il est distinct de la réclamation : la réclamation traite le problème commercial, le sinistre traite la couverture.

#### 4.9.3 Partenaires

| Partenaire | Contribution attendue | Vérification avant signature |
|---|---|---|
| Prestataire de paiement | Encaissement, confirmation, remboursement, rapprochement. | Agrément, frais, délais, sécurité, erreurs. |
| Transporteurs / agences | Livraison, points relais, suivi, preuve de remise. | Couverture, assurance, preuve, niveaux de service. |
| Assureur | Assurance Tout Risques, couvertures complémentaires. | Habilitation, exclusions, plafonds, distribution conforme. |
| Fournisseurs / grossistes | Approvisionnement, disponibilité, prix. | Vérification, qualité, délais, retours. |
| Conseils juridiques | Contrats, conformité, litiges. | Compétence en droit togolais. |
| Hébergement / sécurité | Hébergement, sauvegarde, supervision. | Localisation, transferts, sous-traitance, disponibilité. |

**Aucun partenariat n'est présenté comme acquis avant signature.** Les noms « La Poste » et « Gozem » sont des pistes, pas des engagements.

### 4.10 Réputation, badges et historique

#### 4.10.1 Indicateurs

| Indicateur | Définition | Public |
|---|---|---|
| Identité vérifiée | Contrôles réalisés selon le profil. | Oui, badge. |
| Offres d'achat terminées | Offres clôturées conformément au processus. | Oui. |
| Taux de livraison | Participations livrées parmi celles arrivées à échéance. | Oui, avec le nombre d'offres pour contextualiser. |
| Respect des délais | Livraisons dans le délai annoncé ou mis à jour. | Oui. |
| Réclamations confirmées | Incidents établis après examen, séparés des simples signalements. | Oui, agrégé sur 12 mois. |
| Satisfaction | Évaluations après une expérience réelle. | Oui. |
| Historique d'activité | Offres lancées, montants collectés, paiements, régularité. | Privé, exportable par l'OAG. |

#### 4.10.2 Badges

| Badge | Critère proposé | Statut |
|---|---|---|
| **Identité vérifiée** | KYC validé + contrat accepté + téléphone vérifié. | À valider. |
| **OAG expérimenté** | 10 Offres d'achat terminées + taux de livraison ≥ 95 % + aucune réclamation confirmée sur 6 mois. | À valider. |
| **OAG recommandé** | 25 Offres d'achat terminées + note ≥ 4,5 sur 20 avis + taux de livraison ≥ 98 % + taux de réclamation < 2 % + ancienneté ≥ 12 mois. | À valider. |

Les critères sont **publiés** sur une page dédiée. Un badge n'est pas une garantie absolue de qualité. Toute décision d'attribution ou de retrait est datée, motivée et contestable.

#### 4.10.3 Contestation

L'OAG peut contester un badge ou une notation. La contestation ouvre un dossier de type `CONTESTATION_BADGE`, avec les mêmes garanties qu'une réclamation : accusé de réception, contradictoire, décision motivée, recours. Une erreur corrigée est journalisée.

#### 4.10.4 Historique bancaire

L'export d'activité contient : Offres d'achat lancées, montants collectés, paiements effectués, régularité, grade, commissions, incidents. Il est généré **à la demande de l'OAG**, avec son consentement, et porte la mention « document non contractuel ; la décision de prêt appartient à la banque ». Il ne contient aucune donnée personnelle d'acheteur.

### 4.11 Administration, double validation et audit

#### 4.11.1 Rôles internes

| Rôle | Responsabilités | Ne doit pas pouvoir |
|---|---|---|
| **Direction** | Vision, priorités, arbitrages, décisions exceptionnelles. | Exécuter seule un décaissement ou un remboursement. |
| **Technique / sécurité** | Architecture, infrastructure, sauvegardes, incidents. | Autoriser un décaissement. |
| **Gestion des OAG** | Recrutement, vérification, formation, suivi, suspension. | Autoriser les retraits de ses propres OAG. |
| **Support / litiges** | Réclamations, preuves, médiation, décision de niveau 1 et 2. | Exécuter un remboursement sans validation finance. |
| **Finance / opérations** | Rapprochements, commissions, remboursements, retraits, reporting. | Valider seule un décaissement au-delà du seuil. |
| **Partenariats** | Paiement, logistique, assurance, fournisseurs, notaire. | Accéder aux dossiers KYC sans habilitation. |
| **Conformité / données** | IPDCP, contrats, droits des personnes, sous-traitants, incidents. | Décider d'une suspension commerciale. |
| **Communication** | Image, campagnes, crise. | Accéder aux données personnelles. |

#### 4.11.2 Séparations à ne pas fusionner

- Celui qui valide un OAG ne doit pas être celui qui autorise ses retraits.
- Celui qui mène l'entretien ne doit pas être seul à décider de la validation.
- Celui qui propose un remboursement ne doit pas être seul à l'approuver et à l'exécuter.
- Personne ne peut seul créer une transaction, modifier son statut, approuver un remboursement et effacer la trace.

#### 4.11.3 Double validation

- Les opérations sensibles passent par un statut `A_APPROUVER`, puis `APPROUVE`, puis `EXECUTE`.
- Le demandeur, l'approbateur 1, l'approbateur 2 et l'exécutant sont des personnes distinctes au-delà du seuil.
- Un refus est motivé.
- Le seuil est un paramètre : recommandation 500 000 FCFA pour les décaissements, 100 000 FCFA pour les remboursements.

#### 4.11.4 Journal d'audit

Le journal est **append-only** : aucune modification, aucune suppression via l'interface. Il porte : acteur, rôle, action, objet, valeurs avant/après, motif, adresse IP si collectée, horodatage, chaînage de hash pour détecter une altération.

Actions à journaliser au minimum :

- validation, refus, suspension d'un dossier OAG ;
- consultation d'une pièce KYC ;
- changement de nom d'utilisateur ;
- attribution, correction ou retrait de points ;
- changement de grade ;
- création, approbation, exécution ou refus d'un décaissement ;
- ouverture, décision, remboursement d'une réclamation ;
- activation, expiration ou annulation d'une police ;
- modification des paramètres (prix, seuils, délais) ;
- export ou suppression de données personnelles ;
- accès administrateur refusé.

#### 4.11.5 Tableau de bord de confiance

| Indicateur | Formule | Fréquence |
|---|---|---|
| Taux de vérification OAG | OAG validés / candidatures complètes | Mensuelle |
| Taux d'Offres d'achat abouties | Offres ayant atteint le minimum / offres clôturées | Mensuelle |
| Livraison à temps | Participations livrées à temps / participations arrivées à échéance | Mensuelle |
| Taux de réclamation | Participations avec réclamation / participations payées | Mensuelle |
| Délai de résolution | Temps entre ouverture et clôture | Hebdomadaire |
| Remboursements exécutés | Remboursements exécutés / remboursements dus | Hebdomadaire |
| Réutilisation | Acheteurs avec un nouvel achat / acheteurs actifs | Mensuelle |
| Rétention OAG | OAG actifs en fin de période / OAG actifs en début | Mensuelle |
| Incidents de sécurité | Nombre par gravité et délai de traitement | Mensuelle / immédiate |

### 4.12 Données personnelles et IPDCP

#### 4.12.1 Cartographie

| Catégorie | Exemples | Accès |
|---|---|---|
| Identité acheteur | Nom, prénom, téléphone, e-mail facultatif. | Acheteur ; support habilité si nécessaire. |
| Dossier OAG / KYC | Pièce d'identité, justificatifs d'activité. | Conformité habilitée uniquement ; accès journalisé. |
| Historique d'activité OAG | Offres, montants, paiements, régularité. | Personnel habilité ; OAG pour son historique ; banque avec consentement. |
| Compte | Identifiant, mot de passe haché. | Système d'authentification ; jamais en clair. |
| Paiement | Référence, montant, statut, horodatage. | Finance habilitée ; OAG limité aux données utiles. |
| Livraison | Adresse ou point relais, statut, preuve. | Partenaire et personnes autorisées selon le besoin. |
| Chat | Messages, signalements. | Participants ; modération habilitée. |
| Sécurité | Journaux, IP, événements de connexion. | Équipe sécurité habilitée ; accès journalisé. |

#### 4.12.2 Droits des personnes

- **Consentement** : case non précochée à l'inscription, finalité dite en clair, version et date enregistrées.
- **Accès** : écran « Mes données » et export.
- **Rectification** : l'utilisateur corrige ce qui peut l'être ; le reste passe par une demande.
- **Opposition** : pour les traitements non essentiels.
- **Suppression** : demande de suppression de compte, avec les effets et les limites écrits. Ce qui doit survivre pour des raisons comptables ou probatoires est nommé, pas caché.
- **Durée** : chaque catégorie a une limite, et l'effacement est automatique à son terme.

#### 4.12.3 Durées proposées

| Catégorie | Durée proposée | Base |
|---|---|---|
| Compte | Vie du compte + 1 an | Gestion de la relation. |
| Pièces KYC | 5 ans après la fin de la relation | Preuve et contentieux ; à valider. |
| Contrats | 10 ans après la fin | Prescription ; à valider. |
| Transactions | 10 ans | Comptabilité ; à valider. |
| Messages privés | 2 ans après le dernier message | Service et modération ; à valider. |
| Adresse de livraison | 30 jours après la remise, puis anonymisation | Minimisation. |
| Réclamations | 5 ans après clôture | Preuve ; à valider. |
| Journaux de sécurité | 1 an | Sécurité ; à valider. |
| Adresse IP | 6 mois si collectée | Sécurité ; à valider. |

Ces durées sont des **propositions**. Elles doivent être validées par un juriste et l'IPDCP avant d'être codées en dur. En attendant, elles vivent dans un paramètre, pas dans une constante.

#### 4.12.4 Sous-traitants et incidents

- Contrats de sous-traitance pour l'hébergement, le SMS, le paiement, l'analytics et le support.
- Registre des traitements, cartographie des flux, politique de conservation.
- Procédure de violation de données : détection, qualification, réponse, notification si la loi l'exige.
- Sauvegardes chiffrées, isolées, avec restauration testée.

---

## 5. Matrice des écarts

### 5.1 Synthèse

| Domaine | Écart majeur | Phase |
|---|---|---|
| Points et grades | Barème 10/10/2/10/2/5 et seuils 0/500/700 à remplacer par 5/0/2/10/2/10 et 0/250/400/600. | 1 |
| Contact Privé | 1 000 FCFA, 5 points, sans seuil, révèle le téléphone. | 1 |
| Publication | Ancien système conservé ; aucun changement de formule, mais libellés et points à aligner. | 1 |
| Médias | 3 images + 2 vidéos ; 5 photos de campagne. | 1 |
| Terminologie | « Campagne » et « groupeur » dans l'interface. | 1 |
| Réduction livraison | 150 points dans la v1, 60 dans le manuel, 100 dans le nouveau document ; aucun code. | 1 / 2 |
| OTP | Absent. | 2 |
| Réclamations | Absent ; la v1 dit « la plateforme n'arbitre pas ». | 2 |
| KYC et contrats | 3 statuts, pas de parcours en 6 étapes, pas de contrat/charte. | 2 |
| Badges et réputation | Note et compteurs, pas de badges ni de taux publics. | 2 |
| Assurance | Mentionnée, non modélisée. | 2 |
| Administration | `est_equipe`, pas de rôles, pas de double validation, pas d'audit. | 3 |
| Données | KYC protégé, pas de consentement, export, effacement, durées. | 3 |
| Tableau de bord confiance | Absent. | 3 |
| Partenaires | Pistes, aucun contrat signé. | 4 |

### 5.2 Comptes et OAG

| Existant | Cible | Action | Phase |
|---|---|---|---|
| `comptes/models.py` : `DossierKYC` avec `EN_ATTENTE`, `VALIDE`, `REJETE`. | Parcours en 6 étapes + statuts `CANDIDATURE` à `SUSPENDU`. | Étendre le modèle, ajouter `EvenementKYC`. | 2 |
| Deux profils implicites (commerçant, individuel). | Trois profils : commerçant, individuel, partenaire. | Ajouter `profil` et les pièces associées. | 2 |
| Pas de contrat OAG ni de charte. | `ContratOAG`, `CharteOAG`, versions, dates, statuts. | Nouveaux modèles et écrans. | 2 |
| `Reputation` : note, campagnes, participants, avis. | Ajouter taux de livraison, respect des délais, réclamations confirmées, montant collecté, dernière activité. | Étendre le modèle et les calculs. | 2 |
| Pas de badges. | `Badge`, `BadgeOAG`, critères publiés, contestation. | Nouveaux modèles et écrans. | 2 |
| Pas d'historique bancaire. | Export d'activité avec consentement. | Vue d'export, PDF/CSV. | 2 / 4 |
| `Utilisateur.est_equipe` et `role`. | Rôles internes séparés. | `ProfilAdmin` ou groupes Django + permissions. | 3 |
| Contact Privé révèle `nom_complet` et `telephone`. | Coordonnées masquées ; messagerie interne. | Retirer les champs et adapter les tests. | 1 |

### 5.3 Catalogue et médias

| Existant | Cible | Action | Phase |
|---|---|---|---|
| `MediaProduit.MAX_VIDEOS = 2`. | 1 vidéo maximum. | Passer à 1, migration de données si nécessaire, test. | 1 |
| `MediaProduit.MAX_IMAGES = 3`. | 3 images. | Conforme. | 1 |
| `MediaCampagne.MAX_IMAGES = 5`. | 3 photos de lot, sans vidéo. | Passer à 3, test. | 1 |
| Libellés « campagne », « groupeur ». | « Offre d'achat », « Club d'achat », « OAG ». | Passe de libellés UI et `verbose_name`. | 1 |
| Fiche : prix, description, photos. | Ajouter badge, statut assurance, conditions de réclamation, limites. | Composants de fiche. | 2 |
| Mise en avant non définie. | Service distinct, signalé. | Décider le tarif et le mode. | 2 |

### 5.4 Participation, paiement et commission

| Existant | Cible | Action | Phase |
|---|---|---|---|
| `Participation.code_retrait` statique, QR `GA|campagne|code`. | Jeton imprévisible, statut, révocation, journal. | Durcir le jeton et le scan. | 2 |
| Pas d'OTP. | OTP d'achat + OTP de remise. | Nouveau modèle `CodeOTP`, vues, tests. | 2 |
| `Transaction.simulee`. | Conserver et afficher le statut de simulation. | Mentions UI. | 1 |
| Commission 3,5 / 2,5 / 1,3 %. | 4 / 3 / 2 %. | `grades.py`, tests, démo. | 1 |
| `Decaissement` sans double validation. | Statuts `A_APPROUVER`, `APPROUVE`, `EXECUTE`, deux validateurs. | Modèle et vues admin. | 3 |
| Pas de journal d'audit. | `JournalAudit` append-only. | Nouveau modèle et hooks. | 3 |
| Remboursement après décaissement non défini. | Règle D-10. | Documenter et coder au moment des remboursements. | 2 / 3 |
| Vocabulaire « portefeuille ». | « Solde d'opération », « solde bloqué », « solde retirable ». | Passe de libellés. | 1 |

### 5.5 Contact Privé

| Existant | Cible | Action | Phase |
|---|---|---|---|
| `PRIX_MENSUEL_FCFA = 1000`. | 2 000. | Modifier la constante, les tests, la démo. | 1 |
| `BAREME[CONTACT_PRIVE] = 5`. | 10. | Modifier le barème. | 1 |
| Aucune condition de points. | 50 points cumulés minimum. | Vérifier dans la vue de souscription et l'état. | 1 |
| Révèle nom complet et téléphone. | Nom public et badge seulement. | Retirer `nom_complet` et `telephone` du sérialiseur. | 1 |
| Docstring « l'abonnement vend l'identité ». | « L'abonnement ouvre la messagerie ». | Mettre à jour le commentaire et les tests. | 1 |

### 5.6 Points, grades et publication

| Existant | Cible | Action | Phase |
|---|---|---|---|
| `BAREME` : 10 achat, 10 groupage, 2 parrainage, 10 abonnement, 2 pack, 5 Contact. | 5 achat, 0 groupage, 2 parrainage, 10 abonnement, 2 pack, 10 Contact. | Modifier `points.py`, tests, démo. | 1 |
| `SEUILS` : 0 / 500 / 700. | 0 / 250 / 400 / 600 avec palier Nouveau. | Modifier `grades.py`, tests, affichage. | 1 |
| `COMMISSIONS_CENTIEMES` : 350 / 250 / 130. | 400 / 300 / 200. | Modifier `grades.py`, tests, démo. | 1 |
| `GROUPAGE_ABOUTI` 10 pts. | 0 pt. | Supprimer l'attribution dans `paiements/services.py`. | 1 |
| Publication 2 000/mois + 500/5. | Conservée. | Aucun changement de formule. | 1 |
| Réduction 150/60 points. | 100 points, 50 %, une fois. | Décider le mécanisme, puis coder. | 1 / 2 |
| Pas de modèle d'avantage. | `AvantageAcheteur` si la réduction est retenue. | Nouveau modèle. | 2 |

### 5.7 Réclamations

| Existant | Cible | Action | Phase |
|---|---|---|---|
| Aucun dossier de litige. | `DossierReclamation`, `PreuveReclamation`, `MessageReclamation`, `DecisionReclamation`, `Remboursement`. | Nouveau domaine. | 2 |
| `Avis` : docstring « la plateforme n'arbitre pas ». | La plateforme instruit. | Mettre à jour le texte et la doc. | 1 / 2 |
| Avis = seul recours. | Avis + réclamation. | Écrans acheteur et admin. | 2 |
| Pas de délais ni d'escalade. | 24 h, 2 j, 3–5 j, 10 j ; niveaux 1/2/3. | Champs de dates, statuts, tableau de bord. | 2 |
| Pas de remboursement structuré. | `Remboursement` avec double validation. | Nouveau modèle et vues. | 2 / 3 |

### 5.8 Assurance et partenaires

| Existant | Cible | Action | Phase |
|---|---|---|---|
| Aucun modèle d'assurance. | `PoliceAssurance` par Offre d'achat, statuts. | Nouveau modèle, écran admin, mention fiche. | 2 |
| Aucun sinistre. | `DeclarationSinistre`. | Nouveau modèle. | 4 |
| Partenaires non modélisés. | Table des partenaires, statuts, contrats. | Modèle simple ou documentation. | 4 |
| Communication « assurance » libre. | Règle 0.1. | Passe de libellés et tests de mention. | 1 |

### 5.9 Administration, gouvernance et données

| Existant | Cible | Action | Phase |
|---|---|---|---|
| `est_equipe` + `role`. | Rôles internes et permissions. | `ProfilAdmin` / groupes. | 3 |
| Pas de double validation. | Statuts et validateurs. | Modèles et vues. | 3 |
| Pas de journal d'audit. | `JournalAudit` append-only. | Modèle, hooks, écran. | 3 |
| Console admin : 5 entrées. | Ajouter réclamations, assurance, audit, confiance, données. | Routes et pages. | 2 / 3 |
| Pas de tableau de confiance. | 9 indicateurs. | Requêtes et page. | 3 |
| KYC protégé, pas de consentement. | `Consentement`, `DemandeDroits`, `PolitiqueConservation`. | Nouveaux modèles et écrans. | 3 |
| Pas d'export/suppression. | « Mes données », export, suppression. | Vues et tâches. | 3 |
| Pas de durées. | Paramètres de conservation. | Modèle et tâche d'effacement. | 3 |

### 5.10 Documentation et démonstration

| Existant | Cible | Action | Phase |
|---|---|---|---|
| `CAHIER_DES_CHARGES.md` v1. | Remplacé par ce document. | Validation puis archivage. | 0 |
| `MANUEL_EXPLOITATION.md` : 1 500 FCFA, 3,5/2,5/1,3 %, 60 points, etc. | Aligner sur 2 000, 4/3/2, 100 points. | Passe de mise à jour. | 1 |
| `CLAUDE.md` : décisions v1. | Ajouter les décisions v2. | Mise à jour après validation. | 0 / 1 |
| `charger_demo.py` : barème et commissions v1. | Barème v2, réclamations, polices en `A_SOUSCRIRE`. | Mise à jour + `VERSION_DEMO`. | 1 / 2 |

---

## 6. Modèle de données cible

### 6.1 Modèles existants à modifier

| Modèle | Fichier | Changement |
|---|---|---|
| `Utilisateur` | `comptes/models.py` | `verbose_name` OAG ; pas de téléphone public ; éventuel `profil_admin`. |
| `DossierKYC` | `comptes/models.py` | `profil`, `etape`, statuts étendus, dates d'entretien, formation, signature, observation. |
| `Reputation` | `comptes/models.py` | Taux de livraison, respect des délais, réclamations confirmées, montant collecté, dernière activité. |
| `CompteurPoints` | `comptes/models.py` | Inchangé ; le barème change dans `points.py`. |
| `Campagne` | `catalogue/models.py` | `verbose_name` Offre d'achat ; lien vers `PoliceAssurance` ; pas de changement de structure. |
| `MediaProduit` | `catalogue/models.py` | `MAX_VIDEOS = 1`. |
| `MediaCampagne` | `catalogue/models.py` | `MAX_IMAGES = 3`. |
| `Participation` | `commandes/models.py` | Jeton QR avec statut, révocation, expiration ; lien vers les OTP. |
| `Avis` | `commandes/models.py` | Docstring et règle : la plateforme instruit les réclamations. |
| `Decaissement` | `paiements/models.py` | Champs d'approbation, validateurs, statut `A_APPROUVER`. |
| `Transaction` | `paiements/models.py` | `simulee` conservé ; référence prestataire. |

### 6.2 Nouveaux modèles

| Modèle | Champs clés | Contraintes |
|---|---|---|
| `EvenementKYC` | dossier, etape, acteur, date, commentaire, document. | Append-only. |
| `ContratOAG` | oag, version, statut, date_signature, date_certification, notaire, reference, document. | Un contrat actif par OAG. |
| `CharteOAG` | oag, version, date_acceptation, document. | Version unique par OAG. |
| `Badge` | code, libelle, description, critere, version, actif. | Code unique. |
| `BadgeOAG` | oag, badge, date, statut, motif, conteste_le, resolu_le. | Un badge actif par OAG et par code. |
| `CodeOTP` | utilisateur, participation, usage (`ACHAT`, `REMISE`), code_hash, cree_le, expire_le, consomme_le, tentatives. | Usage unique, expiration, max tentatives. |
| `DossierReclamation` | reference, participation, plaignant, type, description, statut, niveau, dates, decision, motif, montant. | Reference unique. |
| `PreuveReclamation` | dossier, fichier, description, ajoute_par, date. | Taille et type contrôlés. |
| `MessageReclamation` | dossier, auteur, texte, interne, date. | Un message interne n'est pas visible par les parties. |
| `DecisionReclamation` | dossier, decision, motif, acteur, date, montant, statut. | Une décision par version. |
| `Remboursement` | dossier, participation, montant, statut, valide_par_1, valide_par_2, reference, date, preuve, simule. | Montant > 0, double validation au seuil. |
| `PoliceAssurance` | campagne, assureur, reference, statut, couverture, exclusions, plafond, franchise, prime, dates, document. | Une police par campagne. |
| `DeclarationSinistre` | police, participation, nature, date, preuves, statut, decision, montant. | — |
| `JournalAudit` | acteur, role, action, objet_type, objet_id, avant, apres, motif, ip, user_agent, cree_le, hash_precedent, hash. | Append-only. |
| `ValidationSensible` | type, objet, demandeur, approbateur_1, approbateur_2, statut, motif, dates. | Deux validateurs distincts au seuil. |
| `Consentement` | utilisateur, finalite, version, date, preuve. | — |
| `DemandeDroits` | utilisateur, type, statut, date, echeance, reponse, motif. | — |
| `PolitiqueConservation` | categorie, duree, base_legale, version. | — |
| `ParametrePlateforme` | cle, valeur, type, version, modifie_par, date. | Clé unique, historique. |
| `AvantageAcheteur` | utilisateur, type, statut, date_obtention, date_utilisation, reference. | Un avantage `REDUCTION_LIVRAISON` par compte. |

**Note.** `ParametrePlateforme` est recommandé pour les prix, seuils, commissions, délais et durées. Cela évite de redéployer pour changer un seuil et permet de journaliser qui a changé quoi. Pour la Phase 1, les constantes existantes peuvent suffire, mais les valeurs doivent être centralisées.

---

## 7. Écrans et routes

### 7.1 Boutique / acheteur

| Écran | Contenu | Route API | Phase |
|---|---|---|---|
| Fiche Club d'achat | Badge OAG, statut assurance, conditions, réclamation, prix, minimum, date limite. | `GET /catalogue/campagnes/<id>/` | 1 / 2 |
| Mes achats | Statut, QR, OTP, réclamation, preuve. | `GET /participations/` | 2 |
| Détail achat | QR, code de secours, historique, bouton « Ouvrir une réclamation ». | `GET /participations/<id>/` | 2 |
| Réclamation | Formulaire, preuves, suivi, messages, décision. | `POST /reclamations/`, `GET /reclamations/<id>/` | 2 |
| Profil | Points cumulés, solde, avantages, éligibilité Contact Privé. | `GET /comptes/moi/` | 1 |
| Mes données | Consentements, export, demande de suppression. | `GET /comptes/donnees/` | 3 |
| Contact Privé | État, prix, seuil de 50 points, souscription. | `GET /contact-prive/`, `POST /contact-prive/souscrire/` | 1 |
| Messages | Messagerie interne, nom public, badge. | `GET /conversations/` | 1 |

### 7.2 Espace OAG

| Écran | Contenu | Route API | Phase |
|---|---|---|---|
| Tableau de bord | Grade, commission, points, badge, prochain palier, alertes. | `GET /groupeur/tableau-de-bord/` | 1 |
| Nouvelle Offre d'achat | Produit, 3 images + 1 vidéo, prix, minimum, date, conditions. | `POST /groupeur/campagnes/` | 1 |
| Mes Offres d'achat | Statuts, participations, réclamations, preuves. | `GET /groupeur/campagnes/` | 2 |
| Dossier OAG | 6 étapes, pièces, contrat, charte, badges. | `GET /comptes/dossier/` | 2 |
| Réclamations reçues | Dossiers, réponses, preuves, décisions. | `GET /groupeur/reclamations/` | 2 |
| Historique d'activité | Export bancaire, consentement. | `GET /groupeur/historique/` | 2 / 4 |
| Compte OAG | Profil public, coordonnées masquées, Contact Privé. | `GET /comptes/moi/` | 1 |

### 7.3 Administration

| Écran | Contenu | Route API | Phase |
|---|---|---|---|
| Supervision | Indicateurs, files d'attente, alertes. | `GET /admin/tableau-de-bord/` | 1 |
| Dossiers KYC | Étapes, pièces, entretien, formation, signature, observation. | `GET /admin/dossiers/` | 2 |
| Vérification des Offres | File, décision, motif. | `GET /admin/campagnes/a-verifier/` | 1 |
| Décaissements | Double validation, statuts, preuves. | `GET /admin/decaissements/` | 3 |
| Réclamations | Dossiers, délais, escalade, décision, remboursement. | `GET /admin/reclamations/` | 2 |
| Assurance | Polices, statuts, sinistres. | `GET /admin/assurances/` | 2 / 4 |
| Audit | Journal append-only, filtres, export. | `GET /admin/audit/` | 3 |
| Confiance | 9 indicateurs, période, export. | `GET /admin/confiance/` | 3 |
| Données | Demandes, consentements, durées, incidents. | `GET /admin/donnees/` | 3 |
| Modération | Messages signalés, décision, motif. | `GET /admin/messages/` | 1 |

---

## 8. Plan de mise en œuvre

### 8.1 Vue d'ensemble

| Phase | Objectif | Livrables | Critère de sortie |
|---|---|---|---|
| **0. Spécification** | Trancher les règles et les écarts. | Ce document, journal des décisions, matrice. | Décisions P-01 à P-06 prises. |
| **1. Règles et terminologie** | Aligner le produit sur le barème, les prix, les médias et le vocabulaire. | Code, migrations, tests, démo, docs. | Suite de tests verte ; aucun libellé « groupeur » dans l'UI. |
| **2. Confiance produit** | OTP, réclamations, KYC 6 étapes, badges, assurance. | Modèles, API, écrans, tests. | Un dossier de réclamation complet peut être instruit ; un OTP fonctionne ; une police ne s'affiche jamais active sans statut. |
| **3. Gouvernance** | Rôles, double validation, audit, données, tableau de bord. | Modèles, permissions, écrans, tests. | Un admin ne peut pas valider seul au-delà du seuil ; le journal est append-only ; l'export de données fonctionne. |
| **4. Partenaires et pilote** | Tester avec un partenaire de paiement, un assureur, un notaire, la logistique. | Contrats, pilote, rapport. | 5 OAG, 10 offres, 100 acheteurs, 100 % des réclamations suivies. |

### 8.2 Phase 0 — Spécification (en cours)

**Objectif.** Éviter de coder deux fois. Ce document est le livrable.

**À faire avant de coder :**

- Valider D-06 à D-16.
- Trancher P-01 à P-06 (voir section 9).
- Décider si le grade est atteint par les points, par les offres terminées, ou les deux.
- Décider le mécanisme de la réduction de livraison.
- Décider le nombre d'OTP.
- Décider le moment d'exigibilité de la commission et le sort des remboursements après décaissement.
- Valider les mentions de réalité (assurance, contrat, paiement, SMS).

### 8.3 Phase 1 — Règles et terminologie

**Lot 1.1 — Barème, grades et commission.**
- Modifier `comptes/points.py` : 5 / 0 / 2 / 10 / 2 / 10.
- Modifier `comptes/grades.py` : 0 / 250 / 400 / 600, commissions 400 / 300 / 200, palier Nouveau.
- Retirer l'attribution de `GROUPAGE_ABOUTI` dans `paiements/services.py`.
- Mettre à jour `charger_demo.py` et `VERSION_DEMO`.
- Tests : `tests/test_points.py`, `tests/test_cloture.py`, `tests/test_parrainage.py`.

**Lot 1.2 — Contact Privé.**
- `PRIX_MENSUEL_FCFA = 2000`.
- `BAREME[CONTACT_PRIVE] = 10`.
- Condition de 50 points cumulés dans `SouscriptionVue` et dans `_etat`.
- Retirer `nom_complet` et `telephone` du sérialiseur ; le Contact Privé ouvre la messagerie, pas les coordonnées.
- Mettre à jour `tests/test_contact_prive.py`.

**Lot 1.3 — Publication.**
- Conserver 2 000/mois + 500/5.
- Vérifier que les points restent 10/mois et 2/pack.
- Mettre à jour les libellés « OAG ».
- Tests : `tests/test_publication.py` inchangé sur le fond, sauf libellés.

**Lot 1.4 — Médias.**
- `MediaProduit.MAX_VIDEOS = 1`.
- `MediaCampagne.MAX_IMAGES = 3`.
- Migration de données si des vidéos ou photos excèdent les nouveaux plafonds : décider au cas par cas (conserver les plus récentes, ou demander à l'OAG de choisir).
- Tests : `catalogue/tests.py`.

**Lot 1.5 — Terminologie.**
- Passe de libellés dans `frontend/boutique` et `frontend/admin` : « OAG », « Offre d'achat », « Club d'achat ».
- `verbose_name` des modèles `Campagne`, `groupeur`, `Participation`.
- Messages d'erreur et notifications.
- Ne pas renommer les routes ni les modèles.

**Lot 1.6 — Réduction de livraison.**
- Si le mécanisme est tranché : modèle `AvantageAcheteur`, seuil 100, une fois, statut.
- Sinon : afficher « avantage en préparation » et ne pas coder.

**Critères d'acceptation Phase 1.**
- Un achat payé donne 5 points.
- Un groupage abouti ne donne plus de points.
- Un OAG à 249 points est Nouveau, à 250 Bronze, à 400 Argent, à 600 Or.
- La commission est 4 / 3 / 2 %.
- Le Contact Privé coûte 2 000, exige 50 points cumulés, donne 10 points, ne révèle pas le téléphone.
- Une quatrième vidéo est refusée ; une sixième photo de campagne est refusée.
- Aucun écran ne dit « groupeur » pour désigner l'OAG.
- `pytest` est vert.

### 8.4 Phase 2 — Confiance produit

**Lot 2.1 — OTP et QR.**
- Modèle `CodeOTP` (achat, remise), hachage, expiration, tentatives, usage unique.
- Génération de l'OTP d'achat au paiement ; OTP de remise à la demande.
- Jeton QR avec statut, révocation, journal.
- Tests : `tests/test_livraison.py`, `tests/test_securite.py`.

**Lot 2.2 — Réclamations et remboursements.**
- Modèles `DossierReclamation`, `PreuveReclamation`, `MessageReclamation`, `DecisionReclamation`, `Remboursement`.
- API acheteur, OAG, admin.
- Délais, escalade, décision motivée, notification.
- Remboursement : séquestre, fonds de garantie, recouvrement.
- Tests : nouveau `tests/test_reclamations.py`.

**Lot 2.3 — KYC 6 étapes, contrats et charte.**
- Étendre `DossierKYC`, ajouter `EvenementKYC`, `ContratOAG`, `CharteOAG`.
- Écrans admin et OAG.
- Tests : `tests/test_administration.py`, nouveau `tests/test_kyc.py`.

**Lot 2.4 — Badges, réputation et historique.**
- `Badge`, `BadgeOAG`, critères, contestation.
- Étendre `Reputation`.
- Export d'activité.
- Tests : nouveau `tests/test_reputation.py`.

**Lot 2.5 — Assurance.**
- `PoliceAssurance`, `DeclarationSinistre`.
- Statuts, mentions, écran admin, fiche.
- Tests : nouveau `tests/test_assurance.py`, vérifier qu'aucune police n'est active par défaut.

**Critères d'acceptation Phase 2.**
- Un OTP d'achat expire, 3 tentatives, usage unique.
- Un OTP de remise est généré à la demande et ne peut pas être réutilisé.
- Une réclamation peut être ouverte, accusée, passée en contradictoire, décidée et remboursée.
- Le dossier affiche les délais cibles et l'escalade.
- Le KYC a 6 étapes et 3 profils.
- Un badge ne s'affiche que si les critères sont remplis et la décision journalisée.
- Aucune assurance n'est affichée comme active sans police `ACTIVE`.

### 8.5 Phase 3 — Gouvernance

**Lot 3.1 — Rôles et permissions.**
- `ProfilAdmin` ou groupes Django.
- Permissions par rôle.
- Tests d'accès non autorisé.

**Lot 3.2 — Double validation et audit.**
- `ValidationSensible`, `JournalAudit`.
- Statuts de décaissement et remboursement.
- Journal append-only, écran admin.
- Tests : `tests/test_securite.py`, `tests/test_administration.py`.

**Lot 3.3 — Données personnelles.**
- `Consentement`, `DemandeDroits`, `PolitiqueConservation`.
- Écran « Mes données », export, suppression.
- Tâche d'effacement automatique.
- Tests : nouveau `tests/test_donnees.py`.

**Lot 3.4 — Tableau de bord de confiance.**
- 9 indicateurs, filtres, export.
- Tests : nouveau `tests/test_confiance.py`.

**Critères d'acceptation Phase 3.**
- Un décaissement > 500 000 FCFA exige deux validateurs distincts.
- Un remboursement > 100 000 FCFA exige deux validateurs distincts.
- Le journal ne peut pas être modifié ni supprimé via l'API.
- L'export « Mes données » contient les données de l'utilisateur.
- La suppression de compte anonymise ce qui doit l'être et conserve ce qui doit l'être.
- Le tableau de bord affiche les 9 indicateurs.

### 8.6 Phase 4 — Partenaires et pilote

- Sélectionner le prestataire de paiement, l'assureur, le notaire, la logistique, l'hébergement.
- Signer les contrats ou les lettres d'intention.
- Configurer les statuts réels (police `ACTIVE`, contrat `CERTIFIE`, paiement non simulé).
- Pilote : 5 OAG vérifiés, 10 Offres d'achat, 100 acheteurs.
- Mesurer : offres abouties, livraison à temps, réclamations, remboursements, rétention.
- Rapport de pilote et décision de passage à l'échelle.

### 8.7 Tests et qualité

- La suite existante doit rester verte. Elle compte environ 295 tests ; exécuter `python -m pytest` avant et après chaque lot.
- Tests à ajouter : points/grades, Contact Privé, médias, OTP, réclamations, KYC, badges, assurance, rôles, audit, données, confiance.
- Tests de permissions : chaque route admin doit refuser un rôle non habilité.
- Tests de mentions : aucun écran ne doit afficher « assuré » sans police active, ni « certifié » sans contrat certifié.
- Tests de non-régression sur le QR et le scan.

### 8.8 Documentation à aligner

| Document | Mise à jour |
|---|---|
| `CAHIER_DES_CHARGES.md` | Remplacé par `CAHIER_DES_CHARGES_V2.md` après validation ; garder un lien vers l'ancien. |
| `MANUEL_EXPLOITATION.md` | 1 500 → 2 000 FCFA, 3,5/2,5/1,3 → 4/3/2, 60/150 → 100, réclamations, rôles, données. |
| `CLAUDE.md` | Ajouter les décisions v2 et le renvoi vers ce document. |
| `README.md` | Comptes de démonstration, barème, médias, réclamations. |
| `charger_demo.py` | Barème, commissions, polices `A_SOUSCRIRE`, réclamations, badges. |
| `VERSION_DEMO` | Incrémenter dès que le jeu change. |

### 8.9 Définition de « terminé »

Un lot est terminé quand :

1. le comportement est couvert par un test qui échoue avant et passe après ;
2. la suite complète est verte ;
3. l'interface affiche le bon libellé et le bon statut de réalité ;
4. la documentation associée est mise à jour ;
5. le jeu de démonstration montre le cas nominal et au moins un cas limite ;
6. aucune donnée personnelle supplémentaire n'est exposée.

---

## 9. Points ouverts et recommandations

| ID | Question | Options | Recommandation | Bloque |
|---|---|---|---|---|
| **P-01** | Un OAG débute à 0 point ; le document fixe Bronze à 250. | A) Palier Nouveau 0–249, Bronze 250. B) Bronze à 0, 250 = Bronze confirmé. | **A**, avec commission identique Nouveau/Bronze. | Phase 1 |
| **P-02** | Les groupages aboutis rapportent-ils des points ? | A) Grade par points ou par offres terminées (5/15/30). B) Rétablir 10 points par groupage. C) Garder 0 point. | **A** : le barème reste strict, la fiabilité compte. | Phase 1 |
| **P-03** | Les 50 points du Contact Privé sont-ils débités ? | A) Seuil d'éligibilité, non débité. B) Dépense de 50 points. | **A** : le document parle de « minimum », pas de prix. | Phase 1 |
| **P-04** | Mécanisme de la réduction de livraison. | A) Bon nominatif, remboursement à l'agence. B) Remise agence. C) Avoir. | **A**, plafonné, après signature du partenaire. | Phase 1 / 2 |
| **P-05** | Un ou deux OTP ? | A) Deux codes distincts (achat, remise). B) Un seul code non consommé à l'achat. | **A** : plus sûr et plus clair. | Phase 2 |
| **P-06** | Commission et remboursement après décaissement. | A) Commission acquise, remboursement sur fonds de garantie. B) Reprise de commission. C) Recouvrement. | **A**, avec journal et décision direction. | Phase 2 / 3 |
| **P-07** | Quand afficher « assurance active » ? | A) Seulement si police `ACTIVE` et partenaire signé. B) Dès la promesse commerciale. | **A** : jamais de promesse non couverte. | Phase 1 |
| **P-08** | Valeur juridique de l'acceptation en ligne du contrat. | A) Signature électronique à valider. B) Signature manuscrite + certification. | **A** en attendant l'avis du juriste ; afficher « en cours de validation ». | Phase 2 |
| **P-09** | Seuil de double validation. | A) 500 000 décaissement / 100 000 remboursement. B) Autre. | **A**, paramétrable. | Phase 3 |
| **P-10** | Durées de conservation. | Voir 4.12.3. | Valider avec juriste/IPDCP ; paramétrer. | Phase 3 |
| **P-11** | Photos de campagne : 3 ou 5 ? | A) 3, alignées sur l'article. B) 5, comme aujourd'hui. | **A** : cohérence et sobriété. | Phase 1 |
| **P-12** | Renommer `Campagne` et `groupeur` dans le code ? | A) Non, UI seulement. B) Oui, renommage complet. | **A** : coût élevé, gain faible. | Phase 1 |
| **P-13** | Confirmer que le ticket 100/10 n'est pas retenu. | A) Non retenu. B) Ajouté en plus. | **A** : décision D-02. | Phase 1 |
| **P-14** | Seuils des badges. | Voir 4.10.2. | À valider avec les premières données du pilote. | Phase 2 |
| **P-15** | Jours ouvrés et fériés. | A) Jours calendaires avec marge. B) Jours ouvrés avec table de fériés. | **B** à terme ; **A** au pilote. | Phase 2 |
| **P-16** | Mentions de simulation. | A) Bandeau permanent en mode démo. B) Mention au cas par cas. | **A** : un bandeau global + mentions ciblées. | Phase 1 |

---

## 10. Annexes

### 10.1 Barème et commissions

| Élément | Valeur |
|---|---:|
| Achat payé | 5 points |
| Parrainage validé | 2 points |
| Contact Privé payé | 10 points |
| Groupage abouti | 0 point (à rouvrir) |
| Abonnement publication | 10 points/mois |
| Pack publication | 2 points, une fois |
| Contact Privé | 2 000 FCFA/mois |
| Abonnement publication | 2 000 FCFA/mois |
| Pack publication | 500 FCFA/5 |
| Commission Nouveau/Bronze | 4 % |
| Commission Argent | 3 % |
| Commission Or | 2 % |
| Seuil Contact Privé | 50 points cumulés |
| Seuil réduction livraison | 100 points cumulés |
| Réduction livraison | 50 %, une fois |

### 10.2 Statuts

**Participation.** `EN_ATTENTE_PAIEMENT`, `PAYEE`, `PRETE`, `RETIREE`, `REMBOURSEE`, `ANNULEE`.

**Campagne.** `BROUILLON`, `EN_VERIFICATION`, `EN_COURS`, `MINIMUM_NON_ATTEINT`, `FINANCEE`, `DECAISSEE`, `APPROVISIONNEMENT`, `DISTRIBUTION`, `TERMINEE`, `ANNULEE`.

**Réclamation.** `OUVERTE`, `ACCUSE_RECEPTION`, `CONTRADICTOIRE`, `ANALYSE`, `DECISION`, `RECOURS`, `CLOTUREE`, `ANNULEE`.

**Remboursement.** `A_APPROUVER`, `APPROUVE`, `EXECUTE`, `REFUSE`, `ECHOUE`.

**KYC.** `CANDIDATURE`, `VERIFICATION`, `ENTRETIEN`, `FORMATION`, `SIGNATURE`, `OBSERVATION`, `VALIDE`, `REJETE`, `SUSPENDU`.

**Contrat OAG.** `MODELE`, `ACCEPTE_EN_LIGNE`, `SIGNE`, `CERTIFIE`, `RESILIE`.

**Police.** `A_SOUSCRIRE`, `ACTIVE`, `EXPIREE`, `ANNULEE`.

**Décaissement.** `DEMANDE`, `A_APPROUVER`, `APPROUVE`, `EXECUTE`, `REFUSE`.

### 10.3 Délais cibles

| Action | Cible |
|---|---|
| Accusé de réception d'une réclamation | 24 heures ouvrées |
| Première analyse | 2 jours ouvrés |
| Réponse de l'OAG | 2 jours ouvrés |
| Cas simple | 3 à 5 jours ouvrés |
| Cas complexe | jusqu'à 10 jours ouvrés |
| Vérification d'une Offre d'achat Bronze | 24 heures ouvrées |
| Retrait d'un colis | 14 jours recommandés |

### 10.4 Checklist conformité IPDCP

- [ ] Registre des traitements.
- [ ] Cartographie des flux et des sous-traitants.
- [ ] Politique de conservation et de suppression.
- [ ] Procédure de gestion des demandes des personnes.
- [ ] Procédure de gestion des violations de données.
- [ ] Analyse des risques, analyse d'impact si nécessaire.
- [ ] Contrats de sous-traitance et clauses de confidentialité.
- [ ] Politique d'accès aux dossiers KYC et aux conversations signalées.
- [ ] Consentement à l'inscription, versionné.
- [ ] Export et suppression des données.
- [ ] Durées validées par un juriste.
- [ ] Formalités auprès de l'IPDCP engagées.

### 10.5 Checklist avant pilote

- [ ] 5 OAG vérifiés, contrats acceptés, badges attribués.
- [ ] 10 Offres d'achat testées, dont une non aboutie.
- [ ] 100 acheteurs, dont 10 avec réclamation.
- [ ] Paiement traçable à 100 %, même simulé.
- [ ] QR et OTP testés, y compris le cas de panne du QR.
- [ ] Réclamation testée de bout en bout, avec remboursement.
- [ ] Aucune promesse d'assurance non couverte.
- [ ] Journal d'audit actif.
- [ ] Double validation testée.
- [ ] Export de données testé.
- [ ] Sauvegarde et restauration testées.
- [ ] Mentions de simulation affichées.
- [ ] Documents juridiques validés par le juriste.

### 10.6 Journal des modifications

| Date | Version | Modification |
|---|---|---|
| 6 novembre 2026 | 0.1 | Première rédaction à partir du nouveau cahier des charges et des décisions du fondateur. |
