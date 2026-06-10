import streamlit as st
import gspread
import pandas as pd

from oauth2client.service_account import (
    ServiceAccountCredentials
)


@st.cache_resource
def conectar_google_sheets():

    scope = [

        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"

    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(

        st.secrets["google_credentials"],
        scope

    )

    cliente = gspread.authorize(creds)

    return cliente


@st.cache_data(ttl=30)
def ler_aba(nome_planilha, nome_aba):

    cliente = conectar_google_sheets()

    planilha = cliente.open(nome_planilha)

    aba = planilha.worksheet(nome_aba)

    dados = aba.get_all_values()

    if not dados:

        return []

    cabecalho = dados[0]

    linhas = dados[1:]

    df = pd.DataFrame(
        linhas,
        columns=cabecalho
    )

    return df.to_dict(
        orient="records"
    )


def abrir_aba(nome_planilha, nome_aba):

    cliente = conectar_google_sheets()

    planilha = cliente.open(nome_planilha)

    aba = planilha.worksheet(nome_aba)

    return aba


def ler_aba_atual(nome_planilha, nome_aba):

    aba = abrir_aba(
        nome_planilha,
        nome_aba
    )

    dados = aba.get_all_values()

    if not dados:

        return []

    cabecalho = dados[0]

    linhas = dados[1:]

    registros = []

    for indice, linha in enumerate(linhas, start=2):

        linha_completa = (
            linha
            + [""] * max(len(cabecalho) - len(linha), 0)
        )

        registro = dict(
            zip(cabecalho, linha_completa)
        )

        registro["_linha_planilha"] = indice

        registros.append(registro)

    return registros
