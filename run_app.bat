@echo off
echo ===================================================
echo 🚀 LANCEMENT DE L'APPLICATION NLP
echo ===================================================

echo.
echo 1. Activation de l'environnement virtuel...
call venv\Scripts\activate

echo.
echo 2. Installation des dependances manquantes...
pip install -r requirements.txt

echo.
echo 3. Lancement du Backend (API)...
start "API Backend" cmd /k "python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000"

echo.
echo 4. Attente du demarrage de l'API (5 secondes)...
timeout /t 5 /nobreak >nul

echo.
echo 5. Lancement du Frontend (Streamlit)...
start "Frontend Streamlit" cmd /k "streamlit run src/ui/app.py"

echo.
echo ✅ TOUT EST LANCE !
echo.
echo - La fenetre "API Backend" doit rester ouverte
echo - La fenetre "Frontend Streamlit" doit rester ouverte
echo - Votre navigateur va s'ouvrir automatiquement
echo.
pause
