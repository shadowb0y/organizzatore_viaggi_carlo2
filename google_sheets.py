

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json
import streamlit as st
import os

# === CONFIGURAZIONE GOOGLE SHEETS ===
SHEET_NAME = "streamlitorganizzazioneviaggi"
TAB_ID_VISITATI = "ID_Visitati"
TAB_NOMI_ESCLUSI = "Nomi_Esclusi"

def get_creds():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        return ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    except Exception as e:
        st.error("Errore nel caricamento delle credenziali dai secrets.")
        st.exception(e)

    if os.path.exists("creds.json"):
        return ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)

    raise FileNotFoundError("Credenziali non trovate.")



# === OTTIENI FOGLIO SPECIFICO ===
def get_worksheet(tab_name):
    creds = get_creds()
    client = gspread.authorize(creds)
    spreadsheet = client.open(SHEET_NAME)

    try:
        worksheet = spreadsheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=tab_name, rows="100", cols="3")
        if tab_name == "ID_Visitati":
            worksheet.append_row(["ID Progetto", "Data Salvataggio", "Note"])
        elif tab_name == "Nomi_Esclusi":
            worksheet.append_row(["Nome", "Data Salvataggio", "Note"])
        elif tab_name == "Storico_Blocchi":
            worksheet.append_row(["Nome Blocco", "Data Salvataggio", "N. Aziende"])
    return worksheet

# === GESTIONE ID VISITATI ===
def leggi_id_visitati():
    ws = get_worksheet(TAB_ID_VISITATI)
    records = ws.get_all_records()
    return pd.DataFrame(records)

def aggiungi_id_visitati(id_list, data, note):
    ws = get_worksheet(TAB_ID_VISITATI)
    for id_ in id_list:
        ws.append_row([id_, str(data), note])

def elimina_id_visitato(index):
    ws = get_worksheet(TAB_ID_VISITATI)
    ws.delete_rows(index + 2)

# === GESTIONE NOMI ESCLUSI ===
def leggi_nomi_esclusi():
    ws = get_worksheet(TAB_NOMI_ESCLUSI)
    records = ws.get_all_records()
    return pd.DataFrame(records)

def aggiungi_nomi_esclusi(lista_nomi, data, note):
    ws = get_worksheet(TAB_NOMI_ESCLUSI)
    for nome in lista_nomi:
        ws.append_row([nome, str(data), note])

def elimina_nome_escluso(index):
    ws = get_worksheet(TAB_NOMI_ESCLUSI)
    ws.delete_rows(index + 2)

# === GESTIONE BLOCCHI ===
def salva_blocco_su_google_sheets(df, nome_tab):
    ws = get_worksheet(nome_tab)
    ws.clear()

    df_clean = df.replace([float("inf"), float("-inf")], None).fillna("")
    ws.append_row(df_clean.columns.tolist())

    for row in df.itertuples(index=False):
        valori = ["" if (isinstance(c, float) and pd.isna(c)) else str(c) for c in row]
        ws.append_row(valori)

def registra_blocco_in_storico(nome, data, righe):
    ws = get_worksheet("Storico_Blocchi")
    ws.append_row([nome, data, righe])

def leggi_blocchi_salvati_su_google_sheets():
    ws = get_worksheet("Storico_Blocchi")
    records = ws.get_all_records()
    return pd.DataFrame(records)

def elimina_blocco_storico(index):
    ws = get_worksheet("Storico_Blocchi")
    ws.delete_rows(index + 2)

def elimina_tab_blocco(nome_tab):
    creds = get_creds()
    client = gspread.authorize(creds)
    spreadsheet = client.open(SHEET_NAME)

    try:
        worksheet = spreadsheet.worksheet(nome_tab)
        spreadsheet.del_worksheet(worksheet)
    except gspread.exceptions.WorksheetNotFound:
        pass
