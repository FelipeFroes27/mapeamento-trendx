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
    buscar_produto,
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
    "Entrada de Material",
    "Cadastre vagas, inclua produtos e atualize saldos nas posições.",
    mobile=True,
    pagina="entrada",
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


def render_itens_vaga(itens):

    linhas = []

    for linha in itens:

        codigo_item = str(
            linha.get("Código", "")
        ).strip()

        descricao_item = str(
            linha.get("Descrição", "")
        ).strip()

        quantidade_item = str(
            linha.get("Quantidade", "")
        ).strip()

        if not codigo_item and not descricao_item:

            continue

        linhas.append(
            f'<div class="mobile-card">'
            f'<div class="mobile-card-title">{escape(codigo_item)} | Qtd: {escape(quantidade_item)}</div>'
            f'<div class="mobile-card-subtitle">{escape(descricao_item)}</div>'
            f'</div>'
        )

    if linhas:

        st.markdown(
            '<div class="panel-title">Itens na vaga</div>'
            + ''.join(linhas),
            unsafe_allow_html=True
        )


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
    "entrada_vaga"
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
# MOSTRAR VAGA
# ====================================

if vaga_existe:

    render_itens_vaga(
        resultados_vaga
    )

elif vaga:

    st.warning(
        "Vaga ainda não existe no sistema"
    )


# ====================================
# PRODUTO
# ====================================

codigos_produtos = listar_valores_unicos(
    dados_bd,
    "Código"
)

codigo = str(
    selectbox_digitavel(
        "Código do produto",
        codigos_produtos,
        "entrada_codigo"
    )
).strip().upper()


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

    st.markdown(
        f'<div class="readonly-label">Descrição</div>'
        f'<div class="readonly-field">{escape(descricao)}</div>',
        unsafe_allow_html=True
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
    ).strip().upper()


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
).strip().upper()


# ====================================
# REFERENCIA
# ====================================

referencia = st.text_input(
    "Referência"
).strip().upper()


# ====================================
# OBSERVAÇÕES
# ====================================

observacoes = st.text_area(
    "Observações"
).strip().upper()


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

if "entrada_processando" not in st.session_state:

    st.session_state.entrada_processando = False

if "entrada_revisando" not in st.session_state:

    st.session_state.entrada_revisando = False


def marcar_entrada_processando():

    st.session_state.entrada_processando = True


def erro_entrada(mensagem):

    st.session_state.entrada_processando = False

    st.session_state.entrada_revisando = False

    st.error(
        mensagem
    )

    st.stop()


def render_revisao_entrada():

    if vaga_existe and produto_igual:

        operacao = "Produto será somado na vaga existente"

    elif vaga_existe and possui_outro_produto:

        operacao = f"Produto diferente: {modo_operacao or 'definir operação'}"

    elif vaga_existe:

        operacao = "Produto será incluído na vaga disponível"

    elif codigo:

        operacao = "Vaga nova será cadastrada com produto"

    else:

        operacao = "Vaga nova será cadastrada como disponível"

    st.markdown(
        f'<div class="mobile-card">'
        f'<div class="mobile-card-title">Revisar Entrada</div>'
        f'<div class="mobile-card-subtitle">Confira antes de gravar a movimentação.</div>'
        f'<div class="mobile-card-meta">'
        f'<span class="mobile-pill">Vaga: {escape(vaga)}</span>'
        f'<span class="mobile-pill">Código: {escape(codigo or "-")}</span>'
        f'<span class="mobile-pill">Qtd: {int(quantidade)}</span>'
        f'<span class="mobile-pill">Usuário: {escape(usuario or "-")}</span>'
        f'<span class="mobile-pill">Referência: {escape(referencia or "-")}</span>'
        f'<span class="mobile-pill">{escape(operacao)}</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )


if not st.session_state.entrada_revisando:

    if st.button(
        "REVISAR ENTRADA",
        disabled=st.session_state.entrada_processando
    ):

        st.session_state.entrada_revisando = True

        st.rerun()

else:

    render_revisao_entrada()

    col_editar, col_confirmar = st.columns(2)

    with col_editar:

        if st.button(
            "EDITAR",
            use_container_width=True
        ):

            st.session_state.entrada_revisando = False

            st.rerun()

    with col_confirmar:

        st.button(

            "CONFIRMAR ENTRADA",

            disabled=st.session_state.entrada_processando,

            on_click=marcar_entrada_processando,

            use_container_width=True

        )

confirmar = st.session_state.entrada_processando


# ====================================
# PROCESSAMENTO
# ====================================

if confirmar:

    # ====================================
    # VALIDAÇÕES
    # ====================================

    if not vaga:

        erro_entrada(
            "Digite a vaga"
        )

    elif not usuario:

        erro_entrada(
            "Digite o usuário"
        )

    elif vaga_existe and not codigo:

        erro_entrada(
            "Digite o código"
        )

    elif vaga_existe and not descricao:

        erro_entrada(
            "Descrição inválida"
        )

    elif codigo and not descricao:

        erro_entrada(
            "Descrição inválida"
        )

    else:

        assinatura_entrada = (
            vaga,
            codigo,
            int(quantidade),
            usuario,
            referencia,
            observacoes
        )

        ultima_assinatura = st.session_state.get(
            "ultima_entrada_assinatura"
        )

        ultimo_horario = st.session_state.get(
            "ultima_entrada_horario"
        )

        agora = datetime.now()

        if (
            assinatura_entrada == ultima_assinatura
            and ultimo_horario is not None
            and (agora - ultimo_horario).total_seconds() < 10
        ):

            erro_entrada(
                "Esta entrada já foi registrada há poucos segundos. Atualize a tela antes de tentar novamente."
            )

        dados_posicao_atual = ler_aba_atual(
            "Mapeamento Trendx",
            "POSIÇÃO"
        )

        resultado_vaga_atual = buscar_vaga(
            vaga,
            dados_posicao_atual
        )

        vaga_existe_atual = resultado_vaga_atual[
            "vaga_existe"
        ]

        resultados_vaga_atual = resultado_vaga_atual[
            "resultados"
        ]

        aba_posicao = abrir_aba(
            "Mapeamento Trendx",
            "POSIÇÃO"
        )

        if vaga_existe_atual and not codigo:

            erro_entrada(
                "A vaga já existe. Para cadastrar apenas uma vaga vazia, informe uma vaga nova."
            )

        data_atual = datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )


        # ====================================
        # VAGA NOVA
        # ====================================

        if not vaga_existe_atual:

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

            possui_outro_produto_atual = False

            for linha in resultados_vaga_atual:

                codigo_existente_atual = str(
                    linha["Código"]
                ).strip().upper()

                if (
                    codigo_existente_atual
                    and codigo_existente_atual != codigo
                ):

                    possui_outro_produto_atual = True


            # ====================================
            # SOMAR PRODUTO
            # ====================================

            for linha in resultados_vaga_atual:

                codigo_existente = str(
                    linha["Código"]
                ).strip().upper()

                if codigo_existente == codigo:

                    produto_encontrado_vaga = True

                    linha_real = linha[
                        "_linha_planilha"
                    ]

                    quantidade_atual = quantidade_int(
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

                if (
                    possui_outro_produto_atual
                    and modo_operacao is None
                ):

                    erro_entrada(
                        "A vaga mudou enquanto você operava. Atualize a tela e confirme novamente."
                    )


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

                    for linha in resultados_vaga_atual:

                        codigo_existente = str(
                            linha["Código"]
                        ).strip().upper()

                        if codigo_existente == codigo_substituir:

                            linha_real = linha[
                                "_linha_planilha"
                            ]

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

                    linha_real = resultados_vaga_atual[0][
                        "_linha_planilha"
                    ]

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


        st.session_state.ultima_entrada_assinatura = assinatura_entrada

        st.session_state.ultima_entrada_horario = datetime.now()


        st.cache_data.clear()


        # ====================================
        # VOLTA INICIO
        # ====================================

        st.session_state.entrada_processando = False

        st.session_state.entrada_revisando = False

        st.switch_page("app.py")
