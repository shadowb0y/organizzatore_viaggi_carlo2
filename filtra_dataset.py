# === filtra_dataset.py ===
import pandas as pd
import json

import os
os.makedirs("output", exist_ok=True)

def filtra_dati(input_csv_filtrato, input_csv_geo, input_matrice_json, output_csv_geo, output_matrice_json):
    # === CARICA CSV CON ID FILTRATI ===
    df_filtrato = pd.read_csv(input_csv_filtrato, dtype=str)
    id_validi = set(df_filtrato["ID Progetto"].astype(str))

    # === FILTRA CSV GEOCODIFICATO ===
    df_geo = pd.read_csv(input_csv_geo, dtype=str)
    df_geo_filtrato = df_geo[df_geo["ID Progetto"].astype(str).isin(id_validi)]
    df_geo_filtrato.to_csv(output_csv_geo, index=False, encoding="utf-8-sig")

    # === FILTRA MATRICE DURATE ===
    with open(input_matrice_json, "r", encoding="utf-8") as f:
        matrice = json.load(f)

    matrice_filtrata = {
        k: v for k, v in matrice.items()
        if all(elem in id_validi for elem in k.split(" -> "))
    }

    with open(output_matrice_json, "w", encoding="utf-8") as f:
        json.dump(matrice_filtrata, f, ensure_ascii=False, indent=2)

    return df_geo_filtrato, matrice_filtrata