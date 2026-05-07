import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import hashlib
import json
import tempfile
import pandas as pd

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="ASL-FFE - Profil Combattant", layout="wide", initial_sidebar_state="collapsed")

# 2. DESIGN CSS (Variables HSL)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');
    .stApp { background-color: hsl(180, 25%, 15%); font-family: 'Space Grotesk', sans-serif; }
    header, footer { visibility: hidden; }
    .login-title { color: hsl(210, 20%, 95%); font-size: 1.8rem; font-weight: 700; text-align: center; margin-bottom: 30px; }
    .stTextInput input { background-color: hsl(180, 25%, 25%) !important; border: 1px solid hsl(180, 25%, 25%) !important; color: white !important; border-radius: 0.5rem !important; }
    .stButton > button { background-color: hsl(182, 100%, 74%) !important; color: hsl(180, 25%, 10%) !important; font-weight: 700 !important; width: 100% !important; height: 3.5rem !important; border-radius: 0.5rem !important; }
    [data-testid="stVerticalBlock"] > div:has(div.card-container) { background-color: hsl(180, 25%, 20%); border: 1px solid hsl(180, 25%, 25%); border-radius: 0.75rem; padding: 40px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5); }
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
        st.error(f"❌ Erreur Firebase: {e}")
        st.stop()

db = st.session_state.db

# 4. FONCTION DE SÉCURITÉ (HASH)
def verify_hash(provided_code, stored_hash):
    return hashlib.sha256(provided_code.encode('utf-8')).hexdigest() == stored_hash

if 'auth_success' not in st.session_state:
    st.session_state.auth_success = False

# --- LOGIQUE DE CONNEXION ---
if not st.session_state.auth_success:
    _, col_center, _ = st.columns([1, 2.5, 1])

    with col_center:
        st.markdown('<div class="card-container"></div>', unsafe_allow_html=True)
        st.image("https://studio-7691886667-ec4b3.web.app/logo.png", width=200)
        st.markdown('<h1 class="login-title">PROFIL COMBATTANT</h1>', unsafe_allow_html=True)
        
        prenom_input = st.text_input("Prénom (ex: Guillaume)")
        code_input = st.text_input("Code d'accès", type="password")

        if st.button("ACCÉDER AU PROFIL"):
            if prenom_input and code_input:
                # On cherche le document qui porte le nom de l'athlète en minuscule
                doc_ref = db.collection("athletes").document(prenom_input.lower()).get()
                
                if doc_ref.exists:
                    data = doc_ref.to_dict()
                    # Vérification du Hash sécurisé
                    if verify_hash(code_input, data.get("access_code_hash")):
                        st.session_state.auth_success = True
                        st.session_state.athlete_data = data
                        st.rerun()
                    else:
                        st.error("❌ Code d'accès invalide.")
                else:
                    st.error("❌ Athlète non trouvé.")
            else:
                st.warning("⚠️ Remplissez tous les champs.")

# --- PAGE PROFIL ---
else:
    athlete = st.session_state.athlete_data
    # On déballe le JSON contenu dans json_data
    stats_match = json.loads(athlete.get("json_data", "{}"))

    st.title(f"Bienvenue, {athlete.get('name')} 👋")
    st.markdown(f"**Club :** {athlete.get('club')} | **Catégorie :** {athlete.get('category')}")
    st.divider()
    
    # Métriques issues de ton nouveau JSON
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Victoires", stats_match.get("victories", 0))
    c2.metric("Défaites", stats_match.get("defeats", 0))
    c3.metric("Touches +", stats_match.get("total_touches_scored", 0))
    c4.metric("Cible Tête", f"{stats_match.get('head_zone_touches_percentage', 0)}%")
    
    st.divider()
    
    # Tableau des actions
    st.subheader("🤺 Détail des actions")
    actions = stats_match.get("actions_breakdown", {})
    df_actions = pd.DataFrame(list(actions.items()), columns=["Type", "Nombre"])
    st.table(df_actions)
    
    if st.button("Déconnexion"):
        st.session_state.auth_success = False
        st.rerun()
