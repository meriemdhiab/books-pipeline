import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import time
import os
import re

# ============================================================
# ÉTAPE 0 — CONFIGURATION DES LOGS
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)-8s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pipeline.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# ÉTAPE 1 — CONFIGURATION GÉNÉRALE
# ============================================================

CSV_FILE = "books.csv"
BASE_URL = "https://books.toscrape.com/catalogue/"

TOUTES_LES_PAGES = [BASE_URL + f"page-{i}.html" for i in range(1, 51)]

# ============================================================
# ÉTAPE 2 — FONCTIONS UTILITAIRES
# ============================================================

def get_rating_number(rating_text):
    ratings = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
    return ratings.get(rating_text, 0)


def fetch_page(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response

        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Connexion impossible : {url} (tentative {attempt + 1}/{max_retries})")

        except requests.exceptions.HTTPError as e:
            code = e.response.status_code
            if code in [400, 403, 404]:
                logger.error(f"❌ Erreur {code} : {url}")
                return None
            elif code == 429:
                logger.warning(f"⚠️ Erreur 429 - Trop de requêtes → attente 10 secondes")
                time.sleep(10)
            elif code in [500, 503]:
                logger.error(f"❌ Erreur {code} - Serveur : {url} (tentative {attempt + 1}/{max_retries})")
            else:
                logger.error(f"❌ Erreur HTTP {code} : {url}")
                return None

        except requests.exceptions.Timeout:
            logger.warning(f"⏱️ Timeout : {url} (tentative {attempt + 1}/{max_retries})")

        except Exception as e:
            logger.error(f"❌ Erreur inattendue : {e}")
            return None

        if attempt < max_retries - 1:
            logger.info("🔄 Nouvelle tentative dans 2 secondes...")
            time.sleep(2)

    logger.error(f"🛑 Abandon après {max_retries} tentatives : {url}")
    return None


def get_category(book_url):
    response = fetch_page(book_url, max_retries=2)
    if not response:
        return "Non classé"
    try:
        detail_soup = BeautifulSoup(response.content, 'html.parser')
        breadcrumb = detail_soup.find('ul', class_='breadcrumb')
        if breadcrumb:
            category_links = breadcrumb.find_all('a')
            if len(category_links) >= 3:
                return category_links[2].text.strip()
        cat_link = detail_soup.find('a', href=lambda x: x and '/category/' in x)
        if cat_link:
            return cat_link.text.strip()
    except Exception as e:
        logger.warning(f"⚠️ Catégorie introuvable pour {book_url} : {e}")
    return "Non classé"


# ============================================================
# FONCTIONS D'EXTRACTION AVEC FALLBACKS
# ============================================================

def extract_url(book):
    try:
        for balise in ['h3', 'h2', 'h4', 'h1']:
            tag = book.find(balise)
            if tag and tag.a:
                book_link = tag.a.get('href', '')
                if book_link:
                    return BASE_URL + book_link.replace('../../../', '')
    except:
        pass
    try:
        lien = book.find('a', href=True)
        if lien:
            book_link = lien.get('href', '')
            if book_link:
                return BASE_URL + book_link.replace('../../../', '')
    except:
        pass
    return "inconnue"


def extract_titre(book, book_url="inconnue"):
    try:
        h3 = book.find('h3')
        if h3 and h3.a:
            titre = h3.a.get('title', '').strip()
            if titre:
                return titre
    except:
        pass
    try:
        for balise in ['h2', 'h4', 'h1']:
            tag = book.find(balise)
            if tag and tag.a:
                titre = tag.a.get('title', '').strip()
                if titre:
                    logger.warning(f"⚠️ Titre via méthode 2 ({balise}) — URL livre : {book_url}")
                    return titre
    except:
        pass
    try:
        lien = book.find('a', title=True)
        if lien:
            titre = lien.get('title', '').strip()
            if titre:
                logger.warning(f"⚠️ Titre via méthode 3 (a > title) — URL livre : {book_url}")
                return titre
    except:
        pass
    try:
        lien = book.find('a')
        if lien:
            titre = lien.get_text(strip=True)
            if titre:
                logger.warning(f"⚠️ Titre via méthode 4 (texte lien) — URL livre : {book_url}")
                return titre
    except:
        pass
    logger.error(f"❌ Titre introuvable — URL livre : {book_url}")
    return None


def extract_prix(book, book_url="inconnue"):
    try:
        tag = book.find('p', class_='price_color')
        if tag:
            texte = tag.text.replace('£', '').replace('Â', '').strip()
            return float(texte)
    except:
        pass
    try:
        elements = book.find_all(string=lambda t: '£' in t if t else False)
        if elements:
            texte = elements[0].replace('£', '').replace('Â', '').strip()
            logger.warning(f"⚠️ Prix via méthode 2 (texte £) — URL livre : {book_url}")
            return float(texte)
    except:
        pass
    try:
        texte_complet = book.get_text()
        match = re.search(r'(\d+\.\d{2})', texte_complet)
        if match:
            logger.warning(f"⚠️ Prix via méthode 3 (regex) — URL livre : {book_url}")
            return float(match.group(1))
    except:
        pass
    logger.error(f"❌ Prix introuvable — URL livre : {book_url}")
    return None


def extract_note(book, book_url="inconnue"):
    try:
        tag = book.find('p', class_='star-rating')
        if tag:
            classes = tag.get('class', [])
            if len(classes) > 1:
                resultat = get_rating_number(classes[1])
                if resultat > 0:
                    return resultat
    except:
        pass
    try:
        star = book.find(
            class_=lambda c: c and 'star' in c.lower() if isinstance(c, str) else False
        )
        if star:
            for cls in star.get('class', []):
                note = get_rating_number(cls)
                if note > 0:
                    logger.warning(f"⚠️ Note via méthode 2 (classe star) — URL livre : {book_url}")
                    return note
    except:
        pass
    logger.warning(f"⚠️ Note introuvable → NaN — URL livre : {book_url}")
    return float('nan')


def extract_book_info(book):
    book_url = extract_url(book)
    titre    = extract_titre(book, book_url=book_url)
    if not titre:
        return None
    prix = extract_prix(book, book_url=book_url)
    if prix is None:
        return None
    note = extract_note(book, book_url=book_url)
    return {
        'titre': titre,
        'prix':  prix,
        'note':  note,
        '_url':  book_url
    }


# ============================================================
# ÉTAPE 3 — PIPELINE PRINCIPAL
# ============================================================

logger.info("=" * 60)
logger.info("🚀 Démarrage du pipeline Books to Scrape")
logger.info("=" * 60)

start_time      = time.time()
tous_les_livres = []
nb_ok           = 0
nb_ignores      = 0
nb_pages_ok     = 0
nb_pages_erreur = 0


def traiter_livres(livres):
    global nb_ok, nb_ignores
    for livre in livres:
        try:
            book_info = extract_book_info(livre)
            if book_info is None:
                logger.warning("⚠️ Livre ignoré : titre ou prix introuvable")
                nb_ignores += 1
                continue
            if book_info.get('_url') and book_info['_url'] != "inconnue":
                book_info['categorie'] = get_category(book_info['_url'])
            else:
                book_info['categorie'] = "Non classé"
            del book_info['_url']
            tous_les_livres.append(book_info)
            nb_ok += 1
        except Exception as e:
            logger.error(f"❌ Erreur inattendue sur un livre : {e}")
            nb_ignores += 1
            continue


for num_page, url in enumerate(TOUTES_LES_PAGES, start=1):
    logger.info(f"📄 Scraping page {num_page}/{len(TOUTES_LES_PAGES)} : {url}")
    response = fetch_page(url)
    if response is None:
        logger.warning(f"⚠️ Page {num_page} ignorée, on continue avec la suivante.")
        nb_pages_erreur += 1
        continue
    nb_pages_ok += 1
    soup   = BeautifulSoup(response.content, "html.parser")
    livres = soup.find_all("article", class_="product_pod")
    traiter_livres(livres)

# ============================================================
# ÉTAPE 4 — SAUVEGARDE ET RAPPORT FINAL
# ============================================================

duration = time.time() - start_time

if tous_les_livres:
    df = pd.DataFrame(tous_les_livres)[['titre', 'categorie', 'prix', 'note']]
    df.to_csv(CSV_FILE, index=False, encoding="utf-8")

    nb_notes_manquantes = df['note'].isna().sum()

    logger.info("=" * 60)
    logger.info("📊 RAPPORT FINAL")
    logger.info(f"⏱️  Durée totale        : {duration:.2f} secondes")
    logger.info(f"📄  Pages réussies      : {nb_pages_ok}/{len(TOUTES_LES_PAGES)}")
    logger.info(f"❌  Pages en erreur     : {nb_pages_erreur}/{len(TOUTES_LES_PAGES)}")
    logger.info(f"✅  Livres collectés    : {nb_ok}")
    logger.info(f"⚠️   Livres ignorés      : {nb_ignores}")
    logger.info(f"📊  Notes manquantes    : {nb_notes_manquantes}")
    logger.info(f"💾  Fichier sauvegardé  : {CSV_FILE}")
    logger.info(f"📏  Taille du fichier   : {os.path.getsize(CSV_FILE) / 1024:.1f} KB")
    logger.info("=" * 60)

else:
    logger.critical("💀 Aucune donnée collectée. Le fichier CSV n'a pas été créé.")