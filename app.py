import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import pandas as pd

# 1. STYLE CSS POUR LES COULEURS DU CLUB
# Change les codes HEX (#...) pour correspondre exactement à tes couleurs
club_css = """
<style>
    /* Fond de la page */
    .stApp {
        background-color: #0E1117; /* Noir/Gris foncé */
    }
    
    /* Style du titre */
    h1 {
        color: #FFD700 !important; /* Or/Jaune ASL */
        text-align: center;
        font-family: 'Arial Black', sans-serif;
    }
    
    /* Style des boutons */
    .stButton>button {
        background-color: #FFD700 !important;
        color: black !important;
        font-weight: bold;
        border-radius: 10px;
        border: none;
        height: 3em;
        width: 100%;
    }
    
    /* Les boîtes de saisie */
    .stTextInput>div>div>input {
        background-color: #1A1C24;
        color: white;
        border: 1px solid #FFD700;
    }

    /* Logo centré */
    .logo-container {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }
</style>
"""

st.set_page_config(page_title="ASL-FFE Profil", layout="centered", initial_sidebar_state="collapsed")
st.markdown(club_css, unsafe_allow_html=True)

# --- CONNEXION FIREBASE (Identique) ---
if not firebase_admin._apps:
    try:
        fb_credentials = dict(st.secrets["firebase"])
        fb_credentials["private_key"] = fb_credentials["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(fb_credentials)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Erreur : {e}")

db = firestore.client()

if 'auth_success' not in st.session_state:
    st.session_state.auth_success = False

# --- PAGE DE LOGIN (DESIGN CLUB) ---
if not st.session_state.auth_success:
    
    # 1. Affichage du Logo (Remplace l'URL par la tienne ou le nom de ton fichier sur GitHub)
    # Si le fichier est sur GitHub : st.image("logo_club.png", width=120)
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image("https://studio-7691886667-ec4b3.web.app/logo.png", width=150) # Tente de récupérer l'ancien logo
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<h1>PROFIL COMBATTANT</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: white;'>Accès réservé aux membres de l'ASL-FFE</p>", unsafe_allow_html=True)

    with st.container():
        prenom = st.text_input("Prénom")
        code_acces = st.text_input("Code d'accès", type="password")
        
        if st.button("ACCÉDER AU PROFIL"):
            if prenom and code_acces:
                doc_ref = db.collection("athletes").document(code_acces.lower())
                doc = doc_ref.get()

                if doc.exists:
                    st.session_state.auth_success = True
                    st.session_state.prenom_utilisateur = prenom
                    st.session_state.code_valide = code_acces.lower()
                    st.rerun()
                else:
                    st.error("Code d'accès incorrect.")

# --- PAGE PROFIL (APRÈS LOGIN) ---
else:
    # On peut changer le fond pour la page profil si besoin
    st.title(f"Salut {st.session_state.prenom_utilisateur} !")
    
    doc_ref = db.collection("athletes").document(st.session_state.code_valide)
    doc = doc_ref.get()
    data = json.loads(doc.to_dict()["json_data"])
    match = data['history'][0]

    # ... reste du code pour les graphiques ...
    st.success(f"Match enregistré le {match['date'][:10]}")
    st.metric("Explosivité", f"{match['metrics']['explosivite']}%")
    
    if st.button("Déconnexion"):
        st.session_state.auth_success = False
        st.rerun()
