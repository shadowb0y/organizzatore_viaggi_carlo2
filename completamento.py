
# === completamento.py ===
import pandas as pd
import urllib.parse

def completa_blocchi(df_blocchi, csv_path):
    df_geo = pd.read_csv(csv_path, dtype={"ID Progetto": str})
    df_blocchi["ID Progetto"] = df_blocchi["ID Progetto"].astype(str)
    df_geo["ID Progetto"] = df_geo["ID Progetto"].astype(str)

    def trova_ultime_visite(df, limite_secondi):
        risultati = []
        for blocco, gruppo in df.groupby("Blocco"):
            gruppo_valido = gruppo[gruppo["Tempo cumulato (s)"] <= limite_secondi]
            if not gruppo_valido.empty:
                ultima_visita = gruppo_valido.iloc[-1]
                risultati.append({
                    "Blocco": blocco,
                    "Limite (s)": limite_secondi,
                    "Tempo visita (s)": ultima_visita["Tempo cumulato (s)"],
                    "ID Progetto": ultima_visita["ID Progetto"],
                    "Indirizzo": ultima_visita["Indirizzo"]
                })
        return pd.DataFrame(risultati)

    otto_ore = trova_ultime_visite(df_blocchi, 26400)
    sedici_ore = trova_ultime_visite(df_blocchi, 56400)
    df_ultime = pd.merge(otto_ore, sedici_ore, on="Blocco", suffixes=("_8h", "_16h"))

    df = df_blocchi.merge(df_geo[["ID Progetto", "Latitudine", "Longitudine"]], on="ID Progetto", how="left")

    link_rows = []
    for blocco, gruppo in df.groupby("Blocco"):
        gruppo = gruppo.sort_values(by="Ordine")
        punti = list(zip(gruppo["Latitudine"], gruppo["Longitudine"]))
        for parte_idx in range(0, len(punti), 10):
            current_punti = punti[parte_idx:parte_idx+10]
            waypoints = "/".join([f"{lat},{lon}" for lat, lon in current_punti])
            url = f"https://www.google.com/maps/dir/{urllib.parse.quote(waypoints)}"
            link_rows.append({
                "Blocco": blocco,
                "Parte": (parte_idx // 10) + 1,
                "Link Google Maps": url
            })

    df_link = pd.DataFrame(link_rows)
    df_blocchi["Parte"] = df_blocchi.groupby("Blocco").cumcount() // 10 + 1
    df_blocchi = df_blocchi.merge(df_link, on=["Blocco", "Parte"], how="left")

    ultime_id = df_ultime["ID Progetto_8h"].dropna().tolist() + df_ultime["ID Progetto_16h"].dropna().tolist()
    df_blocchi["Ultima"] = df_blocchi["ID Progetto"].isin(ultime_id)
    df_blocchi["Descrizione"] = ""

    df_blocchi["Link Google Maps"] = df_blocchi.apply(
        lambda row: f'=HYPERLINK("{row["Link Google Maps"]}", "Blocco {row["Blocco"]} Parte {row["Parte"]}")'
        if pd.notnull(row["Link Google Maps"]) else "",
        axis=1
    )

    df_blocchi["Ultima"] = df_blocchi["Ultima"].apply(lambda x: "ultima azienda da visitare" if x else "")
    max_ordine_per_blocco = df_blocchi.groupby("Blocco")["Ordine"].max().sort_values(ascending=False)
    nuovi_blocchi = {blocco: idx + 1 for idx, blocco in enumerate(max_ordine_per_blocco.index)}
    df_blocchi["Blocco"] = df_blocchi["Blocco"].map(nuovi_blocchi)
    df_blocchi = df_blocchi.sort_values(by=["Blocco", "Ordine"])

    df_blocchi.to_csv("output/blocco_completo.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter("output/blocchi_multi_foglio.xlsx", engine="openpyxl") as writer:
        for blocco, df_b in df_blocchi.groupby("Blocco"):
            df_b.to_excel(writer, sheet_name=f"Blocco_{blocco}", index=False)

    return df_blocchi
