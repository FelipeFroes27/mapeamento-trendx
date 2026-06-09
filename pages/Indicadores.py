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


st.set_page_config(
    page_title="Indicadores | Mapeamento Trendx",
    layout="wide",
    initial_sidebar_state="expanded",
)

preparar_pagina(
    "Indicadores",
    "Painel amplo para acompanhar ocupação, concentração de estoque e classificação auxiliar dos itens.",
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


def ranking_por_coluna(df, coluna):
    if coluna not in df.columns:
        return pd.DataFrame(columns=[coluna, "Vagas", "Itens", "Quantidade"])

    df = df.copy()
    df[coluna] = df[coluna].fillna("").astype(str).str.strip().replace("", "Sem cadastro")

    return (
        df.groupby(coluna, dropna=False)
        .agg(
            Vagas=("Vaga", "nunique"),
            Itens=("Código", "count"),
            Quantidade=("Quantidade", "sum"),
        )
        .reset_index()
        .sort_values("Quantidade", ascending=False)
    )


def render_barras(titulo, subtitulo, df, coluna_nome, coluna_valor="Quantidade", limite=8):
    df = df.head(limite).copy()
    maximo = max(float(df[coluna_valor].max()), 1) if not df.empty else 1
    linhas = []

    for _, linha in df.iterrows():
        nome = escape(str(linha[coluna_nome]))
        valor = int(linha[coluna_valor])
        largura = max(int((valor / maximo) * 100), 2) if valor > 0 else 0
        linhas.append(
            f'<div class="bar-row">'
            f'<div class="bar-name" title="{nome}">{nome}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{largura}%;"></div></div>'
            f'<div class="bar-value">{numero(valor)}</div>'
            f'</div>'
        )

    conteudo = "".join(linhas) if linhas else '<div class="kpi-note">Sem dados para exibir.</div>'

    st.markdown(
        f'<div class="chart-panel">'
        f'<div class="panel-title">{escape(titulo)}</div>'
        f'<div class="panel-subtitle">{escape(subtitulo)}</div>'
        f'{conteudo}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_tabela(titulo, df, colunas, limite=18):
    linhas = []
    df = df.head(limite).copy()

    for _, linha in df.iterrows():
        celulas = []
        for coluna, alinhamento in colunas:
            valor = linha.get(coluna, "")
            classe = " class='num'" if alinhamento == "num" else ""
            celulas.append(f"<td{classe}>{escape(numero(valor) if alinhamento == 'num' else str(valor))}</td>")
        linhas.append("<tr>" + "".join(celulas) + "</tr>")

    cabecalho = "".join(
        f"<th{' class=\"num\"' if alinhamento == 'num' else ''}>{escape(coluna)}</th>"
        for coluna, alinhamento in colunas
    )
    corpo = "".join(linhas) if linhas else f"<tr><td colspan='{len(colunas)}'>Sem dados.</td></tr>"

    st.markdown(
        f'<div class="chart-panel">'
        f'<div class="panel-title">{escape(titulo)}</div>'
        f'<div class="table-scroll">'
        f'<table class="mini-table">'
        f'<thead><tr>{cabecalho}</tr></thead>'
        f'<tbody>{corpo}</tbody>'
        f'</table>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


df_posicao = carregar_dados_indicadores()
df_ocupado = produtos_ocupados(df_posicao)
resumo = resumo_vagas(df_posicao)

if st.button("Atualizar dados"):
    st.cache_data.clear()
    st.rerun()

k1, k2, k3, k4, k5 = st.columns(5)

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

col_ocupacao, col_status, col_top_vagas = st.columns([1.05, 1.05, 1.4], gap="medium")

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

with col_status:
    ranking_status = ranking_por_coluna(df_posicao, "Status")
    render_barras("Status das vagas", "Linhas da aba POSIÇÃO por status.", ranking_status, "Status", "Itens", 5)

with col_top_vagas:
    if df_ocupado.empty:
        st.markdown('<div class="chart-panel"><div class="panel-title">Top vagas</div><div class="kpi-note">Sem ocupação.</div></div>', unsafe_allow_html=True)
    else:
        ranking_vagas = (
            df_ocupado.groupby("Vaga")
            .agg(Itens=("Código", "count"), Quantidade=("Quantidade", "sum"))
            .reset_index()
            .sort_values("Quantidade", ascending=False)
        )
        render_barras("Top vagas por saldo", "Vagas com maior quantidade armazenada.", ranking_vagas, "Vaga", "Quantidade", 8)

if df_ocupado.empty:
    st.warning("Não há produtos ocupando vagas na aba POSIÇÃO.")
    st.stop()

ranking_categoria = ranking_por_coluna(df_ocupado, "Categoria")
ranking_tipo = ranking_por_coluna(df_ocupado, "Tipo")
ranking_marca = ranking_por_coluna(df_ocupado, "Marca")

col_cat, col_tipo, col_marca = st.columns(3, gap="medium")

with col_cat:
    render_barras("Categorias", "Saldo em peças por categoria auxiliar.", ranking_categoria, "Categoria", "Quantidade", 8)

with col_tipo:
    render_barras("Tipos", "Saldo em peças por tipo auxiliar.", ranking_tipo, "Tipo", "Quantidade", 8)

with col_marca:
    render_barras("Marcas", "Saldo em peças por marca auxiliar.", ranking_marca, "Marca", "Quantidade", 8)

top_produtos = (
    df_ocupado.groupby(["Código", "Descrição"], dropna=False)
    .agg(Vagas=("Vaga", "nunique"), Quantidade=("Quantidade", "sum"))
    .reset_index()
    .sort_values("Quantidade", ascending=False)
)

col_produtos, col_mapa = st.columns([1.05, 1.75], gap="medium")

with col_produtos:
    render_tabela(
        "Top produtos",
        top_produtos,
        [("Código", "txt"), ("Descrição", "txt"), ("Vagas", "num"), ("Quantidade", "num")],
        15,
    )

with col_mapa:
    colunas_mapa = [
        coluna
        for coluna in [
            "Vaga",
            "Status",
            "Código",
            "Descrição",
            "Quantidade",
            "Categoria",
            "Tipo",
            "Marca",
        ]
        if coluna in df_posicao.columns
    ]
    render_tabela("Mapa operacional", df_posicao[colunas_mapa], [(coluna, "num" if coluna == "Quantidade" else "txt") for coluna in colunas_mapa], 26)
