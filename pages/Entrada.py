import streamlit as st


st.set_page_config(
    page_title="Entrada | Mapeamento Trendx",
    layout="wide",
    initial_sidebar_state="expanded",
)

exec(open("entrada.py", encoding="utf-8").read())
