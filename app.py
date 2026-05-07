#!/usr/bin/env python3
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import hashlib
import json
import tempfile
 
st.set_page_config(page_title="ASL-FFE", layout="wide", initial_sidebar_state="collapsed")
 
st.markdown("""
    <style>
    .stApp { background-color: hsl(180, 25%, 15%); font-family: 'Space Grotesk', sans-serif; }
    header { visibility: hidden; }
    .stButton > button { background-color: hsl(182, 100%, 74%) !important; color: hsl(180, 25%, 10%) !important; }
    </style>
    """, unsafe_allow_html=True)
 
# === FIREBASE INIT (UNE SEULE FOIS) ===
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
 
def get_all_athletes() -> list:
    try:
        docs = db.collection("athletes").stream()
        return [doc.id for doc in docs]
    except Exception as e:
        st.error(f"Erreur: {e}")
        return []
 
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
 
# === LOGIN PAGE ===
if not st.session_state.auth_success:
    col_left, col_center, col_right = st.columns([1, 2.5, 1])
    with col_center:
        st.title("⚔️ ASL Vision Engine")
        st.markdown("**PROFIL COMBATTANT**")
        
        athletes = get_all_athletes()
        if not athletes:
            st.error("❌ Aucun combattant disponible")
            st.stop()
        
        selected = st.selectbox(
            "Sélectionnez votre profil:",
            athletes,
            format_func=lambda x: x.replace("_", " ").title()
        )
        code = st.text_input("Code d'accès:", type="password", placeholder="Ex: T3G2VT-0")
        
        if st.button("Accéder au profil", use_container_width=True):
            if code and verify_access_code(selected, code):
                st.session_state.auth_success = True
                st.session_state.athlete_id = selected
                st.session_state.athlete_data = load_athlete_data(selected)
                st.success("✅ Connexion réussie!")
                st.rerun()
            elif code:
                st.error("❌ Code d'accès invalide")
            else:
                st.warning("⚠️ Veuillez entrer votre code")
 
# === PROFILE PAGE ===
else:
    data = st.session_state.athlete_data
    
    if not data:
        st.error("❌ Impossible de charger le profil")
        if st.button("Retour"):
            st.session_state.auth_success = False
            st.rerun()
    else:
        # Header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.title(f"⚔️ {data.get('name', 'Combattant')}")
            st.markdown(f"**Club:** {data.get('club', 'N/A')} | **Catégorie:** {data.get('category', 'N/A')}")
        with col2:
            if st.button("🔒 Déconnexion"):
                st.session_state.auth_success = False
                st.rerun()
        
        st.divider()
        
        # Stats
        stats = data.get("stats", {})
        victories = stats.get("victories", 0)
        defeats = stats.get("defeats", 0)
        total = victories + defeats
        winrate = (victories / total * 100) if total > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🏆 Win Rate", f"{winrate:.1f}%", f"{victories}W-{defeats}L")
        col2.metric("🎯 Touches Marquées", stats.get("total_touches_scored", 0))
        col3.metric("🛡️ Touches Reçues", stats.get("total_touches_received", 0))
        col4.metric("💡 Cible Tête %", f"{stats.get('head_zone_touches_percentage', 0):.1f}%")
        
        st.divider()
        
        # Actions
        actions = data.get("actions_breakdown", {})
        if actions:
            st.subheader("⚡ Répartition des Actions")
            import pandas as pd
            df = pd.DataFrame(list(actions.items()), columns=["Action", "Nombre"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Debug
        with st.expander("🔍 Données brutes"):
            st.json(data)
