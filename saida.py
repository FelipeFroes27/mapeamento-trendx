import streamlit as st
import pandas as pd
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

from utils.ui import preparar_pagina


# ====================================
# LAYOUT
# ====================================

preparar_pagina(
    "Saída de Material",
    "Retire produtos, atualize saldos e libere vagas disponíveis.",
    mobile=True,
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

        return st.selectbox(
            label,
            [""] + opcoes,
            format_func=lambda valor: "Digite ou selecione..." if valor == "" else valor,
            accept_new_options=True,
            key=key
        )

    except TypeError:

        return st.text_input(
            label,
            key=key
        )


# ====================================
# VAGA
# ====================================

vagas_cadastradas = listar_valores_unicos(
    dados_posicao,
    "Vaga"
)

vaga = str(
    selectbox_digitavel(
        "Vaga",
        vagas_cadastradas,
        "saida_vaga"
    )
).strip().upper()


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
).strip()


# ====================================
# BOTÃO
# ====================================

confirmar = st.button(
    "CONFIRMAR SAÍDA"
)


# ====================================
# PROCESSAMENTO
# ====================================

if confirmar:

    # ====================================
    # VALIDAÇÕES
    # ====================================

    if not vaga:

        st.error(
            "Digite a vaga"
        )

    elif not vaga_existe:

        st.error(
            "Vaga não encontrada"
        )

    elif not linha_produto:

        st.error(
            "Selecione um produto"
        )

    elif not usuario:

        st.error(
            "Digite o usuário"
        )

    else:

        codigo_selecionado = str(
            linha_produto["Código"]
        ).strip()

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
            ).strip()

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

            st.error(
                "A vaga mudou enquanto você operava. Atualize a tela e confirme novamente."
            )

            st.stop()

        quantidade_atual = quantidade_int(
            linha_produto_atual["Quantidade"]
        )

        validacao = validar_saida(

            quantidade_atual,
            quantidade_saida

        )

        if not validacao["valido"]:

            st.error(
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
            ).strip()

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

            st.switch_page("app.py")
