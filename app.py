import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import pandas as pd

# 1. Configuration de la page (on cache le menu latéral au début)
st.set_page_config(page_title="ASL-FFE - Profil Combattant", layout="centered", initial_sidebar_state="collapsed")

# 2. Initialisation Firebase
if not firebase_admin._apps:
    try:
        fb_credentials = dict(st.secrets["firebase"])
        fb_credentials["private_key"] = fb_credentials["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(fb_credentials)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Erreur système : {e}")

db = firestore.client()

# --- GESTION DE LA CONNEXION ---
if 'auth_success' not in st.session_state:
    st.session_state.auth_success = False

# --- PAGE D'ACCÈS (STYLE CLONE DE TON ANCIEN PROJET) ---
if not st.session_state.auth_success:
    # Centrage vertical artificiel
    st.write("##")
    
    # Affichage du Logo (si tu as une URL pour ton logo, remplace ici)
    # st.image("logo.png", width=150) 
    
    st.title("🛡️ PROFIL COMBATTANT")
    st.subheader("Accès Profil Combattant")

    # Formulaire de connexion
    with st.container():
        prenom = st.text_input("Prénom")
        code_acces = st.text_input("Code d'accès", type="password")
        
        if st.button("Accéder au Profil", use_container_width=True):
            if prenom and code_acces:
                # On cherche le document avec le code_acces (en minuscules)
                doc_ref = db.collection("athletes").document(code_acces.lower())
                doc = doc_ref.get()

                if doc.exists:
                    st.session_state.auth_success = True
                    st.session_state.prenom_utilisateur = prenom
                    st.session_state.code_valide = code_acces.lower()
                    st.rerun() # On recharge pour afficher le profil
                else:
                    st.error("Code d'accès incorrect.")
            else:
                st.warning("Veuillez remplir les deux champs.")

# --- PAGE PROFIL (S'AFFICHE APRÈS CONNEXION) ---
else:
    # Bouton de déconnexion en haut à droite
    col_title, col_logout = st.columns([0.85, 0.15])
    with col_logout:
        if st.button("Quitter"):
            st.session_state.auth_success = False
            st.rerun()

    # Récupération des données
    doc_ref = db.collection("athletes").document(st.session_state.code_valide)
    doc = doc_ref.get()
    doc_dict = doc.to_dict()
    data = json.loads(doc_dict["json_data"])
    
    # On prend le dernier match
    match = data['history'][0]
    metrics = match['metrics']

    st.title(f"Bonjour, {st.session_state.prenom_utilisateur} 👋")
    st.header(f"Analyse de ton combat contre {match['opponent']['name']}")

    # --- TES GRAPHIQUES ET STATS ---
    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("Résultat", match['result'].upper())
    col2.metric("Ton Score", match['myScore'])
    col3.metric("Explosivité", f"{metrics['explosivite']}%")

    st.subheader("📈 Intensité des échanges")
    df_exchanges = pd.DataFrame(match['exchanges'])
    st.line_chart(df_exchanges.set_index('exchange_num')['avg_wrist_v'])
    
    # ... Tu peux rajouter ici le reste de tes analyses ...
