#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py - Streamlit Dashboard ASL Vision Engine
Affiche les profils combattants avec stats + graphiques
Compatible avec sync_athletes_v2_interactive.py
"""
 
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import hashlib
import logging
 
# === CONFIGURATION ===
logger = logging.getLogger(__name__)
 
st.set_page_config(
    page_title="ASL-FFE - Profil Combattant",
    layout="wide",
    initial_sidebar_state="collapsed"
)
 
# === DESIGN (Variables HSL + améliorations) ===
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
 
    /* Style du conteneur "Card" */
    [data-testid="stVerticalBlock"] > div:has(div.card-container) {
        background-color: hsl(180, 25%, 20%);
        border: 1px solid hsl(180, 25%, 25%);
        border-radius: 0.75rem;
        padding: 40px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }
 
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
    .stTextInput div div input {
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
 
    /* Metrics */
    .metric-card {
        background-color: hsl(180, 25%, 22%);
        padding: 20px;
        border-radius: 0.5rem;
        border-left: 4px solid hsl(182, 100%, 74%);
    }
 
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
 
    .stTabs [data-baseweb="tab"] {
        color: hsl(180, 10%, 60%);
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)
 
# === INITIALISATION FIREBASE ===
@st.cache_resource
def init_firebase():
    """Initialise Firebase une seule fois."""
    if not firebase_admin._apps:
        try:
            fb_credentials = dict(st.secrets["firebase"])
            fb_credentials["private_key"] = fb_credentials["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(fb_credentials)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"❌ Erreur Firebase: {e}")
            st.stop()
    
    return firestore.client()
 
db = init_firebase()
 
# === SESSION STATE ===
if 'auth_success' not in st.session_state:
    st.session_state.auth_success = False
if 'athlete_data' not in st.session_state:
    st.session_state.athlete_data = None
 
# === FONCTIONS UTILITAIRES ===
 
def hash_code(code: str) -> str:
    """Hash un code d'accès."""
    return hashlib.sha256(code.encode('utf-8')).hexdigest()
 
@st.cache_data(ttl=300)
def get_all_athletes() -> list:
    """Récupère la liste de tous les combattants."""
    try:
        docs = db.collection("athletes").stream()
        return [doc.id for doc in docs]
    except Exception as e:
        logger.error(f"Erreur chargement: {e}")
        return []
 
def verify_access_code(athlete_id: str, provided_code: str) -> bool:
    """Vérifie le code d'accès contre le hash stocké."""
    try:
        doc = db.collection("athletes").document(athlete_id).get()
        if not doc.exists:
            return False
        
        stored_hash = doc.get("access_code_hash")
        provided_hash = hash_code(provided_code)
        
        return stored_hash == provided_hash
    except Exception as e:
        logger.error(f"Erreur vérification: {e}")
        return False
 
@st.cache_data(ttl=300)
def load_athlete_data(athlete_id: str) -> dict:
    """Charge les données d'un combattant."""
    try:
        doc = db.collection("athletes").document(athlete_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        logger.error(f"Erreur chargement données: {e}")
        return None
 
# === PAGE LOGIN ===
def page_login():
    """Affiche la page de connexion."""
    col_left, col_center, col_right = st.columns([1, 2.5, 1])
 
    with col_center:
        st.markdown('<div class="card-container"></div>', unsafe_allow_html=True)
        
        # Logo
        try:
            st.image("https://studio-7691886667-ec4b3.web.app/logo.png", use_container_width=True)
        except:
            st.markdown("# ⚔️ ASL Vision Engine")
        
        st.markdown('<h1 class="login-title">PROFIL COMBATTANT</h1>', unsafe_allow_html=True)
        
        # Sélecteur combattant
        athletes = get_all_athletes()
        if not athletes:
            st.error("❌ Aucun combattant disponible")
            return
        
        selected_athlete = st.selectbox(
            "Sélectionner votre profil:",
            athletes,
            format_func=lambda x: x.replace("_", " ").title()
        )
        
        # Code d'accès
        code_acces = st.text_input("Code d'accès", type="password", placeholder="Ex: T3G2VT-0")
        
        # Connexion
        if st.button("ACCÉDER AU PROFIL", use_container_width=True):
            if code_acces:
                # Vérifier le code d'accès
                if verify_access_code(selected_athlete, code_acces):
                    st.session_state.auth_success = True
                    st.session_state.athlete_id = selected_athlete
                    st.session_state.athlete_data = load_athlete_data(selected_athlete)
                    st.success("✅ Connexion réussie!")
                    st.rerun()
                else:
                    st.error("❌ Code d'accès invalide")
            else:
                st.warning("⚠️ Veuillez entrer votre code d'accès")
 
# === PAGE PROFIL ===
def page_profile():
    """Affiche le profil du combattant."""
    
    athlete_data = st.session_state.athlete_data
    
    if not athlete_data:
        st.error("❌ Impossible de charger les données")
        if st.button("Retour à la connexion"):
            st.session_state.auth_success = False
            st.rerun()
        return
    
    # === HEADER ===
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f'<h1 class="profile-title">⚔️ {athlete_data.get("name", "Combattant")}</h1>', 
                   unsafe_allow_html=True)
        st.markdown(f"**Club:** {athlete_data.get('club', 'N/A')} | **Catégorie:** {athlete_data.get('category', 'N/A')}")
    
    with col2:
        if st.button("🔒 Déconnexion"):
            st.session_state.auth_success = False
            st.session_state.athlete_data = None
            st.rerun()
    
    st.divider()
    
    # === STATS PRINCIPALES ===
    stats = athlete_data.get("stats", {})
    
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
                "Ratio Touches": f"{stats.get('total_touches_scored', 0) / max(stats.get('total_touches_received', 1), 1):.2f}",
            }
            for key, value in summary_data.items():
                st.write(f"**{key}:** {value}")
        
        with col2:
            st.subheader("Pourcentages")
            if total_fights > 0:
                fig = go.Figure(data=[go.Pie(
                    labels=['Victoires', 'Défaites'],
                    values=[victories, defeats],
                    marker=dict(colors=['#26D07C', '#FF6B6B'])
                )])
                fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucun combat encore")
    
    # TAB 2: Actions breakdown
    with tab2:
        actions = athlete_data.get("actions_breakdown", {})
        
        if actions:
            df_actions = pd.DataFrame(list(actions.items()), columns=["Action", "Nombre"])
            
            fig = px.bar(
                df_actions,
                x="Action",
                y="Nombre",
                color="Nombre",
                color_continuous_scale="Viridis",
                title="Répartition des Actions"
            )
            fig.update_layout(
                height=400,
                showlegend=False,
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Tableau
            st.dataframe(df_actions, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune donnée d'action disponible")
    
    # TAB 3: Tendance performance
    with tab3:
        trend = athlete_data.get("performance_trend", [])
        
        if trend:
            df_trend = pd.DataFrame(trend)
            
            # Convertir dates si présentes
            if "date" in df_trend.columns:
                df_trend["date"] = pd.to_datetime(df_trend["date"])
                df_trend = df_trend.sort_values("date")
            
            # Graphique tendance
            if "touches_scored" in df_trend.columns:
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=df_trend.index,
                    y=df_trend.get("touches_scored", []),
                    mode='lines+markers',
                    name='Touches Marquées',
                    line=dict(color='#26D07C', width=2),
                ))
                
                if "touches_received" in df_trend.columns:
                    fig.add_trace(go.Scatter(
                        x=df_trend.index,
                        y=df_trend.get("touches_received", []),
                        mode='lines+markers',
                        name='Touches Reçues',
                        line=dict(color='#FF6B6B', width=2),
                    ))
                
                fig.update_layout(
                    title="Performance au fil du temps",
                    xaxis_title="Combat #",
                    yaxis_title="Touches",
                    height=400,
                    hovermode='x unified',
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df_trend, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune tendance disponible")
    
    st.divider()
    
    # === JSON BRUT (DEBUG) ===
    with st.expander("🔍 Données brutes (Debug)"):
        st.json(athlete_data)
 
# === ROUTER PRINCIPAL ===
def main():
    if not st.session_state.auth_success:
        page_login()
    else:
        page_profile()
 
if __name__ == "__main__":
    main()
