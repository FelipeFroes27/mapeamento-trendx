"""Gravação segura de uma linha da aba POSIÇÃO.

Antes de alterar ou apagar uma linha, relê essa linha e confere se ela ainda é
a mesma vaga/produto/saldo lidos pelo app. Outro coletor pode ter apagado uma
linha acima (as linhas sobem) ou mudado o saldo nesse meio tempo.

As alterações de uma linha vão numa única chamada ao Google, para a linha não
ficar pela metade se a conexão cair.
"""

import time


# Colunas da aba POSIÇÃO
COLUNA = {
    "Status": "A",
    "Data": "B",
    "Vaga": "C",
    "Código": "D",
    "Descrição": "E",
    "Quantidade": "F",
    "Referencia": "G",
    "Observações": "H",
}


class LinhaMudou(Exception):
    """A linha da planilha não é mais a que o app leu."""


def _texto(valor):
    return str(valor if valor is not None else "").strip().upper()


def conferir_linha(aba, linha_real, vaga, codigo, quantidade=None):
    """Confere vaga, código (e saldo, se informado) da linha antes de mexer nela."""
    valores = aba.row_values(linha_real)
    valores = valores + [""] * (8 - len(valores))

    if _texto(valores[2]) != _texto(vaga) or _texto(valores[3]) != _texto(codigo):
        raise LinhaMudou()

    if quantidade is not None:
        try:
            saldo = int(float(str(valores[5]).strip() or 0))
        except ValueError:
            saldo = None
        if saldo != int(quantidade):
            raise LinhaMudou()


def gravar_linha(aba, linha_real, valores, tentativas=3):
    """Grava {"Quantidade": 5, "Data": "..."} na linha, numa única chamada.

    Repetir é seguro (só define valores), então tenta de novo se o Google falhar.
    """
    dados = [
        {"range": f"{COLUNA[nome]}{linha_real}", "values": [[valor]]}
        for nome, valor in valores.items()
    ]

    for tentativa in range(tentativas):
        try:
            aba.batch_update(dados)
            return
        except Exception:
            if tentativa == tentativas - 1:
                raise
            time.sleep(1 + tentativa)


def conferir_e_gravar(aba, linha_real, vaga, codigo, valores, quantidade=None):
    conferir_linha(aba, linha_real, vaga, codigo, quantidade)
    gravar_linha(aba, linha_real, valores)
