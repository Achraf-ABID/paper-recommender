# scripts/generate_embeddings.py

import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORPUS_FILE = os.path.join(BASE_DIR, "../data/processed/processed_corpus.jsonl")
OUTPUT_DIR = os.path.join(BASE_DIR, "../data/embeddings")
INDEX_FILE = os.path.join(OUTPUT_DIR, "document_index.faiss")
MAPPING_FILE = os.path.join(OUTPUT_DIR, "index_to_id_mapping.json")

# Choix du modèle. 'all-MiniLM-L6-v2' est un excellent compromis entre vitesse et performance.
MODEL_NAME = "all-MiniLM-L6-v2"


def create_text_for_embedding(doc: dict) -> str:
    """
    Crée une chaîne de texte optimisée pour l'embedding.
    On combine le titre et le résumé pour capturer l'essence du document.
    """
    title = doc.get("title", "")
    abstract = doc.get("abstract", "")

    # Si l'abstract est court, on peut prendre le début du texte complet
    if not abstract or len(abstract) < 100:
        abstract = doc.get("full_text", "")[:500]

    return f"{title}\n{abstract}".strip()


def main():
    """
    Script principal pour générer les embeddings et l'index FAISS.
    """
    print("=" * 60)
    print("Démarrage de la Phase 4 : Génération d'Embeddings et Indexation")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- 1. Charger les documents ---
    if not os.path.exists(CORPUS_FILE):
        print(f"[ERREUR] Le fichier corpus '{CORPUS_FILE}' n'a pas été trouvé.")
        print("Veuillez d'abord exécuter le script de prétraitement.")
        return

    print(f"Chargement du corpus depuis : {CORPUS_FILE}")
    documents = []
    with open(CORPUS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            documents.append(json.loads(line))

    print(f"Total de documents à traiter : {len(documents)}")

    # --- 2. Charger le modèle d'embedding ---
    # SentenceTransformer va télécharger et mettre en cache le modèle automatiquement.
    print(f"Chargement du modèle SentenceTransformer : '{MODEL_NAME}'...")
    model = SentenceTransformer(MODEL_NAME)
    print("Modèle chargé avec succès.")

    # --- 3. Créer le texte pour l'embedding ---
    texts_to_embed = [create_text_for_embedding(doc) for doc in documents]

    # --- 4. Générer les embeddings ---
    # model.encode() est hautement optimisé et peut utiliser le GPU si disponible.
    print("Génération des embeddings... (cela peut prendre quelques minutes)")
    # Le paramètre show_progress_bar affiche une barre de progression
    embeddings = model.encode(texts_to_embed, show_progress_bar=True)
    print(f"Embeddings générés. Forme de la matrice : {embeddings.shape}")

    # Normalisation L2 - Étape importante pour la recherche de similarité cosinus
    faiss.normalize_L2(embeddings)

    # --- 5. Créer et peupler l'index FAISS ---
    embedding_dim = embeddings.shape[1]

    # IndexFlatIP : index simple basé sur le produit scalaire (Inner Product).
    # Equivalent à la similarité cosinus sur des vecteurs normalisés.
    index = faiss.IndexFlatIP(embedding_dim)

    print("Création et peuplement de l'index FAISS...")
    index.add(embeddings)

    print(f"Index créé. Nombre total de vecteurs dans l'index : {index.ntotal}")

    # --- 6. Sauvegarder l'index et le mapping ---
    print(f"Sauvegarde de l'index dans : {INDEX_FILE}")
    faiss.write_index(index, INDEX_FILE)

    # Créer un mapping de l'indice de l'index (0, 1, 2...) à notre ID de document
    index_to_id = {i: doc["id"] for i, doc in enumerate(documents)}

    print(f"Sauvegarde du mapping dans : {MAPPING_FILE}")
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(index_to_id, f)

    print("\n" + "=" * 60)
    print("✅ Phase 4 terminée !")
    print(f"Index FAISS et mapping sauvegardés dans le dossier : {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
