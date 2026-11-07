# -*- coding: utf-8 -*-
"""Importe l'intégralité des 19 photos de photoproduit/ comme 19 produits et campagnes distincts."""
import os
import shutil
from datetime import timedelta

os.environ["DJANGO_FORCER_SQLITE"] = "1"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.core.files import File
from django.utils import timezone
from groupachat.catalogue.models import Categorie, Produit, MediaProduit, Campagne, PalierPrix
from groupachat.commandes.models import Participation
from groupachat.comptes.models import Utilisateur
from groupachat.paiements.services import encaisser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTO_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "photoproduit"))
MEDIA_PROD_DIR = os.path.join(BASE_DIR, "medias", "produits")
PUBLIC_IMG_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "boutique", "public", "images", "produits"))

os.makedirs(MEDIA_PROD_DIR, exist_ok=True)
os.makedirs(PUBLIC_IMG_DIR, exist_ok=True)

PRODUITS_19 = [
    {
        "fichier_source": "07a2ca982a422d93fe0838333e93ce39.jpg",
        "fichier_nom": "riz_royal_basmati_sac.jpg",
        "nom": "Riz Royal Basmati 20 lb (9.08 kg) en Toile de Jute",
        "marque": "Royal",
        "categorie": "Alimentation",
        "description": "Riz Basmati authentique grain extra long, sac traditionnel en toile de jute avec poignée et fermeture zip. Parfum délicat et cuisson légère non collante.",
        "caracteristiques": {"Poids": "9.08 kg (20 lb)", "Conditionnement": "Sac jute zippé", "Origine": "Inde"},
        "prix": 14500,
        "minimum": 15,
        "jours": 10,
        "paliers": [(5, 0, 13500), (1, 10, 13900), (5, 10, 12800)],
        "parts": (3, 2, 4, 2)
    },
    {
        "fichier_source": "3724a1e3838c06473d3f5a4f0b370369.jpg",
        "fichier_nom": "riz_royal_basmati_packshot.jpg",
        "nom": "Riz Royal Basmati Extra Long Grain Qualité Supérieure",
        "marque": "Royal",
        "categorie": "Alimentation",
        "description": "Riz Basmati blanc vieilli pour une saveur optimale. Idéal pour les grandes occasions, réceptions et consommation familiale quotidienne.",
        "caracteristiques": {"Poids": "9.08 kg", "Variété": "Basmati blanc", "Qualité": "Grade A"},
        "prix": 14500,
        "minimum": 12,
        "jours": 12,
        "paliers": [(4, 0, 13800), (1, 8, 14000), (4, 8, 13000)],
        "parts": (2, 3, 2, 1)
    },
    {
        "fichier_source": "d33b8816465e0ab9095513abb95b3755.jpg",
        "fichier_nom": "huile_lesieur_3l.jpg",
        "nom": "Huile Végétale Pure Lesieur 3 Litres (0% Cholestérol)",
        "marque": "Lesieur",
        "categorie": "Alimentation",
        "description": "Huile végétale 100% pure enrichie en vitamine A, garantie sans cholestérol. Bidon ergonomique de 3L avec bouchon verseur antigoutte.",
        "caracteristiques": {"Volume": "3 Litres", "Composition": "Huile végétale pure", "Santé": "0% Cholestérol"},
        "prix": 4800,
        "minimum": 20,
        "jours": 7,
        "paliers": [(4, 0, 4400), (1, 12, 4500), (4, 12, 4100)],
        "parts": (4, 4, 3, 2)
    },
    {
        "fichier_source": "4793e0d4d5f9b1463434ccded56e8dae.jpg",
        "fichier_nom": "tomate_gino_2_2kg.jpg",
        "nom": "Double Concentré de Tomate Gino 2.2 kg Format Économique",
        "marque": "Gino",
        "categorie": "Alimentation",
        "description": "Pur concentré de tomates savoureuses et mûres, texture onctueuse et couleur rouge vive. Grande boîte métallique de 2.2 kg pour traiteurs et familles.",
        "caracteristiques": {"Poids net": "2.2 kg", "Type": "Double concentré 28-30%", "Origine": "Gino International"},
        "prix": 3900,
        "minimum": 18,
        "jours": 8,
        "paliers": [(3, 0, 3600), (1, 10, 3700), (3, 10, 3350)],
        "parts": (3, 3, 2, 2)
    },
    {
        "fichier_source": "b1cf8feca334fb9172d8fe00adbccae9.jpg",
        "fichier_nom": "hp_pc_portables_pile.jpg",
        "nom": "PC Portable HP EliteBook Core i5 8Go RAM SSD 256Go",
        "marque": "HP",
        "categorie": "Électronique",
        "description": "Ordinateur portable professionnel HP EliteBook, châssis aluminium robuste. Processeur Intel Core i5, 8 Go de mémoire vive et SSD 256 Go haute vitesse.",
        "caracteristiques": {"Processeur": "Intel Core i5", "RAM": "8 Go DDR4", "Stockage": "256 Go SSD", "Écran": "14 pouces HD"},
        "prix": 165000,
        "minimum": 6,
        "jours": 14,
        "paliers": [(2, 0, 155000), (1, 4, 158000), (2, 4, 149000)],
        "parts": (1, 2, 1)
    },
    {
        "fichier_source": "cd6bbfe936ddf60947522a459c3f29b9.jpg",
        "fichier_nom": "hp_pc_portables_stock.jpg",
        "nom": "Lot PC Portables HP ProBook — Stock Entreprises & Écoles",
        "marque": "HP",
        "categorie": "Électronique",
        "description": "Arrivage direct conteneur PC portables HP ProBook. Matériel vérifié avec batterie neuve, chargeur d'origine et garantie échange 6 mois.",
        "caracteristiques": {"Marque": "HP", "Garantie": "6 mois échange standard", "État": "Reconditionné Grade A+"},
        "prix": 155000,
        "minimum": 8,
        "jours": 15,
        "paliers": [(2, 0, 145000), (1, 5, 148000), (2, 5, 139000)],
        "parts": (2, 1, 1, 1)
    },
    {
        "fichier_source": "16c132e0975af740105b0eda471685ee.jpg",
        "fichier_nom": "dji_osmo_pocket3_boite.jpg",
        "nom": "Caméra DJI Osmo Pocket 3 Gimbal 4K 120fps (Coffret Neuf)",
        "marque": "DJI",
        "categorie": "Électronique",
        "description": "Caméra stabilisée de poche capteur 1 pouce avec nacelle 3 axes. Enregistrement vidéo 4K/120fps, écran tactile OLED rotatif 2 pouces.",
        "caracteristiques": {"Capteur": "CMOS 1 pouce", "Vidéo": "4K 120fps", "Écran": "Tactile OLED 2\"", "Stabilisation": "Mécanique 3 axes"},
        "prix": 380000,
        "minimum": 4,
        "jours": 12,
        "paliers": [(1, 3, 365000), (2, 3, 350000)],
        "parts": (1, 1)
    },
    {
        "fichier_source": "9c4e3b13d387e2f484031363ea11ee32.jpg",
        "fichier_nom": "dji_osmo_pocket3_action.jpg",
        "nom": "DJI Osmo Pocket 3 Pack Vlogging & Créateurs de Contenu",
        "marque": "DJI",
        "categorie": "Électronique",
        "description": "La référence ultime pour vloggers, créateurs TikTok et journalistes mobiles. Suivi de sujet ActiveTrack 6.0 et micros stéréo omnidirectionnels intégrés.",
        "caracteristiques": {"Autonomie": "166 minutes", "Mise au point": "Tous pixels rapide", "Connectivité": "WiFi & Bluetooth"},
        "prix": 395000,
        "minimum": 3,
        "jours": 14,
        "paliers": [(1, 2, 380000), (2, 2, 365000)],
        "parts": (1, 1)
    },
    {
        "fichier_source": "5004e95f81192a58271b2b0d5d765147.jpg",
        "fichier_nom": "smart_portable_tv_roulettes.jpg",
        "nom": "Smart TV Tactile Mobile 32\" sur Pied à Roulettes",
        "marque": "SmartLife",
        "categorie": "Électronique",
        "description": "Écran connecté mobile façon StanbyME, monté sur un pied télescopique avec 5 roulettes silencieuses. Écran tactile 32 pouces Full HD avec batterie rechargeable intégrée.",
        "caracteristiques": {"Taille": "32 pouces tactile", "Résolution": "Full HD 1080p", "Batterie": "4 heures sans fil", "Système": "Android TV"},
        "prix": 295000,
        "minimum": 5,
        "jours": 15,
        "paliers": [(1, 3, 280000), (2, 3, 269000)],
        "parts": (1, 1, 1)
    },
    {
        "fichier_source": "a4a0f9492a7dc9ef5896f12aa032ab31.jpg",
        "fichier_nom": "smart_portable_tv_rotatif.jpg",
        "nom": "Écran Connecté Portable StanbyME 32\" Pivotant Portrait/Paysage",
        "marque": "SmartLife",
        "categorie": "Électronique",
        "description": "Basculez facilement du format cinéma horizontal au format vertical TikTok/Reels grâce à l'écran rotatif à 90°. Idéal pour salon, chambre, visioconférence et cuisine.",
        "caracteristiques": {"Rotation": "90° portrait/paysage", "Connectivité": "WiFi, HDMI, Bluetooth", "Enceintes": "Stéréo intégrées"},
        "prix": 310000,
        "minimum": 4,
        "jours": 16,
        "paliers": [(1, 3, 295000), (2, 3, 285000)],
        "parts": (1, 1)
    },
    {
        "fichier_source": "26b52454f6d99f8e89e89b0845015fe4.jpg",
        "fichier_nom": "stanley_tumbler_vert.jpg",
        "nom": "Gourde Isotherme Stanley Quencher H2.0 1.18L — Vert Sauge",
        "marque": "Stanley",
        "categorie": "Maison",
        "description": "Le tumbler isotherme mondialement célèbre. Acier inoxydable recyclé 90%, couvercle FlowState 3 positions et paille réutilisable. Boissons glacées 48h.",
        "caracteristiques": {"Contenance": "1.18 Litre (40 oz)", "Couleur": "Vert sauge pastel", "Matière": "Acier inox double paroi"},
        "prix": 16500,
        "minimum": 15,
        "jours": 10,
        "paliers": [(3, 0, 15000), (1, 10, 15500), (3, 10, 14200)],
        "parts": (3, 2, 3, 2)
    },
    {
        "fichier_source": "75404d358fb885e3f4981de938e7166e.jpg",
        "fichier_nom": "stanley_tumbler_rose.jpg",
        "nom": "Gourde Isotherme Stanley Quencher FlowState 1.18L — Rose Lilas",
        "marque": "Stanley",
        "categorie": "Maison",
        "description": "Finition mate soft touch rose lilas, poignée ergonomique renforcée et base effilée compatible porte-gobelet de voiture.",
        "caracteristiques": {"Contenance": "1.18 L", "Couleur": "Rose lilas poudré", "Performance": "Froid 48h / Chaud 7h"},
        "prix": 16500,
        "minimum": 15,
        "jours": 10,
        "paliers": [(3, 0, 15000), (1, 10, 15500), (3, 10, 14200)],
        "parts": (2, 2, 3, 1)
    },
    {
        "fichier_source": "468071eb25177df5b2317cec743f7487.jpg",
        "fichier_nom": "stanley_tumbler_couleurs.jpg",
        "nom": "Collection Gourdes Isothermes Stanley Tumbler Multicolores",
        "marque": "Stanley",
        "categorie": "Maison",
        "description": "Choisissez votre couleur préférée à la commande parmi la collection exclusive Stanley : blanc perle, rose, noir mat, bleu nuit ou vert forêt.",
        "caracteristiques": {"Choix": "Coloris au choix", "Inclus": "Paille + couvercle hermétique", "Capacité": "1.18L"},
        "prix": 17000,
        "minimum": 18,
        "jours": 11,
        "paliers": [(3, 0, 15500), (1, 12, 16000), (3, 12, 14500)],
        "parts": (3, 3, 2, 2)
    },
    {
        "fichier_source": "a158c7c20c3712ea011e7d59b530ddcb.jpg",
        "fichier_nom": "ultrapods_pro_transparent.jpg",
        "nom": "Écouteurs sans fil Ultrapods Pro Boîtier Crystal LED (Noir)",
        "marque": "Ultrapods",
        "categorie": "Électronique",
        "description": "Écouteurs sans fil avec coque transparente crystal et affichage LED numérique du pourcentage de charge restante. Bluetooth 5.3 ultra réactif.",
        "caracteristiques": {"Autonomie": "30h totale", "Affichage": "LED numérique", "Connectivité": "Bluetooth 5.3"},
        "prix": 8500,
        "minimum": 25,
        "jours": 8,
        "paliers": [(5, 0, 7500), (1, 15, 7800), (5, 15, 6900)],
        "parts": (5, 4, 3, 3)
    },
    {
        "fichier_source": "fa4c24e621f6dd12be4ec18f96a078ef.jpg",
        "fichier_nom": "ultrapods_pro_couleurs.jpg",
        "nom": "Écouteurs Bluetooth Ultrapods Pro — 4 Coloris Pastel & Écran LED",
        "marque": "Ultrapods",
        "categorie": "Électronique",
        "description": "Déclinaisons tendance : Noir Crystal, Blanc Pur, Bleu Ciel Pastel et Vert Fluo Néon. Son stéréo Hi-Fi immersif et commandes tactiles.",
        "caracteristiques": {"Couleurs": "4 teintes disponibles", "Recharge": "USB-C rapide", "Son": "Stéréo Hi-Fi"},
        "prix": 8500,
        "minimum": 30,
        "jours": 9,
        "paliers": [(5, 0, 7500), (1, 15, 7800), (5, 15, 6900)],
        "parts": (6, 5, 4, 2)
    },
    {
        "fichier_source": "5cb71ece3a9bba64f7acb4bb51e689dd.jpg",
        "fichier_nom": "fauteuil_oeuf_suspendu.jpg",
        "nom": "Fauteuil Cocon Suspendu Œuf en Rotin Tressé avec Coussin",
        "marque": "HomeDéco",
        "categorie": "Maison",
        "description": "Structure acier haute résistance antirouille et tressage soigné en rotin synthétique traité UV. Livré avec son coussin moelleux et chaîne d'accroche.",
        "caracteristiques": {"Charge max": "150 kg", "Usage": "Intérieur / Balcon / Terrasse", "Inclus": "Chaîne + coussin"},
        "prix": 95000,
        "minimum": 6,
        "jours": 16,
        "paliers": [(1, 4, 88000), (2, 4, 83000)],
        "parts": (1, 1, 1)
    },
    {
        "fichier_source": "70d5070697bc5b9bb0879f764ca4454c.jpg",
        "fichier_nom": "chaise_gaming_dowinx.jpg",
        "nom": "Chaise Gaming Ergonomique Dowinx avec Massage Lombaire USB",
        "marque": "Dowinx",
        "categorie": "Maison",
        "description": "Fauteuil ergonomique pour gamers et professionnels du bureau. Coussin vibrant massant par USB, dossier inclinable à 170° et repose-pieds rétractable.",
        "caracteristiques": {"Massage": "Lombaire vibrant USB", "Inclinaison": "170° verrouillable", "Repose-pieds": "Intégré escamotable"},
        "prix": 88000,
        "minimum": 8,
        "jours": 12,
        "paliers": [(2, 0, 82000), (1, 5, 84000), (2, 5, 78000)],
        "parts": (1, 2, 1)
    },
    {
        "fichier_source": "00f42579321b5272f3b13793dd89b1fd.jpg",
        "fichier_nom": "sac_luofanni_noir.jpg",
        "nom": "Sac à Dos Luofanni Urbain Imperméable (Noir Élégant)",
        "marque": "Luofanni",
        "categorie": "Mode",
        "description": "Sac à dos tendance antivol en tissu Oxford déperlant résistant aux intempéries. Nombreuses poches astucieuses et porte-clé peluche offert.",
        "caracteristiques": {"Matière": "Tissu Oxford imperméable", "Couleur": "Noir classique", "Inclus": "Peluche porte-clé"},
        "prix": 12500,
        "minimum": 20,
        "jours": 9,
        "paliers": [(3, 0, 11000), (1, 12, 11500), (3, 12, 10200)],
        "parts": (3, 3, 2, 2)
    },
    {
        "fichier_source": "5bf680b308d9dcf8acae3d1043813566.jpg",
        "fichier_nom": "sac_luofanni_marron.jpg",
        "nom": "Sac à Dos Luofanni Haute Densité (Marron Chocolat)",
        "marque": "Luofanni",
        "categorie": "Mode",
        "description": "Superbe finition marron chocolat café. Idéal pour cours, bureau et sorties en ville. Bretelles rembourrées confortables et porte-clé peluche inclus.",
        "caracteristiques": {"Matière": "Oxford déperlant", "Couleur": "Marron chocolat", "Compartiments": "Multi-poches zippées"},
        "prix": 12500,
        "minimum": 20,
        "jours": 10,
        "paliers": [(3, 0, 11000), (1, 12, 11500), (3, 12, 10200)],
        "parts": (3, 2, 3, 2)
    },
]

def main():
    print("Demarrage de l'importation complete des 19 produits reels...")

    oag = Utilisateur.objects.filter(telephone="90001122").first()
    if not oag:
        oag = Utilisateur.objects.filter(role="groupeur").first()
    if not oag:
        oag = Utilisateur.objects.first()

    acheteurs = list(Utilisateur.objects.exclude(pk=oag.pk)[:5])
    if not acheteurs:
        acheteurs = [oag]

    # Archiver les anciennes campagnes sans média pour que les 19 vrais produits soient en tête
    anciennes = Campagne.objects.filter(produit__medias__isnull=True).exclude(statut=Campagne.Statut.TERMINEE)
    count_anciennes = anciennes.count()
    anciennes.update(statut=Campagne.Statut.TERMINEE)
    print(f"Archivage de {count_anciennes} anciennes campagnes sans photo.")

    for i, cfg in enumerate(PRODUITS_19, start=1):
        cat, _ = Categorie.objects.get_or_create(
            nom=cfg["categorie"],
            defaults={"icone": "panier", "ordre": 1}
        )

        src_path = os.path.join(PHOTO_DIR, cfg["fichier_source"])
        dst_media = os.path.join(MEDIA_PROD_DIR, cfg["fichier_nom"])
        dst_public = os.path.join(PUBLIC_IMG_DIR, cfg["fichier_nom"])

        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_media)
            shutil.copy2(src_path, dst_public)

        produit, _ = Produit.objects.get_or_create(
            nom=cfg["nom"],
            defaults={
                "marque": cfg["marque"],
                "categorie": cat,
                "description": cfg["description"],
                "caracteristiques": cfg["caracteristiques"],
                "propose_par": oag
            }
        )
        produit.marque = cfg["marque"]
        produit.description = cfg["description"]
        produit.caracteristiques = cfg["caracteristiques"]
        produit.categorie = cat
        produit.save()

        # Supprimer les anciens médias
        produit.medias.all().delete()

        # Attacher la photo principale
        if os.path.exists(dst_media):
            with open(dst_media, "rb") as f:
                m = MediaProduit.objects.create(
                    produit=produit,
                    genre=MediaProduit.Genre.IMAGE,
                    legende=cfg["nom"],
                    ordre=0
                )
                m.fichier.save(cfg["fichier_nom"], File(f), save=True)

        # Créer la campagne
        campagne = Campagne.objects.filter(produit=produit).first()
        if not campagne:
            campagne = Campagne.objects.create(
                produit=produit,
                groupeur=oag,
                titre=f"{cfg['nom']} — Offre Groupée",
                description=f"Groupage officiel certifié par {oag.nom_public}. Livraison express Lomé et retrait points relais sécurisés.",
                prix_unitaire=cfg["prix"],
                quantite_minimale=cfg["minimum"],
                date_limite=timezone.now() + timedelta(days=cfg["jours"]),
                statut=Campagne.Statut.EN_COURS,
                publiee_le=timezone.now()
            )

            for acheteur, quantite in zip(acheteurs, cfg["parts"]):
                prix = campagne.prix_unitaire
                p = Participation.objects.create(
                    campagne=campagne,
                    acheteur=acheteur,
                    quantite=quantite,
                    prix_unitaire_applique=prix,
                    montant_total=prix * quantite,
                    mode_retrait=Participation.ModeRetrait.POSTE,
                    bureau_poste="Bureau de poste Tokoin"
                )
                encaisser(p, operateur="tmoney", numero=acheteur.telephone)

        print(f"[{i}/19] {cfg['nom']} OK (photo: {cfg['fichier_nom']})")

    print("\nSUCCES : Les 19 produits et leurs 19 photos sont tous actifs et en ligne !")

if __name__ == "__main__":
    main()
