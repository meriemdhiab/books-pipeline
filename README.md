# 📚 Books Pipeline

Pipeline de données automatisé pour collecter, nettoyer et stocker les informations des livres du site [Books to Scrape](https://books.toscrape.com).

---

## 🎯 Objectif

Ce projet met en œuvre un pipeline ETL complet :

•⁠  ⁠*Extraire* les données de 1000 livres sur 50 pages web
•⁠  ⁠*Transformer* les données brutes (conversion des prix et des notes)
•⁠  ⁠*Charger* les données nettoyées dans un fichier CSV exploitable

Le pipeline est entièrement *dockerisé* pour garantir un fonctionnement identique sur toutes les machines.

---

## 🏗️ Architecture


┌─────────────────────────────────────────────────────────────┐
│                     DATA PIPELINE                           │
│                      Books to Scrape                        │
└─────────────────────────────────────────────────────────────┘

  ┌──────────────────────┐
  │  🌐  SOURCE          │
  │  books.toscrape.com  │
  │  50 pages / 1000 livres
  └──────────┬───────────┘
             │  requête HTTP GET
             ▼
  ┌──────────────────────┐
  │  📬  EXTRACT         │   requests
  │  Téléchargement      │──────────────► HTML brut
  │  des pages web       │
  └──────────┬───────────┘
             │  HTML brut
             ▼
  ┌──────────────────────┐
  │  🔍  PARSE           │   BeautifulSoup
  │  Extraction des      │──────────────► titre, prix, note
  │  informations        │
  └──────────┬───────────┘
             │  données brutes
             ▼
  ┌──────────────────────┐
  │  🧹  TRANSFORM       │   pandas
  │  Nettoyage           │──────────────► £51.77 → 51.77
  │  des données         │               Three  → 3
  └──────────┬───────────┘
             │  données propres
             ▼
  ┌──────────────────────┐
  │  💾  LOAD            │   pandas
  │  Sauvegarde CSV      │──────────────► books.csv
  └──────────────────────┘


### Stack technique

| Outil | Rôle |
|---|---|
| ⁠ Python 3.11 ⁠ | Langage principal |
| ⁠ requests ⁠ | Téléchargement des pages web |
| ⁠ BeautifulSoup4 ⁠ | Extraction des données HTML |
| ⁠ pandas ⁠ | Nettoyage et sauvegarde CSV |
| ⁠ logging ⁠ | Monitoring du pipeline |
| ⁠ Docker ⁠ | Conteneurisation |
| ⁠ Docker Compose ⁠ | Orchestration |

### Structure du projet


books-pipeline/
├── scraper.py            # Script principal du pipeline
├── requirements.txt      # Dépendances Python
├── Dockerfile            # Image Docker
├── docker-compose.yml    # Orchestration des conteneurs
├── pipeline.md           # Schéma détaillé du pipeline
└── README.md             # Documentation (ce fichier)


---

## 🚀 Comment lancer le pipeline

### Prérequis

•⁠  ⁠[Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et démarré

### Lancement

*1. Cloner le repo*
⁠ bash
git clone https://github.com/talvares-lang/books-pipeline.git
cd books-pipeline
 ⁠

*2. Construire l'image Docker*
⁠ bash
docker compose build
 ⁠

*3. Lancer le pipeline*
⁠ bash
docker compose up
 ⁠

Le pipeline démarre, scrape les 50 pages et génère le fichier ⁠ books.csv ⁠ dans le dossier du projet.

*4. Consulter les logs en temps réel*
⁠ bash
docker logs books_scraper
 ⁠

*5. Arrêter et nettoyer les conteneurs*
⁠ bash
docker compose down
 ⁠

---

## 📊 Description des données

Le pipeline produit un fichier ⁠ books.csv ⁠ avec les colonnes suivantes :

| Colonne | Type | Description | Exemple |
|---|---|---|---|
| ⁠ titre ⁠ | string | Titre complet du livre | "A Light in the Attic" |
| ⁠ categorie ⁠ | string | Genre littéraire | "Poetry" |
| ⁠ prix ⁠ | float | Prix en livres sterling (£) | 51.77 |
| ⁠ note ⁠ | int | Note de 1 à 5 | 3 |

### Résultats obtenus

•⁠  ⁠*1000 livres* collectés
•⁠  ⁠*0 livre ignoré*
•⁠  ⁠Durée d'exécution : ~12 minutes
•⁠  ⁠Taille du fichier : 58.4 KB

---

## 📋 Monitoring

Le pipeline génère des logs détaillés pendant son exécution :


2026-05-19 13:46:57 - INFO - 🚀 Démarrage du pipeline Books to Scrape
2026-05-19 13:46:57 - INFO - 📄 Scraping page 1 : https://books.toscrape.com/catalogue/page-1.html
...
2026-05-19 14:06:12 - INFO - 📊 RAPPORT FINAL
2026-05-19 14:06:12 - INFO - ⏱️ Durée totale : 1155.03 secondes
2026-05-19 14:06:12 - INFO - ✅ Livres collectés : 1000
2026-05-19 14:06:12 - INFO - 💾 Fichier sauvegardé : books.csv


---

## ⚖️ Mentions légales

•⁠  ⁠Site source : [Books to Scrape](https://books.toscrape.com) — site conçu explicitement pour le scraping
•⁠  ⁠Aucune donnée personnelle collectée
•⁠  ⁠Utilisation à des fins pédagogiques uniquement