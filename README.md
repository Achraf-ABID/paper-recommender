# 🚀 Intelligent Research Assistant (RAG + LoRA)

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.68%2B-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.25%2B-red)
![AI](https://img.shields.io/badge/AI-LoRA%20%2B%20RAG-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

**Un moteur de recherche sémantique et de résumé automatique pour la veille technologique.**

Ce projet est un assistant cognitif conçu pour aider les chercheurs et ingénieurs à naviguer dans la littérature scientifique (ArXiv) et technique. Il combine la puissance de la **Recherche Vectorielle (RAG)** avec la précision du **Fine-Tuning (LoRA)** pour générer des synthèses pertinentes.

---

## ✨ Fonctionnalités Clés

*   **🔍 Recherche Sémantique Avancée** : Utilise des embeddings (`all-MiniLM-L6-v2`) et un index FAISS pour trouver des documents par le sens, pas juste par mots-clés.
*   **🧠 Re-Ranking Intelligent** : Un second modèle (Cross-Encoder) réordonne les résultats pour une pertinence maximale.
*   **✍️ Résumé Abstractif (LoRA)** : Génère des résumés concis et fidèles grâce à un modèle BART/T5 fine-tuné avec la méthode LoRA (Low-Rank Adaptation).
*   **📊 Synthèse Multi-Documents** : Capable de lire plusieurs articles et d'en produire une synthèse globale cohérente.
*   **⚡ Interface Moderne** : Frontend réactif en Streamlit couplé à une API Backend rapide en FastAPI.

---

## 🏗️ Architecture Technique

Le système repose sur une architecture **RAG (Retrieval-Augmented Generation)** optimisée :

1.  **Ingestion** : Collecte et nettoyage des articles (ArXiv, Blogs).
2.  **Indexation** : Vectorisation des textes et stockage dans un index **FAISS**.
3.  **Retrieval** : Récupération des candidats les plus proches de la requête utilisateur.
4.  **Re-Ranking** : Tri fin des candidats par un Cross-Encoder (`ms-marco-MiniLM-L-6-v2`).
5.  **Génération** : Le modèle LoRA génère un résumé individuel pour chaque top-article, puis une synthèse globale.

---

## 🚀 Installation et Démarrage

### Prérequis
*   Python 3.9 ou supérieur
*   Un environnement virtuel (recommandé)

### 1. Installation
```bash
# Cloner le dépôt
git clone https://github.com/votre-username/nlp-project.git
cd nlp-project

# Créer l'environnement virtuel
python -m venv venv
.\venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Lancement Rapide (Recommandé)
Utilisez le script automatisé pour lancer le Backend (API) et le Frontend (UI) en une seule fois :

```bash
run_app_secure.bat
```
*L'application sera accessible sur `http://localhost:8501`*

### 3. Lancement Manuel
Si vous préférez lancer les services séparément dans deux terminaux :

**Terminal 1 : Backend (API)**
```bash
# Lance le serveur FastAPI sur http://127.0.0.1:8000
uvicorn src.api.main:app --reload
```

**Terminal 2 : Frontend (UI)**
```bash
# Lance l'interface Streamlit sur http://localhost:8501
streamlit run src/ui/app.py
```

---

## 🛠️ Maintenance et Outils

Le projet inclut des scripts utilitaires pour la gestion des données :

*   **Nettoyage et Réindexation** :
    ```bash
    clean_and_reindex.bat
    ```
    *Supprime les doublons et régénère l'index FAISS.*

*   **Évaluation du Modèle** :
    ```bash
    run_evaluation.bat
    ```
    *Calcule les scores ROUGE et BERTScore sur le jeu de test.*

---

## 📈 Performances

Le modèle de résumé a été évalué sur un dataset de test dédié.

| Métrique | Score | Interprétation |
| :--- | :---: | :--- |
| **BERTScore F1** | **0.896** | Excellent alignement sémantique avec la référence. |
| **ROUGE-1** | 0.385 | Bonne couverture des mots-clés. |
| **ROUGE-L** | 0.278 | Structure de phrase cohérente. |

---

## 📂 Structure du Projet

```
nlp-project/
├── data/                  # Données brutes et index FAISS
├── models/                # Modèles fine-tunés (LoRA)
├── scripts/               # Scripts ETL, Entraînement, Éval
├── src/
│   ├── api/               # Backend FastAPI
│   │   ├── main.py        # Endpoints & Logique RAG
│   │   └── summarizer.py  # Moteur d'inférence LoRA
│   └── ui/                # Frontend Streamlit
│       └── app.py         # Interface Utilisateur
├── requirements.txt       # Dépendances Python
└── README.md              # Documentation
```

---

## 📝 Auteur

**Achraf ABID** - *Ingénieur NLP / Data Scientist*

---
*Projet réalisé dans le cadre d'une recherche sur l'optimisation des LLMs.*