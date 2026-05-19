# 🗺️ Data Pipeline — Books to Scrape

## Schéma du pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                     DATA PIPELINE - SESSION 1               │
│                      Books to Scrape                        │
└─────────────────────────────────────────────────────────────┘

  ┌──────────────────────┐
  │  🌐  SOURCE          │
  │  books.toscrape.com  │
  │  50 pages            │
  │  1000 livres         │
  └──────────┬───────────┘
             │
             │  requête HTTP GET
             ▼
  ┌──────────────────────┐
  │  📬  EXTRACT         │       OUTIL : requests
  │  Téléchargement      │──────────────────────────►  HTML brut
  │  des pages web       │
  └──────────┬───────────┘
             │
             │  HTML brut
             ▼
  ┌──────────────────────┐
  │  🔍  PARSE           │       OUTIL : BeautifulSoup
  │  Lecture du HTML     │──────────────────────────►  titre
  │  Extraction des      │                             prix (£)
  │  informations        │                             note (Three)
  └──────────┬───────────┘
             │
             │  données brutes
             ▼
  ┌──────────────────────┐
  │  🧹  TRANSFORM       │       OUTIL : pandas
  │  Nettoyage           │──────────────────────────►  £51.77 → 51.77
  │  des données         │                             Three  → 3
  └──────────┬───────────┘
             │
             │  données propres
             ▼
  ┌──────────────────────┐
  │  💾  LOAD            │       OUTIL : pandas
  │  Sauvegarde          │──────────────────────────►  books.csv
  │  en fichier CSV      │
  └──────────────────────┘
```

## Les 4 étapes

| Étape | Nom | Outil | Entrée → Sortie |
|---|---|---|---|
| 1️⃣ | **Extract** | `requests` | URL → HTML brut |
| 2️⃣ | **Parse** | `BeautifulSoup` | HTML → données brutes |
| 3️⃣ | **Transform** | `pandas` | données brutes → données propres |
| 4️⃣ | **Load** | `pandas` | données propres → `books.csv` |