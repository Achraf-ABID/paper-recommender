
# src/ui/app.py

import streamlit as st
import requests
import pandas as pd

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Paper & Blog Recommender",
    page_icon="🚀",
    layout="wide"
)

# URL de notre API FastAPI (qui doit être en cours d'exécution)
API_URL = "http://127.0.0.1:8000/search"

# --- INTERFACE UTILISATEUR ---

st.title("🚀 Moteur de Recommandation de Documents Techniques")
st.write("Posez une question sur un sujet technique (IA, LLM, RAG, etc.) et découvrez les articles et blogs les plus pertinents.")

# Barre de recherche
query = st.text_input("Votre question :", placeholder="Ex: What is Retrieval Augmented Generation?")

# Bouton de recherche
if st.button("Rechercher"):
    if query:
        with st.spinner("Recherche en cours..."):
            try:
                # 1. Préparer la requête pour l'API
                payload = {"query": query, "top_k": 5}
                
                # 2. Appeler l'API
                response = requests.post(API_URL, json=payload)
                
                # 3. Traiter la réponse
                if response.status_code == 200:
                    results = response.json()['results']
                    
                    if results:
                        st.success(f"{len(results)} résultats trouvés pour '{query}'")
                        
                        # 4. Afficher les résultats
                        for i, result in enumerate(results):
                            with st.expander(f"**{i+1}. {result['title']}** (Similarité: {result['score']:.2f})"):
                                st.markdown(f"**Source :** {result['source']}")
                                st.markdown(f"**URL :** [{result['url']}]({result['url']})")
                                st.markdown("**Résumé :**")
                                st.write(result['abstract'])
                    else:
                        st.warning("Aucun résultat trouvé.")
                else:
                    st.error(f"Erreur de l'API (Code: {response.status_code}). Le backend est-il bien en cours d'exécution ?")
                    st.json(response.text)

            except requests.exceptions.RequestException as e:
                st.error(f"Erreur de connexion à l'API. Assurez-vous que le serveur backend est lancé à l'adresse {API_URL}")
                st.error(e)
    else:
        st.info("Veuillez entrer une question pour lancer la recherche.")