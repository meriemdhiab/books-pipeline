import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import time
import os

# ============================================================
# ÉTAPE 0 — CONFIGURATION DES LOGS
# Doit être fait EN PREMIER, avant tout le reste
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)-8s - %(message)s",
    handlers=[
        logging.StreamHandler(),                               # → affiche dans le terminal
        logging.FileHandler("pipeline.log", encoding="utf-8") # → sauvegarde dans pipeline.log
    ]
)

# Notre "stylo" pour écrire dans le journal de bord
logger = logging.getLogger(__name__)

# ============================================================
# ÉTAPE 1 — CONFIGURATION GÉNÉRALE
# ============================================================

CSV_FILE  = "books.csv"
BASE_URL  = "https://books.toscrape.com/catalogue/"
START_URL = BASE_URL + "page-1.html"

# ============================================================
# ÉTAPE 2 — FONCTIONS UTILITAIRES
# ============================================================

def get_rating_number(rating_text):
    """
    Convertir le texte de la note en nombre entier (1 à 5).
    Ex : "Three" → 3
    Si la valeur est inconnue, on retourne 0 (pas de crash).
    """
    ratings = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
    return ratings.get(rating_text, 0)


def fetch_page(url, max_retries=3):
    """
    Télécharger une page web avec plusieurs tentatives en cas d'échec.
    Retourne l'objet response, ou None si toutes les tentatives échouent.
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Déclenche une erreur si code HTTP 4xx/5xx
            return response               # Succès → on retourne la réponse

        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Connexion impossible : {url} (tentative {attempt + 1}/{max_retries})")

        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Erreur HTTP {e} sur : {url}")
            return None  # Pas la peine de réessayer sur une erreur HTTP

        except requests.exceptions.Timeout:
            logger.warning(f"⏱️ Timeout sur : {url} (tentative {attempt + 1}/{max_retries})")

        except Exception as e:
            logger.error(f"❌ Erreur inattendue sur {url} : {e}")
            return None

        # Si on n'est pas à la dernière tentative, on attend avant de réessayer
        if attempt < max_retries - 1:
            logger.info("🔄 Nouvelle tentative dans 2 secondes...")
            time.sleep(2)

    logger.error(f"🛑 Abandon après {max_retries} tentatives : {url}")
    return None


def get_category(book_url):
    """
    Aller sur la page détail du livre pour extraire sa catégorie
    via le fil d'Ariane (= breadcrumb).

    Le fil d'Ariane ressemble à :
    Accueil > Books > Mystery > Titre du livre
                      ↑
                  On veut ça (index 2)
    """
    response = fetch_page(book_url, max_retries=2)
    if not response:
        return "Non classé"

    try:
        detail_soup = BeautifulSoup(response.content, 'html.parser')

        # Méthode 1 : breadcrumb (fil d'Ariane)
        breadcrumb = detail_soup.find('ul', class_='breadcrumb')
        if breadcrumb:
            category_links = breadcrumb.find_all('a')
            if len(category_links) >= 3:
                return category_links[2].text.strip()

        # Méthode 2 (fallback) : chercher un lien contenant '/category/'
        cat_link = detail_soup.find('a', href=lambda x: x and '/category/' in x)
        if cat_link:
            return cat_link.text.strip()

    except Exception as e:
        logger.warning(f"⚠️ Catégorie introuvable pour {book_url} : {e}")

    return "Non classé"


def extract_book_info(book):
    """
    Extraire les informations d'un livre depuis son bloc HTML <article>.
    Utilise plusieurs méthodes (fallback) pour chaque champ.
    Retourne un dictionnaire, ou None si les données essentielles manquent.
    """
    book_info = {}

    # ── TITRE ──────────────────────────────────────────────
    titre = None
    try:
        # Méthode 1 : attribut 'title' du lien dans le h3
        h3 = book.find('h3')
        if h3 and h3.a:
            titre = h3.a.get('title', '').strip()
    except:
        pass

    if not titre:
        try:
            # Méthode 2 : chercher n'importe quel lien avec attribut title
            lien = book.find('a', title=True)
            if lien:
                titre = lien.get('title', '').strip()
        except:
            pass

    if not titre:
        return None  # Sans titre → on ignore ce livre

    book_info['titre'] = titre

    # ── PRIX ───────────────────────────────────────────────
    prix = None
    try:
        # Méthode 1 : balise <p class="price_color">
        price_tag = book.find('p', class_='price_color')
        if price_tag:
            price_text = price_tag.text.replace('£', '').replace('Â', '').strip()
            prix = float(price_text)
    except:
        pass

    if prix is None:
        try:
            # Méthode 2 : chercher n'importe quel texte contenant '£'
            price_elements = book.find_all(
                string=lambda text: '£' in text if text else False
            )
            if price_elements:
                price_text = price_elements[0].replace('£', '').replace('Â', '').strip()
                prix = float(price_text)
        except:
            pass

    if prix is None:
        return None  # Sans prix → on ignore ce livre

    book_info['prix'] = prix

    # ── NOTE ───────────────────────────────────────────────
    note = 0
    try:
        rating_tag = book.find('p', class_='star-rating')
        if rating_tag:
            classes = rating_tag.get('class', [])
            if len(classes) > 1:
                note = get_rating_number(classes[1])
    except:
        pass

    book_info['note'] = note

    # ── URL (pour récupérer la catégorie ensuite) ──────────
    book_url = None
    try:
        h3 = book.find('h3')
        if h3 and h3.a:
            book_link = h3.a.get('href', '')
            book_url = BASE_URL + book_link.replace('../../../', '')
    except:
        pass

    # Stocké temporairement — sera supprimé avant la sauvegarde CSV
    book_info['_url'] = book_url

    return book_info


# ============================================================
# ÉTAPE 3 — PIPELINE PRINCIPAL
# ============================================================

logger.info("=" * 60)
logger.info("🚀 Démarrage du pipeline Books to Scrape")
logger.info("=" * 60)

start_time      = time.time()
tous_les_livres = []
url             = START_URL
num_page        = 0
nb_ok           = 0
nb_ignores      = 0

while url:
    num_page += 1
    logger.info(f"📄 Scraping page {num_page} : {url}")

    # Téléchargement de la page (avec retry automatique)
    response = fetch_page(url)

    if response is None:
        logger.error("🛑 Page inaccessible. Arrêt du pipeline.")
        break

    soup   = BeautifulSoup(response.content, "html.parser")
    livres = soup.find_all("article", class_="product_pod")

    for livre in livres:
        try:
            book_info = extract_book_info(livre)

            if book_info is None:
                logger.warning("⚠️ Livre ignoré : titre ou prix manquant")
                nb_ignores += 1
                continue

            # Récupération de la catégorie via la page détail
            if book_info.get('_url'):
                book_info['categorie'] = get_category(book_info['_url'])
            else:
                logger.warning(f"⚠️ URL introuvable pour : {book_info.get('titre', '?')}")
                book_info['categorie'] = "Non classé"

            # On supprime l'URL temporaire avant de stocker
            del book_info['_url']

            tous_les_livres.append(book_info)
            nb_ok += 1

        except Exception as e:
            logger.error(f"❌ Erreur inattendue sur un livre : {e}")
            nb_ignores += 1
            continue

    # Page suivante
    bouton_suivant = soup.find("li", class_="next")
    if bouton_suivant:
        page_suivante = bouton_suivant.find("a")["href"]
        url = BASE_URL + page_suivante
    else:
        url = None  # Plus de page suivante → fin de la boucle

# ============================================================
# ÉTAPE 4 — SAUVEGARDE ET RAPPORT FINAL
# ============================================================

duration = time.time() - start_time

if tous_les_livres:
    df = pd.DataFrame(tous_les_livres)[['titre', 'categorie', 'prix', 'note']]
    df.to_csv(CSV_FILE, index=False, encoding="utf-8")

    logger.info("=" * 60)
    logger.info("📊 RAPPORT FINAL")
    logger.info(f"⏱️  Durée totale        : {duration:.2f} secondes")
    logger.info(f"✅  Livres collectés    : {nb_ok}")
    logger.info(f"⚠️   Livres ignorés      : {nb_ignores}")
    logger.info(f"💾  Fichier sauvegardé  : {CSV_FILE}")
    logger.info(f"📏  Taille du fichier   : {os.path.getsize(CSV_FILE) / 1024:.1f} KB")
    logger.info("=" * 60)

else:
    logger.critical("💀 Aucune donnée collectée. Le fichier CSV n'a pas été créé.")