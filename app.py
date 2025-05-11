import streamlit as st
import pandas as pd
import json
import os
import urllib.parse
import folium
from folium.plugins import MarkerCluster
import random

# === PARAMETRI ===
DEFAULT_TEMPO_VISITA = 1200  # 20 minuti
DEFAULT_TEMPO_MASSIMO = 86400 * 3  # 3 giorni

# === INTERFACCIA ===
st.title("Costruttore di blocchi visite aziendali")

csv_path = st.text_input("Percorso del file aziende_geocodificate.csv")
json_path = st.text_input("Percorso del file matrice_durate.json")

tempo_visita = st.number_input("Tempo visita per azienda (secondi)", value=DEFAULT_TEMPO_VISITA)
tempo_massimo = st.number_input("Tempo massimo per blocco (secondi)", value=DEFAULT_TEMPO_MASSIMO)

if "file_generati" not in st.session_state:
    st.session_state["file_generati"] = False

if st.button("Genera blocchi"):
    if not os.path.exists(csv_path) or not os.path.exists(json_path):
        st.error("\u26a0\ufe0f Verifica che i file esistano nei percorsi indicati.")
    else:
        df = pd.read_csv(csv_path)
        df = df.drop_duplicates(subset="Indirizzo")
        progetti = df["ID Progetto"].astype(str).tolist()

        with open(json_path, "r", encoding="utf-8") as f:
            matrice_raw = json.load(f)

        n = len(progetti)
        matrice = [[0] * n for _ in range(n)]
        indice = {pid: idx for idx, pid in enumerate(progetti)}

        for k, v in matrice_raw.items():
            src, dst = k.split("->")
            if src in indice and dst in indice:
                matrice[indice[src]][indice[dst]] = v

        blocchi = []
        visitati = set()
        blocco_num = 1

        for start_idx in range(n):
            pid_start = progetti[start_idx]
            if pid_start in visitati:
                continue

            ordine = 1
            tempo_cumulato = 0
            blocco = []
            current_idx = start_idx

            while True:
                pid = progetti[current_idx]
                if pid in visitati:
                    break

                if tempo_cumulato + tempo_visita > tempo_massimo:
                    break

                visitati.add(pid)
                blocco.append({
                    "Blocco": blocco_num,
                    "Ordine": ordine,
                    "ID Progetto": pid,
                    "Indirizzo": df.loc[df["ID Progetto"] == int(pid), "Indirizzo"].values[0],
                    "Impresa": df.loc[df["ID Progetto"] == int(pid), "Imprese"].values[0],
                    "Tempo cumulato (s)": tempo_cumulato
                })
                ordine += 1
                tempo_cumulato += tempo_visita

                tempi = matrice[current_idx]
                best_idx = None
                best_tempo = float("inf")

                for i in range(n):
                    pid_i = progetti[i]
                    if pid_i not in visitati and tempo_cumulato + tempi[i] + tempo_visita <= tempo_massimo:
                        if tempi[i] < best_tempo:
                            best_idx = i
                            best_tempo = tempi[i]

                if best_idx is None:
                    break

                tempo_cumulato += best_tempo
                current_idx = best_idx

            blocchi.extend(blocco)
            blocco_num += 1

        df_blocchi = pd.DataFrame(blocchi)
        df_blocchi.to_csv("blocchi_senza_ritorno.csv", index=False, encoding="utf-8-sig")
        st.success("\u2705 File blocchi_senza_ritorno.csv generato")
        st.dataframe(df_blocchi)
        st.download_button("\ud83d\udcc5 Scarica blocchi", data=df_blocchi.to_csv(index=False).encode('utf-8-sig'), file_name="blocchi_senza_ritorno.csv", mime="text/csv")

        df_geo = pd.read_csv(csv_path)
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

        df_blocchi.to_csv("blocco_completo.csv", index=False, encoding="utf-8-sig")

        with pd.ExcelWriter("blocchi_multi_foglio.xlsx", engine="openpyxl") as writer:
            for blocco, df_b in df_blocchi.groupby("Blocco"):
                df_b.to_excel(writer, sheet_name=f"Blocco_{blocco}", index=False)

        st.success("\u2705 File salvati: blocco_completo.csv + blocchi_multi_foglio.xlsx")

        df_map = df_blocchi.merge(df_geo[["ID Progetto", "Latitudine", "Longitudine"]], on="ID Progetto", how="left")
        df_map.dropna(subset=["Latitudine", "Longitudine"], inplace=True)
        df_map["Latitudine"] = df_map["Latitudine"].astype(float)
        df_map["Longitudine"] = df_map["Longitudine"].astype(float)

        center_lat = df_map["Latitudine"].mean()
        center_lon = df_map["Longitudine"].mean()
        mappa = folium.Map(location=[center_lat, center_lon], zoom_start=9)
        marker_cluster = MarkerCluster().add_to(mappa)

        blocchi = sorted(df_map["Blocco"].unique())
        colori = {b: f'#{random.randint(0, 0xFFFFFF):06x}' for b in blocchi}

        for _, row in df_map.iterrows():
            popup_text = f"""
            <b>Blocco:</b> {row['Blocco']}<br>
            <b>Ordine:</b> {row['Ordine']}<br>
            <b>ID:</b> {row['ID Progetto']}<br>
            <b>Impresa:</b> {row.get('Impresa', '')}<br>
            <b>Indirizzo:</b> {row.get('Indirizzo', '')}<br>
            <b>Tempo cumulato:</b> {round(row['Tempo cumulato (s)']/3600, 2)} h
            """
            folium.CircleMarker(
                location=[row["Latitudine"], row["Longitudine"]],
                radius=6,
                popup=folium.Popup(popup_text, max_width=300),
                color=colori[row["Blocco"]],
                fill=True,
                fill_opacity=0.9
            ).add_to(marker_cluster)

        mappa.save("mappa_blocchi_senza_ritorno.html")
        st.success("\U0001f5fa\ufe0f Mappa salvata come: mappa_blocchi_senza_ritorno.html")
        st.session_state["file_generati"] = True

if st.session_state.get("file_generati", False):
    st.markdown("### \ud83d\udcc2 Scarica file generati")
    with open("blocco_completo.csv", "rb") as f:
        st.download_button("\ud83d\udcc5 Scarica blocco_completo.csv", f, file_name="blocco_completo.csv")

    with open("blocchi_multi_foglio.xlsx", "rb") as f:
        st.download_button("\ud83d\udcc5 Scarica blocchi_multi_foglio.xlsx", f, file_name="blocchi_multi_foglio.xlsx")

    with open("mappa_blocchi_senza_ritorno.html", "rb") as f:
        st.download_button("\ud83d\udcc5 Scarica mappa HTML", f, file_name="mappa_blocchi_senza_ritorno.html")
