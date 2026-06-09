from html import escape

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
    mobile=True,
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


def render_cards(df, titulo, colunas, limite=8):
    st.markdown(f'<div class="panel-title">{escape(titulo)}</div>', unsafe_allow_html=True)

    if df.empty:
        st.caption("Sem registros para exibir.")
        return

    for _, linha in df.head(limite).iterrows():
        titulo_card = " | ".join(str(linha.get(coluna, "")).strip() for coluna in colunas[:2] if str(linha.get(coluna, "")).strip())
        subtitulo = str(linha.get("Descrição", "")).strip()
        pills = []

        for coluna in colunas[2:]:
            valor = str(linha.get(coluna, "")).strip()
            if valor:
                pills.append(f'<span class="mobile-pill">{escape(coluna)}: {escape(valor)}</span>')

        st.markdown(
            f"""
            <div class="mobile-card">
                <div class="mobile-card-title">{escape(titulo_card or "Registro")}</div>
                <div class="mobile-card-subtitle">{escape(subtitulo)}</div>
                <div class="mobile-card-meta">{''.join(pills)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_tabela_compacta(titulo, df, colunas, limite=10):
    st.markdown(f'<div class="panel-title">{escape(titulo)}</div>', unsafe_allow_html=True)

    if df.empty:
        st.caption("Sem registros para exibir.")
        return

    cabecalho = "".join(f"<th>{escape(coluna)}</th>" for coluna in colunas)
    linhas = []

    for _, linha in df.head(limite).iterrows():
        celulas = "".join(f"<td>{escape(str(linha.get(coluna, '')))}</td>" for coluna in colunas)
        linhas.append(f"<tr>{celulas}</tr>")

    st.markdown(
        f"""
        <div class="table-scroll" style="max-height: 320px;">
            <table class="mini-table">
                <thead><tr>{cabecalho}</tr></thead>
                <tbody>{''.join(linhas)}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


vagas = []
if "Vaga" in df_posicao.columns:
    vagas = sorted(vaga for vaga in df_posicao["Vaga"].dropna().astype(str).str.strip().unique() if vaga)

vaga_opcao = st.selectbox(
    "Vaga",
    [""] + vagas,
    format_func=lambda valor: "Selecione ou digite para buscar..." if valor == "" else valor,
)
vaga = str(vaga_opcao).strip().upper()

codigo = st.text_input("Código do produto").strip()

if st.button("Atualizar", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

if not vaga and not codigo:
    st.info("Digite uma vaga, um código de produto ou ambos para consultar.")

if vaga:
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
        render_cards("Produtos da vaga", df_vaga[colunas_vaga], ["Código", "Quantidade", "Status", "Categoria", "Tipo", "Marca", "Referência"])

if codigo:
    st.markdown('<div class="panel-title">Informações do item</div>', unsafe_allow_html=True)

    df_item_posicao = df_ocupado[df_ocupado["Código"] == codigo].copy() if "Código" in df_ocupado.columns else pd.DataFrame()
    df_item_bd = df_bd[df_bd["Código"] == codigo].copy() if "Código" in df_bd.columns else pd.DataFrame()

    vagas_saldo = df_item_posicao["Vaga"].nunique() if not df_item_posicao.empty else 0
    saldo_total = int(df_item_posicao["Quantidade"].sum()) if "Quantidade" in df_item_posicao.columns else 0
    movimentacoes = len(df_historico[df_historico["Código"] == codigo]) if "Código" in df_historico.columns else 0

    st.markdown(
        f"""
        <div class="insight-grid" style="grid-template-columns: 1fr;">
            <div class="insight">
                <div class="insight-label">Resumo do item</div>
                <div class="insight-value">{escape(str(vagas_saldo))} vaga(s) | {escape(str(saldo_total))} peças</div>
                <div class="kpi-note">{escape(str(movimentacoes))} movimentação(ões) no histórico</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not df_item_bd.empty:
        colunas_bd = [
            coluna
            for coluna in ["Código", "Descrição", "Categoria", "Tipo", "Marca", "Grupo", "Subgrupo", "Referência"]
            if coluna in df_item_bd.columns
        ]
        render_cards("Cadastro auxiliar", df_item_bd[colunas_bd].head(1), ["Código", "Marca", "Categoria", "Tipo", "Grupo", "Subgrupo", "Referência"])
    else:
        st.warning("Produto não encontrado na aba auxiliar BD PRODUTOS.")

    if not df_item_posicao.empty:
        colunas_item = [
            coluna
            for coluna in ["Vaga", "Status", "Data", "Descrição", "Quantidade", "Categoria", "Tipo", "Marca"]
            if coluna in df_item_posicao.columns
        ]
        render_cards("Vagas onde o item está alocado", df_item_posicao[colunas_item], ["Vaga", "Quantidade", "Status", "Categoria", "Tipo", "Marca", "Data"])

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
    st.markdown('<div class="panel-title">Histórico</div>', unsafe_allow_html=True)
    st.caption("Sem movimentações para os filtros informados.")
else:
    render_tabela_compacta("Histórico", df_hist_filtrado[colunas_historico], colunas_historico, 20)
