@echo off
echo ===================================================
echo 🚀 LANCEMENT SECURISE DE L'APPLICATION NLP
echo ===================================================

echo.
echo 1. Verification de l'environnement...
if not exist "venv\Scripts\python.exe" (
    echo ❌ ERREUR: Environnement virtuel introuvable !
    echo Veuillez creer le venv avec: python -m venv venv
    pause
    exit
)

echo.
echo 2. Installation/Verification des dependances...
venv\Scripts\python.exe -m pip install -r requirements.txt

echo.
echo 3. Lancement du Backend (API)...
start "API Backend" cmd /k "venv\Scripts\python.exe -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000"

echo.
echo 4. Attente du demarrage de l'API (10 secondes)...
timeout /t 10 /nobreak >nul

echo.
echo 5. Lancement du Frontend (Streamlit)...
start "Frontend Streamlit" cmd /k "venv\Scripts\python.exe -m streamlit run src/ui/app.py"

echo.
echo ✅ TOUT EST LANCE !
echo.
pause
