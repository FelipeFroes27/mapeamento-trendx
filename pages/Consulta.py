import pandas as pd
import streamlit as st

from utils.dados import (
    enriquecer_posicao_com_bd,
    preparar_bd_produtos,
    preparar_historico,
    preparar_posicao,
    produtos_ocupados,
)
from utils.sheets import ler_aba
from utils.ui import preparar_pagina


st.set_page_config(
    page_title="Consulta | Mapeamento Trendx",
    layout="wide",
    initial_sidebar_state="expanded",
)

preparar_pagina(
    "Consulta",
    "Consulte vagas, produtos em posição, histórico de movimentações e cadastro auxiliar do item.",
)


@st.cache_data(ttl=30)
def carregar_dados_consulta():
    posicao = preparar_posicao(ler_aba("Mapeamento Trendx", "POSIÇÃO"))
    historico = preparar_historico(ler_aba("Mapeamento Trendx", "HISTÓRICO"))
    bd = preparar_bd_produtos(ler_aba("Mapeamento Trendx", "BD PRODUTOS"))
    posicao = enriquecer_posicao_com_bd(posicao, bd)
    return posicao, historico, bd


df_posicao, df_historico, df_bd = carregar_dados_consulta()
df_ocupado = produtos_ocupados(df_posicao)

col_busca_1, col_busca_2, col_busca_3 = st.columns([1, 1, .55])

with col_busca_1:
    vaga = st.text_input("Vaga").strip().upper()

with col_busca_2:
    codigo = st.text_input("Código do produto").strip()

with col_busca_3:
    st.write("")
    st.write("")
    if st.button("Atualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

if not vaga and not codigo:
    st.info("Digite uma vaga, um código de produto ou ambos para consultar.")

if vaga:
    st.markdown('<div class="panel-title">Produtos da vaga</div>', unsafe_allow_html=True)
    df_vaga = df_posicao[df_posicao["Vaga"] == vaga].copy() if "Vaga" in df_posicao.columns else pd.DataFrame()

    if df_vaga.empty:
        st.warning("Vaga não encontrada na aba POSIÇÃO.")
    else:
        colunas_vaga = [
            coluna
            for coluna in [
                "Status",
                "Data",
                "Vaga",
                "Código",
                "Descrição",
                "Quantidade",
                "Categoria",
                "Tipo",
                "Marca",
                "Referência",
                "Observações",
            ]
            if coluna in df_vaga.columns
        ]
        st.dataframe(df_vaga[colunas_vaga], use_container_width=True, hide_index=True)

if codigo:
    st.markdown('<div class="panel-title">Informações do item</div>', unsafe_allow_html=True)

    df_item_posicao = df_ocupado[df_ocupado["Código"] == codigo].copy() if "Código" in df_ocupado.columns else pd.DataFrame()
    df_item_bd = df_bd[df_bd["Código"] == codigo].copy() if "Código" in df_bd.columns else pd.DataFrame()

    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Vagas com saldo", df_item_posicao["Vaga"].nunique() if not df_item_posicao.empty else 0)
    with k2:
        st.metric("Saldo total", int(df_item_posicao["Quantidade"].sum()) if "Quantidade" in df_item_posicao.columns else 0)
    with k3:
        st.metric("Movimentações", len(df_historico[df_historico["Código"] == codigo]) if "Código" in df_historico.columns else 0)

    if not df_item_bd.empty:
        colunas_bd = [
            coluna
            for coluna in ["Código", "Descrição", "Categoria", "Tipo", "Marca", "Grupo", "Subgrupo", "Referência"]
            if coluna in df_item_bd.columns
        ]
        st.dataframe(df_item_bd[colunas_bd].head(1), use_container_width=True, hide_index=True)
    else:
        st.warning("Produto não encontrado na aba auxiliar BD PRODUTOS.")

    if not df_item_posicao.empty:
        st.markdown('<div class="panel-title">Vagas onde o item está alocado</div>', unsafe_allow_html=True)
        colunas_item = [
            coluna
            for coluna in ["Vaga", "Status", "Data", "Descrição", "Quantidade", "Categoria", "Tipo", "Marca"]
            if coluna in df_item_posicao.columns
        ]
        st.dataframe(df_item_posicao[colunas_item], use_container_width=True, hide_index=True)

st.markdown('<div class="panel-title">Histórico</div>', unsafe_allow_html=True)
df_hist_filtrado = df_historico.copy()

if vaga and "Vaga" in df_hist_filtrado.columns:
    df_hist_filtrado = df_hist_filtrado[df_hist_filtrado["Vaga"] == vaga]

if codigo and "Código" in df_hist_filtrado.columns:
    df_hist_filtrado = df_hist_filtrado[df_hist_filtrado["Código"] == codigo]

if "_DataOrdenacao" in df_hist_filtrado.columns:
    df_hist_filtrado = df_hist_filtrado.sort_values("_DataOrdenacao", ascending=False)

colunas_historico = [
    coluna
    for coluna in ["Data", "Vaga", "Código", "Descrição", "Quantidade", "Usuário"]
    if coluna in df_hist_filtrado.columns
]

if df_hist_filtrado.empty:
    st.caption("Sem movimentações para os filtros informados.")
else:
    st.dataframe(df_hist_filtrado[colunas_historico], use_container_width=True, hide_index=True, height=420)
