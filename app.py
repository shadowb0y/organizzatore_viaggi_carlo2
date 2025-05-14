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
sezione = st.sidebar.selectbox(
    "Seleziona una sezione",
    [
        "Blocchi Visite Aziendali",
        "Estrazione PDF Appalti",
        "📌 ID già visitati",
        "🚫 Nomi da filtrare",
        "📂 Cronologia"
    ],
    index=0
)

# === BLOCCHI VISITE AZIENDALI ===
if sezione == "Blocchi Visite Aziendali":
    csv_path, json_path, tempo_visita, tempo_massimo = interfaccia()

    if csv_path and json_path and tempo_visita and tempo_massimo:
        if st.button("Genera blocchi"):
            df_blocchi = genera_blocchi(csv_path, json_path, tempo_visita, tempo_massimo)
            df_blocchi = completa_blocchi(df_blocchi, csv_path)
            html_path = genera_mappa(df_blocchi, csv_path)

            st.success("✅ Tutti i file generati con successo")

            st.markdown("## 📋 Visualizza blocchi generati:")
            blocchi_disponibili = df_blocchi["Blocco"].unique().tolist()
            blocco_scelto = st.selectbox("Seleziona un blocco da visualizzare o scaricare:", blocchi_disponibili)

            df_blocco_singolo = df_blocchi[df_blocchi["Blocco"] == blocco_scelto]
            st.dataframe(df_blocco_singolo, use_container_width=True)

            # Pulsante per salvare singolo blocco
            if st.button("📥 Scarica blocco selezionato"):
                ora = datetime.now().strftime("%Y-%m-%d_%H-%M")
                nome_file = f"blocco_{blocco_scelto}_{ora}.xlsx"
                path_file = os.path.join("cronologia", nome_file)
                df_blocco_singolo.to_excel(path_file, index=False)
                st.success(f"✅ Blocco {blocco_scelto} salvato in cronologia come {nome_file}")

# === ESTRAZIONE PDF APPALTI ===
elif sezione == "Estrazione PDF Appalti":
    interfaccia_pdf()

# === ID GIÀ VISITATI ===
elif sezione == "📌 ID già visitati":
    interfaccia_id_gia_visitati()

# === NOMI DA FILTRARE ===
elif sezione == "🚫 Nomi da filtrare":
    interfaccia_filtro_nomi()

# === CRONOLOGIA ===
elif sezione == "📂 Cronologia":
    st.title("📂 Cronologia blocchi salvati")

    files_cronologia = sorted([f for f in os.listdir("cronologia") if f.endswith(".xlsx")], reverse=True)

    if not files_cronologia:
        st.info("Nessun blocco salvato ancora.")
    else:
        for nome_file in files_cronologia:
            path = os.path.join("cronologia", nome_file)
            st.markdown(f"### 📄 {nome_file}")
            df = pd.read_excel(path)
            st.dataframe(df, use_container_width=True)
            with open(path, "rb") as f:
                st.download_button("⬇️ Scarica", f, file_name=nome_file, key=nome_file)
