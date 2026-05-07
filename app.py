import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import pandas as pd

# 1. CONFIGURATION ET DESIGN
st.set_page_config(page_title="ASL-FFE - Login", layout="centered", initial_sidebar_state="collapsed")

# Injection de ton CSS personnalisé
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');
    
    /* On cible l'application Streamlit */
    .stApp {{
        background-color: hsl(180, 25%, 15%);
        font-family: 'Space Grotesk', sans-serif;
    }}

    /* Conteneur principal style "Card" */
    .login-card {{
        background-color: hsl(180, 25%, 20%);
        border-radius: 0.75rem;
        border: 1px solid hsl(180, 25%, 25%);
        padding: 2rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        max-width: 400px;
        margin: auto;
    }}

    /* Titres */
    h1, h2, h3 {{
        color: hsl(210, 20%, 95%) !important;
        text-align: center;
    }}

    /* Inputs */
    .stTextInput>div>div>input {{
        background-color: hsl(180, 25%, 25%);
        border: 1px solid hsl(180, 25%, 25%);
        color: white;
        border-radius: 0.375rem;
    }}

    /* Bouton personnalisé */
    .stButton>button {{
        background-color: hsl(182, 100%, 74%) !important;
        color: hsl(180, 25%, 10%) !important;
        font-weight: 700;
        width: 100%;
        border-radius: 0.375rem;
        border: none;
        height: 3rem;
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. CONNEXION FIREBASE
if not firebase_admin._apps:
    try:
        fb_credentials = dict(st.secrets["firebase"])
        fb_credentials["private_key"] = fb_credentials["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(fb_credentials)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Erreur connexion : {e}")

db = firestore.client()

# 3. LOGIQUE D'AUTHENTIFICATION
if 'auth_success' not in st.session_state:
    st.session_state.auth_success = False

# --- INTERFACE DE CONNEXION ---
if not st.session_state.auth_success:
    # Centrage vertical
    st.write("#")
    
    # On recrée la structure de ta Card
    with st.container():
        # Logo
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("https://studio-7691886667-ec4b3.web.app/logo.png", width=150)
        
        st.markdown("<h1>PROFIL COMBATTANT</h1>", unsafe_allow_html=True)
        
        # Champs de saisie
        prenom = st.text_input("Prénom")
        code_acces = st.text_input("Code d'accès", type="password")
        
        st.write("#") # Espace
        
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
                    st.error("Code ou Prénom inconnu.")

# --- INTERFACE PROFIL (UNE FOIS CONNECTÉ) ---
else:
    doc_ref = db.collection("athletes").document(st.session_state.code_valide)
    doc = doc_ref.get()
    
    if doc.exists:
        # On récupère le texte JSON stocké
        raw_data = doc.to_dict().get("json_data")
        data = json.loads(raw_data)
        match = data['history'][0]

        st.title(f"Bonjour {st.session_state.prenom_utilisateur} !")
        
        # Exemple d'affichage des scores
        c1, c2 = st.columns(2)
        c1.metric("Ton Score", match['myScore'])
        c2.metric("Adversaire", match['oppScore'])
        
        # Graphique
        df = pd.DataFrame(match['exchanges'])
        st.line_chart(df.set_index('exchange_num')['avg_wrist_v'])
        
        if st.button("Se déconnecter"):
            st.session_state.auth_success = False
            st.rerun()
