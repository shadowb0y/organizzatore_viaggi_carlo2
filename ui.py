
# === ui.py (esteso con filtro imprese post-estrazione) ===
import streamlit as st
from config import DEFAULT_TEMPO_VISITA, DEFAULT_TEMPO_MASSIMO
import os
import pandas as pd

def interfaccia():
    st.title("Costruttore di blocchi visite aziendali")
    csv_path = st.text_input("Percorso del file aziende_geocodificate.csv")
    json_path = st.text_input("Percorso del file matrice_durate.json")
    tempo_visita = st.number_input("Tempo visita per azienda (secondi)", value=DEFAULT_TEMPO_VISITA)
    tempo_massimo = st.number_input("Tempo massimo per blocco (secondi)", value=DEFAULT_TEMPO_MASSIMO)
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

    output_path = "aziende_filtrate_correttamente.csv"

    if st.button("Estrai e filtra dati", key="estrai_pdf"):
        from estrattore import estrai_dati_da_pdf, pulisci_unifica_filtra

        df_raw = estrai_dati_da_pdf(selected_files)
        df_filtrato = pulisci_unifica_filtra(df_raw)

        df_filtrato.to_csv(output_path, index=False, encoding="utf-8-sig")

        st.success("✅ Estrazione completata")
        st.dataframe(df_filtrato)
        st.download_button("Scarica CSV filtrato", data=df_filtrato.to_csv(index=False).encode("utf-8-sig"), file_name=output_path)

    # === RICARICA FILE CSV E FILTRA IMPRESE SELEZIONATE ===
    if os.path.exists(output_path):
        st.subheader("Filtro imprese da rimuovere")
        df_loaded = pd.read_csv(output_path, dtype=str)
        if "Imprese" in df_loaded.columns:
            tutte_imprese = set()
            for lista in df_loaded["Imprese"].dropna():
                for i in re.split(r";|\+", str(lista)):
                    nome = i.strip()
                    if nome:
                        tutte_imprese.add(nome)
            tutte_imprese = sorted(tutte_imprese)

            selezionate = st.multiselect("Seleziona le imprese da escludere:", tutte_imprese)
            if st.button("Rimuovi imprese selezionate", key="filtro_imprese"):
                def contiene_selezionata(val):
                    if pd.isna(val): return False
                    return any(sel in val for sel in selezionate)

                mask_da_rimuovere = df_loaded["Imprese"].apply(contiene_selezionata)
                df_filtrato_finale = df_loaded.loc[~mask_da_rimuovere].copy()
                df_filtrato_finale.to_csv(output_path, index=False, encoding="utf-8-sig")

                st.success("✅ Righe contenenti imprese selezionate eliminate con successo")
                st.dataframe(df_filtrato_finale)
                st.download_button("Scarica CSV aggiornato", data=df_filtrato_finale.to_csv(index=False).encode("utf-8-sig"), file_name=output_path)
