import streamlit as st
from google.cloud import firestore
import json

# Connexion sécurisée à Firestore
# La configuration est récupérée depuis les 'Secrets' de l'interface Streamlit
db = firestore.Client.from_service_account_info(st.secrets["firebase"])

st.title("Accès Athlète")

# Saisie du code
code_entree = st.text_input("Entrez votre code personnel :", type="password")

if code_entree:
    # On va chercher le document dont l'ID est égal au code entré
    doc_ref = db.collection("athletes").document(code_entree)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict()
        
        # Affichage des données (à adapter selon les clés de ton JSON)
        st.success(f"Profil trouvé pour le code : {code_entree}")
        
        # Exemple de rendu graphique basique avec Plotly ou Streamlit
        st.json(data) # Affiche le JSON brut pour vérifier
        
        # Tu peux ici ajouter tes graphiques basés sur 'data'
        # st.line_chart(data['ton_champ_historique'])
        
    else:
        st.error("Code invalide ou inexistant.")