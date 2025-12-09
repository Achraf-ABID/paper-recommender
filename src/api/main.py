# src/api/main.py

import json
import faiss
from sentence_transformers import SentenceTransformer, CrossEncoder
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os

# Import du summarizer depuis le même dossier (import relatif)
from .summarizer import LoRASummarizer

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


class SummarizeRequest(BaseModel):
    articles: List[dict]  # Liste d'articles à résumer


class IndividualSummary(BaseModel):
    title: Optional[str]
    summary: str
    source: Optional[str]
    url: Optional[str]
    source_url: Optional[str] = None


class SummarizeResponse(BaseModel):
    individual_summaries: List[IndividualSummary]
    global_summary: str
    total_articles: int


# --- CONFIGURATION ET CHARGEMENT DES MODÈLES ---

# Chemins vers nos ressources
INDEX_FILE = "data/embeddings/document_index.faiss"
MAPPING_FILE = "data/embeddings/index_to_id_mapping.json"
CORPUS_FILE = "data/processed/processed_corpus.jsonl"
MODEL_NAME = "all-MiniLM-L6-v2"
# Modèle de Re-Ranking (Cross-Encoder) - Petit et rapide
RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Chemin vers le modèle de résumé LoRA
LORA_MODEL_PATH = os.getenv("LORA_MODEL_PATH", "models/bart-lora-finetuned")

# Création de l'application FastAPI
app = FastAPI(
    title="Paper & Blog Recommender API + Summarizer",
    description="Une API pour la recherche sémantique et le résumé intelligent multi-documents.",
    version="2.1.0",
)

# Dictionnaire global pour stocker les composants chargés
search_engine_components = {}


@app.on_event("startup")
def load_search_engine():
    """
    Fonction exécutée une seule fois au démarrage de l'API.
    Charge tous les composants nécessaires en mémoire.
    """
    print("=" * 80)
    print("🚀 DÉMARRAGE DE L'API - Chargement des composants...")
    print("=" * 80)

    # Charger le modèle d'embedding
    print("\n📥 Chargement du modèle d'embedding...")
    search_engine_components["model"] = SentenceTransformer(MODEL_NAME)
    print("✅ Modèle d'embedding chargé")

    # Charger le modèle de Re-Ranking (Cross-Encoder)
    print("\n📥 Chargement du modèle de Re-Ranking (Cross-Encoder)...")
    try:
        search_engine_components["reranker"] = CrossEncoder(RERANKER_MODEL_NAME)
        print("✅ Modèle de Re-Ranking chargé")
    except Exception as e:
        print(f"⚠️ Impossible de charger le Re-Ranker: {e}")
        search_engine_components["reranker"] = None

    # Charger l'index FAISS
    print("\n📥 Chargement de l'index FAISS...")
    search_engine_components["index"] = faiss.read_index(INDEX_FILE)
    print("✅ Index FAISS chargé")

    # Charger le mapping index -> ID
    print("\n📥 Chargement du mapping...")
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        index_to_id = json.load(f)
        search_engine_components["index_to_id"] = {
            int(k): v for k, v in index_to_id.items()
        }
    print("✅ Mapping chargé")

    # Charger le corpus
    print("\n📥 Chargement du corpus...")
    documents_by_id = {}
    with open(CORPUS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            documents_by_id[doc["id"]] = doc
    search_engine_components["documents_by_id"] = documents_by_id
    print(f"✅ Corpus chargé ({len(documents_by_id)} documents)")

    # Charger le modèle de résumé LoRA
    print("\n📥 Chargement du modèle de résumé LoRA...")
    try:
        search_engine_components["summarizer"] = LoRASummarizer(LORA_MODEL_PATH)
        print("✅ Modèle de résumé LoRA chargé")
    except Exception as e:
        print(f"⚠️  Impossible de charger le modèle de résumé: {e}")
        print("   Le endpoint /summarize ne sera pas disponible.")
        search_engine_components["summarizer"] = None

    print("\n" + "=" * 80)
    print("✅ TOUS LES COMPOSANTS CHARGÉS - API PRÊTE!")
    print("=" * 80 + "\n")


# --- POINTS DE TERMINAISON DE L'API ---


@app.post("/search", response_model=SearchResponse)
def search(query: SearchQuery):
    """
    Prend une requête textuelle et renvoie les k documents les plus similaires.
    Utilise un Re-Ranking pour améliorer la pertinence.
    """
    model = search_engine_components["model"]
    index = search_engine_components["index"]
    index_to_id = search_engine_components["index_to_id"]
    documents_by_id = search_engine_components["documents_by_id"]
    reranker = search_engine_components.get("reranker")

    # 1. Créer et normaliser l'embedding de la requête
    query_embedding = model.encode([query.query])
    faiss.normalize_L2(query_embedding)

    # 2. Chercher dans l'index (On récupère plus de candidats pour le re-ranking)
    # Si on a un reranker, on prend 3x plus de candidats, sinon juste top_k
    fetch_k = query.top_k * 3 if reranker else query.top_k
    distances, indices = index.search(query_embedding, fetch_k)

    # 3. Récupérer les documents candidats
    candidates = []
    for i in range(fetch_k):
        if i >= len(indices[0]):
            break  # Sécurité

        index_pos = indices[0][i]
        # FAISS peut renvoyer -1 si pas assez de voisins
        if index_pos == -1:
            continue

        doc_id = index_to_id.get(index_pos)
        if doc_id:
            document = documents_by_id.get(doc_id)
            if document:
                candidates.append(
                    {
                        "doc": document,
                        "initial_score": float(distances[0][i]),
                        "id": doc_id,
                    }
                )

    # 4. Re-Ranking (Technique 4)
    final_results = []

    if reranker and candidates:
        # Préparer les paires [Query, Document Text]
        pairs = [
            [
                query.query,
                c["doc"].get("title", "") + ". " + c["doc"].get("abstract", ""),
            ]
            for c in candidates
        ]

        # Prédire les scores de pertinence
        rerank_scores = reranker.predict(pairs)

        # Associer les scores aux candidats
        for i, candidate in enumerate(candidates):
            candidate["rerank_score"] = float(rerank_scores[i])

        # Trier par score de re-ranking (décroissant)
        candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

        # Garder les top_k
        top_candidates = candidates[: query.top_k]

        for c in top_candidates:
            final_results.append(
                SearchResult(
                    id=c["id"],
                    score=c["rerank_score"],  # On renvoie le score du reranker
                    title=c["doc"].get("title"),
                    source=c["doc"].get("source"),
                    url=c["doc"].get("url"),
                    abstract=c["doc"].get("abstract"),
                )
            )

    else:
        # Fallback si pas de reranker (comportement original)
        top_candidates = candidates[: query.top_k]
        for c in top_candidates:
            final_results.append(
                SearchResult(
                    id=c["id"],
                    score=c["initial_score"],
                    title=c["doc"].get("title"),
                    source=c["doc"].get("source"),
                    url=c["doc"].get("url"),
                    abstract=c["doc"].get("abstract"),
                )
            )

    return SearchResponse(results=final_results)


@app.post("/summarize", response_model=SummarizeResponse)
def summarize_articles(request: SummarizeRequest):
    """
    Résume plusieurs articles individuellement et crée un résumé global.
    """
    summarizer = search_engine_components.get("summarizer")

    if not summarizer:
        raise HTTPException(
            status_code=503,
            detail="Le modèle de résumé n'est pas disponible. Vérifiez que le modèle LoRA est chargé.",
        )

    # Générer les résumés
    result = summarizer.summarize_multiple(request.articles)

    return SummarizeResponse(**result)


@app.get("/health")
def health_check():
    """
    Vérification de l'état de l'API et de ses composants.
    """
    return {
        "status": "healthy",
        "search_engine": "loaded"
        if search_engine_components.get("model")
        else "not loaded",
        "reranker": "loaded"
        if search_engine_components.get("reranker")
        else "not loaded",
        "summarizer": "loaded"
        if search_engine_components.get("summarizer")
        else "not loaded",
        "total_documents": len(search_engine_components.get("documents_by_id", {})),
    }


@app.get("/")
def root():
    """Page d'accueil de l'API"""
    return {
        "message": "🚀 Paper & Blog Recommender API + Summarizer (v2.1 with Re-Ranking)",
        "version": "2.1.0",
        "endpoints": {
            "/search": "Recherche sémantique avec Re-Ranking",
            "/summarize": "Résumé multi-documents avec IA",
            "/health": "Statut de l'API",
            "/docs": "Documentation interactive",
        },
    }
