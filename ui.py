
# === ui.py ===
import streamlit as st
from config import DEFAULT_TEMPO_VISITA, DEFAULT_TEMPO_MASSIMO

def interfaccia():
    st.title("Costruttore di blocchi visite aziendali")
    csv_path = st.text_input("Percorso del file aziende_geocodificate.csv")
    json_path = st.text_input("Percorso del file matrice_durate.json")
    tempo_visita = st.number_input("Tempo visita per azienda (secondi)", value=DEFAULT_TEMPO_VISITA)
    tempo_massimo = st.number_input("Tempo massimo per blocco (secondi)", value=DEFAULT_TEMPO_MASSIMO)
    return csv_path, json_path, tempo_visita, tempo_massimo
