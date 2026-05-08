import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import hashlib
import json
import tempfile
import pandas as pd

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="ASL-FFE - Profil Combattant", layout="wide", initial_sidebar_state="collapsed")

# 2. DESIGN CSS (Variables HSL pour le look sombre/sport)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');
    
    .stApp {
        background-color: hsl(180, 25%, 15%);
        font-family: 'Space Grotesk', sans-serif;
        color: white;
    }

    header {visibility: hidden;}
    footer {visibility: hidden;}

    .login-title {
        color: hsl(210, 20%, 95%);
        font-size: 1.8rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 30px;
    }

    /* Style des champs de saisie */
    .stTextInput input {
        background-color: hsl(180, 25%, 25%) !important;
        border: 1px solid hsl(180, 25%, 35%) !important;
        color: white !important;
        border-radius: 0.5rem !important;
    }

    /* Style du bouton */
    .stButton > button {
        background-color: hsl(182, 100%, 74%) !important;
        color: hsl(180, 25%, 10%) !important;
        font-weight: 700 !important;
        width: 100% !important;
        height: 3rem !important;
        border: none !important;
        border-radius: 0.5rem !important;
    }

    /* Conteneur de la carte de connexion */
    [data-testid="stVerticalBlock"] > div:has(div.card-container) {
        background-color: hsl(180, 25%, 20%);
        border: 1px solid hsl(180, 25%, 30%);
        border-radius: 0.75rem;
        padding: 40px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }
    </style>
    """, unsafe_allow_html=True)

# 3. INITIALISATION FIREBASE
if 'db' not in st.session_state:
    try:
        firebase_config = dict(st.secrets["firebase"])
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(firebase_config, f)
            temp_file = f.name
        
        try:
            firebase_admin.get_app()
        except ValueError:
            cred = credentials.Certificate(temp_file)
            firebase_admin.initialize_app(cred)
        
        st.session_state.db = firestore.client()
    except Exception as e:
        st.error(f"❌ Erreur de connexion Firebase : {e}")
        st.stop()

db = st.session_state.db

# Initialisation de l'état de connexion
if 'auth_success' not in st.session_state:
    st.session_state.auth_success = False

# 4. LOGIQUE DE CONNEXION
if not st.session_state.auth_success:
    _, col_center, _ = st.columns([1, 2, 1])

    with col_center:
        st.markdown('<div class="card-container"></div>', unsafe_allow_html=True)
        # Remplace l'URL du logo si nécessaire
        st.image("https://studio-7691886667-ec4b3.web.app/logo.png", width=150)
        st.markdown('<h1 class="login-title">ESPACE ATHLÈTE</h1>', unsafe_allow_html=True)
        
        prenom_input = st.text_input("Prénom (ex: Guillaume)").strip().lower()
        code_input = st.text_input("Code d'accès", type="password").strip()

        if st.button("SE CONNECTER"):
            if prenom_input and code_input:
                # On cherche le document dont l'ID est le prénom (ex: 'guillaume')
                doc_ref = db.collection("athletes").document(prenom_input).get()
                
                if doc_ref.exists:
                    data = doc_ref.to_dict()
                    stored_hash = data.get("access_code_hash")
                    # On hache le code tapé pour comparer
                    provided_hash = hashlib.sha256(code_input.encode('utf-8')).hexdigest()
                    
                    if provided_hash == stored_hash:
                        st.session_state.auth_success = True
                        st.session_state.athlete_data = data
                        st.rerun()
                    else:
                        st.error("❌ Code d'accès incorrect.")
                        # Aide au debug : affiche les 5 premiers caractères du hash calculé
                        st.info(f"DEBUG: Hash calculé commence par {provided_hash[:5]}")
                else:
                    st.error(f"❌ L'athlète '{prenom_input}' n'existe pas.")
            else:
                st.warning("⚠️ Veuillez remplir tous les champs.")

# 5. AFFICHAGE DU PROFIL (UNE FOIS CONNECTÉ)
else:
    athlete = st.session_state.athlete_data
    
    # Header du profil
    st.title(f"Tableau de bord : {athlete.get('name', 'Athlète')}")
    st.markdown(f"**Club :** {athlete.get('club')} | **Catégorie :** {athlete.get('category')}")
    st.divider()

    # Déballage des statistiques JSON
    try:
        # On lit le gros bloc de texte JSON stocké dans Firebase
        stats = json.loads(athlete.get("json_data", "{}"))
        
        # Affichage des compteurs principaux
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Victoires", stats.get("victories", 0))
        c2.metric("Défaites", stats.get("defeats", 0))
        c3.metric("Touches Marquées", stats.get("total_touches_scored", 0))
        c4.metric("% Tête", f"{stats.get('head_zone_touches_percentage', 0)}%")

        st.divider()

        # Affichage détaillé des actions
        st.subheader("🤺 Analyse des actions")
        actions = stats.get("actions_breakdown", {})
        if actions:
            df_actions = pd.DataFrame(list(actions.items()), columns=["Action", "Total"])
            st.table(df_actions)
        else:
            st.info("Aucune donnée d'action détaillée.")

    except Exception as e:
        st.error(f"Erreur lors de la lecture des statistiques : {e}")

    # Bouton de déconnexion
    if st.button("Se déconnecter"):
        st.session_state.auth_success = False
        st.rerun()
