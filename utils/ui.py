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
        [data-testid="stHeader"],
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

        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stSidebarCollapseButton"] {
            display: none !important;
            visibility: hidden !important;
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

        div[data-testid="stVerticalBlock"] {
            gap: .3cm !important;
        }

        div[data-testid="stHorizontalBlock"] {
            gap: .3cm !important;
            margin-bottom: .3cm !important;
        }

        div[data-testid="column"] {
            padding-left: 0 !important;
            padding-right: 0 !important;
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

        .kpi-card,
        .chart-panel,
        .panel {
            margin-bottom: .3cm !important;
        }

        .home-panel-title,
        .panel-title {
            margin: 0 0 12px 0;
            color: #000000;
            font-size: 16px;
            font-weight: 850;
        }

        .panel-subtitle {
            margin: -6px 0 12px 0;
            color: #555555;
            font-size: 12px;
            font-weight: 650;
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

        .chart-panel {
            border: 2px solid #000000;
            border-radius: 8px;
            background: #ffffff;
            padding: 12px;
            min-height: 100%;
            box-sizing: border-box;
        }

        .bar-row {
            display: grid;
            grid-template-columns: minmax(96px, 1fr) 2.4fr 74px;
            align-items: center;
            gap: 12px;
            margin: 9px 0;
        }

        .bar-name {
            color: #000000;
            font-size: 13px;
            font-weight: 800;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .bar-track {
            height: 14px;
            border: 2px solid #000000;
            border-radius: 999px;
            background: #ffffff;
            overflow: hidden;
        }

        .bar-fill {
            height: 100%;
            background: #000000;
            border-radius: 999px;
        }

        .color-bar-fill {
            height: 100%;
            border-radius: 999px;
        }

        .bar-value {
            color: #000000;
            font-size: 12px;
            font-weight: 800;
            text-align: right;
            white-space: nowrap;
        }

        .split-bar {
            display: grid;
            grid-template-columns: var(--ocupado, 0%) 1fr;
            height: 36px;
            border: 2px solid #000000;
            border-radius: 999px;
            overflow: hidden;
            background: #ffffff;
        }

        .split-bar .occupied {
            background: #000000;
        }

        .split-labels {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            margin-top: 8px;
            color: #000000;
            font-size: 12px;
            font-weight: 800;
        }

        .donut-wrap {
            display: grid;
            grid-template-columns: 158px 1fr;
            gap: .3cm;
            align-items: center;
        }

        .metric-grid,
        .dashboard-grid {
            display: grid;
            gap: .3cm;
            margin-bottom: .3cm;
        }

        .metric-grid {
            grid-template-columns: repeat(5, minmax(0, 1fr));
        }

        .dashboard-grid.two {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .dashboard-grid.wide {
            grid-template-columns: .9fr 1.4fr;
        }

        .metric-grid .kpi-card,
        .dashboard-grid .chart-panel {
            height: 100%;
            margin-bottom: 0 !important;
        }

        .donut {
            width: 148px;
            height: 148px;
            border-radius: 50%;
            border: 2px solid #000000;
            background: var(--donut-gradient);
            position: relative;
        }

        .donut::after {
            content: "";
            position: absolute;
            inset: 34px;
            border-radius: 50%;
            background: #ffffff;
            border: 2px solid #000000;
        }

        .legend-row {
            display: grid;
            grid-template-columns: 13px minmax(0, 1fr) 48px;
            gap: 8px;
            align-items: center;
            margin: 8px 0;
            color: #000000;
            font-size: 12px;
            font-weight: 800;
        }

        .legend-swatch {
            width: 13px;
            height: 13px;
            border: 1px solid #000000;
            border-radius: 3px;
        }

        .legend-name {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .mini-table {
            width: 100%;
            border-collapse: collapse;
            overflow: hidden;
            border: 2px solid #000000;
            border-radius: 12px;
            font-size: 13px;
        }

        .mini-table th {
            padding: 10px 12px;
            border: 1px solid #000000;
            background: #000000;
            color: #ffffff;
            text-align: left;
            font-weight: 850;
        }

        .mini-table td {
            padding: 10px 12px;
            border: 1px solid #000000;
            color: #000000;
            background: #ffffff;
        }

        .mini-table td.num,
        .mini-table th.num {
            text-align: right;
        }

        .table-scroll {
            max-height: 520px;
            overflow: auto;
            border: 2px solid #000000;
            border-radius: 12px;
        }

        .table-scroll .mini-table {
            border: 0;
            border-radius: 0;
        }

        .table-scroll .mini-table th {
            position: sticky;
            top: 0;
            z-index: 2;
        }

        .insight-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
        }

        .insight {
            border: 2px solid #000000;
            border-radius: 12px;
            padding: 14px;
            background: #ffffff;
        }

        .insight-label {
            color: #555555;
            font-size: 11px;
            font-weight: 850;
            text-transform: uppercase;
        }

        .insight-value {
            margin-top: 5px;
            color: #000000;
            font-size: 16px;
            font-weight: 850;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .mobile-card {
            border: 2px solid #000000;
            border-radius: 10px;
            background: #ffffff;
            padding: 12px;
            margin-bottom: .3cm;
        }

        .mobile-card-title {
            color: #000000;
            font-size: 14px;
            font-weight: 850;
            line-height: 1.25;
        }

        .mobile-card-subtitle {
            margin-top: 4px;
            color: #333333;
            font-size: 12px;
            line-height: 1.35;
        }

        .mobile-card-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 10px;
        }

        .mobile-pill {
            display: inline-flex;
            align-items: center;
            min-height: 26px;
            padding: 4px 8px;
            border: 1px solid #000000;
            border-radius: 999px;
            background: #ffffff;
            color: #000000;
            font-size: 11px;
            font-weight: 800;
        }

        @media (max-width: 900px) {
            .page-head,
            .home-hero {
                grid-template-columns: 1fr;
                flex-direction: column;
            }

            .metric-grid,
            .dashboard-grid.two,
            .dashboard-grid.wide,
            .donut-wrap {
                grid-template-columns: 1fr;
            }

        .home-title {
                font-size: 28px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def aplicar_layout_mobile():
    st.markdown(
        """
        <style>
        .block-container,
        [data-testid="stMainBlockContainer"] {
            max-width: 480px !important;
            padding-left: .85rem !important;
            padding-right: .85rem !important;
            padding-top: .35rem !important;
        }

        .home-hero {
            min-height: auto;
            padding: 16px;
            border-radius: 12px;
            gap: 14px;
        }

        .home-title {
            font-size: 26px !important;
            line-height: 1.08;
        }

        .home-copy {
            font-size: 14px;
            line-height: 1.45;
        }

        .home-panel {
            padding: 12px;
            border-radius: 10px;
        }

        [data-testid="stSidebar"] {
            width: 15.5rem !important;
            min-width: 15.5rem !important;
        }

        .page-head {
            gap: 10px;
            margin-bottom: .75rem;
        }

        .page-title h1 {
            font-size: 23px;
        }

        .page-title p {
            font-size: 12px;
            line-height: 1.35;
        }

        .page-logos img {
            max-height: 24px;
            max-width: 82px;
        }

        .stButton > button {
            min-height: 44px;
        }

        div[data-testid="stDataFrame"],
        div[data-testid="stTable"] {
            font-size: 12px;
        }

        .kpi-card,
        .panel,
        .chart-panel {
            padding: 12px;
            border-radius: 10px;
        }

        .kpi-value {
            font-size: 24px;
        }

        .mini-table {
            font-size: 12px;
        }

        .mini-table th,
        .mini-table td {
            padding: 8px;
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
    if "menu_lateral_aberto" not in st.session_state:
        st.session_state.menu_lateral_aberto = False

    if st.button("Menu", key="menu_lateral_toggle"):
        st.session_state.menu_lateral_aberto = not st.session_state.menu_lateral_aberto
        st.rerun()

    _aplicar_layout_menu(st.session_state.menu_lateral_aberto)

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


def _aplicar_layout_menu(menu_aberto):
    left = "18.85rem" if menu_aberto else "0.75rem"
    sidebar_css = (
        """
        [data-testid="stSidebar"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: fixed !important;
            left: 0 !important;
            top: 0 !important;
            bottom: 0 !important;
            transform: translateX(0) !important;
            min-width: 17.75rem !important;
            width: 17.75rem !important;
            max-width: 17.75rem !important;
            height: 100vh !important;
            background: #ffffff !important;
            border-right: 1px solid #000000 !important;
            z-index: 999998 !important;
            overflow-y: auto !important;
        }

        [data-testid="stSidebar"] > div,
        [data-testid="stSidebarContent"],
        [data-testid="stSidebarUserContent"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: 100% !important;
        }
        """
        if menu_aberto
        else """
        [data-testid="stSidebar"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
        }
        """
    )

    st.markdown(
        f"""
        <style>
        {sidebar_css}

        .st-key-menu_lateral_toggle {{
            position: sticky !important;
            top: .35rem !important;
            left: {left} !important;
            z-index: 999999 !important;
            width: 82px !important;
            margin: 0 0 .3cm 0 !important;
            padding: 0 !important;
        }}

        .st-key-menu_lateral_toggle button {{
            min-height: 36px !important;
            padding: 0 14px !important;
            border: 2px solid #000000 !important;
            border-radius: 8px !important;
            background: #ffffff !important;
            color: #000000 !important;
            font-weight: 800 !important;
            box-shadow: none !important;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


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


def preparar_pagina(titulo, subtitulo="", mobile=False):
    aplicar_layout()
    if mobile:
        aplicar_layout_mobile()
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
