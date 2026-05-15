from utils.sheets import abrir_aba


# ====================================
# REGISTRAR HISTÓRICO
# ====================================

def registrar_historico(

    data,
    vaga,
    codigo,
    descricao,
    quantidade,
    usuario

):

    aba_historico = abrir_aba(

        "Mapeamento Trendx",
        "HISTÓRICO"

    )

    aba_historico.append_row([

        str(data),
        str(vaga),
        str(codigo),
        str(descricao),
        int(quantidade),
        str(usuario)

    ])