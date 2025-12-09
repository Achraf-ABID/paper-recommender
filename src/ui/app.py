# src/ui/app.py

import streamlit as st
import requests

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Paper & Blog Recommender + AI Summarizer", page_icon="🚀", layout="wide"
)

# URL de notre API FastAPI
API_SEARCH_URL = "http://127.0.0.1:8000/search"
API_SUMMARIZE_URL = "http://127.0.0.1:8000/summarize"
API_HEALTH_URL = "http://127.0.0.1:8000/health"

# --- INTERFACE UTILISATEUR ---

st.title("🚀 Moteur de Recommandation + Résumé Intelligent")
st.write(
    "✨ **Nouveau !** Obtenez non seulement des articles pertinents, mais aussi des résumés individuels et un résumé global !"
)

# Vérifier l'état de l'API
try:
    health_response = requests.get(API_HEALTH_URL, timeout=2)
    if health_response.status_code == 200:
        health_data = health_response.json()
        with st.sidebar:
            if health_data.get("summarizer") == "loaded":
                st.success("🤖 IA de résumé : Activée")
            else:
                st.warning("⚠️ IA de résumé : Non disponible")
except:
    pass

# Barre de recherche
query = st.text_input(
    "🔍 Votre question :", placeholder="Ex: What is Retrieval Augmented Generation?"
)

# Options dans la sidebar
with st.sidebar:
    st.header("⚙️ Options")
    top_k = st.slider("Nombre d'articles", 2, 5, 3)
    generate_summaries = st.checkbox("Générer les résumés IA", value=True)

    st.markdown("### 📖 Comment ça marche?")
    st.markdown("""
    1. **🔍 Recherche** : Articles pertinents trouvés
    2. **✨ Résumé individuel** : Pour chaque article  
    3. **📋 Résumé global** : Synthèse de tous les articles
    """)

    st.markdown("### 🎯 Workflow")
    st.code("""
Articles recommandés (3-5)
         ↓
Résumés individuels
         ↓
Résumé global
    """)

# Bouton de recherche
if st.button("🚀 Rechercher", type="primary"):
    if query:
        with st.spinner("🔍 Recherche en cours..."):
            try:
                # 1. Recherche d'articles
                payload = {"query": query, "top_k": top_k}
                response = requests.post(API_SEARCH_URL, json=payload)

                if response.status_code == 200:
                    results = response.json()["results"]

                    if results:
                        st.success(f"✅ {len(results)} articles trouvés pour '{query}'")

                        # 2. Générer les résumés si demandé
                        summaries_data = None
                        if generate_summaries:
                            status_placeholder = st.empty()
                            status_placeholder.info(
                                "🤖 Génération des résumés avec IA (LoRA)... Cela peut prendre quelques secondes."
                            )

                            try:
                                summarize_payload = {"articles": results}
                                summarize_response = requests.post(
                                    API_SUMMARIZE_URL, json=summarize_payload
                                )

                                if summarize_response.status_code == 200:
                                    summaries_data = summarize_response.json()
                                    status_placeholder.empty()  # On nettoie le message de chargement
                                else:
                                    status_placeholder.error(
                                        f"Erreur lors de la génération des résumés: {summarize_response.status_code}"
                                    )
                            except Exception as e:
                                status_placeholder.error(f"Erreur: {e}")

                        # 3. Afficher le résumé global en premier
                        if summaries_data and summaries_data.get("global_summary"):
                            st.markdown("---")
                            st.markdown("## 📋 Résumé Global de Tous les Articles")
                            st.markdown(
                                "*Synthèse intelligente combinant tous les articles recommandés*"
                            )

                            st.info(summaries_data["global_summary"])

                            # Stats
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric(
                                    "Articles analysés",
                                    summaries_data["total_articles"],
                                )
                            with col2:
                                st.metric(
                                    "Résumés individuels",
                                    len(summaries_data["individual_summaries"]),
                                )
                            with col3:
                                st.metric(
                                    "Longueur résumé global",
                                    f"{len(summaries_data['global_summary'].split())} mots",
                                )

                            st.markdown("---")

                        # 4. Afficher les articles individuels
                        st.markdown("## 📚 Articles Recommandés (avec résumés)")

                        for i, result in enumerate(results):
                            with st.expander(
                                f"**{i + 1}. {result['title']}** (Score: {result['score']:.2f})",
                                expanded=(i == 0),
                            ):
                                col1, col2 = st.columns([3, 1])

                                with col1:
                                    st.markdown(f"**Source :** {result['source']}")
                                    st.markdown(
                                        f"**URL :** [{result['url']}]({result['url']})"
                                    )

                                with col2:
                                    st.metric("Similarité", f"{result['score']:.3f}")

                                # Résumé IA si disponible
                                if summaries_data and i < len(
                                    summaries_data.get("individual_summaries", [])
                                ):
                                    st.markdown("### ✨ Résumé IA (LoRA Fine-tuned)")
                                    st.success(
                                        summaries_data["individual_summaries"][i][
                                            "summary"
                                        ]
                                    )

                                    # Abstract original dans un expander
                                    with st.expander("📄 Voir l'abstract original"):
                                        st.write(result["abstract"])
                                else:
                                    # Pas de résumé, afficher l'abstract
                                    st.markdown("### 📄 Abstract")
                                    st.write(result["abstract"])
                    else:
                        st.warning("Aucun résultat trouvé pour cette recherche.")

                else:
                    st.error(f"Erreur de l'API (Code: {response.status_code})")
                    st.error("Le backend est-il bien lancé?")
                    st.info(
                        "💡 Lancez le backend avec: `python -m uvicorn src.api.main:app --reload`"
                    )

            except requests.exceptions.ConnectionError:
                st.error("❌ Impossible de se connecter à l'API")
                st.error("Assurez-vous que le backend est lancé!")
                st.info(
                    "💡 Lancez le backend avec: `python -m uvicorn src.api.main:app --reload`"
                )
            except Exception as e:
                st.error(f"Erreur: {e}")
    else:
        st.info("Veuillez entrer une question pour lancer la recherche.")

# Footer
st.markdown("---")
st.markdown(
    """
<div style='text-align: center; color: gray;'>
    <p>🤖 Propulsé par LoRA Fine-tuned BART + FAISS + Sentence Transformers</p>
</div>
""",
    unsafe_allow_html=True,
)
