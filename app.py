
# === app.py ===
import streamlit as st
from blocchi import genera_blocchi
from completamento import completa_blocchi
from mappa import genera_mappa
import os
import pandas as pd
from ui import interfaccia, interfaccia_pdf

sezione = st.sidebar.selectbox("Seleziona una sezione", [
    "Blocchi Visite Aziendali",
    "Estrazione PDF Appalti"
])

if sezione == "Blocchi Visite Aziendali":
    csv_path, json_path, tempo_visita, tempo_massimo = interfaccia()
    if st.button("Genera blocchi"):
        import os
        from blocchi import genera_blocchi
        from completamento import completa_blocchi
        from mappa import genera_mappa
        import pandas as pd

        if not os.path.exists(csv_path) or not os.path.exists(json_path):
            st.error("Verifica che i file esistano nei percorsi indicati.")
        else:
            df_blocchi = genera_blocchi(csv_path, json_path, tempo_visita, tempo_massimo)
            df_blocchi = completa_blocchi(df_blocchi, csv_path)
            html_path = genera_mappa(df_blocchi, csv_path)

            st.success("✅ Tutti i file generati con successo")
            st.dataframe(df_blocchi)

            st.download_button("Scarica CSV completo", data=df_blocchi.to_csv(index=False).encode('utf-8-sig'), file_name="blocco_completo.csv", mime="text/csv")
            with open("blocchi_multi_foglio.xlsx", "rb") as f:
                st.download_button("Scarica Excel multi-foglio", f, file_name="blocchi_multi_foglio.xlsx")
            with open(html_path, "rb") as f:
                st.download_button("Scarica mappa HTML", f, file_name="mappa_blocchi_senza_ritorno.html")

elif sezione == "Estrazione PDF Appalti":
    interfaccia_pdf()



if st.button("Genera blocchi"):
    if not os.path.exists(csv_path) or not os.path.exists(json_path):
        st.error("Verifica che i file esistano nei percorsi indicati.")
    else:
        df_blocchi = genera_blocchi(csv_path, json_path, tempo_visita, tempo_massimo)
        df_blocchi = completa_blocchi(df_blocchi, csv_path)
        html_path = genera_mappa(df_blocchi, csv_path)

        st.success("Tutti i file generati con successo")
        st.dataframe(df_blocchi)

        st.download_button("Scarica CSV completo", data=df_blocchi.to_csv(index=False).encode('utf-8-sig'), file_name="blocco_completo.csv", mime="text/csv")
        with open("blocchi_multi_foglio.xlsx", "rb") as f:
            st.download_button(" Scarica Excel multi-foglio", f, file_name="blocchi_multi_foglio.xlsx")
        with open(html_path, "rb") as f:
            st.download_button("Scarica mappa HTML", f, file_name="mappa_blocchi_senza_ritorno.html")




# import streamlit as st
# import pandas as pd
# import json
# import os
# import urllib.parse
# import folium
# from folium.plugins import MarkerCluster
# import random

# # === PARAMETRI ===
# DEFAULT_TEMPO_VISITA = 1200  # 20 minuti
# DEFAULT_TEMPO_MASSIMO = 86400 * 3  # 3 giorni

# # === INTERFACCIA ===
# st.title("Costruttore di blocchi visite aziendali")

# csv_path = st.text_input("Percorso del file aziende_geocodificate.csv")
# json_path = st.text_input("Percorso del file matrice_durate.json")

# tempo_visita = st.number_input("Tempo visita per azienda (secondi)", value=DEFAULT_TEMPO_VISITA)
# tempo_massimo = st.number_input("Tempo massimo per blocco (secondi)", value=DEFAULT_TEMPO_MASSIMO)

# # === INIZIALIZZA STATO ===
# if "file_generati" not in st.session_state:
#     st.session_state["file_generati"] = False

# # # === FUNZIONI ===
# # def genera_blocchi(csv_path, json_path, tempo_visita, tempo_massimo):
# #     df_aziende = pd.read_csv(csv_path, dtype={"ID Progetto": str})


# #     df_aziende = df_aziende.sort_values("ID Progetto").reset_index(drop=True)


# #     df_aziende = df_aziende.drop_duplicates(subset="Indirizzo", keep="first")

# #     valid_ids = df_aziende["ID Progetto"].tolist()
# #     id2idx = {k: i for i, k in enumerate(valid_ids)}
# #     idx2id = {i: k for k, i in id2idx.items()}
# #     N = len(valid_ids)

# #     with open(json_path, "r", encoding="utf-8") as f:
# #         raw = json.load(f)

# #     matrice = [[0] * N for _ in range(N)]
# #     for key, val in raw.items():
# #         if val is None:
# #             continue
# #         start, end = key.split(" -> ")
# #         if start in id2idx and end in id2idx:
# #             i, j = id2idx[start], id2idx[end]
# #             matrice[i][j] = val

# #     info_aziende = df_aziende.set_index("ID Progetto")[["Indirizzo", "Imprese"]].to_dict("index")

# #     non_visitati = set(valid_ids)
# #     blocchi = []
# #     blocco_corrente = []
# #     tempo_totale = 0

# #     while non_visitati:
# #         if not blocco_corrente:
# #             current = sorted(non_visitati)[0]
# #             non_visitati.remove(current)

# #             blocco_corrente = [current]
# #             tempo_totale = tempo_visita
# #         else:
# #             ultimo = blocco_corrente[-1]
# #             candidati = [(c, matrice[id2idx[ultimo]][id2idx[c]]) for c in non_visitati if matrice[id2idx[ultimo]][id2idx[c]] > 0]
# #             candidati.sort(key=lambda x: x[1])

# #             aggiunto = False
# #             for candidato, travel_time in candidati:
# #                 tempo_potenziale = tempo_totale + travel_time + tempo_visita
# #                 if tempo_potenziale <= tempo_massimo:
# #                     blocco_corrente.append(candidato)
# #                     tempo_totale = tempo_potenziale
# #                     non_visitati.remove(candidato)
# #                     aggiunto = True
# #                     break

# #             if not aggiunto:
# #                 blocchi.append(blocco_corrente)
# #                 blocco_corrente = []

# #     if blocco_corrente:
# #         blocchi.append(blocco_corrente)

# #     output_rows = []
# #     for i, blocco in enumerate(blocchi, start=1):
# #         tempo_cumulato = 0
# #         for ordine, id_ in enumerate(blocco, start=1):
# #             info = info_aziende.get(id_, {"Indirizzo": "", "Imprese": ""})
# #             output_rows.append({
# #                 "Blocco": i,
# #                 "Ordine": ordine,
# #                 "ID Progetto": id_,
# #                 "Indirizzo": info["Indirizzo"],
# #                 "Impresa": info["Imprese"],
# #                 "Tempo cumulato (s)": tempo_cumulato
# #             })
# #             if ordine < len(blocco):
# #                 next_id = blocco[ordine]
# #                 tempo_cumulato += matrice[id2idx[id_]][id2idx[next_id]] + tempo_visita

# #     df_blocchi = pd.DataFrame(output_rows)
# #     df_blocchi.to_csv("blocchi_senza_ritorno.csv", index=False, encoding="utf-8-sig")
# #     return df_blocchi


# def genera_blocchi(csv_path, json_path, tempo_visita, tempo_massimo):
#     progress_bar = st.progress(0)
#     status_text = st.empty()

#     import networkx as nx
#     from networkx.algorithms.approximation import traveling_salesman_problem, greedy_tsp

#     df_aziende = pd.read_csv(csv_path, dtype={"ID Progetto": str})
#     df_aziende = df_aziende.drop_duplicates(subset="Indirizzo", keep="first")
#     info_aziende = df_aziende.set_index("ID Progetto")[["Indirizzo", "Imprese"]].to_dict("index")

#     valid_ids = df_aziende["ID Progetto"].tolist()
#     id2idx = {k: i for i, k in enumerate(valid_ids)}
#     idx2id = {i: k for k, i in id2idx.items()}

#     with open(json_path, "r", encoding="utf-8") as f:
#         raw = json.load(f)

#     # === CREA GRAFO NON DIRETTO CON CONNESSIONI < 60 MIN ===
#     G = nx.Graph()
#     for key, val in raw.items():
#         if val is None or val >= 3600:
#             continue
#         start, end = key.split(" -> ")
#         if start in id2idx and end in id2idx:
#             G.add_edge(start, end, weight=val)

#     # Mantieni solo la componente connessa più grande
#     G = G.subgraph(max(nx.connected_components(G), key=len)).copy()

#     # Calcolo TSP greedy
#     tsp_path = traveling_salesman_problem(G, weight='weight', cycle=False, method=greedy_tsp)

#     # Rimuove duplicati
#     seen = set()
#     tsp_path = [x for x in tsp_path if not (x in seen or seen.add(x))]

#     # === DIVISIONE IN BLOCCHI ===
#     blocchi = []
#     blocco_corrente = []
#     tempo_totale = 0

#     for i in range(len(tsp_path)):
#         progress_bar.progress(i / len(tsp_path))
#         status_text.text(f"🚗 Elaborazione visita {i + 1} / {len(tsp_path)}")

#         current_id = tsp_path[i]
#         if not blocco_corrente:
#             blocco_corrente.append(current_id)
#             tempo_totale = tempo_visita
#         else:
#             prev_id = blocco_corrente[-1]
#             travel_time = G[prev_id][current_id]["weight"] if G.has_edge(prev_id, current_id) else 0
#             tempo_potenziale = tempo_totale + travel_time + tempo_visita
#             if tempo_potenziale <= tempo_massimo:
#                 blocco_corrente.append(current_id)
#                 tempo_totale = tempo_potenziale
#             else:
#                 blocchi.append(blocco_corrente)
#                 blocco_corrente = [current_id]
#                 tempo_totale = tempo_visita

#     if blocco_corrente:
#         blocchi.append(blocco_corrente)

#     # === COSTRUISCI RIGHE PER CSV ===
#     output_rows = []
#     for i, blocco in enumerate(blocchi, start=1):
#         tempo_cumulato = 0
#         for ordine, id_ in enumerate(blocco, start=1):
#             info = info_aziende.get(id_, {"Indirizzo": "", "Imprese": ""})
#             output_rows.append({
#                 "Blocco": i,
#                 "Ordine": ordine,
#                 "ID Progetto": id_,
#                 "Indirizzo": info["Indirizzo"],
#                 "Impresa": info["Imprese"],
#                 "Tempo cumulato (s)": tempo_cumulato
#             })
#             if ordine < len(blocco):
#                 next_id = blocco[ordine]
#                 if G.has_edge(id_, next_id):
#                     tempo_cumulato += G[id_][next_id]['weight'] + tempo_visita

#     df_blocchi = pd.DataFrame(output_rows)
#     df_blocchi.to_csv("blocchi_senza_ritorno.csv", index=False, encoding="utf-8-sig")
#     progress_bar.empty()
#     status_text.text("✅ Calcolo completato")

#     return df_blocchi











# def completa_blocchi(df_blocchi, csv_path):
#     df_geo = pd.read_csv(csv_path, dtype={"ID Progetto": str})
#     df_blocchi["ID Progetto"] = df_blocchi["ID Progetto"].astype(str)
#     df_geo["ID Progetto"] = df_geo["ID Progetto"].astype(str)

#     def trova_ultime_visite(df, limite_secondi):
#         risultati = []
#         for blocco, gruppo in df.groupby("Blocco"):
#             gruppo_valido = gruppo[gruppo["Tempo cumulato (s)"] <= limite_secondi]
#             if not gruppo_valido.empty:
#                 ultima_visita = gruppo_valido.iloc[-1]
#                 risultati.append({
#                     "Blocco": blocco,
#                     "Limite (s)": limite_secondi,
#                     "Tempo visita (s)": ultima_visita["Tempo cumulato (s)"],
#                     "ID Progetto": ultima_visita["ID Progetto"],
#                     "Indirizzo": ultima_visita["Indirizzo"]
#                 })
#         return pd.DataFrame(risultati)

#     otto_ore = trova_ultime_visite(df_blocchi, 26400)
#     sedici_ore = trova_ultime_visite(df_blocchi, 56400)
#     df_ultime = pd.merge(otto_ore, sedici_ore, on="Blocco", suffixes=("_8h", "_16h"))

#     df = df_blocchi.merge(df_geo[["ID Progetto", "Latitudine", "Longitudine"]], on="ID Progetto", how="left")

#     link_rows = []
#     for blocco, gruppo in df.groupby("Blocco"):
#         gruppo = gruppo.sort_values(by="Ordine")
#         punti = list(zip(gruppo["Latitudine"], gruppo["Longitudine"]))
#         for parte_idx in range(0, len(punti), 10):
#             current_punti = punti[parte_idx:parte_idx+10]
#             waypoints = "/".join([f"{lat},{lon}" for lat, lon in current_punti])
#             url = f"https://www.google.com/maps/dir/{urllib.parse.quote(waypoints)}"
#             link_rows.append({
#                 "Blocco": blocco,
#                 "Parte": (parte_idx // 10) + 1,
#                 "Link Google Maps": url
#             })

#     df_link = pd.DataFrame(link_rows)

#     df_blocchi["Parte"] = df_blocchi.groupby("Blocco").cumcount() // 10 + 1
#     df_blocchi = df_blocchi.merge(df_link, on=["Blocco", "Parte"], how="left")

#     ultime_id = df_ultime["ID Progetto_8h"].dropna().tolist() + df_ultime["ID Progetto_16h"].dropna().tolist()
#     df_blocchi["Ultima"] = df_blocchi["ID Progetto"].isin(ultime_id)
#     df_blocchi["Descrizione"] = ""

#     df_blocchi["Link Google Maps"] = df_blocchi.apply(
#         lambda row: f'=HYPERLINK("{row["Link Google Maps"]}", "Blocco {row["Blocco"]} Parte {row["Parte"]}")'
#         if pd.notnull(row["Link Google Maps"]) else "",
#         axis=1
#     )

#     df_blocchi["Ultima"] = df_blocchi["Ultima"].apply(lambda x: "ultima azienda da visitare" if x else "")
#     max_ordine_per_blocco = df_blocchi.groupby("Blocco")["Ordine"].max().sort_values(ascending=False)
#     nuovi_blocchi = {blocco: idx + 1 for idx, blocco in enumerate(max_ordine_per_blocco.index)}
#     df_blocchi["Blocco"] = df_blocchi["Blocco"].map(nuovi_blocchi)
#     df_blocchi = df_blocchi.sort_values(by=["Blocco", "Ordine"])

#     df_blocchi.to_csv("blocco_completo.csv", index=False, encoding="utf-8-sig")
#     with pd.ExcelWriter("blocchi_multi_foglio.xlsx", engine="openpyxl") as writer:
#         for blocco, df_b in df_blocchi.groupby("Blocco"):
#             df_b.to_excel(writer, sheet_name=f"Blocco_{blocco}", index=False)
#     return df_blocchi

# def genera_mappa(df_blocchi, csv_path):
#     df_geo = pd.read_csv(csv_path, dtype={"ID Progetto": str})
#     df_blocchi = df_blocchi.merge(df_geo[["ID Progetto", "Latitudine", "Longitudine"]], on="ID Progetto", how="left")
#     df_blocchi.dropna(subset=["Latitudine", "Longitudine"], inplace=True)
#     df_blocchi["Latitudine"] = df_blocchi["Latitudine"].astype(float)
#     df_blocchi["Longitudine"] = df_blocchi["Longitudine"].astype(float)

#     center_lat = df_blocchi["Latitudine"].mean()
#     center_lon = df_blocchi["Longitudine"].mean()
#     mappa = folium.Map(location=[center_lat, center_lon], zoom_start=9)
#     marker_cluster = MarkerCluster().add_to(mappa)

#     blocchi = sorted(df_blocchi["Blocco"].unique())
#     colori = {b: f'#{random.randint(0, 0xFFFFFF):06x}' for b in blocchi}

#     for _, row in df_blocchi.iterrows():
#         popup_text = f"""
#         <b>Blocco:</b> {row['Blocco']}<br>
#         <b>Ordine:</b> {row['Ordine']}<br>
#         <b>ID:</b> {row['ID Progetto']}<br>
#         <b>Impresa:</b> {row.get('Impresa', '')}<br>
#         <b>Indirizzo:</b> {row.get('Indirizzo', '')}<br>
#         <b>Tempo cumulato:</b> {round(row['Tempo cumulato (s)']/3600, 2)} h
#         """
#         folium.CircleMarker(
#             location=[row["Latitudine"], row["Longitudine"]],
#             radius=6,
#             popup=folium.Popup(popup_text, max_width=300),
#             color=colori[row["Blocco"]],
#             fill=True,
#             fill_opacity=0.9
#         ).add_to(marker_cluster)

#     mappa.save("mappa_blocchi_senza_ritorno.html")
#     return "mappa_blocchi_senza_ritorno.html"

# # === ESECUZIONE ===
# if st.button("Genera blocchi"):
#     if not os.path.exists(csv_path) or not os.path.exists(json_path):
#         st.error("⚠️ Verifica che i file esistano nei percorsi indicati.")
#     else:
#         df_blocchi = genera_blocchi(csv_path, json_path, tempo_visita, tempo_massimo)
#         df_blocchi = completa_blocchi(df_blocchi, csv_path)
#         html_path = genera_mappa(df_blocchi, csv_path)

#         st.success("✅ Tutti i file generati con successo")
#         st.dataframe(df_blocchi)

#         st.download_button("📥 Scarica CSV completo", data=df_blocchi.to_csv(index=False).encode('utf-8-sig'), file_name="blocco_completo.csv", mime="text/csv")
#         with open("blocchi_multi_foglio.xlsx", "rb") as f:
#             st.download_button("📥 Scarica Excel multi-foglio", f, file_name="blocchi_multi_foglio.xlsx")
#         with open(html_path, "rb") as f:
#             st.download_button("📥 Scarica mappa HTML", f, file_name="mappa_blocchi_senza_ritorno.html")
#         st.session_state["file_generati"] = True
