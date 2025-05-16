# === ui.py (modulare) ===
import streamlit as st
from config import DEFAULT_TEMPO_VISITA, DEFAULT_TEMPO_MASSIMO
import pandas as pd
import re
import json
from datetime import date
import os
import datetime
from google_sheets import leggi_id_visitati, aggiungi_id_visitati, elimina_id_visitato, salva_blocco_su_google_sheets, registra_blocco_in_storico

os.makedirs("output", exist_ok=True)
os.makedirs("cronologia", exist_ok=True)  # nuova cartella per blocchi salvati

# === PATH FILE ===
VISITATI_FILE = "output/id_gia_visitati.json"
NOMI_FILE = "data/nomi.csv"
NOMI_ESCLUSI_FILE = "output/nomi_esclusi.json"

def interfaccia():
    st.title("🕹️ Costruttore di blocchi visite aziendali")

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
    st.header("🖥️ Estrazione dati da PDF di appalti")

    pdf_folder = "pdf"
    # Lista dei PDF solo con nome visibile, ma mantieni path interno
    pdf_files = [f for f in os.listdir("pdf") if f.endswith(".pdf")]
    file_paths = {f: os.path.join("pdf", f) for f in pdf_files}

    selected_filenames = st.multiselect("Seleziona i PDF da elaborare:", options=pdf_files, default=pdf_files)
    selected_files = [file_paths[f] for f in selected_filenames]

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
        from filtra_dataset import filtra_dati  # <--- già qui

        df_raw = estrai_dati_da_pdf(selected_files, filtro_valore_minimo, filtro_data_limite)
        df_filtrato = pulisci_unifica_filtra(df_raw)
        df_filtrato.to_csv(output_path, index=False, encoding="utf-8-sig")
        st.success("Estrazione completata")
        st.dataframe(df_filtrato)

        # Subito dopo, applica il filtro
        input_csv_geo = "data/aziende_geocodificate.csv"
        input_matrice_json = "data/matrice_durate.json"
        output_csv_geo = "output/aziende_geocodificate_filtrate.csv"
        output_matrice_json = "output/matrice_durate_filtrata.json"

        df_geo_filtrato, _ = filtra_dati(output_path, input_csv_geo, input_matrice_json, output_csv_geo, output_matrice_json)
        st.success("✅ File geocodificato e matrice filtrati correttamente")
        st.session_state["sezione_attiva"] = "🧠 Ottimizza visite"
        st.rerun()





def interfaccia_id_gia_visitati():
    st.header("🧹 ID già visitati")

    # === Aggiunta nuovi ID ===
    with st.expander("➕ Aggiungi nuovi ID visitati"):
        nuovi_id = st.text_area("Inserisci uno o più ID progetto separati da virgola, spazio, punto o punto e virgola")
        note = st.text_input("Note (facoltative)")
        data_visita = st.date_input("Data visita", value=datetime.date.today())

        if st.button("Salva ID visitati"):
            ids = [i.strip() for i in re.split(r"[,\s;\.]+", nuovi_id) if i.strip()]
            if ids:
                aggiungi_id_visitati(ids, data_visita, note)
                st.success(f"✅ Salvati {len(ids)} ID visitati.")
                st.rerun()

    # === Visualizzazione + Eliminazione ===
    df_id_visitati = leggi_id_visitati()

    if not df_id_visitati.empty:
        st.markdown("### 📄 ID visitati salvati:")

        for i, row in df_id_visitati.sort_values(by="Data Salvataggio", ascending=False).iterrows():

            col1, col2, col3 = st.columns([4, 2, 1])
            with col1:
                st.write(f"🆔 {row['ID Progetto']} – 📅 {row['Data Salvataggio']} – 📝 {row.get('Note', '')}")

            with col3:
                if st.button("❌", key=f"del_id_{i}"):
                    st.session_state[f"conferma_id_{i}"] = True

                if st.session_state.get(f"conferma_id_{i}", False):
                    with st.expander(f"⚠️ Conferma eliminazione ID {row['ID Progetto']}", expanded=True):
                        st.warning("Questa azione eliminerà definitivamente questo ID. Procedere?")
                        if st.button("✅ Elimina definitivamente", key=f"conferma_del_id_{i}"):
                            elimina_id_visitato(i)
                            st.session_state.pop(f"conferma_id_{i}")
                            st.rerun()


from google_sheets import leggi_nomi_esclusi, aggiungi_nomi_esclusi, elimina_nome_escluso
from google_sheets import leggi_nomi_esclusi, aggiungi_nomi_esclusi, elimina_nome_escluso
import streamlit as st
import pandas as pd
from datetime import date

def interfaccia_filtro_nomi():
    st.header("🧹 Nomi aziende da filtrare")

    with st.expander("➕ Aggiungi nuovi nomi da escludere"):
        # === Leggi nomi esclusi già presenti su Google Sheets
        df_esclusi_sheet = leggi_nomi_esclusi()
        nomi_esclusi = set(df_esclusi_sheet["Nome"]) if not df_esclusi_sheet.empty else set()

        # === Leggi tutti i nomi da data/nomi.csv
        try:
            df_tutti_nomi = pd.read_csv("data/nomi.csv")
            nomi_tutti = set(df_tutti_nomi["Nome"].dropna().unique())
        except Exception as e:
            st.warning(f"⚠️ Impossibile leggere 'data/nomi.csv': {e}")
            nomi_tutti = set()

        # === Unione nomi già esclusi + tutti quelli disponibili
        nomi_esistenti = sorted(nomi_tutti.union(nomi_esclusi))

        # === Campo multiselect con suggerimenti
        nuovi_nomi = st.multiselect(
            "Seleziona o scrivi nuovi nomi da escludere",
            options=nomi_esistenti,
            default=[],
            help="Puoi anche scrivere nuovi nomi e premere Invio"
        )

        nota = st.text_input("Note (facoltative)", key="nota_esclusione_nomi")
        data_esclusione = st.date_input("Data", value=date.today(), key="data_esclusione_nomi")

        if st.button("Salva nomi esclusi"):
            nomi = [n.strip() for n in nuovi_nomi if n.strip()]
            if nomi:
                aggiungi_nomi_esclusi(nomi, data_esclusione, nota)
                st.success(f"✅ Salvati {len(nomi)} nomi esclusi.")
                st.rerun()

    # === Visualizzazione nomi esclusi
    df_esclusi = leggi_nomi_esclusi()

    if not df_esclusi.empty:
        st.markdown("### 📄 Nomi esclusi salvati:")

        # ✅ Rinomina colonna per sorting
        df_esclusi = df_esclusi.rename(columns={"Data Salvataggio": "Data"})

        for i, row in df_esclusi.sort_values(by="Data", ascending=False).iterrows():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.write(f"🏢 {row['Nome']} – 📅 {row['Data']} – 📝 {row.get('Note', '')}")
            with col2:
                if st.button("❌", key=f"del_nome_{i}"):
                    st.session_state[f"conferma_nome_{i}"] = True

                if st.session_state.get(f"conferma_nome_{i}", False):
                    with st.expander(f"⚠️ Conferma eliminazione '{row['Nome']}'", expanded=True):
                        st.warning("Questa azione eliminerà definitivamente questo nome. Procedere?")
                        if st.button("✅ Elimina definitivamente", key=f"conferma_del_nome_{i}"):
                            elimina_nome_escluso(i)
                            st.session_state.pop(f"conferma_nome_{i}")
                            st.rerun()

def interfaccia_cronologia():
    st.title("📂 Cronologia blocchi salvati")

    from google_sheets import leggi_blocchi_salvati_su_google_sheets, get_worksheet, elimina_blocco_storico

    try:
        df_blocchi = leggi_blocchi_salvati_su_google_sheets()
    except Exception as e:
        st.error(f"Errore durante il caricamento da Google Sheets: {e}")
        return

    if df_blocchi.empty:
        st.info("Nessun blocco salvato su Google Sheets.")
        return

    for i, row in df_blocchi.sort_values(by="Data Salvataggio", ascending=False).iterrows():
        col1, col2 = st.columns([8, 1])
        with col1:
            with st.expander(f"📄 {row['Nome Blocco']}"):
                try:
                    ws = get_worksheet(row["Nome Blocco"])
                    df_contenuto = pd.DataFrame(ws.get_all_records())
                    st.dataframe(df_contenuto, use_container_width=True)
                except Exception as e:
                    st.error(f"Errore nel caricamento del blocco '{row['Nome Blocco']}': {e}")

                st.markdown(f"📅 **Data**: {row['Data Salvataggio']} &nbsp;&nbsp;&nbsp; 🏢 **Aziende**: {row['N. Aziende']}")
        
        with col2:
            if st.button("🗑", key=f"del_blocco_{i}"):
                st.session_state[f"conferma_blocco_{i}"] = True
            
            if st.session_state.get(f"conferma_blocco_{i}", False):
                with st.expander(f"⚠️ Conferma eliminazione '{row['Nome Blocco']}'", expanded=True):
                    st.warning("Questa azione eliminerà il blocco sia dallo storico che dal Google Sheets. Procedere?")
            
                    if st.button("✅ Elimina definitivamente", key=f"conferma_del_blocco_{i}"):
                        try:
                            from google_sheets import elimina_blocco_storico, elimina_tab_blocco
            
                            # 🧠 Prima elimina dallo storico
                            elimina_blocco_storico(i)
            
                            # 🧼 Poi elimina anche il tab vero e proprio (se esiste)
                            elimina_tab_blocco(row["Nome Blocco"])
            
                            st.success(f"✅ Blocco '{row['Nome Blocco']}' eliminato da storico e da Google Sheets.")
                        except Exception as e:
                            st.error(f"❌ Errore durante eliminazione: {e}")
                        finally:
                            st.session_state.pop(f"conferma_blocco_{i}", None)
                            st.rerun()

