import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import pandas as pd

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="ASL-FFE - Profil Combattant", layout="wide", initial_sidebar_state="collapsed")

# 2. INJECTION DU DESIGN (Variables HSL fournies)
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');
    
    /* Configuration des couleurs et du fond */
    .stApp {{
        background-color: hsl(180, 25%, 15%);
        font-family: 'Space Grotesk', sans-serif;
    }}

    /* Masquer le header Streamlit */
    header {{visibility: hidden;}}

    /* Style du conteneur "Card" (le bloc central) */
    [data-testid="stVerticalBlock"] > div:has(div.card-container) {{
        background-color: hsl(180, 25%, 20%);
        border: 1px solid hsl(180, 25%, 25%);
        border-radius: 0.75rem;
        padding: 40px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }}

    /* Titres */
    .login-title {{
        color: hsl(210, 20%, 95%);
        font-size: 1.8rem;
        font-weight: 700;
        text-align: center;
        margin-top: 10px;
        margin-bottom: 30px;
        letter-spacing: -0.025em;
    }}

    /* Inputs */
    .stTextInput label {{
        color: hsl(180, 10%, 60%) !important;
    }}
    .stTextInput div div input {{
        background-color: hsl(180, 25%, 25%) !important;
        border: 1px solid hsl(180, 25%, 25%) !important;
        color: white !important;
    }}

    /* Bouton (Couleur Primary) */
    .stButton > button {{
        background-color: hsl(182, 100%, 74%) !important;
        color: hsl(180, 25%, 10%) !important;
        font-weight: 700 !important;
        width: 100% !important;
        height: 3.5rem !important;
        border: none !important;
        margin-top: 20px;
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
        st.error(f"Erreur système : {e}")

db = firestore.client()

if 'auth_success' not in st.session_state:
    st.session_state.auth_success = False

# --- LOGIQUE DE CONNEXION ---

if not st.session_state.auth_success:
    # On crée 3 colonnes pour centrer le container au milieu
    col_left, col_center, col_right = st.columns([1, 2.5, 1])

    with col_center:
        # On utilise une div vide pour que le CSS puisse cibler ce bloc spécifique
        st.markdown('<div class="card-container"></div>', unsafe_allow_html=True)
        
        # Le contenu est maintenant TOUT dans ce bloc
        st.image("https://studio-7691886667-ec4b3.web.app/logo.png", use_container_width=True)
        
        st.markdown('<h1 class="login-title">PROFIL COMBATTANT</h1>', unsafe_allow_html=True)
        
        prenom = st.text_input("Prénom")
        code_acces = st.text_input("Code d'accès", type="password")

        if st.button("ACCÉDER AU PROFIL"):
            if prenom and code_acces:
                # Recherche dans Firebase
                doc_ref = db.collection("athletes").document(code_acces.lower())
                doc = doc_ref.get()
                
                if doc.exists:
                    st.session_state.auth_success = True
                    st.session_state.prenom_utilisateur = prenom
                    st.session_state.code_valide = code_acces.lower()
                    st.rerun()
                else:
                    st.error("Identifiants incorrects.")
            else:
                st.warning("Veuillez remplir tous les champs.")

# --- PAGE PROFIL (DÉVERROUILLÉE) ---
else:
    doc_ref = db.collection("athletes").document(st.session_state.code_valide)
    doc = doc_ref.get()
    
    if doc.exists:
        data = json.loads(doc.to_dict().get("json_data"))
        match = data['history'][0]

        st.title(f"Bienvenue, {st.session_state.prenom_utilisateur}")
        st.divider()
        
        # Affichage rapide
        c1, c2 = st.columns(2)
        c1.metric("Résultat", match['result'].upper())
        c2.metric("Score", f"{match['myScore']} - {match['oppScore']}")

        if st.button("Déconnexion"):
            st.session_state.auth_success = False
            st.rerun()
