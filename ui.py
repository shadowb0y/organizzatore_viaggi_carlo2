# === ui.py (aggiornato) ===
import streamlit as st

from config import DEFAULT_TEMPO_VISITA, DEFAULT_TEMPO_MASSIMO
import pandas as pd
import re
import json
from datetime import date
import os

os.makedirs("output", exist_ok=True)
ELIMINATI_FILE = "imprese_escluse.json"

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
        index=3  # default = 400.000 €
    )

    filtro_data_limite = st.date_input(
        "Escludi progetti con fine lavori prima di:",
        value=date(2025, 2, 1)
    )

    output_path = "output/aziende_filtrate_correttamente.csv"

    if st.button("Estrai e filtra dati", key="estrai_pdf"):
        from estrattore import estrai_dati_da_pdf, pulisci_unifica_filtra

        # ✅ Passaggio dei nuovi parametri
        df_raw = estrai_dati_da_pdf(selected_files, filtro_valore_minimo, filtro_data_limite)
        df_filtrato = pulisci_unifica_filtra(df_raw)

        df_filtrato.to_csv(output_path, index=False, encoding="utf-8-sig")

        st.success("Estrazione completata")
        st.dataframe(df_filtrato)
        st.download_button("Scarica CSV filtrato", data=df_filtrato.to_csv(index=False).encode("utf-8-sig"), file_name=output_path)

    if os.path.exists(output_path):
        st.subheader("Filtro imprese da rimuovere")
        df_loaded = pd.read_csv(output_path, dtype=str)

        if "Imprese" in df_loaded.columns and not df_loaded.empty:
            tutte_imprese = set()
            for lista in df_loaded["Imprese"].dropna():
                for i in re.split(r";|\+", str(lista)):
                    nome = i.strip()
                    if nome:
                        tutte_imprese.add(nome)
            tutte_imprese = sorted(tutte_imprese)

            escluse_storiche = []
            if os.path.exists(ELIMINATI_FILE):
                with open(ELIMINATI_FILE, "r", encoding="utf-8") as f:
                    escluse_storiche = json.load(f)
            default_validi = [imp for imp in escluse_storiche if imp in tutte_imprese]

            col1, col2 = st.columns([1, 2])

            with col2:
                selezionate = st.multiselect(
                    "Seleziona le imprese da escludere:",
                    tutte_imprese,
                    default=default_validi
                )

            with col1:
                st.markdown("Imprese escluse")
                if selezionate:
                    for impresa in selezionate:
                        st.markdown(
                            f'<div style="background-color:#ff4b4b;padding:4px 8px;border-radius:6px;margin-bottom:4px;color:white;font-weight:bold;">{impresa}</div>',
                            unsafe_allow_html=True
                        )
                else:
                    st.info("Nessuna impresa selezionata.")


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
