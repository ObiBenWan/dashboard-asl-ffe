#!/usr/bin/env python3
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import hashlib
import json
import tempfile
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
 
# 1. CONFIGURATION PAGE
st.set_page_config(page_title="ASL-FFE Dashboard", layout="wide", initial_sidebar_state="collapsed")
 
# 2. LUCIDE ICONS SVG (Design clean)
ICONS_SVG = {
    'trophy': '''<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2h-2m-4-3V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v1m8 13l-4-4m4 4l4-4"></path></svg>''',
    'target': '''<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"></circle><circle cx="12" cy="12" r="5"></circle><circle cx="12" cy="12" r="9"></circle></svg>''',
    'shield': '''<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>''',
    'zap': '''<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>''',
    'trending-up': '''<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 17"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>''',
    'activity': '''<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>''',
    'bar-chart': '''<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="20" x2="12" y2="10"></line><line x1="18" y1="20" x2="18" y2="4"></line><line x1="6" y1="20" x2="6" y2="16"></line></svg>''',
    'pie-chart': '''<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><line x1="22" y1="12" x2="12" y2="12"></line></svg>''',
    'log-out': '''<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>''',
}
 
# 3. DESIGN - COULEURS ORIGINALES
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');
    
    * { margin:0; padding:0; box-sizing: border-box; }
    
    html, body, [data-testid="stAppViewContainer"] { 
        background-color: hsl(180, 25%, 15%) !important;
        color: hsl(210, 20%, 95%) !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    
    [data-testid="stHeader"] { background-color: transparent !important; }
    [data-testid="stToolbar"] { display: none !important; }
    
    h1, h2, h3, h4 { color: hsl(210, 20%, 95%) !important; }
    
    .stTabs [role="tablist"] { 
        border-bottom: 2px solid hsl(180, 25%, 25%);
    }
    
    .stTabs [role="tab"][aria-selected="true"] {
        color: hsl(182, 100%, 74%) !important;
        border-bottom: 3px solid hsl(182, 100%, 74%) !important;
    }
    
    .stMetric { 
        background-color: hsl(180, 25%, 20%) !important;
        border: 1px solid hsl(180, 25%, 25%) !important;
        border-radius: 8px !important;
        padding: 15px !important;
    }
    
    .stButton>button {
        background-color: hsl(182, 100%, 74%) !important;
        color: hsl(180, 25%, 10%) !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        padding: 12px 24px !important;
        width: 100% !important;
        font-size: 0.95rem !important;
    }
    
    .stButton>button:hover {
        background-color: hsl(182, 100%, 60%) !important;
    }
    
    .stDivider { border-top: 1px solid hsl(180, 25%, 25%) !important; }
    
    .stTextInput input {
        background-color: hsl(180, 25%, 20%) !important;
        border: 1px solid hsl(180, 25%, 25%) !important;
        color: hsl(210, 20%, 95%) !important;
        border-radius: 6px !important;
        padding: 10px 12px !important;
    }
    
    .stTextInput input::placeholder {
        color: hsl(180, 10%, 50%) !important;
    }
    
    svg { color: hsl(182, 100%, 74%); }
    
    </style>
    """, unsafe_allow_html=True)
 
# 4. INITIALISATION FIREBASE
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
 
if 'auth_success' not in st.session_state:
    st.session_state.auth_success = False
 
# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONNEXION
# ═══════════════════════════════════════════════════════════════════════════════
 
if not st.session_state.auth_success:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style="
                background-color: hsl(180, 25%, 20%);
                border: 1px solid hsl(180, 25%, 25%);
                border-radius: 12px;
                padding: 50px 40px;
            ">
        """, unsafe_allow_html=True)
        
        # Layout: Logo à droite, Texte à gauche
        col_left, col_right = st.columns([1.2, 1])
        
        with col_left:
            st.markdown("""
                <div style="padding-right: 20px;">
                    <h1 style="
                        color: hsl(210, 20%, 95%);
                        font-size: 2rem;
                        font-weight: 700;
                        margin: 0 0 8px 0;
                        letter-spacing: 0.05em;
                    ">ASL-FFE</h1>
                    <p style="
                        color: hsl(180, 10%, 60%);
                        font-size: 0.95rem;
                        margin: 0 0 30px 0;
                        letter-spacing: 0.04em;
                    ">PROFIL COMBATTANT</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col_right:
            st.image("https://studio-7691886667-ec4b3.web.app/logo.png", width=180)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Formulaire
        st.markdown("<br>", unsafe_allow_html=True)
        
        prenom = st.text_input(
            "label",
            placeholder="Nom de combattant",
            key="login_prenom",
            label_visibility="collapsed"
        )
        
        code = st.text_input(
            "label2",
            type="password",
            placeholder="Code d'accès",
            key="login_code",
            label_visibility="collapsed"
        )
        
        if st.button("ACCÉDER AU PROFIL", key="login_btn"):
            if prenom and code:
                athlete_id = prenom.lower()
                try:
                    doc = db.collection("athletes").document(athlete_id).get()
                    if doc.exists:
                        data = doc.to_dict()
                        if hashlib.sha256(code.encode()).hexdigest() == data.get("access_code_hash"):
                            st.session_state.auth_success = True
                            st.session_state.athlete_data = data
                            st.session_state.athlete_name = prenom
                            st.rerun()
                        else:
                            st.error("❌ Code d'accès invalide")
                    else:
                        st.error("❌ Combattant non trouvé")
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
            else:
                st.warning("⚠️ Veuillez remplir tous les champs")
 
# ═══════════════════════════════════════════════════════════════════════════════
# PAGE PROFIL
# ═══════════════════════════════════════════════════════════════════════════════
 
else:
    import os
    _profil_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profil.py")
    with open(_profil_path, encoding="utf-8") as _f:
        exec(compile(_f.read(), _profil_path, "exec"), globals())