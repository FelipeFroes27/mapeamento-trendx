"""Etiquetas EAN-13 geradas a partir das movimentações de vaga.

O cadastro (descrição, referência e EAN) vem da aba "Produtos" da planilha
"Agenda logistica", atualizada todo dia a partir do ERP. Este programa só lê
essa aba, nunca grava nela.

Depois de gravar a movimentação, as etiquetas vão para a fila de impressão
(utils/fila_impressao.py), que o agente do notebook do estoque imprime sozinho.
O PDF para baixar continua disponível para reimpressão.
"""

import math
import re
import time
from html import escape

import streamlit as st

from utils import fila_impressao as fila
from utils.etiquetas import escolher_ean, gerar_etiquetas_pdf
from utils.sheets import abrir_aba, abrir_planilha


PLANILHA_CADASTRO = "Agenda logistica"
ABA_CADASTRO = "Produtos"
VALIDADE_CADASTRO = 60 * 60  # 1 hora
COPIAS_MAXIMO = 5000
INTERVALO_STATUS = 5  # segundos entre consultas do status da impressão
LIMITE_ESPERA = 3 * 60  # depois disso para de consultar e avisa


# ====================================
# CADASTRO (cache de 1 hora)
# ====================================

@st.cache_resource
def _cache_cadastro():
    # cache_resource não é apagado pelo st.cache_data.clear() das movimentações
    return {"lido_em": 0.0, "produtos": {}}


def codigo_etiqueta(codigo):
    """'4164' -> '04164'. Código maior que 5 dígitos ou que não é número fica como está."""
    texto = str(codigo or "").strip().upper()
    if texto.isdigit():
        return texto.zfill(5)
    return texto


def _ler_cadastro():
    linhas = abrir_aba(PLANILHA_CADASTRO, ABA_CADASTRO).get_all_values()
    if not linhas:
        return {}

    cabecalho = [str(coluna).strip() for coluna in linhas[0]]
    produtos = {}

    for linha in linhas[1:]:
        registro = dict(zip(cabecalho, linha + [""] * (len(cabecalho) - len(linha))))
        codigo = codigo_etiqueta(registro.get("Codigo", ""))
        if not codigo:
            continue

        barras = [registro.get("EAN", "")] + re.split(r"[^0-9]+", registro.get("Outros EAN", ""))
        ean, _ = escolher_ean(barras)

        produtos[codigo] = {
            "descricao": str(registro.get("Descricao", "")).strip(),
            "referencia": str(registro.get("Referencia", "")).strip(),
            "ean": ean,
        }

    return produtos


def cadastro_produtos():
    cache = _cache_cadastro()
    if not cache["produtos"] or time.time() - cache["lido_em"] > VALIDADE_CADASTRO:
        cache["produtos"] = _ler_cadastro()
        cache["lido_em"] = time.time()
    return cache["produtos"]


# ====================================
# ITENS DA ETIQUETA
# ====================================

def copias_por_quantidade(quantidade):
    """Uma etiqueta por unidade, arredondando para cima. Mínimo 1."""
    try:
        valor = float(str(quantidade).replace(",", "."))
    except (TypeError, ValueError):
        valor = 1
    return min(max(math.ceil(valor), 1), COPIAS_MAXIMO)


def montar_item(codigo, descricao, referencia, quantidade):
    """Monta o item da etiqueta. Erro ao ler o cadastro não impede a etiqueta."""
    codigo = codigo_etiqueta(codigo)
    aviso_cadastro = ""

    try:
        produto = cadastro_produtos().get(codigo)
    except Exception:
        produto = None
        aviso_cadastro = "cadastro de produtos indisponível"

    produto = produto or {}

    return {
        "codigo": codigo,
        "descricao": (produto.get("descricao") or str(descricao or "")).strip().upper(),
        "referencia": produto.get("referencia") or str(referencia or "").strip() or "—",
        "ean": produto.get("ean", ""),
        "quantidade": None,
        "copias": copias_por_quantidade(quantidade),
        "encontrado": bool(produto),
        "aviso_cadastro": aviso_cadastro,
    }


# ====================================
# FILA DE IMPRESSÃO
# ====================================

@st.cache_resource
def _aba_fila():
    return fila.abrir_ou_criar_aba(
        abrir_planilha(fila.PLANILHA)
    )


def enviar_para_impressao(itens, movimentacao, vaga, usuario):
    """Grava as etiquetas na fila do agente. Devolve os IDs das linhas."""
    linhas = [
        fila.linha_da_fila(item, movimentacao, vaga, usuario)
        for item in itens
    ]
    _aba_fila().append_rows(linhas)
    return [linha[0] for linha in linhas]


def status_impressao(ids):
    """{id: (status, mensagem)} lido da fila."""
    linhas = _aba_fila().get_all_values()
    if not linhas:
        return {}

    cabecalho = linhas[0]
    i_id, i_status, i_mensagem = (cabecalho.index(nome) for nome in ("ID", "Status", "Mensagem"))
    procurados = set(ids)
    resultado = {}

    for linha in linhas[1:]:
        linha = linha + [""] * (len(cabecalho) - len(linha))
        if linha[i_id] in procurados:
            resultado[linha[i_id]] = (linha[i_status].strip().upper(), linha[i_mensagem].strip())

    return resultado


def _enviar_e_guardar(pacote, itens):
    try:
        ids = enviar_para_impressao(
            itens,
            pacote["movimentacao"],
            pacote["vaga"],
            pacote["usuario"],
        )
        pacote["envios"].append({"ids": ids, "total": sum(item["copias"] for item in itens), "status": {}, "enviado_em": time.time()})
        pacote["erro_fila"] = ""
    except Exception as erro:
        pacote["erro_fila"] = str(erro)


def preparar_etiquetas(chave, titulo, itens, movimentacao, vaga, usuario):
    """Envia as etiquetas da movimentação gravada para a impressora e guarda para o painel."""
    pacote = {
        "titulo": titulo,
        "itens": itens,
        "movimentacao": movimentacao,
        "vaga": vaga,
        "usuario": usuario,
        "envios": [],
        "erro_fila": "",
    }
    _enviar_e_guardar(pacote, [dict(item) for item in itens])
    st.session_state[chave] = pacote


# ====================================
# PAINEL
# ====================================

TEXTO_STATUS = {
    fila.PENDENTE: ("info", "Aguardando a impressora do estoque…"),
    fila.IMPRIMINDO: ("info", "Imprimindo…"),
    fila.IMPRESSO: ("success", "Impresso."),
    fila.ERRO: ("error", "Erro na impressão"),
}


def _render_status(chave):
    pacote = st.session_state.get(chave)
    if not pacote or not pacote["envios"]:
        return

    pendentes = [
        envio for envio in pacote["envios"]
        if time.time() - envio["enviado_em"] < LIMITE_ESPERA
        and (
            not envio["status"]
            or any(
                status not in (fila.IMPRESSO, fila.ERRO)
                for status, _ in envio["status"].values()
            )
        )
    ]

    if pendentes:
        try:
            lidos = status_impressao(
                [id_ for envio in pendentes for id_ in envio["ids"]]
            )
            for envio in pendentes:
                envio["status"] = {id_: lidos.get(id_, (fila.PENDENTE, "")) for id_ in envio["ids"]}
        except Exception:
            pass

    for numero, envio in enumerate(pacote["envios"], start=1):
        situacoes = list(envio["status"].values()) or [(fila.PENDENTE, "")]
        if any(status == fila.ERRO for status, _ in situacoes):
            status = fila.ERRO
        elif all(status == fila.IMPRESSO for status, _ in situacoes):
            status = fila.IMPRESSO
        elif any(status == fila.IMPRIMINDO for status, _ in situacoes):
            status = fila.IMPRIMINDO
        else:
            status = fila.PENDENTE

        tipo, texto = TEXTO_STATUS[status]
        mensagens = "; ".join(dict.fromkeys(m for s, m in situacoes if s == fila.ERRO and m))
        rotulo = "Impressão" if numero == 1 else f"Reimpressão {numero - 1}"
        linha = f"{rotulo} ({envio['total']} etiquetas): {texto}"
        if mensagens:
            linha += f" {mensagens}"
        if status in (fila.PENDENTE, fila.IMPRIMINDO) and time.time() - envio["enviado_em"] >= LIMITE_ESPERA:
            tipo = "warning"
            linha = (
                f"{rotulo} ({envio['total']} etiquetas): ainda não impresso. "
                "Confira se o notebook do estoque está ligado, ou baixe o PDF abaixo."
            )
        getattr(st, tipo)(linha)


def render_painel_etiquetas(chave):
    pacote = st.session_state.get(chave)
    if not pacote:
        return

    itens = pacote["itens"]

    st.success(
        pacote["titulo"]
    )

    if pacote["erro_fila"]:
        st.error(
            f"Não foi possível enviar para a impressora ({pacote['erro_fila']}). "
            "A movimentação continua gravada. Use o botão abaixo para baixar o PDF."
        )

    st.fragment(run_every=INTERVALO_STATUS)(_render_status)(chave)

    for item in itens:
        if item["aviso_cadastro"]:
            st.warning(
                f'{item["codigo"]}: {item["aviso_cadastro"]}. A etiqueta sai com os dados da movimentação.'
            )
        elif not item["encontrado"]:
            st.warning(
                f'{item["codigo"]}: código não encontrado no cadastro. A etiqueta sai com a descrição da movimentação.'
            )

    sem_ean = [item for item in itens if not item["ean"]]
    if sem_ean:
        st.warning(
            "Sem código de barras (SEM EAN-13 CADASTRADO): "
            + ", ".join(f'{item["codigo"]} - {item["descricao"]}' for item in sem_ean)
        )

    cards = "".join(
        f'<div class="mobile-card">'
        f'<div class="mobile-card-title">{escape(item["codigo"])} | Etiquetas: {item["copias"]}</div>'
        f'<div class="mobile-card-subtitle">{escape(item["descricao"])}</div>'
        f'<div class="mobile-card-meta">'
        f'<span class="mobile-pill">Referência: {escape(item["referencia"])}</span>'
        f'<span class="mobile-pill">EAN: {escape(item["ean"] or "sem EAN-13")}</span>'
        f'</div>'
        f'</div>'
        for item in itens
    )
    st.markdown(cards, unsafe_allow_html=True)

    with st.expander("Reimprimir / ajustar cópias"):
        copias = [
            int(
                st.number_input(
                    f'{item["codigo"]} - {item["descricao"]}',
                    min_value=1,
                    max_value=COPIAS_MAXIMO,
                    value=int(item["copias"]),
                    step=1,
                    key=f"{chave}_copias_{indice}",
                )
            )
            for indice, item in enumerate(itens)
        ]
        reimpressao = [dict(item, copias=qtd) for item, qtd in zip(itens, copias)]
        total = sum(copias)

        if st.button(
            f"Enviar para a impressora ({total})",
            use_container_width=True,
            key=f"{chave}_reenviar",
        ):
            _enviar_e_guardar(pacote, reimpressao)
            st.rerun()

        # A movimentação já está gravada: se o PDF falhar, só avisa.
        try:
            pdf = gerar_etiquetas_pdf(reimpressao)
        except Exception as erro:
            st.error(
                f"Não foi possível gerar o PDF das etiquetas ({erro}). A movimentação continua gravada."
            )
            return

        st.download_button(
            f"Baixar etiquetas em PDF ({total})",
            data=pdf,
            file_name="etiquetas_" + "_".join(item["codigo"] for item in itens)[:60] + ".pdf",
            mime="application/pdf",
            on_click="ignore",
            use_container_width=True,
            key=f"{chave}_baixar",
        )

        st.caption(
            "PDF: imprima a 100% (sem ajustar à página), no papel de 100 x 30 mm."
        )


def limpar_etiquetas(chave):
    for nome in list(st.session_state.keys()):
        if nome == chave or nome.startswith(f"{chave}_"):
            del st.session_state[nome]
