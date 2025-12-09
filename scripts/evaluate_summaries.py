"""
Script d'évaluation des résumés générés avec ROUGE et BERTScore
"""

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import evaluate
import pandas as pd
from tqdm import tqdm
import json

# ==========================================
# 1. CONFIGURATION
# ==========================================

# Chemins du modèle fine-tuné
# Chemins du modèle fine-tuné
MODEL_PATH = "../models/bart-lora-finetuned"  # Chemin vers votre modèle LoRA
# MODEL_PATH = "facebook/bart-large-cnn"  # Fallback

# Fichier de données de test (format: articles + résumés de référence)
TEST_DATA_PATH = "../test_data_example.json"  # Chemin corrigé

# Paramètres de génération
MAX_INPUT_LENGTH = 1024
MAX_OUTPUT_LENGTH = 150
NUM_BEAMS = 4

# ==========================================
# 2. CHARGEMENT DES MÉTRIQUES
# ==========================================

print("📊 Chargement des métriques d'évaluation...")

# ROUGE: mesure le chevauchement de n-grammes
rouge = evaluate.load("rouge")

# BERTScore: mesure la similarité sémantique
bertscore = evaluate.load("bertscore")

# ==========================================
# 3. CHARGEMENT DU MODÈLE
# ==========================================

from peft import PeftModel, PeftConfig

print(f"🤖 Chargement du modèle: {MODEL_PATH}")

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"💻 Utilisation de: {device}")

# Chargement spécifique pour LoRA
try:
    config = PeftConfig.from_pretrained(MODEL_PATH)
    base_model = AutoModelForSeq2SeqLM.from_pretrained(config.base_model_name_or_path)
    model = PeftModel.from_pretrained(base_model, MODEL_PATH)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    print("✅ Modèle LoRA chargé avec succès")
except Exception as e:
    print(f"⚠️ Erreur chargement LoRA, essai chargement standard: {e}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)

model.to(device)
model.eval()

# ==========================================
# 4. FONCTION DE GÉNÉRATION DE RÉSUMÉ
# ==========================================


def generate_summary(article_text):
    """
    Génère un résumé pour un article donné

    Args:
        article_text (str): Texte de l'article

    Returns:
        str: Résumé généré
    """
    # Tokenisation
    inputs = tokenizer(
        article_text,
        max_length=MAX_INPUT_LENGTH,
        truncation=True,
        padding="max_length",
        return_tensors="pt",
    ).to(device)

    # Génération
    with torch.no_grad():
        summary_ids = model.generate(
            input_ids=inputs["input_ids"],  # Argument nommé obligatoire pour PEFT
            max_length=MAX_OUTPUT_LENGTH,
            num_beams=NUM_BEAMS,
            length_penalty=2.0,
            early_stopping=True,
        )

    # Décodage
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary


# ==========================================
# 5. FONCTION D'ÉVALUATION
# ==========================================


def evaluate_summaries(test_data):
    """
    Évalue les résumés générés par rapport aux résumés de référence

    Args:
        test_data (list): Liste de dictionnaires avec 'article' et 'reference_summary'

    Returns:
        dict: Scores ROUGE et BERTScore
    """
    generated_summaries = []
    reference_summaries = []

    print("\n🔄 Génération des résumés...")

    for item in tqdm(test_data):
        article = item["article"]
        reference = item["reference_summary"]

        # Générer le résumé
        generated = generate_summary(article)

        generated_summaries.append(generated)
        reference_summaries.append(reference)

    print("\n📈 Calcul des scores ROUGE...")

    # Calcul ROUGE
    rouge_scores = rouge.compute(
        predictions=generated_summaries, references=reference_summaries
    )

    print("\n📈 Calcul des scores BERTScore...")

    # Calcul BERTScore
    bertscore_results = bertscore.compute(
        predictions=generated_summaries,
        references=reference_summaries,
        lang="en",  # Changez en "fr" si vos résumés sont en français
    )

    # Moyennes BERTScore
    avg_bertscore = {
        "precision": sum(bertscore_results["precision"])
        / len(bertscore_results["precision"]),
        "recall": sum(bertscore_results["recall"]) / len(bertscore_results["recall"]),
        "f1": sum(bertscore_results["f1"]) / len(bertscore_results["f1"]),
    }

    return {
        "rouge": rouge_scores,
        "bertscore": avg_bertscore,
        "generated_summaries": generated_summaries,
        "reference_summaries": reference_summaries,
    }


# ==========================================
# 6. AFFICHAGE DES RÉSULTATS
# ==========================================


def display_results(results):
    """
    Affiche les résultats d'évaluation de manière lisible
    """
    print("\n" + "=" * 50)
    print("📊 RÉSULTATS D'ÉVALUATION")
    print("=" * 50)

    # ROUGE Scores
    print("\n🔴 ROUGE Scores:")
    print(f"  ROUGE-1: {results['rouge']['rouge1']:.4f}")
    print(f"  ROUGE-2: {results['rouge']['rouge2']:.4f}")
    print(f"  ROUGE-L: {results['rouge']['rougeL']:.4f}")

    # BERTScore
    print("\n🟢 BERTScore:")
    print(f"  Precision: {results['bertscore']['precision']:.4f}")
    print(f"  Recall:    {results['bertscore']['recall']:.4f}")
    print(f"  F1:        {results['bertscore']['f1']:.4f}")

    print("\n" + "=" * 50)


# ==========================================
# 7. FONCTION PRINCIPALE
# ==========================================


def main():
    """
    Fonction principale pour exécuter l'évaluation
    """
    print("🚀 Début de l'évaluation des résumés\n")

    # Charger les données de test
    print(f"📂 Chargement des données: {TEST_DATA_PATH}")

    # EXEMPLE DE FORMAT ATTENDU pour test_data.json:
    # [
    #   {
    #     "article": "Long article text here...",
    #     "reference_summary": "Reference summary here..."
    #   },
    #   ...
    # ]

    try:
        with open(TEST_DATA_PATH, "r", encoding="utf-8") as f:
            test_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {TEST_DATA_PATH}")
        print("\n💡 Créez un fichier JSON avec ce format:")
        print("""
[
  {
    "article": "Votre article complet ici...",
    "reference_summary": "Le résumé de référence ici..."
  }
]
        """)
        return

    print(f"✅ {len(test_data)} exemples chargés\n")

    # Évaluer
    results = evaluate_summaries(test_data)

    # Afficher les résultats
    display_results(results)

    # Sauvegarder les résultats
    output_file = "../results/evaluation_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "rouge": {
                    "rouge1": results["rouge"]["rouge1"],
                    "rouge2": results["rouge"]["rouge2"],
                    "rougeL": results["rouge"]["rougeL"],
                },
                "bertscore": results["bertscore"],
            },
            f,
            indent=2,
        )

    print(f"\n💾 Résultats sauvegardés dans: {output_file}")


# ==========================================
# EXEMPLE D'UTILISATION AVEC VOS PROPRES DONNÉES
# ==========================================


def evaluate_single_summary(article, reference_summary):
    """
    Évalue un seul résumé (utile pour tester rapidement)

    Args:
        article (str): Texte de l'article
        reference_summary (str): Résumé de référence
    """
    generated = generate_summary(article)

    rouge_scores = rouge.compute(
        predictions=[generated], references=[reference_summary]
    )

    bertscore_results = bertscore.compute(
        predictions=[generated], references=[reference_summary], lang="en"
    )

    print("\n📄 Résumé généré:")
    print(generated)
    print("\n📄 Résumé de référence:")
    print(reference_summary)
    print("\n📊 Scores:")
    print(f"ROUGE-1: {rouge_scores['rouge1'].mid.fmeasure:.4f}")
    print(f"ROUGE-2: {rouge_scores['rouge2'].mid.fmeasure:.4f}")
    print(f"BERTScore F1: {bertscore_results['f1'][0]:.4f}")


# ==========================================
# EXÉCUTION
# ==========================================

if __name__ == "__main__":
    main()

    # Ou pour tester avec un seul exemple:
    # evaluate_single_summary(
    #     article="Your article text...",
    #     reference_summary="Your reference summary..."
    # )
