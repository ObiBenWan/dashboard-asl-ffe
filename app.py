#!/usr/bin/env python3
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import hashlib
import json
import tempfile
 
# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="ASL-FFE - Profil Combattant", layout="wide", initial_sidebar_state="collapsed")
 
# 2. INJECTION DU DESIGN
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');
    
    /* Configuration des couleurs et du fond */
    .stApp {
        background-color: hsl(180, 25%, 15%);
        font-family: 'Space Grotesk', sans-serif;
    }

    /* Masquer le header Streamlit */
    header {visibility: hidden;}
    
    /* Masquer le footer */
    footer {visibility: hidden;}

    /* Titres */
    .login-title {
        color: hsl(210, 20%, 95%);
        font-size: 1.8rem;
        font-weight: 700;
        text-align: center;
        margin-top: 10px;
        margin-bottom: 30px;
        letter-spacing: -0.025em;
    }

    .profile-title {
        color: hsl(210, 20%, 95%);
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 20px;
    }

    /* Inputs */
    .stTextInput label {
        color: hsl(180, 10%, 60%) !important;
    }
    .stTextInput input {
        background-color: hsl(180, 25%, 25%) !important;
        border: 1px solid hsl(180, 25%, 25%) !important;
        color: white !important;
    }

    /* Bouton */
    .stButton > button {
        background-color: hsl(182, 100%, 74%) !important;
        color: hsl(180, 25%, 10%) !important;
        font-weight: 700 !important;
        width: 100% !important;
        height: 3.5rem !important;
        border: none !important;
        margin-top: 20px;
    }
    
    /* Conteneur centré */
    .centered-container {
        background-color: hsl(180, 25%, 20%);
        border: 1px solid hsl(180, 25%, 25%);
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
        
        # Créer fichier temporaire
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(firebase_config, f)
            temp_file = f.name
        
        # Initialiser Firebase
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
 
# === SESSION STATE ===
if 'auth_success' not in st.session_state:
    st.session_state.auth_success = False
 
# === FONCTIONS ===
def hash_code(code: str) -> str:
    return hashlib.sha256(code.encode('utf-8')).hexdigest()
 
def verify_access_code(athlete_id: str, provided_code: str) -> bool:
    try:
        doc = db.collection("athletes").document(athlete_id).get()
        if not doc.exists:
            return False
        stored_hash = doc.get("access_code_hash")
        provided_hash = hash_code(provided_code)
        return stored_hash == provided_hash
    except:
        return False
 
def load_athlete_data(athlete_id: str) -> dict:
    try:
        doc = db.collection("athletes").document(athlete_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except:
        return None
 
# --- LOGIQUE DE CONNEXION ---
 
if not st.session_state.auth_success:
    col_left, col_center, col_right = st.columns([1, 2.5, 1])

    with col_center:
        st.markdown('<div class="card-container"></div>', unsafe_allow_html=True)
        
        st.image("https://studio-7691886667-ec4b3.web.app/logo.png", width=500)
        
        st.markdown('<h1 class="login-title">PROFIL COMBATTANT</h1>', unsafe_allow_html=True)
        
        prenom = st.text_input("Prénom")
        code_acces = st.text_input("Code d'accès", type="password")

        if st.button("ACCÉDER AU PROFIL"):
            if prenom and code_acces:
                try:
                    docs = db.collection("athletes").stream()
                    athlete_found = None
                    athlete_id = None
                    
                    for doc in docs:
                        data = doc.to_dict()
                        athlete_name = data.get("name", "").lower()
                        if prenom.lower() in athlete_name:
                            athlete_found = data
                            athlete_id = doc.id
                            break
                    
                    if athlete_found and verify_access_code(athlete_id, code_acces):
                        st.session_state.auth_success = True
                        st.session_state.prenom_utilisateur = prenom
                        st.session_state.code_valide = code_acces
                        st.session_state.athlete_id = athlete_id
                        st.session_state.athlete_data = athlete_found
                        st.success("✅ Connexion réussie!")
                        st.rerun()
                    else:
                        st.error("❌ Identifiants incorrects.")
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
            else:
                st.warning("⚠️ Veuillez remplir tous les champs.")
        
        st.markdown('</div>', unsafe_allow_html=True)
 
# --- PAGE PROFIL (DÉVERROUILLÉE) ---
else:
    data = st.session_state.athlete_data
    
    if data:
        st.title(f"Bienvenue, {st.session_state.prenom_utilisateur}")
        st.divider()
        
        # === STATS PRINCIPALES ===
        stats = data.get("stats", {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        victories = stats.get("victories", 0)
        defeats = stats.get("defeats", 0)
        total_fights = victories + defeats
        winrate = (victories / total_fights * 100) if total_fights > 0 else 0
        
        col1.metric("🏆 Win Rate", f"{winrate:.1f}%", f"{victories}W-{defeats}L")
        col2.metric("🎯 Touches Marquées", stats.get("total_touches_scored", 0))
        col3.metric("🛡️ Touches Reçues", stats.get("total_touches_received", 0))
        col4.metric("💡 Cible Tête %", f"{stats.get('head_zone_touches_percentage', 0):.1f}%")
        
        st.divider()
        
        # === ONGLETS DÉTAILS ===
        tab1, tab2, tab3 = st.tabs(["📊 Stats Détaillées", "⚡ Actions", "📈 Tendance"])
        
        # TAB 1: Stats détaillées
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Résumé Combat")
                summary_data = {
                    "Victoires": victories,
                    "Défaites": defeats,
                    "Touches Marquées": stats.get("total_touches_scored", 0),
                    "Touches Reçues": stats.get("total_touches_received", 0),
                }
                for key, value in summary_data.items():
                    st.write(f"**{key}:** {value}")
        
        # TAB 2: Actions breakdown
        with tab2:
            actions = data.get("actions_breakdown", {})
            
            if actions:
                st.subheader("Répartition des Actions")
                import pandas as pd
                df_actions = pd.DataFrame(list(actions.items()), columns=["Action", "Nombre"])
                st.dataframe(df_actions, use_container_width=True, hide_index=True)
            else:
                st.info("Aucune donnée d'action disponible")
        
        # TAB 3: Tendance performance
        with tab3:
            trend = data.get("performance_trend", [])
            
            if trend:
                st.subheader("Performance au fil du temps")
                import pandas as pd
                df_trend = pd.DataFrame(trend)
                st.dataframe(df_trend, use_container_width=True, hide_index=True)
            else:
                st.info("Aucune tendance disponible")
        
        st.divider()
        
        if st.button("Déconnexion"):
            st.session_state.auth_success = False
            st.rerun()
    else:
        st.error("❌ Impossible de charger le profil")
        if st.button("Retour"):
            st.session_state.auth_success = False
            st.rerun()
