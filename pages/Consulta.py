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
from utils.etiquetas_movimentacao import (
    COPIAS_MAXIMO,
    copias_por_quantidade,
    montar_item,
    preparar_etiquetas,
    render_painel_etiquetas,
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
    "Busque por vaga, código, descrição ou referência para ver posições e histórico.",
    mobile=True,
    pagina="consulta",
)


@st.cache_data(ttl=30)
def carregar_dados_consulta():
    posicao = preparar_posicao(ler_aba("Mapeamento Trendx", "POSIÇÃO"))
    historico = preparar_historico(ler_aba("Mapeamento Trendx", "HISTÓRICO"))
    bd = preparar_bd_produtos(ler_aba("Mapeamento Trendx", "BD PRODUTOS"))
    posicao = enriquecer_posicao_com_bd(posicao, bd)
    return posicao, historico, bd


def texto(valor):
    if pd.isna(valor):
        return ""
    return str(valor).strip()


def contem(serie, termo):
    if not termo:
        return pd.Series([True] * len(serie), index=serie.index)
    return serie.fillna("").astype(str).str.upper().str.contains(termo.upper(), regex=False)


def render_cards(titulo, df, limite=12):
    st.markdown(f'<div class="panel-title">{escape(titulo)}</div>', unsafe_allow_html=True)

    if df.empty:
        st.caption("Sem registros para exibir.")
        return

    for _, linha in df.head(limite).iterrows():
        codigo = texto(linha.get("Código"))
        vaga = texto(linha.get("Vaga"))
        descricao = texto(linha.get("Descrição"))
        quantidade = texto(linha.get("Quantidade"))

        pills = []
        for coluna in ["Status", "Categoria", "Tipo", "Marca", "Referência", "Data", "Observações"]:
            valor = texto(linha.get(coluna))
            if valor:
                pills.append(f'<span class="mobile-pill">{escape(coluna)}: {escape(valor)}</span>')

        st.markdown(
            f'<div class="mobile-card">'
            f'<div class="mobile-card-title">{escape(vaga)} | {escape(codigo)} | Qtd: {escape(quantidade)}</div>'
            f'<div class="mobile-card-subtitle">{escape(descricao)}</div>'
            f'<div class="mobile-card-meta">{"".join(pills)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def render_etiquetas_vaga(vaga, df_vaga):
    """Reimpressão das etiquetas dos produtos que estão na vaga."""
    st.markdown('<div class="panel-title">Etiquetas da vaga</div>', unsafe_allow_html=True)

    pacote = st.session_state.get("consulta_etiquetas")
    if pacote and pacote["vaga"] != vaga:
        st.session_state.pop("consulta_etiquetas", None)
        pacote = None

    if pacote:
        render_painel_etiquetas("consulta_etiquetas")
        if st.button("Imprimir outra vez", use_container_width=True, key="consulta_nova_impressao"):
            st.session_state.pop("consulta_etiquetas", None)
            st.rerun()
        return

    produtos = []
    sem_codigo = []
    for _, linha in df_vaga.iterrows():
        codigo_item = texto(linha.get("Código")).upper()
        # Placeholder como "SC" (ocupado com máquina grande) não tem etiqueta
        if codigo_item.isdigit():
            produtos.append(linha)
        elif codigo_item:
            sem_codigo.append(codigo_item)

    if sem_codigo:
        st.caption("Sem etiqueta (não é código de produto): " + ", ".join(sorted(set(sem_codigo))))

    if not produtos:
        st.caption("Nenhum produto com código nesta vaga.")
        return

    usuario_etiqueta = st.text_input("Usuário", key="consulta_usuario").strip().upper()

    with st.expander("Ajustar cópias"):
        copias = [
            int(
                st.number_input(
                    f'{texto(linha.get("Código"))} - {texto(linha.get("Descrição"))}',
                    min_value=1,
                    max_value=COPIAS_MAXIMO,
                    value=copias_por_quantidade(linha.get("Quantidade")),
                    step=1,
                    key=f"consulta_copias_{vaga}_{indice}",
                )
            )
            for indice, linha in enumerate(produtos)
        ]

    if st.button(
        f"Imprimir etiquetas da vaga ({sum(copias)})",
        type="primary",
        use_container_width=True,
        key="consulta_imprimir",
    ):
        if not usuario_etiqueta:
            st.error("Digite o usuário")
            return

        itens = []
        for linha, qtd in zip(produtos, copias):
            item = montar_item(
                linha.get("Código"),
                texto(linha.get("Descrição")),
                texto(linha.get("Referencia")),
                qtd,
            )
            itens.append(item)

        preparar_etiquetas(
            "consulta_etiquetas",
            f"Etiquetas da vaga {vaga} enviadas para a impressora.",
            itens,
            "REIMPRESSÃO (CONSULTA)",
            vaga,
            usuario_etiqueta,
        )
        st.rerun()


def render_historico(df, limite=20):
    st.markdown('<div class="panel-title">Histórico</div>', unsafe_allow_html=True)

    if df.empty:
        st.caption("Sem movimentações para os filtros informados.")
        return

    for _, linha in df.head(limite).iterrows():
        quantidade = texto(linha.get("Quantidade"))
        sinal = "Entrada" if quantidade and not quantidade.startswith("-") else "Saída"
        st.markdown(
            f'<div class="mobile-card">'
            f'<div class="mobile-card-title">{escape(sinal)} | {escape(texto(linha.get("Vaga")))} | {escape(texto(linha.get("Código")))}</div>'
            f'<div class="mobile-card-subtitle">{escape(texto(linha.get("Descrição")))}</div>'
            f'<div class="mobile-card-meta">'
            f'<span class="mobile-pill">Qtd: {escape(quantidade)}</span>'
            f'<span class="mobile-pill">Data: {escape(texto(linha.get("Data")))}</span>'
            f'<span class="mobile-pill">Usuário: {escape(texto(linha.get("Usuário")))}</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


df_posicao, df_historico, df_bd = carregar_dados_consulta()
df_ocupado = produtos_ocupados(df_posicao)

vagas = []
if "Vaga" in df_posicao.columns:
    vagas = sorted(vaga for vaga in df_posicao["Vaga"].dropna().astype(str).str.strip().unique() if vaga)

codigos = []
if "Código" in df_posicao.columns:
    codigos = sorted(codigo for codigo in df_posicao["Código"].dropna().astype(str).str.strip().unique() if codigo)

descricoes = []
if "Descrição" in df_posicao.columns:
    descricoes = sorted(descricao for descricao in df_posicao["Descrição"].dropna().astype(str).str.strip().unique() if descricao)

referencias = []
if "Referência" in df_posicao.columns:
    referencias = sorted(referencia for referencia in df_posicao["Referência"].dropna().astype(str).str.strip().unique() if referencia)

vaga_opcao = st.selectbox(
    "Vaga",
    [""] + vagas,
    format_func=lambda valor: "Todas" if valor == "" else valor,
)

codigo_opcao = st.selectbox(
    "Código",
    [""] + codigos,
    format_func=lambda valor: "Todos" if valor == "" else valor,
)

descricao_opcao = st.selectbox(
    "Descrição",
    [""] + descricoes,
    format_func=lambda valor: "Todas" if valor == "" else valor,
)

referencia_opcao = st.selectbox(
    "Referência",
    [""] + referencias,
    format_func=lambda valor: "Todas" if valor == "" else valor,
)

if st.button("Atualizar", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

vaga = texto(vaga_opcao).upper()
codigo = texto(codigo_opcao).upper()
descricao = texto(descricao_opcao).upper()
referencia = texto(referencia_opcao).upper()
df_resultado = df_posicao.copy()

if vaga and "Vaga" in df_resultado.columns:
    df_resultado = df_resultado[df_resultado["Vaga"].fillna("").astype(str).str.upper() == vaga]

if codigo and "Código" in df_resultado.columns:
    df_resultado = df_resultado[df_resultado["Código"].fillna("").astype(str).str.strip().str.upper() == codigo]

if descricao and "Descrição" in df_resultado.columns:
    df_resultado = df_resultado[df_resultado["Descrição"].fillna("").astype(str).str.strip().str.upper() == descricao]

if referencia and "Referência" in df_resultado.columns:
    df_resultado = df_resultado[df_resultado["Referência"].fillna("").astype(str).str.strip().str.upper() == referencia]

tem_filtro = any([vaga, codigo, descricao, referencia])

if not tem_filtro:
    st.info("Informe uma vaga, código, descrição ou referência para consultar.")
    st.stop()

render_cards("Posições encontradas", df_resultado)

if vaga:
    render_etiquetas_vaga(vaga, produtos_ocupados(df_resultado))

codigos_encontrados = []
if "Código" in df_resultado.columns:
    codigos_encontrados = [
        item
        for item in df_resultado["Código"].dropna().astype(str).str.strip().unique()
        if item
    ]

df_hist_filtrado = df_historico.copy()

if vaga and "Vaga" in df_hist_filtrado.columns:
    df_hist_filtrado = df_hist_filtrado[df_hist_filtrado["Vaga"].fillna("").astype(str).str.upper() == vaga]

if codigo and "Código" in df_hist_filtrado.columns:
    df_hist_filtrado = df_hist_filtrado[df_hist_filtrado["Código"].fillna("").astype(str).str.strip().str.upper() == codigo]
elif codigos_encontrados and "Código" in df_hist_filtrado.columns:
    df_hist_filtrado = df_hist_filtrado[df_hist_filtrado["Código"].fillna("").astype(str).isin(codigos_encontrados)]

if descricao and "Descrição" in df_hist_filtrado.columns:
    df_hist_filtrado = df_hist_filtrado[df_hist_filtrado["Descrição"].fillna("").astype(str).str.strip().str.upper() == descricao]

if "_DataOrdenacao" in df_hist_filtrado.columns:
    df_hist_filtrado = df_hist_filtrado.sort_values("_DataOrdenacao", ascending=False)

render_historico(df_hist_filtrado)
