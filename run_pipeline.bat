@echo off

REM On affiche un message de démarrage
echo ========================================
echo  Lancement du pipeline Books to Scrape
echo ========================================

REM On se place dans le bon dossier (REMPLACE LE CHEMIN PAR LE TIEN)
cd /d C:\Users\thier\OneDrive\Documents\books_pipeline

REM On lance Docker Compose
docker compose up --build

REM On affiche un message de fin
echo ========================================
echo  Pipeline terminé avec succès !
echo ========================================