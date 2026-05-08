#!/usr/bin/env python3
"""
app.py - Streamlit Dashboard
Affiche les profils et stats des combattants ASL Vision Engine.
Authentification via code d'accès Firebase.
"""
 
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from typing import Dict, Optional
import hashlib
import json
import tempfile

# === PAGE CONFIG ===
st.set_page_config(
    page_title="ASL Vision Engine - Profils",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)
 
# === STYLES ===
st.markdown("""
<style>
    :root {
        --primary: #1f77b4;
        --success: #2ca02c;
        --danger: #d62728;
        --accent: #ff7f0e;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .metric-value {
        font-size: 2.5em;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .metric-label {
        font-size: 0.9em;
        opacity: 0.9;
    }
    
    .header-accent {
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)
 
# === FIREBASE INIT ===

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
 
# === FONCTIONS UTILITAIRES ===
def hash_code(code: str) -> str:
    """Hash un code d'accès."""
    return hashlib.sha256(code.encode()).hexdigest()
 
@st.cache_data(ttl=300)
def load_athlete_data(athlete_id: str) -> Optional[Dict]:
    """Charge les données d'un combattant depuis Firebase."""
    try:
        doc = db.collection("athletes").document(athlete_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        st.error(f"Erreur Firebase: {e}")
        return None
 
@st.cache_data(ttl=60)
def load_all_athletes() -> list:
    """Charge la liste de tous les combattants."""
    try:
        docs = db.collection("athletes").stream()
        return [doc.id for doc in docs]
    except Exception as e:
        st.error(f"Erreur chargement combattants: {e}")
        return []
 
def verify_access(athlete_id: str, provided_code: str) -> bool:
    """Vérifie l'accès avec le code fourni."""
    try:
        doc = db.collection("athletes").document(athlete_id).get()
        if not doc.exists:
            return False
        
        stored_hash = doc.get("access_code_hash")
        provided_hash = hash_code(provided_code)
        
        return stored_hash == provided_hash
    except:
        return False
 
def render_metric_card(label: str, value: str, color: str = "#667eea"):
    """Affiche une carte métrique stylisée."""
    st.markdown(f"""
    <div class="metric-card" style="background: linear-gradient(135deg, {color} 0%, {color}dd 100%);">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)
 
# === SESSION STATE ===
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_athlete" not in st.session_state:
    st.session_state.current_athlete = None
 
# === PAGE: AUTHENTIFICATION ===
def page_login():
    st.markdown("# ⚔️ ASL Vision Engine - Profils Combattants")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Bienvenue !
        
        Connectez-vous avec votre code d'accès personnel pour voir vos stats d'analyse.
        """)
        
        # Sélection combattant
        athletes = load_all_athletes()
        if not athletes:
            st.warning("⚠️ Aucun combattant disponible")
            return
        
        selected_athlete = st.selectbox(
            "Sélectionnez votre profil:",
            athletes,
            format_func=lambda x: x.replace("_", " ").title()
        )
        
        # Code d'accès
        access_code = st.text_input(
            "Code d'accès:",
            type="password",
            help="Entrez votre code d'accès personnel (fourni par l'administrateur)"
        )
        
        # Bouton connexion
        if st.button("🔓 Se connecter", use_container_width=True):
            if verify_access(selected_athlete, access_code):
                st.session_state.authenticated = True
                st.session_state.current_athlete = selected_athlete
                st.success("✅ Connexion réussie!")
                st.rerun()
            else:
                st.error("❌ Code d'accès invalide")
    
    with col2:
        st.info("""
        **ℹ️ Besoin d'aide ?**
        
        Contactez votre administrateur si vous n'avez pas reçu votre code d'accès.
        """)
 
# === PAGE: DASHBOARD PROFIL ===
def page_dashboard():
    athlete_id = st.session_state.current_athlete
    athlete_data = load_athlete_data(athlete_id)
    
    if not athlete_data:
        st.error("❌ Impossible de charger le profil")
        return
    
    # Header
    st.markdown(f"# ⚔️ Profil: {athlete_data.get('name', 'N/A')}")
    st.markdown(f"**Club:** {athlete_data.get('club', 'N/A')} | **Catégorie:** {athlete_data.get('category', 'N/A')}")
    st.markdown("---")
    
    # KPIs principaux
    stats = athlete_data.get("stats", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        victories = stats.get("victories", 0)
        defeats = stats.get("defeats", 0)
        total = victories + defeats
        winrate = (victories / total * 100) if total > 0 else 0
        st.metric("Win Rate", f"{winrate:.1f}%", f"{victories}W-{defeats}L")
    
    with col2:
        touches_scored = stats.get("total_touches_scored", 0)
        st.metric("Touches Marquées", touches_scored)
    
    with col3:
        touches_received = stats.get("total_touches_received", 0)
        st.metric("Touches Reçues", touches_received)
    
    with col4:
        head_zone_pct = stats.get("head_zone_touches_percentage", 0)
        st.metric("Cible Tête %", f"{head_zone_pct:.1f}%")
    
    st.markdown("---")
    
    # Graphiques
    col_graph1, col_graph2 = st.columns(2)
    
    # Graph 1: Répartition actions
    with col_graph1:
        st.subheader("📊 Répartition des Actions")
        actions = athlete_data.get("actions_breakdown", {})
        
        if actions:
            df_actions = pd.DataFrame(list(actions.items()), columns=["Action", "Nombre"])
            fig = px.pie(
                df_actions,
                names="Action",
                values="Nombre",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée d'action disponible")
    
    # Graph 2: Tendance performance
    with col_graph2:
        st.subheader("📈 Tendance de Performance")
        trend = athlete_data.get("performance_trend", [])
        
        if trend:
            df_trend = pd.DataFrame(trend)
            # Supposer que trend contient des champs date et score
            fig = px.line(
                df_trend,
                x="date" if "date" in df_trend.columns else df_trend.index,
                y="score" if "score" in df_trend.columns else df_trend.columns[0],
                markers=True,
                title="Score au fil du temps"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune données de tendance disponible")
    
    st.markdown("---")
    
    # Infos métadonnées
    with st.expander("ℹ️ Infos Techniques"):
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.write(f"**ID Combattant:** `{athlete_id}`")
            st.write(f"**Version Données:** {athlete_data.get('version', 'N/A')}")
        with col_info2:
            st.write(f"**Créé:** {athlete_data.get('created_at', 'N/A')}")
            st.write(f"**Mis à jour:** {athlete_data.get('updated_at', 'N/A')}")
    
    # Bouton déconnexion
    if st.button("🔒 Se déconnecter", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.current_athlete = None
        st.rerun()
 
# === ROUTER ===
def main():
    if not st.session_state.authenticated:
        page_login()
    else:
        page_dashboard()
 
if __name__ == "__main__":
    main()
