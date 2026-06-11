import streamlit as st
import pandas as pd
from html import escape
from datetime import datetime

from utils.sheets import (
    ler_aba,
    abrir_aba,
    ler_aba_atual
)

from utils.estoque import (

    buscar_vaga,
    validar_saida,
    ultimo_produto_vaga,
    listar_valores_unicos,
    quantidade_int

)

from utils.historico import (
    registrar_historico
)

from utils.ui import preparar_pagina, campo_vaga_editavel


# ====================================
# LAYOUT
# ====================================

preparar_pagina(
    "Saída de Material",
    "Retire produtos, atualize saldos e libere vagas disponíveis.",
    mobile=True,
    pagina="saida",
)

if st.button("Voltar ao início"):
    st.switch_page("app.py")


# ====================================
# CACHE
# ====================================

if "dados_posicao" not in st.session_state:

    st.session_state.dados_posicao = ler_aba(
        "Mapeamento Trendx",
        "POSIÇÃO"
    )


dados_posicao = st.session_state.dados_posicao


def selectbox_digitavel(label, opcoes, key):

    try:

        valor = st.selectbox(
            label,
            [""] + opcoes,
            format_func=lambda valor: "Digite ou selecione..." if valor == "" else valor,
            accept_new_options=True,
            key=key
        )

        return str(
            valor
        ).strip().upper()

    except TypeError:

        return st.text_input(
            label,
            key=key
        ).strip().upper()


# ====================================
# VAGA
# ====================================

vagas_cadastradas = listar_valores_unicos(
    dados_posicao,
    "Vaga"
)

vaga = campo_vaga_editavel(
    "Vaga",
    vagas_cadastradas,
    "saida_vaga"
)


resultado_vaga = buscar_vaga(
    vaga,
    dados_posicao
)

vaga_existe = resultado_vaga[
    "vaga_existe"
]

resultados_vaga = resultado_vaga[
    "resultados"
]


# ====================================
# VAGA NÃO EXISTE
# ====================================

if vaga and not vaga_existe:

    st.error(
        "Vaga não encontrada"
    )


# ====================================
# FILTRAR PRODUTOS
# ====================================

produtos_vaga = []

linhas_produtos = {}


if vaga_existe:

    for linha in resultados_vaga:

        codigo = str(
            linha["Código"]
        ).strip()

        descricao = str(
            linha["Descrição"]
        ).strip()

        quantidade = str(
            linha["Quantidade"]
        ).strip()

        status = str(
            linha["Status"]
        ).strip().upper()

        # ====================================
        # IGNORA DISPONIVEL
        # ====================================

        if status == "DISPONIVEL":

            continue

        texto = (

            f"{codigo} | "
            f"{descricao} | "
            f"Qtd: {quantidade}"

        )

        produtos_vaga.append(
            texto
        )

        linhas_produtos[texto] = linha


# ====================================
# VAGA DISPONIVEL
# ====================================

if vaga_existe and len(produtos_vaga) == 0:

    st.warning(
        "Vaga está DISPONIVEL"
    )


# ====================================
# PRODUTOS DA VAGA
# ====================================

produto_selecionado = None

linha_produto = None


if len(produtos_vaga) > 0:

    st.subheader(
        "Produtos da vaga"
    )

    produto_selecionado = st.selectbox(

        "Selecione o produto",

        produtos_vaga

    )

    linha_produto = linhas_produtos[
        produto_selecionado
    ]


# ====================================
# QUANTIDADE ATUAL
# ====================================

quantidade_atual = 0

if linha_produto:

    try:

        quantidade_atual = int(
            linha_produto["Quantidade"]
        )

    except (TypeError, ValueError):

        quantidade_atual = 0

    st.info(
        f"Quantidade atual: {quantidade_atual}"
    )

    st.markdown(
        f'<div class="readonly-label">Descrição</div>'
        f'<div class="readonly-field">{escape(str(linha_produto.get("Descrição", "")).strip())}</div>',
        unsafe_allow_html=True
    )


# ====================================
# QUANTIDADE SAÍDA
# ====================================

quantidade_saida = st.number_input(

    "Quantidade para retirada",

    min_value=1,

    step=1

)


# ====================================
# USUÁRIO
# ====================================

usuario = st.text_input(
    "Usuário"
).strip().upper()


# ====================================
# BOTÃO
# ====================================

if "saida_processando" not in st.session_state:

    st.session_state.saida_processando = False

if "saida_revisando" not in st.session_state:

    st.session_state.saida_revisando = False


def marcar_saida_processando():

    st.session_state.saida_processando = True


def erro_saida(mensagem):

    st.session_state.saida_processando = False

    st.session_state.saida_revisando = False

    st.error(
        mensagem
    )

    st.stop()


def render_revisao_saida():

    saldo_final_previsto = max(
        quantidade_atual - int(quantidade_saida),
        0
    )

    operacao = (
        "Saída total: vaga será liberada"
        if saldo_final_previsto == 0
        else "Saída parcial: saldo será atualizado"
    )

    codigo_revisao = ""

    descricao_revisao = ""

    if linha_produto:

        codigo_revisao = str(
            linha_produto.get("Código", "")
        ).strip()

        descricao_revisao = str(
            linha_produto.get("Descrição", "")
        ).strip()

    st.markdown(
        f'<div class="mobile-card">'
        f'<div class="mobile-card-title">Revisar Saída</div>'
        f'<div class="mobile-card-subtitle">{escape(descricao_revisao)}</div>'
        f'<div class="mobile-card-meta">'
        f'<span class="mobile-pill">Vaga: {escape(vaga)}</span>'
        f'<span class="mobile-pill">Código: {escape(codigo_revisao or "-")}</span>'
        f'<span class="mobile-pill">Atual: {quantidade_atual}</span>'
        f'<span class="mobile-pill">Retirar: {int(quantidade_saida)}</span>'
        f'<span class="mobile-pill">Saldo final: {saldo_final_previsto}</span>'
        f'<span class="mobile-pill">Usuário: {escape(usuario or "-")}</span>'
        f'<span class="mobile-pill">{escape(operacao)}</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )


if not st.session_state.saida_revisando:

    if st.button(
        "REVISAR SAÍDA",
        disabled=st.session_state.saida_processando
    ):

        st.session_state.saida_revisando = True

        st.rerun()

else:

    render_revisao_saida()

    col_editar, col_confirmar = st.columns(2)

    with col_editar:

        if st.button(
            "EDITAR",
            use_container_width=True
        ):

            st.session_state.saida_revisando = False

            st.rerun()

    with col_confirmar:

        st.button(

            "CONFIRMAR SAÍDA",

            disabled=st.session_state.saida_processando,

            on_click=marcar_saida_processando,

            use_container_width=True

        )

confirmar = st.session_state.saida_processando


# ====================================
# PROCESSAMENTO
# ====================================

if confirmar:

    # ====================================
    # VALIDAÇÕES
    # ====================================

    if not vaga:

        erro_saida(
            "Digite a vaga"
        )

    elif not vaga_existe:

        erro_saida(
            "Vaga não encontrada"
        )

    elif not linha_produto:

        erro_saida(
            "Selecione um produto"
        )

    elif not usuario:

        erro_saida(
            "Digite o usuário"
        )

    else:

        codigo_selecionado = str(
            linha_produto["Código"]
        ).strip().upper()

        assinatura_saida = (
            vaga,
            codigo_selecionado,
            int(quantidade_saida),
            usuario
        )

        ultima_assinatura = st.session_state.get(
            "ultima_saida_assinatura"
        )

        ultimo_horario = st.session_state.get(
            "ultima_saida_horario"
        )

        agora = datetime.now()

        if (
            assinatura_saida == ultima_assinatura
            and ultimo_horario is not None
            and (agora - ultimo_horario).total_seconds() < 10
        ):

            erro_saida(
                "Esta saída já foi registrada há poucos segundos. Atualize a tela antes de tentar novamente."
            )

        dados_posicao_atual = ler_aba_atual(
            "Mapeamento Trendx",
            "POSIÇÃO"
        )

        resultado_vaga_atual = buscar_vaga(
            vaga,
            dados_posicao_atual
        )

        resultados_vaga_atual = resultado_vaga_atual[
            "resultados"
        ]

        linha_produto_atual = None

        for linha in resultados_vaga_atual:

            codigo_atual = str(
                linha["Código"]
            ).strip().upper()

            status_atual = str(
                linha["Status"]
            ).strip().upper()

            if (
                codigo_atual == codigo_selecionado
                and status_atual != "DISPONIVEL"
            ):

                linha_produto_atual = linha

                break

        if linha_produto_atual is None:

            erro_saida(
                "A vaga mudou enquanto você operava. Atualize a tela e confirme novamente."
            )

        quantidade_atual = quantidade_int(
            linha_produto_atual["Quantidade"]
        )

        validacao = validar_saida(

            quantidade_atual,
            quantidade_saida

        )

        if not validacao["valido"]:

            erro_saida(
                validacao["mensagem"]
            )

        else:

            aba_posicao = abrir_aba(
                "Mapeamento Trendx",
                "POSIÇÃO"
            )

            data_atual = datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"
            )

            saldo_final = (
                quantidade_atual
                - quantidade_saida
            )

            linha_real = linha_produto_atual[
                "_linha_planilha"
            ]

            codigo = str(
                linha_produto_atual["Código"]
            ).strip().upper()

            descricao = str(
                linha_produto_atual["Descrição"]
            ).strip()


            # ====================================
            # RETIRADA PARCIAL
            # ====================================

            if saldo_final > 0:

                aba_posicao.update(

                    f"F{linha_real}",

                    [[saldo_final]]

                )

                aba_posicao.update(

                    f"B{linha_real}",

                    [[data_atual]]

                )


            # ====================================
            # RETIRADA TOTAL
            # ====================================

            else:

                ultimo_produto = ultimo_produto_vaga(
                    resultados_vaga_atual
                )


                # ====================================
                # ULTIMO PRODUTO
                # ====================================

                if ultimo_produto:

                    aba_posicao.update(

                        f"A{linha_real}",

                        [["DISPONIVEL"]]

                    )

                    aba_posicao.update(

                        f"B{linha_real}",

                        [[data_atual]]

                    )

                    aba_posicao.update(

                        f"D{linha_real}",

                        [[""]]

                    )

                    aba_posicao.update(

                        f"E{linha_real}",

                        [[""]]

                    )

                    aba_posicao.update(

                        f"F{linha_real}",

                        [[""]]

                    )

                    aba_posicao.update(

                        f"G{linha_real}",

                        [[""]]

                    )

                    aba_posicao.update(

                        f"H{linha_real}",

                        [[""]]

                    )


                # ====================================
                # EXISTEM OUTROS PRODUTOS
                # ====================================

                else:

                    aba_posicao.delete_rows(
                        linha_real
                    )


            # ====================================
            # HISTÓRICO
            # ====================================

            registrar_historico(

                data_atual,
                vaga,
                codigo,
                descricao,
                quantidade_saida * -1,
                usuario

            )


            st.session_state.ultima_saida_assinatura = assinatura_saida

            st.session_state.ultima_saida_horario = datetime.now()


            # ====================================
            # LIMPA CACHE
            # ====================================

            st.cache_data.clear()


            # ====================================
            # ATUALIZA CACHE
            # ====================================

            st.session_state.dados_posicao = ler_aba(
                "Mapeamento Trendx",
                "POSIÇÃO"
            )


            # ====================================
            # VOLTA INICIO
            # ====================================

            st.session_state.saida_processando = False

            st.session_state.saida_revisando = False

            st.switch_page("app.py")
