# === ui.py (modulare) ===
import streamlit as st
from config import DEFAULT_TEMPO_VISITA, DEFAULT_TEMPO_MASSIMO
import pandas as pd
import re
import json
from datetime import date
import os
import datetime

os.makedirs("output", exist_ok=True)
os.makedirs("cronologia", exist_ok=True)  # nuova cartella per blocchi salvati

# === PATH FILE ===
VISITATI_FILE = "output/id_gia_visitati.json"
NOMI_FILE = "data/nomi.csv"
NOMI_ESCLUSI_FILE = "output/nomi_esclusi.json"

def interfaccia():
    st.title("Costruttore di blocchi visite aziendali")

    csv_path = "output/aziende_geocodificate_filtrate.csv"
    json_path = "output/matrice_durate_filtrata.json"

    if not os.path.exists(csv_path) or not os.path.exists(json_path):
        st.warning("⚠️ Prima di generare i blocchi, completa la sezione 'Estrazione PDF Appalti' per filtrare i dati.")
        return None, None, None, None

    tempo_visita_min = st.number_input("Tempo visita per azienda (minuti)", min_value=1, value=DEFAULT_TEMPO_VISITA // 60)
    tempo_visita = tempo_visita_min * 60

    col1, col2 = st.columns(2)
    with col1:
        ore = st.number_input("Durata massima blocco (ore)", min_value=0, value=DEFAULT_TEMPO_MASSIMO // 3600)
    with col2:
        minuti = st.number_input("Durata massima blocco (minuti)", min_value=0, value=(DEFAULT_TEMPO_MASSIMO % 3600) // 60)

    tempo_massimo = ore * 3600 + minuti * 60

    return csv_path, json_path, tempo_visita, tempo_massimo

def interfaccia_pdf():
    st.header("Estrazione dati da PDF di appalti")

    pdf_folder = "pdf"
    pdf_files = [os.path.join(pdf_folder, f) for f in os.listdir(pdf_folder) if f.endswith(".pdf")]
    selected_files = st.multiselect("Seleziona i PDF da elaborare:", pdf_files, default=pdf_files)

    st.subheader("Filtri disponibili")
    filtro_valore_minimo = st.selectbox(
        "Escludi progetti con valore stimato inferiore a:",
        [100000, 200000, 300000, 400000, 500000, 600000, 700000, 800000, 900000],
        index=3
    )

    filtro_data_limite = st.date_input(
        "Escludi progetti con fine lavori prima di:",
        value=date(2025, 2, 1)
    )

    output_path = "output/aziende_filtrate_correttamente.csv"

    if st.button("Estrai e filtra dati", key="estrai_pdf"):
        from estrattore import estrai_dati_da_pdf, pulisci_unifica_filtra

        df_raw = estrai_dati_da_pdf(selected_files, filtro_valore_minimo, filtro_data_limite)
        df_filtrato = pulisci_unifica_filtra(df_raw)

        df_filtrato.to_csv(output_path, index=False, encoding="utf-8-sig")

        st.success("Estrazione completata")
        st.dataframe(df_filtrato)
        st.download_button("Scarica CSV filtrato", data=df_filtrato.to_csv(index=False).encode("utf-8-sig"), file_name=output_path)

    st.subheader("Filtra file geocodificato e matrice distanze")
    if st.button("Applica filtro agli altri file", key="filtro_finale"):
        from filtra_dataset import filtra_dati

        input_csv_geo = "data/aziende_geocodificate.csv"
        input_matrice_json = "data/matrice_durate.json"
        output_csv_geo = "output/aziende_geocodificate_filtrate.csv"
        output_matrice_json = "output/matrice_durate_filtrata.json"

        df_geo_filtrato, _ = filtra_dati(output_path, input_csv_geo, input_matrice_json, output_csv_geo, output_matrice_json)
        st.success("✅ File geocodificato e matrice filtrati correttamente")

        st.session_state["sezione_attiva"] = "Blocchi Visite Aziendali"
        st.rerun()

def interfaccia_id_gia_visitati():
    st.header("📌 ID già visitati")

    with st.expander("➕ Aggiungi nuovi ID visitati"):
        nuovi_id = st.text_area("Inserisci uno o più ID progetto separati da virgola, spazio, punto o punto e virgola")
        note = st.text_input("Note (facoltative)")
        data_visita = st.date_input("Data visita", value=datetime.date.today())

        if st.button("Salva ID visitati"):
            ids = [i.strip() for i in re.split(r"[,\s;\.]+", nuovi_id) if i.strip()]
            if ids:
                record = []
                for id_ in ids:
                    record.append({
                        "ID Progetto": id_,
                        "Data": str(data_visita),
                        "Note": note
                    })

                if os.path.exists(VISITATI_FILE):
                    with open(VISITATI_FILE, "r", encoding="utf-8") as f:
                        esistenti = json.load(f)
                else:
                    esistenti = []

                esistenti.extend(record)
                with open(VISITATI_FILE, "w", encoding="utf-8") as f:
                    json.dump(esistenti, f, ensure_ascii=False, indent=2)

                st.success(f"✅ Salvati {len(ids)} ID visitati.")

    if os.path.exists(VISITATI_FILE):
        with open(VISITATI_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            df_id_visitati = pd.DataFrame(data)

        if not df_id_visitati.empty:
            st.markdown("### 📄 ID visitati salvati:")

            for i, row in df_id_visitati.sort_values(by="Data", ascending=False).iterrows():
                col1, col2, col3 = st.columns([4, 2, 1])
                with col1:
                    st.write(f"🆔 {row['ID Progetto']} – 📅 {row['Data']} – 📝 {row.get('Note', '')}")
                with col3:
                    if st.button("❌", key=f"del_id_{i}"):
                        df_id_visitati = df_id_visitati.drop(i)
                        df_id_visitati.to_json(VISITATI_FILE, orient="records", force_ascii=False, indent=2)
                        st.rerun()

def interfaccia_filtro_nomi():
    st.header("🚫 Nomi aziende da filtrare")

    if os.path.exists(NOMI_FILE):
        df_nomi = pd.read_csv(NOMI_FILE, header=None, dtype=str).dropna()
        lista_nomi = sorted(set(df_nomi[0].tolist()))

        with st.expander("➕ Aggiungi nuovi nomi da escludere"):
            selezionati = st.multiselect("Seleziona uno o più nomi da escludere", options=lista_nomi)
            nota = st.text_input("Note (facoltative)", key="nota_esclusione_nomi")
            data_esclusione = st.date_input("Data", value=date.today(), key="data_esclusione_nomi")

            if st.button("Salva nomi esclusi"):
                if selezionati:
                    nuovi_record = [
                        {"Nome": nome, "Data": str(data_esclusione), "Note": nota}
                        for nome in selezionati
                    ]

                    if os.path.exists(NOMI_ESCLUSI_FILE):
                        with open(NOMI_ESCLUSI_FILE, "r", encoding="utf-8") as f:
                            esistenti = json.load(f)
                    else:
                        esistenti = []

                    esistenti.extend(nuovi_record)

                    with open(NOMI_ESCLUSI_FILE, "w", encoding="utf-8") as f:
                        json.dump(esistenti, f, ensure_ascii=False, indent=2)

                    st.success(f"✅ Salvati {len(selezionati)} nomi esclusi.")
    else:
        st.error(f"⚠️ File '{NOMI_FILE}' non trovato. Caricalo manualmente nella cartella /data.")

    if os.path.exists(NOMI_ESCLUSI_FILE):
        with open(NOMI_ESCLUSI_FILE, "r", encoding="utf-8") as f:
            dati_nomi = json.load(f)
            df_esclusi = pd.DataFrame(dati_nomi)

        if not df_esclusi.empty:
            st.markdown("### 📄 Nomi esclusi salvati:")

            for i, row in df_esclusi.sort_values(by="Data", ascending=False).iterrows():
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"🏢 {row['Nome']} – 📅 {row['Data']} – 📝 {row.get('Note', '')}")
                with col2:
                    if st.button("❌", key=f"del_nome_{i}"):
                        df_esclusi = df_esclusi.drop(i)
                        df_esclusi.to_json(NOMI_ESCLUSI_FILE, orient="records", force_ascii=False, indent=2)
                        st.rerun()
()




def interfaccia_cronologia():
    st.title("📂 Cronologia blocchi salvati")

    cartella = "cronologia"
    files_cronologia = sorted([f for f in os.listdir(cartella) if f.endswith(".xlsx")], reverse=True)

    if not files_cronologia:
        st.info("Nessun blocco salvato ancora.")
        return

    for nome_file in files_cronologia:
        path = os.path.join(cartella, nome_file)
        st.markdown(f"### 📄 {nome_file}")
        df = pd.read_excel(path)
        st.dataframe(df, use_container_width=True)
        with open(path, "rb") as f:
            st.download_button("⬇️ Scarica", f, file_name=nome_file, key=nome_file)
