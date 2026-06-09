import pandas as pd


def registros_para_df(registros):
    df = pd.DataFrame(registros)
    if df.empty:
        return df

    df.columns = [str(coluna).strip() for coluna in df.columns]
    return df.fillna("")


def normalizar_textos(df, colunas):
    df = df.copy()
    for coluna in colunas:
        if coluna in df.columns:
            df[coluna] = df[coluna].fillna("").astype(str).str.strip()
    return df


def preparar_posicao(registros):
    df = registros_para_df(registros)
    if df.empty:
        return df

    df = normalizar_textos(
        df,
        ["Status", "Data", "Vaga", "Código", "Descrição", "Referência", "Observações"],
    )

    if "Vaga" in df.columns:
        df["Vaga"] = df["Vaga"].str.upper()

    if "Status" in df.columns:
        df["Status"] = df["Status"].str.upper()

    if "Quantidade" in df.columns:
        df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce").fillna(0).astype(int)

    return df


def preparar_bd_produtos(registros):
    df = registros_para_df(registros)
    if df.empty:
        return df

    return normalizar_textos(
        df,
        ["Código", "Descrição", "Categoria", "Tipo", "Marca", "Grupo", "Subgrupo", "Referência"],
    )


def preparar_historico(registros):
    df = registros_para_df(registros)
    if df.empty:
        return df

    df = normalizar_textos(df, ["Data", "Vaga", "Código", "Descrição", "Usuário"])

    if "Vaga" in df.columns:
        df["Vaga"] = df["Vaga"].str.upper()

    if "Quantidade" in df.columns:
        df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce").fillna(0).astype(int)

    if "Data" in df.columns:
        df["_DataOrdenacao"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)

    return df


def enriquecer_posicao_com_bd(df_posicao, df_bd):
    if df_posicao.empty or df_bd.empty or "Código" not in df_posicao.columns or "Código" not in df_bd.columns:
        return df_posicao

    colunas_auxiliares = [
        coluna
        for coluna in ["Código", "Categoria", "Tipo", "Marca", "Grupo", "Subgrupo"]
        if coluna in df_bd.columns
    ]

    if len(colunas_auxiliares) <= 1:
        return df_posicao

    df_auxiliar = df_bd[colunas_auxiliares].drop_duplicates(subset=["Código"]).copy()
    return df_posicao.merge(df_auxiliar, on="Código", how="left")


def produtos_ocupados(df_posicao):
    if df_posicao.empty:
        return df_posicao

    df = df_posicao.copy()
    mascara_codigo = df.get("Código", "").fillna("").astype(str).str.strip() != ""
    mascara_quantidade = df.get("Quantidade", 0) > 0

    if "Status" in df.columns:
        mascara_status = df["Status"].fillna("").astype(str).str.upper() != "DISPONIVEL"
    else:
        mascara_status = True

    return df[mascara_codigo & mascara_quantidade & mascara_status].copy()


def resumo_vagas(df_posicao):
    if df_posicao.empty or "Vaga" not in df_posicao.columns:
        return {
            "total": 0,
            "ocupadas": 0,
            "disponiveis": 0,
            "itens": 0,
            "quantidade": 0,
        }

    vagas_totais = df_posicao["Vaga"].replace("", pd.NA).dropna().nunique()
    df_ocupado = produtos_ocupados(df_posicao)
    vagas_ocupadas = df_ocupado["Vaga"].replace("", pd.NA).dropna().nunique() if "Vaga" in df_ocupado.columns else 0

    return {
        "total": int(vagas_totais),
        "ocupadas": int(vagas_ocupadas),
        "disponiveis": int(max(vagas_totais - vagas_ocupadas, 0)),
        "itens": int(len(df_ocupado)),
        "quantidade": int(df_ocupado["Quantidade"].sum()) if "Quantidade" in df_ocupado.columns else 0,
    }
