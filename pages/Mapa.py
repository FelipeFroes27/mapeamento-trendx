from html import escape

import pandas as pd
import streamlit as st

from utils.dados import preparar_posicao, resumo_vagas
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


def card_metrica(rotulo, valor, nota):
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{escape(str(rotulo))}</div>'
        f'<div class="kpi-value">{escape(str(valor))}</div>'
        f'<div class="kpi-note">{escape(str(nota))}</div>'
        f'</div>'
    )


def render_mapa(df_vagas):
    if df_vagas.empty:
        st.warning("Nenhuma vaga no padrão ZONA.RUA.LADO.MODULO.NIVEL.VAO para montar o mapa.")
        return

    blocos = []
    grupos = df_vagas.sort_values(
        by=["Zona", "Rua", "Lado", "Modulo"],
        key=lambda serie: serie.map(numero_ordenacao),
    ).groupby(["Zona", "Rua", "Lado", "Modulo"], sort=False)

    for (zona, rua, lado, modulo), grupo in grupos:
        niveis = sorted(
            grupo["Nivel"].dropna().astype(str).unique(),
            key=numero_ordenacao,
            reverse=True,
        )
        vaos = sorted(
            grupo["Vao"].dropna().astype(str).unique(),
            key=numero_ordenacao,
        )

        celulas_por_vaga = {
            str(linha["Nivel"]) + "|" + str(linha["Vao"]): linha
            for _, linha in grupo.iterrows()
        }

        linhas_html = []
        for nivel in niveis:
            celulas = [
                f'<div class="map-level-label">N{escape(str(nivel))}</div>'
            ]

            for vao in vaos:
                linha = celulas_por_vaga.get(str(nivel) + "|" + str(vao))

                if linha is None:
                    celulas.append('<div class="map-slot missing"></div>')
                    continue

                status = str(linha["StatusMapa"]).lower()
                vaga = escape(str(linha["Vaga"]))
                quantidade = escape(str(linha["Quantidade"]))
                itens = escape(str(linha["Itens"]))
                detalhes = escape(str(linha["Detalhes"]))

                celulas.append(
                    f'<div class="map-slot {status}" title="{vaga}\n{detalhes}">'
                    f'<span>{escape(str(vao))}</span>'
                    f'<strong>{quantidade}</strong>'
                    f'<small>{itens} item</small>'
                    f'</div>'
                )

            linhas_html.append(
                f'<div class="map-row" style="--map-columns:{len(vaos)};">'
                + "".join(celulas)
                + '</div>'
            )

        header_vaos = ''.join(
            f'<div class="map-vao-label">{escape(str(vao))}</div>'
            for vao in vaos
        )

        blocos.append(
            f'<div class="map-block">'
            f'<div class="map-block-head">'
            f'<div class="panel-title">Zona {escape(str(zona))} | Rua {escape(str(rua))} | Lado {escape(str(lado))}</div>'
            f'<div class="panel-subtitle">Modulo {escape(str(modulo))}</div>'
            f'</div>'
            f'<div class="map-header-row" style="--map-columns:{len(vaos)};">'
            f'<div></div>{header_vaos}'
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
        background: #111827;
    }

    .map-legend-swatch.available {
        background: #ffffff;
    }

    .map-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: .3cm;
        align-items: start;
    }

    .map-block {
        border: 2px solid #000000;
        border-radius: 10px;
        background: #ffffff;
        padding: 12px;
        overflow-x: auto;
    }

    .map-block-head {
        margin-bottom: 10px;
    }

    .map-header-row,
    .map-row {
        display: grid;
        grid-template-columns: 44px repeat(var(--map-columns), minmax(56px, 1fr));
        gap: 6px;
        min-width: calc(44px + var(--map-columns) * 62px);
        margin-bottom: 6px;
        align-items: stretch;
    }

    .map-vao-label,
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
        border-radius: 6px;
        min-height: 48px;
        background: #ffffff;
    }

    .map-slot {
        min-height: 48px;
        border: 2px solid #000000;
        border-radius: 6px;
        display: grid;
        grid-template-rows: auto auto auto;
        align-items: center;
        justify-items: center;
        padding: 5px 4px;
        color: #000000;
        background: #ffffff;
        box-sizing: border-box;
    }

    .map-slot.ocupada {
        background: #111827;
        color: #ffffff;
    }

    .map-slot.disponivel {
        background: #ffffff;
        color: #000000;
    }

    .map-slot.missing {
        border-style: dashed;
        border-color: #bbbbbb;
        background: #f6f6f6;
    }

    .map-slot span,
    .map-slot strong,
    .map-slot small {
        color: inherit;
        line-height: 1;
    }

    .map-slot span {
        font-size: 11px;
        font-weight: 850;
    }

    .map-slot strong {
        font-size: 15px;
        font-weight: 900;
    }

    .map-slot small {
        font-size: 9px;
        font-weight: 750;
    }

    @media (max-width: 1100px) {
        .map-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


df_posicao = carregar_dados_mapa()

if st.button("Atualizar dados"):
    st.cache_data.clear()
    st.rerun()

if df_posicao.empty:
    st.warning("Não há dados na aba POSIÇÃO.")
    st.stop()

df_mapa, df_fora_padrao = preparar_mapa(df_posicao)
df_vagas = agregar_vagas(df_mapa)
resumo = resumo_vagas(df_posicao)

st.markdown(
    '<div class="metric-grid">'
    + card_metrica("Vagas totais", resumo["total"], "Cadastradas em POSIÇÃO")
    + card_metrica("Ocupadas", resumo["ocupadas"], "Com produto e saldo")
    + card_metrica("Disponíveis", resumo["disponiveis"], "Sem produto em saldo")
    + card_metrica("Itens alocados", resumo["itens"], "Linhas ocupadas")
    + card_metrica("Saldo em peças", resumo["quantidade"], "Quantidade total")
    + '</div>',
    unsafe_allow_html=True,
)

zonas = sorted(df_vagas["Zona"].dropna().astype(str).unique()) if not df_vagas.empty else []
zona = st.selectbox("Zona", ["Todas"] + zonas)

df_filtrado = df_vagas.copy()
if zona != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Zona"] == zona]

ruas = sorted(df_filtrado["Rua"].dropna().astype(str).unique()) if not df_filtrado.empty else []
rua = st.selectbox("Rua", ["Todas"] + ruas)
if rua != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Rua"] == rua]

lados = sorted(df_filtrado["Lado"].dropna().astype(str).unique()) if not df_filtrado.empty else []
lado = st.selectbox("Lado", ["Todos"] + lados)
if lado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Lado"] == lado]

status = st.selectbox("Status", ["Todos", "OCUPADA", "DISPONIVEL"])
if status != "Todos":
    df_filtrado = df_filtrado[df_filtrado["StatusMapa"] == status]

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
