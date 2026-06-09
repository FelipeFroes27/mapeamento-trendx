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
from utils.ui import preparar_pagina, render_kpi


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


def render_donut(titulo, subtitulo, ranking, coluna):
    if ranking.empty:
        st.markdown(
            f'<div class="chart-panel"><div class="panel-title">{escape(titulo)}</div><div class="kpi-note">Sem dados.</div></div>',
            unsafe_allow_html=True,
        )
        return

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

    st.markdown(
        f'<div class="chart-panel">'
        f'<div class="panel-title">{escape(titulo)}</div>'
        f'<div class="panel-subtitle">{escape(subtitulo)}</div>'
        f'<div class="donut-wrap">'
        f'<div class="donut" style="--donut-gradient: conic-gradient({", ".join(segmentos)});"></div>'
        f'<div>{"".join(legenda)}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_barras_coloridas(titulo, subtitulo, ranking, coluna):
    if ranking.empty:
        st.markdown(
            f'<div class="chart-panel"><div class="panel-title">{escape(titulo)}</div><div class="kpi-note">Sem dados.</div></div>',
            unsafe_allow_html=True,
        )
        return

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

    st.markdown(
        f'<div class="chart-panel">'
        f'<div class="panel-title">{escape(titulo)}</div>'
        f'<div class="panel-subtitle">{escape(subtitulo)}</div>'
        f'{"".join(linhas)}'
        f'</div>',
        unsafe_allow_html=True,
    )


df_posicao = carregar_dados_indicadores()
df_ocupado = produtos_ocupados(df_posicao)
resumo = resumo_vagas(df_posicao)

if st.button("Atualizar dados"):
    st.cache_data.clear()
    st.rerun()

k1, k2, k3, k4, k5 = st.columns(5, gap="small")

with k1:
    render_kpi("Vagas totais", resumo["total"], "Cadastradas em POSIÇÃO")
with k2:
    render_kpi("Ocupadas", resumo["ocupadas"], "Com produto e saldo")
with k3:
    render_kpi("Disponíveis", resumo["disponiveis"], "Sem produto em saldo")
with k4:
    render_kpi("Itens alocados", resumo["itens"], "Linhas ocupadas")
with k5:
    render_kpi("Saldo em peças", resumo["quantidade"], "Quantidade total")

if df_posicao.empty:
    st.warning("Não há dados na aba POSIÇÃO.")
    st.stop()

percentual_ocupado = int((resumo["ocupadas"] / resumo["total"]) * 100) if resumo["total"] else 0

col_ocupacao, col_categoria = st.columns([1, 1.45], gap="small")

with col_ocupacao:
    st.markdown(
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
        f'</div>',
        unsafe_allow_html=True,
    )

with col_categoria:
    render_donut(
        "Estoque por categoria",
        "Participação percentual no saldo total.",
        ranking_percentual(df_ocupado, "Categoria"),
        "Categoria",
    )

col_marca, col_tipo = st.columns(2, gap="small")

with col_marca:
    render_donut(
        "Estoque por marca",
        "Participação percentual por marca.",
        ranking_percentual(df_ocupado, "Marca"),
        "Marca",
    )

with col_tipo:
    render_donut(
        "Estoque por tipo",
        "Participação percentual por tipo.",
        ranking_percentual(df_ocupado, "Tipo"),
        "Tipo",
    )

col_barras_categoria, col_barras_marca = st.columns(2, gap="small")

with col_barras_categoria:
    render_barras_coloridas(
        "Ranking de categorias",
        "Distribuição percentual do saldo.",
        ranking_percentual(df_ocupado, "Categoria", limite=8),
        "Categoria",
    )

with col_barras_marca:
    render_barras_coloridas(
        "Ranking de marcas",
        "Distribuição percentual do saldo.",
        ranking_percentual(df_ocupado, "Marca", limite=8),
        "Marca",
    )
