from html import escape

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
from utils.ui import preparar_pagina


CORES = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#7c3aed", "#0891b2", "#4b5563"]


st.set_page_config(
    page_title="Indicadores | Mapeamento Trendx",
    layout="wide",
    initial_sidebar_state="expanded",
)

preparar_pagina(
    "Indicadores",
    "Painel amplo para acompanhar ocupação e composição do estoque.",
)


@st.cache_data(ttl=30)
def carregar_dados_indicadores():
    posicao = preparar_posicao(ler_aba("Mapeamento Trendx", "POSIÇÃO"))
    bd = preparar_bd_produtos(ler_aba("Mapeamento Trendx", "BD PRODUTOS"))
    posicao = enriquecer_posicao_com_bd(posicao, bd)
    return posicao


def numero(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "0"


def ranking_percentual(df, coluna, limite=6):
    if df.empty or coluna not in df.columns:
        return pd.DataFrame(columns=[coluna, "Quantidade", "Percentual"])

    ranking = (
        df.assign(**{coluna: df[coluna].fillna("").astype(str).str.strip().replace("", "Sem cadastro")})
        .groupby(coluna, dropna=False)
        .agg(Quantidade=("Quantidade", "sum"))
        .reset_index()
        .sort_values("Quantidade", ascending=False)
    )

    if len(ranking) > limite:
        top = ranking.head(limite - 1).copy()
        outros = pd.DataFrame(
            [{coluna: "Outros", "Quantidade": ranking.iloc[limite - 1 :]["Quantidade"].sum()}]
        )
        ranking = pd.concat([top, outros], ignore_index=True)

    total = max(float(ranking["Quantidade"].sum()), 1)
    ranking["Percentual"] = (ranking["Quantidade"] / total * 100).round(1)
    return ranking


def kpi_html(rotulo, valor, nota):
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{escape(str(rotulo))}</div>'
        f'<div class="kpi-value">{escape(numero(valor))}</div>'
        f'<div class="kpi-note">{escape(str(nota))}</div>'
        f'</div>'
    )


def donut_html(titulo, subtitulo, ranking, coluna):
    if ranking.empty:
        return f'<div class="chart-panel"><div class="panel-title">{escape(titulo)}</div><div class="kpi-note">Sem dados.</div></div>'

    inicio = 0
    segmentos = []
    legenda = []

    for indice, (_, linha) in enumerate(ranking.iterrows()):
        percentual = float(linha["Percentual"])
        fim = inicio + percentual
        cor = CORES[indice % len(CORES)]
        nome = escape(str(linha[coluna]))
        segmentos.append(f"{cor} {inicio:.1f}% {fim:.1f}%")
        legenda.append(
            f'<div class="legend-row">'
            f'<span class="legend-swatch" style="background:{cor};"></span>'
            f'<span class="legend-name" title="{nome}">{nome}</span>'
            f'<span>{percentual:.1f}%</span>'
            f'</div>'
        )
        inicio = fim

    return (
        f'<div class="chart-panel">'
        f'<div class="panel-title">{escape(titulo)}</div>'
        f'<div class="panel-subtitle">{escape(subtitulo)}</div>'
        f'<div class="donut-wrap">'
        f'<div class="donut" style="--donut-gradient: conic-gradient({", ".join(segmentos)});"></div>'
        f'<div>{"".join(legenda)}</div>'
        f'</div>'
        f'</div>'
    )


def barras_coloridas_html(titulo, subtitulo, ranking, coluna):
    if ranking.empty:
        return f'<div class="chart-panel"><div class="panel-title">{escape(titulo)}</div><div class="kpi-note">Sem dados.</div></div>'

    linhas = []
    for indice, (_, linha) in enumerate(ranking.iterrows()):
        cor = CORES[indice % len(CORES)]
        nome = escape(str(linha[coluna]))
        percentual = float(linha["Percentual"])
        linhas.append(
            f'<div class="bar-row">'
            f'<div class="bar-name" title="{nome}">{nome}</div>'
            f'<div class="bar-track"><div class="color-bar-fill" style="width:{max(percentual, 2)}%; background:{cor};"></div></div>'
            f'<div class="bar-value">{percentual:.1f}%</div>'
            f'</div>'
        )

    return (
        f'<div class="chart-panel">'
        f'<div class="panel-title">{escape(titulo)}</div>'
        f'<div class="panel-subtitle">{escape(subtitulo)}</div>'
        f'{"".join(linhas)}'
        f'</div>'
    )


df_posicao = carregar_dados_indicadores()
df_ocupado = produtos_ocupados(df_posicao)
resumo = resumo_vagas(df_posicao)

if st.button("Atualizar dados"):
    st.cache_data.clear()
    st.rerun()

st.markdown(
    '<div class="metric-grid">'
    + kpi_html("Vagas totais", resumo["total"], "Cadastradas em POSIÇÃO")
    + kpi_html("Ocupadas", resumo["ocupadas"], "Com produto e saldo")
    + kpi_html("Disponíveis", resumo["disponiveis"], "Sem produto em saldo")
    + kpi_html("Itens alocados", resumo["itens"], "Linhas ocupadas")
    + kpi_html("Saldo em peças", resumo["quantidade"], "Quantidade total")
    + '</div>',
    unsafe_allow_html=True,
)

if df_posicao.empty:
    st.warning("Não há dados na aba POSIÇÃO.")
    st.stop()

percentual_ocupado = int((resumo["ocupadas"] / resumo["total"]) * 100) if resumo["total"] else 0

ocupacao_html = (
    f'<div class="chart-panel">'
    f'<div class="panel-title">Ocupação geral</div>'
    f'<div class="panel-subtitle">Percentual de vagas ocupadas no mapa.</div>'
    f'<div class="split-bar" style="--ocupado:{percentual_ocupado}%;">'
    f'<div class="occupied"></div><div></div>'
    f'</div>'
    f'<div class="split-labels">'
    f'<span>{percentual_ocupado}% ocupado</span>'
    f'<span>{100 - percentual_ocupado}% disponível</span>'
    f'</div>'
    f'</div>'
)

st.markdown(
    '<div class="dashboard-grid wide">'
    + ocupacao_html
    + donut_html(
        "Estoque por categoria",
        "Participação percentual no saldo total.",
        ranking_percentual(df_ocupado, "Categoria"),
        "Categoria",
    )
    + '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="dashboard-grid two">'
    + donut_html(
        "Estoque por marca",
        "Participação percentual por marca.",
        ranking_percentual(df_ocupado, "Marca"),
        "Marca",
    )
    + donut_html(
        "Estoque por tipo",
        "Participação percentual por tipo.",
        ranking_percentual(df_ocupado, "Tipo"),
        "Tipo",
    )
    + '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="dashboard-grid two">'
    + barras_coloridas_html(
        "Ranking de categorias",
        "Distribuição percentual do saldo.",
        ranking_percentual(df_ocupado, "Categoria", limite=8),
        "Categoria",
    )
    + barras_coloridas_html(
        "Ranking de marcas",
        "Distribuição percentual do saldo.",
        ranking_percentual(df_ocupado, "Marca", limite=8),
        "Marca",
    )
    + '</div>',
    unsafe_allow_html=True,
)
