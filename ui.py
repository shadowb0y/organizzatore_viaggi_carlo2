
# === ui.py (aggiunta memoria imprese escluse) ===
import streamlit as st
from config import DEFAULT_TEMPO_VISITA, DEFAULT_TEMPO_MASSIMO
import os
import pandas as pd
import re
import json

ELIMINATI_FILE = "imprese_escluse.json"

def interfaccia():
    st.title("Costruttore di blocchi visite aziendali")

    csv_path = "output/aziende_geocodificate_filtrate.csv"
    json_path = "output/matrice_durate_filtrata.json"

    if not os.path.exists(csv_path) or not os.path.exists(json_path):
        st.warning("⚠️ Prima di generare i blocchi, completa la sezione 'Estrazione PDF Appalti' per filtrare i dati.")
        return None, None, None, None

    # === Tempo visita in minuti ===
    tempo_visita_min = st.number_input("Tempo visita per azienda (minuti)", min_value=1, value=DEFAULT_TEMPO_VISITA // 60)
    tempo_visita = tempo_visita_min * 60

    # === Tempo massimo in ore e minuti ===
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
    filtro_valore = st.checkbox("Escludi progetti con valore stimato inferiore a 400.000€", value=True)
    filtro_data = st.checkbox("Escludi progetti con fine lavori prima di Febbraio 2025", value=True)
    filtro_impresa_generica = st.checkbox("Rimuovi righe senza nome impresa o con dicitura 'assegnato'", value=True)

    output_path = "output/aziende_filtrate_correttamente.csv"

    if st.button("Estrai e filtra dati", key="estrai_pdf"):
        from estrattore import estrai_dati_da_pdf, pulisci_unifica_filtra

        df_raw = estrai_dati_da_pdf(selected_files)
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
    
            # Carica le esclusioni solo se ci sono imprese disponibili
            escluse_storiche = []
            if os.path.exists(ELIMINATI_FILE):
                with open(ELIMINATI_FILE, "r", encoding="utf-8") as f:
                    escluse_storiche = json.load(f)
            default_validi = [imp for imp in escluse_storiche if imp in tutte_imprese]
    
            selezionate = st.multiselect("Seleziona le imprese da escludere:", tutte_imprese, default=default_validi)
    
            if st.button("Rimuovi imprese selezionate", key="filtro_imprese"):
                def contiene_selezionata(val):
                    if pd.isna(val): return False
                    return any(sel in val for sel in selezionate)
    
                mask_da_rimuovere = df_loaded["Imprese"].apply(contiene_selezionata)
                df_filtrato_finale = df_loaded.loc[~mask_da_rimuovere].copy()
                df_filtrato_finale.to_csv(output_path, index=False, encoding="utf-8-sig")
    
                with open(ELIMINATI_FILE, "w", encoding="utf-8") as f:
                    json.dump(selezionate, f, ensure_ascii=False, indent=2)
    
                st.success("✅ Righe contenenti imprese selezionate eliminate con successo (e memorizzate)")
                st.dataframe(df_filtrato_finale)
                st.download_button("Scarica CSV aggiornato", data=df_filtrato_finale.to_csv(index=False).encode("utf-8-sig"), file_name=output_path)
    
        st.subheader("Filtra file geocodificato e matrice distanze")
        if st.button("Applica filtro agli altri file", key="filtro_finale"):
            from filtra_dataset import filtra_dati

            input_csv_geo = "data/aziende_geocodificate.csv"
            input_matrice_json = "data/matrice_durate.json"
            output_csv_geo = "output/aziende_geocodificate_filtrate.csv"
            output_matrice_json = "output/matrice_durate_filtrata.json"

            df_geo_filtrato, _ = filtra_dati(output_path, input_csv_geo, input_matrice_json, output_csv_geo, output_matrice_json)
            st.success("✅ File geocodificato e matrice filtrati correttamente")

            # 🔁 Salva stato e vai ai blocchi
            st.session_state["sezione_attiva"] = "Blocchi Visite Aziendali"
            st.rerun()
