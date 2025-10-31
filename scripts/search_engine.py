# scripts/search_engine.py

import json
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import time

# --- CONFIGURATION ---
# Assurez-vous que ces chemins correspondent à vos fichiers de sortie de la phase 4
INDEX_FILE = "data/embeddings/document_index.faiss"
MAPPING_FILE = "data/embeddings/index_to_id_mapping.json"
CORPUS_FILE = "data/processed/processed_corpus.jsonl"
MODEL_NAME = 'all-MiniLM-L6-v2'

# Nombre de résultats à retourner
TOP_K = 5

def main():
    """
    Script interactif pour tester le moteur de recherche sémantique.
    """
    print("="*60)
    print("Moteur de Recherche Sémantique - Interface de Test")
    print("="*60)

    # --- 1. Charger tous les composants ---
    print("Chargement des composants du moteur de recherche...")

    # Charger le modèle d'embedding
    try:
        model = SentenceTransformer(MODEL_NAME)
    except Exception as e:
        print(f"[ERREUR] Impossible de charger le modèle SentenceTransformer : {e}")
        return

    # Charger l'index FAISS
    try:
        index = faiss.read_index(INDEX_FILE)
    except Exception as e:
        print(f"[ERREUR] Impossible de charger l'index FAISS depuis '{INDEX_FILE}' : {e}")
        return

    # Charger le mapping index -> ID
    try:
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            index_to_id = json.load(f)
            # Les clés JSON sont des chaînes, on les reconvertit en entiers
            index_to_id = {int(k): v for k, v in index_to_id.items()}
    except Exception as e:
        print(f"[ERREUR] Impossible de charger le fichier de mapping depuis '{MAPPING_FILE}' : {e}")
        return

    # Charger le corpus complet pour afficher les résultats
    # On le charge dans un dictionnaire pour un accès rapide par ID
    documents_by_id = {}
    try:
        with open(CORPUS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                doc = json.loads(line)
                documents_by_id[doc['id']] = doc
    except Exception as e:
        print(f"[ERREUR] Impossible de charger le corpus depuis '{CORPUS_FILE}' : {e}")
        return

    print("✅ Composants chargés avec succès. Le moteur est prêt.")
    print(f"Entrez votre question, ou tapez 'quit' pour quitter.")
    
    # --- 2. Boucle de recherche interactive ---
    while True:
        query = input("\nVotre question > ")
        if query.lower() == 'quit':
            break
        
        start_time = time.time()
        
        # a. Créer l'embedding pour la question de l'utilisateur
        query_embedding = model.encode([query])
        
        # b. Normaliser l'embedding de la question (très important !)
        faiss.normalize_L2(query_embedding)
        
        # c. Chercher dans l'index FAISS
        # D = distances (scores de similarité), I = indices des vecteurs
        distances, indices = index.search(query_embedding, TOP_K)
        
        end_time = time.time()
        
        print("-"*(len(query) + 18))
        print(f"Résultats pour : '{query}' (recherche en {end_time - start_time:.4f} secondes)")
        print("-"*(len(query) + 18))

        # d. Afficher les résultats
        for i in range(TOP_K):
            index_pos = indices[0][i]
            score = distances[0][i]
            
            doc_id = index_to_id.get(index_pos)
            if not doc_id:
                continue

            document = documents_by_id.get(doc_id)
            if not document:
                continue
            
            print(f"\n[{i+1}] Similarité: {score:.4f} | ID: {doc_id}")
            print(f"    Titre  : {document.get('title', 'N/A')}")
            print(f"    Source : {document.get('source', 'N/A')}")
            print(f"    URL    : {document.get('url', 'N/A')}")
            print(f"    Résumé : {document.get('abstract', 'N/A')[:300]}...")

    print("\nMerci d'avoir utilisé le moteur de recherche. Au revoir !")

if __name__ == "__main__":
    main()