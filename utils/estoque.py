# ====================================
# BUSCAR VAGA
# ====================================

def buscar_vaga(vaga, dados_posicao):

    vaga = str(
        vaga
    ).strip().upper()

    resultados = []

    for linha in dados_posicao:

        vaga_planilha = str(
            linha.get("Vaga", "")
        ).strip().upper()

        if vaga_planilha == vaga:

            resultados.append(linha)

    vaga_existe = len(resultados) > 0

    return {

        "vaga_existe": vaga_existe,

        "resultados": resultados

    }


# ====================================
# BUSCAR PRODUTO
# ====================================

def buscar_produto(codigo, dados_bd):

    codigo = str(
        codigo
    ).strip()

    for produto in dados_bd:

        codigo_bd = str(
            produto.get("Código", "")
        ).strip()

        if codigo_bd == codigo:

            return {

                "produto_encontrado": True,

                "descricao": str(
                    produto.get("Descrição", "")
                ).strip()

            }

    return {

        "produto_encontrado": False,

        "descricao": ""

    }


# ====================================
# LISTAR VALORES
# ====================================

def listar_valores_unicos(dados, coluna):

    valores = []

    for linha in dados:

        valor = str(
            linha.get(coluna, "")
        ).strip()

        if valor and valor not in valores:

            valores.append(valor)

    return sorted(valores)


# ====================================
# QUANTIDADE INTEIRA
# ====================================

def quantidade_int(valor):

    try:

        return int(float(str(valor).strip() or 0))

    except (TypeError, ValueError):

        return 0


# ====================================
# BUSCAR PRODUTO NA VAGA
# ====================================

def buscar_produto_vaga(

    codigo,
    resultados_vaga

):

    codigo = str(
        codigo
    ).strip()

    for linha in resultados_vaga:

        codigo_existente = str(
            linha.get("Código", "")
        ).strip()

        if codigo_existente == codigo:

            return {

                "produto_encontrado": True,

                "linha": linha,

                "quantidade": quantidade_int(
                    linha.get("Quantidade", "")
                )

            }

    return {

        "produto_encontrado": False,

        "linha": None,

        "quantidade": 0

    }


# ====================================
# VALIDAR SAÍDA
# ====================================

def validar_saida(

    quantidade_atual,
    quantidade_saida

):

    quantidade_atual = int(
        quantidade_atual
    )

    quantidade_saida = int(
        quantidade_saida
    )

    if quantidade_saida > quantidade_atual:

        return {

            "valido": False,

            "mensagem": (
                "Quantidade maior "
                "que o saldo disponível"
            )

        }

    return {

        "valido": True,

        "mensagem": ""

    }


# ====================================
# É ÚLTIMO PRODUTO?
# ====================================

def ultimo_produto_vaga(

    resultados_vaga

):

    total_produtos = 0

    for linha in resultados_vaga:

        codigo = str(
            linha.get("Código", "")
        ).strip()

        if codigo != "":

            total_produtos += 1

    return total_produtos == 1
