# On part d'une image Python officielle
FROM python:3.11-slim

# On installe Cron
RUN apt-get update && apt-get install -y cron

# On définit le dossier de travail
WORKDIR /app

# On copie et installe les bibliothèques
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# On copie tout le projet
COPY . .

# On copie le fichier crontab dans le système
COPY crontab /etc/cron.d/books_cron

# On donne les bonnes permissions au fichier cron
RUN chmod 0644 /etc/cron.d/books_cron

# On active le fichier cron
RUN crontab /etc/cron.d/books_cron

# On crée le fichier de logs
RUN touch /app/logs.txt

# On lance Cron au démarrage du conteneur
CMD ["cron", "-f"] 