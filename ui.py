# === ui.py (esteso con interfaccia PDF) ===
import streamlit as st
from config import DEFAULT_TEMPO_VISITA, DEFAULT_TEMPO_MASSIMO
import os

def interfaccia():
    st.title("Costruttore di blocchi visite aziendali")
    csv_path = st.text_input("Percorso del file aziende_geocodificate.csv")
    json_path = st.text_input("Percorso del file matrice_durate.json")
    tempo_visita = st.number_input("Tempo visita per azienda (secondi)", value=DEFAULT_TEMPO_VISITA)
    tempo_massimo = st.number_input("Tempo massimo per blocco (secondi)", value=DEFAULT_TEMPO_MASSIMO)
    return csv_path, json_path, tempo_visita, tempo_massimo

def interfaccia_pdf():
    st.header("Estrazione dati da PDF di appalti")

    # === SELEZIONE FILE ===
    pdf_folder = "pdf"
    pdf_files = [os.path.join(pdf_folder, f) for f in os.listdir(pdf_folder) if f.endswith(".pdf")]
    selected_files = st.multiselect("Seleziona i PDF da elaborare:", pdf_files, default=pdf_files)

    # === SELEZIONE FILTRI ===
    st.subheader("Filtri disponibili")
    filtro_valore = st.checkbox("Escludi progetti con valore stimato inferiore a 400.000€", value=True)
    filtro_data = st.checkbox("Escludi progetti con fine lavori prima di Febbraio 2025", value=True)
    filtro_impresa_generica = st.checkbox("Rimuovi righe senza nome impresa o con dicitura 'assegnato'", value=True)

    if st.button("Estrai e filtra dati"):
        from estrattore import estrai_dati_da_pdf, pulisci_unifica_filtra, salva_csv

        df_raw = estrai_dati_da_pdf(selected_files)

        if not filtro_valore:
            df_raw["Valore Stimato"] = ""
        if not filtro_data:
            df_raw["Data Valid"] = True  # Bypass temporaneo

        df_filtrato = pulisci_unifica_filtra(df_raw)

        if not filtro_impresa_generica:
            df_filtrato = df_filtrato.copy()

        output_path = "aziende_filtrate_correttamente.csv"
        df_filtrato.to_csv(output_path, index=False, encoding="utf-8-sig")

        st.success("✅ Estrazione completata")
        st.dataframe(df_filtrato)
        st.download_button("Scarica CSV filtrato", data=df_filtrato.to_csv(index=False).encode("utf-8-sig"), file_name=output_path)
