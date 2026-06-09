import streamlit as st


st.set_page_config(
    page_title="Saída | Mapeamento Trendx",
    layout="wide",
    initial_sidebar_state="expanded",
)

exec(open("saida.py", encoding="utf-8").read())
