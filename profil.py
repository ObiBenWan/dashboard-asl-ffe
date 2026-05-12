#!/usr/bin/env python3
"""
profil.py — Page profil athlete ASL-FFE (Streamlit)
Architecture identique a CareerProfile.js :
  - Combattant + badges
  - Attributs de Performance Moyens (barres avec seuils Club/Regional/National/Elite)
  - Profil de Combat Moyen (donut Gardien/Eclaireur/Conquerant/Sentinelle)
  - Toile d'Araignee (radar combattant vs profils de reference)
  - Evolution des Metriques
  - Bilan par Profil Adverse
  - Fatigue par Phase
  - Actions / Taux de Reussite
  - Cibles Visees / Touches Recues
  - Analyse Sabre
  - Fautes Commises
  - Plan Coaching IA
"""
import streamlit as st
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import re
import math
 
import math
 
def _donut_svg(data, size=160, thick=30):
    r = (size - thick) / 2
    cx = cy = size / 2
    circ = 2 * math.pi * r
    total = sum(d['value'] for d in data) or 1
    off = 0
    slices = []
    for d in data:
        pct = d['value'] / total
        dash = pct * circ
        gap  = circ - dash
        rot  = off * 360 - 90
        slices.append(dict(label=d['label'],value=d['value'],color=d['color'],
                           dash=dash,gap=gap,rot=rot,pct=round(pct*100)))
        off += pct
    dom = max(slices, key=lambda s:s['pct'])
 
    circles = ''
    for s in slices:
        circles += (
            '<circle cx="' + str(cx) + '" cy="' + str(cy) +
            '" r="' + str(round(r,1)) + '" fill="none" stroke="' + s['color'] +
            '" stroke-width="' + str(thick) +
            '" stroke-dasharray="' + str(round(s['dash'],1)) + ' ' + str(round(s['gap'],1)) +
            '" style="transform:rotate(' + str(round(s['rot'],1)) +
            'deg);transform-origin:' + str(cx) + 'px ' + str(cy) + 'px"/>'
        )
 
    legend = ''
    for d in data:
        legend += (
            '<div style="margin-bottom:7px">'
            '<div style="display:flex;justify-content:space-between;margin-bottom:2px">'
            '<div style="display:flex;align-items:center;gap:6px">'
            '<div style="width:8px;height:8px;border-radius:2px;background:' + d['color'] + '"></div>'
            '<span style="font-size:0.65rem;color:' + SLATE_HI + '">' + d['label'] + '</span></div>'
            '<span style="font-size:0.7rem;font-weight:700;color:' + d['color'] + '">' + str(d['value']) + '%</span></div>'
            '<div style="height:4px;background:' + BORDER + ';border-radius:2px">'
            '<div style="height:100%;width:' + str(d['value']) + '%;background:' + d['color'] +
            ';border-radius:2px;box-shadow:0 0 5px ' + d['color'] + '55"></div></div></div>'
        )
 
    return (
        '<div style="display:flex;align-items:center;gap:20px">'
        '<div style="position:relative;flex-shrink:0">'
        '<svg width="' + str(size) + '" height="' + str(size) + '">'
        '<circle cx="' + str(cx) + '" cy="' + str(cy) + '" r="' + str(round(r,1)) +
        '" fill="none" stroke="' + BORDER + '" stroke-width="' + str(thick) + '"/>'
        + circles +
        '<text x="' + str(cx) + '" y="' + str(cy-7) +
        '" text-anchor="middle" dominant-baseline="middle"'
        ' font-size="14" font-weight="800" fill="' + WHITE + '">' + str(dom['pct']) + '%</text>'
        '<text x="' + str(cx) + '" y="' + str(cy+9) +
        '" text-anchor="middle" dominant-baseline="middle"'
        ' font-size="8" fill="' + dom['color'] + '">' + dom['label'] + '</text>'
        '</svg></div>'
        '<div style="flex:1">' + legend + '</div>'
        '</div>'
    )
 
 
# ─────────────────────────────────────────────────────────────────────────────
# THEME identique a T dans CareerProfile.js
# ─────────────────────────────────────────────────────────────────────────────
BG       = 'hsl(222, 25%, 10%)'
SURFACE  = 'hsl(222, 20%, 14%)'
BORDER   = 'hsl(222, 20%, 22%)'
WHITE    = 'hsl(210, 20%, 95%)'
SLATE    = 'hsl(215, 20%, 55%)'
SLATE_HI = 'hsl(215, 20%, 75%)'
CYAN     = 'hsl(182, 100%, 65%)'
VERT     = 'hsl(142, 71%, 55%)'
ROUGE    = 'hsl(  4,  90%, 60%)'
WARNING  = 'hsl( 38,  92%, 60%)'
DANGER   = 'hsl(  4,  90%, 58%)'
AMBER    = 'hsl( 43,  96%, 56%)'
SUCCESS  = 'hsl(142, 71%, 55%)'
 
FORME_LABELS = {'GARDIEN':'Gardien','ECLAIREUR':'Eclaireur','CONQUERANT':'Conquerant','SENTINELLE':'Sentinelle'}
FORME_COLORS = {'GARDIEN':'#3b82f6','ECLAIREUR':'#10b981','CONQUERANT':'#ef4444','SENTINELLE':'#f59e0b'}
FORME_DESC = {
    'GARDIEN':    "Defenseur attracteur : grande reactivite, attire l'adversaire pour mieux riposter.",
    'ECLAIREUR':  "Defenseur presseur : mobilite et explosivite au service d'une defense active.",
    'CONQUERANT': "Attaquant presseur : explosivite maximale, pression constante, cherche le contact.",
    'SENTINELLE': "Attaquant attracteur : reactivite et precision, gere la distance et l'initiative.",
}
FORMES = list(FORME_LABELS.keys())
 
SEUILS_V09 = {
    'explosivite':               {'label':'Explosivite',         'unite':'/100', 'max':100,
                                  's':{'d':40,'r':60,'n':75,'e':90}},
    'reactivityScore':           {'label':'Reactivite',          'unite':'/100', 'max':100,
                                  's':{'d':45,'r':57,'n':70,'e':85}},
    'touchSuccessRate':          {'label':'Taux de reussite',    'unite':'%',    'max':100,
                                  's':{'d':20,'r':38,'n':55,'e':70}},
    'engagementRate':            {'label':'Engagement',          'unite':'%',    'max':100,
                                  's':{'d':30,'r':45,'n':60,'e':75}},
    'enduranceIndex':            {'label':'Endurance',           'unite':'%',    'max':130,
                                  's':{'d':55,'r':72,'n':90,'e':110}},
    'lateralMoves':              {'label':'Mobilite laterale',   'unite':'chgts','max':120,
                                  's':{'d':15,'r':50,'n':80,'e':100}},
    'avgWristVelocity':          {'label':'Vitesse poignet moy.','unite':'px/s', 'max':400,
                                  's':{'d':80,'r':130,'n':200,'e':300}},
    'totalDistanceTravelled_cm': {'label':'Distance parcourue',  'unite':'m',    'max':8000,
                                  's':{'d':1500,'r':3500,'n':5500,'e':7000}},
    'pressureRatio':             {'label':'Pression offensive',  'unite':'%',    'max':60,
                                  's':{'d':8,'r':15,'n':25,'e':40}},
    'tacticalEfficiency':        {'label':'Efficacite tactique', 'unite':'%',    'max':100,
                                  's':{'d':25,'r':45,'n':60,'e':75}},
}
 
PROFIL_REF = {
    'GARDIEN':    [20,25,35,20],
    'ECLAIREUR':  [30,20,20,30],
    'CONQUERANT': [15,25,25,35],
    'SENTINELLE': [25,25,30,20],
}
ATTR_LABELS = ['Mobilite','Precision','Reactivite','Explosivite']
REF_MAX = max(max(v) for v in PROFIL_REF.values())
 
def niv(key, val):
    ref = SEUILS_V09.get(key)
    if not ref or val is None: return {'l':'—','c':SLATE,'pct':0}
    s = ref['s']
    pct = min(100, val/ref['max']*100)
    if val>=s['e']: return {'l':'Elite',   'c':AMBER,     'pct':pct}
    if val>=s['n']: return {'l':'National','c':'#3b82f6',  'pct':pct}
    if val>=s['r']: return {'l':'Regional','c':VERT,       'pct':pct}
    if val>0:       return {'l':'Club',    'c':SLATE,      'pct':pct}
    return               {'l':'—',        'c':SLATE,      'pct':0}
 
 
def scorer_forme(m, arb=None):
    """Traduit exactement scorerForme de CoachShared.js"""
    if not m:
        return {'GARDIEN':25,'ECLAIREUR':25,'CONQUERANT':25,'SENTINELLE':25}
    arb_tot = ((arb.get('attaques',0) or 0) +
               (arb.get('parades',0) or 0) +
               (arb.get('ripostes',0) or 0)) if arb else 0
    if arb_tot > 0:
        att_pct = (arb.get('attaques',0) or 0) / arb_tot
        def_pct = ((arb.get('parades',0) or 0) + (arb.get('ripostes',0) or 0)) / arb_tot
    else:
        pression   = m.get('pressureRatio',0) or m.get('pressurePercentage',0) or 0
        attraction = m.get('attractionRatio',0) or m.get('attractionPercentage',0) or 0
        precision  = m.get('touchSuccessRate',0) or 0
        s_att = pression*0.50 + precision*0.30 + max(0,50-attraction)*0.20
        s_def = attraction*0.55 + (m.get('riposteRate',0) or 0)*0.30 + max(0,50-pression)*0.15
        t = (s_att+s_def) or 1
        att_pct = s_att/t; def_pct = s_def/t
    pression   = m.get('pressureRatio',0) or m.get('pressurePercentage',0) or 0
    attraction = m.get('attractionRatio',0) or m.get('attractionPercentage',0) or 0
    mobilite   = min(100,(m.get('lateralMoves',0) or 0)*2)
    engagement = m.get('engagementRate',0) or 0
    s_press = pression*0.45 + mobilite*0.30 + engagement*0.25
    s_attr  = attraction*0.60 + max(0,40-pression)*0.40
    t2 = (s_press+s_attr) or 1
    pres_pct = s_press/t2; attr_pct = s_attr/t2
    raw = {
        'GARDIEN':    def_pct*attr_pct,
        'ECLAIREUR':  def_pct*pres_pct,
        'CONQUERANT': att_pct*pres_pct,
        'SENTINELLE': att_pct*attr_pct,
    }
    tot = sum(raw.values()) or 1
    return {k:round(v/tot*100) for k,v in raw.items()}
 
def attr_vals(m):
    if not m: return [0,0,0,0]
    expl = m.get('explosivite') or m.get('explosiveness') or \
           round(min(100,(m.get('p95WristVelocity',0) or 0)/900*100))
    return [
        min(100,round((m.get('lateralMoves',0) or 0)*2)),
        min(100,round(m.get('touchSuccessRate',0) or 0)),
        min(100,round(m.get('engagementRate',0) or m.get('reactivityScore',0) or 0)),
        min(100,round(expl or 0)),
    ]
 
LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color=SLATE_HI,size=10), margin=dict(l=8,r=8,t=16,b=8),
)
 
# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');
html,body,[data-testid="stAppViewContainer"]{{
    background:{BG}!important;color:{WHITE}!important;
    font-family:'Space Grotesk',sans-serif!important;
}}
[data-testid="stHeader"],[data-testid="stToolbar"]{{display:none!important}}
h1,h2,h3{{color:{WHITE}!important}}
.stButton>button{{background:{CYAN}!important;color:{BG}!important;
    border:none!important;border-radius:6px!important;font-weight:700!important;}}
.card{{background:{SURFACE};border:1px solid {BORDER};border-radius:12px;
    padding:16px;margin-bottom:14px;}}
.sec{{font-size:0.72rem;font-weight:700;letter-spacing:0.08em;
    text-transform:uppercase;color:{SLATE_HI};margin-bottom:10px;}}
.row{{display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;}}
.seuils{{display:flex;justify-content:space-between;
    font-size:0.44rem;color:{BORDER};margin-bottom:4px;}}
</style>""", unsafe_allow_html=True)
 
# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.get('auth_success'):
    st.stop()
 
ath  = st.session_state.get('athlete_data', {})
raw  = ath.get('json_data','{}')
data = json.loads(raw) if isinstance(raw,str) else (raw or {})
hist = data.get('history',[])
nb   = len(hist)
 
def avg(key, default=0):
    vs=[h.get('metrics',{}).get(key) for h in hist if h.get('metrics',{}).get(key) is not None]
    return round(sum(vs)/len(vs),1) if vs else default
 
avgM = {k:avg(k) for k in SEUILS_V09}
avgM['p95WristVelocity'] = avg('p95WristVelocity')
avgM['explosivite'] = avgM.get('explosivite') or avg('explosiveness') or \
    round(min(100,avgM['p95WristVelocity']/900*100))
 
avals   = attr_vals(avgM)
# Calculer les forme_pct avec la vraie fonction scorerForme (CoachShared.js)
# React utilise h.arbAdv (propres actions du combattant)
all_fp = [scorer_forme(h.get('metrics') or {}, h.get('arbAdv') or {}) for h in hist]
fpcts  = {f:round(sum(fp.get(f,0) for fp in all_fp)/max(len(all_fp),1)) for f in FORMES} if all_fp else {f:0 for f in FORMES}
dominant = max(fpcts,key=fpcts.get) if any(fpcts.values()) else None
dom_color = FORME_COLORS.get(dominant,CYAN) if dominant else CYAN
 
wins   = sum(1 for h in hist if h.get('result')=='win')
losses = sum(1 for h in hist if h.get('result')=='loss')
wr     = round(wins/max(nb,1)*100,1)
name   = st.session_state.get('athlete_name','')
tC = data.get('touches_C',0); tB=data.get('touches_B',0); tA=data.get('touches_A',0)
scored   = data.get('total_touches_scored',0)
received = data.get('total_touches_received',0)
sanctions_total = (data.get('actions_breakdown') or {}).get('Sanctions',0)
 
# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
ch1,ch2 = st.columns([4,1])
with ch1:
    badges = ''.join([
        f'<span style="padding:3px 10px;border-radius:6px;font-size:0.65rem;font-weight:700;'
        f'background:{c}18;border:1px solid {c}44;color:{c};margin:2px">{l} : {v}</span>'
        for l,v,c in [
            ('Combats', f"{nb} analyse{'s' if nb>1 else ''}", CYAN),
            ('Profil', FORME_LABELS.get(dominant,'—'), dom_color),
            ('Win Rate', f"{wr}%", VERT if wr>=50 else WARNING),
        ]
    ])
    desc = f'<p style="font-size:0.68rem;color:{SLATE_HI};max-width:500px;margin-top:6px">{FORME_DESC[dominant]}</p>' if dominant else ''
    st.markdown(f"""
        <div style="padding:14px 0">
        <h1 style="color:{CYAN};font-size:2.2rem;margin:0;letter-spacing:0.04em">{name.upper()}</h1>
        <p style="color:{SLATE};font-size:0.88rem;margin:4px 0 8px">
            {ath.get('club','ASL-FFE')} &bull; {ath.get('category','N/A')}</p>
        <div>{badges}</div>{desc}
        </div>
    """, unsafe_allow_html=True)
with ch2:
    if st.button("Deconnexion"):
        st.session_state.auth_success = False
        st.session_state.athlete_data = None
        st.rerun()
 
st.markdown(f'<hr style="border-color:{BORDER};margin:0 0 14px">',unsafe_allow_html=True)
 
if nb==0:
    st.info("Aucun combat analyse. Effectuez une session et sauvegardez le profil.")
    st.stop()
 
# ─────────────────────────────────────────────────────────────────────────────
# COL GAUCHE : Attributs  |  COL DROITE : Donut + Radar
# ─────────────────────────────────────────────────────────────────────────────
col_l, col_r = st.columns(2)
 
with col_l:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="sec">Attributs de Performance Moyens</div>', unsafe_allow_html=True)
    for key, ref in SEUILS_V09.items():
        val = avgM.get(key,0) or 0
        n = niv(key,val)
        disp = f"{round(val/100)} m" if key=='totalDistanceTravelled_cm' else f"{round(val)} {ref['unite']}"
        pct  = n['pct']
        s    = ref['s']
        mx   = ref['max']
        markers = ''.join([
            f'<div style="position:absolute;top:-2px;left:{min(100,sv/mx*100):.1f}%;'
            f'width:1px;height:10px;background:{col};opacity:0.6"></div>'
            for sv,col in [(s['d'],SLATE),(s['r'],VERT),(s['n'],'#3b82f6'),(s['e'],AMBER)]
        ])
        st.markdown(f"""
        <div class="row">
            <span style="font-size:0.64rem;color:{SLATE_HI};font-weight:600">{ref['label']}</span>
            <div>
                <span style="font-size:0.61rem;font-weight:700;color:{n['c']}">{n['l']}</span>
                &nbsp;<span style="font-size:0.6rem;color:{SLATE}">{disp}</span>
            </div>
        </div>
        <div style="height:6px;background:{BORDER};border-radius:3px;position:relative;margin:3px 0">
            <div style="height:6px;width:{min(100,pct):.1f}%;background:{n['c']};border-radius:3px"></div>
            {markers}
        </div>
        <div class="seuils"><span>Club</span><span>Regional</span><span>National</span><span>Elite</span></div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
 
with col_r:
    # Donut profil
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="sec">Profil de Combat Moyen — Gardien / Eclaireur / Conquerant / Sentinelle</div>',
                unsafe_allow_html=True)
    fs = sorted(FORMES, key=lambda f:-fpcts[f])
    fig_d = go.Figure(go.Pie(
        labels=[FORME_LABELS[f] for f in fs],
        values=[fpcts[f] for f in fs],
        hole=0.55,
        marker=dict(colors=[FORME_COLORS[f] for f in fs],line=dict(color=BG,width=2)),
        textinfo='label+percent',textfont=dict(size=10,color=WHITE),
    ))
    fig_d.update_layout(**LAYOUT, height=200, showlegend=False)
    st.plotly_chart(fig_d, use_container_width=True, config={'displayModeBar':False})
 
    # Toile d'Araignee
    st.markdown('<div class="sec" style="margin-top:6px">Toile d\'Araignee — Combattant vs Profils de Reference</div>',
                unsafe_allow_html=True)
    fig_r = go.Figure()
    for f in FORMES:
        rv = [round(v/REF_MAX*100) for v in PROFIL_REF[f]]
        fig_r.add_trace(go.Scatterpolar(
            r=rv+[rv[0]], theta=ATTR_LABELS+[ATTR_LABELS[0]],
            mode='lines', name=FORME_LABELS[f],
            line=dict(color=FORME_COLORS[f],width=1.5,dash='dot'),opacity=0.65,
        ))
    fig_r.add_trace(go.Scatterpolar(
        r=avals+[avals[0]], theta=ATTR_LABELS+[ATTR_LABELS[0]],
        fill='toself', mode='lines+markers',
        name=name or 'Combattant',
        line=dict(color=dom_color,width=2.5),
        fillcolor='rgba(14,165,233,0.12)',  # cyan semi-transparent
        marker=dict(size=5),
    ))
    fig_r.update_layout(**LAYOUT, height=230,
        polar=dict(
            radialaxis=dict(visible=True,range=[0,100],gridcolor=BORDER,
                           tickfont=dict(size=7,color=SLATE)),
            angularaxis=dict(tickfont=dict(size=9,color=SLATE_HI)),
            bgcolor='rgba(0,0,0,0)',
        ),
        legend=dict(bgcolor='rgba(0,0,0,0)',font=dict(color=SLATE_HI,size=9)),
        showlegend=True,
    )
    st.plotly_chart(fig_r, use_container_width=True, config={'displayModeBar':False})
    st.markdown('</div>', unsafe_allow_html=True)
 
# ─────────────────────────────────────────────────────────────────────────────
# EVOLUTION METRIQUES
# ─────────────────────────────────────────────────────────────────────────────
if nb > 1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="sec">Evolution des Metriques sur plusieurs combats</div>', unsafe_allow_html=True)
    xl = [h.get('date','')[:10] or f"C{i+1}" for i,h in enumerate(hist)]
    series = [
        ('touchSuccessRate','Taux reussite %','#22c55e'),
        ('pressureRatio',   'Pression %',    '#ec4899'),
        ('explosivite',     'Explosivite',   AMBER),
        ('engagementRate',  'Engagement %',  CYAN),
    ]
    fig_ev = go.Figure()
    for k,lbl,col in series:
        ys=[h.get('metrics',{}).get(k,0) or 0 for h in hist]
        if any(v>0 for v in ys):
            fig_ev.add_trace(go.Scatter(x=xl,y=ys,mode='lines+markers',name=lbl,
                line=dict(color=col,width=2),marker=dict(size=5)))
    fig_ev.update_layout(**LAYOUT, height=190,
        xaxis=dict(gridcolor=BORDER),yaxis=dict(gridcolor=BORDER),
        hovermode='x unified',
        legend=dict(bgcolor='rgba(0,0,0,0)',font=dict(color=SLATE_HI,size=9)))
    st.plotly_chart(fig_ev, use_container_width=True, config={'displayModeBar':False})
    st.markdown('</div>', unsafe_allow_html=True)
 
# ─────────────────────────────────────────────────────────────────────────────
# BILAN PROFIL ADVERSE + FATIGUE
# ─────────────────────────────────────────────────────────────────────────────
cb1, cb2 = st.columns(2)
 
with cb1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="sec">Bilan par Profil Adverse</div>', unsafe_allow_html=True)
    matchup={}
    for h in hist:
        opp=(h.get('profil_adverse') or '?').upper()
        if opp not in matchup: matchup[opp]={'V':0,'D':0,'n':0}
        matchup[opp]['n']+=1
        if h.get('result')=='win':  matchup[opp]['V']+=1
        if h.get('result')=='loss': matchup[opp]['D']+=1
    if matchup:
        rows=[{'Profil':FORME_LABELS.get(k,k),'N':v['n'],'V':v['V'],'D':v['D'],
               'Win%':f"{round(v['V']/max(v['n'],1)*100)}%"} for k,v in matchup.items()]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Donnees adversaire non disponibles")
    st.markdown('</div>', unsafe_allow_html=True)
 
with cb2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="sec">Fatigue par Phase de Combat</div>', unsafe_allow_html=True)
    end_vals=[h.get('metrics',{}).get('enduranceFactor',
              h.get('metrics',{}).get('enduranceIndex',0)) or 0 for h in hist]
    avg_end=round(sum(end_vals)/max(len(end_vals),1))
    end_col=VERT if avg_end>=85 else WARNING if avg_end>=70 else DANGER
    msg=('Excellent maintien' if avg_end>=90 else
         'Legere baisse en fin de combat' if avg_end>=70 else
         'Fatigue marquee — conditionnement recommande')
    ca,cb_=st.columns(2)
    with ca:
        st.metric("Endurance moy.",f"{avg_end}%")
        st.markdown(f'<p style="font-size:0.63rem;color:{end_col}">{msg}</p>',unsafe_allow_html=True)
    with cb_:
        fig_g=go.Figure(go.Indicator(mode="gauge+number",value=min(100,avg_end),
            gauge=dict(axis=dict(range=[0,100]),bar=dict(color=end_col),bgcolor='rgba(30,40,60,1)'),
            number=dict(font=dict(color=end_col,size=26))))
        fig_g.update_layout(**LAYOUT,height=130)
        st.plotly_chart(fig_g,use_container_width=True,config={'displayModeBar':False})
    st.markdown('</div>', unsafe_allow_html=True)
 
 
# Initiative + Reaction pression (donuts)
ci1, ci2 = st.columns(2)
 
with ci1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="sec">Gestion de l''Initiative (Moyenne)</div>', unsafe_allow_html=True)
    pression_pct   = round(avgM.get('pressureRatio',0) or avgM.get('pressurePercentage',0) or 0)
    attraction_pct = round(avgM.get('attractionRatio',0) or avgM.get('attractionPercentage',0) or 0)
    neutral_pct    = max(0, 100 - pression_pct - attraction_pct)
    init_data = [
        {'label':'Pression',   'value':pression_pct,   'color':ROUGE},
        {'label':'Neutre',     'value':neutral_pct,     'color':SLATE},
        {'label':'Attraction', 'value':attraction_pct,  'color':'#a855f7'},
    ]
    if any(d['value']>0 for d in init_data):
        st.markdown(_donut_svg(init_data, 160, 30), unsafe_allow_html=True)
    else:
        st.info("Donnees insuffisantes")
    st.markdown('</div>', unsafe_allow_html=True)
 
with ci2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="sec">Reaction a la Pression (Endurance)</div>', unsafe_allow_html=True)
    end_v = min(100, round(avgM.get('enduranceIndex',0) or avgM.get('enduranceFactor',0) or 0))
    fat_v = max(0, 100 - end_v)
    press_data = [
        {'label':'Endurance', 'value':end_v, 'color':VERT},
        {'label':'Fatigue',   'value':fat_v, 'color':'#7f1d1d'},
    ]
    if any(d['value']>0 for d in press_data):
        st.markdown(_donut_svg(press_data, 160, 30), unsafe_allow_html=True)
        ec = SUCCESS if end_v>=85 else WARNING
        msg2 = ('Excellent maintien' if end_v>=90
                else 'Legere baisse en fin de combat' if end_v>=70
                else 'Chute significative — priorite endurance specifique')
        st.markdown('<div style="margin-top:8px;padding:8px 12px;border-radius:7px;'
                    'background:' + SURFACE + ';font-size:0.63rem;color:' + ec + '">'
                    + msg2 + '</div>', unsafe_allow_html=True)
    else:
        st.info("Donnees insuffisantes")
    st.markdown('</div>', unsafe_allow_html=True)
 
# ─────────────────────────────────────────────────────────────────────────────
# ACTIONS + TAUX DE REUSSITE
# ─────────────────────────────────────────────────────────────────────────────
ca1, ca2 = st.columns(2)
 
with ca1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="sec">Evolution des Actions (%) — Attaques vs Defense</div>', unsafe_allow_html=True)
    if nb>1:
        xl=[h.get('date','')[:10] or f"C{i+1}" for i,h in enumerate(hist)]
        att_p,def_p=[],[]
        for h in hist:
            arb=h.get('arbitrage',{}) or {}
            tot=max((arb.get('attaques',0) or 0)+(arb.get('parades',0) or 0)+
                    (arb.get('ripostes',0) or 0),1)
            att_p.append(round((arb.get('attaques',0) or 0)/tot*100))
            def_p.append(round(((arb.get('parades',0) or 0)+(arb.get('ripostes',0) or 0))/tot*100))
        fig_ac=go.Figure()
        fig_ac.add_trace(go.Scatter(x=xl,y=att_p,mode='lines+markers',name='Attaques %',
            line=dict(color=ROUGE,width=2),marker=dict(size=5)))
        fig_ac.add_trace(go.Scatter(x=xl,y=def_p,mode='lines+markers',name='Defense %',
            line=dict(color=CYAN,width=2),marker=dict(size=5)))
        fig_ac.update_layout(**LAYOUT,height=170,
            xaxis=dict(gridcolor=BORDER),yaxis=dict(gridcolor=BORDER),hovermode='x unified',
            legend=dict(bgcolor='rgba(0,0,0,0)',font=dict(color=SLATE_HI,size=9)))
        st.plotly_chart(fig_ac,use_container_width=True,config={'displayModeBar':False})
    else:
        st.info("Plusieurs combats necessaires")
    st.markdown('</div>', unsafe_allow_html=True)
 
with ca2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="sec">Taux de Reussite des Actions</div>', unsafe_allow_html=True)
    arb=(data.get('actions_breakdown') or {})
    att=arb.get('Attaques',0) or 0
    par=arb.get('Parades',0)  or 0
    rip=arb.get('Ripostes',0) or 0
    rows=[
        {'Action':'Attaques','Nb':att,'Taux':f"{round(scored/max(att,1)*100)}%" if att else '—'},
        {'Action':'Parades', 'Nb':par,'Taux':f"{round((par)/max(par+received,1)*100)}%" if par else '—'},
        {'Action':'Ripostes','Nb':rip,'Taux':f"{round(scored/max(rip,1)*100)}%" if rip else '—'},
    ]
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)
 
# ─────────────────────────────────────────────────────────────────────────────
# CIBLES VISEES + TOUCHES RECUES
# ─────────────────────────────────────────────────────────────────────────────
cz1, cz2 = st.columns(2)
 
with cz1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="sec">Cibles Visees — Touches marquees (moy/combat)</div>', unsafe_allow_html=True)
    zl=['Zone C — Tete/Torse (+5pts)','Zone B — Bras/Jambe (+3pts)','Zone A — Main/Arme (+1pt)']
    zv=[round(tC/max(nb,1),1),round(tB/max(nb,1),1),round(tA/max(nb,1),1)]
    fig_cv=go.Figure(go.Bar(y=zl,x=zv,orientation='h',
        marker=dict(color=[ROUGE,AMBER,VERT]),
        text=[str(v) for v in zv],textposition='outside',
        textfont=dict(color=WHITE)))
    fig_cv.update_layout(**LAYOUT,height=170,
        xaxis=dict(gridcolor=BORDER),yaxis=dict(autorange='reversed'))
    st.plotly_chart(fig_cv,use_container_width=True,config={'displayModeBar':False})
    st.markdown('</div>', unsafe_allow_html=True)
 
with cz2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="sec" style="color:{DANGER}">Touches Recues (Moyenne / combat)</div>',
                unsafe_allow_html=True)
    rC=sum(h.get('touchesRecues',{}).get('touches_C',0) or 0 for h in hist)
    rB=sum(h.get('touchesRecues',{}).get('touches_B',0) or 0 for h in hist)
    rA=sum(h.get('touchesRecues',{}).get('touches_A',0) or 0 for h in hist)
    zrl=['Zone C (+5pts)','Zone B (+3pts)','Zone A (+1pt)']
    zrv=[round(rC/max(nb,1),1),round(rB/max(nb,1),1),round(rA/max(nb,1),1)]
    fig_cr=go.Figure(go.Bar(y=zrl,x=zrv,orientation='h',
        marker=dict(color=[DANGER,WARNING,SLATE]),
        text=[str(v) for v in zrv],textposition='outside',
        textfont=dict(color=WHITE)))
    fig_cr.update_layout(**LAYOUT,height=170,
        xaxis=dict(gridcolor=BORDER),yaxis=dict(autorange='reversed'))
    st.plotly_chart(fig_cr,use_container_width=True,config={'displayModeBar':False})
    st.markdown('</div>', unsafe_allow_html=True)
 
# ─────────────────────────────────────────────────────────────────────────────
# ANALYSE SABRE
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown(f'<div class="sec" style="color:{AMBER}">Analyse Sabre — Donnees v10</div>', unsafe_allow_html=True)
sb=[h.get('sabre',{}) or {} for h in hist]
det=round(sum(s.get('detected_pct',0) or 0 for s in sb)/max(len(sb),1))
ang=round(sum(s.get('avg_angle',0) or 0 for s in sb)/max(len(sb),1))
zdm_set=[s.get('zone_dom') for s in sb if s.get('zone_dom')]
zdm=max(set(zdm_set),key=lambda z:zdm_set.count(z)) if zdm_set else '—'
trt=sum(s.get('tranchant',0) or 0 for s in sb)
cs1,cs2,cs3,cs4=st.columns(4)
with cs1: st.metric("Detection %",f"{det}%")
with cs2: st.metric("Angle moyen",f"{ang} deg")
with cs3: st.metric("Zone dominante",zdm)
with cs4: st.metric("Contacts tranchant",trt)
st.markdown('</div>', unsafe_allow_html=True)
 
# ─────────────────────────────────────────────────────────────────────────────
# FAUTES COMMISES
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown(f'<div class="sec" style="color:{WARNING}">Fautes Commises (Total cumule)</div>', unsafe_allow_html=True)
spm=round(sanctions_total/max(nb,1),2)
scol=VERT if spm<0.5 else WARNING if spm<1.5 else DANGER
sniv="Bon" if spm<0.5 else "Attention" if spm<1.5 else "A ameliorer"
cf1,cf2,cf3=st.columns(3)
with cf1: st.metric("Total sanctions",sanctions_total)
with cf2: st.metric("Moy / combat",spm)
with cf3:
    st.markdown(f'<div style="padding:10px;background:{scol}18;border:1px solid {scol}44;'
                f'border-radius:8px;margin-top:8px">'
                f'<span style="color:{scol};font-weight:700">{sniv}</span></div>',
                unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
 
# ─────────────────────────────────────────────────────────────────────────────
# PLAN COACHING IA
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown(f'<div class="sec" style="color:{VERT}">Plan Coaching — Analyse IA</div>', unsafe_allow_html=True)
 
engine = st.radio("Moteur IA",["Claude API (~0.01€/appel)","Ollama local (gratuit)"],
                  horizontal=True, label_visibility="collapsed")
if engine=="Ollama local (gratuit)":
    ol_model = st.selectbox("Modele Ollama",["llama3.2","mistral","qwen2.5"])
 
if st.button("Generer le plan coaching IA", type="primary"):
    summary = (
        f"Combattant: {name} | Combats: {nb} | Win Rate: {wr}%\n"
        f"Profil dominant: {FORME_LABELS.get(dominant,'—')}\n"
        f"Explosivite: {round(avgM.get('explosivite',0))}/100 | "
        f"Taux reussite: {round(avgM.get('touchSuccessRate',0))}% | "
        f"Endurance: {round(avgM.get('enduranceIndex',0))}%\n"
        f"Pression: {round(avgM.get('pressureRatio',0))}% | "
        f"Touches: {scored} marquees / {received} recues\n"
        f"Zones: C={tC} B={tB} A={tA} | Sanctions: {sanctions_total}"
    )
    prompt = (
        f"Tu es coach expert ASL-FFE sabre laser.\nProfil:\n{summary}\n\n"
        f"Genere un plan coaching en JSON strict (sans markdown) :\n"
        f"{{\"points_forts\":[str,str,str],"
        f"\"axes_progression\":[str,str,str],"
        f"\"objectif_prochain_combat\":str,"
        f"\"conseil_tactique\":str}}"
    )
    with st.spinner("Analyse IA en cours..."):
        try:
            import requests
            if "Claude" in engine:
                r=requests.post("https://api.anthropic.com/v1/messages",
                    headers={"Content-Type":"application/json"},
                    json={"model":"claude-sonnet-4-20250514","max_tokens":600,
                          "messages":[{"role":"user","content":prompt}]},
                    timeout=30)
                txt=r.json()['content'][0]['text']
            else:
                r=requests.post("http://localhost:11434/api/generate",
                    json={"model":ol_model,"prompt":prompt,"stream":False},timeout=60)
                txt=r.json().get('response','{}')
 
            m=re.search(r'\{.*\}',txt,re.DOTALL)
            if m:
                c=json.loads(m.group())
                st.markdown(f"""
                    <div style="background:{SURFACE};border:1px solid {VERT}44;
                    border-radius:10px;padding:14px;margin:8px 0">
                    <p style="color:{SLATE_HI};font-size:0.78rem">
                        <b style="color:{VERT}">Objectif :</b> {c.get('objectif_prochain_combat','—')}</p>
                    <p style="color:{SLATE_HI};font-size:0.78rem;margin-top:6px">
                        <b style="color:{VERT}">Conseil :</b> {c.get('conseil_tactique','—')}</p>
                    </div>
                """,unsafe_allow_html=True)
                cc1,cc2=st.columns(2)
                with cc1:
                    st.markdown("**Points forts**")
                    for p in c.get('points_forts',[]): st.markdown(f"✅ {p}")
                with cc2:
                    st.markdown("**Axes de progression**")
                    for a in c.get('axes_progression',[]): st.markdown(f"🎯 {a}")
            else:
                st.text(txt)
        except Exception as e:
            st.error(f"Erreur IA : {e}")
 
st.markdown('</div>', unsafe_allow_html=True)
