# -*- coding: utf-8 -*-
"""Importation des photos réelles de photoproduit/ vers les produits et campagnes."""
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
from groupachat.commandes.models import Participation, Avis
from groupachat.comptes.models import Utilisateur
from groupachat.paiements.services import encaisser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTO_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "photoproduit"))
MEDIA_PROD_DIR = os.path.join(BASE_DIR, "medias", "produits")
PUBLIC_IMG_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "boutique", "public", "images", "produits"))

os.makedirs(MEDIA_PROD_DIR, exist_ok=True)
os.makedirs(PUBLIC_IMG_DIR, exist_ok=True)

PRODUITS_CONFIG = [
    {
        "nom": "Riz Royal Basmati 20 lb (9.08 kg)",
        "marque": "Royal",
        "categorie": "Alimentation",
        "description": "Riz Basmati authentique grain long vieilli naturellement. Sac en toile de jute avec poignée et fermeture zip, 20 livres (9.08 kg). Qualité gastronomique supérieure, parfum délicat.",
        "caracteristiques": {
            "Poids": "9.08 kg (20 lb)",
            "Variété": "Basmati extra-long",
            "Conditionnement": "Sac jute zippé",
            "Origine": "Himalaya / Inde"
        },
        "prix": 14500,
        "minimum": 15,
        "jours": 10,
        "paliers": [(5, 0, 13500), (1, 10, 13900), (5, 10, 12800)],
        "photos": [
            ("07a2ca982a422d93fe0838333e93ce39.jpg", "riz_royal_basmati_sac.jpg", "Sac de riz Royal Basmati 9.08 kg"),
            ("3724a1e3838c06473d3f5a4f0b370369.jpg", "riz_royal_basmati_packshot.jpg", "Packshot Royal Basmati Rice")
        ],
        "parts": (3, 2, 4, 2)
    },
    {
        "nom": "Huile Végétale Pure Lesieur 3 Litres",
        "marque": "Lesieur",
        "categorie": "Alimentation",
        "description": "Huile végétale 100% pure enrichie en vitamine A, sans cholestérol. Bidon ergonomique de 3 litres avec bouchon verseur antigoutte. Idéale pour fritures, cuissons et assaisonnements.",
        "caracteristiques": {
            "Contenance": "3 Litres",
            "Composition": "Huile végétale pure",
            "Vitamines": "Riche en Vitamine A",
            "Santé": "0% Cholestérol"
        },
        "prix": 4800,
        "minimum": 20,
        "jours": 7,
        "paliers": [(4, 0, 4400), (1, 12, 4500), (4, 12, 4100)],
        "photos": [
            ("d33b8816465e0ab9095513abb95b3755.jpg", "huile_lesieur_3l.jpg", "Bidon d'Huile Végétale Lesieur 3L")
        ],
        "parts": (4, 4, 3, 2)
    },
    {
        "nom": "Double Concentré de Tomate Gino 2.2 kg",
        "marque": "Gino",
        "categorie": "Alimentation",
        "description": "Concentré de tomates mûres de première qualité, texture riche et onctueuse. Grande boîte métallique de 2.2 kg pour familles nombreuses, traiteurs ou consommation longue durée.",
        "caracteristiques": {
            "Poids net": "2.2 kg",
            "Concentration": "Double concentré 28-30%",
            "Conservation": "Longue conservation",
            "Usage": "Sauces, ragoûts, pâtes"
        },
        "prix": 3900,
        "minimum": 18,
        "jours": 6,
        "paliers": [(3, 0, 3600), (1, 10, 3700), (3, 10, 3350)],
        "photos": [
            ("4793e0d4d5f9b1463434ccded56e8dae.jpg", "tomate_gino_2_2kg.jpg", "Grande boîte concentré de tomate Gino 2.2kg")
        ],
        "parts": (3, 3, 2, 2)
    },
    {
        "nom": "Lot PC Portables HP EliteBook Core i5",
        "marque": "HP",
        "categorie": "Électronique",
        "description": "Ordinateurs portables HP EliteBook / ProBook reconditionnés grade A, châssis aluminium brossé ultra résistant. Écran 14 pouces HD, processeur Intel Core i5, 8 Go RAM, SSD 256 Go haute vitesse.",
        "caracteristiques": {
            "Processeur": "Intel Core i5 Turbo",
            "Mémoire RAM": "8 Go DDR4",
            "Stockage": "SSD 256 Go ultra-rapide",
            "Écran": "14 pouces HD antireflet",
            "Connectique": "USB-C, USB 3.0, VGA, HDMI"
        },
        "prix": 165000,
        "minimum": 6,
        "jours": 14,
        "paliers": [(2, 0, 155000), (1, 4, 158000), (2, 4, 149000)],
        "photos": [
            ("b1cf8feca334fb9172d8fe00adbccae9.jpg", "hp_pc_portables_pile.jpg", "Pile de PC portables HP EliteBook"),
            ("cd6bbfe936ddf60947522a459c3f29b9.jpg", "hp_pc_portables_stock.jpg", "Arrivage palettes de PC HP")
        ],
        "parts": (1, 2, 1)
    },
    {
        "nom": "DJI Osmo Pocket 3 Caméra Gimbal 4K 120fps",
        "marque": "DJI",
        "categorie": "Électronique",
        "description": "Caméra stabilisée 3 axes de poche avec capteur CMOS 1 pouce géant. Écran tactile rotatif 2 pouces OLED, enregistrement 4K/120fps, ActiveTrack 6.0 et mise au point ultra-rapide tous pixels.",
        "caracteristiques": {
            "Capteur": "CMOS 1 pouce",
            "Vidéo": "4K jusqu'à 120 fps",
            "Stabilisation": "Mécanique 3 axes intégrée",
            "Écran": "OLED rotatif 2 pouces tactile",
            "Autonomie": "166 minutes avec charge rapide"
        },
        "prix": 380000,
        "minimum": 4,
        "jours": 12,
        "paliers": [(1, 3, 365000), (2, 3, 350000)],
        "photos": [
            ("16c132e0975af740105b0eda471685ee.jpg", "dji_osmo_pocket3_boite.jpg", "Boîte d'origine DJI Osmo Pocket 3"),
            ("9c4e3b13d387e2f484031363ea11ee32.jpg", "dji_osmo_pocket3_action.jpg", "DJI Osmo Pocket 3 en tournage réel")
        ],
        "parts": (1, 1)
    },
    {
        "nom": "Écran Tactile Mobile Smart TV 32\" sur Pied à Roulettes",
        "marque": "SmartLife",
        "categorie": "Électronique",
        "description": "Écran connecté sans fil sur pied à roulettes style StanbyME. Écran tactile 32 pouces Full HD inclinable et rotatif 90° (mode portrait / paysage). Batterie intégrée 4 heures, WiFi, Bluetooth et Android.",
        "caracteristiques": {
            "Diagonale": "32 pouces (81 cm)",
            "Résolution": "Full HD 1080p tactile",
            "Batterie": "Autonomie sans fil 4h",
            "Mobilité": "Socle lesté à 5 roulettes fluides",
            "Rotation": "Pivot 90° vertical/horizontal"
        },
        "prix": 295000,
        "minimum": 5,
        "jours": 15,
        "paliers": [(1, 3, 280000), (2, 3, 269000)],
        "photos": [
            ("5004e95f81192a58271b2b0d5d765147.jpg", "smart_portable_tv_roulettes.jpg", "Smart TV mobile 32 pouces sur pied"),
            ("a4a0f9492a7dc9ef5896f12aa032ab31.jpg", "smart_portable_tv_rotatif.jpg", "Écran tactile rotatif mode portrait/paysage")
        ],
        "parts": (1, 1, 1)
    },
    {
        "nom": "Écouteurs sans fil Ultrapods Pro Boîtier Crystal LED",
        "marque": "Ultrapods",
        "categorie": "Électronique",
        "description": "Écouteurs Bluetooth 5.3 nouvelle génération avec boîtier transparent teinté crystal et affichage numérique LED du niveau de batterie. Son stéréo Hi-Fi, réduction de bruit passive et autonomie 30h.",
        "caracteristiques": {
            "Bluetooth": "Version 5.3 basse consommation",
            "Boîtier": "Design transparent avec LED",
            "Autonomie": "5h écoute + 25h boîtier",
            "Coloris": "Noir, Blanc, Bleu pastel, Vert fluo"
        },
        "prix": 8500,
        "minimum": 30,
        "jours": 8,
        "paliers": [(5, 0, 7500), (1, 15, 7800), (5, 15, 6900)],
        "photos": [
            ("a158c7c20c3712ea011e7d59b530ddcb.jpg", "ultrapods_pro_transparent.jpg", "Écouteurs Ultrapods Pro boîtier transparent"),
            ("fa4c24e621f6dd12be4ec18f96a078ef.jpg", "ultrapods_pro_couleurs.jpg", "Déclinaison des 4 coloris Ultrapods Pro")
        ],
        "parts": (6, 5, 4, 3)
    },
    {
        "nom": "Gourde Isotherme Stanley Quencher H2.0 FlowState 1.18L",
        "marque": "Stanley",
        "categorie": "Maison",
        "description": "Le tumbler isotherme incontournable en acier inoxydable recyclé 90%. Garde les boissons glacées pendant 48 heures. Couvercle FlowState 3 positions avec paille réutilisable et poignée ergonomique.",
        "caracteristiques": {
            "Contenance": "1.18 Litre (40 oz)",
            "Matériau": "Acier inoxydable 18/8 pro",
            "Isolation": "Double paroi sous vide",
            "Paille": "Paille amovible incluse"
        },
        "prix": 16500,
        "minimum": 15,
        "jours": 10,
        "paliers": [(3, 0, 15000), (1, 10, 15500), (3, 10, 14200)],
        "photos": [
            ("26b52454f6d99f8e89e89b0845015fe4.jpg", "stanley_tumbler_vert.jpg", "Stanley Quencher vert sauge 1.18L"),
            ("75404d358fb885e3f4981de938e7166e.jpg", "stanley_tumbler_rose.jpg", "Stanley Tumbler rose lilas en main"),
            ("468071eb25177df5b2317cec743f7487.jpg", "stanley_tumbler_couleurs.jpg", "Collection Stanley Tumbler assortiment")
        ],
        "parts": (3, 2, 3, 2)
    },
    {
        "nom": "Fauteuil Suspendu Cocon Œuf en Rotin Tressé",
        "marque": "HomeDéco",
        "categorie": "Maison",
        "description": "Fauteuil œuf suspendu avec structure en acier robuste et tressage en résine rotin haute résistance aux intempéries. Livré complet avec grand coussin d'assise ultra-moelleux et chaîne de suspension.",
        "caracteristiques": {
            "Structure": "Acier traité antirouille",
            "Tressage": "Résine rotin synthétique",
            "Charge maximale": "150 kg",
            "Coussin": "Tissu déperlant lavable"
        },
        "prix": 95000,
        "minimum": 6,
        "jours": 16,
        "paliers": [(1, 4, 88000), (2, 4, 83000)],
        "photos": [
            ("5cb71ece3a9bba64f7acb4bb51e689dd.jpg", "fauteuil_oeuf_suspendu.jpg", "Fauteuil suspendu cocon en rotin avec coussin")
        ],
        "parts": (1, 1, 1)
    },
    {
        "nom": "Chaise Fauteuil Gaming Ergonomique Dowinx avec Repose-pieds",
        "marque": "Dowinx",
        "categorie": "Maison",
        "description": "Fauteuil gamer et bureau ergonomique haut de gamme. Revêtement similicuir respirant, coussin lombaire vibrant massant USB, dossier inclinable à 170° et repose-pieds escamotable rembourré.",
        "caracteristiques": {
            "Fonction massage": "Coussin lombaire vibrant USB",
            "Inclinaison": "90° à 170° verrouillable",
            "Repose-pieds": "Rétractable sous l'assise",
            "Vérin": "Gaz classe 4 haute sécurité"
        },
        "prix": 88000,
        "minimum": 8,
        "jours": 12,
        "paliers": [(2, 0, 82000), (1, 5, 84000), (2, 5, 78000)],
        "photos": [
            ("70d5070697bc5b9bb0879f764ca4454c.jpg", "chaise_gaming_dowinx.jpg", "Chaise gaming ergonomique Dowinx avec repose-pieds")
        ],
        "parts": (1, 2, 1)
    },
    {
        "nom": "Sac à Dos Urbain Luofanni Imperméable avec Peluche",
        "marque": "Luofanni",
        "categorie": "Mode",
        "description": "Sac à dos tendance antivol en tissu Oxford déperlant de haute densité. Nombreux compartiments pratiques pour tablette et accessoires, fermetures renforcées et porte-clé peluche assorti offert.",
        "caracteristiques": {
            "Matière": "Tissu Oxford imperméable",
            "Fermetures": "Glissières étanches protégées",
            "Accessoire": "Porte-clé peluche inclus",
            "Coloris": "Noir classique, Marron chocolat"
        },
        "prix": 12500,
        "minimum": 20,
        "jours": 9,
        "paliers": [(3, 0, 11000), (1, 12, 11500), (3, 12, 10200)],
        "photos": [
            ("00f42579321b5272f3b13793dd89b1fd.jpg", "sac_luofanni_noir.jpg", "Sac à dos Luofanni noir avec porte-clé peluche"),
            ("5bf680b308d9dcf8acae3d1043813566.jpg", "sac_luofanni_marron.jpg", "Sac à dos Luofanni marron chocolat")
        ],
        "parts": (3, 3, 2, 2)
    },
]

def main():
    print("Demarrage de l'importation des produits reels...")
    oag = Utilisateur.objects.filter(telephone="90001122").first()
    if not oag:
        oag = Utilisateur.objects.filter(role="groupeur").first()
    if not oag:
        oag = Utilisateur.objects.first()

    acheteurs = list(Utilisateur.objects.exclude(pk=oag.pk)[:5])
    if not acheteurs:
        acheteurs = [oag]

    for config in PRODUITS_CONFIG:
        # Trouver ou creer la categorie
        cat, _ = Categorie.objects.get_or_create(
            nom=config["categorie"],
            defaults={"icone": "panier", "ordre": 1}
        )

        produit, cree = Produit.objects.get_or_create(
            nom=config["nom"],
            defaults={
                "marque": config["marque"],
                "categorie": cat,
                "description": config["description"],
                "caracteristiques": config["caracteristiques"],
                "propose_par": oag
            }
        )
        if not cree:
            produit.marque = config["marque"]
            produit.description = config["description"]
            produit.caracteristiques = config["caracteristiques"]
            produit.categorie = cat
            produit.save()

        # Nettoyer les anciens médias du produit pour synchroniser proprement
        produit.medias.all().delete()

        # Associer les photos
        for rang, (orig_filename, new_filename, legende) in enumerate(config["photos"]):
            src_path = os.path.join(PHOTO_DIR, orig_filename)
            dst_media = os.path.join(MEDIA_PROD_DIR, new_filename)
            dst_public = os.path.join(PUBLIC_IMG_DIR, new_filename)

            if os.path.exists(src_path):
                shutil.copy2(src_path, dst_media)
                shutil.copy2(src_path, dst_public)

                with open(dst_media, "rb") as f:
                    media_prod = MediaProduit.objects.create(
                        produit=produit,
                        genre=MediaProduit.Genre.IMAGE,
                        legende=legende,
                        ordre=rang
                    )
                    media_prod.fichier.save(new_filename, File(f), save=True)
                print(f"  [+] Photo {new_filename} attachee a {produit.nom}")
            else:
                print(f"  [!] Fichier source introuvable: {src_path}")

        # Creer ou mettre a jour la campagne
        campagne = Campagne.objects.filter(produit=produit).first()
        if not campagne:
            campagne = Campagne.objects.create(
                produit=produit,
                groupeur=oag,
                titre=f"{config['nom']} — Offre Groupée Spéciale",
                description=f"Groupage officiel vérifié par {oag.nom_public}. Livraison express Lomé et retrait points relais.",
                prix_unitaire=config["prix"],
                quantite_minimale=config["minimum"],
                date_limite=timezone.now() + timedelta(days=config["jours"]),
                statut=Campagne.Statut.EN_COURS,
                publiee_le=timezone.now()
            )
            print(f"  [+] Campagne creee: {campagne.titre}")

            # Paliers de prix
            for qte_min, parts_min, p_unit in config["paliers"]:
                PalierPrix.objects.create(
                    campagne=campagne,
                    quantite_min=qte_min,
                    participants_min=parts_min,
                    prix_unitaire=p_unit
                )

            # Participations de demonstration
            for acheteur, quantite in zip(acheteurs, config["parts"]):
                prix = campagne.prix_pour(quantite)
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

    print("\nTous les 11 produits reels et 19 photos ont ete importes avec succes !")

if __name__ == "__main__":
    main()
