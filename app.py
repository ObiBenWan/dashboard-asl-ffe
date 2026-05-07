import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Initialisation de Firebase (Sécurisée via Secrets)
if not firebase_admin._apps:
    try:
        # On transforme les secrets en dictionnaire
        fb_credentials = dict(st.secrets["firebase"])
        # On remplace les doubles backslash si nécessaire pour la clé privée
        fb_credentials["private_key"] = fb_credentials["private_key"].replace("\\n", "\n")
        
        cred = credentials.Certificate(fb_credentials)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Erreur de configuration Firebase : {e}")

db = firestore.client()

# --- INTERFACE ---
st.title("Accès Athlète")

# La case de saisie que tu as déjà créée
code_personnel = st.text_input("Entrez votre code personnel :", type="password")

if code_personnel:
    # On cherche le document dans la collection 'athletes'
    # L'ID du document DOIT être le code (ex: ATHLETE01)
    doc_ref = db.collection("athletes").document(code_personnel)
    doc = doc_ref.get()

    if doc.exists:
        profil_data = doc.to_dict()
        st.success(f"Bienvenue !")
        
        # --- AFFICHAGE DES DONNÉES DU JSON ---
        # Ici, on adapte selon ce qu'il y a dans ton JSON
        st.header(f"Profil de {profil_data.get('nom', 'Athlète')}")
        
        # Exemple d'affichage de texte et graphiques
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Niveau", profil_data.get("niveau", "N/A"))
        with col2:
            st.metric("Points", profil_data.get("points", "0"))
            
        # Si tu as une liste de scores pour un graphique
        if "performances" in profil_data:
            st.line_chart(profil_data["performances"])
            
    else:
        st.error("Code personnel inconnu. Veuillez vérifier votre saisie.")
