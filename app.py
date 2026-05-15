import streamlit as st


st.set_page_config(
    page_title="Mapeamento Trendx",
    layout="wide"
)


if "pagina" not in st.session_state:

    st.session_state.pagina = "menu"


# ====================================
# MENU
# ====================================

if st.session_state.pagina == "menu":

    st.title("📦 Mapeamento Trendx")

    st.write("Escolha a operação")

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🟢 ENTRADA",
            use_container_width=True
        ):

            st.session_state.pagina = "entrada"

            st.rerun()

    with col2:

        if st.button(
            "🔴 SAÍDA",
            use_container_width=True
        ):

            st.session_state.pagina = "saida"

            st.rerun()


# ====================================
# ENTRADA
# ====================================

elif st.session_state.pagina == "entrada":

    exec(open("entrada.py", encoding="utf-8").read())


# ====================================
# SAÍDA
# ====================================

elif st.session_state.pagina == "saida":

    exec(open("saida.py", encoding="utf-8").read())