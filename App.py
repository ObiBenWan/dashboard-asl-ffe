import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import hashlib
import json
import tempfile
import pandas as pd

# 1. CONFIGURATION
st.set_page_config(page_title="ASL-FFE - Profil Combattant", layout="wide")

# 2. DESIGN CSS
st.markdown("""
    <style>
    .stApp { background-color: hsl(180, 25%, 15%); color: white; }
    .stTextInput input { background-color: hsl(180, 25%, 25%) !important; color: white !important; }
    .stButton > button { background-color: hsl(182, 100%, 74%) !important; color: black !important; font-weight: bold; }
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
        st.error(f"Erreur Firebase: {e}")
        st.stop()

db = st.session_state.db

# 4. LOGIQUE DE CONNEXION
if 'auth_success' not in st.session_state:
    st.session_state.auth_success = False

if not st.session_state.auth_success:
    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        st.title("Connexion")
        prenom = st.text_input("Prénom (ex: Guillaume)").strip()
        code_clair = st.text_input("Code d'accès", type="password").strip()

        if st.button("ACCÉDER AU PROFIL"):
            if prenom and code_clair:
                # On force en minuscule pour correspondre à l'ID document
                doc_id = prenom.lower()
                doc_ref = db.collection("athletes").document(doc_id).get()
                
                if doc_ref.exists:
                    data = doc_ref.to_dict()
                    # On récupère le hash stocké et on enlève les espaces cachés
                    stored_hash = str(data.get("access_code_hash", "")).strip()
                    # On génère le hash du code tapé
                    provided_hash = hashlib.sha256(code_clair.encode('utf-8')).hexdigest()
                    
                    if provided_hash == stored_hash:
                        st.session_state.auth_success = True
                        st.session_state.athlete_data = data
                        st.rerun()
                    else:
                        st.error("❌ Code incorrect.")
                        # Aide au diagnostic (à supprimer plus tard pour la sécurité)
                        st.info(f"DEBUG: Ton hash est {provided_hash[:10]}...")
                else:
                    st.error(f"❌ L'athlète '{doc_id}' est introuvable.")
            else:
                st.warning("Veuillez remplir les deux cases.")

# 5. AFFICHAGE DU PROFIL
else:
    d = st.session_state.athlete_data
    st.header(f"Profil de {d.get('name', 'Athlète')}")
    st.subheader(f"{d.get('club', 'Club')} - {d.get('category', 'Catégorie')}")
    
    # On déballe les données JSON
    try:
        stats = json.loads(d.get("json_data", "{}"))
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Victoires", stats.get("victories", 0))
        c2.metric("Défaites", stats.get("defeats", 0))
        c3.metric("Touches", stats.get("total_touches_scored", 0))
        
        # Tableau des actions
        st.write("### Actions")
        actions = stats.get("actions_breakdown", {})
        if actions:
            df = pd.DataFrame(list(actions.items()), columns=["Action", "Total"])
            st.table(df)
            
    except Exception as e:
        st.error(f"Erreur de lecture du JSON : {e}")

    if st.button("Déconnexion"):
        st.session_state.auth_success = False
        st.rerun()
