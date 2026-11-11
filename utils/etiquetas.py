"""Etiquetas EAN-13 de 100 x 30 mm para os produtos recebidos.

Segue a documentacao "Geracao de etiquetas EAN-13 para a agenda de recebimentos":
regras de EAN valido, escolha do EAN quando ha mais de um e o layout com as
medidas a partir do canto superior esquerdo da etiqueta.
"""

from io import BytesIO

from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


PREFIXO_GOPER = "7898723"
LARGURA, ALTURA = 100 * mm, 30 * mm


# ==================================================
# REGRAS DE DADOS
# ==================================================

def normalizar_codigo(codigo):
    """'4164' -> '04164'. O codigo e sempre texto de 5 digitos."""
    texto = str(codigo or "").strip()
    if not texto:
        return ""
    return texto.zfill(5)[-5:]


def digito_verificador(doze):
    soma = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(doze))
    return (10 - soma % 10) % 10


def ean13_valido(codigo):
    codigo = str(codigo or "").strip()
    return (
        len(codigo) == 13
        and codigo.isdigit()
        and not codigo.startswith(("2", "9000"))
        and digito_verificador(codigo[:12]) == int(codigo[12])
    )


def escolher_ean(barras):
    """Devolve (ean, outros_ean) a partir de todos os codigos de barras do produto."""
    validos = list(dict.fromkeys(str(b).strip() for b in barras if ean13_valido(b)))
    if not validos:
        return "", []
    principal = next((ean for ean in validos if ean.startswith(PREFIXO_GOPER)), validos[0])
    return principal, [ean for ean in validos if ean != principal]


# ==================================================
# CODIFICACAO EAN-13 (95 modulos)
# ==================================================

_L = ["0001101", "0011001", "0010011", "0111101", "0100011", "0110001", "0101111", "0111011", "0110111", "0001011"]
_G = ["0100111", "0110011", "0011011", "0100001", "0011101", "0111001", "0000101", "0010001", "0001001", "0010111"]
_R = ["1110010", "1100110", "1101100", "1000010", "1011100", "1001110", "1010000", "1000100", "1001000", "1110100"]
_PARIDADE = ["LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG", "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL"]


def modulos_ean13(ean):
    """Padrao de 95 modulos ('1' barra, '0' espaco)."""
    if not ean13_valido(ean):
        raise ValueError(f"EAN-13 inválido: {ean}")
    digitos = [int(d) for d in ean]
    paridade = _PARIDADE[digitos[0]]
    esquerda = "".join((_L if p == "L" else _G)[d] for p, d in zip(paridade, digitos[1:7]))
    direita = "".join(_R[d] for d in digitos[7:])
    return "101" + esquerda + "01010" + direita + "101"


def ean_legivel(ean):
    """'7898723149655' -> '7  898723  149655'."""
    return f"{ean[0]}  {ean[1:7]}  {ean[7:]}"


# ==================================================
# LAYOUT 100 x 30 mm
# ==================================================

FONTE = "Helvetica"
FONTE_NEGRITO = "Helvetica-Bold"
MODULO = 1.3  # pt (~0,46 mm) -> 95 modulos = ~43,6 mm
CENTRO_DIREITA = 68 * mm
LARGURA_DESCRICAO = 57 * mm
LARGURA_ESQUERDA = 33 * mm  # de x = 3 mm ate a divisoria em 36 mm


def _y(topo_mm):
    """Medida a partir do topo da etiqueta -> coordenada do PDF (origem embaixo)."""
    return ALTURA - topo_mm * mm


def _quebrar(texto, fonte, tamanho, largura):
    linhas, atual = [], ""
    for palavra in texto.split():
        tentativa = f"{atual} {palavra}".strip()
        if stringWidth(tentativa, fonte, tamanho) <= largura or not atual:
            atual = tentativa
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def _descricao_em_duas_linhas(texto):
    """Ate 2 linhas; reduz 0,5 pt por vez de 8,5 ate 6 pt."""
    tamanho = 8.5
    while True:
        linhas = _quebrar(texto, FONTE_NEGRITO, tamanho, LARGURA_DESCRICAO)
        cabe = len(linhas) <= 2 and all(stringWidth(l, FONTE_NEGRITO, tamanho) <= LARGURA_DESCRICAO for l in linhas)
        if cabe or tamanho <= 6:
            break
        tamanho -= 0.5
    if len(linhas) > 2:
        linhas = linhas[:2]
        while stringWidth(linhas[1] + "…", FONTE_NEGRITO, tamanho) > LARGURA_DESCRICAO and len(linhas[1]) > 1:
            linhas[1] = linhas[1][:-1]
        linhas[1] = linhas[1].rstrip() + "…"
    return linhas, tamanho


def _texto_ajustado(c, texto, x, y, fonte, tamanho, largura, minimo=6):
    while tamanho > minimo and stringWidth(texto, fonte, tamanho) > largura:
        tamanho -= 0.5
    c.setFont(fonte, tamanho)
    c.drawString(x, y, texto)


def _desenhar_etiqueta(c, item, moldura=False):
    c.setFillColorRGB(0, 0, 0)
    c.setStrokeColorRGB(0, 0, 0)

    if moldura:
        c.setLineWidth(0.5 * mm)
        c.rect(0.25 * mm, 0.25 * mm, LARGURA - 0.5 * mm, ALTURA - 0.5 * mm)

    # Lado esquerdo: codigo e referencia
    c.setFont(FONTE_NEGRITO, 6)
    c.drawString(3 * mm, _y(5), "CÓDIGO")
    _texto_ajustado(c, item["codigo"], 3 * mm, _y(15), FONTE_NEGRITO, 26, LARGURA_ESQUERDA)
    c.setFont(FONTE_NEGRITO, 6)
    c.drawString(3 * mm, _y(20), "REFERÊNCIA")
    _texto_ajustado(c, item.get("referencia") or "—", 3 * mm, _y(25), FONTE_NEGRITO, 10, LARGURA_ESQUERDA)

    quantidade = item.get("quantidade")
    if quantidade not in (None, ""):
        c.setFont(FONTE_NEGRITO, 8)
        c.drawString(3 * mm, _y(27.5), f"QTD: {quantidade}")

    # Divisoria vertical
    c.setLineWidth(0.5)
    c.line(36 * mm, _y(3), 36 * mm, _y(27))

    # Lado direito: descricao
    linhas, tamanho = _descricao_em_duas_linhas(" ".join(str(item.get("descricao") or "").upper().split()))
    c.setFont(FONTE_NEGRITO, tamanho)
    for indice, linha in enumerate(linhas):
        c.drawCentredString(CENTRO_DIREITA, _y(6) - indice * tamanho * 1.15, linha)

    ean = str(item.get("ean") or "").strip()
    if not ean13_valido(ean):
        # Produto sem EAN-13 cadastrado: etiqueta sai sem codigo de barras, com o aviso no lugar.
        c.setFont(FONTE_NEGRITO, 8)
        c.drawCentredString(CENTRO_DIREITA, _y(17), "SEM EAN-13 CADASTRADO")
        return

    # Codigo de barras: vetor, uma barra por sequencia de modulos pretos
    padrao = modulos_ean13(ean)
    x0 = CENTRO_DIREITA - len(padrao) * MODULO / 2
    y0, altura = _y(21.5), 11 * mm
    inicio = None
    for indice, modulo in enumerate(padrao + "0"):
        if modulo == "1" and inicio is None:
            inicio = indice
        elif modulo == "0" and inicio is not None:
            c.rect(x0 + inicio * MODULO, y0, (indice - inicio) * MODULO, altura, stroke=0, fill=1)
            inicio = None

    c.setFont(FONTE, 7)
    c.drawCentredString(CENTRO_DIREITA, _y(25.5), ean_legivel(ean))


def gerar_etiquetas_pdf(itens, moldura=False):
    """Gera o PDF com uma pagina de 100 x 30 mm por copia, na ordem dos itens.

    Cada item: codigo, descricao, referencia, ean, quantidade (ou None) e copias.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape((ALTURA, LARGURA)))
    c.setTitle("Etiquetas EAN-13")
    for item in itens:
        for _ in range(max(1, int(item.get("copias") or 1))):
            _desenhar_etiqueta(c, item, moldura=moldura)
            c.showPage()
    c.save()
    return buffer.getvalue()
