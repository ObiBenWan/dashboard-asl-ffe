import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import hashlib
import json
import tempfile
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 1. CONFIGURATION
st.set_page_config(page_title="ASL-FFE - Dashboard", layout="wide")

# 2. DESIGN CSS (Inspiré du look "FighterProfiles")
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. INITIALISATION FIREBASE (Gardée identique)
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

if 'auth_success' not in st.session_state:
    st.session_state.auth_success = False

# --- LOGIQUE DE CONNEXION ---
if not st.session_state.auth_success:
    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        st.title("Connexion Athlète")
        prenom = st.text_input("Prénom").strip().lower()
        code = st.text_input("Code", type="password").strip()
        if st.button("ACCÉDER"):
            doc = db.collection("athletes").document(prenom).get()
            if doc.exists:
                data = doc.to_dict()
                if hashlib.sha256(code.encode()).hexdigest() == data.get("access_code_hash"):
                    st.session_state.auth_success = True
                    st.session_state.athlete_data = data
                    st.rerun()
            st.error("Identifiants incorrects")

# --- PAGE PROFIL (STYLE FIGHTERPROFILES.JS) ---
else:
    d = st.session_state.athlete_data
    stats = json.loads(d.get("json_data", "{}"))
    
    st.title(f"🥊 Profil : {d.get('name')}")
    st.subheader(f"{d.get('club')} | {d.get('category')}")
    
    col1, col2 = st.columns([1, 1])

    with col1:
        # --- GRAPHIQUE RADAR (Capacités) ---
        st.write("### 📊 Analyse des Aptitudes")
        # On simule les données si elles ne sont pas dans le JSON, ou on les extrait
        categories = ['Vitesse', 'Force', 'Technique', 'Tactique', 'Mental']
        valeurs = [80, 75, 90, 85, 70] # Exemple par défaut
        
        fig_radar = go.Figure(data=go.Scatterpolar(
          r=valeurs,
          theta=categories,
          fill='toself',
          line_color='#22d3ee'
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white"
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col2:
        # --- JAUGE D'EXPLOSIVITÉ ---
        st.write("### ⚡ Explosivité (Wrist Velocity)")
        explosivite = stats.get("explosivite", 75) # Valeur extraite du JSON
        
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = explosivite,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Score Vitesse (%)"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "#22d3ee"},
                'steps': [
                    {'range': [0, 50], 'color': "#334155"},
                    {'range': [50, 80], 'color': "#475569"}
                ]
            }
        ))
        fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.divider()

    col3, col4 = st.columns([1, 1])

    with col3:
        # --- RÉPARTITION DES ATTAQUES ---
        st.write("### 🤺 Types d'Attaques")
        actions = stats.get("actions_breakdown", {})
        if actions:
            df_pie = pd.DataFrame(list(actions.items()), columns=["Type", "Nombre"])
            fig_pie = px.pie(df_pie, values='Nombre', names='Type', hole=.4,
                             color_discrete_sequence=px.colors.sequential.Cyan)
            fig_pie.update_layout(showlegend=True, paper_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig_pie, use_container_width=True)

    with col4:
        # --- RÉSULTATS RÉCENTS ---
        st.write("### 🏆 Derniers Résultats")
        win_loss = [stats.get("victories", 0), stats.get("defeats", 0)]
        fig_bar = px.bar(x=["Victoires", "Défaites"], y=win_loss, color=["Victoires", "Défaites"],
                         color_discrete_map={"Victoires": "#22c55e", "Défaites": "#ef4444"})
        fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    if st.button("Se déconnecter"):
        st.session_state.auth_success = False
        st.rerun()
