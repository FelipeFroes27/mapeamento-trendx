import streamlit as st

from utils.ui import aplicar_layout, render_menu_lateral, render_cabecalho


st.set_page_config(
    page_title="Mapeamento Trendx",
    layout="wide",
    initial_sidebar_state="expanded",
)

aplicar_layout()
render_menu_lateral()
render_cabecalho(
    "Mapeamento Trendx",
    "Controle de vagas, produtos, entradas, saídas e disponibilidade logística.",
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
            <div class="home-panel-title">Operações principais</div>
            <div class="home-section">
                Entrada
                <span>Cadastrar vaga, inserir produto, somar saldo ou substituir item.</span>
            </div>
            <div class="home-section">
                Saída
                <span>Retirar produtos da vaga, baixar saldo e liberar posições.</span>
            </div>
            <div class="home-section">
                Consulta e indicadores
                <span>Ver produtos, histórico, dados do item e leitura de ocupação.</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

with col1:
    if st.button("Entrada", use_container_width=True):
        st.switch_page("pages/Entrada.py")

with col2:
    if st.button("Saída", use_container_width=True):
        st.switch_page("pages/Saida.py")
