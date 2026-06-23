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
    "Visualizacao 2D das posicoes por zona, rua, lado, modulo, nivel e vao.",
    pagina="mapa",
)


@st.cache_data(ttl=30)
def carregar_dados_mapa():
    return preparar_posicao(
        ler_aba("Mapeamento Trendx", "POSIÇÃO")
    )


def texto(valor):
    if pd.isna(valor):
        return ""
    return str(valor).strip()


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
                    "Código": texto(linha.get("Código")),
                    "Descrição": texto(linha.get("Descrição")),
                    "Quantidade": linha.get("Quantidade", 0),
                }
            )
            continue

        registro = {
            **partes,
            "Vaga": vaga,
            "Status": texto(linha.get("Status")).upper(),
            "Código": texto(linha.get("Código")),
            "Descrição": texto(linha.get("Descrição")),
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
    "Detalhes",
]


def agregar_vagas(df_mapa):
    if df_mapa.empty:
        return pd.DataFrame(columns=COLUNAS_VAGAS)

    linhas = []
    for vaga, grupo in df_mapa.groupby("Vaga", sort=False):
        primeira = grupo.iloc[0]
        produtos = grupo[
            grupo["Código"].fillna("").astype(str).str.strip() != ""
        ].copy()

        quantidade_total = int(produtos["Quantidade"].sum()) if not produtos.empty else 0
        ocupada = quantidade_total > 0 or any(grupo["Status"].astype(str).str.upper() == "OCUPADO")

        descricoes = []
        for _, item in produtos.head(4).iterrows():
            descricoes.append(
                f'{texto(item.get("Código"))} - {texto(item.get("Descrição"))} | Qtd: {texto(item.get("Quantidade"))}'
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

                subslots = []
                for _, linha in df_celula.iterrows():
                    status = str(linha["StatusMapa"]).lower()
                    vaga = escape(str(linha["Vaga"]))
                    quantidade = escape(str(linha["Quantidade"]))
                    itens = escape(str(linha["Itens"]))
                    detalhes = escape(str(linha["Detalhes"]))
                    vao = escape(str(linha["Vao"]))

                    subslots.append(
                        f'<div class="map-slot {status}" title="{vaga}\n{detalhes}">'
                        f'<span>{vao}</span>'
                        f'<strong>{quantidade}</strong>'
                        f'<small>{itens} item</small>'
                        f'</div>'
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
        font-size: 13px;
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


df_posicao = carregar_dados_mapa()

if df_posicao.empty:
    st.warning("Não há dados na aba POSIÇÃO.")
    st.stop()

df_mapa, df_fora_padrao = preparar_mapa(df_posicao)
df_vagas = agregar_vagas(df_mapa)

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
        status_selecionados = st.multiselect(
            "Status",
            status_opcoes,
            default=status_opcoes,
            key="mapa_filtro_status",
        )
        df_filtrado = aplicar_filtro_multiselect(
            df_filtrado,
            "StatusMapa",
            status_selecionados,
        )

        resumo_filtrado = {
            "total": int(df_filtrado["Vaga"].nunique()) if not df_filtrado.empty else 0,
            "ocupadas": int(df_filtrado[df_filtrado["StatusMapa"] == "OCUPADA"]["Vaga"].nunique()) if not df_filtrado.empty else 0,
            "disponiveis": int(df_filtrado[df_filtrado["StatusMapa"] == "DISPONIVEL"]["Vaga"].nunique()) if not df_filtrado.empty else 0,
            "itens": int(df_filtrado["Itens"].sum()) if not df_filtrado.empty else 0,
            "quantidade": int(df_filtrado["Quantidade"].sum()) if not df_filtrado.empty else 0,
        }

        st.markdown('<div class="map-side-label-title">Resumo</div>', unsafe_allow_html=True)
        st.markdown(
            card_lateral("Vagas", resumo_filtrado["total"], "No filtro atual")
            + card_lateral("Ocupadas", resumo_filtrado["ocupadas"], "Com produto e saldo")
            + card_lateral("Disponíveis", resumo_filtrado["disponiveis"], "Sem produto em saldo")
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

    render_mapa(df_filtrado)

if not df_fora_padrao.empty:
    with st.expander(f"Vagas fora do padrão ({len(df_fora_padrao)})"):
        st.dataframe(
            df_fora_padrao,
            use_container_width=True,
            hide_index=True,
        )
