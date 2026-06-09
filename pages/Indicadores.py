import pandas as pd
import streamlit as st

from utils.dados import (
    enriquecer_posicao_com_bd,
    preparar_bd_produtos,
    preparar_posicao,
    produtos_ocupados,
    resumo_vagas,
)
from utils.sheets import ler_aba
from utils.ui import preparar_pagina, render_kpi


st.set_page_config(
    page_title="Indicadores | Mapeamento Trendx",
    layout="wide",
    initial_sidebar_state="expanded",
)

preparar_pagina(
    "Indicadores",
    "Leitura da ocupação logística com classificação auxiliar por categoria, tipo e marca.",
)


@st.cache_data(ttl=30)
def carregar_dados_indicadores():
    posicao = preparar_posicao(ler_aba("Mapeamento Trendx", "POSIÇÃO"))
    bd = preparar_bd_produtos(ler_aba("Mapeamento Trendx", "BD PRODUTOS"))
    posicao = enriquecer_posicao_com_bd(posicao, bd)
    return posicao


df_posicao = carregar_dados_indicadores()
df_ocupado = produtos_ocupados(df_posicao)
resumo = resumo_vagas(df_posicao)

if st.button("Atualizar dados", use_container_width=False):
    st.cache_data.clear()
    st.rerun()

k1, k2, k3, k4 = st.columns(4)

with k1:
    render_kpi("Vagas totais", resumo["total"], "Vagas cadastradas na aba POSIÇÃO")
with k2:
    render_kpi("Ocupadas", resumo["ocupadas"], "Vagas com produto e saldo")
with k3:
    render_kpi("Disponíveis", resumo["disponiveis"], "Total menos vagas ocupadas")
with k4:
    render_kpi("Saldo em peças", resumo["quantidade"], "Soma das quantidades em posição")

st.divider()

if df_ocupado.empty:
    st.warning("Não há produtos ocupando vagas na aba POSIÇÃO.")
    st.stop()


def ranking_por_coluna(df, coluna):
    if coluna not in df.columns:
        return pd.DataFrame(columns=[coluna, "Vagas", "Itens", "Quantidade"])

    ranking = (
        df.assign(**{coluna: df[coluna].fillna("").replace("", "Sem cadastro")})
        .groupby(coluna, dropna=False)
        .agg(
            Vagas=("Vaga", "nunique"),
            Itens=("Código", "count"),
            Quantidade=("Quantidade", "sum"),
        )
        .reset_index()
        .sort_values("Quantidade", ascending=False)
    )
    return ranking


aba_categoria, aba_tipo, aba_marca = st.tabs(["Categoria", "Tipo", "Marca"])

with aba_categoria:
    ranking = ranking_por_coluna(df_ocupado, "Categoria")
    st.bar_chart(ranking.set_index("Categoria")["Quantidade"])
    st.dataframe(ranking, use_container_width=True, hide_index=True)

with aba_tipo:
    ranking = ranking_por_coluna(df_ocupado, "Tipo")
    st.bar_chart(ranking.set_index("Tipo")["Quantidade"])
    st.dataframe(ranking, use_container_width=True, hide_index=True)

with aba_marca:
    ranking = ranking_por_coluna(df_ocupado, "Marca")
    st.bar_chart(ranking.set_index("Marca")["Quantidade"])
    st.dataframe(ranking, use_container_width=True, hide_index=True)

st.markdown('<div class="panel-title">Mapa operacional</div>', unsafe_allow_html=True)
colunas_mapa = [
    coluna
    for coluna in [
        "Vaga",
        "Status",
        "Data",
        "Código",
        "Descrição",
        "Quantidade",
        "Categoria",
        "Tipo",
        "Marca",
        "Referência",
        "Observações",
    ]
    if coluna in df_posicao.columns
]

st.dataframe(df_posicao[colunas_mapa], use_container_width=True, hide_index=True, height=520)
