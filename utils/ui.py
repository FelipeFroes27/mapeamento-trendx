import base64
from pathlib import Path

import streamlit as st


LOGO_BRANCO = "Logo Branco.bmp"
LOGO_PRETO = "logo preto goper.png"


def aplicar_layout():
    st.markdown(
        """
        <style>
        header,
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stStatusWidget"],
        [data-testid="stDecoration"] {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            min-height: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            border: 0 !important;
        }

        footer, #MainMenu {visibility: hidden !important;}

        .stApp,
        [data-testid="stAppViewContainer"] {
            background: #ffffff;
            color: #000000;
        }

        [data-testid="stSidebar"] {
            background: #ffffff !important;
            border-right: 1px solid #000000;
        }

        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        [data-testid="stSidebar"] a,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        label,
        .stMarkdown,
        .stCaptionContainer {
            color: #000000 !important;
        }

        .block-container,
        [data-testid="stMainBlockContainer"] {
            max-width: 1540px;
            padding-top: .45rem;
            padding-bottom: 1.25rem;
        }

        .sidebar-logo {
            display: flex;
            gap: 8px;
            align-items: center;
            justify-content: center;
            padding: 8px 0 18px 0;
        }

        .sidebar-logo img,
        .page-logos img {
            background: #ffffff;
            border: 0;
            border-radius: 0;
            padding: 0;
            object-fit: contain;
        }

        .sidebar-logo img {
            max-height: 24px;
            width: auto;
        }

        .page-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 1.25rem;
        }

        .page-title h1 {
            margin: 0;
            color: #000000;
            font-size: 29px;
            line-height: 1.05;
            font-weight: 850;
            letter-spacing: 0;
        }

        .page-title p {
            margin: 6px 0 0 0;
            color: #333333;
            font-size: 14px;
        }

        .page-logos {
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 0 0 auto;
        }

        .page-logos img {
            max-height: 30px;
            max-width: 104px;
        }

        .home-hero {
            min-height: 330px;
            display: grid;
            grid-template-columns: 1.1fr .9fr;
            gap: 24px;
            align-items: center;
            padding: 28px;
            border: 2px solid #000000;
            border-radius: 22px;
            background: #ffffff;
        }

        .home-title {
            margin: 0;
            color: #000000;
            font-size: 34px;
            line-height: 1.08;
            font-weight: 850;
            letter-spacing: 0;
        }

        .home-copy {
            max-width: 620px;
            margin: 12px 0 0 0;
            color: #333333;
            font-size: 16px;
            line-height: 1.55;
        }

        .home-panel,
        .panel,
        .kpi-card,
        div[data-testid="stDataFrame"],
        div[data-testid="stTable"] {
            border: 2px solid #000000;
            border-radius: 12px;
            background: #ffffff;
            box-shadow: none;
            overflow: hidden;
        }

        .home-panel,
        .panel,
        .kpi-card {
            padding: 16px;
        }

        .home-panel-title,
        .panel-title {
            margin: 0 0 12px 0;
            color: #000000;
            font-size: 16px;
            font-weight: 850;
        }

        .home-section {
            display: block;
            padding: 12px 14px;
            margin-top: 10px;
            border-radius: 7px;
            border: 2px solid #000000;
            background: #ffffff;
            color: #000000;
            font-size: 14px;
            font-weight: 800;
        }

        .home-section span {
            display: block;
            margin-top: 3px;
            color: #333333;
            font-size: 12px;
            font-weight: 600;
        }

        .stButton > button,
        div[data-baseweb="select"] > div,
        input,
        textarea {
            border: 2px solid #000000 !important;
            background: #ffffff !important;
            color: #000000 !important;
            border-radius: 7px !important;
            box-shadow: none !important;
        }

        .stButton > button {
            font-weight: 800 !important;
        }

        .kpi-label {
            color: #333333;
            font-size: 13px;
            font-weight: 700;
        }

        .kpi-value {
            margin-top: 6px;
            color: #000000;
            font-size: 30px;
            line-height: 1;
            font-weight: 850;
        }

        .kpi-note {
            margin-top: 7px;
            color: #555555;
            font-size: 12px;
        }

        @media (max-width: 900px) {
            .page-head,
            .home-hero {
                grid-template-columns: 1fr;
                flex-direction: column;
            }

            .home-title {
                font-size: 28px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _imagem_base64(caminho):
    arquivo = Path(caminho)
    if not arquivo.exists():
        return ""

    return base64.b64encode(arquivo.read_bytes()).decode("utf-8")


def render_menu_lateral():
    with st.sidebar:
        st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
        if Path(LOGO_BRANCO).exists():
            st.image(LOGO_BRANCO, width=72)
        if Path(LOGO_PRETO).exists():
            st.image(LOGO_PRETO, width=32)
        st.markdown("</div>", unsafe_allow_html=True)

        st.page_link("app.py", label="Início")
        st.page_link("pages/Entrada.py", label="Entrada")
        st.page_link("pages/Saida.py", label="Saída")
        st.page_link("pages/Consulta.py", label="Consulta")
        st.page_link("pages/Indicadores.py", label="Indicadores")


def render_cabecalho(titulo, subtitulo=""):
    logo_branco = _imagem_base64(LOGO_BRANCO)
    logo_preto = _imagem_base64(LOGO_PRETO)
    subtitulo_html = f"<p>{subtitulo}</p>" if subtitulo else ""

    st.markdown(
        f"""
        <div class="page-head">
            <div class="page-title">
                <h1>{titulo}</h1>
                {subtitulo_html}
            </div>
            <div class="page-logos">
                <img src="data:image/bmp;base64,{logo_branco}" alt="Trendx">
                <img src="data:image/png;base64,{logo_preto}" alt="Goper">
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def preparar_pagina(titulo, subtitulo=""):
    aplicar_layout()
    render_menu_lateral()
    render_cabecalho(titulo, subtitulo)


def render_kpi(rotulo, valor, nota=""):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{rotulo}</div>
            <div class="kpi-value">{valor}</div>
            <div class="kpi-note">{nota}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
