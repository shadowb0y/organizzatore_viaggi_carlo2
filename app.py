# === app.py ===
import streamlit as st
st.set_page_config(layout="wide")  # Deve essere subito dopo l'import

from blocchi import genera_blocchi
from completamento import completa_blocchi
from mappa import genera_mappa
from ui import interfaccia, interfaccia_pdf, interfaccia_id_gia_visitati, interfaccia_filtro_nomi

import os
import pandas as pd

os.makedirs("output", exist_ok=True)

# === PULIZIA FILE TEMPORANEI ALL'AVVIO ===
FILES_TEMPORANEI = [
    "output/aziende_filtrate_correttamente.csv",
    "output/aziende_geocodificate_filtrate.csv",
    "output/matrice_durate_filtrata.json",
    "output/blocchi_senza_ritorno.csv",
    "output/blocco_completo.csv",
    "output/blocchi_multi_foglio.xlsx",
    "output/mappa_blocchi_senza_ritorno.html"
]

if not st.session_state.get("gia_pulito", False):
    for file in FILES_TEMPORANEI:
        if os.path.exists(file):
            os.remove(file)
    st.session_state["gia_pulito"] = True

# === INTERFACCIA PRINCIPALE ===
sezione = st.sidebar.selectbox(
    "Seleziona una sezione",
    [
        "Blocchi Visite Aziendali",
        "Estrazione PDF Appalti",
        "📌 ID già visitati",
        "🚫 Nomi da filtrare"
    ],
    index=0 if st.session_state.get("sezione_attiva") == "Blocchi Visite Aziendali" else 1
)

# === SEZIONE BLOCCHI VISITE AZIENDALI ===
if sezione == "Blocchi Visite Aziendali":
    csv_path, json_path, tempo_visita, tempo_massimo = interfaccia()

    if csv_path and json_path and tempo_visita and tempo_massimo:
        if st.button("Genera blocchi"):
            df_blocchi = genera_blocchi(csv_path, json_path, tempo_visita, tempo_massimo)
            df_blocchi = completa_blocchi(df_blocchi, csv_path)
            html_path = genera_mappa(df_blocchi, csv_path)

            st.success("✅ Tutti i file generati con successo")

            with open("output/blocchi_multi_foglio.xlsx", "rb") as f:
                st.download_button("Scarica Excel multi-foglio", f, file_name="output/blocchi_multi_foglio.xlsx")

            with open(html_path, "rb") as f:
                st.download_button("Scarica mappa HTML", f, file_name="output/mappa_blocchi_senza_ritorno.html")

# === SEZIONE ESTRAZIONE PDF APPALTI ===
elif sezione == "Estrazione PDF Appalti":
    interfaccia_pdf()

# === SOTTOSEZIONE: ID GIÀ VISITATI ===
elif sezione == "📌 ID già visitati":
    interfaccia_id_gia_visitati()

# === SOTTOSEZIONE: NOMI DA FILTRARE ===
elif sezione == "🚫 Nomi da filtrare":
    interfaccia_filtro_nomi()
