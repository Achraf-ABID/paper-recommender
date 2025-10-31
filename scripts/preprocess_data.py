# scripts/preprocess_data.py

import os
import json
import re
import fitz  # PyMuPDF

# --- CONFIGURATION DES CHEMINS ---
ARXIV_RAW_DIR = "data/raw/arxiv"
BLOGS_NORMALIZED_DIR = "data/normalized/blogs"
PROCESSED_OUTPUT_DIR = "data/processed"
PROCESSED_OUTPUT_FILE = os.path.join(PROCESSED_OUTPUT_DIR, "processed_corpus.jsonl")

def clean_text(text: str) -> str:
    """
    Applique une série de nettoyages standards sur un bloc de texte.
    """
    if not text:
        return ""
    
    # Remplacer les multiples sauts de ligne par un seul
    text = re.sub(r'\n\s*\n', '\n\n', text)
    # Remplacer les multiples espaces par un seul
    text = re.sub(r'\s{2,}', ' ', text)
    # Supprimer les espaces en début et fin de ligne
    text = '\n'.join([line.strip() for line in text.split('\n')])
    
    return text.strip()

def process_arxiv_papers():
    """
    Traite tous les articles d'ArXiv : lit les métadonnées JSON,
    extrait le texte du PDF correspondant et nettoie le contenu.
    Retourne une liste de dictionnaires de documents traités.
    """
    print(f"\n--- Traitement des articles d'ArXiv depuis : {ARXIV_RAW_DIR} ---")
    processed_docs = []
    
    if not os.path.exists(ARXIV_RAW_DIR):
        print(f"[AVERTISSEMENT] Le dossier ArXiv n'existe pas. Ignoré.")
        return []

    for filename in os.listdir(ARXIV_RAW_DIR):
        if filename.endswith(".json"):
            json_filepath = os.path.join(ARXIV_RAW_DIR, filename)
            pdf_filepath = json_filepath.replace(".json", ".pdf")

            if not os.path.exists(pdf_filepath):
                print(f"  [AVERTISSEMENT] PDF manquant pour {filename}. Ignoré.")
                continue

            try:
                # 1. Lire les métadonnées
                with open(json_filepath, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # 2. Extraire le texte du PDF
                full_text = ""
                with fitz.open(pdf_filepath) as doc:
                    for page in doc:
                        full_text += page.get_text()
                
                # 3. Nettoyer le texte
                cleaned_text = clean_text(full_text)
                
                # 4. Créer le document unifié
                processed_doc = {
                    "id": f"arxiv_{metadata['paper_id']}",
                    "source": "arxiv.org",
                    "url": f"https://arxiv.org/abs/{metadata['paper_id']}",
                    "title": metadata.get("title", "Titre non trouvé"),
                    "published_date": metadata.get("published_date"),
                    "authors": metadata.get("authors", []),
                    "abstract": metadata.get("summary", ""),
                    "full_text": cleaned_text
                }
                processed_docs.append(processed_doc)
                print(f"  [OK] Traité : {metadata['paper_id']} - {metadata['title'][:50]}...")

            except Exception as e:
                print(f"  [ERREUR] Échec du traitement de {filename}: {e}")
                
    return processed_docs

def process_blog_posts():
    """
    Traite tous les blogs depuis les métadonnées normalisées.
    Retourne une liste de dictionnaires de documents traités.
    """
    print(f"\n--- Traitement des articles de Blogs depuis : {BLOGS_NORMALIZED_DIR} ---")
    processed_docs = []

    if not os.path.exists(BLOGS_NORMALIZED_DIR):
        print(f"[AVERTISSEMENT] Le dossier de blogs normalisés n'existe pas. Ignoré.")
        return []
        
    for filename in os.listdir(BLOGS_NORMALIZED_DIR):
        if filename.endswith("_metadata.json") and filename != "all_blogs_metadata.json":

            filepath = os.path.join(BLOGS_NORMALIZED_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                cleaned_text = clean_text(metadata.get("raw_text", ""))
                
                processed_doc = {
                    "id": metadata.get("id"),
                    "source": metadata.get("source"),
                    "url": metadata.get("url"),
                    "title": metadata.get("title", "Titre non trouvé"),
                    "published_date": metadata.get("date"),
                    "authors": metadata.get("authors", []),
                    "abstract": metadata.get("abstract", metadata.get("first_paragraph", "")),
                    "full_text": cleaned_text
                }
                processed_docs.append(processed_doc)
                print(f"  [OK] Traité : {metadata['id']} - {metadata['title'][:50]}...")

            except Exception as e:
                print(f"  [ERREUR] Échec du traitement de {filename}: {e}")
    
    return processed_docs


def main():
    """
    Orchestre le processus complet de prétraitement.
    """
    print("="*60)
    print("Démarrage de la Phase 3 : Prétraitement et Nettoyage des Données")
    print("="*60)

    # Créer le dossier de sortie
    os.makedirs(PROCESSED_OUTPUT_DIR, exist_ok=True)

    # Traiter les deux sources
    arxiv_docs = process_arxiv_papers()
    blog_docs = process_blog_posts()

    # Combiner les corpus
    all_docs = arxiv_docs + blog_docs

    # Sauvegarder dans un fichier JSON Lines
    # JSONL est un format efficace pour de grands ensembles de données textuelles
    with open(PROCESSED_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for doc in all_docs:
            f.write(json.dumps(doc, ensure_ascii=False) + '\n')

    print("\n" + "="*60)
    print("✅ Phase 3 terminée !")
    print(f"Total de documents traités : {len(all_docs)}")
    print(f"Corpus unifié sauvegardé dans : {PROCESSED_OUTPUT_FILE}")
    print("="*60)


if __name__ == "__main__":
    main()