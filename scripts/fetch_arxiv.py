# scripts/fetch_arxiv.py

import arxiv
import os
import json
from datetime import datetime

# --- CONFIGURATION ---
# Définissez les mots-clés de recherche. Vous pouvez les rendre plus complexes.
# Voir la documentation de l'API ArXiv pour les requêtes avancées (AND, OR, etc.)
SEARCH_QUERY = "LLM OR 'Large Language Model' OR RAG OR 'Retrieval Augmented Generation'"
MAX_RESULTS = 50  # Nombre d'articles à récupérer

# Définissez le chemin où sauvegarder les données
OUTPUT_DIR = "data/raw/arxiv"

# --- LOGIQUE DU SCRIPT ---
def fetch_arxiv_papers():
    """
    Interroge l'API ArXiv, télécharge les métadonnées et les PDF des articles.
    """
    # Crée le dossier de sortie s'il n'existe pas
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Le dossier de sortie est : {OUTPUT_DIR}")

    # Crée un client de recherche ArXiv
    search = arxiv.Search(
        query=SEARCH_QUERY,
        max_results=MAX_RESULTS,
        sort_by=arxiv.SortCriterion.SubmittedDate  # Trie par date de soumission la plus récente
    )

    print(f"Recherche des {MAX_RESULTS} articles les plus récents pour la requête : '{SEARCH_QUERY}'...")

    # Itère sur les résultats
    for result in search.results():
        try:
            # Crée un nom de fichier sûr à partir de l'ID de l'article
            paper_id = result.entry_id.split('/')[-1]
            filename_base = os.path.join(OUTPUT_DIR, paper_id)
            
            # --- 1. Sauvegarder les métadonnées ---
            metadata = {
                "paper_id": paper_id,
                "title": result.title,
                "authors": [author.name for author in result.authors],
                "summary": result.summary,
                "published_date": result.published.isoformat(),
                "updated_date": result.updated.isoformat(),
                "pdf_url": result.pdf_url,
                "categories": result.categories,
                "retrieved_at": datetime.utcnow().isoformat()
            }
            
            # Écrit les métadonnées dans un fichier JSON
            metadata_filepath = f"{filename_base}.json"
            with open(metadata_filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=4)
            
            print(f"  [OK] Métadonnées sauvegardées pour : {paper_id} - {result.title[:50]}...")

            # --- 2. Télécharger le PDF ---
            pdf_filepath = f"{filename_base}.pdf"
            result.download_pdf(dirpath=OUTPUT_DIR, filename=f"{paper_id}.pdf")
            
            print(f"  [OK] PDF téléchargé : {pdf_filepath}")

        except Exception as e:
            print(f"  [ERREUR] Échec du traitement de l'article {result.entry_id}: {e}")

    print("\nCollecte des données d'ArXiv terminée.")

if __name__ == "__main__":
    fetch_arxiv_papers()
