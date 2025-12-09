"""
Module de résumé avec le modèle LoRA fine-tuné
"""

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel, PeftConfig
import torch
from typing import List, Optional


class LoRASummarizer:
    """Classe pour gérer le résumé avec le modèle LoRA"""

    def __init__(self, model_path: str):
        """
        Initialise le résumeur avec le modèle LoRA

        Args:
            model_path: Chemin vers le dossier du modèle LoRA
        """
        print(f"🤖 Chargement du modèle de résumé depuis {model_path}...")

        try:
            # Charger la configuration LoRA
            config = PeftConfig.from_pretrained(model_path)

            # Charger le modèle de base
            base_model = AutoModelForSeq2SeqLM.from_pretrained(
                config.base_model_name_or_path
            )

            # Charger les adaptateurs LoRA
            self.model = PeftModel.from_pretrained(base_model, model_path)

            # Charger le tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)

            # Détecter le device
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            self.model.eval()

            print(f"✅ Modèle chargé sur {self.device.upper()}")

        except Exception as e:
            print(f"❌ Erreur lors du chargement du modèle: {e}")
            raise

    def summarize_single(
        self,
        text: str,
        max_length: int = 150,  # Augmenté pour plus de détails
        min_length: int = 50,
        num_beams: int = 4,  # Augmenté pour la qualité
        length_penalty: float = 2.0,
    ) -> str:
        """
        Résume un seul article avec des paramètres optimisés pour la qualité
        """
        # Technique 2: Prompt Engineering (Contextualisation)
        prompt = f"Summarize the following technical article concisely:\n\n{text}"

        # Tokenizer
        inputs = self.tokenizer(
            prompt, return_tensors="pt", max_length=1024, truncation=True
        ).to(self.device)

        # Génération avec paramètres anti-répétition (Technique 1)
        with torch.no_grad():
            summary_ids = self.model.generate(
                input_ids=inputs["input_ids"],
                max_length=max_length,
                min_length=min_length,
                length_penalty=length_penalty,
                num_beams=num_beams,
                no_repeat_ngram_size=3,  # Empêche les répétitions de 3 mots
                repetition_penalty=1.2,  # Punit les répétitions
                early_stopping=True,
            )

        # Décoder
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary

    def summarize_multiple(
        self,
        articles: List[dict],
        individual_max_length: int = 120,
        global_max_length: int = 250,
    ) -> dict:
        """
        Résume plusieurs articles avec une stratégie Map-Reduce améliorée
        """
        individual_summaries = []

        # 1. Résumer chaque article individuellement
        for article in articles:
            # On combine titre et abstract pour plus de contexte
            text = f"Title: {article.get('title', '')}\nContent: {article.get('abstract', '')}"

            summary = self.summarize_single(
                text, max_length=individual_max_length, min_length=40
            )
            individual_summaries.append(
                {
                    "title": article.get("title"),
                    "summary": summary,
                    "source": article.get("source"),
                    "url": article.get("url"),
                }
            )

        # 2. Créer un résumé global (Technique 3: Stratégie améliorée)
        # On utilise les résumés individuels comme base
        combined_text = " ".join(
            [
                f"Source {i + 1}: {summ['summary']}"
                for i, summ in enumerate(individual_summaries)
            ]
        )

        # Prompt spécifique pour la synthèse
        synthesis_prompt = f"Synthesize these summaries into a single coherent technical overview:\n\n{combined_text}"

        global_summary = self.summarize_single(
            synthesis_prompt,
            max_length=global_max_length,
            min_length=100,
            num_beams=5,  # Qualité maximale pour le résumé final
            length_penalty=2.5,
        )

        return {
            "individual_summaries": individual_summaries,
            "global_summary": global_summary,
            "total_articles": len(articles),
        }
