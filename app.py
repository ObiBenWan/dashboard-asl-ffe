import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import pandas as pd

# 1. Configuration de la page
st.set_page_config(page_title="Dashboard ASL-FFE", layout="wide")

# 2. Initialisation sécurisée de Firebase
if not firebase_admin._apps:
    try:
        # Transformation des secrets TOML en dictionnaire
        fb_credentials = dict(st.secrets["firebase"])
        # Correction des sauts de ligne pour la clé privée
        fb_credentials["private_key"] = fb_credentials["private_key"].replace("\\n", "\n")
        
        cred = credentials.Certificate(fb_credentials)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Erreur de connexion Firebase : {e}")

db = firestore.client()

# 3. Interface d'accueil
st.title("🛡️ Espace Athlète - ASL-FFE")
st.write("Consultez vos statistiques de match et analyses de performance.")

# 4. Formulaire d'accès
with st.sidebar:
    st.image("https://via.placeholder.com/150", caption="ASL-FFE Tracking") # Tu pourras mettre ton logo ici
    code_acces = st.text_input("Code personnel :", type="password")

if code_acces:
    # On cherche le document correspondant au code (en minuscules)
    doc_ref = db.collection("athletes").document(code_acces.lower())
    doc = doc_ref.get()

    if doc.exists:
        # Récupération de la chaîne JSON
        doc_dict = doc.to_dict()
        
        try:
            # Conversion du texte brut en dictionnaire Python
            data = json.loads(doc_dict["json_data"])
            
            # Extraction des données du dernier match
            match = data['history'][0]
            metrics = match['metrics']
            
            st.success(f"Bienvenue {data['name']} ! Voici vos analyses pour le match contre {match['opponent']['name']}.")

            # --- SECTION 1 : RÉSUMÉ ---
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Résultat", match['result'].upper())
            col2.metric("Score", f"{match['myScore']} - {match['oppScore']}")
            col3.metric("Explosivité", f"{metrics['explosivite']}%")
            col4.metric("Réactivité", f"{metrics['reactivityScore']}/100")

            # --- SECTION 2 : GRAPHIQUES ---
            st.divider()
            st.subheader("📈 Analyse de l'intensité des échanges")
            
            # Préparation des données pour le graphique
            df_exchanges = pd.DataFrame(match['exchanges'])
            
            # Graphique de la vitesse moyenne du poignet par échange
            st.line_chart(df_exchanges.set_index('exchange_num')['avg_wrist_v'])
            
            # --- SECTION 3 : DÉTAILS ---
            st.divider()
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("🎯 Précision des touches")
                st.write(f"**Taux de succès :** {metrics['touchSuccessRate']}%")
                st.write(f"**Zone dominante :** {match['saber']['zone_dom']}")
                st.write(f"**Distance totale :** {metrics['totalDistanceTravelled_cm'] / 100:.2f} m")

            with c2:
                st.subheader("🤺 Arbitrage & Tactique")
                st.write(f"**Attaques :** {match['arbitrage']['attaques']}")
                st.write(f"**Parades :** {match['arbitrage']['parades']}")
                st.write(f"**Efficacité tactique :** {metrics['tacticalEfficiency']}%")

        except Exception as e:
            st.error(f"Erreur lors de la lecture des données : {e}")
            
    else:
        st.error("Code d'accès invalide. Veuillez contacter votre entraîneur.")
else:
    st.info("Veuillez entrer votre code dans la barre latérale pour accéder à vos données.")
