---
type: recette
statut: terminée
date: 2026-10-26
tags: [recette, M-001]
---

# Recette du MVP — état des lieux (T1)

Mission : [[M-001-terminer-le-mvp]] · Backlog : [[backlog]] · Failles : [[2026-10-26-recette-failles]]

---
RECETTE DU MVP (T1, M-001) : 7 fonctionnalités OK, 9 KO, 11 OK avec réserves. Aucun fichier de code ni de git touché.

Méthode : 165 tests pytest verts et tous collectés ; tsc --noEmit et build Vite OK ; runserver sur SQLite jetable + charger_demo, scénarios rejoués par rôle ; Playwright à 390 px sur le build servi par Django ; console admin non jouée en navigateur.

Pannes bloquantes :
1. F-030 pièces KYC lisibles sans compte : GET /medias/x/%2e%2e/kyc/<fichier> → 200 anonyme, même DJANGO_DEBUG=0. L'expression `^medias/(?!kyc/)` laisse passer `x/..`, `media_publique` (config/service/fichiers.py:34-36) ne teste que Path(chemin).parts[0], serve() normalise ensuite. En DEBUG=1, `static(MEDIA_URL…)` dans config/urls.py sert /medias/kyc/<fichier> directement. Nom de fichier d'origine, devinable. Aucun test.
2. F-010/F-021 : AvisVueEnsemble est un ModelViewSet gardé par LectureLibreEcritureVerifiee seulement. Un autre acheteur a changé la note d'un avis (3→1) puis l'a supprimé (204) ; le groupeur concerné a modifié puis supprimé l'avis qui le vise ; un acheteur sans participation a supprimé un avis. Réputation manipulable. Aucun test.
3. F-016/F-017/F-024 double paiement : groupeur demande le retrait d'une campagne financee puis l'annule ; acheteurs remboursés (475 000) ; l'admin exécute ensuite le décaissement en attente. executer_decaissement ne vérifie ni le statut de la campagne ni le solde. 475 000 remboursés + 473 500 versés. Campagne repasse de annulee à approvisionnement. Pas de contrainte en base (C-006).
4. F-005 à 390 px : bouton « Participer » (FicheCampagne.tsx:515, z-30) recouvert par la barre d'onglets (z-40) ; seuls 8 px touchables. OK ≥ 768 px.
5. F-016 : /api/api/groupeur/campagnes/<id>/maintenir/ → 404, affiché « Connexion impossible ». Seules occurrences : CampagneGroupeur.tsx:70 et :74.
6. F-008 : liens /participations/<id> → 404 (connu).
7. F-011 : l'écran n'envoie aucune pièce ; le serveur accepte le multipart et garde l'accès (connu).

Gênes : F-005 confirmation de paiement jamais affichée (recharger() remplace la page par un squelette, bouton « Voir mon QR » absent) ; F-017/F-019 même mécanisme (feuille « Demande enregistrée », bannière « Colis remis à X » perdues) ; F-017 bouton « Demander le retrait » reste affiché ; F-009 reponse_a accepte un message d'une autre campagne (201), commentaire sur le brouillon d'autrui (201 + notification), campagne inexistante → 500 (Campagne.objects.get dans perform_create) ; F-001 page_size=24 ignoré, aucune pagination écran (au-delà de 20 invisible), /catalogue?groupeur=id non lu par Catalogue.tsx ; F-005 prix affiché prix_courant × quantité alors que le serveur applique le palier atteint (35 000 affichés, 32 000 facturés) ; paiement en deux temps : part en attente bloquante si échec (F-043) ; F-018 mettre_a_disposition accepte financee (fonds jamais libérés) ; F-013 quantite_minimale=0 et prix 0 acceptés, produit orphelin si la création de campagne échoue ; Mes achats et Notifications affichent une erreur comme un état vide.

Cosmétique : part retirée/remboursée affiche « Ce code deviendra actif… » ; « n'a pas atteint son minimum » faux pour une annulation depuis en_cours/financee ; notification « Remboursement effectué » lien vide ; « Minimum atteint » renvoyé à chaque paiement au-delà ; tableau de bord admin ne compte pas approvisionnement, distribution, minimum_non_atteint ; textes C-009.

Verdicts : F-001 OK (réserve pagination) ; F-002 OK serveur ; F-003 OK serveur ; F-004 OK (réserve « Ses campagnes ») ; F-005 KO ; F-006 OK ; F-007 OK ; F-009 KO (intégrité) ; F-010 KO ; F-012 OK ; F-013 OK (réserves) ; F-014 non vérifiable (503 sans CLOUDINARY_*, conforme Q11) ; F-015 OK ; F-017 OK avec réserves ; F-018 OK (réserve saut du décaissement) ; F-019 OK avec réserves ; F-020 OK ; F-021 KO (via F-010) ; F-022 OK ; F-023 OK (réserve F-011) ; F-024 KO ; F-025 non vérifiable en détail ; F-026 OK ; F-027 OK (planification Coolify non vérifiable) ; F-028 OK (idem) ; F-029 OK (réserve somme non plafonnée) ; F-030 KO. F-008, F-011, F-016, F-031 confiées à T2–T5.

Non vérifié : console admin en navigateur ; inscription/connexion/profil/espace groupeur en navigateur ; envoi réel Cloudinary ; planification Coolify et variables CLOUDINARY_* ; largeurs autres que 390/1280, thème sombre ; concurrence (double exécution simultanée d'un décaissement, pas de verrou).

Autres : InscriptionSerialiseur accepte role=groupeur (contraire Q12), sans effet d'accès ; piece_kyc n'autorise que est_equipe alors qu'EstAdministrateur accepte aussi role=administrateur.
---

## Note de l'archiviste (2026-10-26)

Les comptes de l'en-tête (7 OK / 11 avec réserves / 9 KO) ne correspondent pas à la liste « Verdicts » ci-dessus, qui donne sur les 27 fonctionnalités constatées : 11 OK (F-002, F-003, F-006, F-007, F-012, F-015, F-020, F-022, F-026, F-027, F-028), 8 OK avec réserves (F-001, F-004, F-013, F-017, F-018, F-019, F-023, F-029), 6 KO (F-005, F-009, F-010, F-021, F-024, F-030), 2 non vérifiables (F-014, F-025). Les trois KO hors liste (F-008, F-011, F-016) sont confiées à T2–T3. Le backlog suit la liste « Verdicts ». Les comptes sont à confirmer par l'auteur de la recette.

Tranché (2026-10-26, archiviste) : la liste « Verdicts » fait foi (11 OK, 8 avec réserves, 6 KO, 2 non vérifiables, soit 27). L'en-tête (7 / 11 / 9) est erroné ; M-001 et le backlog suivent la liste.
