# On part d'une image Python officielle
FROM python:3.11-slim

# On définit le dossier de travail
WORKDIR /app

# On copie et installe les bibliothèques
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# On copie tout le projet
COPY . .

# On lance le scraper au démarrage du conteneur
CMD ["python", "scraper.py"]

