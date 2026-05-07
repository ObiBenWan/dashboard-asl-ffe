import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import pandas as pd

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="ASL-FFE - Profil Combattant", layout="centered", initial_sidebar_state="collapsed")

# 2. DESIGN CSS AVANCÉ (Conteneur centré et Logo agrandi)
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');
    
    /* Global */
    .stApp {{
        background-color: hsl(180, 25%, 15%);
        font-family: 'Space Grotesk', sans-serif;
        display: flex;
        justify-content: center;
        align-items: center;
    }}

    /* Masquer les éléments Streamlit inutiles en haut */
    header {{visibility: hidden;}}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* Conteneur Principal (La Card) */
    .main-container {{
        background-color: hsl(180, 25%, 20%);
        border: 1px solid hsl(180, 25%, 25%);
        border-radius: 1rem;
        padding: 3rem 2rem;
        width: 100%;
        max-width: 450px;
        margin: auto;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
        text-align: center;
    }}

    /* Logo */
    .logo-img {{
        width: 200px; /* Plus grand */
        margin-bottom: 1.5rem;
    }}

    /* Titre */
    .main-title {{
        font-size: 1.8rem;
        font-weight: 700;
        color: hsl(210, 20%, 95%);
        margin-bottom: 0.5rem;
        letter-spacing: -0.025em;
    }}

    .sub-title {{
        color: hsl(180, 10%, 60%);
        font-size: 0.9rem;
        margin-bottom: 2rem;
    }}

    /* Personnalisation des Inputs Streamlit pour qu'ils s'intègrent au design */
    .stTextInput label {{
        color: hsl(180, 10%, 60%) !important;
        font-size: 0.8rem !important;
    }}
    
    .stTextInput div div input {{
        background-color: hsl(180, 25%, 25%) !important;
        border: 1px solid hsl(180, 25%, 25%) !important;
        color: white !important;
        border-radius: 0.5rem !important;
        height: 3rem !important;
    }}

    /* Bouton */
    .stButton > button {{
        background-color: hsl(182, 100%, 74%) !important;
        color: hsl(180, 25%, 10%) !important;
        border: none !important;
        border-radius: 0.5rem !important;
        height: 3.5rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        width: 100% !important;
        margin-top: 1rem !important;
        transition: all 0.3s ease !important;
    }}

    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(182, 255, 252, 0.3);
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. INITIALISATION FIREBASE
if not firebase_admin._apps:
    try:
        fb_credentials = dict(st.secrets["firebase"])
        fb_credentials["private_key"] = fb_credentials["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(fb_credentials)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Erreur connexion : {e}")

db = firestore.client()

if 'auth_success' not in st.session_state:
    st.session_state.auth_success = False

# --- LOGIQUE D'AFFICHAGE ---

if not st.session_state.auth_success:
    # On crée le conteneur HTML pour le centrage visuel
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Logo et Titres en HTML pour un contrôle total
    st.markdown(f"""
        <img src="https://studio-7691886667-ec4b3.web.app/logo.png" class="logo-img">
        <div class="main-title">PROFIL COMBATTANT</div>
        <div class="sub-title">Accédez à vos analyses ASL-FFE</div>
    """, unsafe_allow_html=True)

    # Les champs Streamlit (placés dans le flux HTML par le container)
    prenom = st.text_input("Prénom", placeholder="Ex: Léandre")
    code_acces = st.text_input("Code d'accès", type="password", placeholder="••••••••")

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
                st.error("Code d'accès invalide.")
        else:
            st.warning("Merci de remplir tous les champs.")
            
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- PAGE DE PROFIL (AFFICHÉE APRÈS CONNEXION) ---
    doc_ref = db.collection("athletes").document(st.session_state.code_valide)
    doc = doc_ref.get()
    
    if doc.exists:
        raw_data = doc.to_dict().get("json_data")
        data = json.loads(raw_data)
        match = data['history'][0]

        st.title(f"Salut, {st.session_state.prenom_utilisateur} !")
        
        # Affichage rapide pour tester la data
        col1, col2 = st.columns(2)
        col1.metric("Résultat", match['result'].upper())
        col2.metric("Score", f"{match['myScore']} - {match['oppScore']}")

        if st.button("Se déconnecter"):
            st.session_state.auth_success = False
            st.rerun()
