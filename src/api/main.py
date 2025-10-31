# src/api/main.py

import json
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

# --- MODÈLES DE DONNÉES (pour la validation et la documentation) ---

class SearchQuery(BaseModel):
    query: str
    top_k: int = 5

class SearchResult(BaseModel):
    id: str
    score: float
    title: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]

# --- CONFIGURATION ET CHARGEMENT DES MODÈLES ---

# Chemins vers nos ressources
INDEX_FILE = "data/embeddings/document_index.faiss"
MAPPING_FILE = "data/embeddings/index_to_id_mapping.json"
CORPUS_FILE = "data/processed/processed_corpus.jsonl"
MODEL_NAME = 'all-MiniLM-L6-v2'

# Création de l'application FastAPI
app = FastAPI(
    title="Paper & Blog Recommender API",
    description="Une API pour la recherche sémantique dans une base de documents techniques.",
    version="1.0.0"
)

# Dictionnaire global pour stocker les composants chargés
# Cela évite de recharger les modèles à chaque requête, ce qui est crucial pour la performance
search_engine_components = {}

@app.on_event("startup")
def load_search_engine():
    """
    Fonction exécutée une seule fois au démarrage de l'API.
    Charge tous les composants nécessaires en mémoire.
    """
    print("Chargement du moteur de recherche au démarrage de l'API...")
    
    # Charger le modèle d'embedding
    search_engine_components['model'] = SentenceTransformer(MODEL_NAME)
    
    # Charger l'index FAISS
    search_engine_components['index'] = faiss.read_index(INDEX_FILE)
    
    # Charger le mapping index -> ID
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        index_to_id = json.load(f)
        search_engine_components['index_to_id'] = {int(k): v for k, v in index_to_id.items()}
        
    # Charger le corpus
    documents_by_id = {}
    with open(CORPUS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            doc = json.loads(line)
            documents_by_id[doc['id']] = doc
    search_engine_components['documents_by_id'] = documents_by_id
    
    print("✅ Moteur de recherche chargé et prêt.")

# --- POINT DE TERMINAISON DE L'API ---

@app.post("/search", response_model=SearchResponse)
def search(query: SearchQuery):
    """
    Prend une requête textuelle et renvoie les k documents les plus similaires.
    """
    model = search_engine_components['model']
    index = search_engine_components['index']
    index_to_id = search_engine_components['index_to_id']
    documents_by_id = search_engine_components['documents_by_id']

    # 1. Créer et normaliser l'embedding de la requête
    query_embedding = model.encode([query.query])
    faiss.normalize_L2(query_embedding)
    
    # 2. Chercher dans l'index
    distances, indices = index.search(query_embedding, query.top_k)
    
    # 3. Formater les résultats
    results = []
    for i in range(query.top_k):
        index_pos = indices[0][i]
        score = float(distances[0][i])
        doc_id = index_to_id.get(index_pos)
        
        if doc_id:
            document = documents_by_id.get(doc_id)
            if document:
                results.append(SearchResult(
                    id=doc_id,
                    score=score,
                    title=document.get('title'),
                    source=document.get('source'),
                    url=document.get('url'),
                    abstract=document.get('abstract')
                ))

    return SearchResponse(results=results)