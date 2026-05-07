#!/usr/bin/env python3
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import hashlib

st.set_page_config(page_title="ASL-FFE", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background-color: hsl(180, 25%, 15%); font-family: 'Space Grotesk', sans-serif; }
    header { visibility: hidden; }
    .stButton > button { background-color: hsl(182, 100%, 74%) !important; color: hsl(180, 25%, 10%) !important; }
    </style>
    """, unsafe_allow_html=True)

# === FIREBASE INIT ===
@st.cache_resource
def init_firebase():
    if not firebase_admin.get_app():
        try:
            # Récupérer JSON depuis secrets et l'écrire dans un fichier temporaire
            import json
            import tempfile
            
            firebase_config = dict(st.secrets["firebase"])
            
            # Créer un fichier temporaire avec le JSON
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(firebase_config, f)
                temp_file = f.name
            
            # Initialiser Firebase avec le chemin du fichier
            cred = credentials.Certificate(temp_file)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"❌ Erreur Firebase: {e}")
            st.stop()
    
    return firestore.client()

db = init_firebase()

# === SESSION STATE ===
if 'auth_success' not in st.session_state:
    st.session_state.auth_success = False

# === FONCTIONS ===
def hash_code(code: str) -> str:
    return hashlib.sha256(code.encode('utf-8')).hexdigest()

@st.cache_data(ttl=300)
def get_all_athletes() -> list:
    try:
        docs = db.collection("athletes").stream()
        return [doc.id for doc in docs]
    except:
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

@st.cache_data(ttl=300)
def load_athlete_data(athlete_id: str) -> dict:
    try:
        doc = db.collection("athletes").document(athlete_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except:
        return None

# === LOGIN ===
if not st.session_state.auth_success:
    col_left, col_center, col_right = st.columns([1, 2.5, 1])
    with col_center:
        st.title("⚔️ ASL Vision Engine")
        
        athletes = get_all_athletes()
        if not athletes:
            st.error("❌ Aucun combattant")
            st.stop()
        
        selected = st.selectbox("Profil:", athletes, format_func=lambda x: x.replace("_", " ").title())
        code = st.text_input("Code:", type="password", placeholder="Ex: T3G2VT-0")
        
        if st.button("Accéder", use_container_width=True):
            if code and verify_access_code(selected, code):
                st.session_state.auth_success = True
                st.session_state.athlete_id = selected
                st.session_state.athlete_data = load_athlete_data(selected)
                st.success("✅ OK!")
                st.rerun()
            else:
                st.error("❌ Invalide")

# === PROFILE ===
else:
    data = st.session_state.athlete_data
    if not data:
        st.error("❌ Erreur")
        if st.button("Retour"):
            st.session_state.auth_success = False
            st.rerun()
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.title(f"⚔️ {data.get('name', 'Combattant')}")
        with col2:
            if st.button("Déconnexion"):
                st.session_state.auth_success = False
                st.rerun()
        
        stats = data.get("stats", {})
        victories = stats.get("victories", 0)
        defeats = stats.get("defeats", 0)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Win Rate", f"{(victories/(victories+defeats+1)*100):.1f}%")
        col2.metric("Touches", stats.get("total_touches_scored", 0))
        col3.metric("Reçues", stats.get("total_touches_received", 0))
        col4.metric("Tête %", f"{stats.get('head_zone_touches_percentage', 0):.1f}%")
