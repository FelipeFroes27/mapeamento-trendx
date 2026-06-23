import re
import unicodedata
from html import escape

import pandas as pd
import streamlit as st

from utils.dados import preparar_posicao
from utils.sheets import ler_aba
from utils.ui import preparar_pagina


st.set_page_config(
    page_title="Mapa | Mapeamento Trendx",
    layout="wide",
    initial_sidebar_state="expanded",
)

preparar_pagina(
    "Mapa de Vagas",
    pagina="mapa",
)


@st.cache_data(ttl=30)
def carregar_dados_mapa():
    posicao = preparar_posicao(
        ler_aba("Mapeamento Trendx", "POSIÇÃO")
    )
    bd = pd.DataFrame(
        ler_aba("Mapeamento Trendx", "BD PRODUTOS")
    )
    return posicao, bd


def texto(valor):
    if pd.isna(valor):
        return ""
    return str(valor).strip()


def valor_linha(linha, *colunas):
    for coluna in colunas:
        if coluna in linha:
            return linha.get(coluna)
    return ""


def normalizar_nome_coluna(coluna):
    texto_coluna = unicodedata.normalize(
        "NFKD",
        str(coluna).lower()
    )
    return re.sub(
        r"[^a-z0-9]",
        "",
        texto_coluna
    )


def valor_campo(linha, campo):
    alvos = {
        "codigo": {"codigo", "cdigo"},
        "descricao": {"descricao", "descrio"},
        "categoria": {"categoria"},
        "tipo": {"tipo"},
        "marca": {"marca"},
        "referencia": {"referencia", "referncia"},
        "grupo": {"grupo"},
        "subgrupo": {"subgrupo"},
    }

    for coluna in linha.index:
        if normalizar_nome_coluna(coluna) in alvos.get(campo, set()):
            return linha.get(coluna)

    return ""


def preparar_bd_mapa(df_bd):
    if df_bd.empty:
        return {}

    mapa = {}
    for _, linha in df_bd.iterrows():
        codigo = texto(valor_campo(linha, "codigo")).upper()
        if not codigo or codigo in mapa:
            continue

        mapa[codigo] = {
            "Categoria": texto(valor_campo(linha, "categoria")),
            "Tipo": texto(valor_campo(linha, "tipo")),
            "Marca": texto(valor_campo(linha, "marca")),
            "Referencia": texto(valor_campo(linha, "referencia")),
            "Grupo": texto(valor_campo(linha, "grupo")),
            "Subgrupo": texto(valor_campo(linha, "subgrupo")),
            "Item": texto(valor_campo(linha, "descricao")),
        }

    return mapa


def numero_ordenacao(valor):
    valor = texto(valor)
    try:
        return f"{int(valor):08d}"
    except ValueError:
        return valor


def parse_vaga(vaga):
    partes = texto(vaga).upper().split(".")

    if len(partes) != 6 or any(not parte for parte in partes):
        return None

    return {
        "Zona": partes[0],
        "Rua": partes[1],
        "Lado": partes[2],
        "Modulo": partes[3],
        "Nivel": partes[4],
        "Vao": partes[5],
    }


def preparar_mapa(df_posicao):
    if df_posicao.empty or "Vaga" not in df_posicao.columns:
        return pd.DataFrame(), pd.DataFrame()

    registros = []
    fora_padrao = []

    for _, linha in df_posicao.iterrows():
        vaga = texto(linha.get("Vaga")).upper()
        partes = parse_vaga(vaga)

        if not vaga:
            continue

        if partes is None:
            fora_padrao.append(
                {
                    "Vaga": vaga,
                    "Status": texto(linha.get("Status")).upper(),
                    "Codigo": texto(valor_campo(linha, "codigo")),
                    "Descricao": texto(valor_campo(linha, "descricao")),
                    "Quantidade": linha.get("Quantidade", 0),
                }
            )
            continue

        registro = {
            **partes,
            "Vaga": vaga,
            "Status": texto(linha.get("Status")).upper(),
            "Codigo": texto(valor_campo(linha, "codigo")),
            "Descricao": texto(valor_campo(linha, "descricao")),
            "Quantidade": linha.get("Quantidade", 0),
        }
        registros.append(registro)

    if not registros:
        return pd.DataFrame(), pd.DataFrame(fora_padrao)

    df = pd.DataFrame(registros)
    df["Quantidade"] = pd.to_numeric(
        df["Quantidade"],
        errors="coerce",
    ).fillna(0).astype(int)

    return df, pd.DataFrame(fora_padrao)


COLUNAS_VAGAS = [
    "Vaga",
    "Zona",
    "Rua",
    "Lado",
    "Modulo",
    "Nivel",
    "Vao",
    "StatusMapa",
    "Itens",
    "Quantidade",
    "Codigo",
    "Descricao",
    "Categoria",
    "Tipo",
    "Marca",
    "Referencia",
    "Grupo",
    "Subgrupo",
    "Item",
    "EhSC",
    "Detalhes",
]


def agregar_vagas(df_mapa, bd_produtos):
    if df_mapa.empty:
        return pd.DataFrame(columns=COLUNAS_VAGAS)

    linhas = []
    for vaga, grupo in df_mapa.groupby("Vaga", sort=False):
        primeira = grupo.iloc[0]
        produtos = grupo[
            grupo["Codigo"].fillna("").astype(str).str.strip() != ""
        ].copy()

        quantidade_total = int(produtos["Quantidade"].sum()) if not produtos.empty else 0
        ocupada = quantidade_total > 0 or any(grupo["Status"].astype(str).str.upper() == "OCUPADO")
        codigo_principal = texto(primeira.get("Codigo")).upper()
        descricao_principal = texto(primeira.get("Descricao"))
        dados_produto = bd_produtos.get(codigo_principal, {})
        item_principal = dados_produto.get("Item") or descricao_principal
        eh_sc = codigo_principal == "SC"

        descricoes = []
        for _, item in produtos.head(4).iterrows():
            descricoes.append(
                f'{texto(item.get("Codigo"))} - {texto(item.get("Descricao"))} | Qtd: {texto(item.get("Quantidade"))}'
            )

        linhas.append(
            {
                "Vaga": vaga,
                "Zona": primeira["Zona"],
                "Rua": primeira["Rua"],
                "Lado": primeira["Lado"],
                "Modulo": primeira["Modulo"],
                "Nivel": primeira["Nivel"],
                "Vao": primeira["Vao"],
                "StatusMapa": "OCUPADA" if ocupada else "DISPONIVEL",
                "Itens": len(produtos),
                "Quantidade": quantidade_total,
                "Codigo": codigo_principal,
                "Descricao": descricao_principal,
                "Categoria": dados_produto.get("Categoria", ""),
                "Tipo": dados_produto.get("Tipo", ""),
                "Marca": dados_produto.get("Marca", ""),
                "Referencia": dados_produto.get("Referencia", ""),
                "Grupo": dados_produto.get("Grupo", ""),
                "Subgrupo": dados_produto.get("Subgrupo", ""),
                "Item": item_principal,
                "EhSC": eh_sc,
                "Detalhes": "\n".join(descricoes) if descricoes else "Sem produto",
            }
        )

    return pd.DataFrame(linhas, columns=COLUNAS_VAGAS)


def card_lateral(rotulo, valor, nota):
    return (
        f'<div class="map-side-card">'
        f'<div class="map-side-label">{escape(str(rotulo))}</div>'
        f'<div class="map-side-value">{escape(str(valor))}</div>'
        f'<div class="map-side-note">{escape(str(nota))}</div>'
        f'</div>'
    )


def opcoes_multiselect(df, coluna):
    if df.empty or coluna not in df.columns:
        return []

    return sorted(
        valor
        for valor in df[coluna].dropna().astype(str).str.strip().unique()
        if valor
    )


def aplicar_filtro_multiselect(df, coluna, selecionados):
    if not selecionados or df.empty or coluna not in df.columns:
        return df.iloc[0:0].copy()

    return df[df[coluna].astype(str).isin(selecionados)].copy()


def aplicar_filtro_visual(df, filtros):
    df = df.copy()

    if df.empty:
        df["VisivelMapa"] = False
        return df

    mascara = pd.Series(True, index=df.index)
    for coluna, selecionados in filtros.items():
        if selecionados is None or coluna not in df.columns:
            continue
        if not selecionados:
            mascara = pd.Series(False, index=df.index)
            break
        mascara = mascara & df[coluna].fillna("").astype(str).isin(selecionados)

    df["VisivelMapa"] = mascara
    return df


def filtro_produto(coluna, selecionados, opcoes):
    if selecionados is None:
        return None
    if len(selecionados) == len(opcoes):
        return None
    return selecionados


def valor_combobox(valor):
    if not valor or valor == "Todos":
        return None
    return [valor]


def selectbox_filtro(rotulo, opcoes, key):
    return st.selectbox(
        rotulo,
        ["Todos"] + list(opcoes),
        index=0,
        key=key,
    )


def slot_html(linha, vaos=None, grande=False):
    if not bool(linha.get("VisivelMapa", True)):
        return '<div class="map-slot empty"></div>'

    status = str(linha["StatusMapa"]).lower()
    vaga = escape(str(linha["Vaga"]))
    itens = escape(str(linha["Itens"]))
    detalhes = escape(str(linha["Detalhes"]))
    codigo = texto(linha.get("Codigo")).upper()
    vaos = vaos or [str(linha["Vao"])]
    vao_label = escape("+".join(str(vao) for vao in vaos))
    classe_grande = " grande" if grande else ""
    titulo = f"{vaga}\n{detalhes}"

    conteudo = "SC" if bool(linha.get("EhSC", False)) else codigo
    conteudo = escape(conteudo) if conteudo else "&nbsp;"

    return (
        f'<div class="map-slot {status}{classe_grande}" title="{titulo}">'
        f'<span>{vao_label}</span>'
        f'<strong>{conteudo}</strong>'
        f'<small>{itens} item</small>'
        f'</div>'
    )


def slots_com_sc(df_celula, vaos_esperados):
    linhas_por_vao = {
        str(linha["Vao"]): linha
        for _, linha in df_celula.iterrows()
    }
    linhas = [
        linhas_por_vao.get(str(vao))
        for vao in vaos_esperados
    ]
    usados = set()
    slots = []

    for indice, linha in enumerate(linhas):
        if indice in usados:
            continue

        if linha is None:
            slots.append('<div class="map-slot empty"></div>')
            usados.add(indice)
            continue

        eh_sc = bool(linha.get("EhSC", False))
        proximo_indice = indice + 1

        if eh_sc:
            if (
                proximo_indice < len(linhas)
                and proximo_indice not in usados
                and linhas[proximo_indice] is not None
                and not bool(linhas[proximo_indice].get("EhSC", False))
            ):
                vizinho = linhas[proximo_indice]
                slots.append(
                    slot_html(
                        vizinho,
                        [linha["Vao"], vizinho["Vao"]],
                        grande=True,
                    )
                )
                usados.add(indice)
                usados.add(proximo_indice)
            else:
                slots.append(
                    slot_html(linha)
                )
                usados.add(indice)

            continue

        if (
            proximo_indice < len(linhas)
            and proximo_indice not in usados
            and linhas[proximo_indice] is not None
            and bool(linhas[proximo_indice].get("EhSC", False))
        ):
            vizinho = linhas[proximo_indice]
            slots.append(
                slot_html(
                    linha,
                    [linha["Vao"], vizinho["Vao"]],
                    grande=True,
                )
            )
            usados.add(indice)
            usados.add(proximo_indice)
        else:
            slots.append(
                slot_html(linha)
            )
            usados.add(indice)

    return slots


def render_fora_padrao(df_fora_padrao):
    if df_fora_padrao.empty:
        return

    linhas = []
    for _, linha in df_fora_padrao.iterrows():
        linhas.append(
            "<tr>"
            f"<td>{escape(texto(linha.get('Vaga')))}</td>"
            f"<td>{escape(texto(linha.get('Status')))}</td>"
            f"<td>{escape(texto(linha.get('Codigo')))}</td>"
            f"<td>{escape(texto(linha.get('Descricao')))}</td>"
            f"<td class=\"num\">{escape(texto(linha.get('Quantidade')))}</td>"
            "</tr>"
        )

    st.markdown(
        '<div class="map-invalid-card">'
        '<div class="panel-title">Vagas fora do padrão</div>'
        '<div class="panel-subtitle">Endereços que não seguem ZONA.RUA.LADO.MÓDULO.NÍVEL.VÃO.</div>'
        '<div class="table-scroll">'
        '<table class="mini-table">'
        '<thead><tr><th>Vaga</th><th>Status</th><th>Código</th><th>Descrição</th><th class="num">Qtd</th></tr></thead>'
        f'<tbody>{"".join(linhas)}</tbody>'
        '</table>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_mapa(df_vagas):
    if df_vagas.empty:
        st.warning("Nenhuma vaga no padrão ZONA.RUA.LADO.MODULO.NIVEL.VAO para montar o mapa.")
        return

    blocos = []
    grupos = df_vagas.sort_values(
        by=["Zona", "Rua", "Lado", "Modulo", "Nivel", "Vao"],
        key=lambda serie: serie.map(numero_ordenacao),
    ).groupby(["Zona", "Rua", "Lado"], sort=False)

    for (zona, rua, lado), grupo in grupos:
        modulos = sorted(
            grupo["Modulo"].dropna().astype(str).unique(),
            key=numero_ordenacao,
        )
        niveis = sorted(
            grupo["Nivel"].dropna().astype(str).unique(),
            key=numero_ordenacao,
            reverse=True,
        )
        vaos_esperados = sorted(
            grupo["Vao"].dropna().astype(str).unique(),
            key=numero_ordenacao,
        )

        linhas_html = []
        for nivel in niveis:
            celulas = [
                f'<div class="map-level-label">N{escape(str(nivel))}</div>'
            ]

            for modulo in modulos:
                df_celula = grupo[
                    (grupo["Modulo"].astype(str) == str(modulo))
                    & (grupo["Nivel"].astype(str) == str(nivel))
                ].sort_values("Vao", key=lambda serie: serie.map(numero_ordenacao))

                if df_celula.empty:
                    celulas.append('<div class="map-bay missing"></div>')
                    continue

                subslots = slots_com_sc(
                    df_celula,
                    vaos_esperados,
                )

                celulas.append(
                    f'<div class="map-bay">'
                    f'{"".join(subslots)}'
                    f'</div>'
                )

            linhas_html.append(
                f'<div class="map-row" style="--map-columns:{len(modulos)};">'
                + "".join(celulas)
                + '</div>'
            )

        header_modulos = ''.join(
            f'<div class="map-module-label">Módulo {escape(str(modulo))}</div>'
            for modulo in modulos
        )

        blocos.append(
            f'<div class="map-block">'
            f'<div class="map-block-head">'
            f'<div class="panel-title">Zona {escape(str(zona))} | Rua {escape(str(rua))} | Lado {escape(str(lado))}</div>'
            f'<div class="panel-subtitle">Porta-palete por módulos, níveis e vãos</div>'
            f'</div>'
            f'<div class="map-header-row" style="--map-columns:{len(modulos)};">'
            f'<div></div>{header_modulos}'
            f'</div>'
            f'{"".join(linhas_html)}'
            f'</div>'
        )

    st.markdown(
        '<div class="map-grid">'
        + ''.join(blocos)
        + '</div>',
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <style>
    .map-legend {
        display: flex;
        flex-wrap: wrap;
        gap: .3cm;
        margin-bottom: .3cm;
    }

    .map-block {
        --rack-post-width: 5px;
    }

    .map-legend-item {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border: 2px solid #000000;
        border-radius: 8px;
        padding: 8px 10px;
        background: #ffffff;
        color: #000000;
        font-size: 13px;
        font-weight: 800;
    }

    .map-legend-swatch {
        width: 18px;
        height: 18px;
        border: 2px solid #000000;
        border-radius: 4px;
    }

    .map-legend-swatch.occupied {
        background: #fecaca;
    }

    .map-legend-swatch.available {
        background: #bbf7d0;
    }

    .st-key-mapa_lateral {
        border: 2px solid #000000 !important;
        border-radius: 8px !important;
        background: #ffffff !important;
        padding: 12px !important;
        box-sizing: border-box;
        align-self: flex-start !important;
    }

    .block-container,
    [data-testid="stMainBlockContainer"] {
        max-width: 1840px !important;
        padding-left: 1.15rem !important;
        padding-right: 1.15rem !important;
        padding-top: .35rem !important;
    }

    .page-head {
        max-width: 1840px;
        margin-left: auto;
        margin-right: auto;
    }

    .st-key-mapa_lateral [data-baseweb="tag"] {
        max-width: 78px !important;
        height: 28px !important;
        margin: 2px 3px 2px 0 !important;
        border-radius: 7px !important;
    }

    .st-key-mapa_lateral [data-baseweb="tag"] span {
        max-width: 46px !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        white-space: nowrap !important;
    }

    .st-key-mapa_lateral div[data-testid="stMultiSelect"],
    .st-key-mapa_lateral div[data-testid="stSelectbox"] {
        margin-bottom: .3cm !important;
    }

    .st-key-mapa_lateral div[data-testid="stMultiSelect"] div[data-baseweb="select"] {
        min-height: 43px !important;
        max-height: 110px !important;
        overflow-y: auto !important;
        align-items: flex-start !important;
        padding-top: 3px !important;
        padding-bottom: 3px !important;
    }

    .st-key-mapa_lateral div[data-testid="stMultiSelect"] input {
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        border: 0 !important;
        opacity: 0 !important;
    }

    .st-key-mapa_lateral div[data-testid="stMultiSelect"] div[data-baseweb="input"],
    .st-key-mapa_lateral div[data-testid="stMultiSelect"] div[data-baseweb="input"] > div {
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        border: 0 !important;
        background: transparent !important;
    }

    .st-key-mapa_atualizar_dados button {
        min-height: 38px !important;
        margin-bottom: .3cm !important;
    }

    .map-side-title {
        margin: 0 0 .3cm 0;
        color: #000000;
        font-size: 18px;
        line-height: 1.05;
        font-weight: 900;
    }

    .map-side-label-title {
        margin: 10px 0 6px 0;
        color: #000000;
        font-size: 13px;
        font-weight: 900;
    }

    .map-side-card {
        border: 2px solid #000000;
        border-radius: 8px;
        background: #ffffff;
        padding: 8px 9px;
        margin-bottom: .3cm;
        box-sizing: border-box;
    }

    .map-side-label {
        color: #111111;
        font-size: 12px;
        font-weight: 850;
    }

    .map-side-value {
        margin-top: 4px;
        color: #000000;
        font-size: 24px;
        line-height: 1;
        font-weight: 900;
    }

    .map-side-note {
        margin-top: 5px;
        color: #333333;
        font-size: 10px;
        font-weight: 650;
    }

    .map-grid {
        display: flex;
        flex-direction: column;
        gap: .3cm;
        align-items: stretch;
        width: 100%;
    }

    .map-invalid-card {
        border: 2px solid #000000;
        border-radius: 10px;
        background: #ffffff;
        padding: 12px;
        margin-top: .3cm;
        box-sizing: border-box;
    }

    .map-block {
        border: 2px solid #000000;
        border-radius: 10px;
        background: #ffffff;
        padding: 12px;
        overflow-x: auto;
        max-width: 100%;
        box-sizing: border-box;
    }

    .map-block-head {
        margin-bottom: 10px;
    }

    .map-header-row,
    .map-row {
        display: grid;
        grid-template-columns: 42px repeat(var(--map-columns), minmax(86px, 1fr));
        gap: 0;
        min-width: calc(42px + var(--map-columns) * 92px);
        margin-bottom: 0;
        align-items: stretch;
    }

    .map-module-label,
    .map-level-label {
        color: #000000;
        font-size: 12px;
        font-weight: 850;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .map-level-label {
        border: 2px solid #000000;
        border-right: 0;
        border-bottom: 0;
        border-radius: 0;
        min-height: 48px;
        background: #ffffff;
    }

    .map-header-row .map-level-label,
    .map-header-row > div:first-child {
        border: 0;
        min-height: 28px;
    }

    .map-module-label {
        min-height: 28px;
        border-left: var(--rack-post-width) solid #4b5563;
        border-right: 0;
        border-bottom: 2px solid #000000;
        background: #f8fafc;
    }

    .map-bay {
        min-height: 48px;
        border: 2px solid #000000;
        border-left: var(--rack-post-width) solid #4b5563;
        border-right: 0;
        border-bottom: 0;
        display: flex;
        gap: 4px;
        align-items: center;
        justify-content: stretch;
        padding: 4px;
        background: #ffffff;
        box-sizing: border-box;
    }

    .map-row:last-child .map-level-label,
    .map-row:last-child .map-bay {
        border-bottom: 2px solid #000000;
    }

    .map-bay.missing {
        border-style: solid;
        border-left: var(--rack-post-width) solid #4b5563;
        border-right: 0;
        background: #ffffff;
    }

    .map-header-row .map-module-label:last-child,
    .map-row .map-bay:last-child {
        border-right: var(--rack-post-width) solid #4b5563;
    }

    .map-slot {
        flex: 1 1 0;
        min-width: 32px;
        min-height: 36px;
        border: 1px solid #000000;
        border-radius: 4px;
        display: grid;
        grid-template-rows: auto auto auto;
        align-items: center;
        justify-items: center;
        padding: 4px 3px;
        color: #000000;
        box-sizing: border-box;
    }

    .map-slot.grande {
        flex: 2 1 0;
    }

    .map-slot.empty {
        border-color: transparent;
        background: transparent;
    }

    .map-slot.ocupada {
        background: #fecaca;
    }

    .map-slot.disponivel {
        background: #bbf7d0;
    }

    .map-slot span,
    .map-slot strong,
    .map-slot small {
        color: inherit;
        line-height: 1;
    }

    .map-slot span {
        font-size: 10px;
        font-weight: 850;
    }

    .map-slot strong {
        max-width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 11px;
        font-weight: 900;
    }

    .map-slot small {
        font-size: 8px;
        font-weight: 750;
    }

    @media (max-width: 1100px) {
        .st-key-mapa_lateral {
            margin-bottom: .3cm;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


df_posicao, df_bd = carregar_dados_mapa()

if df_posicao.empty:
    st.warning("Não há dados na aba POSIÇÃO.")
    st.stop()

df_mapa, df_fora_padrao = preparar_mapa(df_posicao)
bd_produtos = preparar_bd_mapa(df_bd)
df_vagas = agregar_vagas(df_mapa, bd_produtos)

col_lateral, col_mapa = st.columns(
    [0.95, 7.05],
    gap="small",
    vertical_alignment="top",
)

with col_lateral:
    with st.container(key="mapa_lateral"):
        st.markdown('<div class="map-side-title">Mapa</div>', unsafe_allow_html=True)

        if st.button("Atualizar dados", key="mapa_atualizar_dados", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown('<div class="map-side-label-title">Filtros</div>', unsafe_allow_html=True)

        zonas = opcoes_multiselect(df_vagas, "Zona")
        zonas_selecionadas = st.multiselect(
            "Zona",
            zonas,
            default=zonas,
            key="mapa_filtro_zona",
        )

        df_filtrado = aplicar_filtro_multiselect(
            df_vagas,
            "Zona",
            zonas_selecionadas,
        )

        ruas = opcoes_multiselect(df_filtrado, "Rua")
        ruas_selecionadas = st.multiselect(
            "Rua",
            ruas,
            default=ruas,
            key="mapa_filtro_rua",
        )
        df_filtrado = aplicar_filtro_multiselect(
            df_filtrado,
            "Rua",
            ruas_selecionadas,
        )

        lados = opcoes_multiselect(df_filtrado, "Lado")
        lados_selecionados = st.multiselect(
            "Lado",
            lados,
            default=lados,
            key="mapa_filtro_lado",
        )
        df_filtrado = aplicar_filtro_multiselect(
            df_filtrado,
            "Lado",
            lados_selecionados,
        )

        status_opcoes = ["OCUPADA", "DISPONIVEL"]
        status_selecionado = selectbox_filtro(
            "Status",
            status_opcoes,
            "mapa_filtro_status_combo",
        )
        status_filtro = valor_combobox(status_selecionado)
        if status_filtro is not None:
            df_filtrado = aplicar_filtro_multiselect(
                df_filtrado,
                "StatusMapa",
                status_filtro,
            )

        st.markdown('<div class="map-side-label-title">Produto</div>', unsafe_allow_html=True)

        categorias = opcoes_multiselect(df_filtrado, "Categoria")
        categorias_selecionadas = st.multiselect(
            "Categoria",
            categorias,
            default=categorias,
            key="mapa_filtro_categoria",
        )

        base_marca = aplicar_filtro_visual(
            df_filtrado,
            {
                "Categoria": filtro_produto(
                    "Categoria",
                    categorias_selecionadas,
                    categorias,
                )
            },
        )
        marcas = opcoes_multiselect(
            base_marca[base_marca["VisivelMapa"]],
            "Marca",
        )
        marca_selecionada = selectbox_filtro(
            "Marca",
            marcas,
            "mapa_filtro_marca_combo",
        )
        marcas_selecionadas = valor_combobox(marca_selecionada)

        base_tipo = aplicar_filtro_visual(
            df_filtrado,
            {
                "Categoria": filtro_produto(
                    "Categoria",
                    categorias_selecionadas,
                    categorias,
                ),
                "Marca": filtro_produto(
                    "Marca",
                    marcas_selecionadas,
                    marcas,
                ),
            },
        )
        tipos = opcoes_multiselect(
            base_tipo[base_tipo["VisivelMapa"]],
            "Tipo",
        )
        tipo_selecionado = selectbox_filtro(
            "Tipo",
            tipos,
            "mapa_filtro_tipo_combo",
        )
        tipos_selecionados = valor_combobox(tipo_selecionado)

        base_item = aplicar_filtro_visual(
            df_filtrado,
            {
                "Categoria": filtro_produto(
                    "Categoria",
                    categorias_selecionadas,
                    categorias,
                ),
                "Marca": filtro_produto(
                    "Marca",
                    marcas_selecionadas,
                    marcas,
                ),
                "Tipo": filtro_produto(
                    "Tipo",
                    tipos_selecionados,
                    tipos,
                ),
            },
        )

        grupos = opcoes_multiselect(
            base_item[base_item["VisivelMapa"]],
            "Grupo",
        )
        grupo_selecionado = selectbox_filtro(
            "Grupo",
            grupos,
            "mapa_filtro_grupo_combo",
        )
        grupos_selecionados = valor_combobox(grupo_selecionado)

        base_item = aplicar_filtro_visual(
            df_filtrado,
            {
                "Categoria": filtro_produto(
                    "Categoria",
                    categorias_selecionadas,
                    categorias,
                ),
                "Marca": filtro_produto(
                    "Marca",
                    marcas_selecionadas,
                    marcas,
                ),
                "Tipo": filtro_produto(
                    "Tipo",
                    tipos_selecionados,
                    tipos,
                ),
                "Grupo": filtro_produto(
                    "Grupo",
                    grupos_selecionados,
                    grupos,
                ),
            },
        )
        itens = opcoes_multiselect(
            base_item[base_item["VisivelMapa"]],
            "Item",
        )
        item_selecionado = selectbox_filtro(
            "Item",
            itens,
            "mapa_filtro_item_combo",
        )
        itens_selecionados = valor_combobox(item_selecionado)

        df_visual = aplicar_filtro_visual(
            df_filtrado,
            {
                "Categoria": filtro_produto(
                    "Categoria",
                    categorias_selecionadas,
                    categorias,
                ),
                "Marca": filtro_produto(
                    "Marca",
                    marcas_selecionadas,
                    marcas,
                ),
                "Tipo": filtro_produto(
                    "Tipo",
                    tipos_selecionados,
                    tipos,
                ),
                "Grupo": filtro_produto(
                    "Grupo",
                    grupos_selecionados,
                    grupos,
                ),
                "Item": filtro_produto(
                    "Item",
                    itens_selecionados,
                    itens,
                ),
            },
        )

        df_visivel = df_visual[df_visual["VisivelMapa"]] if not df_visual.empty else df_visual
        resumo_filtrado = {
            "total": int(df_visivel["Vaga"].nunique()) if not df_visivel.empty else 0,
            "ocupadas": int(df_visivel[df_visivel["StatusMapa"] == "OCUPADA"]["Vaga"].nunique()) if not df_visivel.empty else 0,
            "disponiveis": int(df_visivel[df_visivel["StatusMapa"] == "DISPONIVEL"]["Vaga"].nunique()) if not df_visivel.empty else 0,
            "itens": int(df_visivel["Itens"].sum()) if not df_visivel.empty else 0,
            "quantidade": int(df_visivel["Quantidade"].sum()) if not df_visivel.empty else 0,
        }

        st.markdown('<div class="map-side-label-title">Resumo</div>', unsafe_allow_html=True)
        st.markdown(
            card_lateral("Vagas", resumo_filtrado["total"], "No filtro atual")
            + card_lateral("Ocupadas", resumo_filtrado["ocupadas"], "Com produto e saldo")
            + card_lateral("Disponiveis", resumo_filtrado["disponiveis"], "Sem produto em saldo")
            + card_lateral("Saldo", resumo_filtrado["quantidade"], "Quantidade total"),
            unsafe_allow_html=True,
        )
with col_mapa:
    st.markdown(
        '<div class="map-legend">'
        '<div class="map-legend-item"><span class="map-legend-swatch occupied"></span>Ocupada</div>'
        '<div class="map-legend-item"><span class="map-legend-swatch available"></span>Disponível</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    render_mapa(df_visual)

if not df_fora_padrao.empty:
    with col_mapa:
        render_fora_padrao(df_fora_padrao)
