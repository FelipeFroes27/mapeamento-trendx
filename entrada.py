import streamlit as st
import pandas as pd
from datetime import datetime

from utils.sheets import (
    ler_aba,
    abrir_aba
)

from utils.estoque import (
    buscar_vaga,
    buscar_produto
)

from utils.historico import (
    registrar_historico
)

from utils.ui import preparar_pagina


# ====================================
# LAYOUT
# ====================================

preparar_pagina(
    "Entrada de Material",
    "Cadastre vagas, inclua produtos e atualize saldos nas posições.",
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


if "dados_bd" not in st.session_state:

    st.session_state.dados_bd = ler_aba(
        "Mapeamento Trendx",
        "BD PRODUTOS"
    )


dados_posicao = st.session_state.dados_posicao

dados_bd = st.session_state.dados_bd


# ====================================
# VAGA
# ====================================

vaga = st.text_input(
    "Vaga"
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
# MOSTRAR VAGA
# ====================================

if vaga_existe:

    tabela_vaga = []

    for linha in resultados_vaga:

        tabela_vaga.append({

            "Código": linha["Código"],
            "Descrição": linha["Descrição"],
            "Quantidade": linha["Quantidade"]

        })

    st.table(
        pd.DataFrame(tabela_vaga)
    )

elif vaga:

    st.warning(
        "Vaga ainda não existe no sistema"
    )


# ====================================
# PRODUTO
# ====================================

codigo = st.text_input(
    "Código do produto"
).strip()


resultado_produto = buscar_produto(
    codigo,
    dados_bd
)

produto_encontrado = resultado_produto[
    "produto_encontrado"
]

descricao = resultado_produto[
    "descricao"
]


# ====================================
# PRODUTO ENCONTRADO
# ====================================

if codigo and produto_encontrado:

    st.success(
        "Produto encontrado no BD"
    )

    st.text_input(

        "Descrição",

        value=descricao,

        disabled=True

    )


# ====================================
# PRODUTO NÃO ENCONTRADO
# ====================================

elif codigo:

    st.warning(
        "Produto não existe no banco de dados"
    )

    descricao = st.text_input(
        "Digite a descrição manualmente"
    ).strip()


# ====================================
# QUANTIDADE
# ====================================

quantidade = st.number_input(

    "Quantidade",

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
# REFERENCIA
# ====================================

referencia = st.text_input(
    "Referência"
).strip()


# ====================================
# OBSERVAÇÕES
# ====================================

observacoes = st.text_area(
    "Observações"
).strip()


# ====================================
# ANÁLISE DA VAGA
# ====================================

produto_igual = False

possui_outro_produto = False

modo_operacao = None

linha_substituir = None

produtos_vaga = []


if vaga_existe and resultados_vaga and codigo:

    for linha in resultados_vaga:

        codigo_existente = str(
            linha["Código"]
        ).strip()

        if codigo_existente == codigo:

            produto_igual = True

        elif codigo_existente != "":

            possui_outro_produto = True

            produtos_vaga.append(

                f'{linha["Código"]} - '
                f'{linha["Descrição"]}'

            )


    # ====================================
    # SOMAR
    # ====================================

    if produto_igual:

        st.info(
            "Produto já existe na vaga. A quantidade será somada."
        )


    # ====================================
    # PRODUTO DIFERENTE
    # ====================================

    elif possui_outro_produto:

        modo_operacao = st.radio(

            "Produto diferente encontrado na vaga",

            [
                "MANTER AMBOS",
                "SUBSTITUIR"
            ]

        )


        # ====================================
        # SUBSTITUIR
        # ====================================

        if modo_operacao == "SUBSTITUIR":

            linha_substituir = st.selectbox(

                "Selecione o produto que será substituído",

                produtos_vaga

            )


# ====================================
# BOTÃO
# ====================================

confirmar = st.button(
    "CONFIRMAR ENTRADA"
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

    elif not usuario:

        st.error(
            "Digite o usuário"
        )

    elif vaga_existe and not codigo:

        st.error(
            "Digite o código"
        )

    elif vaga_existe and not descricao:

        st.error(
            "Descrição inválida"
        )

    elif codigo and not descricao:

        st.error(
            "Descrição inválida"
        )

    else:

        aba_posicao = abrir_aba(
            "Mapeamento Trendx",
            "POSIÇÃO"
        )

        data_atual = datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )


        # ====================================
        # VAGA NOVA
        # ====================================

        if not vaga_existe:

            # ====================================
            # VAGA NOVA COM PRODUTO
            # ====================================

            if codigo:

                aba_posicao.append_row([

                    "OCUPADO",
                    data_atual,
                    vaga,
                    codigo,
                    descricao,
                    quantidade,
                    referencia,
                    observacoes

                ])

            # ====================================
            # VAGA NOVA VAZIA
            # ====================================

            else:

                aba_posicao.append_row([

                    "DISPONIVEL",
                    data_atual,
                    vaga,
                    "",
                    "",
                    "",
                    "",
                    ""

                ])


        # ====================================
        # VAGA EXISTE
        # ====================================

        else:

            produto_encontrado_vaga = False


            # ====================================
            # SOMAR PRODUTO
            # ====================================

            for linha in resultados_vaga:

                codigo_existente = str(
                    linha["Código"]
                ).strip()

                if codigo_existente == codigo:

                    produto_encontrado_vaga = True

                    linha_real = (
                        dados_posicao.index(linha)
                        + 2
                    )

                    quantidade_atual = int(
                        linha["Quantidade"]
                    )

                    nova_quantidade = (
                        quantidade_atual + quantidade
                    )

                    aba_posicao.update(

                        f"F{linha_real}",
                        [[nova_quantidade]]

                    )

                    aba_posicao.update(

                        f"B{linha_real}",
                        [[data_atual]]

                    )

                    aba_posicao.update(

                        f"G{linha_real}",
                        [[referencia]]

                    )

                    aba_posicao.update(

                        f"H{linha_real}",
                        [[observacoes]]

                    )

                    break


            # ====================================
            # PRODUTO NOVO
            # ====================================

            if not produto_encontrado_vaga:


                # ====================================
                # MANTER AMBOS
                # ====================================

                if modo_operacao == "MANTER AMBOS":

                    aba_posicao.append_row([

                        "OCUPADO",
                        data_atual,
                        vaga,
                        codigo,
                        descricao,
                        quantidade,
                        referencia,
                        observacoes

                    ])


                # ====================================
                # SUBSTITUIR
                # ====================================

                elif modo_operacao == "SUBSTITUIR":

                    codigo_substituir = (

                        linha_substituir
                        .split(" - ")[0]

                    )

                    for linha in resultados_vaga:

                        codigo_existente = str(
                            linha["Código"]
                        ).strip()

                        if codigo_existente == codigo_substituir:

                            linha_real = (

                                dados_posicao.index(linha)
                                + 2

                            )

                            aba_posicao.update(

                                f"D{linha_real}",
                                [[codigo]]

                            )

                            aba_posicao.update(

                                f"E{linha_real}",
                                [[descricao]]

                            )

                            aba_posicao.update(

                                f"F{linha_real}",
                                [[quantidade]]

                            )

                            aba_posicao.update(

                                f"G{linha_real}",
                                [[referencia]]

                            )

                            aba_posicao.update(

                                f"H{linha_real}",
                                [[observacoes]]

                            )

                            aba_posicao.update(

                                f"B{linha_real}",
                                [[data_atual]]

                            )

                            break


                # ====================================
                # VAGA DISPONÍVEL
                # ====================================

                else:

                    linha_real = (

                        dados_posicao.index(
                            resultados_vaga[0]
                        ) + 2

                    )

                    aba_posicao.update(

                        f"A{linha_real}",
                        [["OCUPADO"]]

                    )

                    aba_posicao.update(

                        f"B{linha_real}",
                        [[data_atual]]

                    )

                    aba_posicao.update(

                        f"D{linha_real}",
                        [[codigo]]

                    )

                    aba_posicao.update(

                        f"E{linha_real}",
                        [[descricao]]

                    )

                    aba_posicao.update(

                        f"F{linha_real}",
                        [[quantidade]]

                    )

                    aba_posicao.update(

                        f"G{linha_real}",
                        [[referencia]]

                    )

                    aba_posicao.update(

                        f"H{linha_real}",
                        [[observacoes]]

                    )


        # ====================================
        # HISTÓRICO
        # ====================================

        if codigo:

            registrar_historico(

                data_atual,
                vaga,
                codigo,
                descricao,
                quantidade,
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
