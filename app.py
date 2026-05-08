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
 
# 2. DESIGN TOKENS (Identique à FighterProfiles.js)
T = {
    'bg':       '#07090d',
    'surface':  '#0d1117',
    'panel':    '#111827',
    'border':   '#1f2937',
    'borderHi': '#374151',
    'cyan':     '#22d3ee',
    'cyanDim':  '#0891b2',
    'slate':    '#94a3b8',
    'slateHi':  '#cbd5e1',
    'rouge':    '#ef4444',
    'rougeDim': '#7f1d1d',
    'vert':     '#22c55e',
    'vertDim':  '#14532d',
    'success':  '#22c55e',
    'warning':  '#f59e0b',
    'danger':   '#ef4444',
    'info':     '#38bdf8',
}
 
# 3. CSS GLOBAL
st.markdown(f"""
    <style>
    * {{ margin:0; padding:0; }}
    html, body, [data-testid="stAppViewContainer"] {{ 
        background-color: {T['bg']} !important;
        color: {T['slateHi']} !important;
    }}
    [data-testid="stHeader"] {{ background-color: transparent !important; }}
    [data-testid="stToolbar"] {{ display: none !important; }}
    .stTabs [role="tablist"] {{
        border-bottom: 1px solid {T['border']};
    }}
    .stTabs [role="tab"][aria-selected="true"] {{
        color: {T['cyan']} !important;
        border-bottom: 2px solid {T['cyan']} !important;
    }}
    .stMetric {{ 
        background-color: {T['panel']} !important;
        border: 1px solid {T['border']} !important;
        border-radius: 8px !important;
        padding: 12px !important;
    }}
    .stButton>button {{
        background-color: {T['cyan']} !important;
        color: {T['bg']} !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        padding: 8px 16px !important;
    }}
    .stButton>button:hover {{
        background-color: {T['cyanDim']} !important;
    }}
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
    # Container centré
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown(f"""
            <div style="
                background-color: {T['panel']};
                border: 1px solid {T['border']};
                border-radius: 12px;
                padding: 40px;
                text-align: center;
            ">
        """, unsafe_allow_html=True)
        
        # Logo
        st.image("https://studio-7691886667-ec4b3.web.app/logo.png", width=200)
        
        st.markdown(f"""
            <h1 style="
                color: {T['slateHi']};
                font-size: 1.8rem;
                font-weight: 700;
                margin-top: 20px;
                margin-bottom: 10px;
                letter-spacing: 0.05em;
            ">⚔️ ASL-FFE</h1>
            <p style="
                color: {T['slate']};
                font-size: 0.9rem;
                margin-bottom: 30px;
                letter-spacing: 0.04em;
            ">PROFIL COMBATTANT</p>
        """, unsafe_allow_html=True)
        
        prenom = st.text_input("Prénom", placeholder="Ex: Guillaume", key="login_prenom")
        code = st.text_input("Code d'accès", type="password", placeholder="••••••••", key="login_code")
        
        if st.button("🔓 ACCÉDER AU PROFIL", key="login_btn", use_container_width=True):
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
        
        st.markdown("</div>", unsafe_allow_html=True)
 
# ═══════════════════════════════════════════════════════════════════════════════
# PAGE PROFIL
# ═══════════════════════════════════════════════════════════════════════════════
 
else:
    data = st.session_state.athlete_data
    stats = json.loads(data.get("json_data", "{}")) if isinstance(data.get("json_data"), str) else data.get("json_data", {})
    
    # En-tête
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.markdown(f"""
            <div style="padding: 20px 0;">
                <h1 style="color: {T['cyan']}; font-size: 2.2rem; margin: 0;">
                    ⚔️ {st.session_state.athlete_name.upper()}
                </h1>
                <p style="color: {T['slate']}; font-size: 0.9rem; margin-top: 5px;">
                    {data.get('club', 'ASL-FFE')} • {data.get('category', 'N/A')}
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    with col_header2:
        if st.button("🔒 Déconnexion", key="logout_btn"):
            st.session_state.auth_success = False
            st.session_state.athlete_data = None
            st.rerun()
    
    st.divider()
    
    # STATS PRINCIPALES
    st.subheader("📊 Statistiques Principales")
    
    victories = stats.get("victories", 0) if isinstance(stats, dict) else 0
    defeats = stats.get("defeats", 0) if isinstance(stats, dict) else 0
    total = victories + defeats
    winrate = (victories / total * 100) if total > 0 else 0
    touches_scored = stats.get("total_touches_scored", 0) if isinstance(stats, dict) else 0
    touches_received = stats.get("total_touches_received", 0) if isinstance(stats, dict) else 0
    head_zone_pct = stats.get("head_zone_touches_percentage", 0) if isinstance(stats, dict) else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏆 Win Rate", f"{winrate:.1f}%", f"{victories}W-{defeats}L")
    with col2:
        st.metric("🎯 Touches Marquées", int(touches_scored))
    with col3:
        st.metric("🛡️ Touches Reçues", int(touches_received))
    with col4:
        st.metric("💡 Cible Tête %", f"{head_zone_pct:.1f}%")
    
    st.divider()
    
    # ONGLETS
    tab1, tab2, tab3 = st.tabs(["📈 Analyse", "⚡ Actions", "📊 Historique"])
    
    # ─── TAB 1: ANALYSE ──────────────────────────────────────────────────────
    with tab1:
        col_graph1, col_graph2 = st.columns(2)
        
        # Radar chart (capacités simulées)
        with col_graph1:
            st.markdown("**Profil Physique**")
            categories = ['Vitesse', 'Force', 'Technique', 'Tactique', 'Mental']
            values = [
                min(100, (touches_scored / max(touches_received, 1)) * 50 + 40),  # Vitesse
                80,  # Force (simulée)
                min(100, (winrate * 1.2)),  # Technique
                min(100, (victories * 10)),  # Tactique
                85   # Mental (simulée)
            ]
            
            fig_radar = go.Figure(data=go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                line=dict(color=T['cyan']),
                fillcolor=T['cyan']+'22',
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100], gridcolor=T['border']),
                    angularaxis=dict(gridcolor=T['border']),
                    bgcolor=T['panel']+'00'
                ),
                paper_bgcolor=T['panel'],
                plot_bgcolor=T['panel'],
                font=dict(color=T['slateHi'], size=10),
                showlegend=False,
                height=350,
                margin=dict(l=50, r=50, t=50, b=50)
            )
            st.plotly_chart(fig_radar, use_container_width=True, config={'displayModeBar': False})
        
        # Jauge explosivité
        with col_graph2:
            st.markdown("**Explosivité Sabre**")
            explosivite = min(100, stats.get("explosivity", 75) if isinstance(stats, dict) else 75)
            
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=explosivite,
                domain=dict(x=[0, 1], y=[0, 1]),
                gauge=dict(
                    axis=dict(range=[None, 100], gridcolor=T['border']),
                    bar=dict(color=T['cyan']),
                    steps=[
                        dict(range=[0, 50], color=T['panel']),
                        dict(range=[50, 80], color=T['panel']),
                        dict(range=[80, 100], color=T['panel'])
                    ],
                    threshold=dict(
                        line=dict(color="red", width=4),
                        thickness=0.75,
                        value=90
                    )
                ),
                number=dict(font=dict(color=T['cyan'])),
            ))
            fig_gauge.update_layout(
                paper_bgcolor=T['panel'],
                font=dict(color=T['slateHi'], size=11),
                height=350,
                margin=dict(l=20, r=20, t=80, b=20)
            )
            st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
    
    # ─── TAB 2: ACTIONS ──────────────────────────────────────────────────────
    with tab2:
        actions = stats.get("actions_breakdown", {}) if isinstance(stats, dict) else {}
        
        if actions:
            col_pie1, col_pie2 = st.columns(2)
            
            # Pie chart actions
            with col_pie1:
                st.markdown("**Répartition des Actions**")
                df_actions = pd.DataFrame(list(actions.items()), columns=["Type", "Nombre"])
                
                fig_pie = px.pie(
                    df_actions, 
                    values='Nombre', 
                    names='Type',
                    hole=0.3,
                    color_discrete_sequence=[T['cyan'], T['vert'], T['rouge'], T['warning'], T['info']]
                )
                fig_pie.update_layout(
                    paper_bgcolor=T['panel'],
                    plot_bgcolor=T['panel'],
                    font=dict(color=T['slateHi'], size=10),
                    height=350,
                )
                st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
            
            # Bar chart
            with col_pie2:
                st.markdown("**Statistiques Détaillées**")
                fig_bar = px.bar(
                    df_actions,
                    x='Type',
                    y='Nombre',
                    color='Type',
                    color_discrete_sequence=[T['cyan'], T['vert'], T['rouge'], T['warning'], T['info']]
                )
                fig_bar.update_layout(
                    paper_bgcolor=T['panel'],
                    plot_bgcolor=T['panel'],
                    font=dict(color=T['slateHi'], size=10),
                    showlegend=False,
                    height=350,
                    xaxis_title="",
                    yaxis_title="Nombre"
                )
                st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Aucune donnée d'action disponible")
    
    # ─── TAB 3: HISTORIQUE ──────────────────────────────────────────────────
    with tab3:
        trend = stats.get("performance_trend", []) if isinstance(stats, dict) else []
        
        if trend and isinstance(trend, list) and len(trend) > 0:
            st.markdown("**Évolution des Performances**")
            df_trend = pd.DataFrame(trend)
            
            # Assurer les colonnes nécessaires
            if 'touches_scored' in df_trend.columns and 'touches_received' in df_trend.columns:
                fig_trend = go.Figure()
                
                fig_trend.add_trace(go.Scatter(
                    x=df_trend.index,
                    y=df_trend['touches_scored'],
                    mode='lines+markers',
                    name='Touches Marquées',
                    line=dict(color=T['vert'], width=3),
                    marker=dict(size=8)
                ))
                
                fig_trend.add_trace(go.Scatter(
                    x=df_trend.index,
                    y=df_trend['touches_received'],
                    mode='lines+markers',
                    name='Touches Reçues',
                    line=dict(color=T['rouge'], width=3),
                    marker=dict(size=8)
                ))
                
                fig_trend.update_layout(
                    paper_bgcolor=T['panel'],
                    plot_bgcolor=T['panel'],
                    font=dict(color=T['slateHi'], size=10),
                    hovermode='x unified',
                    height=400,
                    xaxis_title="Combat",
                    yaxis_title="Touches"
                )
                
                st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
            else:
                st.dataframe(df_trend, use_container_width=True)
        else:
            st.info("Aucun historique disponible")
