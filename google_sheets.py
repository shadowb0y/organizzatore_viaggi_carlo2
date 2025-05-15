import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# === CONFIGURAZIONE GOOGLE SHEETS ===
SHEET_NAME = "streamlitorganizzazioneviaggi"
TAB_ID_VISITATI = "ID_Visitati"

# === SETUP CONNESSIONE ===
def get_worksheet(tab_name):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(".streamlit/creds.json", scope)

    client = gspread.authorize(creds)

    spreadsheet = client.open(SHEET_NAME)
    try:
        worksheet = spreadsheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=tab_name, rows="100", cols="3")
        worksheet.append_row(["ID Progetto", "Data", "Note"])
    return worksheet

def leggi_id_visitati():
    ws = get_worksheet(TAB_ID_VISITATI)
    records = ws.get_all_records()
    return pd.DataFrame(records)

def aggiungi_id_visitati(id_list, data, note):
    ws = get_worksheet(TAB_ID_VISITATI)
    for id_ in id_list:
        ws.append_row([id_, str(data), note])
        
def elimina_id_visitato(index):
    ws = get_worksheet("ID_Visitati")
    ws.delete_rows(index + 2)  # +2 perché gspread è 1-based e c'è header


TAB_NOMI_ESCLUSI = "Nomi_Esclusi"

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
    ws.delete_rows(index + 2)  # +2 perché header e 1-based

def salva_blocco_su_google_sheets(df, nome_tab):
    ws = get_worksheet(nome_tab)
    ws.clear()

    # ✅ Rimuove valori non compatibili con JSON (come NaN, inf, -inf)
    df_clean = df.replace([float("inf"), float("-inf")], None)
    df_clean = df_clean.fillna("")

    ws.append_row(df_clean.columns.tolist())
    for row in df_clean.itertuples(index=False):
        ws.append_row(list(row))

def registra_blocco_in_storico(nome, data, righe):
    ws = get_worksheet("Storico_Blocchi")
    ws.append_row([nome, data, righe])
