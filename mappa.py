
# === mappa.py ===
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import random

def genera_mappa(df_blocchi, csv_path):
    df_geo = pd.read_csv(csv_path, dtype={"ID Progetto": str})
    df_blocchi = df_blocchi.merge(df_geo[["ID Progetto", "Latitudine", "Longitudine"]], on="ID Progetto", how="left")
    df_blocchi.dropna(subset=["Latitudine", "Longitudine"], inplace=True)
    df_blocchi["Latitudine"] = df_blocchi["Latitudine"].astype(float)
    df_blocchi["Longitudine"] = df_blocchi["Longitudine"].astype(float)

    center_lat = df_blocchi["Latitudine"].mean()
    center_lon = df_blocchi["Longitudine"].mean()
    mappa = folium.Map(location=[center_lat, center_lon], zoom_start=9)
    marker_cluster = MarkerCluster().add_to(mappa)

    blocchi = sorted(df_blocchi["Blocco"].unique())
    colori = {b: f'#{random.randint(0, 0xFFFFFF):06x}' for b in blocchi}

    for _, row in df_blocchi.iterrows():
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

    mappa.save("output/mappa_blocchi_senza_ritorno.html")
    return "output/mappa_blocchi_senza_ritorno.html"
