#!/usr/bin/env python3
import streamlit as st
import firebase_admin
from firebase_admin import firestore
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
 
# PAGE CONFIG
st.set_page_config(page_title="Profil - ASL-FFE", layout="wide", initial_sidebar_state="collapsed")
 
# DESIGN
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');
    * { margin:0; padding:0; }
    html, body, [data-testid="stAppViewContainer"] { 
        background-color: hsl(180, 25%, 15%) !important;
        color: hsl(210, 20%, 95%) !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    h1, h2, h3 { color: hsl(210, 20%, 95%) !important; }
    .stTabs [role="tablist"] { border-bottom: 2px solid hsl(180, 25%, 25%); }
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
    }
    .stDivider { border-top: 1px solid hsl(180, 25%, 25%) !important; }
    </style>
    """, unsafe_allow_html=True)
 
# FIREBASE
db = st.session_state.db
 
if not st.session_state.auth_success:
    st.switch_page("app.py")
else:
    data = st.session_state.athlete_data
    stats = json.loads(data.get("json_data", "{}")) if isinstance(data.get("json_data"), str) else data.get("json_data", {})
    
    # HEADER
    col_h1, col_h2 = st.columns([3, 1])
    
    with col_h1:
        st.markdown(f"""
            <div style="padding: 20px 0;">
                <h1 style="color: hsl(182, 100%, 74%); font-size: 2.4rem; margin: 0;">
                    {st.session_state.athlete_name.upper()}
                </h1>
                <p style="color: hsl(180, 10%, 60%); font-size: 0.95rem; margin-top: 6px;">
                    {data.get('club', 'ASL-FFE')} • {data.get('category', 'N/A')}
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    with col_h2:
        if st.button("↪️ Déconnexion", key="logout"):
            st.session_state.auth_success = False
            st.session_state.athlete_data = None
            st.switch_page("app.py")
    
    st.divider()
    
    # EXTRACT STATS
    victories = stats.get("victories", 0) if isinstance(stats, dict) else 0
    defeats = stats.get("defeats", 0) if isinstance(stats, dict) else 0
    total = victories + defeats
    winrate = (victories / total * 100) if total > 0 else 0
    touches_scored = stats.get("total_touches_scored", 0) if isinstance(stats, dict) else 0
    touches_received = stats.get("total_touches_received", 0) if isinstance(stats, dict) else 0
    head_zone_pct = stats.get("head_zone_touches_percentage", 0) if isinstance(stats, dict) else 0
    
    # MAIN STATS
    st.subheader("📊 Statistiques Principales")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Win Rate", f"{winrate:.1f}%", f"{victories}W-{defeats}L")
    with col2:
        st.metric("Touches Marquées", int(touches_scored))
    with col3:
        st.metric("Touches Reçues", int(touches_received))
    with col4:
        st.metric("Cible Tête %", f"{head_zone_pct:.1f}%")
    
    st.divider()
    
    # TABS
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Analyse Physique",
        "⚡ Actions",
        "🎯 Zones de Touche",
        "🏆 Cartons FFE",
        "📊 Historique"
    ])
    
    # ─── TAB 1: ANALYSE PHYSIQUE ──────────────────────────────────────────────
    with tab1:
        col_g1, col_g2, col_g3 = st.columns(3)
        
        with col_g1:
            st.markdown("**Profil Physique (Radar)**")
            categories = ['Vitesse', 'Force', 'Technique', 'Tactique', 'Mental']
            values = [
                min(100, (touches_scored / max(touches_received, 1)) * 50 + 40),
                80,
                min(100, (winrate * 1.2)),
                min(100, (victories * 10)),
                85
            ]
            
            fig_radar = go.Figure(data=go.Scatterpolar(
                r=values, theta=categories, fill='toself',
                line=dict(color='hsl(182, 100%, 74%)'),
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                paper_bgcolor='hsl(180, 25%, 20%)',
                plot_bgcolor='hsl(180, 25%, 20%)',
                font=dict(color='hsl(210, 20%, 95%)', size=10),
                showlegend=False,
                height=350,
            )
            st.plotly_chart(fig_radar, use_container_width=True, config={'displayModeBar': False})
        
        with col_g2:
            st.markdown("**Explosivité Sabre**")
            explosivite = min(100, stats.get("explosivity", 75) if isinstance(stats, dict) else 75)
            
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=explosivite,
                gauge=dict(axis=dict(range=[None, 100]), bar=dict(color='hsl(182, 100%, 74%)')),
                number=dict(font=dict(color='hsl(182, 100%, 74%)')),
            ))
            fig_gauge.update_layout(
                paper_bgcolor='hsl(180, 25%, 20%)',
                plot_bgcolor='hsl(180, 25%, 20%)',
                font=dict(color='hsl(210, 20%, 95%)', size=11),
                height=350,
            )
            st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
        
        with col_g3:
            st.markdown("**Résumé Stats**")
            st.markdown(f"""
                <div style="background-color: hsl(180, 25%, 20%); border: 1px solid hsl(180, 25%, 25%);
                border-radius: 8px; padding: 15px; font-size: 0.9rem;">
                <p><strong>Combats:</strong> {total}</p>
                <p><strong>Victoires:</strong> {victories}</p>
                <p><strong>Défaites:</strong> {defeats}</p>
                <p><strong>Touches Total:</strong> {touches_scored + touches_received}</p>
                <p><strong>Moyenne/Combat:</strong> {(touches_scored / max(total, 1)):.1f} touches</p>
                </div>
            """, unsafe_allow_html=True)
    
    # ─── TAB 2: ACTIONS ──────────────────────────────────────────────────────
    with tab2:
        actions = stats.get("actions_breakdown", {}) if isinstance(stats, dict) else {}
        
        if actions:
            col_a1, col_a2 = st.columns(2)
            
            with col_a1:
                st.markdown("**Répartition des Actions (Pie)**")
                df_actions = pd.DataFrame(list(actions.items()), columns=["Type", "Nombre"])
                
                fig_pie = px.pie(df_actions, values='Nombre', names='Type', hole=0.3,
                    color_discrete_sequence=['hsl(182, 100%, 74%)', 'hsl(0, 100%, 50%)', 'hsl(120, 100%, 50%)', 'hsl(60, 100%, 50%)'])
                fig_pie.update_layout(
                    paper_bgcolor='hsl(180, 25%, 20%)',
                    plot_bgcolor='hsl(180, 25%, 20%)',
                    font=dict(color='hsl(210, 20%, 95%)', size=10),
                    height=350,
                )
                st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
            
            with col_a2:
                st.markdown("**Détails par Action (Bar)**")
                fig_bar = px.bar(df_actions, x='Type', y='Nombre', color_discrete_sequence=['hsl(182, 100%, 74%)'])
                fig_bar.update_layout(
                    paper_bgcolor='hsl(180, 25%, 20%)',
                    plot_bgcolor='hsl(180, 25%, 20%)',
                    font=dict(color='hsl(210, 20%, 95%)', size=10),
                    showlegend=False,
                    height=350,
                    xaxis_title="", yaxis_title="Nombre"
                )
                st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Aucune donnée d'action")
    
    # ─── TAB 3: ZONES DE TOUCHE ──────────────────────────────────────────────
    with tab3:
        st.markdown("**Zones de Touche (FighterProfiles style)**")
        
        col_z1, col_z2 = st.columns(2)
        
        with col_z1:
            st.markdown("""
                <div style="background-color: hsl(180, 25%, 20%); border: 1px solid hsl(180, 25%, 25%);
                border-radius: 8px; padding: 15px;">
                <h4 style="color: hsl(182, 100%, 74%); margin-bottom: 10px;">Grille de Zones</h4>
                <table style="width:100%; font-size: 0.85rem;">
                <tr><td style="padding: 5px;"><strong>Tête</strong></td><td style="text-align: right; color: hsl(0, 100%, 50%);">+5 pts</td></tr>
                <tr><td style="padding: 5px;"><strong>Tronc</strong></td><td style="text-align: right; color: hsl(0, 100%, 50%);">+5 pts</td></tr>
                <tr><td style="padding: 5px;"><strong>Bras armé</strong></td><td style="text-align: right; color: hsl(240, 100%, 50%);">+3 pts</td></tr>
                <tr><td style="padding: 5px;"><strong>Jambe armée</strong></td><td style="text-align: right; color: hsl(240, 100%, 50%);">+3 pts</td></tr>
                <tr><td style="padding: 5px;"><strong>Main</strong></td><td style="text-align: right; color: hsl(120, 100%, 50%);">+1 pt</td></tr>
                <tr><td style="padding: 5px;"><strong>Arme</strong></td><td style="text-align: right; color: hsl(120, 100%, 50%);">+1 pt</td></tr>
                </table>
                </div>
            """, unsafe_allow_html=True)
        
        with col_z2:
            # Heatmap simple
            zones = ['Tête', 'Tronc', 'Bras', 'Jambe', 'Main', 'Arme']
            hits = [5, 4, 3, 2, 1, 1]  # Données simulées
            
            fig_heatmap = go.Figure(data=go.Bar(
                x=zones, y=hits,
                marker=dict(color=hits, colorscale=['hsl(240, 100%, 50%)', 'hsl(0, 100%, 50%)']),
            ))
            fig_heatmap.update_layout(
                paper_bgcolor='hsl(180, 25%, 20%)',
                plot_bgcolor='hsl(180, 25%, 20%)',
                font=dict(color='hsl(210, 20%, 95%)', size=10),
                showlegend=False,
                height=250,
                xaxis_title="", yaxis_title="Touches"
            )
            st.plotly_chart(fig_heatmap, use_container_width=True, config={'displayModeBar': False})
    
    # ─── TAB 4: CARTONS FFE ──────────────────────────────────────────────────
    with tab4:
        st.markdown("**Système de Cartons (Règlement FFE)**")
        
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        
        cartons_data = [
            {"g": 1, "label": "Groupe 1", "color": "#f1f5f9", "txt": "BLANC", "pts": 0},
            {"g": 2, "label": "Groupe 2", "color": "#fbbf24", "txt": "JAUNE", "pts": 3},
            {"g": 3, "label": "Groupe 3", "color": "#ef4444", "txt": "ROUGE", "pts": 5},
            {"g": 4, "label": "Groupe 4", "color": "#030712", "txt": "NOIR", "pts": 0},
        ]
        
        for i, carton in enumerate(cartons_data):
            with [col_c1, col_c2, col_c3, col_c4][i]:
                st.markdown(f"""
                    <div style="background-color: {carton['color']}; border: 2px solid {carton['color']};
                    border-radius: 8px; padding: 20px; text-align: center;">
                    <p style="color: #0f172a; font-weight: 700; font-size: 1.2rem; margin: 0;">
                        {carton['txt']}
                    </p>
                    <p style="color: #0f172a; font-size: 0.9rem; margin: 5px 0 0 0;">
                        {carton['pts']} pts
                    </p>
                    </div>
                """, unsafe_allow_html=True)
        
        st.info("Règle FFE: Gr.1(1→BLANC, 2+→JAUNE) | Gr.2(1→JAUNE, 2+→ROUGE) | Gr.3(1→ROUGE, 2+→NOIR) | Gr.4(1+→NOIR)")
    
    # ─── TAB 5: HISTORIQUE ──────────────────────────────────────────────────
    with tab5:
        trend = stats.get("performance_trend", []) if isinstance(stats, dict) else []
        
        if trend and isinstance(trend, list) and len(trend) > 0:
            st.markdown("**Évolution des Performances**")
            df_trend = pd.DataFrame(trend)
            
            if 'touches_scored' in df_trend.columns and 'touches_received' in df_trend.columns:
                fig_trend = go.Figure()
                
                fig_trend.add_trace(go.Scatter(
                    x=df_trend.index, y=df_trend['touches_scored'],
                    mode='lines+markers', name='Touches Marquées',
                    line=dict(color='hsl(120, 100%, 50%)', width=3),
                    marker=dict(size=8)
                ))
                
                fig_trend.add_trace(go.Scatter(
                    x=df_trend.index, y=df_trend['touches_received'],
                    mode='lines+markers', name='Touches Reçues',
                    line=dict(color='hsl(0, 100%, 50%)', width=3),
                    marker=dict(size=8)
                ))
                
                fig_trend.update_layout(
                    paper_bgcolor='hsl(180, 25%, 20%)',
                    plot_bgcolor='hsl(180, 25%, 20%)',
                    font=dict(color='hsl(210, 20%, 95%)', size=10),
                    hovermode='x unified',
                    height=400,
                )
                st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
            else:
                st.dataframe(df_trend, use_container_width=True)
        else:
            st.info("Aucun historique disponible")
