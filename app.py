# === app.py ===
import streamlit as st
from blocchi import genera_blocchi
from completamento import completa_blocchi
from mappa import genera_mappa
import os
import pandas as pd
from ui import interfaccia, interfaccia_pdf

# === PULIZIA FILE FILTRATI ALL'AVVIO ===
FILES_TEMPORANEI = [
    "aziende_filtrate_correttamente.csv",
    "aziende_geocodificate_filtrate.csv",
    "matrice_durate_filtrata.json",
    "blocchi_senza_ritorno.csv",
    "blocco_completo.csv",
    "blocchi_multi_foglio.xlsx",
    "mappa_blocchi_senza_ritorno.html"
]

if not st.session_state.get("gia_pulito", False):
    for file in FILES_TEMPORANEI:
        if os.path.exists(file):
            os.remove(file)
    st.session_state["gia_pulito"] = True




sezione = st.sidebar.selectbox(
    "Seleziona una sezione",
    ["Blocchi Visite Aziendali", "Estrazione PDF Appalti"],
    index=0 if st.session_state.get("sezione_attiva") == "Blocchi Visite Aziendali" else 1
)

if sezione == "Blocchi Visite Aziendali":
    csv_path, json_path, tempo_visita, tempo_massimo = interfaccia()

    if csv_path and json_path and tempo_visita and tempo_massimo:
        if st.button("Genera blocchi"):
            df_blocchi = genera_blocchi(csv_path, json_path, tempo_visita, tempo_massimo)
            df_blocchi = completa_blocchi(df_blocchi, csv_path)
            html_path = genera_mappa(df_blocchi, csv_path)

            st.success("✅ Tutti i file generati con successo")
           
            with open("blocchi_multi_foglio.xlsx", "rb") as f:
                st.download_button("Scarica Excel multi-foglio", f, file_name="blocchi_multi_foglio.xlsx")

            with open(html_path, "rb") as f:
                st.download_button("Scarica mappa HTML", f, file_name="mappa_blocchi_senza_ritorno.html")

elif sezione == "Estrazione PDF Appalti":
    interfaccia_pdf()
