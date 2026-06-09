import streamlit as st

from utils.ui import preparar_pagina


st.set_page_config(
    page_title="Mapeamento Trendx",
    layout="wide",
    initial_sidebar_state="expanded",
)

preparar_pagina(
    "Mapeamento Trendx",
    "Controle de vagas, produtos, entradas, saídas e disponibilidade logística.",
    mobile=True,
)

st.markdown(
    """
    <div class="home-hero">
        <div>
            <h1 class="home-title">Espaço logístico sob controle</h1>
            <p class="home-copy">
                Consulte vagas, registre movimentações e acompanhe a ocupação do estoque
                em uma visão simples, direta e operacional.
            </p>
        </div>
        <div class="home-panel">
            <div class="home-panel-title">Como o sistema está organizado</div>
            <div class="home-section">
                POSIÇÃO
                <span>Base principal do mapa: vagas, status, produtos, saldos e observações.</span>
            </div>
            <div class="home-section">
                HISTÓRICO
                <span>Registro das movimentações de entrada e saída feitas no estoque.</span>
            </div>
            <div class="home-section">
                BD PRODUTOS
                <span>Cadastro auxiliar para classificar produto por categoria, tipo e marca.</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
