import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import tempfile
import pandas as pd

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="ASL-FFE - Profil Combattant", layout="wide", initial_sidebar_state="collapsed")

# 2. INJECTION DU DESIGN (Variables HSL)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');
    
    .stApp {
        background-color: hsl(180, 25%, 15%);
        font-family: 'Space Grotesk', sans-serif;
    }

    header {visibility: hidden;}
    footer {visibility: hidden;}

    .login-title {
        color: hsl(210, 20%, 95%);
        font-size: 1.8rem;
        font-weight: 700;
        text-align: center;
        margin-top: 10px;
        margin-bottom: 30px;
        letter-spacing: -0.025em;
    }

    .stTextInput label {
        color: hsl(180, 10%, 60%) !important;
    }
    
    .stTextInput input {
        background-color: hsl(180, 25%, 25%) !important;
        border: 1px solid hsl(180, 25%, 25%) !important;
        color: white !important;
        border-radius: 0.5rem !important;
    }

    .stButton > button {
        background-color: hsl(182, 100%, 74%) !important;
        color: hsl(180, 25%, 10%) !important;
        font-weight: 700 !important;
        width: 100% !important;
        height: 3.5rem !important;
        border: none !important;
        border-radius: 0.5rem !important;
        margin-top: 20px;
    }
    
    /* Conteneur Card centré */
    [data-testid="stVerticalBlock"] > div:has(div.card-container) {
        background-color: hsl(180, 25%, 20%);
        border: 1px solid hsl(180, 25%, 25%);
        border-radius: 0.75rem;
        padding: 40px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }
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

# --- LOGIQUE DE CONNEXION ---
if not st.session_state.auth_success:
    _, col_center, _ = st.columns([1, 2.5, 1])

    with col_center:
        st.markdown('<div class="card-container"></div>', unsafe_allow_html=True)
        st.image("https://studio-7691886667-ec4b3.web.app/logo.png", width=200)
        st.markdown('<h1 class="login-title">PROFIL COMBATTANT</h1>', unsafe_allow_html=True)
        
        prenom = st.text_input("Prénom")
        code_acces = st.text_input("Code d'accès", type="password")

        if st.button("ACCÉDER AU PROFIL"):
            if prenom and code_acces:
                # On cherche le document dont l'ID est le code d'accès
                doc_ref = db.collection("athletes").document(code_acces.lower())
                doc = doc_ref.get()
                
                if doc.exists:
                    try:
                        raw_data = doc.to_dict().get("json_data")
                        st.session_state.athlete_data = json.loads(raw_data)
                        st.session_state.auth_success = True
                        st.session_state.prenom_utilisateur = prenom
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur de données : {e}")
                else:
                    st.error("❌ Code d'accès incorrect.")
            else:
                st.warning("⚠️ Veuillez remplir tous les champs.")

# --- PAGE PROFIL ---
else:
    athlete_data = st.session_state.athlete_data
    # On récupère le dernier match de l'historique
    match = athlete_data['history'][0]
    metrics = match['metrics']

    st.title(f"Bienvenue, {st.session_state.prenom_utilisateur} 👋")
    st.markdown(f"### Analyse du match contre {match['opponent']['name']}")
    st.divider()
    
    # Métriques principales
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Résultat", match['result'].upper(), f"{match['myScore']} - {match['oppScore']}")
    c2.metric("Explosivité", f"{metrics['explosivite']}%")
    c3.metric("Réactivité", f"{metrics['reactivityScore']}/100")
    c4.metric("Tactique", f"{metrics['tacticalEfficiency']}%")
    
    st.divider()
    
    # Graphique de vitesse
    st.subheader("📈 Vitesse du poignet durant les échanges")
    df_exchanges = pd.DataFrame(match['exchanges'])
    st.line_chart(df_exchanges.set_index('exchange_num')['avg_wrist_v'])
    
    if st.button("Déconnexion"):
        st.session_state.auth_success = False
        st.rerun()
