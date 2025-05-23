# === app.py ===
import streamlit as st
st.set_page_config(layout="wide")

from blocchi import genera_blocchi
from completamento import completa_blocchi
from mappa import genera_mappa
from ui import interfaccia, interfaccia_pdf, interfaccia_id_gia_visitati, interfaccia_filtro_nomi

import os
import pandas as pd
from datetime import datetime

os.makedirs("output", exist_ok=True)
os.makedirs("cronologia", exist_ok=True)  # ✅ nuova cartella per salvataggi singoli

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

# === SEZIONI ===

# === Lista voci
voci = [
    "🖥️ Parsing PDF",
    "🧠 Ottimizza visite",
    "🧹 Filtro ID",
    "🧹 Filtro nomi imprese",
    "📂 Storico blocchi"
]

# === Imposta sezione iniziale se non esiste
if "sezione_attiva" not in st.session_state:
    st.session_state["sezione_attiva"] = "🖥️ Parsing PDF"

# === Selectbox reattiva (sincronizzata con session_state)
selezionata = st.sidebar.selectbox(
    "Seleziona una sezione",
    voci,
    index=voci.index(st.session_state["sezione_attiva"]),
    key="selectbox_sezione"
)

# === Aggiorna sezione attiva se è stata cambiata manualmente
if st.session_state["sezione_attiva"] != st.session_state["selectbox_sezione"]:
    st.session_state["sezione_attiva"] = st.session_state["selectbox_sezione"]

# === Sezione corrente usata nel main
sezione = st.session_state["sezione_attiva"]












if sezione == "🧠 Ottimizza visite":
    csv_path, json_path, tempo_visita, tempo_massimo = interfaccia()

    if csv_path and json_path and tempo_visita and tempo_massimo:
        if st.button("Genera blocchi"):
            df_blocchi = genera_blocchi(csv_path, json_path, tempo_visita, tempo_massimo)
            df_blocchi = completa_blocchi(df_blocchi, csv_path)
            html_path = genera_mappa(df_blocchi, csv_path)

            # Salva anche la versione "pulita" per uso con salvataggio
            st.session_state["df_blocchi"] = df_blocchi.copy()
            st.success("✅ Tutti i file generati con successo")

    # === VISUALIZZAZIONE BLOCCO SOLO SE ESISTE ===
    if "df_blocchi" in st.session_state:
        df_blocchi = st.session_state["df_blocchi"]

        st.markdown("## 📋 Visualizza blocchi generati:")
        blocchi_disponibili = df_blocchi["Blocco"].unique().tolist()
        blocco_scelto = st.selectbox("Seleziona un blocco da visualizzare o scaricare:", blocchi_disponibili)

        df_blocco_singolo = df_blocchi[df_blocchi["Blocco"] == blocco_scelto].copy()
        st.dataframe(df_blocco_singolo, use_container_width=True)

        if st.button("💾 Salva su Google Sheets"):
            from google_sheets import salva_blocco_su_google_sheets, registra_blocco_in_storico

            ora = datetime.now().strftime("%Y-%m-%d %H:%M")
            nome_tab = f"Blocco_{blocco_scelto}_{ora}"

            salva_blocco_su_google_sheets(df_blocco_singolo, nome_tab)
            registra_blocco_in_storico(nome_tab, ora, len(df_blocco_singolo))
            st.success(f"✅ Blocco salvato su Google Sheets come '{nome_tab}'")
            
            # 🔁 Redirect automatico alla sezione "Storico blocchi"
            st.session_state["sezione_attiva"] = "📂 Storico blocchi"
            st.rerun()


            
# === ESTRAZIONE PDF APPALTI ===
elif sezione == "🖥️ Parsing PDF":
    interfaccia_pdf()

# === ID GIÀ VISITATI ===
elif sezione == "🧹 Filtro ID":
    interfaccia_id_gia_visitati()

# === NOMI DA FILTRARE ===
elif sezione == "🧹 Filtro nomi imprese":
    interfaccia_filtro_nomi()

# === CRONOLOGIA ===
elif sezione == "📂 Storico blocchi":
    from ui import interfaccia_cronologia
    interfaccia_cronologia()
