"""Fila de impressão de etiquetas, compartilhada entre o app e o agente do notebook.

O app grava uma linha por produto na aba "FILA IMPRESSÃO" da planilha
"Mapeamento Trendx". O agente de impressão (agente_impressao/agente.py) lê as
linhas PENDENTE, imprime e marca IMPRESSO ou ERRO.

Este módulo não depende do Streamlit, para o agente poder usar também.
"""

import uuid
from datetime import datetime, timedelta, timezone


PLANILHA = "Mapeamento Trendx"
ABA = "FILA IMPRESSÃO"

COLUNAS = [
    "ID",
    "Criado em",
    "Movimentação",
    "Vaga",
    "Usuário",
    "Codigo",
    "Descricao",
    "Referencia",
    "EAN",
    "Copias",
    "Status",
    "Impresso em",
    "Mensagem",
]

PENDENTE = "PENDENTE"
IMPRIMINDO = "IMPRIMINDO"
IMPRESSO = "IMPRESSO"
ERRO = "ERRO"

FUSO_BRASILIA = timezone(timedelta(hours=-3))


def agora_brasilia():
    return datetime.now(FUSO_BRASILIA).strftime("%d/%m/%Y %H:%M:%S")


def coluna_letra(nome):
    """Letra da coluna na planilha ('Status' -> 'K')."""
    return chr(ord("A") + COLUNAS.index(nome))


def abrir_ou_criar_aba(planilha):
    """Abre a aba da fila; cria com o cabeçalho se ainda não existir."""
    import gspread

    try:
        return planilha.worksheet(ABA)
    except gspread.WorksheetNotFound:
        aba = planilha.add_worksheet(title=ABA, rows=1000, cols=len(COLUNAS))
        aba.append_row(COLUNAS)
        return aba


def linha_da_fila(item, movimentacao, vaga, usuario):
    """Linha da planilha para um item de etiqueta."""
    return [
        uuid.uuid4().hex[:12],
        agora_brasilia(),
        movimentacao,
        vaga,
        usuario,
        item["codigo"],
        item["descricao"],
        item["referencia"],
        item["ean"],
        int(item["copias"]),
        PENDENTE,
        "",
        "",
    ]


def item_da_linha(registro):
    """Item no formato de gerar_etiquetas_pdf a partir de uma linha da fila."""
    try:
        copias = int(float(str(registro.get("Copias", "1")).replace(",", ".")))
    except ValueError:
        copias = 1

    return {
        "codigo": str(registro.get("Codigo", "")).strip(),
        "descricao": str(registro.get("Descricao", "")).strip(),
        "referencia": str(registro.get("Referencia", "")).strip() or "—",
        "ean": str(registro.get("EAN", "")).strip(),
        "quantidade": None,
        "copias": max(copias, 1),
    }
