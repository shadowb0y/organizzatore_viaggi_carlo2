# === estrattore.py (aggiornato) ===
import fitz  # PyMuPDF
import pandas as pd
import re
from datetime import datetime
import os
import json

os.makedirs("output", exist_ok=True)

# === Costanti per filtri automatici ===
ID_VISITATI_FILE = "output/id_gia_visitati.json"
NOMI_ESCLUSI_FILE = "output/nomi_esclusi.json"

def rimuovi_date(testo):
    pattern_date = r'\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b\d{4}/\d{1,2}\b|\b\d{1,2}/\d{4}\b|\b\d{4}\b'
    return "; ".join([imp for imp in testo.split(";") if not re.search(pattern_date, imp)])

def estrai_dati_da_pdf(pdf_files, valore_minimo, data_limite):
    estratti = []

    for pdf_path in pdf_files:
        nome_file = os.path.basename(pdf_path).replace(".pdf", "")
        try:
            doc = fitz.open(pdf_path)
        except:
            print(f"Errore nell'aprire il file: {pdf_path}")
            continue

        for i, page in enumerate(doc):
            testo = page.get_text()

            # === Valore stimato ===
            valore_stimato = ""
            match_valore = re.search(r'Valore stimato\s+€?\s*([\d\.]+)', testo)
            if match_valore:
                valore_stimato = match_valore.group(1).replace(".", "")
            try:
                if valore_stimato and int(valore_stimato) < valore_minimo:
                    continue
            except:
                continue

            # === ID progetto ===
            id_match = re.search(r'ID Progetto\s+(\d+)', testo)
            id_progetto = id_match.group(1) if id_match else f"{nome_file}_pag_{i+1}"

            # === Fine lavori ===
            fine_lavori_match = re.search(r'Fine lavori\s+(\d{4})/(\d{2})', testo)
            if fine_lavori_match:
                anno, mese = int(fine_lavori_match.group(1)), int(fine_lavori_match.group(2))
                if datetime(anno, mese, 1).date() < data_limite:
                    continue

            # === Indirizzo ===
            indirizzo = ""
            match_indirizzo = re.search(r'([^\n]*\d{5} [^\n]*\(.*?\))', testo)
            if match_indirizzo:
                indirizzo = match_indirizzo.group(1).strip()

            # === Imprese ===
            imprese = []
            blocchi = testo.split("Appalto")
            for blocco in blocchi[1:]:
                righe = [r.strip() for r in blocco.strip().split("\n") if len(r.strip()) > 2]
                if righe:
                    imprese.append(righe[0])
            imprese_pulite = rimuovi_date("; ".join(imprese))

            estratti.append({
                "File": nome_file,
                "Pagina": i + 1,
                "ID Progetto": id_progetto,
                "Indirizzo": indirizzo,
                "Imprese": imprese_pulite,
                "Valore Stimato": valore_stimato
            })

    return pd.DataFrame(estratti)

def pulisci_unifica_filtra(df):
    # === Carica ID già visitati ===
    from google_sheets import leggi_id_visitati
    df_id_visitati = leggi_id_visitati()
    col_id = [c for c in df_id_visitati.columns if "id" in c.lower() and "progetto" in c.lower()]
    if col_id:
        id_da_escludere = set(df_id_visitati[col_id[0]].astype(str))
    else:
        id_da_escludere = set()
        print("⚠️ Nessuna colonna trovata per 'ID Progetto'")



    # === Carica nomi da escludere ===
    from google_sheets import leggi_nomi_esclusi

    try:
        df_nomi_esclusi = leggi_nomi_esclusi()
        nomi_da_escludere = set(df_nomi_esclusi["Nome"].dropna().str.lower().str.strip())
    except:
        nomi_da_escludere = set()

    final_rows = []
    for id_progetto, gruppo in df.groupby("ID Progetto"):
        indirizzi_validi = gruppo["Indirizzo"].dropna().loc[lambda x: x.str.strip() != ""]
        indirizzo_finale = indirizzi_validi.iloc[0] if not indirizzi_validi.empty else ""

        tutte_imprese = []
        for imp in gruppo["Imprese"]:
            if pd.notna(imp):
                tutte_imprese.extend([i.strip() for i in imp.split(";") if i.strip()])
        imprese_uniche = "; ".join(sorted(set(tutte_imprese)))

        valori_stimati_validi = gruppo["Valore Stimato"].dropna().loc[lambda x: x.str.strip() != ""]
        valore_stimato_finale = valori_stimati_validi.iloc[0] if not valori_stimati_validi.empty else ""

        final_rows.append({
            "ID Progetto": id_progetto,
            "File": gruppo["File"].iloc[0],
            "Indirizzo": indirizzo_finale,
            "Imprese": imprese_uniche,
            "Valore Stimato": valore_stimato_finale
        })

    df_finale = pd.DataFrame(final_rows)
    df_finale = df_finale[df_finale['Imprese'].str.strip() != '']

    # === Unione imprese su stesso indirizzo ===
    duplicati = df_finale[df_finale.duplicated(subset="Indirizzo", keep=False)].copy()
    mappa_unione = (
        duplicati.groupby("Indirizzo")["Imprese"]
        .apply(lambda x: " + ".join(sorted(set(str(i) for i in x.dropna()))))
        .to_dict()
    )

    df_unificato = df_finale.drop_duplicates(subset="Indirizzo", keep="first").copy()
    df_unificato["Imprese"] = df_unificato.apply(
        lambda row: mappa_unione[row["Indirizzo"]] if row["Indirizzo"] in mappa_unione else row["Imprese"],
        axis=1
    )

    # === Rimozione record generici ===
    df_unificato["Imprese_clean"] = df_unificato["Imprese"].str.lower().str.strip()
    frasi_da_escludere = ["nominativo al momento non dichiarato", "assegnato"]

    def contiene_solo_generiche(testo):
        elementi = [x.strip(" ()") for part in testo.split(";") for x in part.split("+")]
        elementi = [e for e in elementi if e]
        return all(e in frasi_da_escludere for e in elementi)

    mask_generici = df_unificato["Imprese_clean"].apply(contiene_solo_generiche)
    df_unificato["Indirizzo_clean"] = df_unificato["Indirizzo"].str.lower().str.strip()
    mask_inizia_con_cap = df_unificato["Indirizzo_clean"].str.match(r"^\d{5}\b")

    # === Rimozione per ID visitati ===
    mask_id_esclusi = df_unificato["ID Progetto"].astype(str).isin(id_da_escludere)

    # === Rimozione per nomi esclusi ===
    def contiene_nome_escluso(testo):
        if pd.isna(testo): return False
        for nome in nomi_da_escludere:
            if nome in testo.lower():
                return True
        return False

    mask_nome_escluso = df_unificato["Imprese"].apply(contiene_nome_escluso)

    # === Applica tutti i filtri
    mask_finale = ~(mask_generici | mask_inizia_con_cap | mask_id_esclusi | mask_nome_escluso)
    df_filtrato = df_unificato.loc[mask_finale].drop(columns=["Imprese_clean", "Indirizzo_clean"])

    return df_filtrato

def salva_csv(df, path="dati_corretti_aziende.csv"):
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"\u2705 File finale salvato come: {path}")
