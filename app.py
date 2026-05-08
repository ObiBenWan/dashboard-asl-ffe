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
 
# 2. DESIGN - COULEURS ORIGINALES
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
        padding: 10px 20px !important;
        width: 100% !important;
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
    }
    
    .stTextInput input::placeholder {
        color: hsl(180, 10%, 50%) !important;
    }
    
    .icon-small { font-size: 1.2rem; margin-right: 4px; }
    
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
 
if 'auth_success' not in st.session_state:
    st.session_state.auth_success = False
 
# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONNEXION
# ═══════════════════════════════════════════════════════════════════════════════
 
if not st.session_state.auth_success:
    col1, col2, col3 = st.columns([1, 1.8, 1])
    
    with col2:
        st.markdown("""
            <div style="
                background-color: hsl(180, 25%, 20%);
                border: 1px solid hsl(180, 25%, 25%);
                border-radius: 12px;
                padding: 50px 40px;
                text-align: center;
            ">
        """, unsafe_allow_html=True)
        
        # Logo du club
        st.image("https://studio-7691886667-ec4b3.web.app/logo.png", width=220)
        
        st.markdown("""
            <h1 style="
                color: hsl(210, 20%, 95%);
                font-size: 1.9rem;
                font-weight: 700;
                margin-top: 25px;
                margin-bottom: 8px;
                letter-spacing: 0.05em;
            ">ASL-FFE</h1>
            <p style="
                color: hsl(180, 10%, 60%);
                font-size: 0.92rem;
                margin-bottom: 35px;
                letter-spacing: 0.04em;
            ">PROFIL COMBATTANT</p>
        """, unsafe_allow_html=True)
        
        prenom = st.text_input(
            "Prénom",
            placeholder="Entrez votre prénom",
            key="login_prenom",
            label_visibility="collapsed"
        )
        code = st.text_input(
            "Code d'accès",
            type="password",
            placeholder="••••••••",
            key="login_code",
            label_visibility="collapsed"
        )
        
        if st.button("🔓 ACCÉDER AU PROFIL", key="login_btn"):
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
    
    # En-tête avec logo + nom
    col_header1, col_header2 = st.columns([3, 1])
    
    with col_header1:
        st.markdown(f"""
            <div style="padding: 20px 0;">
                <h1 style="
                    color: hsl(182, 100%, 74%);
                    font-size: 2.3rem;
                    margin: 0;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                ">
                    ⚔️ {st.session_state.athlete_name.upper()}
                </h1>
                <p style="
                    color: hsl(180, 10%, 60%);
                    font-size: 0.92rem;
                    margin-top: 6px;
                ">
                    {data.get('club', 'ASL-FFE')} • {data.get('category', 'N/A')}
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    with col_header2:
        if st.button("🚪", key="logout_btn", help="Déconnexion"):
            st.session_state.auth_success = False
            st.session_state.athlete_data = None
            st.rerun()
    
    st.divider()
    
    # STATS PRINCIPALES
    st.markdown("""
        <h2 style="
            color: hsl(210, 20%, 95%);
            font-size: 1.3rem;
            margin-bottom: 15px;
        ">📊 Statistiques Principales</h2>
    """, unsafe_allow_html=True)
    
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
        
        # Radar chart
        with col_graph1:
            st.markdown("**📊 Profil Physique**")
            categories = ['Vitesse', 'Force', 'Technique', 'Tactique', 'Mental']
            values = [
                min(100, (touches_scored / max(touches_received, 1)) * 50 + 40),
                80,
                min(100, (winrate * 1.2)),
                min(100, (victories * 10)),
                85
            ]
            
            fig_radar = go.Figure(data=go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                line=dict(color='hsl(182, 100%, 74%)'),
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100]),
                ),
                paper_bgcolor='hsl(180, 25%, 20%)',
                plot_bgcolor='hsl(180, 25%, 20%)',
                font=dict(color='hsl(210, 20%, 95%)', size=10),
                showlegend=False,
                height=350,
            )
            st.plotly_chart(fig_radar, use_container_width=True, config={'displayModeBar': False})
        
        # Jauge explosivité
        with col_graph2:
            st.markdown("**⚡ Explosivité Sabre**")
            explosivite = min(100, stats.get("explosivity", 75) if isinstance(stats, dict) else 75)
            
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=explosivite,
                gauge=dict(
                    axis=dict(range=[None, 100]),
                    bar=dict(color='hsl(182, 100%, 74%)'),
                ),
                number=dict(font=dict(color='hsl(182, 100%, 74%)')),
            ))
            fig_gauge.update_layout(
                paper_bgcolor='hsl(180, 25%, 20%)',
                plot_bgcolor='hsl(180, 25%, 20%)',
                font=dict(color='hsl(210, 20%, 95%)', size=11),
                height=350,
            )
            st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
    
    # ─── TAB 2: ACTIONS ──────────────────────────────────────────────────────
    with tab2:
        actions = stats.get("actions_breakdown", {}) if isinstance(stats, dict) else {}
        
        if actions:
            col_pie1, col_pie2 = st.columns(2)
            
            with col_pie1:
                st.markdown("**🎯 Répartition des Actions**")
                df_actions = pd.DataFrame(list(actions.items()), columns=["Type", "Nombre"])
                
                fig_pie = px.pie(
                    df_actions, 
                    values='Nombre', 
                    names='Type',
                    hole=0.3,
                    color_discrete_sequence=['hsl(182, 100%, 74%)', 'hsl(0, 100%, 50%)', 'hsl(120, 100%, 50%)', 'hsl(60, 100%, 50%)', 'hsl(240, 100%, 50%)']
                )
                fig_pie.update_layout(
                    paper_bgcolor='hsl(180, 25%, 20%)',
                    plot_bgcolor='hsl(180, 25%, 20%)',
                    font=dict(color='hsl(210, 20%, 95%)', size=10),
                    height=350,
                )
                st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
            
            with col_pie2:
                st.markdown("**📋 Statistiques Détaillées**")
                fig_bar = px.bar(
                    df_actions,
                    x='Type',
                    y='Nombre',
                    color_discrete_sequence=['hsl(182, 100%, 74%)']
                )
                fig_bar.update_layout(
                    paper_bgcolor='hsl(180, 25%, 20%)',
                    plot_bgcolor='hsl(180, 25%, 20%)',
                    font=dict(color='hsl(210, 20%, 95%)', size=10),
                    showlegend=False,
                    height=350,
                    xaxis_title="",
                    yaxis_title="Nombre"
                )
                st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("⚠️ Aucune donnée d'action disponible")
    
    # ─── TAB 3: HISTORIQUE ──────────────────────────────────────────────────
    with tab3:
        trend = stats.get("performance_trend", []) if isinstance(stats, dict) else []
        
        if trend and isinstance(trend, list) and len(trend) > 0:
            st.markdown("**📈 Évolution des Performances**")
            df_trend = pd.DataFrame(trend)
            
            if 'touches_scored' in df_trend.columns and 'touches_received' in df_trend.columns:
                fig_trend = go.Figure()
                
                fig_trend.add_trace(go.Scatter(
                    x=df_trend.index,
                    y=df_trend['touches_scored'],
                    mode='lines+markers',
                    name='Touches Marquées',
                    line=dict(color='hsl(120, 100%, 50%)', width=3),
                    marker=dict(size=8, color='hsl(120, 100%, 50%)')
                ))
                
                fig_trend.add_trace(go.Scatter(
                    x=df_trend.index,
                    y=df_trend['touches_received'],
                    mode='lines+markers',
                    name='Touches Reçues',
                    line=dict(color='hsl(0, 100%, 50%)', width=3),
                    marker=dict(size=8, color='hsl(0, 100%, 50%)')
                ))
                
                fig_trend.update_layout(
                    paper_bgcolor='hsl(180, 25%, 20%)',
                    plot_bgcolor='hsl(180, 25%, 20%)',
                    font=dict(color='hsl(210, 20%, 95%)', size=10),
                    hovermode='x unified',
                    height=400,
                    xaxis_title="",
                    yaxis_title="Touches"
                )
                
                st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
            else:
                st.dataframe(df_trend, use_container_width=True)
        else:
            st.info("⚠️ Aucun historique disponible")
