"""Agente de impressão de etiquetas do Mapeamento Trendx.

Roda no notebook do estoque, ligado por USB na impressora Honeywell. A cada
poucos segundos lê a aba "FILA IMPRESSÃO" da planilha "Mapeamento Trendx",
imprime as linhas PENDENTE e marca IMPRESSO ou ERRO.

Uso:
    python agente.py                 roda o agente (fica em loop)
    python agente.py --impressoras   lista as impressoras instaladas no Windows
    python agente.py --teste         imprime uma etiqueta de teste e sai
"""

import argparse
import configparser
import logging
import os
import sys
import time
import tomllib
from logging.handlers import RotatingFileHandler
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA.parent))

from utils import fila_impressao as fila  # noqa: E402
from utils.etiquetas import gerar_etiquetas_pdf  # noqa: E402


log = logging.getLogger("agente")

COMPUTADOR = os.environ.get("COMPUTERNAME", "computador")

# Bits de status da impressora (winspool) que impedem a impressão
PROBLEMAS_IMPRESSORA = {
    0x00000080: "impressora offline",
    0x00001000: "impressora indisponível",
    0x00000010: "sem etiqueta",
    0x00000008: "etiqueta enroscada",
    0x00400000: "tampa aberta",
    0x00040000: "sem ribbon",
    0x00100000: "impressora pedindo intervenção",
    0x00000002: "impressora em erro",
}
ATRIBUTO_OFFLINE = 0x00000400  # "Usar impressora offline" / USB desconectada

# Bits de status de um trabalho preso na fila do Windows
PROBLEMAS_TRABALHO = 0x00000002 | 0x00000020 | 0x00000040 | 0x00000200 | 0x00010000


class ImpressoraIndisponivel(Exception):
    pass


# ====================================
# CONFIGURAÇÃO
# ====================================

def carregar_config():
    config = configparser.ConfigParser()
    config.read(PASTA / "config.ini", encoding="utf-8")
    secao = config["agente"] if config.has_section("agente") else {}
    return {
        "impressora": secao.get("impressora", "").strip(),
        "intervalo": float(secao.get("intervalo_segundos", "4")),
        "credenciais": PASTA / secao.get("credenciais", "credenciais.toml"),
    }


def conectar_fila(arquivo_credenciais):
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    with open(arquivo_credenciais, "rb") as arquivo:
        credenciais = tomllib.load(arquivo)["google_credentials"]

    cliente = gspread.authorize(
        ServiceAccountCredentials.from_json_keyfile_dict(
            credenciais,
            [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ],
        )
    )
    return fila.abrir_ou_criar_aba(cliente.open(fila.PLANILHA))


# ====================================
# IMPRESSÃO (Windows, pelo driver da impressora)
# ====================================

def listar_impressoras():
    import win32print

    return [
        impressora[2]
        for impressora in win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )
    ]


def verificar_impressora(impressora):
    """Erro se a impressora estiver offline, desconectada ou com problema."""
    import win32print

    handle = win32print.OpenPrinter(impressora)
    try:
        info = win32print.GetPrinter(handle, 2)
    finally:
        win32print.ClosePrinter(handle)

    if info["Attributes"] & ATRIBUTO_OFFLINE:
        raise ImpressoraIndisponivel("impressora offline ou desconectada")

    problemas = [texto for bit, texto in PROBLEMAS_IMPRESSORA.items() if info["Status"] & bit]
    if problemas:
        raise ImpressoraIndisponivel(", ".join(problemas))


def aguardar_saida_da_fila(impressora, nome_documento, paginas):
    """Espera o trabalho sair da fila do Windows. Se travar, cancela e dá erro.

    Sem isso, uma etiqueta presa (impressora desligada, sem etiqueta...) seria
    marcada como IMPRESSO e sairia horas depois, quando a impressora voltasse.
    """
    import win32print

    limite = time.time() + 30 + 2 * paginas
    handle = win32print.OpenPrinter(impressora)
    try:
        while True:
            trabalhos = [
                trabalho for trabalho in win32print.EnumJobs(handle, 0, 999, 1)
                if trabalho["pDocument"] == nome_documento
            ]
            if not trabalhos:
                return

            travado = any(trabalho["Status"] & PROBLEMAS_TRABALHO for trabalho in trabalhos)
            if travado or time.time() > limite:
                for trabalho in trabalhos:
                    win32print.SetJob(handle, trabalho["JobId"], 0, None, win32print.JOB_CONTROL_DELETE)
                raise ImpressoraIndisponivel(
                    "a etiqueta ficou presa na fila do Windows e foi cancelada "
                    "(impressora desligada, desconectada ou sem etiqueta?)"
                )

            time.sleep(0.5)
    finally:
        win32print.ClosePrinter(handle)


def imprimir_pdf(pdf, impressora, arquivo_saida=None, nome_documento="Etiquetas Mapeamento Trendx"):
    """Imprime cada página do PDF em tamanho real (100 x 30 mm) pelo driver do Windows."""
    import pypdfium2
    import win32con
    import win32gui
    import win32print
    import win32ui
    from PIL import Image, ImageWin

    documento = pypdfium2.PdfDocument(pdf)

    # Papel da etiqueta (100 x 30 mm) pedido ao driver em cada impressão,
    # sem depender do padrão configurado no Windows.
    largura_pt, altura_pt = documento[0].get_size()
    handle = win32print.OpenPrinter(impressora)
    try:
        devmode = win32print.GetPrinter(handle, 2)["pDevMode"]
    finally:
        win32print.ClosePrinter(handle)
    devmode.PaperSize = 256  # DMPAPER_USER (tamanho personalizado)
    devmode.PaperWidth = round(max(largura_pt, altura_pt) / 72 * 254)  # décimos de mm
    devmode.PaperLength = round(min(largura_pt, altura_pt) / 72 * 254)
    devmode.Orientation = win32con.DMORIENT_PORTRAIT
    devmode.Fields |= (
        win32con.DM_PAPERSIZE | win32con.DM_PAPERWIDTH | win32con.DM_PAPERLENGTH | win32con.DM_ORIENTATION
    )

    dc = win32ui.CreateDCFromHandle(
        win32gui.CreateDC("WINSPOOL", impressora, devmode)
    )

    try:
        dpi_x = dc.GetDeviceCaps(win32con.LOGPIXELSX)
        dpi_y = dc.GetDeviceCaps(win32con.LOGPIXELSY)
        pagina_horizontal = dc.GetDeviceCaps(win32con.PHYSICALWIDTH) >= dc.GetDeviceCaps(win32con.PHYSICALHEIGHT)
        margem_x = dc.GetDeviceCaps(win32con.PHYSICALOFFSETX)
        margem_y = dc.GetDeviceCaps(win32con.PHYSICALOFFSETY)

        dc.StartDoc(nome_documento, arquivo_saida)
        cache = {}

        for indice in range(len(documento)):
            pagina = documento[indice]
            conteudo = pagina.get_textpage().get_text_range()
            imagem = cache.get(conteudo)

            if imagem is None:
                imagem = pagina.render(scale=dpi_x / 72, grayscale=True).to_pil().convert("1", dither=Image.NONE)
                # Driver configurado com a etiqueta "em pé": gira para caber em tamanho real.
                if (imagem.width >= imagem.height) != pagina_horizontal:
                    imagem = imagem.rotate(90, expand=True)
                cache[conteudo] = imagem

            largura_pt, altura_pt = pagina.get_size()
            if imagem.width < imagem.height:
                largura_pt, altura_pt = altura_pt, largura_pt
            largura = round(largura_pt / 72 * dpi_x)
            altura = round(altura_pt / 72 * dpi_y)

            dc.StartPage()
            ImageWin.Dib(imagem.convert("RGB")).draw(
                dc.GetHandleOutput(),
                (-margem_x, -margem_y, largura - margem_x, altura - margem_y),
            )
            dc.EndPage()

        dc.EndDoc()
        paginas = len(documento)
    finally:
        dc.DeleteDC()
        documento.close()

    if arquivo_saida is None:
        aguardar_saida_da_fila(impressora, nome_documento, paginas)


# ====================================
# FILA
# ====================================

def atualizar_linha(aba, numero_linha, status, mensagem=""):
    inicio = fila.coluna_letra("Status")
    fim = fila.coluna_letra("Mensagem")
    aba.update(
        [[status, fila.agora_brasilia(), mensagem[:300]]],
        f"{inicio}{numero_linha}:{fim}{numero_linha}",
    )


def ler_fila(aba):
    linhas = aba.get_all_values()
    if not linhas:
        return []
    cabecalho = linhas[0]
    return [
        (numero, dict(zip(cabecalho, linha + [""] * (len(cabecalho) - len(linha)))))
        for numero, linha in enumerate(linhas[1:], start=2)
    ]


def recuperar_interrompidas(aba):
    """Linhas que ficaram IMPRIMINDO (agente desligado no meio) viram ERRO para não imprimir em dobro."""
    for numero, registro in ler_fila(aba):
        if registro.get("Status", "").strip().upper() == fila.IMPRIMINDO:
            atualizar_linha(
                aba,
                numero,
                fila.ERRO,
                "Agente reiniciado durante a impressão. Confira e reimprima se faltar etiqueta.",
            )


def processar_pendentes(aba, impressora):
    for numero, registro in ler_fila(aba):
        if registro.get("Status", "").strip().upper() != fila.PENDENTE:
            continue

        item = fila.item_da_linha(registro)

        try:
            verificar_impressora(impressora)
        except Exception as erro:
            log.warning("Impressora indisponível para %s (linha %s): %s", item["codigo"], numero, erro)
            atualizar_linha(aba, numero, fila.ERRO, f"{COMPUTADOR} / {impressora}: {erro}")
            continue

        atualizar_linha(aba, numero, fila.IMPRIMINDO)

        try:
            imprimir_pdf(
                gerar_etiquetas_pdf([item]),
                impressora,
                nome_documento=f"Etiquetas {registro.get('ID', '')}",
            )
        except Exception as erro:
            log.exception("Erro ao imprimir %s (linha %s)", item["codigo"], numero)
            atualizar_linha(aba, numero, fila.ERRO, f"{COMPUTADOR} / {impressora}: {erro}")
            continue

        atualizar_linha(aba, numero, fila.IMPRESSO, f"{COMPUTADOR} / {impressora}")
        log.info("Impresso %s x%s (%s)", item["codigo"], item["copias"], registro.get("Movimentação", ""))


def rodar(config):
    log.info("Agente iniciado. Impressora: %s", config["impressora"])
    aba = None

    while True:
        try:
            if aba is None:
                aba = conectar_fila(config["credenciais"])
                recuperar_interrompidas(aba)
            processar_pendentes(aba, config["impressora"])
            time.sleep(config["intervalo"])
        except KeyboardInterrupt:
            log.info("Agente encerrado.")
            return
        except Exception:
            # Sem internet, Google fora do ar, cota excedida...: espera e reconecta.
            log.exception("Erro no ciclo do agente. Nova tentativa em 30 s.")
            aba = None
            time.sleep(30)


# ====================================
# INÍCIO
# ====================================

def configurar_log():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            RotatingFileHandler(PASTA / "agente.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--impressoras", action="store_true", help="lista as impressoras do Windows")
    parser.add_argument("--teste", action="store_true", help="imprime uma etiqueta de teste")
    argumentos = parser.parse_args()

    configurar_log()

    if argumentos.impressoras:
        for nome in listar_impressoras():
            print(nome)
        return

    config = carregar_config()
    if not config["impressora"]:
        sys.exit("Defina o nome da impressora em config.ini (use --impressoras para ver os nomes).")

    if argumentos.teste:
        item = {
            "codigo": "00003",
            "descricao": "ETIQUETA DE TESTE - MAPEAMENTO TRENDX",
            "referencia": "TESTE",
            "ean": "7898723145367",
            "quantidade": None,
            "copias": 1,
        }
        verificar_impressora(config["impressora"])
        imprimir_pdf(gerar_etiquetas_pdf([item]), config["impressora"])
        print("Etiqueta de teste impressa em", config["impressora"])
        return

    rodar(config)


if __name__ == "__main__":
    main()
