# 🚀 Moteur de Recommandation de Documents Techniques

Ce projet est un moteur de recherche sémantique complet qui permet de trouver des articles de recherche (via ArXiv) et des articles de blog techniques pertinents en réponse à une question posée en langage naturel.

![Capture d'écran de l'application Streamlit](URL_DE_VOTRE_CAPTURE_D_ECRAN_ICI)
*(Astuce : faites une capture d'écran de votre application finale et déposez-la dans votre dépôt GitHub pour obtenir une URL)*

---

## ✨ Fonctionnalités

*   **Collecte de Données Multi-sources :** Scrapers robustes pour l'API ArXiv et plusieurs sites de blogs techniques (Hugging Face, AWS, Medium).
*   **Recherche Sémantique :** Utilise des modèles `sentence-transformers` pour comprendre le sens des requêtes, pas seulement les mots-clés.
*   **Backend Performant :** Une API web construite avec FastAPI qui sert les résultats de recherche à la vitesse de l'éclair.
*   **Indexation Vectorielle Rapide :** Utilise FAISS (développé par Meta) pour des recherches de similarité quasi-instantanées.
*   **Interface Utilisateur Interactive :** Une application web simple et élégante construite avec Streamlit.

---

## 🛠️ Stack Technique

*   **Backend :** Python, FastAPI
*   **Frontend :** Streamlit
*   **Modèles de NLP :** `sentence-transformers` (Hugging Face)
*   **Base de Données Vectorielle :** FAISS
*   **Scraping :** Playwright, BeautifulSoup, Requests
*   **Traitement de Données :** PyMuPDF (fitz), NumPy

---

## 🚀 Installation et Lancement

Suivez ces étapes pour lancer le projet sur votre machine locale.

### 1. Prérequis

*   Python 3.10 ou supérieur
*   Git

### 2. Installation

```bash
# Clonez le dépôt
git clone https://github.com/[VOTRE_NOM_UTILISATEUR]/[NOM_DE_VOTRE_DEPOT].git
cd [NOM_DE_VOTRE_DEPOT]

# Créez et activez un environnement virtuel
python -m venv venv
# Sur Windows
.\venv\Scripts\activate
# Sur macOS/Linux
# source venv/bin/activate

# Installez les dépendances
pip install -r requirements.txt

# Téléchargez les navigateurs pour Playwright (uniquement la première fois)
playwright install