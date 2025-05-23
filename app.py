import streamlit as st
from blocchi import genera_blocchi
from completamento import completa_blocchi
from mappa import genera_mappa
from ui import interfaccia, interfaccia_pdf, interfaccia_id_gia_visitati, interfaccia_filtro_nomi
import os
import pandas as pd
from datetime import datetime



st.set_page_config(layout="wide")

os.makedirs("output", exist_ok=True)
os.makedirs("cronologia", exist_ok=True)

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

voci = [
    "🖥️ Parsing PDF",
    "🧠 Ottimizza visite",
    "🧹 Filtro ID",
    "🧹 Filtro nomi imprese",
    "📂 Storico blocchi"
]

if "sezione_attiva" not in st.session_state:
    st.session_state["sezione_attiva"] = "🖥️ Parsing PDF"

selezionata = st.sidebar.selectbox(
    "Seleziona una sezione",
    voci,
    index=voci.index(st.session_state["sezione_attiva"]),
    key="selectbox_sezione"
)

if st.session_state["sezione_attiva"] != st.session_state["selectbox_sezione"]:
    st.session_state["sezione_attiva"] = st.session_state["selectbox_sezione"]

sezione = st.session_state["sezione_attiva"]

if sezione == "🧠 Ottimizza visite":
    lat, lon = rileva_posizione()

    csv_path, json_path, tempo_visita, tempo_massimo = interfaccia()

    if lat and lon:
        try:
            df = pd.read_csv("output/aziende_geocodificate_filtrate.csv")
            riga_utente = pd.DataFrame([{  # posizione utente come punto extra
                "Nome": "\U0001F4CD Tua posizione",
                "Latitudine": lat,
                "Longitudine": lon,
                "Comune": "Posizione attuale",
                "Provincia": "",
                "Indirizzo": ""
            }])
            df = pd.concat([riga_utente, df], ignore_index=True)
            df.to_csv("output/aziende_geocodificate_filtrate.csv", index=False)
            st.success("Posizione utente aggiunta ai dati.")
        except Exception as e:
            st.error(f"Errore durante l'aggiunta della posizione: {e}")

    if csv_path and json_path and tempo_visita and tempo_massimo:
        if st.button("Genera blocchi"):
            df_blocchi = genera_blocchi(csv_path, json_path, tempo_visita, tempo_massimo)
            df_blocchi = completa_blocchi(df_blocchi, csv_path)
            html_path = genera_mappa(df_blocchi, csv_path)
            st.session_state["df_blocchi"] = df_blocchi.copy()
            st.success("✅ Tutti i file generati con successo")

    if "df_blocchi" in st.session_state:
        df_blocchi = st.session_state["df_blocchi"]

        st.markdown("## 📋 Visualizza blocchi generati:")
        blocchi_disponibili = df_blocchi["Blocco"].unique().tolist()
        blocco_scelto = st.selectbox("Seleziona un blocco da visualizzare o scaricare:", blocchi_disponibili)
        df_blocco_singolo = df_blocchi[df_blocchi["Blocco"] == blocco_scelto].copy()
        st.dataframe(df_blocco_singolo, use_container_width=True)

        if st.button("📅 Salva su Google Sheets"):
            from google_sheets import salva_blocco_su_google_sheets, registra_blocco_in_storico
            ora = datetime.now().strftime("%Y-%m-%d %H:%M")
            nome_tab = f"Blocco_{blocco_scelto}_{ora}"
            salva_blocco_su_google_sheets(df_blocco_singolo, nome_tab)
            registra_blocco_in_storico(nome_tab, ora, len(df_blocco_singolo))
            st.success(f"✅ Blocco salvato su Google Sheets come '{nome_tab}'")
            st.session_state["sezione_attiva"] = "📂 Storico blocchi"
            st.rerun()

elif sezione == "🖥️ Parsing PDF":
    interfaccia_pdf()
elif sezione == "🧹 Filtro ID":
    interfaccia_id_gia_visitati()
elif sezione == "🧹 Filtro nomi imprese":
    interfaccia_filtro_nomi()
elif sezione == "📂 Storico blocchi":
    from ui import interfaccia_cronologia
    interfaccia_cronologia()
