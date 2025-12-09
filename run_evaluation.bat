@echo off
echo ===================================================
echo 📊 EVALUATION DU MODELE (ROUGE + BERTScore)
echo ===================================================

echo.
echo 1. Verification de l'environnement...
if not exist "venv\Scripts\python.exe" (
    echo ❌ ERREUR: Environnement virtuel introuvable !
    pause
    exit
)

echo.
echo 2. Lancement de l'evaluation...
echo Cela peut prendre du temps selon la taille des donnees de test.
echo.

cd scripts
..\venv\Scripts\python.exe evaluate_summaries.py

echo.
echo ✅ EVALUATION TERMINEE !
echo Les resultats sont sauvegardes dans scripts/results/evaluation_results.json
echo.
pause
