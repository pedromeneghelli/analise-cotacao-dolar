"""Coleta da cotação do dólar na API de Séries Temporais (SGS) do Banco Central."""

from datetime import date, timedelta

import pandas as pd
import requests

URL_SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"

# Série 1: Taxa de câmbio livre - Dólar americano (venda) - diária
SERIE_DOLAR_VENDA = 1

# A API limita consultas de séries diárias a janelas de até 10 anos.
DIAS_POR_JANELA = 3650


def gerar_janelas(inicio: date, fim: date, dias: int = DIAS_POR_JANELA):
    """Divide o período em janelas consecutivas, sem buracos nem sobreposição."""
    if inicio > fim:
        raise ValueError("A data inicial não pode ser maior que a data final.")
    atual = inicio
    while atual <= fim:
        limite = min(atual + timedelta(days=dias - 1), fim)
        yield atual, limite
        atual = limite + timedelta(days=1)


def baixar_serie(codigo: int, inicio: date, fim: date, timeout: int = 30) -> pd.DataFrame:
    """Baixa uma série do SGS e devolve um DataFrame com as colunas 'data' e 'valor'."""
    registros = []
    for ini, fi in gerar_janelas(inicio, fim):
        params = {
            "formato": "json",
            "dataInicial": ini.strftime("%d/%m/%Y"),
            "dataFinal": fi.strftime("%d/%m/%Y"),
        }
        resposta = requests.get(URL_SGS.format(codigo=codigo), params=params, timeout=timeout)
        if resposta.status_code == 404:
            # Janela sem dados (ex.: só fim de semana ou feriado)
            continue
        resposta.raise_for_status()
        registros.extend(resposta.json())

    return pd.DataFrame(registros, columns=["data", "valor"])
