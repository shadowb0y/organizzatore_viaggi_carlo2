
# === blocchi.py ===
import pandas as pd
import json
import streamlit as st
import networkx as nx
from networkx.algorithms.approximation import traveling_salesman_problem, greedy_tsp

def genera_blocchi(csv_path, json_path, tempo_visita, tempo_massimo):
    progress_bar = st.progress(0)
    status_text = st.empty()

    df_aziende = pd.read_csv(csv_path, dtype={"ID Progetto": str})
    df_aziende = df_aziende.drop_duplicates(subset="Indirizzo", keep="first")
    info_aziende = df_aziende.set_index("ID Progetto")[["Indirizzo", "Imprese"]].to_dict("index")

    valid_ids = df_aziende["ID Progetto"].tolist()
    id2idx = {k: i for i, k in enumerate(valid_ids)}

    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    G = nx.Graph()
    for key, val in raw.items():
        if val is None or val >= 3600:
            continue
        start, end = key.split(" -> ")
        if start in id2idx and end in id2idx:
            G.add_edge(start, end, weight=val)

    G = G.subgraph(max(nx.connected_components(G), key=len)).copy()
    tsp_path = traveling_salesman_problem(G, weight='weight', cycle=False, method=greedy_tsp)
    seen = set()
    tsp_path = [x for x in tsp_path if not (x in seen or seen.add(x))]

    blocchi = []
    blocco_corrente = []
    tempo_totale = 0

    for i in range(len(tsp_path)):
        progress_bar.progress(i / len(tsp_path))
        status_text.text(f"Elaborazione visita {i + 1} / {len(tsp_path)}")

        current_id = tsp_path[i]
        if not blocco_corrente:
            blocco_corrente.append(current_id)
            tempo_totale = tempo_visita
        else:
            prev_id = blocco_corrente[-1]
            travel_time = G[prev_id][current_id]["weight"] if G.has_edge(prev_id, current_id) else 0
            tempo_potenziale = tempo_totale + travel_time + tempo_visita
            if tempo_potenziale <= tempo_massimo:
                blocco_corrente.append(current_id)
                tempo_totale = tempo_potenziale
            else:
                blocchi.append(blocco_corrente)
                blocco_corrente = [current_id]
                tempo_totale = tempo_visita

    if blocco_corrente:
        blocchi.append(blocco_corrente)

    output_rows = []
    for i, blocco in enumerate(blocchi, start=1):
        tempo_cumulato = 0
        for ordine, id_ in enumerate(blocco, start=1):
            info = info_aziende.get(id_, {"Indirizzo": "", "Imprese": ""})
            output_rows.append({
                "Blocco": i,
                "Ordine": ordine,
                "ID Progetto": id_,
                "Indirizzo": info["Indirizzo"],
                "Impresa": info["Imprese"],
                "Tempo cumulato (s)": tempo_cumulato
            })
            if ordine < len(blocco):
                next_id = blocco[ordine]
                if G.has_edge(id_, next_id):
                    tempo_cumulato += G[id_][next_id]['weight'] + tempo_visita

    df_blocchi = pd.DataFrame(output_rows)
    df_blocchi.to_csv("blocchi_senza_ritorno.csv", index=False, encoding="utf-8-sig")
    progress_bar.empty()
    status_text.text("Calcolo completato")
    return df_blocchi
